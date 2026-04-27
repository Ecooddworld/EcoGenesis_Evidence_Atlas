from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import os
from time import perf_counter
from typing import Any, Callable, TypeVar
from uuid import uuid4

from .artifacts import build_artifacts
from .gbif import GBIFClient, NormalizedOccurrence, normalize_occurrences
from .schemas import EvidenceRunRequest, SourceMode
from .science import build_grid_metrics, build_records_geojson, quality_metrics, serialize_records
from .scoring import PURPOSE_LABELS, purpose_score_matrix
from .storage import save_artifacts, save_zip_artifact


T = TypeVar("T")


class EvidenceRunError(Exception):
    def __init__(self, *, status_code: int, detail: dict[str, Any]) -> None:
        super().__init__(detail.get("message") or detail.get("error") or "Evidence run failed")
        self.status_code = status_code
        self.detail = detail


def run_evidence_passport(request: EvidenceRunRequest) -> dict[str, Any]:
    run_id = uuid4().hex
    started_at = datetime.now(timezone.utc)
    steps: list[dict[str, Any]] = []
    requested_source_mode = resolve_source_mode(request)

    species_match, raw_payload, source_summary = fetch_gbif_inputs(request, requested_source_mode, steps)
    records = timed_step(steps, "normalize", lambda: normalize_occurrences(raw_payload, max_records=request.max_records))
    current_year = datetime.now(timezone.utc).year

    def compute_science() -> dict[str, Any]:
        quality = quality_metrics(records, current_year=current_year)
        grid = build_grid_metrics(records, request.bbox, current_year=current_year)
        match_confidence = float(species_match.get("confidence") or 0)
        matrix = purpose_score_matrix(quality, grid, match_confidence=match_confidence)
        readiness = matrix[request.purpose]
        return {
            "quality": quality,
            "grid": grid,
            "purpose_matrix": matrix,
            "readiness": readiness,
        }

    science = timed_step(steps, "score", compute_science)
    quality = science["quality"]
    grid = science["grid"]
    readiness = science["readiness"]
    matrix = science["purpose_matrix"]
    dataset_contributions = summarize_dataset_contributions(records)
    claim_guardrails = build_claim_guardrails(records, quality, grid, readiness)
    publisher_feedback = build_publisher_feedback(records)
    citation_autopilot = build_citation_autopilot(request, records, dataset_contributions, source_summary=source_summary)
    records_geojson = build_records_geojson(records)
    main_risks = summarize_main_risks(quality, grid, citation_autopilot, source_summary)
    next_actions = build_next_actions(quality, grid, citation_autopilot, publisher_feedback, source_summary)
    finished_at = datetime.now(timezone.utc)

    pack: dict[str, Any] = {
        "run": {
            "run_id": run_id,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "source_mode": source_summary["used_source_mode"],
            "request": request.model_dump(),
            "gbif_species_match": species_match,
            "steps": steps,
        },
        "passport": {
            "title": "GBIF Evidence Passport",
            "taxon": request.taxon,
            "accepted_name": species_match.get("scientificName") or request.taxon,
            "taxonKey": species_match.get("usageKey"),
            "match_confidence": species_match.get("confidence"),
            "region_name": request.region_name,
            "bbox": request.bbox,
            "purpose": request.purpose,
            "records_used": len(records),
            "datasets_used": len(dataset_contributions),
        },
        "source_summary": source_summary,
        "evidence_readiness": readiness,
        "purpose_score_matrix": matrix,
        "quality_metrics": quality,
        "dataset_contributions": dataset_contributions,
        "claim_guardrails": claim_guardrails,
        "citation_autopilot": citation_autopilot,
        "publisher_feedback": publisher_feedback,
        "grid_metrics": grid,
        "records_geojson": records_geojson,
        "normalized_records": serialize_records(records),
        "main_risks": main_risks,
        "next_actions": next_actions,
    }

    export_started = perf_counter()
    artifacts = build_artifacts(pack)
    exports = save_artifacts(run_id, artifacts)
    zip_export = save_zip_artifact(run_id, artifacts)
    pack["exports"] = sorted([*exports, zip_export], key=lambda item: item["name"])
    steps.append(
        {
            "name": "exports",
            "status": "completed",
            "duration_ms": round((perf_counter() - export_started) * 1000, 2),
            "details": {"artifact_count": len(pack["exports"])},
        }
    )

    artifacts = build_artifacts(pack)
    exports = save_artifacts(run_id, artifacts)
    zip_export = save_zip_artifact(run_id, artifacts)
    pack["exports"] = sorted([*exports, zip_export], key=lambda item: item["name"])
    pack["run"]["artifact_checksums"] = {item["name"]: item.get("sha256") for item in pack["exports"]}
    final_artifacts = build_artifacts(pack)
    save_artifacts(
        run_id,
        {
            "evidence_pack.json": final_artifacts["evidence_pack.json"],
            "run.json": final_artifacts["run.json"],
            "provenance.json": final_artifacts["provenance.json"],
        },
    )
    save_zip_artifact(run_id, final_artifacts)
    return pack


def resolve_source_mode(request: EvidenceRunRequest) -> SourceMode:
    if request.source_mode:
        return request.source_mode
    if request.use_fixture:
        return "fixture"
    env_mode = os.getenv("EVIDENCE_MODE")
    if env_mode in {"online", "online_with_fixture_fallback"}:
        return env_mode  # type: ignore[return-value]
    return "online_with_fixture_fallback"


def fetch_gbif_inputs(
    request: EvidenceRunRequest,
    requested_source_mode: SourceMode,
    steps: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    base_summary: dict[str, Any] = {
        "requested_source_mode": requested_source_mode,
        "used_source_mode": requested_source_mode,
        "gbif_api_status": "not_called" if requested_source_mode == "fixture" else "pending",
        "fallback_used": False,
        "warnings": [],
        "gbif_base_url": os.getenv("GBIF_BASE_URL") or "https://api.gbif.org/v1",
        "selected_taxon_key": request.taxon_key,
    }
    if requested_source_mode == "fixture":
        client = GBIFClient(mode="fixture")
        species_match = timed_step(steps, "species_match", lambda: resolve_species_match(client, request, use_fixture=True))
        base_summary["matched_taxon_key"] = species_match.get("usageKey")
        raw_payload = timed_step(
            steps,
            "occurrence_fetch",
            lambda: client.occurrence_search(
                taxon_key=matched_taxon_key(species_match),
                bbox=request.bbox,
                limit=request.max_records,
                use_fixture=True,
            ),
        )
        attach_payload_summary(base_summary, raw_payload)
        return species_match, raw_payload, base_summary

    online_client = GBIFClient(mode="online")
    try:
        species_match = timed_step(steps, "species_match", lambda: resolve_species_match(online_client, request))
        base_summary["matched_taxon_key"] = species_match.get("usageKey")
        raw_payload = timed_step(
            steps,
            "occurrence_fetch",
            lambda: online_client.occurrence_search(
                taxon_key=matched_taxon_key(species_match),
                bbox=request.bbox,
                limit=request.max_records,
            ),
        )
        base_summary["used_source_mode"] = "online"
        base_summary["gbif_api_status"] = "ok"
        attach_payload_summary(base_summary, raw_payload)
        return species_match, raw_payload, base_summary
    except EvidenceRunError:
        raise
    except Exception as exc:
        message = f"GBIF API request failed: {type(exc).__name__}: {exc}"
        if requested_source_mode == "online":
            raise EvidenceRunError(
                status_code=502,
                detail={
                    "error": "gbif_api_failed",
                    "message": message,
                    "requested_source_mode": requested_source_mode,
                    "fallback_used": False,
                },
            ) from exc

        fixture_client = GBIFClient(mode="fixture")
        base_summary.update(
            {
                "used_source_mode": "fixture",
                "gbif_api_status": "failed",
                "fallback_used": True,
                "warnings": [
                    message,
                    "Fixture fallback was used to keep the judge demo reproducible; do not use this fallback pack for publication claims.",
                ],
            }
        )
        steps.append(
            {
                "name": "fixture_fallback",
                "status": "completed",
                "duration_ms": 0.0,
                "details": {"reason": message},
            }
        )
        species_match = timed_step(
            steps,
            "species_match_fixture_fallback",
            lambda: resolve_species_match(fixture_client, request, use_fixture=True),
        )
        base_summary["matched_taxon_key"] = species_match.get("usageKey")
        raw_payload = timed_step(
            steps,
            "occurrence_fetch_fixture_fallback",
            lambda: fixture_client.occurrence_search(
                taxon_key=matched_taxon_key(species_match),
                bbox=request.bbox,
                limit=request.max_records,
                use_fixture=True,
            ),
        )
        attach_payload_summary(base_summary, raw_payload)
        return species_match, raw_payload, base_summary


def resolve_species_match(client: GBIFClient, request: EvidenceRunRequest, *, use_fixture: bool = False) -> dict[str, Any]:
    if request.taxon_key:
        return client.species_by_key(request.taxon_key, taxon=request.taxon, use_fixture=use_fixture)
    return client.species_match(request.taxon, use_fixture=use_fixture)


def matched_taxon_key(species_match: dict[str, Any]) -> int:
    taxon_key = _int_or_none(species_match.get("usageKey"))
    if taxon_key:
        return taxon_key
    raise EvidenceRunError(
        status_code=422,
        detail={
            "error": "taxon_not_matched",
            "message": "GBIF did not return a usable taxonKey. Choose a taxon from the GBIF suggestions or refine the scientific name.",
            "gbif_species_match": species_match,
        },
    )


def timed_step(steps: list[dict[str, Any]], name: str, callback: Callable[[], T]) -> T:
    started = perf_counter()
    try:
        value = callback()
    except Exception as exc:
        steps.append(
            {
                "name": name,
                "status": "failed",
                "duration_ms": round((perf_counter() - started) * 1000, 2),
                "details": {"error": f"{type(exc).__name__}: {exc}"},
            }
        )
        raise
    steps.append({"name": name, "status": "completed", "duration_ms": round((perf_counter() - started) * 1000, 2)})
    return value


def attach_payload_summary(source_summary: dict[str, Any], raw_payload: dict[str, Any]) -> None:
    source_summary["gbif_result_count"] = raw_payload.get("count")
    source_summary["gbif_returned_records"] = len(raw_payload.get("results") or [])
    source_summary["gbif_limit"] = raw_payload.get("limit")
    source_summary["gbif_offset"] = raw_payload.get("offset")


def summarize_dataset_contributions(records: list[NormalizedOccurrence]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for record in records:
        row = grouped.setdefault(
            record.dataset_key,
            {
                "datasetKey": record.dataset_key,
                "datasetTitle": record.dataset_title,
                "publisher": record.publisher,
                "license": record.license,
                "record_count": 0,
                "issue_counter": Counter(),
            },
        )
        row["record_count"] += 1
        for issue in record.issues:
            row["issue_counter"][issue] += 1
        if not record.event_date and not record.year:
            row["issue_counter"]["MISSING_EVENT_DATE"] += 1
        if (record.coordinate_uncertainty_m or 0) > 10000:
            row["issue_counter"]["HIGH_COORDINATE_UNCERTAINTY"] += 1
    rows = []
    for row in grouped.values():
        issues = row.pop("issue_counter")
        row["main_issues"] = ", ".join(issue for issue, _ in issues.most_common(3)) or "none_detected"
        rows.append(row)
    return sorted(rows, key=lambda item: item["record_count"], reverse=True)


def build_claim_guardrails(
    records: list[NormalizedOccurrence],
    quality: dict[str, Any],
    grid: dict[str, Any],
    readiness: dict[str, Any],
) -> dict[str, list[str]]:
    supported = [
        "GBIF-mediated records matching the selected taxon and region are present in the evidence pack.",
        "Dataset provenance is preserved through datasetKey-level contribution summaries.",
    ]
    weak = [
        "Record clusters can indicate areas of observation activity, but they may also reflect observer effort.",
        f"The selected-purpose readiness score is {readiness['score']}/100 and should be interpreted with the component scores.",
    ]
    unsupported = [
        "Absence cannot be inferred from empty or low-evidence grid cells.",
        "Observed GBIF distribution must not be treated as the true species distribution.",
        "Population trend cannot be inferred without temporal sampling-bias correction.",
    ]
    required = [
        "Create a DOI-backed GBIF occurrence download or derived dataset before formal publication.",
        "Inspect high coordinate-uncertainty records before using them in fine-scale decisions.",
    ]
    if quality["missing_date_count"]:
        required.append("Review records missing eventDate/year before temporal claims.")
    if grid["meta"]["under_sampled_occupied_cells"]:
        required.append("Treat undersampled occupied cells as survey priorities, not confirmed absences.")
    if grid["meta"]["empty_cell_count"]:
        required.append("Treat empty grid cells as no-evidence cells, not absence evidence.")
    if not records:
        unsupported.append("No biodiversity claim is supported because no records were retained.")
    return {
        "supported_claims": supported,
        "weak_claims": weak,
        "unsupported_claims": unsupported,
        "required_verification": required,
    }


def build_citation_autopilot(
    request: EvidenceRunRequest,
    records: list[NormalizedOccurrence],
    dataset_contributions: list[dict[str, Any]],
    *,
    source_summary: dict[str, Any],
) -> dict[str, Any]:
    if source_summary["fallback_used"]:
        citation_status = "online_failed_fixture_fallback"
    elif source_summary["used_source_mode"] == "fixture":
        citation_status = "fixture_demo_not_for_publication"
    else:
        citation_status = "online_api_without_download_doi"
    methods = (
        f"Occurrence evidence for {request.taxon} in {request.region_name} was assembled from GBIF-mediated "
        f"occurrence-style records using bbox {request.bbox}. The workflow retained datasetKey provenance, "
        f"record counts per contributing dataset, coordinate uncertainty, event dates, licenses and GBIF issue flags. "
        f"The evidence readiness score was computed for purpose '{request.purpose}' from spatial, temporal, "
        "taxonomic, sampling and provenance components. Empty grid cells were treated as no-evidence cells rather than absences."
    )
    return {
        "citation_status": citation_status,
        "record_count": len(records),
        "dataset_count": len(dataset_contributions),
        "gbif_download_warning": (
            "This evidence pack does not include a GBIF download DOI. For publication, create and cite a DOI-backed "
            "GBIF occurrence download or derived dataset. Fixture or fallback packs are demo artifacts, not publication evidence."
        ),
        "derived_dataset_recipe": {
            "preserve_fields": ["datasetKey", "gbifID", "scientificName", "decimalLatitude", "decimalLongitude", "eventDate"],
            "group_by": "datasetKey",
            "include_counts": True,
        },
        "methods_text": methods,
    }


def build_publisher_feedback(records: list[NormalizedOccurrence]) -> list[dict[str, Any]]:
    issue_rows: dict[tuple[str, str], int] = defaultdict(int)
    for record in records:
        if not record.has_valid_coordinate:
            issue_rows[(record.dataset_key, "Missing or invalid coordinates")] += 1
        if (record.coordinate_uncertainty_m or 0) > 10000:
            issue_rows[(record.dataset_key, "High coordinate uncertainty")] += 1
        if not record.event_date and not record.year:
            issue_rows[(record.dataset_key, "Missing eventDate/year")] += 1
        if not record.accepted_taxon_key:
            issue_rows[(record.dataset_key, "Unresolved taxon match")] += 1
        if "COUNTRY_COORDINATE_MISMATCH" in record.issues:
            issue_rows[(record.dataset_key, "Country-coordinate mismatch")] += 1
    rows = []
    for (dataset_key, issue), count in issue_rows.items():
        rows.append(
            {
                "datasetKey": dataset_key,
                "main_issue": issue,
                "records_affected": count,
                "suggested_fix": _suggested_fix(issue),
            }
        )
    return sorted(rows, key=lambda item: (item["datasetKey"], item["main_issue"]))


def summarize_main_risks(
    quality: dict[str, Any],
    grid: dict[str, Any],
    citation: dict[str, Any],
    source_summary: dict[str, Any],
) -> list[str]:
    risks = []
    if quality["high_uncertainty_count"]:
        risks.append(f"{quality['high_uncertainty_count']} records have coordinate uncertainty above 10 km.")
    if quality["missing_date_count"]:
        risks.append(f"{quality['missing_date_count']} records are missing eventDate/year.")
    if grid["meta"]["under_sampled_occupied_cells"]:
        risks.append(f"{grid['meta']['under_sampled_occupied_cells']} occupied grid cells are under-sampled by the coverage proxy.")
    if grid["meta"]["empty_cell_count"]:
        risks.append(f"{grid['meta']['empty_cell_count']} grid cells have no retained records; they are no-evidence cells, not absences.")
    if citation["citation_status"] != "doi_backed":
        risks.append("No GBIF download DOI is attached to this evidence pack yet.")
    if source_summary["fallback_used"]:
        risks.append("GBIF online access failed and fixture fallback was used for this run.")
    if not risks:
        risks.append("No major quality risks were detected by the MVP rules.")
    return risks


def build_next_actions(
    quality: dict[str, Any],
    grid: dict[str, Any],
    citation: dict[str, Any],
    feedback: list[dict[str, Any]],
    source_summary: dict[str, Any],
) -> list[str]:
    actions = [
        "Preserve datasetKey and run.json with any downstream analysis.",
        "Avoid absence claims for empty or low-effort grid cells.",
    ]
    if citation["citation_status"] != "doi_backed":
        actions.insert(0, "Create a DOI-backed GBIF occurrence download or derived dataset before publication.")
    if source_summary["fallback_used"]:
        actions.append("Re-run in online GBIF mode before using this evidence pack outside the demo.")
    if quality["high_uncertainty_count"]:
        actions.append("Review records with coordinate uncertainty above 10 km.")
    if quality["missing_date_count"]:
        actions.append("Review records missing eventDate/year before temporal interpretation.")
    if grid["meta"]["survey_priority_cells"]:
        actions.append("Prioritize survey design around no-evidence and under-sampled grid cells.")
    if feedback:
        actions.append("Share the Publisher Feedback Pack with dataset managers for prioritized fixes.")
    return actions


def _suggested_fix(issue: str) -> str:
    return {
        "Missing or invalid coordinates": "Review georeferencing and coordinate fields.",
        "High coordinate uncertainty": "Improve georeferencing or flag coarse records for coarse-scale use only.",
        "Missing eventDate/year": "Add eventDate or at least year where available.",
        "Unresolved taxon match": "Review scientificName, taxonID and backbone mapping.",
        "Country-coordinate mismatch": "Check countryCode and coordinates for transposition or georeferencing errors.",
    }.get(issue, "Review source records and metadata.")


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
