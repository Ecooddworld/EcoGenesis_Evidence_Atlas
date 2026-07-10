from __future__ import annotations

import json
from typing import Any

from .barcode.search_backend import search_status
from .competition_reports import list_competition_report_summaries
from .observatory.storage import latest_observatory_run_id
from .observatory.verification import verify_observatory_run_outputs


def contest_readiness_dossier() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    backend_status = search_status()
    competition = list_competition_report_summaries()
    latest_run_id = latest_observatory_run_id()
    observatory_verification: dict[str, Any] | None = None

    require(checks, "api_service_ok", True, "ecogenesis-barcode-gbif-compiler")
    require(
        checks,
        "reference_search_backend_available",
        any(backend_status.get("available_backends", {}).values()),
        backend_status.get("preferred_backend"),
    )
    require(
        checks,
        "competition_regression_batches_pass",
        all(
            report.get("summary", {}).get("regression_status") == "pass"
            for report in competition.get("reports", [])
        ),
        {
            report.get("report_id"): report.get("summary", {}).get("regression_status")
            for report in competition.get("reports", [])
        },
    )
    review(
        checks,
        "independent_external_validation_attached",
        competition.get("status") == "pass",
        competition.get("status"),
    )
    for report in competition.get("reports", []):
        report_id = report.get("report_id", "unknown")
        summary = report.get("summary", {})
        require(checks, f"{report_id}:records_100", summary.get("records") == 100, summary.get("records"))
        require(checks, f"{report_id}:expected_failed_0", summary.get("expected_failed") == 0, summary.get("expected_failed"))
        require(
            checks,
            f"{report_id}:rule_evidence_parquet",
            summary.get("rule_evidence_parquet_magic") == "PAR1",
            summary.get("rule_evidence_parquet_magic"),
        )
        require(
            checks,
            f"{report_id}:release_invariants_have_no_failures",
            summary.get("release_invariant_gate") in {"pass", "review"}
            and summary.get("release_invariant_failures") == 0,
            {
                "gate": summary.get("release_invariant_gate"),
                "failures": summary.get("release_invariant_failures"),
            },
        )
        require(checks, f"{report_id}:graph_roundtrip", summary.get("graph_roundtrip_status") == "pass", summary.get("graph_roundtrip_status"))

    require(checks, "observatory_latest_run_exists", bool(latest_run_id), latest_run_id or "missing")
    if latest_run_id:
        try:
            observatory_verification = verify_observatory_run_outputs(latest_run_id)
        except FileNotFoundError:
            observatory_verification = None
        verification_summary = observatory_verification.get("summary", {}) if observatory_verification else {}
        require(checks, "observatory_run_verification_pass", verification_summary.get("status") == "pass", verification_summary.get("status", "missing"))
        require(checks, "observatory_run_failed_0", verification_summary.get("failed") == 0, verification_summary.get("failed", "missing"))
        require(checks, "observatory_run_zip_checked", verification_summary.get("zip_entries", 0) >= 40, verification_summary.get("zip_entries", "missing"))

    failed = [check for check in checks if check["status"] == "fail"]
    review_required = [check for check in checks if check["status"] == "review"]
    return {
        "schema": "ecogenesis.contest_readiness.dossier.v1",
        "status": "fail" if failed else "review" if review_required else "pass",
        "summary": {
            "checks": len(checks),
            "failed": len(failed),
            "review_required": len(review_required),
            "competition_reports": len(competition.get("reports", [])),
            "competition_status": competition.get("status"),
            "observatory_run_id": latest_run_id,
            "observatory_status": (observatory_verification or {}).get("summary", {}).get("status", "missing"),
            "reference_backend": backend_status.get("preferred_backend"),
        },
        "checks": checks,
        "backend": backend_status,
        "competition": competition,
        "observatory_verification": observatory_verification,
        "downloads": contest_readiness_downloads(latest_run_id, competition),
    }


def contest_readiness_markdown(dossier: dict[str, Any]) -> str:
    summary = dossier.get("summary", {})
    checks = dossier.get("checks", [])
    failed = [check for check in checks if check.get("status") == "fail"]
    review_required = [check for check in checks if check.get("status") == "review"]
    checks_table = "\n".join(
        f"| `{check.get('name')}` | `{check.get('status')}` | `{format_observed(check.get('observed'))}` |"
        for check in checks
    )
    failures = "\n".join(
        f"- `{check.get('name')}` observed `{format_observed(check.get('observed'))}`"
        for check in failed
    ) or "- none"
    reviews = "\n".join(
        f"- `{check.get('name')}` observed `{format_observed(check.get('observed'))}`"
        for check in review_required
    ) or "- none"
    competition_lines = "\n".join(
        f"- `{report.get('report_id')}`: `{report.get('summary', {}).get('status')}`, "
        f"{report.get('summary', {}).get('records')} records, "
        f"{report.get('summary', {}).get('expected_failed')} failed"
        for report in dossier.get("competition", {}).get("reports", [])
    ) or "- none"
    return f"""# EcoGenesis Contest Readiness Dossier

Status: `{dossier.get("status")}`

| Metric | Value |
| --- | --- |
| Checks | `{summary.get("checks", 0)}` |
| Failed | `{summary.get("failed", 0)}` |
| Review required | `{summary.get("review_required", 0)}` |
| Reference backend | `{summary.get("reference_backend", "missing")}` |
| Competition status | `{summary.get("competition_status", "missing")}` |
| Observatory run | `{summary.get("observatory_run_id") or "missing"}` |
| Observatory verification | `{summary.get("observatory_status", "missing")}` |

## Competition Packs

{competition_lines}

## Failed Checks

{failures}

## Review / External Evidence Required

{reviews}

## All Checks

| Check | Status | Observed |
| --- | --- | --- |
{checks_table}

## Boundary

This dossier summarizes system readiness and export integrity checks. It does not convert occurrence context, visualization, or AI-ready labels into stronger biological claims; claim strength remains governed by barcode gates, rule-evidence segment rows, graph provenance, and release invariants.
"""


def require(checks: list[dict[str, Any]], name: str, predicate: bool, observed: Any) -> None:
    checks.append({"name": name, "status": "pass" if predicate else "fail", "observed": observed})


def review(checks: list[dict[str, Any]], name: str, predicate: bool, observed: Any) -> None:
    """Record a non-failing boundary that still requires external evidence."""
    checks.append({"name": name, "status": "pass" if predicate else "review", "observed": observed})


def contest_readiness_downloads(latest_run_id: str | None, competition: dict[str, Any]) -> list[dict[str, str]]:
    downloads = [
        {"name": "contest_readiness.json", "url": "/api/contest-readiness"},
        {"name": "contest_readiness.md", "url": "/api/contest-readiness/report.md"},
    ]
    if latest_run_id:
        downloads.append(
            {
                "name": "latest_observatory_verification.md",
                "url": f"/api/observatory/runs/{latest_run_id}/verification/report.md",
            }
        )
    for report in competition.get("reports", []):
        for item in report.get("downloads", [])[:2]:
            downloads.append({"name": item["name"], "url": item["url"]})
    return downloads


def format_observed(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)
