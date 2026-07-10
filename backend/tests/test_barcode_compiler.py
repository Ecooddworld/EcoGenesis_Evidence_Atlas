from __future__ import annotations

from copy import deepcopy
import csv
import hashlib
import io
from itertools import product
import json
import zipfile

from fastapi.testclient import TestClient
import pytest

from app.barcode.compiler import SELF_REFERENTIAL_EXPORTS, run_barcode_compiler
from app.barcode.demo import (
    AMBIGUOUS_RECORD,
    DEFAULT_BARCODE_REQUEST,
    GOOD_RECORD,
    MISSING_METADATA_RECORD,
    WEAK_RECORD,
    request_with_records,
)
from app.barcode.schemas import BarcodeCompilerRequest, SequenceRecord
from app.barcode.scientific_gates import (
    ATTESTATION_KEY_ID_ENV,
    ATTESTATION_SECRET_ENV,
    attest_reference_completeness,
)
from app.barcode.storage import barcode_artifact_path
from app.main import app
from scripts.generate_competition_reports import build_report_artifacts


TEST_ATTESTATION_SECRET = "pytest-only-attestation-secret-32-bytes-minimum"


@pytest.fixture(autouse=True)
def configured_test_attestation_secret(monkeypatch) -> None:
    monkeypatch.setenv(ATTESTATION_SECRET_ENV, TEST_ATTESTATION_SECRET)
    monkeypatch.setenv(ATTESTATION_KEY_ID_ENV, "pytest-scientific-gate-key")


def trusted_record(record: dict) -> dict:
    payload = deepcopy(record)
    evidence = payload.get("reference_completeness")
    if evidence is None:
        return payload
    evidence.update({
        "status": "audited_sufficient",
        "audit_source": "pytest server-verified reference audit fixture",
        "audit_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "notes": "Test-only trusted fixture; never used by the built-in demo.",
    })
    model = SequenceRecord(**payload)
    candidate_species = len({hit.taxon for hit in model.hits if str(hit.rank).lower() == "species"})
    evidence["attestation"] = attest_reference_completeness(
        model,
        candidate_species_in_hits=candidate_species,
    )
    return payload


def trusted_request(request: dict) -> dict:
    payload = deepcopy(request)
    payload["records"] = [trusted_record(record) for record in payload["records"]]
    return payload


def compile_records(*records: dict) -> dict:
    signed_records = [trusted_record(record) for record in records]
    return run_barcode_compiler(BarcodeCompilerRequest(**request_with_records("pytest barcode demo", signed_records)))


def test_checksum_manifest_stays_non_self_referential_across_rebuilds(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    pack = run_barcode_compiler(BarcodeCompilerRequest(**DEFAULT_BARCODE_REQUEST))
    expected_names = {item["name"] for item in pack["exports"]} - SELF_REFERENTIAL_EXPORTS

    assert set(pack["run"]["artifact_checksums"]) == expected_names
    api_pack = TestClient(app).get(f"/api/barcode/runs/{pack['run']['run_id']}").json()
    assert set(api_pack["run"]["artifact_checksums"]) == expected_names

    for _ in range(3):
        # Simulate a caller feeding a full external export manifest back into a report rebuild.
        pack["run"]["artifact_checksums"] = {
            item["name"]: item["sha256"] for item in pack["exports"]
        }
        pack, artifacts = build_report_artifacts(pack)
        checksum_payload = json.loads(str(artifacts["artifact_checksums.json"]))
        embedded_checksums = checksum_payload["checksums"]

        assert set(embedded_checksums) == expected_names
        assert not (set(embedded_checksums) & SELF_REFERENTIAL_EXPORTS)
        assert embedded_checksums == pack["run"]["artifact_checksums"]
        for name, expected_sha256 in embedded_checksums.items():
            content = artifacts[name]
            payload = content if isinstance(content, bytes) else content.encode("utf-8")
            assert hashlib.sha256(payload).hexdigest() == expected_sha256


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
    assert decision["scientific_decision_state"] == "species-rule-pass"
    assert decision["decision_class"] == "not-publishable"
    assert decision["publication_bucket"] == "repair_required"
    assert decision["export_state"] == "evidence_publishable_repair_required"
    assert any("scientificName conflicts with top molecular hit" in blocker for blocker in decision["blockers"])


def test_negative_barcode_gap_blocks_species_claim(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {
        "barcode_gap": GOOD_RECORD["barcode_gap"] | {"intra_max_distance": 0.02, "inter_min_distance": 0.015}
    }

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
            "target_sequence_count": 12,
            "negative_taxon_count": 4,
            "negative_sequence_count": 30,
            "conservation_fraction": 1.0,
            "canonicalized": True,
            "reverse_complement_checked": True,
            "background_scope": "test negative universe",
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

    response = client.post("/api/barcode/run", json=trusted_request(DEFAULT_BARCODE_REQUEST))

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    run_id = payload["run_id"]
    export_names = {item["name"] for item in payload["exports"]}
    assert export_names >= {
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
        "math_viability_audit.json",
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
        "dwc_occurrence_core_validation_candidates.csv",
        "dwc_occurrence_core_review.csv",
        "dwc_occurrence_core_review_or_repair.csv",
        "dna_derived_extension_template.csv",
        "dna_derived_extension_publishable.csv",
        "dna_derived_extension_validation_candidates.csv",
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
        "release_invariant_checklist.json",
        "artifact_checksums.json",
        "query_smoke_report.md",
        "ci_math_oracle_report.json",
        "gseg_graph_schema.json",
        "gsig_graph_schema.yaml",
        "evidence_graph.jsonld",
        "rule_evidence_segment_array.csv",
        "rule_evidence_segment_array.jsonl",
        "rule_evidence_segment_array.parquet",
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
    retired_aliases = {
        "dwc_occurrence_core_gbif_ready.csv",
        "dna_derived_extension_gbif_ready.csv",
        "theorem_checklist.json",
        "verified_segment_evidence_array.csv",
        "verified_segment_evidence_array.jsonl",
        "verified_segment_evidence_array.parquet",
    }
    assert retired_aliases.isdisjoint(export_names)

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
    assert "validation_candidate_n" in ledger.text
    assert "gbif_ready_n" in ledger.text  # deprecated compatibility metric

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

    invariant = client.get(f"/api/barcode/runs/{run_id}/exports/release_invariant_checklist.json")
    assert invariant.status_code == 200
    invariant_payload = invariant.json()
    assert invariant_payload["summary"]["release_gate"] == "review"
    assert invariant_payload["summary"]["external_validation_missing"] >= 1
    assert invariant_payload["summary"]["blocked_roadmap_no_claim"] >= 1
    for retired_name in retired_aliases:
        retired = client.get(f"/api/barcode/runs/{run_id}/exports/{retired_name}")
        assert retired.status_code == 404

    vsea = client.get(f"/api/barcode/runs/{run_id}/exports/rule_evidence_segment_array.csv")
    assert vsea.status_code == 200
    assert "segmentHash" in vsea.text
    assert "claimState" in vsea.text
    assert "taxon_supported" in vsea.text

    stored_pack = client.get(f"/api/barcode/runs/{run_id}").json()
    stored_names = {item["name"]: item for item in stored_pack["exports"]}
    assert stored_names["evidence_pack.json"]["sha256"]
    persisted_pack = barcode_artifact_path(run_id, "evidence_pack.json").read_text(encoding="utf-8")
    assert '"evidence_pack.json":' not in persisted_pack
    assert '"artifact_checksums.json":' not in persisted_pack

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
            "math_viability_audit.json",
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
            "release_invariant_checklist.json",
            "rule_evidence_segment_array.csv",
            "rule_evidence_segment_array.parquet",
            "segment_safe_taxa.csv",
            "graph_provenance_audit.csv",
            "sharedness_overclaim_audit.csv",
            "ai_output_guardrail_audit.csv",
            "judge_reproducibility_report.md",
        } <= set(archive.namelist())
        assert retired_aliases.isdisjoint(archive.namelist())


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
    assert decision["scientific_decision_state"] == "species-level-molecular-candidate-assay-blocked"
    assert decision["decision_class"] == "not-publishable"
    assert decision["publication_stage"] == "record_not_ready"
    assert decision["metadata_readiness"]["assay_gate"]["assay_gate_pass"] is False
    assert "occurrenceStatus" in decision["metadata_readiness"]["assay_gate"]["assay_required_missing"]
    assert any("assay gate blocked publication" in blocker for blocker in decision["blockers"])


def test_metabarcoding_assay_gate_blocks_publication_without_controls_and_replicates(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {
        "metadata": GOOD_RECORD["metadata"] | {"assayType": "metabarcoding"},
    }

    pack = compile_records(record)
    decision = pack["records"][0]

    assert decision["taxonomic_status"] == "species-safe"
    assert decision["scientific_decision_state"] == "species-level-molecular-candidate-assay-blocked"
    assert decision["decision_class"] == "not-publishable"
    assert decision["publication_stage"] == "record_not_ready"
    assert decision["metadata_readiness"]["assay_gate"]["assay_gate_pass"] is False
    required_missing = decision["metadata_readiness"]["assay_gate"]["assay_required_missing"]
    assert "negativeControlStatus" in required_missing
    assert "biologicalReplicateCount" in required_missing
    assert "technicalReplicateCount" in required_missing


def test_scientific_release_gate_is_fail_closed_without_external_holdout(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(GOOD_RECORD)

    assert pack["scientific_release_gate"]["status"] == "blocked"
    assert pack["scientific_release_gate"]["release_eligible"] is False
    assert "holdout" in str(pack["scientific_release_gate"]["contract"]).lower()


def test_builtin_demo_reference_evidence_is_unsigned_informational_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = run_barcode_compiler(BarcodeCompilerRequest(**DEFAULT_BARCODE_REQUEST))

    assert pack["metrics"]["species_rule_pass_records"] == 0
    assert pack["metrics"]["species_safe_records"] == 0
    first = pack["records"][0]
    assert first["reference_completeness"]["gate_pass"] is False
    assert first["reference_completeness"]["trust_status"] == "unsigned"
    assert first["reference_completeness"]["evidence_use"] == "informational_only"
    assert first["scientific_decision_state"] != "species-rule-pass"


def test_species_gate_blocks_missing_reference_completeness_and_chimera_qc(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {"reference_completeness": None, "sequence_qc": None}

    decision = compile_records(record)["records"][0]

    assert decision["taxonomic_status"] == "ambiguous"
    assert decision["reference_completeness"]["gate_pass"] is False
    assert decision["sequence_qc"]["chimera_status"] == "not_evaluated"
    assert any("reference completeness" in blocker for blocker in decision["blockers"])


def test_qpcr_semantic_gate_rejects_bad_controls_and_efficiency(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    record = GOOD_RECORD | {
        "metadata": GOOD_RECORD["metadata"] | {
            "assayType": "qpcr_ddpcr",
            "occurrenceStatus": "present",
            "assayPlatform": "qPCR",
            "contaminationAssessment": "not assessed",
            "negativeControlStatus": "amplified",
            "positiveControlStatus": "detected",
            "inhibitionControlStatus": "pass",
            "technicalReplicateCount": 1,
            "assaySpecificityEvidence": "validated primers",
            "limitOfDetection": 0,
            "quantificationCycle": 39,
            "amplificationEfficiency": 160,
        }
    }

    gate = compile_records(record)["records"][0]["metadata_readiness"]["assay_gate"]

    assert gate["assay_gate_pass"] is False
    assert any("negativeControlStatus" in issue for issue in gate["assay_semantic_issues"])
    assert any("amplificationEfficiency" in issue for issue in gate["assay_semantic_issues"])
