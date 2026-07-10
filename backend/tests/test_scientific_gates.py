from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.barcode.benchmark import (
    benchmark_contract,
    genus_for_decision,
    holdout_metrics,
    independent_case_fingerprint,
    naive_baseline_metrics,
    stratified_metrics,
    wilson_interval,
)
from app.barcode.demo import GOOD_RECORD, request_with_records
from app.barcode.schemas import BarcodeCompilerRequest, ExternalValidationManifest, SequenceRecord
from app.barcode.scientific_gates import (
    ATTESTATION_KEY_ID_ENV,
    ATTESTATION_SECRET_ENV,
    attest_external_validation_manifest,
    attest_reference_completeness,
    canonical_kmer,
    compiler_contract_sha256,
    evaluate_reference_completeness,
    evaluate_sequence_qc,
    global_alignment_distance,
    reverse_complement,
    scientific_release_gate,
)
from app.barcode.search_backend import reference_evidence_from_sequences


TEST_ATTESTATION_SECRET = "pytest-only-attestation-secret-32-bytes-minimum"


def external_release_request(monkeypatch, *, signed: bool = True, issued_at: datetime | None = None) -> tuple[BarcodeCompilerRequest, dict]:
    monkeypatch.setenv(ATTESTATION_SECRET_ENV, TEST_ATTESTATION_SECRET)
    monkeypatch.setenv(ATTESTATION_KEY_ID_ENV, "pytest-scientific-gate-key")
    base = BarcodeCompilerRequest(**request_with_records("attestation contract test", [GOOD_RECORD]))
    metric_values = {
        "species_precision": 1.0,
        "species_precision_ci_low": 0.96,
        "species_precision_ci_high": 1.0,
        "species_recall": 0.98,
        "species_recall_ci_low": 0.95,
        "species_recall_ci_high": 1.0,
        "genus_precision": 1.0,
        "abstention_rate": 0.02,
        "false_species_rule_pass_rate": 0.0,
        "false_species_rule_pass_rate_ci_low": 0.0,
        "false_species_rule_pass_rate_ci_high": 0.005,
    }
    manifest = {
        "dataset_id": "urn:pytest:independent-holdout",
        "dataset_version": "2026-07-10",
        "source": "independent pytest fixture issuer",
        "doi_or_url": "https://example.org/independent-holdout",
        "license": "CC-BY-4.0",
        "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "holdout": True,
        "thresholds_frozen_before_holdout": True,
        "ground_truth_independent": True,
        "specimen_backed": True,
        "generated_from_demo_fixtures": False,
        "record_count": 100,
        "unique_case_count": 100,
        "marker_families": ["COI", "16S"],
        "taxonomic_groups": ["Diptera", "Coleoptera"],
        "evaluated_at": "2026-07-10T10:00:00Z",
        "harness_version": "ecogenesis-independent-holdout-v1",
        "compiler_contract_sha256": compiler_contract_sha256(base),
        "metrics": metric_values,
        "baseline_metrics": {
            "naive_top_hit_species_precision": 0.8,
            "naive_top_hit_false_species_rate": 0.1,
        },
        "strata": {
            "marker": {"COI": deepcopy(metric_values), "16S": deepcopy(metric_values)},
            "taxonomic_group": {
                "Diptera": deepcopy(metric_values),
                "Coleoptera": deepcopy(metric_values),
            },
            "reference_completeness": {"pass": deepcopy(metric_values)},
        },
    }
    if signed:
        manifest["attestation"] = attest_external_validation_manifest(
            manifest,
            now=issued_at,
            ttl_seconds=60 if issued_at is not None else 3600,
            nonce="0123456789abcdef0123456789abcdef",
        )
    request = BarcodeCompilerRequest(**{**base.model_dump(), "external_validation_manifest": manifest})
    return request, manifest


def request_with_resigned_manifest(
    request: BarcodeCompilerRequest,
    manifest: dict,
) -> BarcodeCompilerRequest:
    candidate = deepcopy(manifest)
    candidate.pop("attestation", None)
    candidate["attestation"] = attest_external_validation_manifest(candidate)
    assert candidate["attestation"] is not None
    return BarcodeCompilerRequest(**{
        **request.model_dump(exclude={"external_validation_manifest"}),
        "external_validation_manifest": candidate,
    })


def server_attested_reference_record(monkeypatch) -> SequenceRecord:
    monkeypatch.setenv(ATTESTATION_SECRET_ENV, TEST_ATTESTATION_SECRET)
    monkeypatch.setenv(ATTESTATION_KEY_ID_ENV, "pytest-scientific-gate-key")
    payload = deepcopy(GOOD_RECORD)
    payload["reference_completeness"].update({
        "status": "audited_sufficient",
        "audit_source": "pytest server-verified reference inventory",
        "audit_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
    })
    unsigned = SequenceRecord(**payload)
    candidate_species = len({hit.taxon for hit in unsigned.hits if str(hit.rank).lower() == "species"})
    payload["reference_completeness"]["attestation"] = attest_reference_completeness(
        unsigned,
        candidate_species_in_hits=candidate_species,
        nonce="abcdef0123456789abcdef0123456789",
    )
    return SequenceRecord(**payload)


def test_global_alignment_distance_handles_indel_and_reverse_complement() -> None:
    indel = global_alignment_distance("ACGTACGT", "ACGTTACGT")
    reverse = global_alignment_distance("AACCGGTTACGA", reverse_complement("AACCGGTTACGA"))

    assert indel["status"] == "pass"
    assert indel["gap_count"] == 1
    assert indel["distance"] == pytest.approx(1 / 9)
    assert reverse["distance"] == 0
    assert reverse["orientation"] == "reverse"


def test_reference_evidence_blocks_singletons_and_uses_conserved_canonical_kmers() -> None:
    sequences = {
        "Taxon alpha": ["AACCGGTTAACCGGTT", "AACCGGTTAACCGGTA", "AACCGGTTAACCGGTC"],
        "Taxon beta": ["TTTTGGTTAACCAAAA"],
        "Taxon gamma": ["GGGGGGTTAACCCCCC"],
    }
    gaps, diagnostics, completeness = reference_evidence_from_sequences(sequences)

    assert gaps["Taxon beta"]["intra_max_distance"] is None
    assert gaps["Taxon beta"]["target_reference_count"] == 1
    assert diagnostics["Taxon alpha"]["canonicalized"] is True
    assert diagnostics["Taxon alpha"]["reverse_complement_checked"] is True
    assert all(item == canonical_kmer(item) for item in diagnostics["Taxon alpha"]["diagnostic_kmers"])
    assert completeness["Taxon alpha"]["status"] == "not_evaluated"


def test_benchmark_metrics_include_wilson_baseline_and_strata() -> None:
    rows = [
        {
            "truth_rank": "species",
            "abstained_from_species": False,
            "species_correct": True,
            "false_species_rule_pass": False,
            "predicted_genus": "Aedes",
            "genus_correct": True,
            "naive_top_hit_taxon": "Aedes aegypti",
            "naive_species_correct": False,
            "naive_false_species": True,
            "marker": "COI",
        },
        {
            "truth_rank": "species",
            "abstained_from_species": True,
            "species_correct": False,
            "false_species_rule_pass": False,
            "predicted_genus": "Aedes",
            "genus_correct": True,
            "naive_top_hit_taxon": "Aedes albopictus",
            "naive_species_correct": True,
            "naive_false_species": False,
            "marker": "COI",
        },
    ]

    metrics = holdout_metrics(rows)
    baseline = naive_baseline_metrics(rows)

    assert metrics["species_precision"] == 1
    assert metrics["species_recall"] == 0.5
    assert 0 <= metrics["false_species_rule_pass_rate_ci_low"] <= metrics["false_species_rule_pass_rate_ci_high"] <= 1
    assert baseline["naive_top_hit_species_precision"] == 0.5
    assert stratified_metrics(rows, "marker")["COI"]["records"] == 2
    assert wilson_interval(0, 10)[1] > 0


def test_genus_prediction_does_not_promote_an_abstained_species_candidate() -> None:
    species_candidate = {
        "candidate_taxon": {"rank": "species", "name": "Aedes albopictus"},
    }

    assert genus_for_decision({
        **species_candidate,
        "scientific_decision_state": "species-level-molecular-candidate-assay-blocked",
    }) is None
    assert genus_for_decision({
        **species_candidate,
        "scientific_decision_state": "ambiguous",
    }) is None
    assert genus_for_decision({
        **species_candidate,
        "scientific_decision_state": "species-rule-pass",
    }) == "Aedes"
    assert genus_for_decision({
        "candidate_taxon": {"rank": "genus", "name": "Aedes"},
        "scientific_decision_state": "genus-safe",
    }) == "Aedes"


def test_case_fingerprint_detects_id_only_fixture_clones() -> None:
    first = {
        "case_id": "one",
        "specimen_id": "voucher-one",
        "ground_truth": {"taxon": "Aedes albopictus", "rank": "species", "source_id": "voucher"},
        "compiler_record": {"sequence_id": "one", "sequence": "ACGT", "metadata": {"occurrenceID": "one"}},
    }
    second = deepcopy(first)
    second["case_id"] = "two"
    second["specimen_id"] = "voucher-two"
    second["compiler_record"]["sequence_id"] = "two"
    second["compiler_record"]["metadata"]["occurrenceID"] = "two"

    assert independent_case_fingerprint(first) == independent_case_fingerprint(second)


def test_external_holdout_requires_and_accepts_server_verified_attestation(monkeypatch) -> None:
    request, _manifest = external_release_request(monkeypatch)

    gate = scientific_release_gate(request)

    assert gate["status"] == "pass"
    assert gate["release_eligible"] is True
    assert gate["trust_status"] == "verified"
    assert gate["attestation_verification"]["verified"] is True
    assert gate["checks"]["server_attestation_verified"] is True
    assert gate["checks"]["compiler_contract_bound"] is True


@pytest.mark.parametrize(
    ("field", "value", "failed_check"),
    [
        ("species_recall", None, "required_metrics_finite_numeric"),
        ("species_recall", 1.01, "required_metrics_in_range"),
        ("species_recall_ci_low", 0.99, "required_confidence_intervals_valid"),
        ("species_recall_ci_high", 0.97, "required_confidence_intervals_valid"),
    ],
)
def test_external_holdout_blocks_invalid_overall_metrics(
    monkeypatch,
    field: str,
    value: float | None,
    failed_check: str,
) -> None:
    request, manifest = external_release_request(monkeypatch)
    candidate = deepcopy(manifest)
    candidate["metrics"][field] = value
    invalid_request = request_with_resigned_manifest(request, candidate)

    gate = scientific_release_gate(invalid_request)

    assert gate["release_eligible"] is False
    assert gate["checks"][failed_check] is False


def test_external_holdout_blocks_missing_overall_metric(monkeypatch) -> None:
    request, manifest = external_release_request(monkeypatch)
    candidate = deepcopy(manifest)
    candidate["metrics"].pop("species_recall")
    invalid_request = request_with_resigned_manifest(request, candidate)

    gate = scientific_release_gate(invalid_request)

    assert gate["release_eligible"] is False
    assert gate["checks"]["required_metrics_present"] is False


@pytest.mark.parametrize(
    ("mutation", "failed_check"),
    [
        ("missing_metric", "required_strata_complete"),
        ("none_metric", "required_strata_finite_numeric"),
        ("out_of_range", "required_strata_metrics_in_range"),
        ("invalid_ci", "required_strata_confidence_intervals_valid"),
    ],
)
def test_external_holdout_blocks_incomplete_or_invalid_stratum_metrics(
    monkeypatch,
    mutation: str,
    failed_check: str,
) -> None:
    request, manifest = external_release_request(monkeypatch)
    candidate = deepcopy(manifest)
    metric_bundle = candidate["strata"]["marker"]["COI"]
    if mutation == "missing_metric":
        metric_bundle.pop("genus_precision")
    elif mutation == "none_metric":
        metric_bundle["genus_precision"] = None
    elif mutation == "out_of_range":
        metric_bundle["genus_precision"] = -0.01
    else:
        metric_bundle["species_recall_ci_low"] = 0.99
    invalid_request = request_with_resigned_manifest(request, candidate)

    gate = scientific_release_gate(invalid_request)

    assert gate["release_eligible"] is False
    assert gate["checks"][failed_check] is False


def test_external_holdout_strata_cover_all_declared_categories(monkeypatch) -> None:
    request, manifest = external_release_request(monkeypatch)
    candidate = deepcopy(manifest)
    candidate["strata"]["marker"].pop("16S")
    candidate["strata"]["taxonomic_group"].pop("Coleoptera")
    invalid_request = request_with_resigned_manifest(request, candidate)

    gate = scientific_release_gate(invalid_request)

    assert gate["release_eligible"] is False
    assert gate["checks"]["marker_strata_cover_manifest"] is False
    assert gate["checks"]["taxonomic_group_strata_cover_manifest"] is False


@pytest.mark.parametrize(
    ("field", "value", "failed_check"),
    [
        ("naive_top_hit_species_precision", None, "naive_baseline_finite_numeric"),
        ("naive_top_hit_false_species_rate", 1.01, "naive_baseline_in_range"),
    ],
)
def test_external_holdout_blocks_invalid_baseline_metrics(
    monkeypatch,
    field: str,
    value: float | None,
    failed_check: str,
) -> None:
    request, manifest = external_release_request(monkeypatch)
    candidate = deepcopy(manifest)
    candidate["baseline_metrics"][field] = value
    invalid_request = request_with_resigned_manifest(request, candidate)

    gate = scientific_release_gate(invalid_request)

    assert gate["release_eligible"] is False
    assert gate["checks"][failed_check] is False


@pytest.mark.parametrize(
    "bad_value",
    [float("nan"), float("inf"), float("-inf"), True, "0.98"],
)
@pytest.mark.parametrize("location", ["overall", "stratum"])
def test_external_manifest_schema_rejects_non_numeric_or_non_finite_metrics(
    monkeypatch,
    bad_value: object,
    location: str,
) -> None:
    _request, manifest = external_release_request(monkeypatch)
    candidate = deepcopy(manifest)
    candidate.pop("attestation")
    if location == "overall":
        candidate["metrics"]["species_recall"] = bad_value
    else:
        candidate["strata"]["marker"]["COI"]["species_recall"] = bad_value

    with pytest.raises(ValidationError):
        ExternalValidationManifest(**candidate)


def test_unsigned_holdout_is_informational_and_cli_issuer_needs_configured_secret(monkeypatch) -> None:
    request, manifest = external_release_request(monkeypatch, signed=False)

    gate = scientific_release_gate(request)

    assert gate["status"] == "blocked"
    assert gate["release_eligible"] is False
    assert gate["trust_status"] == "unsigned"
    assert gate["evidence_use"] == "informational_only"

    legacy_manifest = deepcopy(manifest)
    legacy_manifest.pop("compiler_contract_sha256")
    legacy_request = BarcodeCompilerRequest(**{
        **request.model_dump(exclude={"external_validation_manifest"}),
        "external_validation_manifest": legacy_manifest,
    })
    legacy_gate = scientific_release_gate(legacy_request)
    assert legacy_gate["status"] == "blocked"
    assert legacy_gate["checks"]["compiler_contract_bound"] is False

    monkeypatch.delenv(ATTESTATION_SECRET_ENV)
    assert attest_external_validation_manifest(manifest) is None
    assert benchmark_contract()["attestation"]["secret_environment_variable"] == ATTESTATION_SECRET_ENV


def test_signed_holdout_blocks_when_server_secret_is_missing(monkeypatch) -> None:
    request, _manifest = external_release_request(monkeypatch)
    monkeypatch.delenv(ATTESTATION_SECRET_ENV)

    gate = scientific_release_gate(request)

    assert gate["status"] == "blocked"
    assert gate["release_eligible"] is False
    assert gate["trust_status"] == "server_verification_not_configured"
    assert gate["evidence_use"] == "informational_only"


def test_holdout_signature_and_payload_tampering_are_rejected(monkeypatch) -> None:
    request, manifest = external_release_request(monkeypatch)
    bad_signature = deepcopy(manifest)
    signature = bad_signature["attestation"]["signature"]
    bad_signature["attestation"]["signature"] = ("0" if signature[0] != "0" else "1") + signature[1:]
    signature_request = BarcodeCompilerRequest(**{
        **request.model_dump(exclude={"external_validation_manifest"}),
        "external_validation_manifest": bad_signature,
    })
    assert scientific_release_gate(signature_request)["trust_status"] == "invalid_signature"

    tampered = deepcopy(manifest)
    tampered["metrics"]["species_precision"] = 0.5
    tampered_request = BarcodeCompilerRequest(**{
        **request.model_dump(exclude={"external_validation_manifest"}),
        "external_validation_manifest": tampered,
    })
    tampered_gate = scientific_release_gate(tampered_request)
    assert tampered_gate["trust_status"] == "payload_tampered"
    assert tampered_gate["release_eligible"] is False


def test_expired_holdout_attestation_blocks_stale_replay(monkeypatch) -> None:
    old_time = datetime.now(timezone.utc) - timedelta(hours=2)
    request, _manifest = external_release_request(monkeypatch, issued_at=old_time)

    gate = scientific_release_gate(request)

    assert gate["trust_status"] == "expired_or_stale_replay"
    assert gate["release_eligible"] is False


def test_reference_completeness_is_gate_eligible_only_when_server_attested(monkeypatch) -> None:
    record = server_attested_reference_record(monkeypatch)
    candidate_species = len({hit.taxon for hit in record.hits if str(hit.rank).lower() == "species"})

    result = evaluate_reference_completeness(
        record,
        candidate_species_in_hits=candidate_species,
    )

    assert result["status"] == "pass"
    assert result["gate_pass"] is True
    assert result["trust_status"] == "verified"
    assert result["checks"]["server_attestation_verified"] is True


def test_reference_attestation_blocks_unsigned_missing_secret_and_subject_replay(monkeypatch) -> None:
    trusted = server_attested_reference_record(monkeypatch)
    candidate_species = len({hit.taxon for hit in trusted.hits if str(hit.rank).lower() == "species"})

    unsigned_payload = trusted.model_dump(mode="json")
    unsigned_payload["reference_completeness"]["attestation"] = None
    unsigned = evaluate_reference_completeness(
        SequenceRecord(**unsigned_payload),
        candidate_species_in_hits=candidate_species,
    )
    assert unsigned["gate_pass"] is False
    assert unsigned["trust_status"] == "unsigned"
    assert unsigned["evidence_use"] == "informational_only"
    unsigned_qc = evaluate_sequence_qc(SequenceRecord(**unsigned_payload), {"coding_marker": False})
    assert unsigned_qc["gate_pass"] is False
    assert unsigned_qc["trust_status"] == "unsigned"

    copied_payload = trusted.model_dump(mode="json")
    copied_payload["sequence_id"] = "different-subject"
    copied = evaluate_reference_completeness(
        SequenceRecord(**copied_payload),
        candidate_species_in_hits=candidate_species,
    )
    assert copied["gate_pass"] is False
    assert copied["trust_status"] == "payload_tampered"

    for field, replacement in (
        ("barcode_gap", {**copied_payload["barcode_gap"], "inter_min_distance": 0.5}),
        ("sequence_qc", {**copied_payload["sequence_qc"], "chimera_method": "tampered"}),
    ):
        tampered_payload = trusted.model_dump(mode="json")
        tampered_payload[field] = replacement
        tampered = evaluate_reference_completeness(
            SequenceRecord(**tampered_payload),
            candidate_species_in_hits=candidate_species,
        )
        assert tampered["gate_pass"] is False
        assert tampered["trust_status"] == "payload_tampered"

    trusted_qc = evaluate_sequence_qc(trusted, {"coding_marker": False})
    assert trusted_qc["gate_pass"] is True
    assert trusted_qc["trust_status"] == "verified"

    monkeypatch.delenv(ATTESTATION_SECRET_ENV)
    unconfigured = evaluate_reference_completeness(
        trusted,
        candidate_species_in_hits=candidate_species,
    )
    assert unconfigured["gate_pass"] is False
    assert unconfigured["trust_status"] == "server_verification_not_configured"
