from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.barcode.compiler import run_barcode_compiler
from app.barcode.csv_import import parse_barcode_csv
from app.barcode.schemas import BarcodeCompilerRequest
from app.barcode.storage import barcode_artifact_path
from app.main import app


EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


def compile_csv(name: str, tmp_path, monkeypatch) -> dict:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    parsed = parse_barcode_csv((EXAMPLES_DIR / name).read_text(encoding="utf-8"))
    assert parsed["validation"]["ok"] is True
    return run_barcode_compiler(BarcodeCompilerRequest(**parsed["request"]))


def test_csv_good_example_compiles_species_safe(tmp_path, monkeypatch) -> None:
    pack = compile_csv("aedes_good.csv", tmp_path, monkeypatch)
    record = pack["records"][0]

    assert record["decision_class"] == "species-safe"
    assert record["published_taxon"]["name"] == "Aedes albopictus"
    assert record["barcode_gap"]["status"] == "pass"
    assert record["diagnostic_kmers"]["status"] == "pass"


def test_csv_ambiguous_example_downgrades_to_genus(tmp_path, monkeypatch) -> None:
    pack = compile_csv("aedes_ambiguous.csv", tmp_path, monkeypatch)
    record = pack["records"][0]

    assert record["decision_class"] == "genus-safe"
    assert record["published_taxon"] == {"rank": "genus", "name": "Aedes", "taxon_key": None}
    assert any("safe rank to genus" in blocker for blocker in record["blockers"])


def test_csv_missing_metadata_preserves_taxonomic_evidence_but_blocks_publication(tmp_path, monkeypatch) -> None:
    pack = compile_csv("aedes_missing_metadata.csv", tmp_path, monkeypatch)
    record = pack["records"][0]

    assert record["taxonomic_status"] == "species-safe"
    assert record["decision_class"] == "not-publishable"
    assert record["published_taxon"]["rank"] == "none"
    assert record["metadata_readiness"]["core_missing"] == ["occurrenceID", "eventDate"]


def test_csv_weak_coverage_compiles_as_weak(tmp_path, monkeypatch) -> None:
    pack = compile_csv("aedes_weak_coverage.csv", tmp_path, monkeypatch)
    record = pack["records"][0]

    assert record["decision_class"] == "weak"
    assert record["match_type"] == "weak"
    assert record["published_taxon"]["rank"] == "none"


def test_csv_invalid_dna_characters_are_validation_errors() -> None:
    parsed = parse_barcode_csv(
        "sequenceID,sequence,topTaxon,topIdentity,topCoverage\n"
        "bad-1,ACGTXYZ,Aedes albopictus,99.6,96\n"
    )

    assert parsed["validation"]["ok"] is False
    assert parsed["validation"]["invalid_sequence_count"] == 1
    assert "unsupported DNA/IUPAC" in parsed["validation"]["errors"][0]


def test_csv_missing_required_columns_is_import_error() -> None:
    parsed = parse_barcode_csv("id_only,topTaxon\nAALB-1,Aedes albopictus\n")

    assert parsed["validation"]["ok"] is False
    assert parsed["validation"]["missing_required_columns"] == ["sequenceID", "sequence"]
    assert parsed["request"] is None


def test_csv_alias_columns_resolve_and_compile(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    parsed = parse_barcode_csv(
        "id,sequence,occurrenceId,basisOfRecord,scientificName,eventDate,marker,referenceDatabase,methodOrSOP,identity,queryCoverage,barcodeIntraMax,barcodeInterMin,diagnosticKmers\n"
        "alias-1,ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCG,urn:alias:1,MaterialSample,Aedes albopictus,2026-04-18,COI-5P,COI Animals / BOLD public clustered reference,Sequence ID CSV,99.6,96,0.009,0.018,ACGTTGACCTAGGCT\n"
    )

    assert parsed["validation"]["ok"] is True
    request = BarcodeCompilerRequest(**parsed["request"])
    assert request.records[0].sequence_id == "alias-1"
    assert request.records[0].metadata["occurrenceID"] == "urn:alias:1"
    assert request.records[0].hits[0].taxon == "Aedes albopictus"

    pack = run_barcode_compiler(request)
    assert pack["records"][0]["decision_class"] == "species-safe"


def test_import_csv_api_returns_request_preview_and_validation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    text = (EXAMPLES_DIR / "aedes_good.csv").read_text(encoding="utf-8")

    response = client.post("/api/barcode/import-csv", files={"file": ("aedes_good.csv", text, "text/csv")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["validation"]["ok"] is True
    assert payload["validation"]["records_found"] == 1
    assert payload["preview_rows"][0]["sequenceID"] == "AALB-COI-good"
    assert payload["request"]["records"][0]["hits"][0]["taxon"] == "Aedes albopictus"


def test_run_csv_api_creates_run_and_exports_zip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    text = (EXAMPLES_DIR / "aedes_good.csv").read_text(encoding="utf-8")

    response = client.post("/api/barcode/run-csv", files={"file": ("aedes_good.csv", text, "text/csv")})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["summary"]["species_safe_records"] == 1
    assert any(item["name"] == "evidence_pack.zip" for item in payload["exports"])
    assert barcode_artifact_path(payload["run_id"], "evidence_pack.zip").exists()


def test_run_csv_api_rejects_fatal_validation_errors(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/barcode/run-csv",
        files={"file": ("bad.csv", "sequenceID,sequence\nbad-1,ACGTXYZ\n", "text/csv")},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["ok"] is False
