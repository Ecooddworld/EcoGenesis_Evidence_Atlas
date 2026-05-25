from __future__ import annotations

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
    assert record["barcode_gap"]["status"] == "pass"
    assert record["diagnostic_kmers"]["status"] == "pass"
    assert record["diagnostic_kmers"]["p_false_positive"] <= 0.01
    assert record["metadata_readiness"]["core_pass"] is True
    assert record["metadata_readiness"]["dna_pass"] is True


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
        "sequence_safety_table.csv",
        "safe_taxonomic_assignments.csv",
        "review_taxonomic_hints.csv",
        "ambiguous_sequences.csv",
        "barcode_gap_report.csv",
        "diagnostic_kmer_report.csv",
        "gbif_backbone_matches.csv",
        "publication_blockers.csv",
        "dwc_occurrence_core_template.csv",
        "dwc_occurrence_core_publishable.csv",
        "dwc_occurrence_core_review.csv",
        "dna_derived_extension_template.csv",
        "dna_derived_extension_publishable.csv",
        "molecular_evidence_report.html",
        "methods_text.md",
        "citations.md",
        "evidence_graph.json",
        "evidence_pack.json",
        "evidence_pack.zip",
    }

    detail = client.get(f"/api/barcode/runs/{run_id}")
    assert detail.status_code == 200
    pack = detail.json()
    assert pack["metrics"]["processed_records"] == 4
    assert pack["metrics"]["species_safe_records"] == 1
    assert pack["metrics"]["blocked_species_claims"] >= 2

    report = client.get(f"/api/barcode/runs/{run_id}/report")
    assert report.status_code == 200
    assert "Barcode-to-GBIF Evidence Compiler" in report.text

    blockers = client.get(f"/api/barcode/runs/{run_id}/exports/publication_blockers.csv")
    assert blockers.status_code == 200
    assert "missing required Occurrence core field eventDate" in blockers.text

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

    zip_head = client.head(f"/api/barcode/runs/{run_id}/exports/evidence_pack.zip")
    assert zip_head.status_code == 200
    assert int(zip_head.headers["content-length"]) > 0

    with zipfile.ZipFile(barcode_artifact_path(run_id, "evidence_pack.zip")) as archive:
        assert {
            "sequence_safety_table.csv",
            "reference_manifest.json",
            "molecular_evidence_report.html",
            "dwc_occurrence_core_publishable.csv",
            "review_taxonomic_hints.csv",
            "dwc_occurrence_core_template.csv",
            "dna_derived_extension_template.csv",
            "proof_by_failure_modes.md",
        } <= set(archive.namelist())


def test_barcode_reference_status_and_demos() -> None:
    client = TestClient(app)

    status = client.get("/api/barcode/reference-status")
    assert status.status_code == 200
    assert status.json()["match_gates"]["exact"] == "identity >= 99% and queryCoverage >= 80%"

    demos = client.get("/api/barcode/demo-scenarios")
    assert demos.status_code == 200
    assert any(item["id"] == "mixed-batch" for item in demos.json())
