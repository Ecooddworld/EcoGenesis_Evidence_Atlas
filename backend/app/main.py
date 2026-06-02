from __future__ import annotations

import mimetypes
import os

import requests
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response

from .barcode.compiler import run_barcode_compiler
from .barcode.csv_import import CSV_TEMPLATE_TEXT, parse_barcode_csv
from .barcode.demo import BARCODE_DEMO_SCENARIOS, DEFAULT_BARCODE_REQUEST
from .barcode.schemas import BarcodeCompilerCreated, BarcodeCompilerRequest, BarcodeReferenceSearchRequest
from .barcode.search_backend import compiler_request_from_search, list_reference_datasets, search_reference, search_status
from .barcode.storage import barcode_artifact_path, list_barcode_summaries, load_barcode_pack
from .evidence.demo import DEMO_SCENARIOS, REGION_PRESETS
from .evidence.gbif import GBIFClient
from .evidence.pipeline import EvidenceRunError, run_evidence_passport
from .evidence.schemas import EvidenceRunCreated, EvidenceRunRequest
from .evidence.storage import artifact_path, list_run_summaries, load_pack


app = FastAPI(
    title="EcoGenesis Barcode-to-GBIF Evidence Compiler API",
    version="0.2.0",
    description="Deterministic barcode/metabarcoding compiler plus legacy GBIF Evidence Passport API.",
)

origins = [item.strip() for item in os.getenv("CORS_ALLOW_ORIGINS", "*").split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "ecogenesis-barcode-gbif-compiler"}


@app.get("/api/barcode/demo-scenarios")
def barcode_demo_scenarios() -> list[dict]:
    return BARCODE_DEMO_SCENARIOS


@app.get("/api/barcode/default-request")
def barcode_default_request() -> dict:
    return DEFAULT_BARCODE_REQUEST


@app.get("/api/barcode/reference-status")
def barcode_reference_status() -> dict:
    return {
        "status": "ready",
        "message": "Compiler is using deterministic local gates over supplied Sequence ID or reference-hit results.",
        "official_links": {
            "gbif_sequence_id": "https://www.gbif.org/tools/sequence-id",
            "dna_derived_guide": "https://docs.gbif.org/publishing-dna-derived-data/en/",
            "occurrence_quality_requirements": "https://www.gbif.org/data-quality-requirements-occurrences",
            "challenge_rules": "https://www.gbif.org/awards/ebbe-2026-rules",
        },
        "match_gates": {
            "exact": "identity >= 99% and queryCoverage >= 80%",
            "close": "90% < identity < 99% and queryCoverage >= 80%",
            "weak": "identity < 90% or queryCoverage < 80%",
        },
    }


@app.get("/api/barcode/search-status")
def barcode_search_status() -> dict:
    return search_status()


@app.get("/api/barcode/reference-datasets")
def barcode_reference_datasets() -> list[dict]:
    return list_reference_datasets()


@app.post("/api/barcode/search")
def barcode_reference_search(request: BarcodeReferenceSearchRequest) -> dict:
    try:
        search_result = search_reference(
            sequence=request.sequence,
            sequence_id=request.sequence_id,
            reference_dataset=request.reference_dataset,
            backend=request.backend,
            max_hits=request.max_hits,
        )
        compiler_request = compiler_request_from_search(
            search_result,
            sequence=request.sequence,
            sequence_id=request.sequence_id,
            project_title=request.project_title,
            metadata=request.metadata,
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    payload: dict = {
        "search": search_result,
        "request": compiler_request.model_dump(),
    }
    if request.compile:
        pack = run_barcode_compiler(compiler_request)
        payload["run"] = {
            "run_id": pack["run"]["run_id"],
            "status": "completed",
            "summary": pack["summary"],
            "exports": pack["exports"],
        }
        payload["pack"] = pack
    return payload


@app.get("/api/barcode/csv-template")
def barcode_csv_template() -> Response:
    return Response(
        content=CSV_TEMPLATE_TEXT,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="barcode_compiler_template.csv"'},
    )


@app.post("/api/barcode/import-csv")
async def import_barcode_csv(
    file: UploadFile = File(...),
    project_title: str | None = Form(default=None),
    marker: str | None = Form(default=None),
    reference_database: str | None = Form(default=None),
    method_or_sop: str | None = Form(default=None),
) -> dict:
    text = await read_uploaded_csv(file)
    return parse_barcode_csv(
        text,
        project_title=project_title,
        marker=marker,
        reference_database=reference_database,
        method_or_sop=method_or_sop,
    )


@app.post("/api/barcode/run-csv", response_model=BarcodeCompilerCreated)
async def run_barcode_csv(
    file: UploadFile = File(...),
    project_title: str | None = Form(default=None),
    marker: str | None = Form(default=None),
    reference_database: str | None = Form(default=None),
    method_or_sop: str | None = Form(default=None),
) -> dict:
    text = await read_uploaded_csv(file)
    parsed = parse_barcode_csv(
        text,
        project_title=project_title,
        marker=marker,
        reference_database=reference_database,
        method_or_sop=method_or_sop,
    )
    if not parsed["validation"]["ok"] or not parsed["request"]:
        raise HTTPException(status_code=422, detail=parsed["validation"])
    pack = run_barcode_compiler(BarcodeCompilerRequest(**parsed["request"]))
    return {
        "run_id": pack["run"]["run_id"],
        "status": "completed",
        "summary": pack["summary"],
        "exports": pack["exports"],
    }


@app.post("/api/barcode/run", response_model=BarcodeCompilerCreated)
def run_barcode(request: BarcodeCompilerRequest) -> dict:
    pack = run_barcode_compiler(request)
    return {
        "run_id": pack["run"]["run_id"],
        "status": "completed",
        "summary": pack["summary"],
        "exports": pack["exports"],
    }


async def read_uploaded_csv(file: UploadFile) -> str:
    content = await file.read()
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded.") from exc


@app.get("/api/barcode/runs")
def list_barcode_runs() -> list[dict]:
    return list_barcode_summaries()


@app.get("/api/barcode/runs/{run_id}")
def get_barcode_run(run_id: str) -> dict:
    try:
        return load_barcode_pack(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="barcode run not found") from exc


@app.get("/api/barcode/runs/{run_id}/report", response_class=HTMLResponse)
def get_barcode_report(run_id: str) -> HTMLResponse:
    path = barcode_artifact_path(run_id, "molecular_evidence_report.html")
    if not path.exists():
        raise HTTPException(status_code=404, detail="barcode report not found")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@app.get("/api/barcode/runs/{run_id}/exports")
def get_barcode_exports(run_id: str) -> list[dict]:
    return get_barcode_run(run_id)["exports"]


@app.get("/api/barcode/runs/{run_id}/exports/{artifact_name}")
def download_barcode_export(run_id: str, artifact_name: str) -> FileResponse:
    path = barcode_artifact_path(run_id, artifact_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found")
    return FileResponse(path, filename=path.name)


@app.head("/api/barcode/runs/{run_id}/exports/{artifact_name}")
def head_barcode_export(run_id: str, artifact_name: str) -> Response:
    path = barcode_artifact_path(run_id, artifact_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found")
    media_type, _ = mimetypes.guess_type(path.name)
    return Response(
        status_code=200,
        media_type=media_type or "application/octet-stream",
        headers={
            "Content-Length": str(path.stat().st_size),
            "Content-Disposition": f'attachment; filename="{path.name}"',
        },
    )


@app.post("/api/evidence/run", response_model=EvidenceRunCreated)
def run_evidence(request: EvidenceRunRequest) -> dict:
    try:
        pack = run_evidence_passport(request)
    except EvidenceRunError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return {
        "run_id": pack["run"]["run_id"],
        "status": "completed",
        "passport": pack["passport"] | {"readiness": pack["evidence_readiness"]},
        "exports": pack["exports"],
    }


@app.get("/api/evidence/demo-scenarios")
def demo_scenarios() -> list[dict]:
    return DEMO_SCENARIOS


@app.get("/api/evidence/region-presets")
def region_presets() -> list[dict]:
    return REGION_PRESETS


@app.get("/api/evidence/gbif-status")
def gbif_status() -> dict:
    client = GBIFClient(mode="online")
    try:
        results = client.species_suggest("Aedes", limit=1)
    except requests.RequestException as exc:
        return {
            "status": "unavailable",
            "base_url": client.base_url,
            "message": f"GBIF API is unavailable: {type(exc).__name__}. Live runs will use an empty no-evidence fallback.",
        }
    return {
        "status": "ok" if results else "degraded",
        "base_url": client.base_url,
        "message": "GBIF API reachable. Live occurrence runs use GBIF-mediated records.",
    }


@app.get("/api/evidence/taxon-suggest")
def taxon_suggest(q: str = Query(default="", max_length=120), limit: int = Query(default=10, ge=1, le=20)) -> dict:
    client = GBIFClient(mode="online")
    try:
        results = client.species_suggest(q, limit=limit)
        return {"query": q, "source": "gbif_api" if len(q.strip()) >= 2 else "curated_defaults", "warnings": [], "results": results}
    except requests.RequestException as exc:
        fallback = GBIFClient(mode="fixture").species_suggest(q, limit=limit, use_fixture=True)
        return {
            "query": q,
            "source": "fixture_fallback",
            "warnings": [f"GBIF species suggest failed: {type(exc).__name__}: {exc}"],
            "results": fallback,
        }


@app.get("/api/evidence/runs")
def list_runs() -> list[dict]:
    return list_run_summaries()


@app.get("/api/evidence/runs/{run_id}")
def get_run(run_id: str) -> dict:
    try:
        return load_pack(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc


@app.get("/api/evidence/runs/{run_id}/overview")
def get_overview(run_id: str) -> dict:
    pack = get_run(run_id)
    return {
        "passport": pack["passport"],
        "evidence_readiness": pack["evidence_readiness"],
        "main_risks": pack["main_risks"],
        "next_actions": pack["next_actions"],
        "source_summary": pack["source_summary"],
        "top_survey_priority_cells": pack["grid_metrics"]["meta"].get("top_survey_priority_cells", []),
    }


@app.get("/api/evidence/runs/{run_id}/passport", response_class=HTMLResponse)
def get_passport(run_id: str) -> HTMLResponse:
    path = artifact_path(run_id, "passport.html")
    if not path.exists():
        raise HTTPException(status_code=404, detail="passport not found")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@app.get("/api/evidence/runs/{run_id}/map")
def get_map(run_id: str) -> dict:
    pack = get_run(run_id)
    return pack["records_geojson"]


@app.get("/api/evidence/runs/{run_id}/map-layers")
def get_map_layers(run_id: str) -> dict:
    pack = get_run(run_id)
    return {"records": pack["records_geojson"], "grid": pack["grid_metrics"]}


@app.get("/api/evidence/runs/{run_id}/quality")
def get_quality(run_id: str) -> dict:
    pack = get_run(run_id)
    return {
        "quality_metrics": pack["quality_metrics"],
        "normalized_records": pack["normalized_records"],
        "grid_metrics": pack["grid_metrics"],
    }


@app.get("/api/evidence/runs/{run_id}/sampling-gaps")
def get_sampling_gaps(run_id: str) -> dict:
    pack = get_run(run_id)
    priority_cells = [
        feature
        for feature in pack["grid_metrics"]["features"]
        if feature["properties"].get("survey_priority")
    ]
    return {
        "meta": pack["grid_metrics"]["meta"],
        "priority_cells": sorted(priority_cells, key=lambda item: item["properties"]["gap_priority_score"], reverse=True),
    }


@app.get("/api/evidence/runs/{run_id}/claims")
def get_claims(run_id: str) -> dict:
    pack = get_run(run_id)
    return pack["claim_guardrails"]


@app.get("/api/evidence/runs/{run_id}/publisher-feedback")
def get_publisher_feedback(run_id: str) -> list[dict]:
    pack = get_run(run_id)
    return pack["publisher_feedback"]


@app.get("/api/evidence/runs/{run_id}/graph-memory")
def get_graph_memory(run_id: str) -> dict:
    pack = get_run(run_id)
    return pack["graph_memory"]["graph"]


@app.get("/api/evidence/runs/{run_id}/submission-readiness")
def get_submission_readiness(run_id: str) -> dict:
    pack = get_run(run_id)
    return {
        "decision_memo": pack["decision_memo"],
        "validation_summary": pack["validation_summary"],
        "submission_readiness": pack["submission_readiness"],
    }


@app.get("/api/evidence/runs/{run_id}/citations")
def get_citations(run_id: str) -> dict:
    pack = get_run(run_id)
    return {
        "citation_autopilot": pack["citation_autopilot"],
        "dataset_contributions": pack["dataset_contributions"],
        "source_summary": pack["source_summary"],
    }


@app.get("/api/evidence/runs/{run_id}/exports")
def get_exports(run_id: str) -> list[dict]:
    pack = get_run(run_id)
    return pack["exports"]


@app.get("/api/evidence/runs/{run_id}/exports/{artifact_name}")
def download_export(run_id: str, artifact_name: str) -> FileResponse:
    path = artifact_path(run_id, artifact_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found")
    return FileResponse(path, filename=path.name)


@app.head("/api/evidence/runs/{run_id}/exports/{artifact_name}")
def head_export(run_id: str, artifact_name: str) -> Response:
    path = artifact_path(run_id, artifact_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="artifact not found")
    media_type, _ = mimetypes.guess_type(path.name)
    return Response(
        status_code=200,
        media_type=media_type or "application/octet-stream",
        headers={
            "Content-Length": str(path.stat().st_size),
            "Content-Disposition": f'attachment; filename="{path.name}"',
        },
    )
