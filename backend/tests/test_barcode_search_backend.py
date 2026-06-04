from __future__ import annotations

from fastapi.testclient import TestClient

from app.barcode import search_backend
from app.barcode.compiler import run_barcode_compiler
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
    monkeypatch.setenv("GBIF_BACKBONE_ENRICH_UPLOADS", "false")
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


def test_user_reference_fasta_upload_then_search(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("USER_REFERENCE_DATA_DIR", str(tmp_path / "reference-datasets"))
    monkeypatch.setenv("GBIF_BACKBONE_ENRICH_UPLOADS", "false")
    client = TestClient(app)
    fasta = (
        ">AALB_USER_REF|Aedes albopictus|species|1651430\n"
        f"{QUERY}\n"
        ">AAEG_USER_REF|Aedes aegypti|species|1651431\n"
        "ACGTTGACCTAGGCTTACGATCGTATCGATGCTAGCTAGGATCCGATCGTACGATAGTAGCTAGCATCGGATCATACCGTAGCTAGCTAGGATAGCTAGGATCGATCGTACGAT\n"
    )

    upload = client.post(
        "/api/barcode/reference-datasets/upload",
        data={"dataset_id": "custom_aedes_coi", "title": "Custom Aedes COI", "marker": "COI-5P"},
        files={"file": ("custom_aedes.fasta", fasta, "text/plain")},
    )

    assert upload.status_code == 200
    dataset = upload.json()["dataset"]
    assert dataset["id"] == "custom_aedes_coi"
    assert dataset["source_type"] == "uploaded"
    assert dataset["records"] == 2

    datasets = client.get("/api/barcode/reference-datasets")
    assert any(row["id"] == "custom_aedes_coi" and row["source_type"] == "uploaded" for row in datasets.json())

    response = client.post(
        "/api/barcode/search",
        json={
            "sequence_id": "CUSTOM_QUERY",
            "sequence": QUERY,
            "reference_dataset": "custom_aedes_coi",
            "backend": "python-local",
            "compile": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["search"]["hits"][0]["taxon"] == "Aedes albopictus"
    assert payload["pack"]["records"][0]["decision_class"] == "species-safe"


def test_uploaded_reference_ambiguous_binomials_downgrade_to_genus(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("USER_REFERENCE_DATA_DIR", str(tmp_path / "reference-datasets"))
    monkeypatch.setenv("GBIF_BACKBONE_ENRICH_UPLOADS", "false")
    client = TestClient(app)
    fasta = (
        ">AALB_USER_REF|Aedes albopictus|species|1651430\n"
        f"{QUERY}\n"
        ">AAEG_USER_REF|Aedes aegypti|species|1651431\n"
        f"{QUERY}\n"
    )

    upload = client.post(
        "/api/barcode/reference-datasets/upload",
        data={"dataset_id": "ambiguous_aedes_coi", "title": "Ambiguous Aedes COI", "marker": "COI-5P"},
        files={"file": ("ambiguous_aedes.fasta", fasta, "text/plain")},
    )
    assert upload.status_code == 200

    response = client.post(
        "/api/barcode/search",
        json={
            "sequence_id": "AMBIGUOUS_QUERY",
            "sequence": QUERY,
            "reference_dataset": "ambiguous_aedes_coi",
            "backend": "python-local",
            "compile": True,
        },
    )

    assert response.status_code == 200
    record = response.json()["pack"]["records"][0]
    assert record["decision_class"] == "genus-safe"
    assert record["candidate_taxon"]["rank"] == "genus"
    assert record["candidate_taxon"]["name"] == "Aedes"
    assert record["published_taxon"]["rank"] == "genus"


def test_uploaded_reference_uses_gbif_backbone_enrichment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("USER_REFERENCE_DATA_DIR", str(tmp_path / "reference-datasets"))
    monkeypatch.setenv("GBIF_BACKBONE_ENRICH_UPLOADS", "true")

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "usageKey": 1651430,
                "scientificName": "Aedes albopictus (Skuse, 1894)",
                "canonicalName": "Aedes albopictus",
                "rank": "SPECIES",
                "status": "ACCEPTED",
                "confidence": 99,
                "matchType": "EXACT",
                "kingdom": "Animalia",
                "phylum": "Arthropoda",
                "class": "Insecta",
                "order": "Diptera",
                "family": "Culicidae",
                "genus": "Aedes",
                "species": "Aedes albopictus",
                "kingdomKey": 1,
                "phylumKey": 54,
                "classKey": 216,
                "orderKey": 811,
                "familyKey": 3346,
                "genusKey": 7924646,
                "speciesKey": 1651430,
            }

    def fake_get(url: str, params: dict, timeout: float) -> FakeResponse:
        assert url.endswith("/species/match")
        assert params == {"name": "Aedes albopictus"}
        assert timeout > 0
        return FakeResponse()

    monkeypatch.setattr(search_backend.requests, "get", fake_get)
    client = TestClient(app)
    upload = client.post(
        "/api/barcode/reference-datasets/upload",
        data={"dataset_id": "gbif_enriched_upload", "title": "GBIF enriched upload", "marker": "COI-5P"},
        files={"file": ("gbif_enriched.fasta", f">AALB_USER_REF Aedes albopictus\n{QUERY}\n", "text/plain")},
    )

    assert upload.status_code == 200
    manifest_path = tmp_path / "reference-datasets" / "gbif_enriched_upload" / "manifest.json"
    manifest = search_backend.json.loads(manifest_path.read_text(encoding="utf-8"))
    reference = manifest["references"]["AALB_USER_REF"]
    assert reference["gbif_taxon_key"] == 1651430
    assert reference["lineage"][5]["name"] == "Aedes"
    assert reference["lineage"][5]["taxon_key"] == 7924646
    assert reference["gbif_backbone_match"]["status"] == "enriched"
    assert manifest["gbif_backbone_enrichment"]["enriched_records"] == 1


def test_real_ncbi_aedes_pack_compiles_species_safe() -> None:
    manifest, fasta_path, _entries = search_backend.load_reference_dataset("ncbi_aedes_coi_small")
    sequence = next(iter(search_backend.read_fasta(fasta_path).values()))

    result = search_reference(
        sequence=sequence,
        sequence_id="LC881945_1_AALB_COI",
        reference_dataset=manifest["id"],
        backend="python-local",
        max_hits=5,
    )
    request = search_backend.compiler_request_from_search(result, sequence=sequence, sequence_id="LC881945_1_AALB_COI")
    pack = run_barcode_compiler(request)
    record = pack["records"][0]

    assert result["hits"][0]["taxon"] == "Aedes albopictus"
    assert result["hits"][0]["gbif_taxon_key"] == 1651430
    assert record["decision_class"] == "species-safe"
    assert record["published_taxon"]["name"] == "Aedes albopictus"


def test_real_ncbi_quercus_pack_downgrades_conserved_rbcl_to_genus() -> None:
    manifest, fasta_path, _entries = search_backend.load_reference_dataset("ncbi_quercus_rbcl_small")
    sequence = next(iter(search_backend.read_fasta(fasta_path).values()))

    result = search_reference(
        sequence=sequence,
        sequence_id="PQ178973_1_QROB_RBCL",
        reference_dataset=manifest["id"],
        backend="python-local",
        max_hits=5,
    )
    request = search_backend.compiler_request_from_search(result, sequence=sequence, sequence_id="PQ178973_1_QROB_RBCL")
    pack = run_barcode_compiler(request)
    record = pack["records"][0]

    assert result["hits"][0]["taxon"] == "Quercus robur"
    assert result["hits"][1]["taxon"] == "Quercus petraea"
    assert result["hits"][1]["identity"] == 100
    assert record["decision_class"] == "genus-safe"
    assert record["published_taxon"] == {"rank": "genus", "name": "Quercus", "taxon_key": 2877951}


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
