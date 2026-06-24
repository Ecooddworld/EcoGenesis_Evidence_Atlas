from __future__ import annotations

import math
from typing import Any


SAFE_TAXONOMIC_STATUSES = {"species-safe", "genus-safe", "higher-rank-safe"}
HIGHER_RANKS = {"family", "order", "class", "phylum", "kingdom"}


def audit_pack_math(pack: dict[str, Any], *, scope: str = "current_pack") -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    records = pack.get("records", [])
    metrics = pack.get("metrics", {})

    require(checks, "records_present", bool(records), len(records))
    for record in records:
        audit_record_math(checks, record)
    audit_metrics(checks, records, metrics)
    audit_batch_invariants(checks, records)

    failed = [check for check in checks if check["status"] != "pass"]
    return {
        "schema": "ecogenesis.barcode.math_viability_audit.v1",
        "scope": scope,
        "summary": {
            "status": "pass" if not failed else "fail",
            "checks": len(checks),
            "failed": len(failed),
            "records": len(records),
        },
        "unit_contract": {
            "api_identity_query_coverage": "percent values in [0, 100]",
            "formula_identity_query_coverage": "normalized fractions p_identity=identity/100 and p_coverage=queryCoverage/100",
            "barcode_gap_distances": "fractions in [0, 1]",
            "diagnostic_probability": "probability in [0, 1]",
        },
        "method_boundary": [
            "The audit proves internal mathematical consistency for supplied evidence and frozen gates.",
            "It does not prove absolute species truth outside the supplied reference context.",
            "It does not infer presence, absence, abundance, distribution, phenotype or function without external evidence.",
            "Reference completeness remains a visible caveat when no external reference-coverage audit is attached.",
        ],
        "checks": checks,
    }


def audit_record_math(checks: list[dict[str, Any]], record: dict[str, Any]) -> None:
    sequence_id = record.get("sequence_id", "unknown")
    top = record.get("top_hit")
    profile = record.get("metadata_readiness", {}).get("marker_profile", {})

    expected_match = expected_match_type(top, profile)
    require(
        checks,
        f"{sequence_id}:match_gate_formula",
        record.get("match_type") == expected_match,
        {"actual": record.get("match_type"), "expected": expected_match},
    )
    if top:
        require(
            checks,
            f"{sequence_id}:percent_fraction_boundary",
            0 <= top.get("identity", -1) <= 100 and 0 <= top.get("query_coverage", -1) <= 100,
            {"identity": top.get("identity"), "queryCoverage": top.get("query_coverage")},
        )
    hit_metric_issues = [
        {
            "taxon": hit.get("taxon"),
            "identity": hit.get("identity"),
            "queryCoverage": hit.get("query_coverage"),
            "alignedLength": hit.get("aligned_length"),
        }
        for hit in record.get("hits", [])
        if not hit_metrics_in_bounds(hit)
    ]
    require(
        checks,
        f"{sequence_id}:all_hit_metric_units",
        not hit_metric_issues,
        hit_metric_issues or "all hit metrics in percent/positive-length bounds",
    )

    expected_uncertainty = expected_uncertainty_taxa(record)
    actual_uncertainty = sorted({hit.get("taxon") for hit in record.get("indistinguishable_hits", []) if hit.get("taxon")})
    require(
        checks,
        f"{sequence_id}:ambiguity_set_formula",
        actual_uncertainty == expected_uncertainty,
        {"actual": actual_uncertainty, "expected": expected_uncertainty},
    )

    expected_lca = expected_lca_taxon(record.get("indistinguishable_hits", []))
    expected_candidate = expected_candidate_after_marker_profile(record, expected_lca)
    candidate = record.get("candidate_taxon", {})
    require(
        checks,
        f"{sequence_id}:safe_lca_formula",
        not expected_candidate
        or (candidate.get("rank") == expected_candidate.get("rank") and candidate.get("name") == expected_candidate.get("name")),
        {"actual": candidate, "expected": expected_candidate, "raw_lca": expected_lca},
    )

    gap = record.get("barcode_gap", {})
    expected_gap = {"status": "not_evaluated", "gap": None} if not top else expected_barcode_gap(gap)
    require(
        checks,
        f"{sequence_id}:barcode_gap_formula",
        gap.get("status") == expected_gap.get("status") and rounded_equal(gap.get("gap"), expected_gap.get("gap"), digits=6),
        {"actual": gap, "expected": expected_gap},
    )

    diagnostic = record.get("diagnostic_kmers", {})
    expected_diagnostic = (
        {"status": "not_evaluated", "support_rate": 0, "p_false_positive": None}
        if not top
        else expected_diagnostic_gate(diagnostic)
    )
    require(
        checks,
        f"{sequence_id}:diagnostic_kmer_probability_formula",
        diagnostic_subset_matches(diagnostic, expected_diagnostic),
        {"actual": diagnostic, "expected": expected_diagnostic},
    )

    exact_pass = record.get("match_type") == "exact"
    ambiguity_pass = candidate.get("rank") == "species" and len(actual_uncertainty) == 1
    barcode_pass = gap.get("status") == "pass"
    diagnostic_pass = diagnostic.get("status") == "pass"
    marker_pass = profile.get("species_gate_pass") is True
    readiness = record.get("metadata_readiness", {})
    core_pass = readiness.get("core_pass") is True
    dna_pass = readiness.get("dna_pass") is True
    assay_pass = readiness.get("assay_gate", {}).get("assay_gate_pass") is True
    species_safe_hard_pass = all(
        [exact_pass, ambiguity_pass, barcode_pass, diagnostic_pass, marker_pass, core_pass, dna_pass, assay_pass]
    )
    require(
        checks,
        f"{sequence_id}:species_safe_implies_all_hard_gates",
        record.get("decision_class") != "species-safe" or species_safe_hard_pass,
        {
            "decisionClass": record.get("decision_class"),
            "exact": exact_pass,
            "ambiguity": ambiguity_pass,
            "barcodeGap": barcode_pass,
            "diagnosticKmer": diagnostic_pass,
            "marker": marker_pass,
            "core": core_pass,
            "dna": dna_pass,
            "assay": assay_pass,
        },
    )

    taxonomic_status = record.get("taxonomic_status")
    decision_class = record.get("decision_class")
    published_rank = record.get("published_taxon", {}).get("rank")
    if taxonomic_status in SAFE_TAXONOMIC_STATUSES and decision_class == "not-publishable":
        require(
            checks,
            f"{sequence_id}:metadata_cannot_publish_safe_taxon",
            published_rank == "none" and record.get("export_state") == "evidence_publishable_repair_required",
            {"publishedRank": published_rank, "exportState": record.get("export_state")},
        )
    require(
        checks,
        f"{sequence_id}:published_taxon_requires_safe_decision_class",
        published_rank == "none" or decision_class in SAFE_TAXONOMIC_STATUSES,
        {"decisionClass": decision_class, "publishedRank": published_rank},
    )


def audit_metrics(checks: list[dict[str, Any]], records: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    processed = len(records)
    species_safe = count(records, "decision_class", "species-safe")
    genus_safe = count(records, "decision_class", "genus-safe")
    higher_safe = count(records, "decision_class", "higher-rank-safe")
    not_publishable = count(records, "decision_class", "not-publishable")
    top_species = sum(1 for record in records if (record.get("top_hit") or {}).get("rank") == "species")
    blocked_species = sum(
        1
        for record in records
        if (record.get("top_hit") or {}).get("rank") == "species" and record.get("decision_class") != "species-safe"
    )
    publishable = sum(1 for record in records if record.get("published_taxon", {}).get("rank") != "none")

    expected = {
        "processed_records": processed,
        "species_safe_records": species_safe,
        "genus_safe_records": genus_safe,
        "higher_rank_safe_records": higher_safe,
        "not_publishable_records": not_publishable,
        "safe_rank_records": species_safe + genus_safe + higher_safe,
        "top_species_hits": top_species,
        "blocked_species_claims": blocked_species,
        "publishable_template_records": publishable,
        "species_safe_yield": round(species_safe / processed, 6) if processed else 0,
        "safe_rank_yield": round((species_safe + genus_safe + higher_safe) / processed, 6) if processed else 0,
        "molecular_evidence_conversion_yield": round(publishable / processed, 6) if processed else 0,
        "overclaim_prevention_rate": round(blocked_species / top_species, 6) if top_species else 0,
    }
    for key, value in expected.items():
        require(checks, f"metrics:{key}", metrics.get(key) == value, {"actual": metrics.get(key), "expected": value})


def audit_batch_invariants(checks: list[dict[str, Any]], records: list[dict[str, Any]]) -> None:
    require(
        checks,
        "batch:no_unsafe_species_export",
        all(
            not (
                (record.get("published_taxon", {}).get("rank") == "species")
                and record.get("decision_class") != "species-safe"
            )
            for record in records
        ),
        "published species rows checked",
    )
    require(
        checks,
        "batch:weak_and_no_match_never_publish",
        all(
            record.get("published_taxon", {}).get("rank") == "none"
            for record in records
            if record.get("taxonomic_status") in {"weak", "no-match", "ambiguous"}
        ),
        "weak/no-match/ambiguous rows checked",
    )


def expected_match_type(top: dict[str, Any] | None, profile: dict[str, Any]) -> str:
    if not top:
        return "no_match"
    identity = float(top.get("identity") or 0)
    coverage = float(top.get("query_coverage") or 0)
    if identity >= float(profile.get("identity_species_min") or 0) and coverage >= float(profile.get("coverage_species_min") or 0):
        return "exact"
    if (
        float(profile.get("identity_close_min") or 0) < identity < float(profile.get("identity_species_min") or 0)
        and coverage >= float(profile.get("coverage_close_min") or 0)
    ):
        return "close"
    return "weak"


def expected_uncertainty_taxa(record: dict[str, Any]) -> list[str]:
    hits = record.get("hits", [])
    if not hits:
        return []
    top = hits[0]
    fallback_length = int(record.get("sequence_length") or 1)
    top_d = mismatch_rate(top)
    top_se = standard_error(top, fallback_length)
    taxa = [top.get("taxon")]
    for hit in hits[1:]:
        delta = mismatch_rate(hit) - top_d
        boundary = 1.96 * math.sqrt(top_se**2 + standard_error(hit, fallback_length) ** 2)
        if delta <= boundary:
            taxa.append(hit.get("taxon"))
    return sorted({taxon for taxon in taxa if taxon})


def mismatch_rate(hit: dict[str, Any]) -> float:
    return max(0.0, min(1.0, 1 - float(hit.get("identity") or 0) / 100))


def standard_error(hit: dict[str, Any], fallback_length: int) -> float:
    d = mismatch_rate(hit)
    length = int(hit.get("aligned_length") or fallback_length or 1)
    return math.sqrt((d * (1 - d)) / length)


def expected_lca_taxon(hits: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not hits:
        return {"rank": "none", "name": "No match", "taxon_key": None}
    if len(hits) == 1:
        hit = hits[0]
        lineage = hit.get("lineage") or []
        rank = normalize_rank(hit.get("rank"))
        for item in reversed(lineage):
            if normalize_rank(item.get("rank")) == rank:
                return {"rank": rank, "name": item.get("name"), "taxon_key": item.get("taxon_key")}
        return {"rank": rank, "name": hit.get("taxon"), "taxon_key": hit.get("gbif_taxon_key")}
    lineages = [lineage_or_hit(hit) for hit in hits]
    shortest = min(len(items) for items in lineages)
    last_common = None
    for index in range(shortest):
        names = {str(items[index].get("name") or "").strip().lower() for items in lineages}
        ranks = {items[index]["rank"] for items in lineages}
        if "" not in names and len(names) == 1 and len(ranks) == 1:
            last_common = lineages[0][index]
        else:
            break
    return last_common or {"rank": "unranked", "name": "Ambiguous lineage", "taxon_key": None}


def expected_candidate_after_marker_profile(record: dict[str, Any], expected_lca: dict[str, Any] | None) -> dict[str, Any] | None:
    if not expected_lca:
        return expected_lca
    profile = record.get("metadata_readiness", {}).get("marker_profile", {})
    top = record.get("top_hit")
    if expected_lca.get("rank") == "species" and profile.get("species_gate_pass") is not True and top:
        genus = ancestor_from_hit_summary(top, "genus")
        return genus or expected_lca
    return expected_lca


def ancestor_from_hit_summary(hit: dict[str, Any], rank: str) -> dict[str, Any] | None:
    for item in hit.get("lineage") or []:
        if normalize_rank(item.get("rank")) == rank:
            return {"rank": rank, "name": item.get("name"), "taxon_key": item.get("taxon_key")}
    return None


def lineage_or_hit(hit: dict[str, Any]) -> list[dict[str, Any]]:
    lineage = hit.get("lineage") or []
    if lineage:
        return [
            {"rank": normalize_rank(item.get("rank")), "name": item.get("name"), "taxon_key": item.get("taxon_key")}
            for item in lineage
        ]
    return [{"rank": normalize_rank(hit.get("rank")), "name": hit.get("taxon"), "taxon_key": hit.get("gbif_taxon_key")}]


def normalize_rank(rank: Any) -> str:
    value = str(rank or "unranked").strip().lower()
    return value if value in {"kingdom", "phylum", "class", "order", "family", "genus", "species", "none"} else "unranked"


def hit_metrics_in_bounds(hit: dict[str, Any]) -> bool:
    try:
        identity = float(hit.get("identity"))
        coverage = float(hit.get("query_coverage"))
        aligned_length = hit.get("aligned_length")
        length_ok = aligned_length is None or int(aligned_length) > 0
    except (TypeError, ValueError):
        return False
    return 0 <= identity <= 100 and 0 <= coverage <= 100 and length_ok


def expected_barcode_gap(gap: dict[str, Any]) -> dict[str, Any]:
    intra = gap.get("intra_max_distance")
    inter = gap.get("inter_min_distance")
    if intra is None or inter is None:
        return {"status": "missing", "gap": None}
    value = float(inter) - float(intra)
    return {"status": "pass" if value > 0 else "fail", "gap": round(value, 6)}


def expected_diagnostic_gate(diagnostic: dict[str, Any]) -> dict[str, Any]:
    support = int(diagnostic.get("support_count") or 0)
    query_windows = int(diagnostic.get("query_window_count") or 0)
    diagnostic_count = int(diagnostic.get("diagnostic_kmer_count") or 0)
    k = diagnostic.get("k")
    alpha = float(diagnostic.get("alpha") or 0.01)
    if not k or diagnostic_count <= 0:
        return {
            "status": "missing" if support == 0 else diagnostic.get("status"),
            "support_rate": 0 if query_windows == 0 else round(support / max(query_windows, 1), 6),
            "p_false_positive": diagnostic.get("p_false_positive"),
        }
    p_false_positive = 1 - ((1 - min(1.0, diagnostic_count / (4 ** int(k)))) ** query_windows) if query_windows > 0 else 0.0
    if support < 1:
        status = "fail_no_support"
    elif p_false_positive > alpha:
        status = "fail_false_positive_risk"
    else:
        status = "pass"
    return {
        "status": status,
        "support_rate": round(support / max(query_windows, 1), 6),
        "expected_random_hits": round(query_windows * (diagnostic_count / (4 ** int(k))), 6),
        "p_false_positive": round(p_false_positive, 8),
    }


def diagnostic_subset_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    for key in ("status", "support_rate", "p_false_positive"):
        if key in expected and not rounded_equal(actual.get(key), expected.get(key), digits=8 if key == "p_false_positive" else 6):
            return False
    if expected.get("expected_random_hits") is not None and not rounded_equal(
        actual.get("expected_random_hits"), expected.get("expected_random_hits"), digits=6
    ):
        return False
    return True


def rounded_equal(left: Any, right: Any, *, digits: int = 6) -> bool:
    if left is None or right is None:
        return left is None and right is None
    try:
        return round(float(left), digits) == round(float(right), digits)
    except (TypeError, ValueError):
        return left == right


def count(records: list[dict[str, Any]], field: str, value: Any) -> int:
    return sum(1 for record in records if record.get(field) == value)


def require(checks: list[dict[str, Any]], name: str, predicate: bool, observed: Any) -> None:
    checks.append({"name": name, "status": "pass" if predicate else "fail", "observed": observed})
