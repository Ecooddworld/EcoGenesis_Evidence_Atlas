from __future__ import annotations

import csv
import io
from itertools import product
import zipfile

from fastapi.testclient import TestClient

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import (
    AMBIGUOUS_RECORD,
    DEFAULT_BARCODE_REQUEST,
    GOOD_RECORD,
    MISSING_METADATA_RECORD,
    WEAK_RECORD,
    request_with_records,
)
from app.barcode.schemas import BarcodeCompilerRequest
from app.barcode.storage import barcode_artifact_path
from app.main import app


def compile_records(*records: dict) -> dict:
    return run_barcode_compiler(BarcodeCompilerRequest(**request_with_records("pytest barcode demo", list(records))))


def test_species_safe_when_all_gates_pass(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(GOOD_RECORD)
    record = pack["records"][0]

    assert record["match_type"] == "exact"
    assert record["decision_class"] == "species-safe"
    assert record["candidate_taxon"]["rank"] == "species"
    assert record["published_taxon"]["rank"] == "species"
    assert record["publication_stage"] == "record_recommended_ready"
    assert record["publication_status"] == "record-ready"
    assert record["publication_bucket"] == "publishable_candidate"
    assert record["claim_boundary"]["supported"].startswith("Species-level molecular assignment candidate")
    assert record["barcode_gap"]["status"] == "pass"
    assert record["diagnostic_kmers"]["status"] == "pass"
    assert record["diagnostic_kmers"]["p_false_positive"] <= 0.01
    assert record["metadata_readiness"]["core_pass"] is True
    assert record["metadata_readiness"]["dna_pass"] is True
    assert pack["metrics"]["hard_gate_failures"] == 0
    assert pack["nexus_v3"]["conversion_metrics"]["SSY_species_safe_yield"] == 1


def test_ambiguous_hits_downgrade_to_genus(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(AMBIGUOUS_RECORD)
    record = pack["records"][0]

    assert record["match_type"] == "exact"
    assert record["decision_class"] == "genus-safe"
    assert record["candidate_taxon"]["rank"] == "genus"
    assert record["published_taxon"]["rank"] == "genus"
    assert record["publication_status"] == "record-ready"
    assert any("statistically indistinguishable competitors" in blocker for blocker in record["blockers"])
    assert pack["naive_top_hit_overclaims"][0]["compilerDecision"] == "genus-safe"


def test_weak_coverage_blocks_species_claim(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(WEAK_RECORD)
    record = pack["records"][0]

    assert record["match_type"] == "weak"
    assert record["taxonomic_status"] == "weak"
    assert record["decision_class"] == "weak"
    assert record["published_taxon"]["rank"] == "none"
    assert any("query coverage < 80%" in blocker for blocker in record["blockers"])


def test_missing_occurrence_metadata_is_not_publishable(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(MISSING_METADATA_RECORD)
    record = pack["records"][0]

    assert record["taxonomic_status"] == "species-safe"
    assert record["decision_class"] == "not-publishable"
    assert record["published_taxon"]["rank"] == "none"
    assert record["publication_stage"] == "record_not_ready"
    assert record["metadata_readiness"]["core_missing"] == ["occurrenceID", "eventDate"]
    assert any("missing required Occurrence core field eventDate" in blocker for blocker in record["blockers"])


def test_scientific_name_conflict_blocks_publication_not_taxonomic_evidence(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {
        "metadata": GOOD_RECORD["metadata"] | {"scientificName": "Culex pipiens"},
    }

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["taxonomic_status"] == "species-safe"
    assert decision["decision_class"] == "not-publishable"
    assert decision["publication_bucket"] == "repair_required"
    assert decision["export_state"] == "evidence_publishable_repair_required"
    assert any("scientificName conflicts with top molecular hit" in blocker for blocker in decision["blockers"])


def test_negative_barcode_gap_blocks_species_claim(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {"barcode_gap": {"intra_max_distance": 0.02, "inter_min_distance": 0.015}}

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["barcode_gap"]["status"] == "fail"
    assert decision["taxonomic_status"] == "ambiguous"
    assert decision["decision_class"] == "ambiguous"
    assert decision["published_taxon"]["rank"] == "none"
    assert any("barcode gap fail" in blocker for blocker in decision["blockers"])


def test_missing_diagnostic_kmers_block_species_claim(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {"diagnostic": {"diagnostic_kmers": [], "reference_total_windows": 5_000_000, "epsilon": 0.01}}

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["diagnostic_kmers"]["status"] == "missing"
    assert decision["taxonomic_status"] == "ambiguous"
    assert decision["decision_class"] == "ambiguous"
    assert decision["published_taxon"]["rank"] == "none"
    assert any("diagnostic k-mer support missing" in blocker for blocker in decision["blockers"])


def test_diagnostic_false_positive_risk_blocks_species_claim(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    all_kmers = ["".join(items) for items in product("ACGT", repeat=8)]
    risky_kmers = [GOOD_RECORD["sequence"][:8], *all_kmers[:199]]
    record = GOOD_RECORD | {
        "diagnostic": {
            "diagnostic_kmers": risky_kmers,
            "k": 8,
            "reference_total_windows": 5_000_000,
            "epsilon": 0.01,
            "alpha": 0.01,
        }
    }

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["diagnostic_kmers"]["status"] == "fail_false_positive_risk"
    assert decision["diagnostic_kmers"]["p_false_positive"] > 0.01
    assert decision["taxonomic_status"] == "ambiguous"
    assert decision["published_taxon"]["rank"] == "none"


def test_evidence_graph_node_ids_are_unique(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(GOOD_RECORD, AMBIGUOUS_RECORD, WEAK_RECORD, MISSING_METADATA_RECORD)
    node_ids = [node["id"] for node in pack["evidence_graph"]["nodes"]]

    assert len(node_ids) == len(set(node_ids))


def test_barcode_api_and_exports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    response = client.post("/api/barcode/run", json=DEFAULT_BARCODE_REQUEST)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    run_id = payload["run_id"]
    assert {item["name"] for item in payload["exports"]} >= {
        "reference_manifest.json",
        "source_provenance_manifest.json",
        "data_accounting_ledger.csv",
        "sequence_safety_table.csv",
        "state_machine_audit.csv",
        "claim_boundaries.csv",
        "segment_overlap_report.csv",
        "safe_taxonomic_assignments.csv",
        "review_taxonomic_hints.csv",
        "ambiguous_sequences.csv",
        "barcode_gap_report.csv",
        "diagnostic_kmer_report.csv",
        "gbif_backbone_matches.csv",
        "publication_blockers.csv",
        "repair_plan.csv",
        "metadata_bottlenecks.csv",
        "reference_gap_index.csv",
        "reference_completeness_audit.csv",
        "marker_profile_audit.csv",
        "assay_gate_audit.csv",
        "dna_extension_readiness.csv",
        "repair_gain_estimates.csv",
        "hard_gate_audit.csv",
        "naive_top_hit_overclaims.csv",
        "dwc_occurrence_core_template.csv",
        "dwc_occurrence_core_publishable.csv",
        "dwc_occurrence_core_gbif_ready.csv",
        "dwc_occurrence_core_review.csv",
        "dwc_occurrence_core_review_or_repair.csv",
        "dna_derived_extension_template.csv",
        "dna_derived_extension_publishable.csv",
        "dna_derived_extension_gbif_ready.csv",
        "molecular_evidence_report.html",
        "methods_text.md",
        "citations.md",
        "evidence_graph.json",
        "nexus_v3_summary.json",
        "external_tool_adapter_matrix.csv",
        "proof_by_failure_modes.md",
        "segments.csv",
        "segment_safe_taxa.csv",
        "match_gate_audit.csv",
        "cross_marker_consensus.csv",
        "dwc_occurrence_core_readiness.csv",
        "validation_fold_metrics.csv",
        "theorem_checklist.json",
        "artifact_checksums.json",
        "query_smoke_report.md",
        "ci_math_oracle_report.json",
        "gseg_graph_schema.json",
        "gsig_graph_schema.yaml",
        "evidence_graph.jsonld",
        "verified_segment_evidence_array.csv",
        "verified_segment_evidence_array.jsonl",
        "verified_segment_evidence_array.parquet",
        "segment_canonicalization_audit.csv",
        "segment_cluster_audit.csv",
        "sharedness_overclaim_audit.csv",
        "function_claim_boundary_audit.csv",
        "ai_output_guardrail_audit.csv",
        "graph_provenance_audit.csv",
        "ai_dataset_export_audit.csv",
        "graph_roundtrip_audit.json",
        "vsea_graph_reconciliation.csv",
        "ruleset_diff_report.json",
        "report_consistency_audit.csv",
        "segment_taxon_matrix_audit.csv",
        "judge_reproducibility_report.md",
        "evidence_pack.json",
        "evidence_pack.zip",
    }

    detail = client.get(f"/api/barcode/runs/{run_id}")
    assert detail.status_code == 200
    pack = detail.json()
    assert pack["metrics"]["processed_records"] == 4
    assert pack["metrics"]["species_safe_records"] == 1
    assert pack["metrics"]["blocked_species_claims"] >= 2
    assert pack["metrics"]["hard_gate_failures"] == 0
    assert pack["nexus_v3"]["audit"]["blocked_or_downgraded_top_species_hits"] >= 2

    report = client.get(f"/api/barcode/runs/{run_id}/report")
    assert report.status_code == 200
    assert "Barcode-to-GBIF Evidence Compiler" in report.text
    assert "Nexus V3 conversion audit" in report.text

    blockers = client.get(f"/api/barcode/runs/{run_id}/exports/publication_blockers.csv")
    assert blockers.status_code == 200
    assert "missing required Occurrence core field eventDate" in blockers.text
    assert "blocker.kind" in blockers.text
    assert "occurrence_core" in blockers.text

    ledger = client.get(f"/api/barcode/runs/{run_id}/exports/data_accounting_ledger.csv")
    assert ledger.status_code == 200
    assert "input_n" in ledger.text
    assert "gbif_ready_n" in ledger.text

    state_machine = client.get(f"/api/barcode/runs/{run_id}/exports/state_machine_audit.csv")
    assert state_machine.status_code == 200
    assert "dwc_template_ready" in state_machine.text
    assert "evidence_publishable_repair_required" in state_machine.text

    safe_assignments = client.get(f"/api/barcode/runs/{run_id}/exports/safe_taxonomic_assignments.csv")
    assert safe_assignments.status_code == 200
    assert "profile_id" in safe_assignments.text
    assert "coi_full_barcode" in safe_assignments.text

    claim_boundaries = client.get(f"/api/barcode/runs/{run_id}/exports/claim_boundaries.csv")
    assert claim_boundaries.status_code == 200
    assert "rationale" in claim_boundaries.text
    assert "Evidence path" in claim_boundaries.text

    publishable_core = client.get(f"/api/barcode/runs/{run_id}/exports/dwc_occurrence_core_publishable.csv")
    assert publishable_core.status_code == 200
    assert "urn:ecogenesis:demo:AALB-COI-good" in publishable_core.text
    assert "Aedes albopictus" in publishable_core.text
    assert "AALB-COI-short" not in publishable_core.text
    assert "AALB-COI-metadata-gap" not in publishable_core.text

    review_hints = client.get(f"/api/barcode/runs/{run_id}/exports/review_taxonomic_hints.csv")
    assert review_hints.status_code == 200
    assert "AALB-COI-short" in review_hints.text
    assert "AALB-COI-metadata-gap" in review_hints.text

    hard_gate = client.get(f"/api/barcode/runs/{run_id}/exports/hard_gate_audit.csv")
    assert hard_gate.status_code == 200
    assert "hardGateViolation" in hard_gate.text
    assert "True" not in hard_gate.text
    assert "markerProfileGate" in hard_gate.text

    marker_profile = client.get(f"/api/barcode/runs/{run_id}/exports/marker_profile_audit.csv")
    assert marker_profile.status_code == 200
    assert "coi_full_barcode" in marker_profile.text

    assay_gate = client.get(f"/api/barcode/runs/{run_id}/exports/assay_gate_audit.csv")
    assert assay_gate.status_code == 200
    assert "single_specimen_barcode" in assay_gate.text

    dna_ready = client.get(f"/api/barcode/runs/{run_id}/exports/dna_extension_readiness.csv")
    assert dna_ready.status_code == 200
    assert "materialSampleID" in dna_ready.text

    overclaims = client.get(f"/api/barcode/runs/{run_id}/exports/naive_top_hit_overclaims.csv")
    assert overclaims.status_code == 200
    assert "AALB-COI-ambiguous" in overclaims.text
    assert "genus-safe" in overclaims.text

    theorem = client.get(f"/api/barcode/runs/{run_id}/exports/theorem_checklist.json")
    assert theorem.status_code == 200
    theorem_payload = theorem.json()
    assert theorem_payload["summary"]["fail"] == 0
    assert theorem_payload["summary"]["release_gate"] == "pass"
    assert theorem_payload["summary"]["blocked_roadmap_no_claim"] >= 1

    vsea = client.get(f"/api/barcode/runs/{run_id}/exports/verified_segment_evidence_array.csv")
    assert vsea.status_code == 200
    assert "segmentHash" in vsea.text
    assert "claimState" in vsea.text
    assert "taxon_supported" in vsea.text

    graph_provenance = client.get(f"/api/barcode/runs/{run_id}/exports/graph_provenance_audit.csv")
    assert graph_provenance.status_code == 200
    assert "status" in graph_provenance.text
    provenance_rows = list(csv.DictReader(io.StringIO(graph_provenance.text)))
    assert provenance_rows
    assert {row["status"] for row in provenance_rows} == {"pass"}

    graph_roundtrip = client.get(f"/api/barcode/runs/{run_id}/exports/graph_roundtrip_audit.json")
    assert graph_roundtrip.status_code == 200
    assert graph_roundtrip.json()["status"] == "pass"

    zip_head = client.head(f"/api/barcode/runs/{run_id}/exports/evidence_pack.zip")
    assert zip_head.status_code == 200
    assert int(zip_head.headers["content-length"]) > 0

    with zipfile.ZipFile(barcode_artifact_path(run_id, "evidence_pack.zip")) as archive:
        assert {
            "sequence_safety_table.csv",
            "reference_manifest.json",
            "source_provenance_manifest.json",
            "data_accounting_ledger.csv",
            "claim_boundaries.csv",
            "state_machine_audit.csv",
            "segment_overlap_report.csv",
            "molecular_evidence_report.html",
            "dwc_occurrence_core_publishable.csv",
            "review_taxonomic_hints.csv",
            "dwc_occurrence_core_template.csv",
            "dna_derived_extension_template.csv",
            "hard_gate_audit.csv",
            "naive_top_hit_overclaims.csv",
            "reference_gap_index.csv",
            "repair_plan.csv",
            "metadata_bottlenecks.csv",
            "reference_completeness_audit.csv",
            "marker_profile_audit.csv",
            "assay_gate_audit.csv",
            "dna_extension_readiness.csv",
            "nexus_v3_summary.json",
            "external_tool_adapter_matrix.csv",
            "proof_by_failure_modes.md",
            "theorem_checklist.json",
            "verified_segment_evidence_array.csv",
            "verified_segment_evidence_array.parquet",
            "segment_safe_taxa.csv",
            "graph_provenance_audit.csv",
            "sharedness_overclaim_audit.csv",
            "ai_output_guardrail_audit.csv",
            "judge_reproducibility_report.md",
        } <= set(archive.namelist())


def test_barcode_reference_status_and_demos() -> None:
    client = TestClient(app)

    status = client.get("/api/barcode/reference-status")
    assert status.status_code == 200
    assert status.json()["match_gates"]["exact"] == "identity >= 99% and queryCoverage >= 80%"

    demos = client.get("/api/barcode/demo-scenarios")
    assert demos.status_code == 200
    assert any(item["id"] == "mixed-batch" for item in demos.json())


def test_marker_profile_can_force_safe_rank_review(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {
        "metadata": GOOD_RECORD["metadata"] | {"marker": "16S"},
        "hits": [
            GOOD_RECORD["hits"][0] | {"identity": 100, "query_coverage": 100, "aligned_length": 250},
        ],
    }

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["metadata_readiness"]["marker_profile"]["profile_id"] == "s16_short_amplicon"
    assert decision["metadata_readiness"]["marker_profile"]["species_gate_pass"] is False
    assert decision["decision_class"] == "genus-safe"
    assert any("marker profile blocked species claim" in blocker for blocker in decision["blockers"])
    assert pack["metrics"]["marker_species_disabled_records"] == 1


def test_qpcr_assay_gate_blocks_publication_without_controls(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {
        "metadata": GOOD_RECORD["metadata"] | {"assayType": "qpcr_ddpcr"},
    }

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["taxonomic_status"] == "species-safe"
    assert decision["decision_class"] == "not-publishable"
    assert decision["publication_stage"] == "record_not_ready"
    assert decision["metadata_readiness"]["assay_gate"]["assay_gate_pass"] is False
    assert "occurrenceStatus" in decision["metadata_readiness"]["assay_gate"]["assay_required_missing"]
    assert any("assay gate blocked publication" in blocker for blocker in decision["blockers"])
