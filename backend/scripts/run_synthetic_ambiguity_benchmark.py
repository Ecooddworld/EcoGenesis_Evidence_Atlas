from __future__ import annotations

import argparse
import csv
from copy import deepcopy
import json
from pathlib import Path
import sys
from typing import Any

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import AMBIGUOUS_RECORD, GOOD_RECORD, MISSING_METADATA_RECORD, WEAK_RECORD, request_with_records
from app.barcode.schemas import BarcodeCompilerRequest


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "reports" / "synthetic-ambiguity-benchmark"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run EcoGenesis synthetic ambiguous benchmark.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--records", type=int, default=120)
    args = parser.parse_args()
    summary = run_benchmark(output_dir=Path(args.output_dir), record_count=args.records)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def run_benchmark(*, output_dir: Path, record_count: int = 120) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = synthetic_records(record_count)
    request = BarcodeCompilerRequest(**request_with_records("Synthetic ambiguous top-hit benchmark", records))
    pack = run_barcode_compiler(request)
    comparison_rows = naive_vs_ecogenesis_rows(pack)
    summary = benchmark_summary(pack, comparison_rows)

    write_csv(output_dir / "synthetic_ambiguous_dataset.csv", dataset_rows(pack))
    write_csv(output_dir / "naive_vs_ecogenesis.csv", comparison_rows)
    (output_dir / "benchmark_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "summary.md").write_text(summary_md(summary), encoding="utf-8")
    (output_dir / "evidence_pack.json").write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def synthetic_records(record_count: int) -> list[dict[str, Any]]:
    templates = [
        ("species-safe-control", GOOD_RECORD),
        ("ambiguous-near-tie", AMBIGUOUS_RECORD),
        ("weak-coverage", WEAK_RECORD),
        ("metadata-gap", MISSING_METADATA_RECORD),
    ]
    weights = [0.25, 0.45, 0.15, 0.15]
    counts = weighted_counts(record_count, weights)
    records = []
    for (case_name, template), count in zip(templates, counts, strict=True):
        for index in range(count):
            record = deepcopy(template)
            sequence_id = f"SYN-{case_name}-{index + 1:03d}"
            record["sequence_id"] = sequence_id
            metadata = dict(record.get("metadata") or {})
            if "occurrenceID" in metadata:
                metadata["occurrenceID"] = f"urn:ecogenesis:synthetic:{sequence_id}"
            metadata["benchmarkCase"] = case_name
            record["metadata"] = metadata
            records.append(record)
    return records


def weighted_counts(record_count: int, weights: list[float]) -> list[int]:
    counts = [int(record_count * weight) for weight in weights]
    while sum(counts) < record_count:
        counts[counts.index(max(counts))] += 1
    while sum(counts) > record_count:
        counts[counts.index(max(counts))] -= 1
    return counts


def dataset_rows(pack: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record in pack["records"]:
        top = record["top_hit"] or {}
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "benchmarkCase": record["metadata"].get("benchmarkCase"),
                "topTaxon": top.get("taxon"),
                "topIdentity": top.get("identity"),
                "topCoverage": top.get("query_coverage"),
                "compilerDecision": record["decision_class"],
                "candidateTaxon": record["candidate_taxon"]["name"],
                "candidateRank": record["candidate_taxon"]["rank"],
                "publishedTaxon": record["published_taxon"]["name"],
                "publishedRank": record["published_taxon"]["rank"],
                "blockers": "; ".join(record["blockers"]),
            }
        )
    return rows


def naive_vs_ecogenesis_rows(pack: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record in pack["records"]:
        top = record["top_hit"] or {}
        naive_claim = top.get("taxon") if top.get("rank") == "species" else ""
        unsafe_naive = bool(naive_claim and record["decision_class"] != "species-safe")
        rows.append(
            {
                "sequenceID": record["sequence_id"],
                "benchmarkCase": record["metadata"].get("benchmarkCase"),
                "naiveTopHitSpeciesClaim": naive_claim,
                "naiveWouldPublishSpecies": bool(naive_claim),
                "naiveUnsafeUnderEcoGenesisRules": unsafe_naive,
                "ecogenesisDecision": record["decision_class"],
                "ecogenesisPublishedTaxon": record["published_taxon"]["name"],
                "ecogenesisPublishedRank": record["published_taxon"]["rank"],
                "safeRank": record["safe_taxon"]["rank"],
                "primaryBlocker": record["blockers"][0] if record["blockers"] else "",
            }
        )
    return rows


def benchmark_summary(pack: dict[str, Any], comparison_rows: list[dict[str, Any]]) -> dict[str, Any]:
    naive_species = sum(1 for row in comparison_rows if row["naiveWouldPublishSpecies"])
    unsafe_naive = sum(1 for row in comparison_rows if row["naiveUnsafeUnderEcoGenesisRules"])
    eco_species = pack["metrics"]["species_safe_records"]
    safe_rank = pack["metrics"]["safe_rank_records"]
    hard_gate_failures = pack["metrics"]["hard_gate_failures"]
    return {
        "status": "pass" if hard_gate_failures == 0 and unsafe_naive > 0 else "review",
        "records": pack["metrics"]["processed_records"],
        "naive_species_claims": naive_species,
        "naive_unsafe_species_claims": unsafe_naive,
        "ecogenesis_species_safe_claims": eco_species,
        "ecogenesis_safe_rank_records": safe_rank,
        "hard_gate_failures": hard_gate_failures,
        "overclaim_prevention_rate": pack["metrics"]["overclaim_prevention_rate"],
        "unsafe_naive_fraction": round(unsafe_naive / naive_species, 6) if naive_species else 0,
        "main_result": (
            f"Naive top-hit would emit {naive_species} species claims; "
            f"{unsafe_naive} are blocked or downgraded by EcoGenesis hard gates."
        ),
    }


def summary_md(summary: dict[str, Any]) -> str:
    return f"""# Synthetic Ambiguous Benchmark

Цель benchmark: проверить не красивую презентацию, а защиту от главной ошибки `top hit = species`.

## Result

- Status: `{summary['status']}`
- Records processed: {summary['records']}
- Naive top-hit species claims: {summary['naive_species_claims']}
- Unsafe naive species claims under EcoGenesis rules: {summary['naive_unsafe_species_claims']}
- EcoGenesis species-safe claims: {summary['ecogenesis_species_safe_claims']}
- EcoGenesis safe-rank records: {summary['ecogenesis_safe_rank_records']}
- Hard-gate failures: {summary['hard_gate_failures']}
- Overclaim prevention rate: {summary['overclaim_prevention_rate']}

## Conclusion

{summary['main_result']}

EcoGenesis не пытается угадать вид по лучшему hit. Если ambiguity/LCA, barcode gap, diagnostic k-mers или metadata gates не проходят, species-level publication claim блокируется, понижается до safe rank или отправляется в repair/review queue.
"""


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
