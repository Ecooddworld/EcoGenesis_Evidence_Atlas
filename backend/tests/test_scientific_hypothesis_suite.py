from __future__ import annotations

from argparse import Namespace

from scripts.run_scientific_hypothesis_suite import build_claims, build_run_index, claim_templates


def fake_pack() -> dict:
    return {
        "run": {"run_id": "run-1"},
        "passport": {"records_used": 120, "datasets_used": 3},
        "source_summary": {"gbif_result_count": 500},
        "quality_metrics": {
            "valid_coordinate_rate": 0.99,
            "date_present_rate": 0.95,
            "recent_record_rate": 0.7,
            "high_uncertainty_count": 0,
            "missing_date_count": 0,
        },
        "grid_metrics": {
            "meta": {
                "grid_size": 4,
                "occupied_cell_count": 9,
                "empty_cell_count": 7,
                "survey_priority_cells": 8,
                "under_sampled_cells": 2,
            }
        },
        "evidence_readiness": {"score": 86, "components": {"spatial": 90}},
        "citation_autopilot": {"citation_status": "online_api_without_download_doi"},
        "dataset_contributions": [
            {"datasetKey": "a", "record_count": 50},
            {"datasetKey": "b", "record_count": 40},
            {"datasetKey": "c", "record_count": 30},
        ],
    }


def fake_scenario() -> dict:
    return {
        "id": "aedes-spain",
        "taxon": "Aedes albopictus",
        "taxon_key": 1651430,
        "region_name": "Spain GBIF bbox",
        "purpose": "invasive_watch",
    }


def test_claim_templates_create_ten_safe_hypotheses() -> None:
    rows = claim_templates(fake_scenario(), fake_pack())

    assert len(rows) == 10
    assert rows[0]["status"] == "supported"
    assert rows[7]["status"] == "blocked"
    assert rows[8]["status"] == "blocked"
    assert rows[9]["status"] == "requires_verification"
    assert all(row["evidence_fields"] and row["caveat"] and row["recommended_action"] for row in rows)


def test_build_claims_and_acceptance_summary() -> None:
    successful = [
        {
            "scenario": fake_scenario() | {"id": f"scenario-{index}"},
            "pack": fake_pack(),
            "eligible": True,
            "scenario_id": f"scenario-{index}",
        }
        for index in range(10)
    ]
    claims = build_claims(successful)
    attempted = [{"eligible": True, "scenario_id": f"scenario-{index}"} for index in range(10)]
    records = [{"gbif_id": str(index)} for index in range(1000)]
    args = Namespace(target_records=1000, target_claims=100)

    run_index = build_run_index(args, attempted, records, claims[:100], duplicate_count=3)

    assert len(claims) == 100
    assert run_index["duplicate_records_skipped"] == 3
    assert all(run_index["acceptance"].values())
