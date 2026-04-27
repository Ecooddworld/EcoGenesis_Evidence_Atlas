from __future__ import annotations

import os
from pathlib import Path
from typing import Any
import json
import zipfile
import io
import hashlib


def data_dir() -> Path:
    path = Path(os.getenv("EVIDENCE_DATA_DIR", "./data")).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def run_dir(run_id: str) -> Path:
    path = data_dir() / "runs" / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_artifacts(run_id: str, artifacts: dict[str, str]) -> list[dict[str, Any]]:
    directory = run_dir(run_id)
    exports = []
    for name, content in artifacts.items():
        path = directory / name
        path.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        exports.append(
            {
                "name": name,
                "url": f"/api/evidence/runs/{run_id}/exports/{name}",
                "size_bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return sorted(exports, key=lambda item: item["name"])


def save_zip_artifact(run_id: str, artifacts: dict[str, str], *, name: str = "evidence_pack.zip") -> dict[str, Any]:
    directory = run_dir(run_id)
    path = directory / name
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact_name, content in sorted(artifacts.items()):
            archive.writestr(artifact_name, content)
    path.write_bytes(buffer.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "name": name,
        "url": f"/api/evidence/runs/{run_id}/exports/{name}",
        "size_bytes": path.stat().st_size,
        "sha256": digest,
    }


def artifact_path(run_id: str, name: str) -> Path:
    safe_name = Path(name).name
    return data_dir() / "runs" / run_id / safe_name


def load_pack(run_id: str) -> dict[str, Any]:
    path = artifact_path(run_id, "evidence_pack.json")
    if not path.exists():
        raise FileNotFoundError(run_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_run_summaries(limit: int = 20) -> list[dict[str, Any]]:
    directory = data_dir() / "runs"
    if not directory.exists():
        return []
    summaries = []
    for path in directory.iterdir():
        pack_path = path / "evidence_pack.json"
        if not pack_path.exists():
            continue
        try:
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        summaries.append(
            {
                "run_id": pack.get("run", {}).get("run_id") or path.name,
                "taxon": pack.get("passport", {}).get("taxon"),
                "region_name": pack.get("passport", {}).get("region_name"),
                "purpose": pack.get("evidence_readiness", {}).get("purpose_label"),
                "score": pack.get("evidence_readiness", {}).get("score"),
                "finished_at": pack.get("run", {}).get("finished_at"),
                "source_mode": pack.get("source_summary", {}).get("used_source_mode")
                or pack.get("run", {}).get("source_mode"),
                "fallback_used": pack.get("source_summary", {}).get("fallback_used", False),
            }
        )
    return sorted(summaries, key=lambda item: item.get("finished_at") or "", reverse=True)[:limit]
