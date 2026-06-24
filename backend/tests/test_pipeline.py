from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import zipfile

import requests

from app.evidence.gbif import GBIFClient, normalize_occurrences
from app.evidence.pipeline import run_evidence_passport
from app.evidence.schemas import EvidenceRunRequest
from app.evidence.science import hill_metrics
from app.evidence.storage import artifact_path


def test_gbif_normalization_preserves_provenance() -> None:
    payload = GBIFClient(mode="fixture").occurrence_search(
        taxon_key=1651430,
        bbox=[-10.0, 35.0, 4.5, 44.5],
        limit=300,
        use_fixture=True,
    )
    records = normalize_occurrences(payload, max_records=300)

    first = records[0]
    assert first.gbif_id == "1001"
    assert first.dataset_key == "spain-mosquito-watch"
    assert first.license == "CC_BY_4_0"
    assert first.accepted_taxon_key == "1651430"
    assert first.has_valid_coordinate is True


def test_hill_metrics_flags_under_sampled_community() -> None:
    metrics = hill_metrics(Counter({"taxon:a": 2, "taxon:b": 1, "taxon:c": 1}))

    assert metrics["occurrence_count"] == 4
    assert metrics["species_count"] == 3
    assert metrics["good_coverage"] == 0.5
    assert metrics["coverage_status"] == "under_sampled"


def test_purpose_aware_score_changes_by_purpose(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    common = {
        "taxon": "Aedes albopictus",
        "region_name": "Spain demo bbox",
        "bbox": [-10.0, 35.0, 4.5, 44.5],
        "use_fixture": True,
    }

    invasive = run_evidence_passport(EvidenceRunRequest(**common, purpose="invasive_watch"))
    sampling = run_evidence_passport(EvidenceRunRequest(**common, purpose="sampling_gaps"))

    assert invasive["evidence_readiness"]["score"] != sampling["evidence_readiness"]["score"]
    assert invasive["evidence_readiness"]["weights"]["temporal_recency"] > sampling["evidence_readiness"]["weights"]["temporal_recency"]
    assert sampling["evidence_readiness"]["weights"]["sampling_coverage"] > invasive["evidence_readiness"]["weights"]["sampling_coverage"]


def test_source_mode_compatibility_grid_and_exports(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.evidence.gbif.requests.get", lambda *_, **__: (_ for _ in ()).throw(requests.Timeout("offline")))
    pack = run_evidence_passport(EvidenceRunRequest(use_fixture=False))

    assert pack["source_summary"]["requested_source_mode"] == "online_with_empty_fallback"
    assert pack["source_summary"]["fallback_used"] is True
    assert pack["source_summary"]["used_source_mode"] == "online_empty_fallback"
    assert pack["passport"]["records_used"] == 0
    assert pack["records_geojson"]["features"] == []
    assert pack["grid_metrics"]["meta"]["cell_count"] == 16
    assert pack["grid_metrics"]["meta"]["empty_cell_count"] == 16
    assert pack["grid_metrics"]["meta"]["top_survey_priority_cells"]
    assert "gap_priority_score" in pack["grid_metrics"]["features"][0]["properties"]
    assert set(pack["purpose_score_matrix"]) == {
        "conservation_brief",
        "invasive_watch",
        "sampling_gaps",
        "dataset_quality_review",
    }

    export_names = {item["name"] for item in pack["exports"]}
    assert {
        "claim_guardrails.md",
        "decision_memo.md",
        "submission_readiness.md",
        "validation_summary.md",
        "impact_brief.md",
        "video_script.md",
        "decision_memo.json",
        "submission_readiness.json",
        "validation_summary.json",
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
        "evidence_pack.zip",
    } <= export_names

    with zipfile.ZipFile(artifact_path(pack["run"]["run_id"], "evidence_pack.zip")) as archive:
        assert {
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
            "provenance.json",
            "vault/index.md",
            f"vault/runs/{pack['run']['run_id']}.md",
        } <= set(archive.namelist())

    with zipfile.ZipFile(artifact_path(pack["run"]["run_id"], "evidence_vault.zip")) as archive:
        assert "index.md" in archive.namelist()
        assert f"runs/{pack['run']['run_id']}.md" in archive.namelist()


def test_empty_fallback_does_not_reuse_fixture_records(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setattr("app.evidence.gbif.requests.get", lambda *_, **__: (_ for _ in ()).throw(requests.Timeout("offline")))

    pack = run_evidence_passport(
        EvidenceRunRequest(
            taxon="Lynx pardinus",
            taxon_key=2435261,
            region_name="Iberian Peninsula GBIF bbox",
            bbox=[-10.0, 35.0, 4.5, 44.5],
            purpose="dataset_quality_review",
            source_mode="online_with_empty_fallback",
            max_records=300,
        )
    )

    assert pack["citation_autopilot"]["citation_status"] == "online_failed_empty_fallback"
    assert pack["source_summary"]["used_source_mode"] == "online_empty_fallback"
    assert pack["passport"]["records_used"] == 0
    assert pack["dataset_contributions"] == []
    assert pack["records_geojson"]["features"] == []
    assert pack["grid_metrics"]["meta"]["empty_cell_count"] == 16
    assert any("No old fixture occurrence records were reused" in warning for warning in pack["source_summary"]["warnings"])


def test_request_fingerprint_changes_with_request_inputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    first = run_evidence_passport(EvidenceRunRequest(use_fixture=True, taxon="Aedes albopictus"))
    second = run_evidence_passport(EvidenceRunRequest(use_fixture=True, taxon="Quercus robur", taxon_key=2878688))
    third = run_evidence_passport(
        EvidenceRunRequest(
            use_fixture=True,
            taxon="Aedes albopictus",
            bbox=[-9.0, 35.0, 4.5, 44.5],
        )
    )

    assert first["request_fingerprint"] != second["request_fingerprint"]
    assert first["request_fingerprint"] != third["request_fingerprint"]
    assert first["run"]["request_fingerprint"] == first["request_fingerprint"]


def test_claim_guardrails_and_publisher_feedback(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    pack = run_evidence_passport(EvidenceRunRequest(use_fixture=True, purpose="dataset_quality_review"))

    assert any("Absence cannot be inferred" in claim for claim in pack["claim_guardrails"]["unsupported_claims"])
    assert any(row["datasetKey"] == "legacy-mosquito-import" for row in pack["publisher_feedback"])
    assert any(row["main_issue"] == "High coordinate uncertainty" for row in pack["publisher_feedback"])
    assert pack["citation_autopilot"]["derived_dataset_recipe"]["group_by"] == "datasetKey"
    assert any(not item["ready"] for item in pack["citation_autopilot"]["doi_completion_flow"])
    assert pack["publisher_feedback"][0]["fix_priority"] == 1
    assert pack["publisher_feedback"][0]["severity"] in {"high", "medium", "low"}
    assert pack["graph_memory"]["graph"]["node_counts"]["claims"] >= 4
    assert "index.md" in pack["graph_memory"]["vault"]
    assert "artifact_checksums" in pack["run"]
    assert pack["decision_memo"]["verdict"]
    assert pack["submission_readiness"]["ready_count"] >= 7
    assert any(item["id"] == "doi_backed_case" for item in pack["submission_readiness"]["checklist"])
    assert pack["validation_summary"]["recommended_demo_suite"]


def test_evidence_passport_schema_is_valid_json() -> None:
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "evidence_passport.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    assert schema["title"] == "EcoGenesis GBIF Evidence Passport"
    assert "decision_memo" in schema["required"]
    assert schema["properties"]["passport"]["properties"]["title"]["const"] == "GBIF Evidence Passport"
