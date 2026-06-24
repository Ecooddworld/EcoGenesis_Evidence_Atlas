from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.competition_reports import list_competition_report_summaries
from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_competition_reports_api_reads_frozen_100_sequence_batches(monkeypatch) -> None:
    monkeypatch.setenv("COMPETITION_REPORTS_DIR", str(REPO_ROOT / "reports"))
    client = TestClient(app)

    index = client.get("/api/competition-reports")
    assert index.status_code == 200
    body = index.json()
    assert body["status"] == "pass"
    reports = {item["report_id"]: item for item in body["reports"]}
    assert set(reports) == {"competition-100-sequences", "adversarial-100-sequences"}

    competition = reports["competition-100-sequences"]
    assert competition["summary"]["status"] == "pass"
    assert competition["summary"]["records"] == 100
    assert competition["summary"]["expected_matched"] == 100
    assert competition["summary"]["expected_failed"] == 0
    assert competition["summary"]["exports"] == 90
    assert competition["summary"]["vsea_parquet_magic"] == "PAR1"
    assert competition["summary"]["theorem_release_gate"] == "pass"
    assert competition["summary"]["math_viability_status"] == "pass"
    assert competition["summary"]["math_viability_failures"] == 0
    assert competition["summary"]["math_viability_checks"] > 0
    assert competition["summary"]["graph_roundtrip_status"] == "pass"
    assert competition["decision_classes"]["species-safe"] == 25

    adversarial = client.get("/api/competition-reports/adversarial-100-sequences")
    assert adversarial.status_code == 200
    assert adversarial.json()["summary"]["records"] == 100
    assert adversarial.json()["decision_classes"]["not-publishable"] == 30

    report = client.get("/api/competition-reports/competition-100-sequences/files/competition_100_sequence_report.md")
    assert report.status_code == 200
    assert "Competition 100-Sequence Atlas Run Report" in report.text

    report_head = client.head("/api/competition-reports/competition-100-sequences/files/evidence_pack.zip")
    assert report_head.status_code == 200
    assert int(report_head.headers["content-length"]) > 0

    blocked = client.get("/api/competition-reports/competition-100-sequences/files/../README.md")
    assert blocked.status_code == 404


def test_competition_reports_default_root_survives_backend_cwd(monkeypatch) -> None:
    monkeypatch.delenv("COMPETITION_REPORTS_DIR", raising=False)
    monkeypatch.chdir(REPO_ROOT / "backend")

    body = list_competition_report_summaries()

    assert body["status"] == "pass"
    assert {item["summary"]["records"] for item in body["reports"]} == {100}


def test_contest_readiness_dossier_aggregates_competition_and_observatory(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("COMPETITION_REPORTS_DIR", str(REPO_ROOT / "reports"))
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    created = client.post("/api/observatory/run-demo", json={"mode": "offline_demo", "force_fixture": True, "limit": 20})
    assert created.status_code == 200
    run_id = created.json()["run_id"]

    readiness = client.get("/api/contest-readiness")
    assert readiness.status_code == 200
    body = readiness.json()
    assert body["status"] == "pass"
    assert body["summary"]["failed"] == 0
    assert body["summary"]["competition_status"] == "pass"
    assert body["summary"]["observatory_run_id"] == run_id
    assert body["summary"]["observatory_status"] == "pass"
    assert any(check["name"] == "observatory_run_verification_pass" for check in body["checks"])

    report = client.get("/api/contest-readiness/report.md")
    assert report.status_code == 200
    assert "# EcoGenesis Contest Readiness Dossier" in report.text
    assert "Status: `pass`" in report.text

    report_head = client.head("/api/contest-readiness/report.md")
    assert report_head.status_code == 200
    assert int(report_head.headers["content-length"]) > 0
