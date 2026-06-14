from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any
import zipfile


ArtifactContent = str | bytes


def observatory_data_dir() -> Path:
    path = Path(os.getenv("EVIDENCE_DATA_DIR", "./data")).resolve() / "observatory-runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def observatory_run_dir(run_id: str) -> Path:
    path = observatory_data_dir() / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_observatory_artifacts(run_id: str, artifacts: dict[str, ArtifactContent]) -> list[dict[str, Any]]:
    directory = observatory_run_dir(run_id)
    exports = []
    for name, content in artifacts.items():
        path = directory / Path(name).name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        exports.append(
            {
                "name": path.name,
                "url": f"/api/observatory/runs/{run_id}/exports/{path.name}",
                "size_bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return sorted(exports, key=lambda item: item["name"])


def save_observatory_zip_artifact(
    run_id: str,
    artifacts: dict[str, ArtifactContent],
    *,
    name: str = "observatory_evidence_pack.zip",
) -> dict[str, Any]:
    directory = observatory_run_dir(run_id)
    path = directory / name
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for artifact_name, content in sorted(artifacts.items()):
            archive.writestr(artifact_name, content)
    path.write_bytes(buffer.getvalue())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "name": name,
        "url": f"/api/observatory/runs/{run_id}/exports/{name}",
        "size_bytes": path.stat().st_size,
        "sha256": digest,
    }


def observatory_artifact_path(run_id: str, name: str) -> Path:
    return observatory_data_dir() / run_id / Path(name).name


def load_observatory_pack(run_id: str) -> dict[str, Any]:
    path = observatory_artifact_path(run_id, "observatory_evidence_pack.json")
    if not path.exists():
        raise FileNotFoundError(run_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_observatory_summaries(limit: int = 20) -> list[dict[str, Any]]:
    summaries = []
    for directory in observatory_data_dir().iterdir():
        pack_path = directory / "observatory_evidence_pack.json"
        if not pack_path.exists():
            continue
        try:
            pack = json.loads(pack_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        summaries.append(
            {
                "run_id": pack.get("run", {}).get("run_id") or directory.name,
                "mode": pack.get("run", {}).get("mode"),
                "taxon": pack.get("request", {}).get("taxon"),
                "snapshot_id": pack.get("snapshot_manifest", {}).get("snapshot_id"),
                "records": pack.get("summary", {}).get("normalized_occurrence_records"),
                "segments": pack.get("summary", {}).get("segments"),
                "hard_gate_status": pack.get("proof_summary", {}).get("hard_gate_status"),
                "finished_at": pack.get("run", {}).get("finished_at"),
            }
        )
    return sorted(summaries, key=lambda item: item.get("finished_at") or "", reverse=True)[:limit]


def observatory_export_manifest(run_id: str) -> list[dict[str, Any]]:
    directory = observatory_run_dir(run_id)
    exports = []
    for path in sorted(item for item in directory.iterdir() if item.is_file()):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        exports.append(
            {
                "name": path.name,
                "url": f"/api/observatory/runs/{run_id}/exports/{path.name}",
                "size_bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return exports


def latest_observatory_run_id() -> str | None:
    summaries = list_observatory_summaries(limit=1)
    if not summaries:
        return None
    return str(summaries[0]["run_id"])
