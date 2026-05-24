from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
from typing import Any
from uuid import uuid4

from .artifacts import build_barcode_artifacts
from .schemas import BarcodeCompilerRequest, ReferenceHit, SequenceRecord
from .storage import save_barcode_artifacts, save_barcode_zip_artifact


CORE_REQUIRED_FIELDS = ["occurrenceID", "basisOfRecord", "scientificName", "eventDate"]
DNA_REQUIRED_FIELDS = ["marker", "sequenceID", "referenceDatabase", "identity", "queryCoverage", "methodOrSOP"]
HIGHER_RANKS = {"family", "order", "class", "phylum", "kingdom"}
SAFE_RANK_ORDER = ["kingdom", "phylum", "class", "order", "family", "genus", "species"]


def run_barcode_compiler(request: BarcodeCompilerRequest) -> dict[str, Any]:
    run_id = uuid4().hex
    started_at = datetime.now(timezone.utc)
    decisions = [decide_record(record, request) for record in request.records]
    metrics = summarize_decisions(decisions)
    finished_at = datetime.now(timezone.utc)
    request_payload = request.model_dump()

    pack: dict[str, Any] = {
        "run": {
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "tool": "Barcode-to-GBIF Evidence Compiler",
            "ruleset_version": request.ruleset_version,
            "request_fingerprint": fingerprint_request(request_payload),
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
            "blocked_species_claims": metrics["blocked_species_claims"],
            "verdict": build_run_verdict(metrics),
        },
        "decision_rules": decision_rules(),
        "metrics": metrics,
        "records": decisions,
        "request": request_payload,
    }
    pack["evidence_graph"] = build_evidence_graph(pack)
    artifacts = build_barcode_artifacts(pack)
    exports = save_barcode_artifacts(run_id, artifacts)
    zip_export = save_barcode_zip_artifact(run_id, artifacts)
    pack["exports"] = sorted([*exports, zip_export], key=lambda item: item["name"])
    pack["run"]["artifact_checksums"] = {item["name"]: item.get("sha256") for item in pack["exports"]}
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
    metadata = normalized_metadata(record, request)
    sequence = record.sequence
    sequence_length = len(sequence)
    blockers: list[str] = []
    actions: list[str] = []

    core_missing = missing_fields(metadata, CORE_REQUIRED_FIELDS)
    dna_missing = missing_fields(metadata, DNA_REQUIRED_FIELDS)
    core_pass = not core_missing
    dna_pass = not dna_missing
    publication_ready = core_pass and dna_pass

    if not hits:
        blockers.append("no reference hit returned")
        actions.append("Run the sequence against a marker-appropriate reference database and attach hit metrics.")
        return build_decision(
            record=record,
            metadata=metadata,
            hits=[],
            top_hit=None,
            sequence_length=sequence_length,
            match_type="no_match",
            safe_taxon={"rank": "none", "name": "No match"},
            indistinguishable_hits=[],
            barcode_gap_result={"status": "not_evaluated", "gap": None},
            diagnostic_result={"status": "not_evaluated", "support_count": 0, "support_rate": 0, "k": None},
            taxonomic_status="no-match",
            decision_class="not-publishable" if not publication_ready else "no-match",
            core_pass=core_pass,
            dna_pass=dna_pass,
            core_missing=core_missing,
            dna_missing=dna_missing,
            blockers=[*blockers, *metadata_blockers(core_missing, dna_missing)],
            actions=[*actions, *metadata_actions(core_missing, dna_missing)],
        )

    top_hit = hits[0]
    match_type = classify_match(top_hit)
    indistinguishable_hits = ambiguity_set(top_hit, hits, fallback_length=sequence_length)
    safe_taxon = lowest_common_ancestor(indistinguishable_hits)
    barcode_gap_result = evaluate_barcode_gap(record)
    diagnostic_result = evaluate_diagnostic_kmers(record)
    taxonomic_status = classify_taxonomic_status(
        match_type=match_type,
        safe_taxon=safe_taxon,
        indistinguishable_hits=indistinguishable_hits,
        barcode_gap_result=barcode_gap_result,
        diagnostic_result=diagnostic_result,
        top_hit=top_hit,
    )

    if match_type != "exact":
        blockers.append("species claim blocked: top hit does not pass exact match gate identity >= 99% and query coverage >= 80%")
        actions.append("Use a longer/cleaner marker sequence or treat the assignment below species rank.")
    if top_hit.query_coverage < 80:
        blockers.append("species claim blocked: query coverage < 80%")
    if top_hit.identity < 99:
        blockers.append("species claim blocked: identity < 99%")
    if len({hit.taxon for hit in indistinguishable_hits}) > 1 and safe_taxon["rank"] != "species":
        blockers.append(f"species claim blocked: statistically indistinguishable competitors collapse the safe rank to {safe_taxon['rank']}")
        actions.append(f"Publish the molecular assignment at {safe_taxon['rank']} rank unless additional evidence resolves the ambiguity.")
    if barcode_gap_result["status"] != "pass":
        blockers.append(f"species claim blocked: barcode gap {barcode_gap_result['status']}")
        actions.append("Attach reference-set intra/inter distances or use a marker/reference set with positive species separation.")
    if diagnostic_result["status"] != "pass":
        blockers.append(f"species claim blocked: diagnostic k-mer support {diagnostic_result['status']}")
        actions.append("Attach diagnostic k-mers or keep the assignment below species rank.")

    blockers.extend(metadata_blockers(core_missing, dna_missing))
    actions.extend(metadata_actions(core_missing, dna_missing))

    decision_class = taxonomic_status
    if not publication_ready:
        decision_class = "not-publishable"

    return build_decision(
        record=record,
        metadata=metadata,
        hits=hits,
        top_hit=top_hit,
        sequence_length=sequence_length,
        match_type=match_type,
        safe_taxon=safe_taxon,
        indistinguishable_hits=indistinguishable_hits,
        barcode_gap_result=barcode_gap_result,
        diagnostic_result=diagnostic_result,
        taxonomic_status=taxonomic_status,
        decision_class=decision_class,
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


def hit_sort_key(hit: ReferenceHit) -> tuple[float, float, float]:
    bit_score = hit.bit_score if hit.bit_score is not None else hit.identity * hit.query_coverage
    return (float(bit_score), float(hit.identity), float(hit.query_coverage))


def classify_match(hit: ReferenceHit) -> str:
    if hit.identity >= 99 and hit.query_coverage >= 80:
        return "exact"
    if 90 < hit.identity < 99 and hit.query_coverage >= 80:
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
        return {"status": "missing", "support_count": 0, "support_rate": 0, "k": None, "expected_random_hits": None}
    diagnostic_kmers = {item.upper() for item in record.diagnostic.diagnostic_kmers if item}
    if not diagnostic_kmers:
        return {"status": "missing", "support_count": 0, "support_rate": 0, "k": record.diagnostic.k, "expected_random_hits": None}
    k = record.diagnostic.k or infer_k(record.diagnostic.reference_total_windows, record.diagnostic.epsilon, diagnostic_kmers)
    query_kmers = set(kmers(record.sequence, k))
    support_count = len(query_kmers & diagnostic_kmers)
    support_rate = support_count / max(len(query_kmers), 1)
    expected_random_hits = expected_diagnostic_collisions(len(query_kmers), len(diagnostic_kmers), k)
    return {
        "status": "pass" if support_count > 0 else "fail",
        "support_count": support_count,
        "support_rate": round(support_rate, 6),
        "k": k,
        "query_window_count": len(query_kmers),
        "diagnostic_kmer_count": len(diagnostic_kmers),
        "expected_random_hits": round(expected_random_hits, 6),
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


def classify_taxonomic_status(
    *,
    match_type: str,
    safe_taxon: dict[str, Any],
    indistinguishable_hits: list[ReferenceHit],
    barcode_gap_result: dict[str, Any],
    diagnostic_result: dict[str, Any],
    top_hit: ReferenceHit,
) -> str:
    safe_rank = safe_taxon["rank"]
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


def metadata_blockers(core_missing: list[str], dna_missing: list[str]) -> list[str]:
    blockers = []
    for field in core_missing:
        blockers.append(f"publication blocked: missing required Occurrence core field {field}")
    for field in dna_missing:
        blockers.append(f"publication blocked: missing DNA-derived evidence field {field}")
    return blockers


def metadata_actions(core_missing: list[str], dna_missing: list[str]) -> list[str]:
    actions = []
    if core_missing:
        actions.append("Complete required Darwin Core Occurrence core fields before GBIF publication.")
    if dna_missing:
        actions.append("Attach marker, sequence ID, reference database, identity, coverage and method/SOP metadata.")
    return actions


def build_decision(
    *,
    record: SequenceRecord,
    metadata: dict[str, Any],
    hits: list[ReferenceHit],
    top_hit: ReferenceHit | None,
    sequence_length: int,
    match_type: str,
    safe_taxon: dict[str, Any],
    indistinguishable_hits: list[ReferenceHit],
    barcode_gap_result: dict[str, Any],
    diagnostic_result: dict[str, Any],
    taxonomic_status: str,
    decision_class: str,
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
        "publication_status": "gbif-ready" if core_pass and dna_pass and taxonomic_status in {"species-safe", "genus-safe", "higher-rank-safe"} else "not-ready",
        "match_type": match_type,
        "safe_taxon": safe_taxon,
        "top_hit": hit_summary(top_hit),
        "indistinguishable_hits": [hit_summary(hit) for hit in indistinguishable_hits],
        "barcode_gap": barcode_gap_result,
        "diagnostic_kmers": diagnostic_result,
        "metadata_readiness": {
            "core_pass": core_pass,
            "dna_pass": dna_pass,
            "core_missing": core_missing,
            "dna_missing": dna_missing,
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
    species_safe = sum(1 for item in decisions if item["decision_class"] == "species-safe")
    genus_safe = sum(1 for item in decisions if item["decision_class"] == "genus-safe")
    higher_rank_safe = sum(1 for item in decisions if item["decision_class"] == "higher-rank-safe")
    ambiguous = sum(1 for item in decisions if item["taxonomic_status"] == "ambiguous")
    weak = sum(1 for item in decisions if item["taxonomic_status"] == "weak")
    no_match = sum(1 for item in decisions if item["taxonomic_status"] == "no-match")
    not_publishable = sum(1 for item in decisions if item["decision_class"] == "not-publishable")
    blocked_species = sum(
        1
        for item in decisions
        if item["top_hit"] and item["top_hit"]["rank"] == "species" and item["decision_class"] != "species-safe"
    )
    not_ready_with_blockers = sum(1 for item in decisions if item["publication_status"] == "not-ready" and item["blockers"])
    not_ready = sum(1 for item in decisions if item["publication_status"] == "not-ready")
    return {
        "processed_records": processed,
        "processing_coverage": 1 if processed else 0,
        "species_safe_records": species_safe,
        "genus_safe_records": genus_safe,
        "higher_rank_safe_records": higher_rank_safe,
        "ambiguous_records": ambiguous,
        "weak_records": weak,
        "no_match_records": no_match,
        "not_publishable_records": not_publishable,
        "species_safe_yield": round(species_safe / processed, 6) if processed else 0,
        "blocked_species_claims": blocked_species,
        "overclaim_prevention_proxy": 1 if blocked_species else None,
        "publication_repair_efficiency": round(not_ready_with_blockers / not_ready, 6) if not_ready else 1,
    }


def build_run_verdict(metrics: dict[str, Any]) -> str:
    if metrics["species_safe_records"]:
        return "At least one sequence is species-safe and GBIF-ready under the frozen molecular evidence gates."
    if metrics["genus_safe_records"] or metrics["higher_rank_safe_records"]:
        return "The run produced safe downgraded molecular evidence, but no species-level publication candidate."
    return "The run correctly blocked species-level publication claims."


def decision_rules() -> dict[str, Any]:
    return {
        "exact_match": "identity >= 99% and queryCoverage >= 80%",
        "close_match": "90% < identity < 99% and queryCoverage >= 80%",
        "weak_match": "identity < 90% or queryCoverage < 80%",
        "ambiguity_test": "competitor is indistinguishable when delta mismatch rate <= 1.96 * combined standard error",
        "safe_rank": "lowest common ancestor of statistically indistinguishable hits",
        "barcode_gap": "species gate requires inter_min_distance - intra_max_distance > 0",
        "diagnostic_kmers": "species gate requires at least one query k-mer unique to the target taxon in the reference set",
        "publication_readiness": {
            "occurrence_core_required": CORE_REQUIRED_FIELDS,
            "dna_required": DNA_REQUIRED_FIELDS,
        },
    }


def build_evidence_graph(pack: dict[str, Any]) -> dict[str, Any]:
    run_id = pack["run"]["run_id"]
    nodes = [{"id": f"run:{run_id}", "type": "run", "label": pack["summary"]["project_title"]}]
    edges = []
    for record in pack["records"]:
        sequence_node = f"sequence:{record['sequence_id']}"
        assignment_node = f"assignment:{record['sequence_id']}"
        taxon_node = f"taxon:{record['safe_taxon']['rank']}:{record['safe_taxon']['name']}"
        nodes.extend(
            [
                {"id": sequence_node, "type": "sequence", "label": record["sequence_id"], "md5": record["sequence_md5"]},
                {"id": assignment_node, "type": "assignment", "label": record["decision_class"]},
                {"id": taxon_node, "type": "taxon", "label": record["safe_taxon"]["name"], "rank": record["safe_taxon"]["rank"]},
            ]
        )
        edges.extend(
            [
                {"source": f"run:{run_id}", "target": sequence_node, "type": "contains_sequence"},
                {"source": sequence_node, "target": assignment_node, "type": "receives_assignment"},
                {"source": assignment_node, "target": taxon_node, "type": "safe_taxon"},
            ]
        )
        for hit in record["hits"][:5]:
            hit_node = f"hit:{record['sequence_id']}:{hit.get('reference_id') or hit['taxon']}"
            nodes.append({"id": hit_node, "type": "hit", "label": hit["taxon"], "identity": hit["identity"], "coverage": hit["query_coverage"]})
            edges.append({"source": sequence_node, "target": hit_node, "type": "matches_reference"})
    return {"nodes": nodes, "edges": edges}


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
