from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import re
from typing import Any
from uuid import uuid4

from .artifacts import build_barcode_artifacts
from .profiles import (
    ASSAY_PROFILES,
    MARKER_PROFILES,
    assay_gate_readiness,
    dna_extension_readiness,
    marker_profile_readiness,
)
from .schemas import BarcodeCompilerRequest, ReferenceHit, SequenceRecord
from .storage import save_barcode_artifacts, save_barcode_zip_artifact


CORE_REQUIRED_FIELDS = ["occurrenceID", "basisOfRecord", "scientificName", "eventDate"]
DNA_REQUIRED_FIELDS = ["marker", "sequenceID", "referenceDatabase", "identity", "queryCoverage", "methodOrSOP"]
CORE_RECOMMENDED_FIELDS = ["countryCode", "decimalLatitude", "decimalLongitude", "geodeticDatum", "coordinateUncertaintyInMeters"]
DATASET_METADATA_FIELDS = ["title", "description", "publishingOrganization", "type", "license", "contact", "creator", "metadataProvider"]
HIGHER_RANKS = {"family", "order", "class", "phylum", "kingdom"}
SAFE_RANK_ORDER = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]
SAFE_TAXONOMIC_STATUSES = {"species-safe", "genus-safe", "higher-rank-safe"}
NONE_TAXON = {"rank": "none", "name": "None", "taxon_key": None}


def run_barcode_compiler(request: BarcodeCompilerRequest) -> dict[str, Any]:
    run_id = uuid4().hex
    started_at = datetime.now(timezone.utc)
    reference_manifest = build_reference_manifest(request)
    decisions = [decide_record(record, request) for record in request.records]
    metrics = summarize_decisions(decisions)
    nexus = build_nexus_v3_summary(decisions, metrics)
    finished_at = datetime.now(timezone.utc)
    request_payload = request.model_dump()
    manifest_sha256 = fingerprint_request(reference_manifest)

    pack: dict[str, Any] = {
        "run": {
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "tool": "Barcode-to-GBIF Evidence Compiler",
            "ruleset_version": request.ruleset_version,
            "request_fingerprint": fingerprint_request(request_payload),
            "reference_manifest_sha256": manifest_sha256,
        },
        "summary": {
            "title": "Barcode-to-GBIF Evidence Compiler",
            "project_title": request.project_title,
            "marker": request.marker,
            "reference_database": request.reference_database,
            "method_or_sop": request.method_or_sop,
            "processed_records": metrics["processed_records"],
            "species_safe_records": metrics["species_safe_records"],
            "genus_safe_records": metrics["genus_safe_records"],
            "not_publishable_records": metrics["not_publishable_records"],
            "record_ready_records": metrics["record_ready_records"],
            "dataset_ready_records": metrics["dataset_ready_records"],
            "blocked_species_claims": metrics["blocked_species_claims"],
            "verdict": build_run_verdict(metrics),
        },
        "reference_manifest": reference_manifest,
        "source_provenance": build_source_provenance(request, reference_manifest, decisions),
        "decision_rules": decision_rules(),
        "metrics": metrics,
        "data_accounting_ledger": build_data_accounting_ledger(decisions, metrics),
        "nexus_v3": nexus,
        "hard_gate_audit": hard_gate_audit(decisions),
        "naive_top_hit_overclaims": naive_top_hit_overclaims(decisions),
        "metadata_bottlenecks": metadata_bottlenecks(decisions),
        "reference_gap_index": reference_gap_index(decisions),
        "repair_plan": repair_plan(decisions),
        "records": decisions,
        "request": request_payload,
    }
    pack["evidence_graph"] = build_evidence_graph(pack)
    artifacts = build_barcode_artifacts(pack)
    exports = save_barcode_artifacts(run_id, artifacts)
    zip_export = save_barcode_zip_artifact(run_id, artifacts)
    pack["exports"] = sorted([*exports, zip_export], key=lambda item: item["name"])
    pack["run"]["artifact_checksums"] = {item["name"]: item.get("sha256") for item in pack["exports"]}
    pack["evidence_graph"] = build_evidence_graph(pack)
    final_artifacts = build_barcode_artifacts(pack)
    save_barcode_artifacts(
        run_id,
        {
            "evidence_pack.json": final_artifacts["evidence_pack.json"],
            "run.json": final_artifacts["run.json"],
            "evidence_graph.json": final_artifacts["evidence_graph.json"],
        },
    )
    save_barcode_zip_artifact(run_id, final_artifacts)
    return pack


def decide_record(record: SequenceRecord, request: BarcodeCompilerRequest) -> dict[str, Any]:
    hits = sorted(record.hits, key=hit_sort_key, reverse=True)
    top_hit = hits[0] if hits else None
    metadata = normalized_metadata(record, request)
    sequence = record.sequence
    sequence_length = len(sequence)
    blockers: list[str] = []
    actions: list[str] = []
    marker_profile = marker_profile_readiness(request, record, top_hit)
    enrich_molecular_metadata(metadata, record, request, top_hit, marker_profile)
    assay_gate = assay_gate_readiness(request, metadata)
    dna_extension = dna_extension_readiness(metadata)

    core_missing = missing_fields(metadata, CORE_REQUIRED_FIELDS)
    dna_missing = missing_fields(metadata, DNA_REQUIRED_FIELDS)
    data_quality_blockers = metadata_quality_blockers(metadata, top_hit)
    core_pass = not core_missing and not data_quality_blockers
    dna_pass = not dna_missing
    publication_stage, publication_checks = publication_stage_for(
        metadata,
        request,
        core_pass=core_pass,
        dna_pass=dna_pass,
        assay_publication_pass=not assay_gate["assay_blockers"],
    )

    if not hits:
        blockers.append("no reference hit returned")
        actions.append("Run the sequence against a marker-appropriate reference database and attach hit metrics.")
        blockers.extend(assay_gate["assay_blockers"])
        actions.extend(assay_gate["assay_actions"])
        actions.extend(dna_extension_actions(dna_extension))
        return build_decision(
            record=record,
            metadata=metadata,
            hits=[],
            top_hit=None,
            sequence_length=sequence_length,
            match_type="no_match",
            candidate_taxon={"rank": "none", "name": "No match", "taxon_key": None},
            published_taxon=NONE_TAXON,
            indistinguishable_hits=[],
            barcode_gap_result={"status": "not_evaluated", "gap": None},
            diagnostic_result={"status": "not_evaluated", "support_count": 0, "support_rate": 0, "k": None, "p_false_positive": None},
            taxonomic_status="no-match",
            decision_class="not-publishable" if publication_stage == "record_not_ready" else "no-match",
            publication_stage=publication_stage,
            publication_checks=publication_checks,
            marker_profile=marker_profile,
            assay_gate=assay_gate,
            dna_extension=dna_extension,
            core_pass=core_pass,
            dna_pass=dna_pass,
            core_missing=core_missing,
            dna_missing=dna_missing,
            blockers=[*blockers, *metadata_blockers(core_missing, dna_missing, data_quality_blockers)],
            actions=[*actions, *metadata_actions(core_missing, dna_missing), *degraded_backend_actions(metadata)],
        )

    match_type = classify_match(top_hit, marker_profile)
    indistinguishable_hits = ambiguity_set(top_hit, hits, fallback_length=sequence_length)
    candidate_taxon = lowest_common_ancestor(indistinguishable_hits)
    barcode_gap_result = evaluate_barcode_gap(record)
    diagnostic_result = evaluate_diagnostic_kmers(record)
    taxonomic_status = classify_taxonomic_status(
        match_type=match_type,
        candidate_taxon=candidate_taxon,
        indistinguishable_hits=indistinguishable_hits,
        barcode_gap_result=barcode_gap_result,
        diagnostic_result=diagnostic_result,
        top_hit=top_hit,
    )

    if taxonomic_status == "species-safe" and not marker_profile["species_gate_pass"]:
        profile_taxon = ancestor_from_hit(top_hit, "genus") or candidate_taxon
        if profile_taxon["rank"] == "genus":
            candidate_taxon = profile_taxon
            taxonomic_status = "genus-safe"
        else:
            candidate_taxon = profile_taxon
            taxonomic_status = "ambiguous"

    if marker_profile["profile_blockers"]:
        blockers.extend(marker_profile["profile_blockers"])
        actions.append("Use a marker-specific validation profile, longer target region or safe-rank downgrade before species export.")
    for warning in marker_profile["profile_warnings"]:
        actions.append(f"Review marker profile warning: {warning}")

    if match_type != "exact":
        blockers.append(
            "species claim blocked: top hit does not pass "
            f"{marker_profile['profile_id']} exact gate identity >= {format_threshold(marker_profile['identity_species_min'])}% "
            f"and query coverage >= {format_threshold(marker_profile['coverage_species_min'])}%"
        )
        actions.append("Use a longer/cleaner marker sequence or treat the assignment below species rank.")
    if top_hit.query_coverage < marker_profile["coverage_species_min"]:
        blockers.append(f"species claim blocked: query coverage < {format_threshold(marker_profile['coverage_species_min'])}%")
    if top_hit.identity < marker_profile["identity_species_min"]:
        blockers.append(f"species claim blocked: identity < {format_threshold(marker_profile['identity_species_min'])}%")
    if len({hit.taxon for hit in indistinguishable_hits}) > 1 and candidate_taxon["rank"] != "species":
        blockers.append(f"species claim blocked: statistically indistinguishable competitors collapse the safe rank to {candidate_taxon['rank']}")
        actions.append(f"Publish the molecular assignment at {candidate_taxon['rank']} rank unless additional evidence resolves the ambiguity.")
    if barcode_gap_result["status"] != "pass":
        blockers.append(f"species claim blocked: barcode gap {barcode_gap_result['status']}")
        actions.append("Attach reference-set intra/inter distances or use a marker/reference set with positive species separation.")
    if diagnostic_result["status"] != "pass":
        blockers.append(f"species claim blocked: diagnostic k-mer support {diagnostic_result['status']}")
        actions.append("Attach diagnostic k-mers or keep the assignment below species rank.")

    blockers.extend(metadata_blockers(core_missing, dna_missing, data_quality_blockers))
    actions.extend(metadata_actions(core_missing, dna_missing))
    actions.extend(degraded_backend_actions(metadata))
    blockers.extend(assay_gate["assay_blockers"])
    actions.extend(assay_gate["assay_actions"])
    actions.extend(dna_extension_actions(dna_extension))

    published_taxon = published_taxon_for_status(taxonomic_status, candidate_taxon, top_hit)
    decision_class = taxonomic_status
    if taxonomic_status in SAFE_TAXONOMIC_STATUSES and publication_stage == "record_not_ready":
        decision_class = "not-publishable"
        published_taxon = NONE_TAXON
    elif taxonomic_status not in SAFE_TAXONOMIC_STATUSES:
        published_taxon = NONE_TAXON

    return build_decision(
        record=record,
        metadata=metadata,
        hits=hits,
        top_hit=top_hit,
        sequence_length=sequence_length,
        match_type=match_type,
        candidate_taxon=candidate_taxon,
        published_taxon=published_taxon,
        indistinguishable_hits=indistinguishable_hits,
        barcode_gap_result=barcode_gap_result,
        diagnostic_result=diagnostic_result,
        taxonomic_status=taxonomic_status,
        decision_class=decision_class,
        publication_stage=publication_stage,
        publication_checks=publication_checks,
        marker_profile=marker_profile,
        assay_gate=assay_gate,
        dna_extension=dna_extension,
        core_pass=core_pass,
        dna_pass=dna_pass,
        core_missing=core_missing,
        dna_missing=dna_missing,
        blockers=dedupe(blockers),
        actions=dedupe(actions),
    )


def normalized_metadata(record: SequenceRecord, request: BarcodeCompilerRequest) -> dict[str, Any]:
    hit = sorted(record.hits, key=hit_sort_key, reverse=True)[0] if record.hits else None
    metadata = dict(record.metadata)
    metadata.setdefault("marker", request.marker)
    metadata.setdefault("sequenceID", record.sequence_id)
    metadata.setdefault("referenceDatabase", request.reference_database)
    metadata.setdefault("methodOrSOP", request.method_or_sop)
    if hit:
        metadata.setdefault("identity", hit.identity)
        metadata.setdefault("queryCoverage", hit.query_coverage)
        metadata.setdefault("scientificName", hit.taxon)
    return metadata


def enrich_molecular_metadata(
    metadata: dict[str, Any],
    record: SequenceRecord,
    request: BarcodeCompilerRequest,
    hit: ReferenceHit | None,
    marker_profile: dict[str, Any],
) -> None:
    metadata.setdefault("assayType", request.assay_type)
    metadata.setdefault("DNA_sequence", record.sequence)
    metadata.setdefault("target_gene", marker_profile["target_gene"])
    metadata.setdefault("target_subfragment", marker_profile["target_subfragment"])
    metadata.setdefault("otu_db", metadata.get("referenceDatabase") or request.reference_database)
    metadata.setdefault("otu_class_appr", metadata.get("methodOrSOP") or request.method_or_sop)
    metadata.setdefault("sop", metadata.get("methodOrSOP") or request.method_or_sop)
    if hit:
        metadata.setdefault("otu_seq_comp_appr", f"identity={hit.identity}; queryCoverage={hit.query_coverage}")


def hit_sort_key(hit: ReferenceHit) -> tuple[float, float, float]:
    bit_score = hit.bit_score if hit.bit_score is not None else hit.identity * hit.query_coverage
    return (float(bit_score), float(hit.identity), float(hit.query_coverage))


def classify_match(hit: ReferenceHit, marker_profile: dict[str, Any]) -> str:
    if hit.identity >= marker_profile["identity_species_min"] and hit.query_coverage >= marker_profile["coverage_species_min"]:
        return "exact"
    if (
        marker_profile["identity_close_min"] < hit.identity < marker_profile["identity_species_min"]
        and hit.query_coverage >= marker_profile["coverage_close_min"]
    ):
        return "close"
    return "weak"


def ambiguity_set(top_hit: ReferenceHit, hits: list[ReferenceHit], *, fallback_length: int) -> list[ReferenceHit]:
    top_d = mismatch_rate(top_hit)
    top_se = standard_error(top_hit, fallback_length)
    indistinguishable = [top_hit]
    for hit in hits[1:]:
        delta = mismatch_rate(hit) - top_d
        boundary = 1.96 * math.sqrt(top_se**2 + standard_error(hit, fallback_length) ** 2)
        if delta <= boundary:
            indistinguishable.append(hit)
    return indistinguishable


def mismatch_rate(hit: ReferenceHit) -> float:
    return max(0.0, min(1.0, 1 - hit.identity / 100))


def standard_error(hit: ReferenceHit, fallback_length: int) -> float:
    d = mismatch_rate(hit)
    length = hit.aligned_length or fallback_length or 1
    return math.sqrt((d * (1 - d)) / length)


def lowest_common_ancestor(hits: list[ReferenceHit]) -> dict[str, Any]:
    if not hits:
        return {"rank": "none", "name": "No match", "taxon_key": None}
    if len(hits) == 1:
        hit = hits[0]
        if hit.lineage:
            species = next((item for item in reversed(hit.lineage) if normalize_rank(item.rank) == normalize_rank(hit.rank)), None)
            if species:
                return {"rank": normalize_rank(species.rank), "name": species.name, "taxon_key": species.taxon_key}
        return {"rank": normalize_rank(hit.rank), "name": hit.taxon, "taxon_key": hit.gbif_taxon_key}

    lineages = [lineage_or_hit(hit) for hit in hits]
    shortest = min(len(items) for items in lineages)
    last_common: dict[str, Any] | None = None
    for index in range(shortest):
        names = {items[index]["name"].lower() for items in lineages}
        ranks = {items[index]["rank"] for items in lineages}
        if len(names) == 1 and len(ranks) == 1:
            last_common = lineages[0][index]
        else:
            break
    return last_common or {"rank": "unranked", "name": "Ambiguous lineage", "taxon_key": None}


def lineage_or_hit(hit: ReferenceHit) -> list[dict[str, Any]]:
    if hit.lineage:
        return [
            {"rank": normalize_rank(item.rank), "name": item.name, "taxon_key": item.taxon_key}
            for item in hit.lineage
        ]
    return [{"rank": normalize_rank(hit.rank), "name": hit.taxon, "taxon_key": hit.gbif_taxon_key}]


def normalize_rank(rank: str) -> str:
    normalized = str(rank or "unranked").strip().lower()
    return normalized if normalized in {*SAFE_RANK_ORDER, "none"} else "unranked"


def evaluate_barcode_gap(record: SequenceRecord) -> dict[str, Any]:
    if not record.barcode_gap:
        return {"status": "missing", "gap": None, "intra_max_distance": None, "inter_min_distance": None}
    intra = record.barcode_gap.intra_max_distance
    inter = record.barcode_gap.inter_min_distance
    if intra is None or inter is None:
        return {"status": "missing", "gap": None, "intra_max_distance": intra, "inter_min_distance": inter}
    gap = inter - intra
    return {
        "status": "pass" if gap > 0 else "fail",
        "gap": round(gap, 6),
        "intra_max_distance": intra,
        "inter_min_distance": inter,
    }


def evaluate_diagnostic_kmers(record: SequenceRecord) -> dict[str, Any]:
    if not record.diagnostic:
        return {"status": "missing", "support_count": 0, "support_rate": 0, "k": None, "expected_random_hits": None, "p_false_positive": None}
    diagnostic_kmers = {item.upper() for item in record.diagnostic.diagnostic_kmers if item}
    if not diagnostic_kmers:
        return {"status": "missing", "support_count": 0, "support_rate": 0, "k": record.diagnostic.k, "expected_random_hits": None, "p_false_positive": None}
    k = record.diagnostic.k or infer_k(record.diagnostic.reference_total_windows, record.diagnostic.epsilon, diagnostic_kmers)
    query_kmer_windows = kmers(record.sequence, k)
    query_kmers = set(query_kmer_windows)
    support_count = len(query_kmers & diagnostic_kmers)
    query_window_count = len(query_kmer_windows)
    support_rate = support_count / max(query_window_count, 1)
    expected_random_hits = expected_diagnostic_collisions(query_window_count, len(diagnostic_kmers), k)
    p_false_positive = false_positive_probability(query_window_count, len(diagnostic_kmers), k)
    status = "pass" if support_count >= 1 and p_false_positive <= record.diagnostic.alpha else "fail"
    if support_count < 1:
        status = "fail_no_support"
    elif p_false_positive > record.diagnostic.alpha:
        status = "fail_false_positive_risk"
    return {
        "status": status,
        "support_count": support_count,
        "support_rate": round(support_rate, 6),
        "k": k,
        "query_window_count": query_window_count,
        "diagnostic_kmer_count": len(diagnostic_kmers),
        "expected_random_hits": round(expected_random_hits, 6),
        "p_false_positive": round(p_false_positive, 8),
        "alpha": record.diagnostic.alpha,
    }


def infer_k(reference_total_windows: int | None, epsilon: float, diagnostic_kmers: set[str]) -> int:
    if reference_total_windows:
        return max(1, math.ceil(math.log(reference_total_windows / epsilon, 4)))
    return len(next(iter(diagnostic_kmers)))


def kmers(sequence: str, k: int) -> list[str]:
    clean = sequence.upper()
    return [clean[index : index + k] for index in range(0, max(len(clean) - k + 1, 0)) if "N" not in clean[index : index + k]]


def expected_diagnostic_collisions(query_windows: int, diagnostic_count: int, k: int) -> float:
    return query_windows * (diagnostic_count / (4**k))


def false_positive_probability(query_windows: int, diagnostic_count: int, k: int) -> float:
    if query_windows <= 0 or diagnostic_count <= 0:
        return 0.0
    single_window_probability = min(1.0, diagnostic_count / (4**k))
    return 1 - ((1 - single_window_probability) ** query_windows)


def classify_taxonomic_status(
    *,
    match_type: str,
    candidate_taxon: dict[str, Any],
    indistinguishable_hits: list[ReferenceHit],
    barcode_gap_result: dict[str, Any],
    diagnostic_result: dict[str, Any],
    top_hit: ReferenceHit,
) -> str:
    safe_rank = candidate_taxon["rank"]
    if match_type == "weak":
        return "weak"
    if (
        match_type == "exact"
        and safe_rank == "species"
        and len({hit.taxon for hit in indistinguishable_hits}) == 1
        and barcode_gap_result["status"] == "pass"
        and diagnostic_result["status"] == "pass"
    ):
        return "species-safe"
    if len({hit.taxon for hit in indistinguishable_hits}) > 1 and safe_rank != "species":
        if safe_rank == "genus":
            return "genus-safe"
        if safe_rank in HIGHER_RANKS:
            return "higher-rank-safe"
        return "ambiguous"
    if match_type == "close" and safe_rank in {"species", "genus"}:
        return "genus-safe"
    if safe_rank == "genus":
        return "genus-safe"
    if safe_rank in HIGHER_RANKS:
        return "higher-rank-safe"
    if normalize_rank(top_hit.rank) == "species":
        return "ambiguous"
    return "weak"


def missing_fields(metadata: dict[str, Any], fields: list[str]) -> list[str]:
    missing = []
    for field in fields:
        value = metadata.get(field)
        if value is None or str(value).strip() == "":
            missing.append(field)
    return missing


def metadata_quality_blockers(metadata: dict[str, Any], top_hit: ReferenceHit | None = None) -> list[str]:
    blockers = []
    event_date = metadata.get("eventDate")
    if event_date and not re.match(r"^\d{4}(-\d{2})?(-\d{2})?$", str(event_date)):
        blockers.append("publication blocked: eventDate must follow ISO 8601 date format")
    uncertainty = metadata.get("coordinateUncertaintyInMeters")
    if uncertainty is not None and str(uncertainty).strip() != "":
        try:
            if float(uncertainty) == 0:
                blockers.append("publication blocked: coordinateUncertaintyInMeters cannot be 0")
        except (TypeError, ValueError):
            blockers.append("publication blocked: coordinateUncertaintyInMeters must be numeric")
    if is_degraded_reference_search(metadata):
        blockers.append("publication blocked: production reference search backend was not used; python-local mini-search is review-only")
    supplied_name = str(metadata.get("scientificName") or "").strip()
    if top_hit and supplied_name and supplied_name.lower() != top_hit.taxon.lower():
        blockers.append(
            "publication blocked: supplied scientificName conflicts with top molecular hit "
            f"({supplied_name} vs {top_hit.taxon})"
        )
    return blockers


def publication_stage_for(
    metadata: dict[str, Any],
    request: BarcodeCompilerRequest,
    *,
    core_pass: bool,
    dna_pass: bool,
    assay_publication_pass: bool,
) -> tuple[str, dict[str, Any]]:
    core_recommended_missing = missing_fields(metadata, CORE_RECOMMENDED_FIELDS)
    core_recommended_pass = not core_recommended_missing and str(metadata.get("coordinateUncertaintyInMeters")).strip() != "0"
    dataset_metadata = request.dataset_metadata.model_dump()
    dataset_missing = []
    for field in DATASET_METADATA_FIELDS:
        value = dataset_metadata.get(field)
        if value is None or value == [] or str(value).strip() == "":
            dataset_missing.append(field)
    dataset_pass = not dataset_missing
    if not (core_pass and dna_pass and assay_publication_pass):
        stage = "record_not_ready"
    elif dataset_pass and core_recommended_pass:
        stage = "gold_ready"
    elif dataset_pass:
        stage = "dataset_ready"
    elif core_recommended_pass:
        stage = "record_recommended_ready"
    else:
        stage = "record_min_ready"
    return stage, {
        "core_recommended_pass": core_recommended_pass,
        "core_recommended_missing": core_recommended_missing,
        "dataset_metadata_pass": dataset_pass,
        "dataset_metadata_missing": dataset_missing,
        "assay_publication_pass": assay_publication_pass,
    }


def metadata_blockers(core_missing: list[str], dna_missing: list[str], quality_blockers: list[str]) -> list[str]:
    blockers = []
    for field in core_missing:
        blockers.append(f"publication blocked: missing required Occurrence core field {field}")
    for field in dna_missing:
        blockers.append(f"publication blocked: missing DNA-derived evidence field {field}")
    blockers.extend(quality_blockers)
    return blockers


def metadata_actions(core_missing: list[str], dna_missing: list[str]) -> list[str]:
    actions = []
    if core_missing:
        actions.append("Complete required Darwin Core Occurrence core fields before GBIF publication.")
    if dna_missing:
        actions.append("Attach marker, sequence ID, reference database, identity, coverage and method/SOP metadata.")
    return actions


def degraded_backend_actions(metadata: dict[str, Any]) -> list[str]:
    if not is_degraded_reference_search(metadata):
        return []
    return [
        "Re-run reference search with VSEARCH, BLAST+ or an audited external reference workflow before GBIF-ready export."
    ]


def is_degraded_reference_search(metadata: dict[str, Any]) -> bool:
    backend = str(
        metadata.get("referenceSearchBackend")
        or metadata.get("searchBackend")
        or metadata.get("backend_used")
        or ""
    ).strip().lower()
    return backend in {"python-local", "python", "local"}


def dna_extension_actions(dna_extension: dict[str, Any]) -> list[str]:
    missing = dna_extension.get("dna_extension_high_priority_missing", [])
    if not missing:
        return []
    return [
        "Add high-priority DNA-derived extension fields: "
        + ", ".join(missing[:8])
        + ("..." if len(missing) > 8 else "")
        + "."
    ]


def published_taxon_for_status(taxonomic_status: str, candidate_taxon: dict[str, Any], top_hit: ReferenceHit) -> dict[str, Any]:
    if taxonomic_status == "species-safe" and candidate_taxon["rank"] == "species":
        return candidate_taxon
    if taxonomic_status == "genus-safe":
        if candidate_taxon["rank"] == "genus":
            return candidate_taxon
        genus = ancestor_from_hit(top_hit, "genus")
        return genus or NONE_TAXON
    if taxonomic_status == "higher-rank-safe" and candidate_taxon["rank"] in HIGHER_RANKS:
        return candidate_taxon
    return NONE_TAXON


def ancestor_from_hit(hit: ReferenceHit, rank: str) -> dict[str, Any] | None:
    for item in hit.lineage:
        if normalize_rank(item.rank) == rank:
            return {"rank": rank, "name": item.name, "taxon_key": item.taxon_key}
    return None


def publication_status(decision_class: str, publication_stage: str) -> str:
    if decision_class not in SAFE_TAXONOMIC_STATUSES:
        return "not-ready"
    if publication_stage in {"dataset_ready", "gold_ready"}:
        return "gbif-ready"
    if publication_stage in {"record_min_ready", "record_recommended_ready"}:
        return "record-ready"
    return "not-ready"


def publication_bucket(decision_class: str, publication_stage: str, published_taxon: dict[str, Any], blockers: list[str]) -> str:
    if published_taxon.get("rank") != "none" and publication_stage in {"dataset_ready", "gold_ready"}:
        return "gbif_ready"
    if published_taxon.get("rank") != "none" and decision_class in SAFE_TAXONOMIC_STATUSES:
        return "publishable_candidate"
    if blockers:
        return "repair_required"
    return "review_only"


def claim_boundary(
    *,
    decision_class: str,
    taxonomic_status: str,
    candidate_taxon: dict[str, Any],
    published_taxon: dict[str, Any],
    publication_stage: str,
    metadata: dict[str, Any],
    top_hit: ReferenceHit | None,
    indistinguishable_hits: list[ReferenceHit],
    barcode_gap_result: dict[str, Any],
    diagnostic_result: dict[str, Any],
    marker_profile: dict[str, Any],
    assay_gate: dict[str, Any],
    core_pass: bool,
    dna_pass: bool,
) -> dict[str, Any]:
    if top_hit and top_hit.reference_database:
        reference_context = top_hit.reference_database
    else:
        reference_context = metadata.get("referenceDatabase") or "not supplied"
    safe_rank = candidate_taxon.get("rank") or "none"
    safe_name = candidate_taxon.get("name") or "No safe taxon"
    if decision_class == "species-safe":
        supported = f"Species-level molecular assignment candidate for {safe_name} within the supplied reference context."
    elif decision_class == "genus-safe":
        supported = f"Genus-level molecular evidence for {safe_name}; species-level naming is blocked for this sequence."
    elif decision_class == "higher-rank-safe":
        supported = f"{safe_rank.title()}-level molecular evidence for {safe_name}; lower-rank claims are blocked."
    elif taxonomic_status == "weak":
        supported = "Review-only molecular hint; identity, coverage or marker profile is too weak for a safe taxonomic claim."
    elif taxonomic_status == "no-match":
        supported = "No taxonomic claim from the supplied reference evidence."
    else:
        supported = f"Review-only candidate at {safe_rank} rank: {safe_name}."

    if published_taxon.get("rank") == "none" and taxonomic_status in SAFE_TAXONOMIC_STATUSES:
        publication = "Taxonomy is bounded as safe, but publication repair is required before Darwin Core or DNA-derived export."
    elif published_taxon.get("rank") == "none":
        publication = "Not GBIF-ready; repair blockers before publishing Darwin Core or DNA-derived rows."
    elif publication_stage in {"dataset_ready", "gold_ready"}:
        publication = "GBIF-ready export candidate under the current metadata and dataset-level checks."
    else:
        publication = "Publishable candidate for review; dataset-level GBIF metadata is still incomplete."

    competitor_taxa = sorted({hit.taxon for hit in indistinguishable_hits})
    evidence_fields = {
        "top_hit": top_hit.taxon if top_hit else None,
        "top_identity": top_hit.identity if top_hit else None,
        "top_query_coverage": top_hit.query_coverage if top_hit else None,
        "competitor_taxa": competitor_taxa,
        "competitor_count": len(competitor_taxa),
        "lca_safe_rank": safe_rank,
        "lca_safe_taxon": safe_name,
        "barcode_gap_status": barcode_gap_result.get("status"),
        "barcode_gap": barcode_gap_result.get("gap"),
        "diagnostic_kmer_status": diagnostic_result.get("status"),
        "diagnostic_kmer_support": diagnostic_result.get("support_count"),
        "diagnostic_p_false_positive": diagnostic_result.get("p_false_positive"),
        "marker_profile": marker_profile.get("profile_id"),
        "marker_species_gate": marker_profile.get("species_gate_pass"),
        "assay_gate": assay_gate.get("assay_gate_pass"),
        "occurrence_core_gate": core_pass,
        "dna_metadata_gate": dna_pass,
    }
    evidence_rationale = claim_evidence_rationale(evidence_fields)

    return {
        "supported": supported,
        "reference_context": reference_context,
        "safe_rank": safe_rank,
        "safe_taxon": safe_name,
        "publication": publication,
        "evidence_fields": evidence_fields,
        "evidence_rationale": evidence_rationale,
        "not_supported": [
            "absolute species truth outside the stated reference context",
            "natural presence, absence, abundance or distribution without occurrence evidence",
            "phenotype, pathogenicity, ecological role or invasiveness",
            "replacement for GBIF Sequence ID, curated reference databases or expert review",
        ],
        "boundary_text": f"{supported} {publication} {evidence_rationale}",
    }


def build_decision(
    *,
    record: SequenceRecord,
    metadata: dict[str, Any],
    hits: list[ReferenceHit],
    top_hit: ReferenceHit | None,
    sequence_length: int,
    match_type: str,
    candidate_taxon: dict[str, Any],
    published_taxon: dict[str, Any],
    indistinguishable_hits: list[ReferenceHit],
    barcode_gap_result: dict[str, Any],
    diagnostic_result: dict[str, Any],
    taxonomic_status: str,
    decision_class: str,
    publication_stage: str,
    publication_checks: dict[str, Any],
    marker_profile: dict[str, Any],
    assay_gate: dict[str, Any],
    dna_extension: dict[str, Any],
    core_pass: bool,
    dna_pass: bool,
    core_missing: list[str],
    dna_missing: list[str],
    blockers: list[str],
    actions: list[str],
) -> dict[str, Any]:
    return {
        "sequence_id": record.sequence_id,
        "sequence_md5": hashlib.md5(record.sequence.encode("utf-8")).hexdigest(),
        "sequence_length": sequence_length,
        "decision_class": decision_class,
        "taxonomic_status": taxonomic_status,
        "publication_status": publication_status(decision_class, publication_stage),
        "publication_stage": publication_stage,
        "publication_bucket": publication_bucket(decision_class, publication_stage, published_taxon, blockers),
        "export_state": export_state(decision_class, taxonomic_status, publication_stage, published_taxon),
        "match_type": match_type,
        "candidate_taxon": candidate_taxon,
        "published_taxon": published_taxon,
        "safe_taxon": candidate_taxon,
        "claim_boundary": claim_boundary(
            decision_class=decision_class,
            taxonomic_status=taxonomic_status,
            candidate_taxon=candidate_taxon,
            published_taxon=published_taxon,
            publication_stage=publication_stage,
            metadata=metadata,
            top_hit=top_hit,
            indistinguishable_hits=indistinguishable_hits,
            barcode_gap_result=barcode_gap_result,
            diagnostic_result=diagnostic_result,
            marker_profile=marker_profile,
            assay_gate=assay_gate,
            core_pass=core_pass,
            dna_pass=dna_pass,
        ),
        "top_hit": hit_summary(top_hit),
        "indistinguishable_hits": [hit_summary(hit) for hit in indistinguishable_hits],
        "barcode_gap": barcode_gap_result,
        "diagnostic_kmers": diagnostic_result,
        "reference_completeness": reference_completeness_summary(metadata, top_hit, hits),
        "metadata_readiness": {
            "core_pass": core_pass,
            "dna_pass": dna_pass,
            "core_missing": core_missing,
            "dna_missing": dna_missing,
            "marker_profile": marker_profile,
            "assay_gate": assay_gate,
            **dna_extension,
            **publication_checks,
        },
        "blockers": blockers,
        "actions": actions,
        "metadata": metadata,
        "hits": [hit_summary(hit) for hit in hits],
    }


def hit_summary(hit: ReferenceHit | None) -> dict[str, Any] | None:
    if hit is None:
        return None
    return {
        "taxon": hit.taxon,
        "rank": normalize_rank(hit.rank),
        "identity": hit.identity,
        "query_coverage": hit.query_coverage,
        "aligned_length": hit.aligned_length,
        "bit_score": hit.bit_score,
        "evalue": hit.evalue,
        "reference_id": hit.reference_id,
        "reference_database": hit.reference_database,
        "gbif_taxon_key": hit.gbif_taxon_key,
        "lineage": [item.model_dump() for item in hit.lineage],
    }


def summarize_decisions(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    processed = len(decisions)
    candidate_records = sum(1 for item in decisions if item["top_hit"])
    species_safe = sum(1 for item in decisions if item["decision_class"] == "species-safe")
    genus_safe = sum(1 for item in decisions if item["decision_class"] == "genus-safe")
    higher_rank_safe = sum(1 for item in decisions if item["decision_class"] == "higher-rank-safe")
    ambiguous = sum(1 for item in decisions if item["taxonomic_status"] == "ambiguous")
    weak = sum(1 for item in decisions if item["taxonomic_status"] == "weak")
    no_match = sum(1 for item in decisions if item["taxonomic_status"] == "no-match")
    not_publishable = sum(1 for item in decisions if item["decision_class"] == "not-publishable")
    record_ready = sum(1 for item in decisions if item["publication_status"] in {"record-ready", "gbif-ready"})
    dataset_ready = sum(1 for item in decisions if item["publication_stage"] in {"dataset_ready", "gold_ready"})
    blocked_species = sum(
        1
        for item in decisions
        if item["top_hit"] and item["top_hit"]["rank"] == "species" and item["decision_class"] != "species-safe"
    )
    top_species = sum(1 for item in decisions if item["top_hit"] and item["top_hit"]["rank"] == "species")
    safe_rank_records = species_safe + genus_safe + higher_rank_safe
    publishable_template_records = sum(1 for item in decisions if item["published_taxon"]["rank"] != "none")
    gbif_ready_records = sum(1 for item in decisions if item.get("publication_bucket") == "gbif_ready")
    publishable_candidate_records = sum(1 for item in decisions if item.get("publication_bucket") == "publishable_candidate")
    repair_required_records = sum(1 for item in decisions if item.get("publication_bucket") == "repair_required")
    review_only_records = sum(1 for item in decisions if item.get("publication_bucket") == "review_only")
    repairable_records = sum(1 for item in decisions if item["actions"] or item["blockers"])
    not_ready_with_blockers = sum(1 for item in decisions if item["publication_status"] == "not-ready" and item["blockers"])
    not_ready = sum(1 for item in decisions if item["publication_status"] == "not-ready")
    hard_gate_failures = sum(1 for item in hard_gate_audit(decisions) if item["hardGateViolation"])
    assay_gate_failures = sum(1 for item in decisions if not item["metadata_readiness"]["assay_gate"]["assay_gate_pass"])
    dna_extension_ready = sum(1 for item in decisions if item["metadata_readiness"].get("dna_extension_high_priority_pass"))
    marker_species_disabled = sum(1 for item in decisions if not item["metadata_readiness"]["marker_profile"]["species_claim_allowed"])
    return {
        "processed_records": processed,
        "input_records": processed,
        "eligible_records": processed,
        "candidate_records": candidate_records,
        "safe_records": safe_rank_records,
        "processing_coverage": 1 if processed else 0,
        "species_safe_records": species_safe,
        "genus_safe_records": genus_safe,
        "higher_rank_safe_records": higher_rank_safe,
        "ambiguous_records": ambiguous,
        "weak_records": weak,
        "no_match_records": no_match,
        "not_publishable_records": not_publishable,
        "record_ready_records": record_ready,
        "dataset_ready_records": dataset_ready,
        "publishable_template_records": publishable_template_records,
        "gbif_ready_records": gbif_ready_records,
        "publishable_candidate_records": publishable_candidate_records,
        "repair_required_records": repair_required_records,
        "review_only_records": review_only_records,
        "safe_rank_records": safe_rank_records,
        "repairable_records": repairable_records,
        "top_species_hits": top_species,
        "blocked_or_downgraded_top_species_hits": blocked_species,
        "species_safe_yield": round(species_safe / processed, 6) if processed else 0,
        "safe_rank_yield": round(safe_rank_records / processed, 6) if processed else 0,
        "molecular_evidence_conversion_yield": round(publishable_template_records / processed, 6) if processed else 0,
        "repairable_yield": round(repairable_records / processed, 6) if processed else 0,
        "blocked_species_claims": blocked_species,
        "overclaim_prevention_rate": round(blocked_species / top_species, 6) if top_species else 0,
        "overclaim_prevention_proxy": 1 if blocked_species else None,
        "publication_repair_efficiency": round(not_ready_with_blockers / not_ready, 6) if not_ready else 1,
        "hard_gate_failures": hard_gate_failures,
        "assay_gate_failures": assay_gate_failures,
        "dna_extension_ready_records": dna_extension_ready,
        "marker_species_disabled_records": marker_species_disabled,
    }


def build_run_verdict(metrics: dict[str, Any]) -> str:
    if metrics.get("hard_gate_failures"):
        return "Hard-gate audit found a species-safe inconsistency; do not use this run for publication until the rules are fixed."
    if metrics["species_safe_records"]:
        return "At least one sequence is species-safe under the frozen molecular evidence gates; publication readiness is reported separately."
    if metrics["genus_safe_records"] or metrics["higher_rank_safe_records"]:
        return "The run produced safe downgraded molecular evidence, but no species-level publication candidate."
    return "The run correctly blocked species-level publication claims."


def build_nexus_v3_summary(decisions: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
    return {
        "positioning": "Molecular Evidence Conversion & Repair Engine for GBIF",
        "working_layer": "Barcode-to-GBIF Evidence Compiler",
        "ruleset_family": "EcoGenesis Nexus V3 conservative hard-gate workflow",
        "scientific_claim": (
            "The compiler computes the safest publishable taxonomic rank and repair actions under supplied "
            "molecular hits, reference evidence and GBIF/DNA-derived metadata. It does not treat a top hit as species truth."
        ),
        "conversion_metrics": {
            "MECY_molecular_evidence_conversion_yield": metrics["molecular_evidence_conversion_yield"],
            "SRY_safe_rank_yield": metrics["safe_rank_yield"],
            "SSY_species_safe_yield": metrics["species_safe_yield"],
            "RY_repairable_yield": metrics["repairable_yield"],
            "OPR_overclaim_prevention_rate": metrics["overclaim_prevention_rate"],
        },
        "audit": {
            "hard_gate_failures": metrics["hard_gate_failures"],
            "assay_gate_failures": metrics["assay_gate_failures"],
            "dna_extension_ready_records": metrics["dna_extension_ready_records"],
            "marker_species_disabled_records": metrics["marker_species_disabled_records"],
            "top_species_hits": metrics["top_species_hits"],
            "blocked_or_downgraded_top_species_hits": metrics["blocked_or_downgraded_top_species_hits"],
            "species_safe_records": metrics["species_safe_records"],
            "publishable_template_records": metrics["publishable_template_records"],
            "gbif_ready_records": metrics["gbif_ready_records"],
            "publishable_candidate_records": metrics["publishable_candidate_records"],
            "repair_required_records": metrics["repair_required_records"],
            "review_only_records": metrics["review_only_records"],
            "candidate_records": metrics["candidate_records"],
            "safe_records": metrics["safe_records"],
        },
        "next_platform_layers": [
            "reference completeness gate calibrated by taxon/marker coverage",
            "protein sanity gate for coding markers",
            "assay evidence gate for eDNA/metabarcoding/qPCR controls",
            "fragment sharedness atlas",
            "Molecular Evidence Graph",
        ],
        "safe_language": [
            "sequence-derived occurrence evidence, not proof of living presence",
            "empty cells are no-evidence cells, not absence",
            "observed GBIF records are evidence context, not true distribution",
            "protein/phenotype links remain hypotheses unless external curated evidence is attached",
        ],
    }


def hard_gate_audit(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in decisions:
        top = record["top_hit"] or {}
        exact_pass = record["match_type"] == "exact"
        ambiguity_pass = record["candidate_taxon"]["rank"] == "species" and len({hit["taxon"] for hit in record["indistinguishable_hits"]}) == 1
        barcode_pass = record["barcode_gap"]["status"] == "pass"
        diagnostic_pass = record["diagnostic_kmers"]["status"] == "pass"
        core_pass = record["metadata_readiness"]["core_pass"] is True
        dna_pass = record["metadata_readiness"]["dna_pass"] is True
        marker_profile_pass = record["metadata_readiness"]["marker_profile"]["species_gate_pass"] is True
        assay_pass = record["metadata_readiness"]["assay_gate"]["assay_gate_pass"] is True
        species_safe = record["decision_class"] == "species-safe"
        hard_gate_violation = species_safe and not all(
            [exact_pass, ambiguity_pass, barcode_pass, diagnostic_pass, marker_profile_pass, core_pass, dna_pass, assay_pass]
        )
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "topHit": top.get("taxon"),
                "topHitRank": top.get("rank"),
                "decisionClass": record["decision_class"],
                "publicationBucket": record.get("publication_bucket"),
                "markerProfile": record["metadata_readiness"]["marker_profile"]["profile_id"],
                "exactMatchGate": gate_status(exact_pass),
                "ambiguityLcaGate": gate_status(ambiguity_pass),
                "barcodeGapGate": record["barcode_gap"]["status"],
                "diagnosticKmerGate": record["diagnostic_kmers"]["status"],
                "markerProfileGate": gate_status(marker_profile_pass),
                "occurrenceCoreGate": gate_status(core_pass),
                "dnaMetadataGate": gate_status(dna_pass),
                "assayGate": gate_status(assay_pass),
                "hardGateViolation": hard_gate_violation,
                "auditConclusion": "FAIL: species-safe emitted with failed gate" if hard_gate_violation else "pass: fail-closed rules preserved",
            }
        )
    return rows


def naive_top_hit_overclaims(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for record in decisions:
        top = record["top_hit"] or {}
        if top.get("rank") != "species" or record["decision_class"] == "species-safe":
            continue
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "naiveClaim": top.get("taxon"),
                "naiveRank": top.get("rank"),
                "compilerDecision": record["decision_class"],
                "safeTaxon": record["safe_taxon"]["name"],
                "safeRank": record["safe_taxon"]["rank"],
                "publishedTaxon": record["published_taxon"]["name"],
                "publishedRank": record["published_taxon"]["rank"],
                "reason": "; ".join(record["blockers"]) or "species gate did not pass",
            }
        )
    return rows


def metadata_bottlenecks(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    total = max(len(decisions), 1)
    for record in decisions:
        readiness = record["metadata_readiness"]
        for field in readiness.get("core_missing", []):
            counts[f"missing Occurrence core field: {field}"] = counts.get(f"missing Occurrence core field: {field}", 0) + 1
        for field in readiness.get("dna_missing", []):
            counts[f"missing DNA-derived field: {field}"] = counts.get(f"missing DNA-derived field: {field}", 0) + 1
        for field in readiness.get("core_recommended_missing", []):
            counts[f"missing recommended field: {field}"] = counts.get(f"missing recommended field: {field}", 0) + 1
        for field in readiness.get("dataset_metadata_missing", []):
            counts[f"missing dataset metadata: {field}"] = counts.get(f"missing dataset metadata: {field}", 0) + 1
        for field in readiness.get("dna_extension_high_priority_missing", []):
            counts[f"missing DNA-derived extension field: {field}"] = counts.get(f"missing DNA-derived extension field: {field}", 0) + 1
        for field in readiness.get("assay_gate", {}).get("assay_required_missing", []):
            counts[f"missing assay-required field: {field}"] = counts.get(f"missing assay-required field: {field}", 0) + 1
        for field in readiness.get("assay_gate", {}).get("assay_recommended_missing", []):
            counts[f"missing assay-recommended field: {field}"] = counts.get(f"missing assay-recommended field: {field}", 0) + 1
    return [
        {"bottleneck": key, "records": value, "MBI_metadata_bottleneck_index": round(value / total, 6)}
        for key, value in sorted(counts.items(), key=lambda item: item[1], reverse=True)
    ]


def reference_gap_index(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}
    for record in decisions:
        marker = record["metadata"].get("marker") or "unknown-marker"
        safe = record["safe_taxon"]
        key = f"{marker}|{safe['rank']}|{safe['name']}"
        bucket = buckets.setdefault(
            key,
            {
                "markerRankTaxon": key,
                "marker": marker,
                "safeRank": safe["rank"],
                "safeTaxon": safe["name"],
                "records": 0,
                "referenceBlockedRecords": 0,
                "blockerExamples": set(),
            },
        )
        bucket["records"] += 1
        reference_blockers = reference_blocker_reasons(record)
        if reference_blockers:
            bucket["referenceBlockedRecords"] += 1
            bucket["blockerExamples"].update(reference_blockers)
    rows = []
    for bucket in buckets.values():
        rows.append(
            {
                "markerRankTaxon": bucket["markerRankTaxon"],
                "marker": bucket["marker"],
                "safeRank": bucket["safeRank"],
                "safeTaxon": bucket["safeTaxon"],
                "records": bucket["records"],
                "referenceBlockedRecords": bucket["referenceBlockedRecords"],
                "RGI_reference_gap_index": round(bucket["referenceBlockedRecords"] / bucket["records"], 6) if bucket["records"] else 0,
                "blockerExamples": "; ".join(sorted(bucket["blockerExamples"])),
            }
        )
    return sorted(rows, key=lambda row: row["RGI_reference_gap_index"], reverse=True)


def repair_plan(decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action_to_records: dict[str, set[str]] = {}
    for record in decisions:
        for action in record["actions"]:
            action_to_records.setdefault(action, set()).add(record["sequence_id"])
    rows = []
    total = max(len(decisions), 1)
    for action, record_ids in action_to_records.items():
        rows.append(
            {
                "repairAction": action,
                "unlockableRecords": len(record_ids),
                "estimatedGain": round(len(record_ids) / total, 6),
                "estimatedCost": repair_cost(action),
                "exampleRecords": "; ".join(sorted(record_ids)[:8]),
            }
        )
    return sorted(rows, key=lambda row: (row["unlockableRecords"], row["estimatedGain"]), reverse=True)


def reference_blocker_reasons(record: dict[str, Any]) -> list[str]:
    reasons = []
    if not record["hits"]:
        reasons.append("no reference hits")
    if record["barcode_gap"]["status"] != "pass":
        reasons.append(f"barcode gap {record['barcode_gap']['status']}")
    if record["diagnostic_kmers"]["status"] != "pass":
        reasons.append(f"diagnostic k-mer {record['diagnostic_kmers']['status']}")
    if len({hit["taxon"] for hit in record["indistinguishable_hits"]}) > 1 and record["safe_taxon"]["rank"] != "species":
        reasons.append("LCA downgrade from indistinguishable competitors")
    return reasons


def repair_cost(action: str) -> str:
    lowered = action.lower()
    if lowered.startswith("complete") or lowered.startswith("attach marker"):
        return "low"
    if "reference" in lowered or "diagnostic" in lowered or "barcode" in lowered:
        return "medium"
    if "sequence" in lowered or "marker" in lowered:
        return "high"
    return "medium"


def export_state(
    decision_class: str,
    taxonomic_status: str,
    publication_stage: str,
    published_taxon: dict[str, Any],
) -> str:
    if published_taxon.get("rank") != "none" and publication_stage in {"dataset_ready", "gold_ready"}:
        return "formal_gbif_ready"
    if published_taxon.get("rank") != "none" and decision_class in SAFE_TAXONOMIC_STATUSES:
        return "dwc_template_ready"
    if taxonomic_status in SAFE_TAXONOMIC_STATUSES:
        return "evidence_publishable_repair_required"
    if decision_class in {"weak", "ambiguous", "no-match"}:
        return "review_only"
    return "not_exportable"


def reference_completeness_summary(
    metadata: dict[str, Any],
    top_hit: ReferenceHit | None,
    hits: list[ReferenceHit],
) -> dict[str, Any]:
    reference_context = metadata.get("referenceDatabase") or (top_hit.reference_database if top_hit else None) or "not supplied"
    close_competitors = len({hit.taxon for hit in hits if hit.rank == "species"})
    return {
        "status": "reference_context_supplied",
        "rci2_status": "not_measured_without_external_reference_audit",
        "reference_context": reference_context,
        "close_relative_coverage": "not_measured",
        "sequence_quality": "checked_by_identity_coverage_and_length_gates",
        "geographic_coverage": "not_measured",
        "per_species_depth": "not_measured",
        "taxonomic_stability": "tracked_by_lineage_and_gbif_taxon_keys_when_supplied",
        "candidate_species_in_hit_table": close_competitors,
        "claim_scope": "bounded_to_supplied_reference_context_not_absolute_species_truth",
    }


def claim_evidence_rationale(fields: dict[str, Any]) -> str:
    top = fields.get("top_hit") or "no top hit"
    identity = fields.get("top_identity")
    coverage = fields.get("top_query_coverage")
    competitors = fields.get("competitor_count", 0)
    return (
        f"Evidence path: top hit {top} at identity={identity}, coverage={coverage}; "
        f"{competitors} indistinguishable taxon candidate(s) collapse to {fields.get('lca_safe_rank')} "
        f"{fields.get('lca_safe_taxon')}; barcode gap={fields.get('barcode_gap_status')} "
        f"({fields.get('barcode_gap')}); diagnostic k-mer={fields.get('diagnostic_kmer_status')} "
        f"support={fields.get('diagnostic_kmer_support')}, p_false_positive={fields.get('diagnostic_p_false_positive')}; "
        f"marker profile={fields.get('marker_profile')}; gates core={fields.get('occurrence_core_gate')}, "
        f"dna={fields.get('dna_metadata_gate')}, assay={fields.get('assay_gate')}."
    )


def build_data_accounting_ledger(decisions: list[dict[str, Any]], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    processed = max(metrics.get("processed_records", len(decisions)), 0)
    top_species = metrics.get("top_species_hits", 0)

    def row(metric: str, value: Any, denominator: Any, layer: str, meaning: str) -> dict[str, Any]:
        numeric_value = value if isinstance(value, (int, float)) else None
        numeric_denominator = denominator if isinstance(denominator, (int, float)) else None
        rate = round(numeric_value / numeric_denominator, 6) if numeric_denominator else None
        return {
            "metric": metric,
            "value": value,
            "denominator": denominator,
            "rate": rate,
            "unit": "sequence_records",
            "layer": layer,
            "meaning": meaning,
        }

    return [
        row("input_n", processed, processed, "input", "Records received by the Barcode-to-GBIF compiler."),
        row(
            "downloaded_n",
            "not_applicable",
            "occurrence_audit_only",
            "input",
            "No GBIF occurrence download happens inside this compiler run.",
        ),
        row(
            "deduped_n",
            "not_applicable",
            "occurrence_audit_only",
            "input",
            "Deduplication belongs to the separate GBIF occurrence audit layer.",
        ),
        row("eligible_n", metrics.get("eligible_records", processed), processed, "compiler", "Records that reached deterministic gate evaluation."),
        row("candidate_n", metrics.get("candidate_records", 0), processed, "taxonomy", "Records with at least one supplied reference hit."),
        row("safe_n", metrics.get("safe_records", 0), processed, "taxonomy", "Records safe at species/genus/higher-rank level."),
        row(
            "publishable_candidate_n",
            metrics.get("publishable_candidate_records", 0),
            processed,
            "publication",
            "Safe records emitted into publishable review templates but not formal GBIF-ready.",
        ),
        row(
            "gbif_ready_n",
            metrics.get("gbif_ready_records", 0),
            processed,
            "publication",
            "Records that passed dataset-level metadata checks for formal GBIF-ready export.",
        ),
        row(
            "repair_required_n",
            metrics.get("repair_required_records", 0),
            processed,
            "publication",
            "Records blocked by molecular, occurrence, assay, backend or metadata gates.",
        ),
        row(
            "review_only_n",
            metrics.get("review_only_records", 0),
            processed,
            "publication",
            "Evidence retained for review but not exportable as occurrence rows.",
        ),
        row(
            "blocked_top_species_claims_n",
            metrics.get("blocked_or_downgraded_top_species_hits", metrics.get("blocked_species_claims", 0)),
            top_species,
            "safety",
            "Species-ranked top hits that were blocked or downgraded by fail-closed gates.",
        ),
        row(
            "hard_gate_failures_n",
            metrics.get("hard_gate_failures", 0),
            max(metrics.get("species_safe_records", 0), 1),
            "safety",
            "Species-safe records with any failed hard gate; must remain zero.",
        ),
    ]


def gate_status(value: bool) -> str:
    return "pass" if value else "fail"


def decision_rules() -> dict[str, Any]:
    return {
        "exact_match": "marker-profile-specific identity and queryCoverage thresholds",
        "close_match": "marker-profile-specific close threshold",
        "weak_match": "falls below marker-profile exact/close gates",
        "marker_profiles": MARKER_PROFILES,
        "assay_profiles": ASSAY_PROFILES,
        "ambiguity_test": "competitor is indistinguishable when delta mismatch rate <= 1.96 * combined standard error",
        "safe_rank": "lowest common ancestor of statistically indistinguishable hits",
        "barcode_gap": "species gate requires inter_min_distance - intra_max_distance > 0",
        "diagnostic_kmers": "species gate requires at least one query k-mer unique to the target taxon in the reference set",
        "diagnostic_false_positive_gate": "diagnostic support passes only when support_count >= 1 and p_false_positive <= alpha",
        "publication_readiness": {
            "occurrence_core_required": CORE_REQUIRED_FIELDS,
            "occurrence_core_recommended": CORE_RECOMMENDED_FIELDS,
            "dna_required": DNA_REQUIRED_FIELDS,
            "dataset_metadata": DATASET_METADATA_FIELDS,
        },
        "publication_buckets": {
            "gbif_ready": "safe taxonomic decision plus dataset-level metadata readiness",
            "publishable_candidate": "safe taxonomic decision and record-level metadata, but dataset metadata still needs review",
            "repair_required": "blocked by molecular, backend, assay, Occurrence core or DNA-derived metadata issues",
            "review_only": "kept as evidence context, not exportable as a GBIF occurrence row",
        },
    }


def build_reference_manifest(request: BarcodeCompilerRequest) -> dict[str, Any]:
    if request.reference_manifest:
        manifest = request.reference_manifest.model_dump()
    else:
        manifest = {
            "db_name": request.reference_database,
            "db_version": "not_supplied",
            "source": "request.reference_database",
            "accessed_at": datetime.now(timezone.utc).date().isoformat(),
            "doi_or_url": None,
            "license": None,
            "sha256": None,
        }
    compact = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    manifest["manifest_sha256"] = hashlib.sha256(compact.encode("utf-8")).hexdigest()
    return manifest


def build_source_provenance(
    request: BarcodeCompilerRequest,
    reference_manifest: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    backends = sorted(
        {
            str(record["metadata"].get("referenceSearchBackend"))
            for record in decisions
            if record["metadata"].get("referenceSearchBackend")
        }
    )
    return {
        "tool": "EcoGenesis Nexus",
        "layer": "Barcode-to-GBIF Evidence Compiler",
        "reference_database": request.reference_database,
        "reference_manifest_sha256": reference_manifest.get("manifest_sha256"),
        "reference_source": reference_manifest.get("source"),
        "reference_doi_or_url": reference_manifest.get("doi_or_url"),
        "reference_license": reference_manifest.get("license"),
        "reference_search_backends": backends,
        "degraded_backend_records": [
            record["sequence_id"]
            for record in decisions
            if is_degraded_reference_search(record["metadata"])
        ],
        "input_contract": (
            "Sequence ID, BLAST, VSEARCH or lab-pipeline hits are treated as source evidence. "
            "EcoGenesis computes bounded claims and publication readiness; it does not convert a top hit directly into species truth."
        ),
    }


def build_evidence_graph(pack: dict[str, Any]) -> dict[str, Any]:
    run_id = pack["run"]["run_id"]
    node_registry: dict[str, dict[str, Any]] = {}
    edges = []
    add_node(node_registry, {"id": f"run:{run_id}", "type": "run", "label": pack["summary"]["project_title"]})
    manifest_node = f"reference_manifest:{pack['reference_manifest']['manifest_sha256']}"
    add_node(node_registry, {"id": manifest_node, "type": "reference_manifest", "label": pack["reference_manifest"]["db_name"]})
    edges.append({"source": f"run:{run_id}", "target": manifest_node, "type": "frozen_against"})
    for record in pack["records"]:
        sequence_node = f"sequence:{record['sequence_id']}"
        assignment_node = f"assignment:{record['sequence_id']}"
        taxon = record["published_taxon"] if record["published_taxon"]["rank"] != "none" else record["candidate_taxon"]
        taxon_node = f"taxon:{taxon['rank']}:{taxon['name']}"
        boundary_node = f"claim_boundary:{record['sequence_id']}"
        add_node(node_registry, {"id": sequence_node, "type": "sequence", "label": record["sequence_id"], "md5": record["sequence_md5"]})
        add_node(node_registry, {"id": assignment_node, "type": "assignment", "label": record["decision_class"]})
        add_node(node_registry, {"id": taxon_node, "type": "taxon", "label": taxon["name"], "rank": taxon["rank"]})
        add_node(
            node_registry,
            {
                "id": boundary_node,
                "type": "claim_boundary",
                "label": record["claim_boundary"]["supported"],
                "publication_bucket": record.get("publication_bucket"),
            },
        )
        edges.extend(
            [
                {"source": f"run:{run_id}", "target": sequence_node, "type": "contains_sequence"},
                {"source": sequence_node, "target": assignment_node, "type": "receives_assignment"},
                {"source": assignment_node, "target": taxon_node, "type": "published_or_candidate_taxon"},
                {"source": assignment_node, "target": boundary_node, "type": "bounded_by"},
            ]
        )
        for blocker in record["blockers"]:
            blocker_node = f"blocker:{hashlib.sha1(blocker.encode('utf-8')).hexdigest()[:12]}"
            add_node(node_registry, {"id": blocker_node, "type": "blocker", "label": blocker})
            edges.append({"source": assignment_node, "target": blocker_node, "type": "blocked_by"})
        for hit in record["hits"][:5]:
            hit_node = f"hit:{record['sequence_id']}:{hit.get('reference_id') or hit['taxon']}"
            add_node(node_registry, {"id": hit_node, "type": "hit", "label": hit["taxon"], "identity": hit["identity"], "coverage": hit["query_coverage"]})
            edges.append({"source": sequence_node, "target": hit_node, "type": "matches_reference"})
    for artifact in pack.get("exports", []):
        artifact_node = f"artifact:{artifact['name']}"
        add_node(node_registry, {"id": artifact_node, "type": "artifact", "label": artifact["name"], "sha256": artifact.get("sha256")})
        edges.append({"source": f"run:{run_id}", "target": artifact_node, "type": "produces_artifact"})
    return {
        "meta": {
            "run_id": run_id,
            "ruleset_version": pack["run"]["ruleset_version"],
            "reference_manifest_sha256": pack["reference_manifest"]["manifest_sha256"],
            "created_at": pack["run"]["finished_at"],
        },
        "stats": {
            "sequence_count": len(pack["records"]),
            "safe_count": sum(1 for record in pack["records"] if record["decision_class"] in SAFE_TAXONOMIC_STATUSES),
            "blocked_count": sum(1 for record in pack["records"] if record["blockers"]),
        },
        "nodes": list(node_registry.values()),
        "edges": edges,
    }


def add_node(registry: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    registry.setdefault(node["id"], node)


def fingerprint_request(payload: dict[str, Any]) -> str:
    compact = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result


def format_threshold(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)
