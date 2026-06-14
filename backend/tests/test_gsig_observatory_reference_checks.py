from __future__ import annotations

from app.observatory.reference_checks import (
    ai_export_is_safe,
    load_json,
    load_yaml,
    validate_pipeline_dag,
    validate_proof_obligations,
    validate_source_registry,
    validate_ui_contract,
    visual_claim_projection,
)


def test_observatory_source_registry_contract() -> None:
    errors = validate_source_registry(load_yaml("gsig_observatory_source_registry.yaml"))
    assert errors == []


def test_observatory_pipeline_dag_contract() -> None:
    errors = validate_pipeline_dag(load_yaml("gsig_observatory_pipeline_dag.yaml"))
    assert errors == []


def test_observatory_ui_contract() -> None:
    errors = validate_ui_contract(load_yaml("gsig_observatory_ui_contract.yaml"))
    assert errors == []


def test_observatory_proof_obligations_contract() -> None:
    errors = validate_proof_obligations(load_json("ecogenesis_gsig_observatory_proof_obligations_v4.json"))
    assert errors == []


def test_observatory_visualization_cannot_promote_claim_state() -> None:
    assert visual_claim_projection("taxon_supported", "verified_segment")
    assert not visual_claim_projection("verified_segment", "experimentally_supported")


def test_observatory_ai_export_label_separation() -> None:
    safe_rows = [
        {"segment_id": "s1", "claim_state": "taxon_supported", "label": "positive_verified"},
        {"segment_id": "s2", "claim_state": "statistical_hypothesis", "label": "candidate_hypothesis"},
    ]
    unsafe_rows = [
        {"segment_id": "s3", "claim_state": "statistical_hypothesis", "label": "positive_verified"},
    ]
    assert ai_export_is_safe(safe_rows)
    assert not ai_export_is_safe(unsafe_rows)
