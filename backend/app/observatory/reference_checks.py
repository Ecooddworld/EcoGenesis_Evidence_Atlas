from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


CONTRACT_DIR = Path(__file__).resolve().parent / "contracts"
CLAIM_ORDER = {
    "blocked": 0,
    "raw": 1,
    "weak_hypothesis": 1,
    "normalized": 2,
    "taxon_ambiguous": 2,
    "verified_segment": 3,
    "taxon_supported": 4,
    "clade_specific": 5,
    "annotation_attached": 6,
    "statistical_hypothesis": 7,
    "experimentally_supported": 8,
}


def load_yaml(name: str) -> dict[str, Any]:
    return yaml.safe_load((CONTRACT_DIR / name).read_text(encoding="utf-8"))


def load_json(name: str) -> dict[str, Any]:
    return json.loads((CONTRACT_DIR / name).read_text(encoding="utf-8"))


def source_registry() -> dict[str, Any]:
    return load_yaml("gsig_observatory_source_registry.yaml")


def pipeline_dag() -> dict[str, Any]:
    return load_yaml("gsig_observatory_pipeline_dag.yaml")


def ui_contract() -> dict[str, Any]:
    return load_yaml("gsig_observatory_ui_contract.yaml")


def proof_obligations() -> dict[str, Any]:
    return load_json("ecogenesis_gsig_observatory_proof_obligations_v4.json")


def validate_source_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for src in registry.get("sources", []):
        sid = src.get("source_id", "<missing>")
        for field in [
            "license_policy",
            "rate_limit_policy",
            "provenance_required",
            "allowed_claims",
            "blocked_claims",
            "outputs",
        ]:
            if field not in src or src[field] in (None, "", []):
                errors.append(f"{sid}: missing {field}")
        if src.get("provenance_required") is not True:
            errors.append(f"{sid}: provenance_required must be true")
    return errors


def validate_pipeline_dag(dag: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    guardrails = " ".join(dag.get("global_guardrails", [])).lower()
    if "no visualization" not in guardrails or "no ai output" not in guardrails:
        errors.append("global guardrails must block visualization and AI claim promotion")
    for step in dag.get("steps", []):
        sid = step.get("id", "<missing>")
        if not step.get("module"):
            errors.append(f"{sid}: missing module")
        if not step.get("outputs"):
            errors.append(f"{sid}: missing outputs")
        if not step.get("validations"):
            errors.append(f"{sid}: missing validations")
    return errors


def validate_ui_contract(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    global_controls = set(contract.get("global_controls", []))
    required_global = {"claim_state_filter", "provenance_panel", "download_evidence_pack"}
    missing = required_global - global_controls
    if missing:
        errors.append(f"missing global controls: {sorted(missing)}")
    for screen in contract.get("screens", []):
        sid = screen.get("id", "<missing>")
        if not screen.get("required_widgets"):
            errors.append(f"{sid}: missing widgets")
        if not screen.get("guardrails"):
            errors.append(f"{sid}: missing guardrails")
    return errors


def validate_proof_obligations(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for item in contract.get("obligations", []):
        oid = item.get("id", "<missing>")
        for field in ["name", "artifact", "test", "acceptance_criteria", "severity", "claim_boundary"]:
            if not item.get(field):
                errors.append(f"{oid}: missing {field}")
        forbidden = ["full genome decoded", "absolute truth", "ai overwrites"]
        text = json.dumps(item).lower()
        for phrase in forbidden:
            if phrase in text:
                errors.append(f"{oid}: forbidden overclaim phrase {phrase}")
    return errors


def visual_claim_projection(graph_claim_state: str, ui_claim_state: str) -> bool:
    return CLAIM_ORDER[ui_claim_state] <= CLAIM_ORDER[graph_claim_state]


def ai_export_is_safe(rows: list[dict[str, str]]) -> bool:
    for row in rows:
        if row.get("label") == "positive_verified" and row.get("claim_state") in {
            "blocked",
            "weak_hypothesis",
            "statistical_hypothesis",
        }:
            return False
    return True


def contract_validation_summary() -> dict[str, Any]:
    checks = {
        "source_registry": validate_source_registry(source_registry()),
        "pipeline_dag": validate_pipeline_dag(pipeline_dag()),
        "ui_contract": validate_ui_contract(ui_contract()),
        "proof_obligations": validate_proof_obligations(proof_obligations()),
    }
    return {
        "status": "pass" if all(not errors for errors in checks.values()) else "fail",
        "checks": checks,
        "contract_versions": {
            "source_registry": source_registry().get("registry_version"),
            "pipeline_dag": pipeline_dag().get("dag_version"),
            "ui_contract": ui_contract().get("ui_contract_version"),
            "proof_obligation_set": proof_obligations().get("proof_obligation_set"),
        },
    }
