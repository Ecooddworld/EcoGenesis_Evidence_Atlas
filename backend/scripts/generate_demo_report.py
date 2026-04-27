from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evidence.pipeline import run_evidence_passport
from app.evidence.schemas import EvidenceRunRequest
from app.evidence.storage import artifact_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("EVIDENCE_DATA_DIR", str(repo_root / "data"))
    request = EvidenceRunRequest(
        taxon="Aedes albopictus",
        taxon_key=1651430,
        region_name="Spain live GBIF bbox",
        bbox=[-10.0, 35.0, 4.5, 44.5],
        purpose="invasive_watch",
        source_mode="online_with_empty_fallback",
        use_fixture=False,
        max_records=300,
    )
    pack = run_evidence_passport(request)
    output_dir = repo_root / "reports" / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)
    for export in pack["exports"]:
        shutil.copy2(artifact_path(pack["run"]["run_id"], export["name"]), output_dir / export["name"])
    (output_dir / "README.md").write_text(
        "# Demo Evidence Passport\n\n"
        f"Generated `{pack['source_summary']['used_source_mode']}` run: `{pack['run']['run_id']}`\n\n"
        f"GBIF API status: `{pack['source_summary']['gbif_api_status']}`. "
        f"Returned records: `{pack['source_summary'].get('gbif_returned_records')}`.\n\n"
        "Open `passport.html` or inspect the JSON/CSV/Markdown artifacts.\n",
        encoding="utf-8",
    )
    print(json.dumps({"run_id": pack["run"]["run_id"], "output_dir": str(output_dir)}, indent=2))


if __name__ == "__main__":
    main()
