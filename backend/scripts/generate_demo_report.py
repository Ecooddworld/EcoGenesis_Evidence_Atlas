from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.evidence.demo import DEMO_SCENARIOS
from app.evidence.pipeline import run_evidence_passport
from app.evidence.schemas import EvidenceRunRequest
from app.evidence.storage import artifact_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    os.environ.setdefault("EVIDENCE_DATA_DIR", str(repo_root / "data"))
    generated = []
    for scenario in [item for item in DEMO_SCENARIOS if item["id"] in {"invasive", "gaps", "quality"}]:
        pack = run_evidence_passport(EvidenceRunRequest(**scenario["form"]))
        output_dir = repo_root / "reports" / "demo-cases" / scenario["id"]
        copy_pack(pack, output_dir)
        generated.append(
            {
                "id": scenario["id"],
                "label": scenario["label"],
                "run_id": pack["run"]["run_id"],
                "output_dir": str(output_dir),
                "records_used": pack["passport"]["records_used"],
                "source_mode": pack["source_summary"]["used_source_mode"],
                "gbif_api_status": pack["source_summary"]["gbif_api_status"],
            }
        )
        if scenario["id"] == "invasive":
            copy_pack(pack, repo_root / "reports" / "demo")
    suite_dir = repo_root / "reports" / "demo-cases"
    suite_dir.mkdir(parents=True, exist_ok=True)
    (suite_dir / "README.md").write_text(_suite_readme(generated), encoding="utf-8")
    print(json.dumps({"demo_cases": generated}, indent=2))


def copy_pack(pack: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for export in pack["exports"]:
        shutil.copy2(artifact_path(pack["run"]["run_id"], export["name"]), output_dir / export["name"])
    (output_dir / "README.md").write_text(_case_readme(pack), encoding="utf-8")


def _case_readme(pack: dict) -> str:
    return (
        "# Demo Evidence Passport\n\n"
        f"Generated `{pack['source_summary']['used_source_mode']}` run: `{pack['run']['run_id']}`\n\n"
        f"Taxon: `{pack['passport']['taxon']}`. Region: `{pack['passport']['region_name']}`. "
        f"Purpose: `{pack['evidence_readiness']['purpose_label']}`.\n\n"
        f"GBIF API status: `{pack['source_summary']['gbif_api_status']}`. "
        f"Returned records: `{pack['source_summary'].get('gbif_returned_records')}`.\n\n"
        f"Submission readiness: `{pack['submission_readiness']['ready_count']}/{pack['submission_readiness']['total_count']}` checks ready.\n\n"
        "Open `passport.html` first, then inspect `decision_memo.md`, `publisher_issue_templates.md`, "
        "`submission_readiness.md`, `validation_summary.md`, `impact_brief.md`, `video_script.md` and the JSON/CSV/Markdown artifacts.\n"
    )


def _suite_readme(rows: list[dict]) -> str:
    lines = [
        "# EcoGenesis Demo Case Suite",
        "",
        "These three cases are the recommended GBIF Ebbe Nielsen Challenge demo suite.",
        "",
        "| Case | Run | Source | GBIF status | Records | Folder |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['label']} | `{row['run_id']}` | `{row['source_mode']}` | `{row['gbif_api_status']}` | {row['records_used']} | `{row['id']}/` |"
        )
    lines.extend(
        [
            "",
            "Use the case folders in the video and submission review. The root `reports/demo/` folder mirrors the invasive-watch case for backward compatibility.",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
