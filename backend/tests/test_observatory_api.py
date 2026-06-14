from __future__ import annotations

from fastapi.testclient import TestClient
import requests

from app.main import app
from app.observatory.pipeline import run_observatory_demo
from app.observatory.schemas import ObservatoryRunRequest
from app.observatory.storage import load_observatory_pack, observatory_artifact_path, observatory_export_manifest


OPO_ARTIFACTS = {
    "source_registry_audit.json",
    "snapshot_manifest.json",
    "api_policy_audit.csv",
    "gbif_query_strategy_audit.csv",
    "source_provenance_manifest.json",
    "vsea_provenance_audit.csv",
    "visualization_guardrail_audit.csv",
    "blocked_claim_visibility_audit.csv",
    "sharedness_visual_overclaim_audit.csv",
    "ai_dataset_export_audit.csv",
    "literature_claim_state_audit.csv",
    "contradiction_visual_audit.csv",
    "gbif_export_claim_boundary_audit.csv",
    "repair_optimizer_guardrail_audit.csv",
    "offline_demo_reproducibility.json",
    "ui_ledger_consistency_audit.csv",
    "graph_roundtrip_audit.csv",
    "source_freshness_claim_audit.csv",
    "license_blocker_audit.csv",
    "judge_mode_non_claims_audit.csv",
}


def test_observatory_pipeline_builds_release_pack(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = run_observatory_demo(ObservatoryRunRequest(mode="offline_demo", force_fixture=True, limit=20))
    export_names = {item["name"] for item in pack["exports"]}

    assert pack["summary"]["hard_gate_status"] == "pass"
    assert pack["proof_summary"]["hard_gate_failures"] == 0
    assert pack["summary"]["normalized_occurrence_records"] == 12
    assert pack["summary"]["segments"] == 4
    assert pack["summary"]["gbif_export_states"]["candidate_gbif_row"] >= 1
    assert OPO_ARTIFACTS <= export_names
    assert {
        "observatory_evidence_pack.json",
        "observatory_report.md",
        "observatory_vsea.csv",
        "observatory_vsea.parquet",
        "observatory_graph.jsonld",
        "gbif_export_preview.csv",
        "ai_ready_dataset.jsonl",
        "observatory_evidence_pack.zip",
    } <= export_names
    actual_exports = observatory_export_manifest(pack["run"]["run_id"])
    assert pack["exports"] == actual_exports
    persisted_pack = load_observatory_pack(pack["run"]["run_id"])
    persisted_exports = {item["name"]: item for item in persisted_pack["exports"]}
    for name in {"observatory_evidence_pack.json", "observatory_evidence_pack.zip"}:
        assert persisted_exports[name]["sha256"] is None
        assert persisted_exports[name]["checksum_status"] == "external_manifest_only"
        assert name not in persisted_pack["run"]["artifact_checksums"]
    assert observatory_artifact_path(pack["run"]["run_id"], "observatory_vsea.parquet").read_bytes()[:4] == b"PAR1"
    assert all(row["context_claim_boundary"].startswith("GBIF context") for row in pack["vsea"])


def test_observatory_api_endpoints(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    created = client.post("/api/observatory/run-demo", json={"mode": "offline-demo", "force_fixture": True, "limit": 20})
    assert created.status_code == 200
    run_id = created.json()["run_id"]

    status = client.get("/api/observatory/status")
    assert status.status_code == 200
    assert status.json()["latest_run"]["run_id"] == run_id

    sources = client.get("/api/observatory/sources")
    assert sources.status_code == 200
    assert sources.json()["audit"]["status"] == "pass"

    vsea = client.get("/api/observatory/vsea", params={"run_id": run_id})
    assert vsea.status_code == 200
    rows = vsea.json()["rows"]
    assert rows
    assert any(row["claim_state"] == "weak_hypothesis" for row in rows)

    segment_id = rows[0]["segment_id"]
    segment = client.get(f"/api/observatory/segments/{segment_id}", params={"run_id": run_id})
    assert segment.status_code == 200
    assert segment.json()["segment_id"] == segment_id

    taxa = client.get(f"/api/observatory/segments/{segment_id}/taxa", params={"run_id": run_id})
    assert taxa.status_code == 200
    assert taxa.json()[0]["segment_id"] == segment_id

    sharedness = client.get(f"/api/observatory/segments/{segment_id}/sharedness", params={"run_id": run_id})
    assert sharedness.status_code == 200
    assert sharedness.json()["claim_boundary"].startswith("Sharedness")

    claim_id = segment.json()["claim_boundaries"][0]["claim_id"]
    provenance = client.get(f"/api/observatory/claims/{claim_id}/provenance", params={"run_id": run_id})
    assert provenance.status_code == 200
    assert provenance.json()["snapshot"]["snapshot_hash"]

    gbif_export = client.post("/api/observatory/export/gbif", params={"run_id": run_id})
    assert gbif_export.status_code == 200
    assert gbif_export.json()["artifact"]["name"] == "gbif_export_preview.csv"

    zip_head = client.head(f"/api/observatory/runs/{run_id}/exports/observatory_evidence_pack.zip")
    assert zip_head.status_code == 200
    assert int(zip_head.headers["content-length"]) > 0


def test_observatory_live_mode_records_fixture_fallback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.evidence.gbif.requests.get", lambda *_, **__: (_ for _ in ()).throw(requests.Timeout("offline")))

    pack = run_observatory_demo(ObservatoryRunRequest(mode="live_gbif_small", limit=20))

    assert pack["summary"]["fallback_used"] is True
    assert pack["snapshot_manifest"]["source_mode"] == "fixture_fallback"
    assert pack["snapshot_manifest"]["fallback_error"].startswith("Timeout")
