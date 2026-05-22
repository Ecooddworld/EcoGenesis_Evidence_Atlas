from __future__ import annotations

from fastapi.testclient import TestClient
import requests

from app.main import app


class FakeGBIFResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


def test_gbif_status_reports_reachable_api(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.evidence.gbif.requests.get",
        lambda *_, **__: FakeGBIFResponse(
            [
                {
                    "key": 1651430,
                    "scientificName": "Aedes albopictus (Skuse, 1894)",
                    "canonicalName": "Aedes albopictus",
                    "rank": "SPECIES",
                }
            ]
        ),
    )
    client = TestClient(app)

    response = client.get("/api/evidence/gbif-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["base_url"] == "https://api.gbif.org/v1"
    assert "Live occurrence runs use GBIF-mediated records" in payload["message"]


def test_gbif_status_reports_unavailable_api(monkeypatch) -> None:
    monkeypatch.setattr("app.evidence.gbif.requests.get", lambda *_, **__: (_ for _ in ()).throw(requests.Timeout("offline")))
    client = TestClient(app)

    response = client.get("/api/evidence/gbif-status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "unavailable"
    assert payload["base_url"] == "https://api.gbif.org/v1"
    assert "empty no-evidence fallback" in payload["message"]


def test_fixture_run_and_export_endpoints(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/evidence/run",
        json={
            "taxon": "Aedes albopictus",
            "region_name": "Spain demo bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "use_fixture": True,
            "max_records": 300,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    run_id = payload["run_id"]
    assert payload["status"] == "completed"
    assert {item["name"] for item in payload["exports"]} >= {
        "passport.html",
        "evidence_pack.json",
        "citations.md",
        "evidence_pack.zip",
        "claim_guardrails.md",
        "decision_memo.md",
        "submission_readiness.md",
        "validation_summary.md",
        "impact_brief.md",
        "video_script.md",
        "readiness_scorecard.csv",
        "source_summary.json",
        "demo_scenario.json",
        "gap_priorities.csv",
        "methods_text.md",
        "publisher_feedback.csv",
        "publisher_issue_templates.md",
        "derived_dataset_recipe.json",
        "evidence_graph.json",
        "graph_memory.md",
        "evidence_vault.zip",
        "provenance.json",
    }

    detail = client.get(f"/api/evidence/runs/{run_id}")
    assert detail.status_code == 200
    assert detail.json()["passport"]["records_used"] == 12

    claims = client.get(f"/api/evidence/runs/{run_id}/claims")
    assert claims.status_code == 200
    assert "unsupported_claims" in claims.json()

    feedback = client.get(f"/api/evidence/runs/{run_id}/publisher-feedback")
    assert feedback.status_code == 200
    assert isinstance(feedback.json(), list)
    assert "severity" in feedback.json()[0]

    graph_memory = client.get(f"/api/evidence/runs/{run_id}/graph-memory")
    assert graph_memory.status_code == 200
    assert graph_memory.json()["summary"]["run_id"] == run_id
    assert graph_memory.json()["node_counts"]["datasets"] >= 1

    submission = client.get(f"/api/evidence/runs/{run_id}/submission-readiness")
    assert submission.status_code == 200
    assert submission.json()["decision_memo"]["verdict"]
    assert submission.json()["submission_readiness"]["ready_count"] >= 7

    geojson = client.get(f"/api/evidence/runs/{run_id}/map")
    assert geojson.status_code == 200
    assert geojson.json()["type"] == "FeatureCollection"

    map_layers = client.get(f"/api/evidence/runs/{run_id}/map-layers")
    assert map_layers.status_code == 200
    assert map_layers.json()["grid"]["meta"]["cell_count"] == 16

    gaps = client.get(f"/api/evidence/runs/{run_id}/sampling-gaps")
    assert gaps.status_code == 200
    assert gaps.json()["priority_cells"]

    quality = client.get(f"/api/evidence/runs/{run_id}/quality")
    assert quality.status_code == 200
    assert quality.json()["quality_metrics"]["total_records"] == 12

    citations = client.get(f"/api/evidence/runs/{run_id}/citations")
    assert citations.status_code == 200
    assert citations.json()["citation_autopilot"]["derived_dataset_recipe"]["group_by"] == "datasetKey"
    assert citations.json()["citation_autopilot"]["doi_completion_flow"]

    passport = client.get(f"/api/evidence/runs/{run_id}/passport")
    assert passport.status_code == 200
    assert "GBIF Evidence Passport" in passport.text

    artifact = client.get(f"/api/evidence/runs/{run_id}/exports/citations.md")
    assert artifact.status_code == 200
    assert "Citation Autopilot" in artifact.text

    decision_artifact = client.get(f"/api/evidence/runs/{run_id}/exports/decision_memo.md")
    assert decision_artifact.status_code == 200
    assert "Decision Memo" in decision_artifact.text

    publisher_issue_templates = client.get(f"/api/evidence/runs/{run_id}/exports/publisher_issue_templates.md")
    assert publisher_issue_templates.status_code == 200
    assert "Publisher Issue Templates" in publisher_issue_templates.text

    zip_artifact = client.get(f"/api/evidence/runs/{run_id}/exports/evidence_pack.zip")
    assert zip_artifact.status_code == 200
    assert zip_artifact.headers["content-type"] in {"application/zip", "application/x-zip-compressed"}

    vault_artifact = client.get(f"/api/evidence/runs/{run_id}/exports/evidence_vault.zip")
    assert vault_artifact.status_code == 200
    assert vault_artifact.headers["content-type"] in {"application/zip", "application/x-zip-compressed"}

    zip_head = client.head(f"/api/evidence/runs/{run_id}/exports/evidence_pack.zip")
    assert zip_head.status_code == 200
    assert int(zip_head.headers["content-length"]) > 0

    runs = client.get("/api/evidence/runs")
    assert runs.status_code == 200
    assert any(row["run_id"] == run_id for row in runs.json())

    scenarios = client.get("/api/evidence/demo-scenarios")
    assert scenarios.status_code == 200
    assert scenarios.json()[0]["form"]["source_mode"] == "online_with_empty_fallback"

    regions = client.get("/api/evidence/region-presets")
    assert regions.status_code == 200
    assert any(row["id"] == "spain" for row in regions.json())

    taxon_suggest = client.get("/api/evidence/taxon-suggest")
    assert taxon_suggest.status_code == 200
    assert taxon_suggest.json()["results"][0]["usageKey"] == 1651430


def test_selected_taxon_key_is_preserved_in_request_and_match(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    response = client.post(
        "/api/evidence/run",
        json={
            "taxon": "Quercus robur",
            "taxon_key": 2878688,
            "region_name": "Western Europe live bbox",
            "bbox": [-10.0, 42.0, 12.0, 56.0],
            "purpose": "sampling_gaps",
            "source_mode": "fixture",
            "max_records": 300,
        },
    )
    assert response.status_code == 200
    detail = client.get(f"/api/evidence/runs/{response.json()['run_id']}").json()
    assert detail["run"]["request"]["taxon_key"] == 2878688
    assert detail["passport"]["taxonKey"] == 2878688
    assert detail["source_summary"]["selected_taxon_key"] == 2878688


def test_online_failure_falls_back_when_requested(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.evidence.gbif.requests.get", lambda *_, **__: (_ for _ in ()).throw(requests.Timeout("offline")))
    client = TestClient(app)

    empty = client.post(
        "/api/evidence/run",
        json={
            "taxon": "Aedes albopictus",
            "region_name": "Spain demo bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "online_with_empty_fallback",
            "max_records": 300,
        },
    )
    assert empty.status_code == 200
    empty_detail = client.get(f"/api/evidence/runs/{empty.json()['run_id']}").json()
    assert empty_detail["source_summary"]["used_source_mode"] == "online_empty_fallback"
    assert empty_detail["passport"]["records_used"] == 0
    assert empty_detail["records_geojson"]["features"] == []
    assert empty_detail["citation_autopilot"]["citation_status"] == "online_failed_empty_fallback"

    response = client.post(
        "/api/evidence/run",
        json={
            "taxon": "Aedes albopictus",
            "region_name": "Spain demo bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "online_with_fixture_fallback",
            "max_records": 300,
        },
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]
    detail = client.get(f"/api/evidence/runs/{run_id}").json()
    assert detail["source_summary"]["fallback_used"] is True
    assert detail["citation_autopilot"]["citation_status"] == "online_failed_fixture_fallback"

    strict = client.post(
        "/api/evidence/run",
        json={
            "taxon": "Aedes albopictus",
            "region_name": "Spain demo bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "online",
            "max_records": 300,
        },
    )
    assert strict.status_code == 502
    assert strict.json()["detail"]["error"] == "gbif_api_failed"
