from __future__ import annotations

from fastapi.testclient import TestClient

from app.barcode.search_backend import search_reference
from app.main import app


QUERY = (
    "ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCG"
    "GATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGTACGAT"
)


def test_python_local_reference_search_returns_ranked_hits() -> None:
    result = search_reference(
        sequence=QUERY,
        sequence_id="AALB_SEARCH_QUERY",
        reference_dataset="aedes_coi_mini",
        backend="python-local",
        max_hits=3,
    )

    assert result["backend_used"] == "python-local"
    assert result["reference_dataset"]["id"] == "aedes_coi_mini"
    assert result["hits"][0]["taxon"] == "Aedes albopictus"
    assert result["hits"][0]["identity"] == 100
    assert result["hits"][0]["query_coverage"] == 100
    assert len(result["hits"]) == 3


def test_reference_dataset_and_search_api_compile_run(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    status = client.get("/api/barcode/search-status")
    assert status.status_code == 200
    assert status.json()["available_backends"]["python-local"] is True

    datasets = client.get("/api/barcode/reference-datasets")
    assert datasets.status_code == 200
    assert any(row["id"] == "aedes_coi_mini" for row in datasets.json())

    response = client.post(
        "/api/barcode/search",
        json={
            "sequence_id": "AALB_SEARCH_QUERY",
            "sequence": QUERY,
            "reference_dataset": "aedes_coi_mini",
            "backend": "python-local",
            "compile": True,
            "metadata": {
                "countryCode": "ES",
                "decimalLatitude": 40.4168,
                "decimalLongitude": -3.7038,
                "geodeticDatum": "WGS84",
                "coordinateUncertaintyInMeters": 50,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["search"]["hits"][0]["taxon"] == "Aedes albopictus"
    assert payload["run"]["status"] == "completed"
    assert payload["pack"]["records"][0]["decision_class"] == "species-safe"
    assert payload["pack"]["records"][0]["published_taxon"]["name"] == "Aedes albopictus"
    assert payload["pack"]["metrics"]["hard_gate_failures"] == 0


def test_reference_search_rejects_invalid_sequence() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/barcode/search",
        json={
            "sequence_id": "bad-query",
            "sequence": "ACGTXYZ",
            "reference_dataset": "aedes_coi_mini",
            "backend": "python-local",
        },
    )

    assert response.status_code == 422
    assert "unsupported characters" in response.json()["detail"]
