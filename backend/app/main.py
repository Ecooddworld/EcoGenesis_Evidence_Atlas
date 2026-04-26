from __future__ import annotations

import mimetypes
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response

from .evidence.demo import DEMO_SCENARIOS
from .evidence.pipeline import EvidenceRunError, run_evidence_passport
from .evidence.schemas import EvidenceRunCreated, EvidenceRunRequest
from .evidence.storage import artifact_path, list_run_summaries, load_pack


app = FastAPI(
    title="EcoGenesis Evidence Atlas API",
    version="0.1.0",
    description="GBIF Evidence Passport API for reproducible, citation-aware biodiversity evidence packs.",
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
    return {"status": "ok", "service": "ecogenesis-evidence-atlas"}


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


@app.get("/api/evidence/runs")
def list_runs() -> list[dict]:
    return list_run_summaries()


@app.get("/api/evidence/runs/{run_id}")
def get_run(run_id: str) -> dict:
    try:
        return load_pack(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc


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


@app.get("/api/evidence/runs/{run_id}/claims")
def get_claims(run_id: str) -> dict:
    pack = get_run(run_id)
    return pack["claim_guardrails"]


@app.get("/api/evidence/runs/{run_id}/publisher-feedback")
def get_publisher_feedback(run_id: str) -> list[dict]:
    pack = get_run(run_id)
    return pack["publisher_feedback"]


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
