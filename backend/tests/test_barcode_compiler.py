from __future__ import annotations

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
    assert record["safe_taxon"]["rank"] == "species"
    assert record["barcode_gap"]["status"] == "pass"
    assert record["diagnostic_kmers"]["status"] == "pass"
    assert record["metadata_readiness"]["core_pass"] is True
    assert record["metadata_readiness"]["dna_pass"] is True


def test_ambiguous_hits_downgrade_to_genus(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(AMBIGUOUS_RECORD)
    record = pack["records"][0]

    assert record["match_type"] == "exact"
    assert record["decision_class"] == "genus-safe"
    assert record["safe_taxon"]["rank"] == "genus"
    assert any("statistically indistinguishable competitors" in blocker for blocker in record["blockers"])


def test_weak_coverage_blocks_species_claim(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(WEAK_RECORD)
    record = pack["records"][0]

    assert record["match_type"] == "weak"
    assert record["taxonomic_status"] == "weak"
    assert record["decision_class"] == "weak"
    assert any("query coverage < 80%" in blocker for blocker in record["blockers"])


def test_missing_occurrence_metadata_is_not_publishable(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = compile_records(MISSING_METADATA_RECORD)
    record = pack["records"][0]

    assert record["taxonomic_status"] == "species-safe"
    assert record["decision_class"] == "not-publishable"
    assert record["metadata_readiness"]["core_missing"] == ["occurrenceID", "eventDate"]
    assert any("missing required Occurrence core field eventDate" in blocker for blocker in record["blockers"])


def test_barcode_api_and_exports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    response = client.post("/api/barcode/run", json=DEFAULT_BARCODE_REQUEST)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    run_id = payload["run_id"]
    assert {item["name"] for item in payload["exports"]} >= {
        "sequence_safety_table.csv",
        "safe_taxonomic_assignments.csv",
        "ambiguous_sequences.csv",
        "barcode_gap_report.csv",
        "diagnostic_kmer_report.csv",
        "gbif_backbone_matches.csv",
        "publication_blockers.csv",
        "dwc_occurrence_core_template.csv",
        "dna_derived_extension_template.csv",
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

    zip_head = client.head(f"/api/barcode/runs/{run_id}/exports/evidence_pack.zip")
    assert zip_head.status_code == 200
    assert int(zip_head.headers["content-length"]) > 0

    with zipfile.ZipFile(barcode_artifact_path(run_id, "evidence_pack.zip")) as archive:
        assert {
            "sequence_safety_table.csv",
            "molecular_evidence_report.html",
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
