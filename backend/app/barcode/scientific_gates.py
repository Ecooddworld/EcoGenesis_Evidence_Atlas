from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import secrets
from typing import Any, Iterable

from .schemas import (
    BarcodeCompilerRequest,
    EvidenceAttestation,
    ExternalValidationManifest,
    ReferenceCompletenessEvidence,
    SequenceRecord,
)


MIN_TARGET_REFERENCE_SPECIMENS = 3
MIN_CLOSE_RELATIVE_TAXA = 2
MIN_NEGATIVE_REFERENCE_SEQUENCES = 6
MIN_GEOGRAPHIC_REGIONS = 2
MIN_DIAGNOSTIC_KMER_SUPPORT = 2
MIN_DIAGNOSTIC_CONSERVATION = 0.95
MIN_PAIRWISE_ALIGNED_SITES = 80
MAX_AMBIGUOUS_BASE_FRACTION = 0.01
MIN_NORMALIZED_SHANNON_ENTROPY = 0.55
MAX_HOMOPOLYMER_RUN = 12
MIN_EXTERNAL_HOLDOUT_RECORDS = 30
MAX_ALIGNMENT_CELLS = 4_000_000
ATTESTATION_VERSION = "ecogenesis-evidence-attestation-v1"
ATTESTATION_ALGORITHM = "hmac-sha256"
ATTESTATION_SECRET_ENV = "ECOGENESIS_EVIDENCE_ATTESTATION_SECRET"
ATTESTATION_KEY_ID_ENV = "ECOGENESIS_EVIDENCE_ATTESTATION_KEY_ID"
DEFAULT_ATTESTATION_KEY_ID = "configured-local-hmac-v1"
MIN_ATTESTATION_SECRET_BYTES = 32
DEFAULT_ATTESTATION_TTL_SECONDS = 24 * 60 * 60
MAX_ATTESTATION_TTL_SECONDS = 7 * 24 * 60 * 60
ATTESTATION_CLOCK_SKEW_SECONDS = 5 * 60
EXTERNAL_HOLDOUT_PURPOSE = "external_holdout"
REFERENCE_COMPLETENESS_PURPOSE = "reference_completeness"
REQUIRED_HOLDOUT_METRICS = (
    "species_precision",
    "species_precision_ci_low",
    "species_precision_ci_high",
    "species_recall",
    "species_recall_ci_low",
    "species_recall_ci_high",
    "genus_precision",
    "abstention_rate",
    "false_species_rule_pass_rate",
    "false_species_rule_pass_rate_ci_low",
    "false_species_rule_pass_rate_ci_high",
)
REQUIRED_BASELINE_METRICS = (
    "naive_top_hit_species_precision",
    "naive_top_hit_false_species_rate",
)
REQUIRED_HOLDOUT_STRATA = (
    "marker",
    "taxonomic_group",
    "reference_completeness",
)
HOLDOUT_CONFIDENCE_INTERVALS = (
    ("species_precision", "species_precision_ci_low", "species_precision_ci_high"),
    ("species_recall", "species_recall_ci_low", "species_recall_ci_high"),
    (
        "false_species_rule_pass_rate",
        "false_species_rule_pass_rate_ci_low",
        "false_species_rule_pass_rate_ci_high",
    ),
)

IUPAC_BASES = {
    "A": frozenset("A"),
    "C": frozenset("C"),
    "G": frozenset("G"),
    "T": frozenset("T"),
    "R": frozenset("AG"),
    "Y": frozenset("CT"),
    "S": frozenset("CG"),
    "W": frozenset("AT"),
    "K": frozenset("GT"),
    "M": frozenset("AC"),
    "B": frozenset("CGT"),
    "D": frozenset("AGT"),
    "H": frozenset("ACT"),
    "V": frozenset("ACG"),
    "N": frozenset("ACGT"),
}

COMPLEMENT = str.maketrans(
    "ACGTRYSWKMBDHVN",
    "TGCAYRSWMKVHDBN",
)


def stable_payload_sha256(payload: Any) -> str:
    compact = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def compiler_contract_sha256(request: BarcodeCompilerRequest) -> str:
    """Bind external validation to the declared scientific ruleset and gate policy.

    Dataset title, records and presentation metadata are intentionally excluded: an
    independent benchmark attests a ruleset, not one later API request.  Changing a
    scientific threshold or the ruleset version changes this digest.
    """

    implementation_root = Path(__file__).resolve().parent
    implementation_files = (
        "benchmark.py",
        "compiler.py",
        "profiles.py",
        "schemas.py",
        "scientific_gates.py",
    )
    implementation_hashes = {
        name: hashlib.sha256((implementation_root / name).read_bytes()).hexdigest()
        for name in implementation_files
    }
    return stable_payload_sha256({
        "attestation_contract": ATTESTATION_VERSION,
        "ruleset_version": request.ruleset_version,
        # Bind the attestation to the exact executable scientific contract, not
        # only to a user-provided version label. Any gate/profile/harness change
        # therefore invalidates an older holdout attestation fail-closed.
        "implementation_sha256": implementation_hashes,
        "scientific_gate_policy": {
            "minimum_external_holdout_records": MIN_EXTERNAL_HOLDOUT_RECORDS,
            "minimum_target_reference_specimens": MIN_TARGET_REFERENCE_SPECIMENS,
            "minimum_close_relative_taxa": MIN_CLOSE_RELATIVE_TAXA,
            "minimum_negative_reference_sequences": MIN_NEGATIVE_REFERENCE_SEQUENCES,
            "minimum_geographic_regions": MIN_GEOGRAPHIC_REGIONS,
            "minimum_diagnostic_kmer_support": MIN_DIAGNOSTIC_KMER_SUPPORT,
            "minimum_diagnostic_conservation": MIN_DIAGNOSTIC_CONSERVATION,
            "minimum_pairwise_aligned_sites": MIN_PAIRWISE_ALIGNED_SITES,
            "maximum_ambiguous_base_fraction": MAX_AMBIGUOUS_BASE_FRACTION,
        },
    })


def attestation_configuration_status() -> dict[str, Any]:
    raw_secret = os.getenv(ATTESTATION_SECRET_ENV, "")
    key_id = os.getenv(ATTESTATION_KEY_ID_ENV, "").strip() or DEFAULT_ATTESTATION_KEY_ID
    if not raw_secret:
        return {
            "status": "server_verification_not_configured",
            "configured": False,
            "key_id": key_id,
            "minimum_secret_bytes": MIN_ATTESTATION_SECRET_BYTES,
        }
    secret_bytes = raw_secret.encode("utf-8")
    if len(secret_bytes) < MIN_ATTESTATION_SECRET_BYTES:
        return {
            "status": "server_verification_misconfigured",
            "configured": False,
            "key_id": key_id,
            "minimum_secret_bytes": MIN_ATTESTATION_SECRET_BYTES,
        }
    return {
        "status": "configured",
        "configured": True,
        "key_id": key_id,
        "minimum_secret_bytes": MIN_ATTESTATION_SECRET_BYTES,
    }


def issue_evidence_attestation(
    payload: Any,
    *,
    purpose: str,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_ATTESTATION_TTL_SECONDS,
    nonce: str | None = None,
) -> dict[str, Any] | None:
    """Issue an HMAC attestation only when a sufficiently strong secret is configured."""

    if purpose not in {EXTERNAL_HOLDOUT_PURPOSE, REFERENCE_COMPLETENESS_PURPOSE}:
        raise ValueError(f"unsupported evidence attestation purpose: {purpose}")
    if ttl_seconds <= 0 or ttl_seconds > MAX_ATTESTATION_TTL_SECONDS:
        raise ValueError(
            f"attestation ttl_seconds must be within 1..{MAX_ATTESTATION_TTL_SECONDS}"
        )
    configuration = attestation_configuration_status()
    if not configuration["configured"]:
        return None
    secret = os.environ[ATTESTATION_SECRET_ENV].encode("utf-8")
    issued_at = _as_utc(now or datetime.now(timezone.utc))
    expires_at = issued_at + timedelta(seconds=ttl_seconds)
    envelope = {
        "version": ATTESTATION_VERSION,
        "algorithm": ATTESTATION_ALGORITHM,
        "purpose": purpose,
        "key_id": configuration["key_id"],
        "issued_at": _format_utc(issued_at),
        "expires_at": _format_utc(expires_at),
        "nonce": nonce or secrets.token_hex(16),
        "payload_sha256": stable_payload_sha256(payload),
    }
    signature = hmac.new(
        secret,
        _attestation_message(envelope),
        hashlib.sha256,
    ).hexdigest()
    return {**envelope, "signature": signature}


def verify_evidence_attestation(
    payload: Any,
    attestation: EvidenceAttestation | dict[str, Any] | None,
    *,
    purpose: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Verify payload binding, trust configuration, purpose and bounded validity."""

    if attestation is None:
        return {
            "status": "unsigned",
            "verified": False,
            "purpose": purpose,
            "evidence_use": "informational_only",
        }
    values = (
        attestation.model_dump(mode="json")
        if isinstance(attestation, EvidenceAttestation)
        else dict(attestation)
    )
    configuration = attestation_configuration_status()
    if not configuration["configured"]:
        return {
            "status": configuration["status"],
            "verified": False,
            "purpose": purpose,
            "key_id": values.get("key_id"),
            "evidence_use": "informational_only",
        }
    if values.get("version") != ATTESTATION_VERSION or values.get("algorithm") != ATTESTATION_ALGORITHM:
        return _failed_attestation("unsupported_contract", purpose, values)
    if values.get("purpose") != purpose:
        return _failed_attestation("purpose_mismatch", purpose, values)
    if not hmac.compare_digest(str(values.get("key_id") or ""), str(configuration["key_id"])):
        return _failed_attestation("unknown_key", purpose, values)

    actual_payload_sha256 = stable_payload_sha256(payload)
    supplied_payload_sha256 = str(values.get("payload_sha256") or "")
    if not hmac.compare_digest(actual_payload_sha256, supplied_payload_sha256):
        return _failed_attestation("payload_tampered", purpose, values)

    signed_envelope = {key: value for key, value in values.items() if key != "signature"}
    expected_signature = hmac.new(
        os.environ[ATTESTATION_SECRET_ENV].encode("utf-8"),
        _attestation_message(signed_envelope),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_signature, str(values.get("signature") or "")):
        return _failed_attestation("invalid_signature", purpose, values)

    try:
        issued_at = _parse_utc(values.get("issued_at"))
        expires_at = _parse_utc(values.get("expires_at"))
    except (TypeError, ValueError):
        return _failed_attestation("invalid_time_window", purpose, values)
    current = _as_utc(now or datetime.now(timezone.utc))
    if expires_at <= issued_at or (expires_at - issued_at).total_seconds() > MAX_ATTESTATION_TTL_SECONDS:
        return _failed_attestation("invalid_time_window", purpose, values)
    if issued_at > current + timedelta(seconds=ATTESTATION_CLOCK_SKEW_SECONDS):
        return _failed_attestation("issued_in_future", purpose, values)
    if expires_at <= current:
        return _failed_attestation("expired_or_stale_replay", purpose, values)
    return {
        "status": "verified",
        "verified": True,
        "purpose": purpose,
        "key_id": values.get("key_id"),
        "payload_sha256": actual_payload_sha256,
        "issued_at": values.get("issued_at"),
        "expires_at": values.get("expires_at"),
        "evidence_use": "scientific_gate_input",
    }


def canonical_external_validation_payload(
    manifest: ExternalValidationManifest | dict[str, Any],
) -> dict[str, Any]:
    values = manifest.model_dump(mode="json") if isinstance(manifest, ExternalValidationManifest) else dict(manifest)
    values.pop("attestation", None)
    return ExternalValidationManifest(**values).model_dump(mode="json", exclude={"attestation"})


def attest_external_validation_manifest(
    manifest: ExternalValidationManifest | dict[str, Any],
    *,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_ATTESTATION_TTL_SECONDS,
    nonce: str | None = None,
) -> dict[str, Any] | None:
    return issue_evidence_attestation(
        canonical_external_validation_payload(manifest),
        purpose=EXTERNAL_HOLDOUT_PURPOSE,
        now=now,
        ttl_seconds=ttl_seconds,
        nonce=nonce,
    )


def reference_completeness_attestation_payload(
    record: SequenceRecord,
    *,
    candidate_species_in_hits: int,
) -> dict[str, Any]:
    if record.reference_completeness is None:
        raise ValueError("reference completeness evidence is required for attestation")
    evidence = record.reference_completeness.model_dump(mode="json", exclude={"attestation"})
    hit_payload = [hit.model_dump(mode="json") for hit in record.hits]
    return {
        # One trusted audit envelope binds the full externally supplied
        # scientific evidence bundle. A valid completeness signature therefore
        # cannot be replayed after changing gap, k-mer or chimera/QC evidence.
        "evidence": {
            "reference_completeness": ReferenceCompletenessEvidence(**evidence).model_dump(
                mode="json", exclude={"attestation"}
            ),
            "barcode_gap": record.barcode_gap.model_dump(mode="json") if record.barcode_gap else None,
            "diagnostic_kmers": record.diagnostic.model_dump(mode="json") if record.diagnostic else None,
            "sequence_qc": record.sequence_qc.model_dump(mode="json") if record.sequence_qc else None,
        },
        "subject": {
            "sequence_id": record.sequence_id,
            "sequence_sha256": hashlib.sha256(record.sequence.encode("utf-8")).hexdigest(),
            "reference_hit_set_sha256": stable_payload_sha256(hit_payload),
            "candidate_species_in_hits": candidate_species_in_hits,
        },
    }


def attest_reference_completeness(
    record: SequenceRecord,
    *,
    candidate_species_in_hits: int,
    now: datetime | None = None,
    ttl_seconds: int = DEFAULT_ATTESTATION_TTL_SECONDS,
    nonce: str | None = None,
) -> dict[str, Any] | None:
    return issue_evidence_attestation(
        reference_completeness_attestation_payload(
            record,
            candidate_species_in_hits=candidate_species_in_hits,
        ),
        purpose=REFERENCE_COMPLETENESS_PURPOSE,
        now=now,
        ttl_seconds=ttl_seconds,
        nonce=nonce,
    )


def _attestation_message(envelope: dict[str, Any]) -> bytes:
    domain_separated = {
        "domain": "ecogenesis.scientific-evidence.attestation",
        "envelope": envelope,
    }
    compact = json.dumps(domain_separated, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return compact.encode("utf-8")


def _failed_attestation(status: str, purpose: str, values: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": status,
        "verified": False,
        "purpose": purpose,
        "key_id": values.get("key_id"),
        "evidence_use": "informational_only",
    }


def _parse_utc(value: Any) -> datetime:
    text = str(value or "").strip()
    parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("attestation timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("attestation datetime must include a timezone")
    return value.astimezone(timezone.utc)


def _format_utc(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def reverse_complement(sequence: str) -> str:
    return str(sequence or "").upper().translate(COMPLEMENT)[::-1]


def canonical_kmer(kmer: str) -> str:
    clean = str(kmer or "").upper()
    reverse = reverse_complement(clean)
    return min(clean, reverse)


def canonical_kmers(sequence: str, k: int, *, minimum_entropy: float = 0.55) -> set[str]:
    clean = str(sequence or "").upper()
    if k < 1 or len(clean) < k:
        return set()
    result = set()
    for index in range(len(clean) - k + 1):
        window = clean[index : index + k]
        if set(window) - set("ACGT"):
            continue
        if normalized_shannon_entropy(window) < minimum_entropy:
            continue
        result.add(canonical_kmer(window))
    return result


def normalized_shannon_entropy(sequence: str) -> float:
    clean = [base for base in str(sequence or "").upper() if base in "ACGT"]
    if not clean:
        return 0.0
    counts = Counter(clean)
    total = len(clean)
    entropy = -sum((count / total) * math.log2(count / total) for count in counts.values())
    return entropy / 2.0


def longest_homopolymer(sequence: str) -> int:
    longest = 0
    current = 0
    previous = None
    for base in str(sequence or "").upper():
        if base == previous:
            current += 1
        else:
            previous = base
            current = 1
        longest = max(longest, current)
    return longest


def global_alignment_distance(first: str, second: str) -> dict[str, Any]:
    """Return an orientation-aware global edit alignment p-distance.

    The dynamic program treats substitutions and indels as one difference, excludes
    ambiguous IUPAC/IUPAC columns from the p-distance denominator, and evaluates both
    orientations of the second sequence.  It is deliberately bounded: oversized
    alignments return ``not_evaluated`` instead of silently reverting to positional
    comparison.
    """

    forward = _global_alignment_distance_one_orientation(first, second)
    reverse = _global_alignment_distance_one_orientation(first, reverse_complement(second))
    evaluated = [item for item in (forward, reverse) if item["status"] == "pass"]
    if not evaluated:
        return {
            "status": "not_evaluated",
            "distance": None,
            "aligned_sites": 0,
            "comparable_sites": 0,
            "gap_count": 0,
            "orientation": "unknown",
            "method": "needleman_wunsch_edit_p_distance_v1",
            "reason": forward.get("reason") or reverse.get("reason"),
        }
    selected_orientation, selected = min(
        (("forward", forward), ("reverse", reverse)),
        key=lambda pair: (
            1 if pair[1]["status"] != "pass" else 0,
            pair[1].get("distance") if pair[1].get("distance") is not None else 1.0,
            -pair[1].get("comparable_sites", 0),
            pair[1].get("gap_count", 0),
        ),
    )
    best = dict(selected)
    best["orientation"] = selected_orientation
    return best


def _global_alignment_distance_one_orientation(first: str, second: str) -> dict[str, Any]:
    left = str(first or "").upper().replace("-", "")
    right = str(second or "").upper().replace("-", "")
    if not left or not right:
        return {
            "status": "not_evaluated",
            "distance": None,
            "reason": "empty_sequence",
        }
    if len(left) * len(right) > MAX_ALIGNMENT_CELLS:
        return {
            "status": "not_evaluated",
            "distance": None,
            "reason": f"alignment_exceeds_{MAX_ALIGNMENT_CELLS}_cell_safety_limit",
        }

    # tuple: edit cost, aligned columns, comparable columns, differences, gaps
    previous: list[tuple[int, int, int, int, int]] = [
        (index, index, 0, index, index) for index in range(len(right) + 1)
    ]
    for row_index, left_base in enumerate(left, start=1):
        current: list[tuple[int, int, int, int, int]] = [(row_index, row_index, 0, row_index, row_index)]
        for column_index, right_base in enumerate(right, start=1):
            diagonal = previous[column_index - 1]
            canonical_pair = left_base in "ACGT" and right_base in "ACGT"
            compatible = bool(IUPAC_BASES.get(left_base, frozenset()) & IUPAC_BASES.get(right_base, frozenset()))
            substitution = 0 if compatible else 1
            diagonal_candidate = (
                diagonal[0] + substitution,
                diagonal[1] + 1,
                diagonal[2] + (1 if canonical_pair else 0),
                diagonal[3] + (substitution if canonical_pair else 0),
                diagonal[4],
            )
            up = previous[column_index]
            up_candidate = (up[0] + 1, up[1] + 1, up[2], up[3] + 1, up[4] + 1)
            left_cell = current[column_index - 1]
            left_candidate = (
                left_cell[0] + 1,
                left_cell[1] + 1,
                left_cell[2],
                left_cell[3] + 1,
                left_cell[4] + 1,
            )
            current.append(
                min(
                    (diagonal_candidate, up_candidate, left_candidate),
                    key=lambda item: (item[0], -item[2], item[4], item[1]),
                )
            )
        previous = current

    _cost, columns, comparable, differences, gaps = previous[-1]
    denominator = comparable + gaps
    return {
        "status": "pass" if denominator else "not_evaluated",
        "distance": round(differences / denominator, 8) if denominator else None,
        "aligned_sites": columns,
        "comparable_sites": comparable,
        "gap_count": gaps,
        "orientation": "forward",
        "method": "needleman_wunsch_edit_p_distance_v1",
        "reason": None if denominator else "no_comparable_sites",
    }


def evaluate_sequence_qc(record: SequenceRecord, marker_profile: dict[str, Any]) -> dict[str, Any]:
    sequence = record.sequence.upper()
    ambiguity_count = sum(base not in "ACGT" for base in sequence)
    ambiguity_fraction = ambiguity_count / max(len(sequence), 1)
    entropy = normalized_shannon_entropy(sequence)
    homopolymer = longest_homopolymer(sequence)
    low_complexity_pass = entropy >= MIN_NORMALIZED_SHANNON_ENTROPY and homopolymer <= MAX_HOMOPOLYMER_RUN
    ambiguity_pass = ambiguity_fraction <= MAX_AMBIGUOUS_BASE_FRACTION

    coding_marker = bool(marker_profile.get("coding_marker"))
    orf = evaluate_coding_orf(sequence, marker_profile) if coding_marker else {
        "status": "not_applicable",
        "pass": True,
        "orientation": None,
        "frame": None,
        "internal_stop_count": None,
        "codon_count": None,
        "genetic_code": None,
    }
    supplied = record.sequence_qc
    chimera_status = supplied.chimera_status if supplied else "not_evaluated"
    evidence_bundle_trust = verify_record_evidence_bundle(record)
    chimera_pass = chimera_status == "pass" and evidence_bundle_trust["verified"]
    blockers = []
    if not ambiguity_pass:
        blockers.append(
            f"sequence QC failed: ambiguous base fraction {ambiguity_fraction:.4f} exceeds {MAX_AMBIGUOUS_BASE_FRACTION:.4f}"
        )
    if not low_complexity_pass:
        blockers.append(
            "sequence QC failed: low-complexity sequence "
            f"(normalized entropy={entropy:.4f}, longest homopolymer={homopolymer})"
        )
    if not orf["pass"]:
        blockers.append(
            "sequence QC failed: coding-marker ORF check found no stop-free reading frame "
            f"({orf['internal_stop_count']} internal stops in best frame)"
        )
    if not chimera_pass:
        blockers.append(
            "sequence QC failed: chimera check "
            f"{chimera_status}; evidence-bundle trust={evidence_bundle_trust['status']}"
        )
    return {
        "status": "pass" if not blockers else "fail",
        "gate_pass": not blockers,
        "ambiguity_base_count": ambiguity_count,
        "ambiguity_fraction": round(ambiguity_fraction, 8),
        "ambiguity_gate_pass": ambiguity_pass,
        "normalized_shannon_entropy": round(entropy, 8),
        "longest_homopolymer": homopolymer,
        "low_complexity_gate_pass": low_complexity_pass,
        "reverse_complement_checked": True,
        "orf": orf,
        "chimera_status": chimera_status,
        "chimera_method": supplied.chimera_method if supplied else None,
        "chimera_reference_sha256": supplied.chimera_reference_sha256 if supplied else None,
        "trust_status": evidence_bundle_trust["status"],
        "evidence_use": evidence_bundle_trust["evidence_use"],
        "attestation_verification": evidence_bundle_trust,
        "blockers": blockers,
    }


def verify_record_evidence_bundle(record: SequenceRecord) -> dict[str, Any]:
    evidence = record.reference_completeness
    if evidence is None:
        return {
            "status": "missing",
            "verified": False,
            "purpose": REFERENCE_COMPLETENESS_PURPOSE,
            "evidence_use": "informational_only",
        }
    candidate_species = len(
        {
            hit.taxon
            for hit in record.hits
            if str(hit.rank or "").strip().lower() == "species"
        }
    )
    return verify_evidence_attestation(
        reference_completeness_attestation_payload(
            record,
            candidate_species_in_hits=candidate_species,
        ),
        evidence.attestation,
        purpose=REFERENCE_COMPLETENESS_PURPOSE,
    )


def evaluate_coding_orf(sequence: str, marker_profile: dict[str, Any]) -> dict[str, Any]:
    marker_family = str(marker_profile.get("marker_family") or "").lower()
    if marker_family == "coi":
        stops = {"TAA", "TAG"}
        genetic_code = "invertebrate_mitochondrial_stop_set"
    else:
        stops = {"TAA", "TAG", "TGA"}
        genetic_code = "standard_stop_set"
    candidates = []
    for orientation, oriented in (("forward", sequence), ("reverse", reverse_complement(sequence))):
        for frame in range(3):
            codons = [oriented[index : index + 3] for index in range(frame, len(oriented) - 2, 3)]
            internal = codons[:-1] if codons else []
            stop_count = sum(codon in stops for codon in internal)
            candidates.append((stop_count, -len(codons), orientation, frame + 1, len(codons)))
    best = min(candidates) if candidates else (1, 0, "unknown", 0, 0)
    stop_count, negative_codons, orientation, frame, codon_count = best
    minimum_codons = max(20, int((marker_profile.get("min_aligned_length") or 60) / 3 * 0.5))
    passed = stop_count == 0 and codon_count >= minimum_codons
    return {
        "status": "pass" if passed else "fail",
        "pass": passed,
        "orientation": orientation,
        "frame": frame,
        "internal_stop_count": stop_count,
        "codon_count": codon_count,
        "minimum_codon_count": minimum_codons,
        "genetic_code": genetic_code,
    }


def evaluate_reference_completeness(record: SequenceRecord, *, candidate_species_in_hits: int) -> dict[str, Any]:
    evidence = record.reference_completeness
    if evidence is None:
        return {
            "status": "missing",
            "rci2_status": "not_measured_without_external_reference_audit",
            "gate_pass": False,
            "trust_status": "missing",
            "evidence_use": "informational_only",
            "candidate_species_in_hit_table": candidate_species_in_hits,
            "blockers": ["reference completeness audit is missing"],
            "claim_scope": "bounded_to_supplied_reference_context_not_absolute_species_truth",
        }
    values = evidence.model_dump(mode="json")
    attestation_verification = verify_evidence_attestation(
        reference_completeness_attestation_payload(
            record,
            candidate_species_in_hits=candidate_species_in_hits,
        ),
        evidence.attestation,
        purpose=REFERENCE_COMPLETENESS_PURPOSE,
    )
    expected = values.get("close_relative_taxa_expected")
    represented = values.get("close_relative_taxa_represented")
    checks = {
        "server_attestation_verified": attestation_verification["verified"],
        "externally_audited_status": values.get("status") == "audited_sufficient",
        "minimum_target_references": (values.get("target_taxon_reference_count") or 0) >= MIN_TARGET_REFERENCE_SPECIMENS,
        "minimum_target_specimens": (values.get("target_taxon_specimen_count") or 0) >= MIN_TARGET_REFERENCE_SPECIMENS,
        "close_relative_universe_declared": expected is not None and expected >= MIN_CLOSE_RELATIVE_TAXA,
        "close_relative_universe_covered": expected is not None and represented is not None and represented >= expected,
        "negative_taxa_depth": (values.get("negative_reference_taxa_count") or 0) >= MIN_CLOSE_RELATIVE_TAXA,
        "negative_sequence_depth": (values.get("negative_reference_sequence_count") or 0) >= MIN_NEGATIVE_REFERENCE_SEQUENCES,
        "geographic_depth": (values.get("geographic_regions_count") or 0) >= MIN_GEOGRAPHIC_REGIONS,
        "audit_source_supplied": bool(str(values.get("audit_source") or "").strip()),
        "audit_checksum_supplied": bool(values.get("audit_sha256")),
    }
    failed = [name for name, passed in checks.items() if not passed]
    coverage = (represented / expected) if expected and represented is not None else None
    blockers = [f"reference completeness failed: {name}" for name in failed]
    if not attestation_verification["verified"]:
        blockers.insert(
            0,
            "reference completeness attestation blocked scientific use: "
            f"{attestation_verification['status']}",
        )
    return {
        **values,
        "status": "pass" if not failed else "fail",
        "rci2_status": (
            "audited_sufficient"
            if not failed
            else (
                "informational_unverified_reference_audit"
                if not attestation_verification["verified"]
                else "external_reference_audit_incomplete"
            )
        ),
        "gate_pass": not failed,
        "trust_status": attestation_verification["status"],
        "evidence_use": attestation_verification["evidence_use"],
        "attestation_verification": attestation_verification,
        "checks": checks,
        "failed_checks": failed,
        "close_relative_coverage": round(coverage, 6) if coverage is not None else None,
        "candidate_species_in_hit_table": candidate_species_in_hits,
        "blockers": blockers,
        "claim_scope": "bounded_to_audited_reference_context_not_absolute_species_truth",
    }


def _is_finite_number(value: Any) -> bool:
    """Return true only for real JSON-style numbers usable by a release gate."""

    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _is_probability(value: Any) -> bool:
    return _is_finite_number(value) and 0.0 <= float(value) <= 1.0


def _holdout_metric_bundle_validation(metrics: Any) -> dict[str, bool]:
    """Validate one overall or per-stratum bundle without coercing bad values."""

    is_mapping = isinstance(metrics, Mapping)
    required_present = is_mapping and all(key in metrics for key in REQUIRED_HOLDOUT_METRICS)
    finite_numeric = required_present and all(
        _is_finite_number(metrics[key]) for key in REQUIRED_HOLDOUT_METRICS
    )
    in_range = finite_numeric and all(
        _is_probability(metrics[key]) for key in REQUIRED_HOLDOUT_METRICS
    )
    confidence_intervals_valid = in_range and all(
        float(metrics[low]) <= float(metrics[estimate]) <= float(metrics[high])
        for estimate, low, high in HOLDOUT_CONFIDENCE_INTERVALS
    )
    return {
        "required_present": bool(required_present),
        "finite_numeric": bool(finite_numeric),
        "in_range": bool(in_range),
        "confidence_intervals_valid": bool(confidence_intervals_valid),
    }


def _required_strata_validation(strata: Any) -> dict[str, bool]:
    is_mapping = isinstance(strata, Mapping)
    required_present = is_mapping and all(
        isinstance(strata.get(name), Mapping) and bool(strata[name])
        for name in REQUIRED_HOLDOUT_STRATA
    )
    bundles = []
    if is_mapping:
        for name in REQUIRED_HOLDOUT_STRATA:
            groups = strata.get(name)
            if not isinstance(groups, Mapping):
                continue
            bundles.extend(
                _holdout_metric_bundle_validation(metrics)
                for metrics in groups.values()
            )
    return {
        "required_present": bool(required_present),
        "complete": bool(
            required_present
            and bundles
            and all(bundle["required_present"] for bundle in bundles)
        ),
        "finite_numeric": bool(
            required_present
            and bundles
            and all(bundle["finite_numeric"] for bundle in bundles)
        ),
        "in_range": bool(
            required_present
            and bundles
            and all(bundle["in_range"] for bundle in bundles)
        ),
        "confidence_intervals_valid": bool(
            required_present
            and bundles
            and all(bundle["confidence_intervals_valid"] for bundle in bundles)
        ),
    }


def _stratum_category_coverage(
    strata: Any,
    *,
    stratum: str,
    expected: Any,
) -> bool:
    if not isinstance(strata, Mapping) or not isinstance(strata.get(stratum), Mapping):
        return False
    expected_names = {str(value) for value in (expected or []) if str(value).strip()}
    actual_names = {str(value) for value in strata[stratum]}
    return bool(expected_names) and expected_names.issubset(actual_names)


def scientific_release_gate(request: BarcodeCompilerRequest) -> dict[str, Any]:
    manifest = request.external_validation_manifest
    requirements = {
        "external_dataset_provenance": "source, DOI/URL, license and SHA-256",
        "independent_holdout": "holdout labels and specimens independent from threshold calibration",
        "no_fixture_cloning": "unique_case_count must equal record_count; demo-derived records are forbidden",
        "minimum_sample_size": MIN_EXTERNAL_HOLDOUT_RECORDS,
        "coverage": "at least two marker families and two taxonomic groups",
        "required_metrics": list(REQUIRED_HOLDOUT_METRICS),
        "metric_validity": (
            "every required metric must be a finite number in [0, 1]; each confidence interval must be "
            "ordered and contain its estimate"
        ),
        "baseline": "finite naive top-hit precision and false-species rate in [0, 1]",
        "strata": (
            "complete valid metric bundles for every supplied marker, taxonomic group and "
            "reference-completeness stratum"
        ),
        "trusted_attestation": {
            "version": ATTESTATION_VERSION,
            "algorithm": ATTESTATION_ALGORITHM,
            "secret_configuration": ATTESTATION_SECRET_ENV,
            "secret_minimum_bytes": MIN_ATTESTATION_SECRET_BYTES,
            "maximum_ttl_seconds": MAX_ATTESTATION_TTL_SECONDS,
            "unsigned_or_unverifiable_policy": "informational_only_and_release_blocked",
        },
    }
    if manifest is None:
        return {
            "status": "blocked",
            "release_eligible": False,
            "trust_status": "missing",
            "evidence_use": "informational_only",
            "blockers": ["independent external holdout validation manifest is missing"],
            "contract": requirements,
        }
    values = manifest.model_dump(mode="json")
    attestation_verification = verify_evidence_attestation(
        canonical_external_validation_payload(manifest),
        manifest.attestation,
        purpose=EXTERNAL_HOLDOUT_PURPOSE,
    )
    metrics = values.get("metrics") or {}
    baseline = values.get("baseline_metrics") or {}
    strata = values.get("strata") or {}
    overall_metric_validation = _holdout_metric_bundle_validation(metrics)
    strata_validation = _required_strata_validation(strata)
    baseline_present = isinstance(baseline, Mapping) and all(
        key in baseline for key in REQUIRED_BASELINE_METRICS
    )
    baseline_finite_numeric = baseline_present and all(
        _is_finite_number(baseline[key]) for key in REQUIRED_BASELINE_METRICS
    )
    baseline_in_range = baseline_finite_numeric and all(
        _is_probability(baseline[key]) for key in REQUIRED_BASELINE_METRICS
    )
    false_species_rate = metrics.get("false_species_rule_pass_rate")
    species_precision = metrics.get("species_precision")
    naive_false_species_rate = baseline.get("naive_top_hit_false_species_rate")
    checks = {
        "server_attestation_verified": attestation_verification["verified"],
        "compiler_contract_bound": values.get("compiler_contract_sha256") == compiler_contract_sha256(request),
        "holdout": bool(values.get("holdout")),
        "thresholds_frozen_before_holdout": bool(values.get("thresholds_frozen_before_holdout")),
        "independent_ground_truth": bool(values.get("ground_truth_independent")),
        "specimen_backed": bool(values.get("specimen_backed")),
        "not_demo_fixture_derived": not bool(values.get("generated_from_demo_fixtures")),
        "minimum_records": int(values.get("record_count") or 0) >= MIN_EXTERNAL_HOLDOUT_RECORDS,
        "all_cases_unique": values.get("unique_case_count") == values.get("record_count"),
        "multiple_marker_families": len(set(values.get("marker_families") or [])) >= 2,
        "multiple_taxonomic_groups": len(set(values.get("taxonomic_groups") or [])) >= 2,
        "required_metrics_present": overall_metric_validation["required_present"],
        "required_metrics_finite_numeric": overall_metric_validation["finite_numeric"],
        "required_metrics_in_range": overall_metric_validation["in_range"],
        "required_confidence_intervals_valid": overall_metric_validation[
            "confidence_intervals_valid"
        ],
        "naive_baseline_present": bool(baseline_present),
        "naive_baseline_finite_numeric": bool(baseline_finite_numeric),
        "naive_baseline_in_range": bool(baseline_in_range),
        "false_species_rate_noninferior_to_naive": bool(
            _is_probability(false_species_rate)
            and _is_probability(naive_false_species_rate)
            and float(false_species_rate) <= float(naive_false_species_rate)
        ),
        "required_strata_present": strata_validation["required_present"],
        "required_strata_complete": strata_validation["complete"],
        "required_strata_finite_numeric": strata_validation["finite_numeric"],
        "required_strata_metrics_in_range": strata_validation["in_range"],
        "required_strata_confidence_intervals_valid": strata_validation[
            "confidence_intervals_valid"
        ],
        "marker_strata_cover_manifest": _stratum_category_coverage(
            strata,
            stratum="marker",
            expected=values.get("marker_families"),
        ),
        "taxonomic_group_strata_cover_manifest": _stratum_category_coverage(
            strata,
            stratum="taxonomic_group",
            expected=values.get("taxonomic_groups"),
        ),
        "false_species_rate_within_limit": bool(
            _is_probability(false_species_rate) and float(false_species_rate) <= 0.01
        ),
        "species_precision_within_limit": bool(
            _is_probability(species_precision) and float(species_precision) >= 0.95
        ),
        "false_species_ci_upper_within_limit": bool(
            _is_probability(metrics.get("false_species_rule_pass_rate_ci_high"))
            and float(metrics["false_species_rule_pass_rate_ci_high"]) <= 0.01
        ),
        "species_precision_ci_lower_within_limit": bool(
            _is_probability(metrics.get("species_precision_ci_low"))
            and float(metrics["species_precision_ci_low"]) >= 0.95
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    blockers = [f"external validation contract failed: {name}" for name in failed]
    if not attestation_verification["verified"]:
        blockers.insert(
            0,
            "external validation attestation blocked scientific release: "
            f"{attestation_verification['status']}",
        )
    return {
        "status": "pass" if not failed else "blocked",
        "release_eligible": not failed,
        "trust_status": attestation_verification["status"],
        "evidence_use": attestation_verification["evidence_use"],
        "attestation_verification": attestation_verification,
        "checks": checks,
        "blockers": blockers,
        "contract": requirements,
        "manifest": values,
    }


def intersection_all(sets: Iterable[set[str]]) -> set[str]:
    iterator = iter(sets)
    try:
        result = set(next(iterator))
    except StopIteration:
        return set()
    for values in iterator:
        result.intersection_update(values)
    return result
