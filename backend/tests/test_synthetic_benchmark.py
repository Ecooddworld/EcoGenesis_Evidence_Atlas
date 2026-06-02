from __future__ import annotations

from scripts.run_synthetic_ambiguity_benchmark import run_benchmark


def test_synthetic_ambiguity_benchmark_outputs_comparison(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path / "runs"))

    summary = run_benchmark(output_dir=tmp_path / "benchmark", record_count=40)

    assert summary["records"] == 40
    assert summary["hard_gate_failures"] == 0
    assert summary["naive_species_claims"] == 40
    assert summary["naive_unsafe_species_claims"] > 0
    assert summary["ecogenesis_species_safe_claims"] < summary["naive_species_claims"]
    assert (tmp_path / "benchmark" / "naive_vs_ecogenesis.csv").exists()
    assert (tmp_path / "benchmark" / "summary.md").exists()
