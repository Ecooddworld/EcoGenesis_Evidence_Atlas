from __future__ import annotations

import csv
import html
import io
import json
import re
from typing import Any

from app.barcode.math_audit import audit_pack_math
from app.gseg.artifacts import ArtifactContent, build_gseg_gsig_artifacts


def build_barcode_artifacts(pack: dict[str, Any]) -> dict[str, ArtifactContent]:
    artifacts: dict[str, ArtifactContent] = {
        "evidence_pack.json": json.dumps(pack, indent=2, ensure_ascii=False),
        "run.json": json.dumps(pack["run"], indent=2, ensure_ascii=False),
        "reference_manifest.json": json.dumps(pack["reference_manifest"], indent=2, ensure_ascii=False),
        "source_provenance_manifest.json": json.dumps(pack.get("source_provenance", {}), indent=2, ensure_ascii=False),
        "data_accounting_ledger.csv": table_csv(pack.get("data_accounting_ledger", [])),
        "sequence_safety_table.csv": sequence_safety_csv(pack),
        "state_machine_audit.csv": state_machine_audit_csv(pack),
        "claim_boundaries.csv": claim_boundaries_csv(pack),
        "segment_overlap_report.csv": segment_overlap_report_csv(pack),
        "safe_taxonomic_assignments.csv": safe_assignments_csv(pack),
        "review_taxonomic_hints.csv": review_hints_csv(pack),
        "ambiguous_sequences.csv": filtered_sequences_csv(pack, {"ambiguous", "genus-safe", "higher-rank-safe"}),
        "barcode_gap_report.csv": barcode_gap_csv(pack),
        "diagnostic_kmer_report.csv": diagnostic_kmer_csv(pack),
        "gbif_backbone_matches.csv": gbif_matches_csv(pack),
        "publication_blockers.csv": blockers_csv(pack),
        "repair_plan.csv": table_csv(pack.get("repair_plan", [])),
        "metadata_bottlenecks.csv": table_csv(pack.get("metadata_bottlenecks", [])),
        "reference_gap_index.csv": table_csv(pack.get("reference_gap_index", [])),
        "reference_completeness_audit.csv": reference_completeness_audit_csv(pack),
        "marker_profile_audit.csv": marker_profile_audit_csv(pack),
        "assay_gate_audit.csv": assay_gate_audit_csv(pack),
        "dna_extension_readiness.csv": dna_extension_readiness_csv(pack),
        "repair_gain_estimates.csv": table_csv(pack.get("repair_plan", [])),
        "hard_gate_audit.csv": table_csv(pack.get("hard_gate_audit", [])),
        "naive_top_hit_overclaims.csv": table_csv(pack.get("naive_top_hit_overclaims", [])),
        "dwc_occurrence_core_template.csv": occurrence_core_csv(pack, publishable_only=False),
        "dwc_occurrence_core_publishable.csv": occurrence_core_csv(pack, publishable_only=True),
        "dwc_occurrence_core_gbif_ready.csv": occurrence_core_csv(pack, publishable_only=True, gbif_ready_only=True),
        "dwc_occurrence_core_review.csv": occurrence_core_csv(pack, publishable_only=False),
        "dwc_occurrence_core_review_or_repair.csv": occurrence_review_or_repair_csv(pack),
        "dna_derived_extension_template.csv": dna_extension_csv(pack, publishable_only=False),
        "dna_derived_extension_publishable.csv": dna_extension_csv(pack, publishable_only=True),
        "dna_derived_extension_gbif_ready.csv": dna_extension_csv(pack, publishable_only=True, gbif_ready_only=True),
        "molecular_evidence_report.html": molecular_report_html(pack),
        "methods_text.md": methods_text_md(pack),
        "citations.md": citations_md(pack),
        "evidence_graph.json": json.dumps(pack["evidence_graph"], indent=2, ensure_ascii=False),
        "nexus_v3_summary.json": json.dumps(pack["nexus_v3"], indent=2, ensure_ascii=False),
        "external_tool_adapter_matrix.csv": external_tool_adapter_matrix_csv(),
        "proof_by_failure_modes.md": proof_by_failure_modes_md(pack),
        "math_viability_audit.json": json.dumps(audit_pack_math(pack), indent=2, ensure_ascii=False),
    }
    artifacts.update(build_gseg_gsig_artifacts(pack))
    return artifacts


def sequence_safety_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        top = record["top_hit"] or {}
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "decisionClass": record["decision_class"],
                "taxonomicStatus": record["taxonomic_status"],
                "publicationStatus": record["publication_status"],
                "publicationStage": record["publication_stage"],
                "publicationBucket": record.get("publication_bucket"),
                "exportState": record.get("export_state"),
                "referenceCompletenessStatus": record.get("reference_completeness", {}).get("rci2_status"),
                "markerProfile": record["metadata_readiness"]["marker_profile"]["profile_id"],
                "assayType": record["metadata_readiness"]["assay_gate"]["assay_type"],
                "candidateTaxon": record["candidate_taxon"]["name"],
                "candidateRank": record["candidate_taxon"]["rank"],
                "publishedTaxon": record["published_taxon"]["name"],
                "publishedRank": record["published_taxon"]["rank"],
                "matchType": record["match_type"],
                "topHit": top.get("taxon"),
                "identity": top.get("identity"),
                "queryCoverage": top.get("query_coverage"),
                "barcodeGap": record["barcode_gap"].get("gap"),
                "diagnosticKmerSupport": record["diagnostic_kmers"].get("support_count"),
                "diagnosticPFalsePositive": record["diagnostic_kmers"].get("p_false_positive"),
                "blockers": "; ".join(record["blockers"]),
            }
        )
    return write_csv(rows)


def state_machine_audit_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "taxonomicStatus": record["taxonomic_status"],
                "decisionClass": record["decision_class"],
                "publicationStatus": record["publication_status"],
                "publicationStage": record["publication_stage"],
                "publicationBucket": record.get("publication_bucket"),
                "exportState": record.get("export_state"),
                "candidateTaxon": record["candidate_taxon"]["name"],
                "candidateRank": record["candidate_taxon"]["rank"],
                "publishedTaxon": record["published_taxon"]["name"],
                "publishedRank": record["published_taxon"]["rank"],
                "stateExplanation": export_state_explanation(record),
            }
        )
    return write_csv(rows)


def claim_boundaries_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        boundary = record.get("claim_boundary", {})
        evidence = boundary.get("evidence_fields", {})
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "decisionClass": record["decision_class"],
                "publicationBucket": record.get("publication_bucket"),
                "exportState": record.get("export_state"),
                "supported": boundary.get("supported"),
                "referenceContext": boundary.get("reference_context"),
                "publication": boundary.get("publication"),
                "topHit": evidence.get("top_hit"),
                "competitorCount": evidence.get("competitor_count"),
                "lcaSafeRank": evidence.get("lca_safe_rank"),
                "barcodeGapStatus": evidence.get("barcode_gap_status"),
                "barcodeGap": evidence.get("barcode_gap"),
                "diagnosticKmerStatus": evidence.get("diagnostic_kmer_status"),
                "diagnosticKmerSupport": evidence.get("diagnostic_kmer_support"),
                "markerProfile": evidence.get("marker_profile"),
                "rationale": boundary.get("evidence_rationale"),
                "notSupported": "; ".join(boundary.get("not_supported", [])),
                "boundaryText": boundary.get("boundary_text"),
            }
        )
    return write_csv(rows)


def segment_overlap_report_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        for hit in record["hits"]:
            rows.append(
                {
                    "sequenceID": record["sequence_id"],
                    "segmentStart": 1,
                    "segmentEnd": record["sequence_length"],
                    "segmentLength": record["sequence_length"],
                    "referenceID": hit.get("reference_id"),
                    "taxon": hit.get("taxon"),
                    "rank": hit.get("rank"),
                    "identityPercent": hit.get("identity"),
                    "queryCoveragePercent": hit.get("query_coverage"),
                    "alignedLength": hit.get("aligned_length"),
                    "safeTaxon": record["safe_taxon"]["name"],
                    "safeRank": record["safe_taxon"]["rank"],
                    "claimBoundary": record.get("claim_boundary", {}).get("supported"),
                }
            )
    return write_csv(rows)


def safe_assignments_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        if record["decision_class"] not in {"species-safe", "genus-safe", "higher-rank-safe"}:
            continue
        if record["published_taxon"]["rank"] == "none":
            continue
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "acceptedScientificName": record["published_taxon"]["name"],
                "taxonRank": record["published_taxon"]["rank"],
                "decisionClass": record["decision_class"],
                "profile_id": record["metadata_readiness"]["marker_profile"]["profile_id"],
                "exportState": record.get("export_state"),
                "basis": "deterministic identity/coverage, ambiguity LCA, barcode gap, diagnostic k-mer and GBIF metadata gates",
            }
        )
    return write_csv(rows)


def review_hints_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        if record["published_taxon"]["rank"] != "none":
            continue
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "decisionClass": record["decision_class"],
                "candidateTaxon": record["candidate_taxon"]["name"],
                "candidateRank": record["candidate_taxon"]["rank"],
                "publicationStage": record["publication_stage"],
                "reviewReason": "; ".join(record["blockers"]),
            }
        )
    return write_csv(rows)


def filtered_sequences_csv(pack: dict[str, Any], statuses: set[str]) -> str:
    rows = [
        {
            "sequenceID": record["sequence_id"],
            "taxonomicStatus": record["taxonomic_status"],
            "decisionClass": record["decision_class"],
            "candidateTaxon": record["candidate_taxon"]["name"],
            "candidateRank": record["candidate_taxon"]["rank"],
            "publishedTaxon": record["published_taxon"]["name"],
            "publishedRank": record["published_taxon"]["rank"],
            "indistinguishableHits": "; ".join(hit["taxon"] for hit in record["indistinguishable_hits"]),
            "blockers": "; ".join(record["blockers"]),
        }
        for record in pack["records"]
        if record["taxonomic_status"] in statuses
    ]
    return write_csv(rows)


def barcode_gap_csv(pack: dict[str, Any]) -> str:
    return write_csv(
        [
            {
                "sequenceID": record["sequence_id"],
                "status": record["barcode_gap"]["status"],
                "intraMaxDistance": record["barcode_gap"].get("intra_max_distance"),
                "interMinDistance": record["barcode_gap"].get("inter_min_distance"),
                "barcodeGap": record["barcode_gap"].get("gap"),
            }
            for record in pack["records"]
        ]
    )


def diagnostic_kmer_csv(pack: dict[str, Any]) -> str:
    return write_csv(
        [
            {
                "sequenceID": record["sequence_id"],
                "status": record["diagnostic_kmers"]["status"],
                "k": record["diagnostic_kmers"].get("k"),
                "queryWindowCount": record["diagnostic_kmers"].get("query_window_count"),
                "diagnosticKmerCount": record["diagnostic_kmers"].get("diagnostic_kmer_count"),
                "supportCount": record["diagnostic_kmers"].get("support_count"),
                "supportRate": record["diagnostic_kmers"].get("support_rate"),
                "expectedRandomHits": record["diagnostic_kmers"].get("expected_random_hits"),
                "pFalsePositive": record["diagnostic_kmers"].get("p_false_positive"),
                "alpha": record["diagnostic_kmers"].get("alpha"),
            }
            for record in pack["records"]
        ]
    )


def gbif_matches_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        for hit in record["hits"]:
            rows.append(
                {
                    "sequenceID": record["sequence_id"],
                    "taxon": hit["taxon"],
                    "rank": hit["rank"],
                    "gbifTaxonKey": hit.get("gbif_taxon_key"),
                    "identity": hit["identity"],
                    "queryCoverage": hit["query_coverage"],
                    "referenceDatabase": hit.get("reference_database"),
                    "referenceID": hit.get("reference_id"),
                }
            )
    return write_csv(rows)


def blockers_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        for blocker in record["blockers"]:
            rows.append({"sequenceID": record["sequence_id"], **structured_blocker(blocker, record)})
    return write_csv(rows)


def structured_blocker(blocker: str, record: dict[str, Any]) -> dict[str, Any]:
    lowered = blocker.lower()
    field = blocker_field(blocker)
    if "occurrence core" in lowered:
        kind = "occurrence_core"
    elif "dna-derived" in lowered or "dna derived" in lowered:
        kind = "dna_extension"
    elif "dataset metadata" in lowered or "doi" in lowered or "publisher" in lowered:
        kind = "dataset_metadata"
    elif "assay gate" in lowered or "contamination" in lowered or "control" in lowered:
        kind = "assay"
    elif "reference" in lowered or "barcode gap" in lowered or "diagnostic k-mer" in lowered:
        kind = "reference_or_molecular_qc"
    elif "marker profile" in lowered or "identity" in lowered or "query coverage" in lowered or "scientificname conflicts" in lowered:
        kind = "taxonomic"
    else:
        kind = "publication"
    severity = "hard" if "blocked" in lowered or "species claim" in lowered else "review"
    taxonomy_safe = record["taxonomic_status"] in {"species-safe", "genus-safe", "higher-rank-safe"}
    if taxonomy_safe and kind in {"occurrence_core", "dna_extension", "dataset_metadata", "assay", "publication"}:
        unlockable = "yes_after_repair"
    elif kind in {"taxonomic", "reference_or_molecular_qc"}:
        unlockable = "requires_new_molecular_or_reference_evidence"
    else:
        unlockable = "review"
    return {
        "blocker.kind": kind,
        "severity": severity,
        "field": field,
        "blocker": blocker,
        "action": best_action_for_blocker(blocker, record.get("actions", [])),
        "unlockable": unlockable,
        "taxonomicStatus": record["taxonomic_status"],
        "publicationBucket": record.get("publication_bucket"),
        "exportState": record.get("export_state"),
    }


def blocker_field(blocker: str) -> str:
    patterns = [
        r"field ([A-Za-z0-9_]+)",
        r"query coverage",
        r"identity",
        r"barcode gap",
        r"diagnostic k-mer",
        r"marker profile",
        r"reference search backend",
    ]
    for pattern in patterns:
        match = re.search(pattern, blocker, flags=re.IGNORECASE)
        if not match:
            continue
        if match.groups():
            return match.group(1)
        return pattern.replace(r"\-", "-").replace(" ", "_")
    return ""


def best_action_for_blocker(blocker: str, actions: list[str]) -> str:
    lowered = blocker.lower()
    for action in actions:
        action_lower = action.lower()
        if "occurrence core" in lowered and "darwin core" in action_lower:
            return action
        if "dna-derived" in lowered and "dna-derived" in action_lower:
            return action
        if "reference" in lowered and "reference" in action_lower:
            return action
        if "marker" in lowered and "marker" in action_lower:
            return action
        if "assay" in lowered and "assay" in action_lower:
            return action
    return actions[0] if actions else "Review the blocker and attach missing evidence before export."


def export_state_explanation(record: dict[str, Any]) -> str:
    state = record.get("export_state")
    if state == "formal_gbif_ready":
        return "Safe taxonomic decision plus dataset-level metadata gates; formal GBIF-ready export row is allowed."
    if state == "dwc_template_ready":
        return "Safe taxonomic decision with a non-empty published taxon; publishable template row is allowed, dataset metadata still needs review."
    if state == "evidence_publishable_repair_required":
        return "Taxonomic evidence is bounded as safe, but occurrence/DNA/assay metadata must be repaired before export."
    if state == "review_only":
        return "Record is retained as evidence context or expert review material, not an occurrence export row."
    return "Record is blocked from publication export in this run."


def reference_completeness_audit_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        completeness = record.get("reference_completeness", {})
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "status": completeness.get("status"),
                "rci2Status": completeness.get("rci2_status"),
                "referenceContext": completeness.get("reference_context"),
                "closeRelativeCoverage": completeness.get("close_relative_coverage"),
                "sequenceQuality": completeness.get("sequence_quality"),
                "geographicCoverage": completeness.get("geographic_coverage"),
                "perSpeciesDepth": completeness.get("per_species_depth"),
                "taxonomicStability": completeness.get("taxonomic_stability"),
                "candidateSpeciesInHitTable": completeness.get("candidate_species_in_hit_table"),
                "claimScope": completeness.get("claim_scope"),
            }
        )
    return write_csv(rows)


def marker_profile_audit_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        profile = record["metadata_readiness"]["marker_profile"]
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "markerProfile": profile["profile_id"],
                "profileLabel": profile["profile_label"],
                "markerFamily": profile["marker_family"],
                "codingMarker": profile["coding_marker"],
                "alignedSpan": profile["aligned_span"],
                "minAlignedLength": profile["min_aligned_length"],
                "maxAlignedLength": profile["max_aligned_length"],
                "lengthPass": profile["length_pass"],
                "speciesClaimAllowed": profile["species_claim_allowed"],
                "speciesGatePass": profile["species_gate_pass"],
                "identitySpeciesMin": profile["identity_species_min"],
                "coverageSpeciesMin": profile["coverage_species_min"],
                "targetGene": profile["target_gene"],
                "targetSubfragment": profile["target_subfragment"],
                "profileBlockers": "; ".join(profile["profile_blockers"]),
                "profileWarnings": "; ".join(profile["profile_warnings"]),
                "claimCaveat": profile["claim_caveat"],
            }
        )
    return write_csv(rows)


def assay_gate_audit_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        assay = record["metadata_readiness"]["assay_gate"]
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "assayType": assay["assay_type"],
                "assayLabel": assay["assay_label"],
                "assayGatePass": assay["assay_gate_pass"],
                "publicationBlocking": assay["assay_publication_blocking"],
                "requiredMissing": "; ".join(assay["assay_required_missing"]),
                "recommendedMissing": "; ".join(assay["assay_recommended_missing"]),
                "assayBlockers": "; ".join(assay["assay_blockers"]),
                "claimCaveat": assay["claim_caveat"],
            }
        )
    return write_csv(rows)


def dna_extension_readiness_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        readiness = record["metadata_readiness"]
        metadata = record["metadata"]
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "highPriorityPass": readiness["dna_extension_high_priority_pass"],
                "missingFields": "; ".join(readiness["dna_extension_high_priority_missing"]),
                "eventID": metadata.get("eventID"),
                "materialSampleID": metadata.get("materialSampleID"),
                "target_gene": metadata.get("target_gene"),
                "target_subfragment": metadata.get("target_subfragment"),
                "pcr_primer_forward": metadata.get("pcr_primer_forward"),
                "pcr_primer_reverse": metadata.get("pcr_primer_reverse"),
                "seq_meth": metadata.get("seq_meth"),
                "otu_class_appr": metadata.get("otu_class_appr"),
                "otu_seq_comp_appr": metadata.get("otu_seq_comp_appr"),
                "otu_db": metadata.get("otu_db"),
                "sop": metadata.get("sop"),
            }
        )
    return write_csv(rows)


def table_csv(rows: list[dict[str, Any]]) -> str:
    return write_csv(rows)


def occurrence_core_csv(pack: dict[str, Any], *, publishable_only: bool, gbif_ready_only: bool = False) -> str:
    rows = []
    for record in pack["records"]:
        if gbif_ready_only and record.get("publication_bucket") != "gbif_ready":
            continue
        if publishable_only and record["published_taxon"]["rank"] == "none":
            continue
        metadata = record["metadata"]
        taxon = record["published_taxon"]
        rows.append(
            {
                "occurrenceID": metadata.get("occurrenceID"),
                "eventID": metadata.get("eventID"),
                "materialSampleID": metadata.get("materialSampleID"),
                "basisOfRecord": metadata.get("basisOfRecord") or "MaterialSample",
                "scientificName": "" if taxon["rank"] == "none" else taxon["name"],
                "taxonRank": "" if taxon["rank"] == "none" else taxon["rank"],
                "eventDate": metadata.get("eventDate"),
                "countryCode": metadata.get("countryCode"),
                "decimalLatitude": metadata.get("decimalLatitude"),
                "decimalLongitude": metadata.get("decimalLongitude"),
                "geodeticDatum": metadata.get("geodeticDatum"),
                "coordinateUncertaintyInMeters": metadata.get("coordinateUncertaintyInMeters"),
                "occurrenceStatus": metadata.get("occurrenceStatus"),
                "organismQuantity": metadata.get("organismQuantity"),
                "organismQuantityType": metadata.get("organismQuantityType"),
                "verbatimIdentification": record["candidate_taxon"]["name"],
                "candidateTaxonRank": record["candidate_taxon"]["rank"],
                "publicationStage": record["publication_stage"],
                "publicationBucket": record.get("publication_bucket"),
                "identificationRemarks": identification_remarks(record, pack),
            }
        )
    return write_csv(rows)


def occurrence_review_or_repair_csv(pack: dict[str, Any]) -> str:
    rows = []
    for record in pack["records"]:
        if record["published_taxon"]["rank"] != "none":
            continue
        metadata = record["metadata"]
        rows.append(
            {
                "occurrenceID": metadata.get("occurrenceID"),
                "eventID": metadata.get("eventID"),
                "materialSampleID": metadata.get("materialSampleID"),
                "basisOfRecord": metadata.get("basisOfRecord") or "MaterialSample",
                "verbatimIdentification": record["candidate_taxon"]["name"],
                "candidateTaxonRank": record["candidate_taxon"]["rank"],
                "decisionClass": record["decision_class"],
                "publicationStage": record["publication_stage"],
                "blockers": "; ".join(record["blockers"]),
                "repairActions": "; ".join(record["actions"]),
            }
        )
    return write_csv(rows)


def dna_extension_csv(pack: dict[str, Any], *, publishable_only: bool, gbif_ready_only: bool = False) -> str:
    rows = []
    for record in pack["records"]:
        if gbif_ready_only and record.get("publication_bucket") != "gbif_ready":
            continue
        if publishable_only and record["published_taxon"]["rank"] == "none":
            continue
        metadata = record["metadata"]
        top = record["top_hit"] or {}
        rows.append(
            {
                "occurrenceID": metadata.get("occurrenceID"),
                "sequenceID": record["sequence_id"],
                "DNA_sequence_md5": record["sequence_md5"],
                "DNA_sequence": metadata.get("DNA_sequence"),
                "target_gene": metadata.get("target_gene") or metadata.get("marker"),
                "target_subfragment": metadata.get("target_subfragment"),
                "pcr_primer_forward": metadata.get("pcr_primer_forward"),
                "pcr_primer_reverse": metadata.get("pcr_primer_reverse"),
                "seq_meth": metadata.get("seq_meth"),
                "otu_db": metadata.get("otu_db") or metadata.get("referenceDatabase"),
                "otu_class_appr": metadata.get("otu_class_appr") or metadata.get("methodOrSOP"),
                "otu_seq_comp_appr": metadata.get("otu_seq_comp_appr") or f"identity={top.get('identity')}; queryCoverage={top.get('query_coverage')}",
                "sop": metadata.get("sop") or metadata.get("methodOrSOP"),
                "contaminationAssessment": metadata.get("contaminationAssessment"),
                "experimentalVariance": metadata.get("experimentalVariance"),
                "quantificationCycle": metadata.get("quantificationCycle"),
                "estimatedNumberOfCopies": metadata.get("estimatedNumberOfCopies"),
                "identificationReferences": "https://www.gbif.org/tools/sequence-id",
                "identificationRemarks": identification_remarks(record, pack),
            }
        )
    return write_csv(rows)


def identification_remarks(record: dict[str, Any], pack: dict[str, Any]) -> str:
    top = record["top_hit"] or {}
    return (
        f"{record['decision_class']} by {pack['run']['ruleset_version']}; "
        f"match={record['match_type']}; top={top.get('taxon')} "
        f"identity={top.get('identity')} coverage={top.get('query_coverage')}; "
        f"candidate rank={record['candidate_taxon']['rank']}; "
        f"published rank={record['published_taxon']['rank']}; "
        f"publication stage={record['publication_stage']}; "
        f"export state={record.get('export_state')}."
    )


def molecular_report_html(pack: dict[str, Any]) -> str:
    nexus = pack.get("nexus_v3", {})
    conversion = nexus.get("conversion_metrics", {})
    ledger_rows = "\n".join(
        f"<tr><td>{html.escape(str(row['metric']))}</td><td>{html.escape(str(row['value']))}</td>"
        f"<td>{html.escape(str(row['denominator']))}</td><td>{html.escape(str(row.get('rate') if row.get('rate') is not None else '-'))}</td>"
        f"<td>{html.escape(str(row['meaning']))}</td></tr>"
        for row in pack.get("data_accounting_ledger", [])
        if row.get("metric")
        in {
            "input_n",
            "candidate_n",
            "safe_n",
            "publishable_candidate_n",
            "gbif_ready_n",
            "repair_required_n",
            "blocked_top_species_claims_n",
            "hard_gate_failures_n",
        }
    )
    repair_rows = "\n".join(
        f"<tr><td>{html.escape(row['repairAction'])}</td><td>{row['unlockableRecords']}</td><td>{html.escape(row['estimatedCost'])}</td><td>{html.escape(row['exampleRecords'])}</td></tr>"
        for row in pack.get("repair_plan", [])[:8]
    )
    overclaim_rows = "\n".join(
        f"<tr><td>{html.escape(row['sequenceID'])}</td><td>{html.escape(str(row['naiveClaim']))}</td><td>{html.escape(row['compilerDecision'])}</td><td>{html.escape(row['safeRank'])} {html.escape(row['safeTaxon'])}</td></tr>"
        for row in pack.get("naive_top_hit_overclaims", [])[:8]
    )
    hard_gate_failures = pack["metrics"].get("hard_gate_failures", 0)
    profile_rows = "\n".join(
        f"<tr><td>{html.escape(record['sequence_id'])}</td><td>{html.escape(record['metadata_readiness']['marker_profile']['profile_id'])}</td>"
        f"<td>{html.escape(str(record['metadata_readiness']['marker_profile']['species_gate_pass']))}</td>"
        f"<td>{html.escape(record['metadata_readiness']['assay_gate']['assay_type'])}</td>"
        f"<td>{html.escape(str(record['metadata_readiness']['assay_gate']['assay_gate_pass']))}</td>"
        f"<td>{html.escape('; '.join(record['metadata_readiness']['dna_extension_high_priority_missing']) or 'none')}</td></tr>"
        for record in pack["records"]
    )
    rows = "\n".join(
        f"<tr><td>{html.escape(record['sequence_id'])}</td><td>{html.escape(record['decision_class'])}</td>"
        f"<td>{html.escape(record['candidate_taxon']['name'])}</td><td>{html.escape(record['candidate_taxon']['rank'])}</td>"
        f"<td>{html.escape(record['published_taxon']['name'])}</td><td>{html.escape(record['published_taxon']['rank'])}</td>"
        f"<td>{html.escape(record['publication_stage'])}</td>"
        f"<td>{html.escape('; '.join(record['blockers']) or 'none')}</td></tr>"
        for record in pack["records"]
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <link rel="icon" href="data:," />
  <title>{html.escape(pack['summary']['title'])}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 32px; color: #17201a; }}
    h1 {{ max-width: 880px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }}
    .nexus {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin: 24px 0; }}
    .card {{ border: 1px solid #d7e2dc; border-radius: 8px; padding: 14px; background: #f8fbf8; }}
    .ok {{ background:#ecf8ef; border-color:#b7dac0; }}
    .warn {{ background:#fff8e8; border-color:#e6c776; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d7e2dc; padding: 10px; text-align: left; vertical-align: top; }}
    th {{ background: #eef5ef; }}
  </style>
</head>
<body>
  <p><strong>EcoGenesis</strong> / GBIF Ebbe Nielsen Challenge 2026</p>
  <h1>{html.escape(pack['summary']['project_title'])}</h1>
  <p>{html.escape(pack['summary']['verdict'])}</p>
  <section class="summary">
    <div class="card"><strong>{pack['metrics']['processed_records']}</strong><br />processed</div>
    <div class="card"><strong>{pack['metrics']['species_safe_records']}</strong><br />species-safe</div>
    <div class="card"><strong>{pack['metrics']['blocked_species_claims']}</strong><br />blocked species claims</div>
    <div class="card"><strong>{pack['metrics']['publication_repair_efficiency']}</strong><br />repair explainability</div>
  </section>
  <h2>Nexus V3 conversion audit</h2>
  <section class="nexus">
    <div class="card"><strong>{conversion.get('MECY_molecular_evidence_conversion_yield', 0)}</strong><br />MECY conversion yield</div>
    <div class="card"><strong>{conversion.get('SRY_safe_rank_yield', 0)}</strong><br />safe-rank yield</div>
    <div class="card"><strong>{conversion.get('OPR_overclaim_prevention_rate', 0)}</strong><br />overclaim prevention</div>
    <div class="card"><strong>{conversion.get('RY_repairable_yield', 0)}</strong><br />repairable yield</div>
    <div class="card {'ok' if hard_gate_failures == 0 else 'warn'}"><strong>{hard_gate_failures}</strong><br />hard-gate failures</div>
  </section>
  <h2>Data accounting ledger</h2>
  <table>
    <thead><tr><th>Metric</th><th>Value</th><th>Denominator</th><th>Rate</th><th>Meaning</th></tr></thead>
    <tbody>{ledger_rows or '<tr><td colspan="5">No data accounting ledger was generated.</td></tr>'}</tbody>
  </table>
  <h2>Top repair actions</h2>
  <table>
    <thead><tr><th>Repair action</th><th>Unlockable records</th><th>Cost</th><th>Examples</th></tr></thead>
    <tbody>{repair_rows or '<tr><td colspan="4">No repair actions required.</td></tr>'}</tbody>
  </table>
  <h2>Marker, assay and DNA-derived readiness</h2>
  <table>
    <thead><tr><th>Sequence</th><th>Marker profile</th><th>Marker species gate</th><th>Assay</th><th>Assay gate</th><th>DNA extension gaps</th></tr></thead>
    <tbody>{profile_rows}</tbody>
  </table>
  <h2>Naive top-hit overclaims prevented</h2>
  <table>
    <thead><tr><th>Sequence</th><th>Naive species claim</th><th>Compiler decision</th><th>Safe taxon</th></tr></thead>
    <tbody>{overclaim_rows or '<tr><td colspan="4">No unsafe top-hit species claims found in this run.</td></tr>'}</tbody>
  </table>
  <h2>Sequence decisions</h2>
  <table>
    <thead><tr><th>Sequence</th><th>Decision</th><th>Candidate taxon</th><th>Candidate rank</th><th>Published taxon</th><th>Published rank</th><th>Publication stage</th><th>Blockers</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""


def methods_text_md(pack: dict[str, Any]) -> str:
    return f"""# Methods

This run used **EcoGenesis Nexus V3 / Barcode-to-GBIF Evidence Compiler** ruleset `{pack['run']['ruleset_version']}`.

## Purpose

The workflow converts DNA barcode, metabarcoding or Sequence ID / BLAST-style results into rank-aware molecular occurrence evidence for GBIF-oriented review. It is a downstream evidence compiler, not a replacement for GBIF Sequence ID, BOLD, UNITE, PR2, GTDB, BLAST+ or VSEARCH.

## Input Evidence

For each DNA sequence, the compiler consumed:

- sequence identifier and nucleotide sequence;
- reference-hit metrics: taxon, rank, lineage, percent identity, query coverage, aligned length, bit score and e-value when supplied;
- barcode-gap evidence: maximum within-taxon distance and minimum outside-taxon distance;
- diagnostic k-mer evidence and false-positive threshold;
- marker profile evidence: marker family, aligned span, marker-specific identity/coverage thresholds and species-claim policy;
- assay profile evidence: single-specimen barcode, metabarcoding/eDNA, qPCR/ddPCR or custom targeted workflow metadata;
- Darwin Core Occurrence metadata and DNA-derived workflow metadata.

Reference context: **{pack['summary']['reference_database']}**. Marker: **{pack['summary']['marker']}**.

## Deterministic Gates

For each DNA barcode/metabarcoding sequence, the compiler evaluated a marker-specific identity/coverage profile, a 95% ambiguity test over mismatch-rate standard errors, lowest common ancestor of indistinguishable hits, barcode gap, diagnostic k-mer support, diagnostic false-positive probability, assay evidence gates and GBIF publication metadata readiness.

Species-level output is fail-closed: a sequence is `species-safe` only when the marker exact-match gate, ambiguity/LCA gate, positive barcode gap gate, diagnostic k-mer gate, marker-profile species gate, assay gate and publication-readiness gates all pass.

The pack separates `candidate_taxon` from `published_taxon`: blocked or weak records can remain useful as review hints, but they are not emitted as publishable Darwin Core species records.

## Naive Top-Hit Comparison

The `naive_top_hit_overclaims.csv` export lists records where a naive workflow would have published the top hit as a species, but EcoGenesis blocked, downgraded or moved the record to review. This is the core overclaim-prevention audit.

## Repair Optimization

The `repair_plan.csv` export ranks repair actions by unlockable record count. Metadata repairs are separated from molecular/reference blockers so publishers can see whether records need field repair, reference curation or new laboratory work.

Nexus V3 audit files in this Evidence Pack add:

- `data_accounting_ledger.csv` for explicit numerators and denominators;
- `state_machine_audit.csv` for taxonomic status, publication bucket and export-state separation;
- `hard_gate_audit.csv` for species-safe consistency checks;
- `naive_top_hit_overclaims.csv` for overclaim prevention evidence;
- `reference_gap_index.csv` for marker/reference bottlenecks;
- `reference_completeness_audit.csv` for explicit RCI 2.0 status and reference-context caveats;
- `marker_profile_audit.csv` for marker-specific gates and caveats;
- `assay_gate_audit.csv` for qPCR/eDNA/control metadata status;
- `dna_extension_readiness.csv` for GBIF DNA-derived high-priority fields;
- `repair_plan.csv` for publisher repair prioritization;
- `metadata_bottlenecks.csv` for field-level publication blockers.

## Claim Boundaries

The output is sequence-derived occurrence evidence under supplied reference context. It does not prove living presence, absence, population trend, true distribution, phenotype truth or ecological causality. Empty or low-evidence cells must be treated as no-evidence cells, not absence.
"""


def citations_md(pack: dict[str, Any]) -> str:
    manifest = pack.get("reference_manifest", {})
    return f"""# Citations And Source Links

## Project And Tool Citation

EcoGenesis Nexus V3 / Barcode-to-GBIF Evidence Compiler. Ruleset `{pack['run']['ruleset_version']}`. Run ID `{pack['run']['run_id']}`. Request fingerprint `{pack['run']['request_fingerprint']}`.

## Reference Dataset Used In This Run

- Database: {manifest.get('db_name') or pack['summary']['reference_database']}
- Version: {manifest.get('db_version') or 'not supplied'}
- Source: {manifest.get('source') or 'not supplied'}
- DOI or URL: {manifest.get('doi_or_url') or 'not supplied'}
- License: {manifest.get('license') or 'not supplied'}
- SHA-256: {manifest.get('sha256') or manifest.get('manifest_sha256') or 'not supplied'}

## GBIF And Methods Links

- GBIF Sequence ID: https://www.gbif.org/tools/sequence-id
- GBIF DNA-derived data publishing guide: https://docs.gbif.org/publishing-dna-derived-data/en/
- GBIF occurrence dataset quality requirements: https://www.gbif.org/data-quality-requirements-occurrences
- GBIF 2026 Ebbe Nielsen Challenge rules: https://www.gbif.org/awards/ebbe-2026-rules

Retain reference database names, versions, sequence identifiers and GBIF taxon keys when publishing or reviewing derived molecular occurrence evidence.

## DOI Caveat For Formal GBIF Use

API-derived evidence packs and local reference-search examples are useful for review and reproducibility, but formal GBIF-mediated occurrence publication should attach an appropriate GBIF download DOI, derived dataset citation or source reference dataset DOI where applicable.
"""


def proof_by_failure_modes_md(pack: dict[str, Any]) -> str:
    return """# Proof By Failure Modes

The compiler blocks species-level claims when any required gate fails:

- identity or coverage below the selected marker profile threshold;
- statistically indistinguishable competitor collapses the safe taxon to genus or higher;
- barcode gap is missing or non-positive;
- diagnostic k-mer support is missing, zero or above the configured false-positive probability threshold;
- marker profile disallows species export for the supplied marker/span;
- qPCR/ddPCR required assay evidence is missing;
- required Occurrence core or DNA-derived metadata is missing.

Therefore `species-safe` is not a blind top-hit label. It means the record passed all frozen molecular evidence and GBIF-readiness gates in this run.

## Nexus V3 Hard-Gate Audit

The `hard_gate_audit.csv` export verifies the contradiction condition explicitly:

If a record is emitted as `species-safe`, then the marker exact-match gate, ambiguity/LCA gate, barcode gap gate, diagnostic k-mer gate, marker profile gate, Occurrence core gate, DNA metadata gate and assay gate must all pass.

If any of those gates fail while `species-safe` is emitted, `hardGateViolation=true`. A valid run must have zero hard-gate failures.
"""


def external_tool_adapter_matrix_csv() -> str:
    return write_csv(
        [
            {
                "tool": "GBIF Sequence ID",
                "role": "Reference-hit source",
                "normalizedFields": "sequenceID; topTaxon; identity; queryCoverage; matchType; GBIF backbone taxon",
                "claimPolicy": "Never publish top hit directly; pass through Nexus hard gates.",
            },
            {
                "tool": "BLAST+",
                "role": "Alignment and candidate hits",
                "normalizedFields": "pident; qcov; bitscore; evalue; alignedLength; subjectID",
                "claimPolicy": "Use as supplied H(s); species claim still requires ambiguity/LCA and reference support.",
            },
            {
                "tool": "VSEARCH / DADA2 / QIIME 2",
                "role": "ASV and metabarcoding upstream pipeline",
                "normalizedFields": "ASV id; sequence; taxonomy; confidence; read/count context",
                "claimPolicy": "Add assay evidence gates before ecological or monitoring claims.",
            },
            {
                "tool": "BOLD / UNITE / PR2 / GTDB",
                "role": "Reference database context",
                "normalizedFields": "database name; version; marker; reference taxon; lineage",
                "claimPolicy": "Report reference gaps and reference completeness caveats.",
            },
            {
                "tool": "MAFFT + IQ-TREE / EPA-ng",
                "role": "Optional phylogenetic placement",
                "normalizedFields": "placement; support; clade; tree version",
                "claimPolicy": "Can support or caveat safe rank; does not override failed metadata gates.",
            },
            {
                "tool": "Cutadapt / fastp",
                "role": "Sequence QC and trimming",
                "normalizedFields": "trimmed length; quality; primer status; ambiguous bases",
                "claimPolicy": "Feeds QC blockers and repair actions.",
            },
        ]
    )


def write_csv(rows: list[dict[str, Any]]) -> str:
    output = io.StringIO()
    if not rows:
        return ""
    fields = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()
