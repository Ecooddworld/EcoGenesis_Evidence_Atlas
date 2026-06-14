from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any
import zipfile


def barcode_data_dir() -> Path:
    path = Path(os.getenv("EVIDENCE_DATA_DIR", "./data")).resolve() / "barcode-runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def barcode_run_dir(run_id: str) -> Path:
    path = barcode_data_dir() / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


ArtifactContent = str | bytes


def save_barcode_artifacts(run_id: str, artifacts: dict[str, ArtifactContent]) -> list[dict[str, Any]]:
    directory = barcode_run_dir(run_id)
    exports = []
    for name, content in artifacts.items():
        path = directory / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        exports.append(
            {
                "name": name,
                "url": f"/api/barcode/runs/{run_id}/exports/{name}",
                "size_bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return sorted(exports, key=lambda item: item["name"])


def save_barcode_zip_artifact(run_id: str, artifacts: dict[str, ArtifactContent], *, name: str = "evidence_pack.zip") -> dict[str, Any]:
    directory = barcode_run_dir(run_id)
    path = directory / name
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact_name, content in sorted(artifacts.items()):
            archive.writestr(artifact_name, content)
    path.write_bytes(buffer.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "name": name,
        "url": f"/api/barcode/runs/{run_id}/exports/{name}",
        "size_bytes": path.stat().st_size,
        "sha256": digest,
    }


def barcode_artifact_path(run_id: str, name: str) -> Path:
    return barcode_data_dir() / run_id / Path(name).name


def load_barcode_pack(run_id: str) -> dict[str, Any]:
    path = barcode_artifact_path(run_id, "evidence_pack.json")
    if not path.exists():
        raise FileNotFoundError(run_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_barcode_summaries(limit: int = 20) -> list[dict[str, Any]]:
    summaries = []
    for directory in barcode_data_dir().iterdir():
        pack_path = directory / "evidence_pack.json"
        if not pack_path.exists():
            continue
        try:
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        summaries.append(
            {
                "run_id": pack.get("run", {}).get("run_id") or directory.name,
                "project_title": pack.get("summary", {}).get("project_title"),
                "marker": pack.get("summary", {}).get("marker"),
                "processed_records": pack.get("summary", {}).get("processed_records"),
                "species_safe_records": pack.get("summary", {}).get("species_safe_records"),
                "finished_at": pack.get("run", {}).get("finished_at"),
            }
        )
    return sorted(summaries, key=lambda item: item.get("finished_at") or "", reverse=True)[:limit]
