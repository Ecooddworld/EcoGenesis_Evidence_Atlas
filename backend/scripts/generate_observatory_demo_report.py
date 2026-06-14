from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
import sys
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.observatory.pipeline import run_observatory_demo
from app.observatory.schemas import ObservatoryRunRequest
from app.observatory.storage import observatory_artifact_path


REPORT_DIR = REPO_ROOT / "reports" / "observatory-demo"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in REPORT_DIR.iterdir():
        if path.is_file():
            path.unlink()
    pack = run_observatory_demo(ObservatoryRunRequest(mode="offline_demo", force_fixture=True, limit=50))
    run_id = pack["run"]["run_id"]
    copied = []
    for export in pack["exports"]:
        source = observatory_artifact_path(run_id, export["name"])
        destination = REPORT_DIR / export["name"]
        shutil.copy2(source, destination)
        copied.append(
            {
                "name": export["name"],
                "sha256": export.get("sha256"),
                "size_bytes": export.get("size_bytes"),
            }
        )

    write_manifest(REPORT_DIR / "observatory_demo_manifest.csv", copied)
    (REPORT_DIR / "README.md").write_text(readme(pack), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "pass",
                "run_id": run_id,
                "report_dir": str(REPORT_DIR),
                "exports": len(copied),
                "hard_gate_status": pack["summary"]["hard_gate_status"],
                "vsea_rows": pack["summary"]["vsea_rows"],
            },
            indent=2,
        )
    )


def write_manifest(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "sha256", "size_bytes"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def readme(pack: dict[str, Any]) -> str:
    summary = pack["summary"]
    return f"""# GSIG Observatory Demo Report

Generated from the repository code with:

```bash
cd backend
.venv/bin/python scripts/generate_observatory_demo_report.py
```

Run ID: `{pack['run']['run_id']}`

## Result

- Hard gate status: `{summary['hard_gate_status']}`
- GBIF source mode: `{summary['source_mode']}`
- Occurrence context rows: `{summary['normalized_occurrence_records']}`
- VSEA rows: `{summary['vsea_rows']}`
- Segments: `{summary['segments']}`
- Graph: `{summary['graph_nodes']}` nodes, `{summary['graph_edges']}` edges
- Claim states: `{json.dumps(summary['claim_states'], sort_keys=True)}`

## Contest Boundary

This report uses the Observatory layer as a source-backed explanation and audit shell. GBIF occurrence rows are hashed context only. Molecular claim states are produced by the barcode/GSEG gates, and the UI/export layer cannot upgrade them.

Key files:

- `observatory_evidence_pack.zip`
- `observatory_report.md`
- `snapshot_manifest.json`
- `source_registry_audit.json`
- `observatory_vsea.parquet`
- `observatory_graph.jsonld`
- `gbif_export_preview.csv`
- `ai_ready_dataset.jsonl`
- `proof_summary.json`
"""


if __name__ == "__main__":
    main()
