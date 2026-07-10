import csv
import io
import json

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import BASE_SEQUENCE, base_metadata, request_with_records
from app.barcode.schemas import BarcodeCompilerRequest
from app.gseg.artifacts import build_gseg_gsig_artifacts, recompute_safe_taxon_lca
from app.gseg.reference_checks import (
    GateVector,
    Hit,
    MarkerProfile,
    Taxonomy,
    ai_output_allowed,
    assert_no_species_safe_hard_gate_violation,
    barcode_gap_pass,
    benjamini_hochberg,
    canonical_segment,
    graph_provenance_complete,
    preserve_claim_states_for_ai_export,
    rci2_score,
    reverse_complement,
    safe_taxon,
    segment_hash,
    sharedness,
    species_specific_allowed,
    specificity,
    taxonomic_entropy,
    transition_allowed,
    evidence_claim_valid,
)


def taxonomy() -> Taxonomy:
    return Taxonomy(
        parent={
            "Aedes albopictus": "Aedes",
            "Aedes aegypti": "Aedes",
            "Aedes": "Culicidae",
            "Culicidae": None,
        },
        rank={
            "Aedes albopictus": "species",
            "Aedes aegypti": "species",
            "Aedes": "genus",
            "Culicidae": "family",
        },
    )


def test_lca_downgrades_close_competitor_to_genus() -> None:
    profile = MarkerProfile("COI", identity_min=0.99, coverage_min=0.8, min_aligned_length=500)
    hits = [
        Hit("h1", "Aedes albopictus", 0.994, 0.96, 658),
        Hit("h2", "Aedes aegypti", 0.993, 0.96, 658),
    ]
    assert safe_taxon(hits, taxonomy(), profile) == "Aedes"


def test_species_safe_requires_all_hard_gates() -> None:
    gates = GateVector(True, True, True, False, True, True, True)
    assert not gates.species_hard_pass


def test_barcode_gap_and_rci2_bounds() -> None:
    ok, gap = barcode_gap_pass(0.009, 0.018)
    assert ok
    assert round(gap, 3) == 0.009
    assert 0.999 <= rci2_score(1, 1, 1, 1, 1) <= 1.001
    assert rci2_score(1, 0, 1, 1, 1) < 0.1


def test_metadata_does_not_strengthen_taxon_proof_obligation() -> None:
    rows = [
        {
            "id": "x",
            "decision_class": "species-safe",
            "exact": True,
            "ambiguity_lca": True,
            "barcode_gap": True,
            "diagnostic_kmer": True,
            "marker_profile": True,
            "assay": True,
            "rci2": True,
        }
    ]
    assert_no_species_safe_hard_gate_violation(rows)


def test_canonicalization_is_deterministic_and_reverse_complement_aware() -> None:
    a = canonical_segment(" acgtn ", strand_policy="canonical_min")
    b = canonical_segment(reverse_complement("ACGTN"), strand_policy="canonical_min")
    assert a == b
    assert a == "ACGTN"


def test_segment_hash_depends_on_coordinates_and_ruleset() -> None:
    h1 = segment_hash("ACGTACGT", 0, 8, "gsig-v1")
    h2 = segment_hash("ACGTACGT", 1, 8, "gsig-v1")
    h3 = segment_hash("ACGTACGT", 0, 8, "gsig-v2")
    assert h1 != h2
    assert h1 != h3


def test_shared_segment_cannot_be_species_specific() -> None:
    probs = {"species_A": 0.52, "species_B": 0.48}
    assert sharedness(probs) == 2
    assert not species_specific_allowed(probs)


def test_taxonomic_entropy_high_for_shared_distribution() -> None:
    shared = {"A": 0.5, "B": 0.5}
    specific = {"A": 0.99, "B": 0.01}
    assert taxonomic_entropy(shared) > taxonomic_entropy(specific)
    assert specificity(specific) > specificity(shared)


def test_claim_state_transitions_and_evidence_sources() -> None:
    assert not transition_allowed("raw", "function_hypothesis")
    assert transition_allowed("raw", "normalized")
    good = {
        "claim_id": "c1",
        "claim_type": "function",
        "claim_state": "experimentally_supported",
        "evidence_type": "direct_experiment",
        "source_id": "doi:example",
        "provenance_hash": "abc",
    }
    bad = dict(good, evidence_type="computational_prediction")
    assert evidence_claim_valid(good)
    assert not evidence_claim_valid(bad)


def test_ai_output_and_graph_provenance_guardrails() -> None:
    assert not ai_output_allowed({"source": "ai_only", "writes_verified_graph_fact": True})
    assert not ai_output_allowed({"source": "ai_only", "claim_state": "experimentally_supported"})
    assert ai_output_allowed({"source": "ai_only", "claim_state": "function_hypothesis"})
    assert graph_provenance_complete([{"id": "n1", "provenance_hash": "h1"}], [{"id": "e1", "provenance_hash": "h2"}])
    assert not graph_provenance_complete([{"id": "n1", "provenance_hash": "h1"}], [{"id": "e2"}])


def test_ai_export_preserves_claim_states_and_bh_fdr() -> None:
    rows = [{"claim_state": "function_hypothesis", "ai_label": "hypothesis"}]
    bad = [{"claim_state": "function_hypothesis", "ai_label": "fact"}]
    assert preserve_claim_states_for_ai_export(rows)
    assert not preserve_claim_states_for_ai_export(bad)
    assert benjamini_hochberg([0.001, 0.02, 0.20], alpha=0.05) == [True, True, False]


def test_gseg_artifacts_handle_no_match_records(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    metadata = base_metadata("NOHIT-001")
    metadata.update({"identity": 0, "queryCoverage": 0})
    request = BarcodeCompilerRequest(
        **request_with_records(
            "No-match GSEG artifact regression",
            [{"sequence_id": "NOHIT-001", "sequence": BASE_SEQUENCE, "metadata": metadata, "hits": []}],
        )
    )
    pack = run_barcode_compiler(request)

    assert pack["records"][0]["top_hit"] is None
    assert pack["records"][0]["decision_class"] == "no-match"
    artifacts = build_gseg_gsig_artifacts(pack)
    invariant = json.loads(artifacts["release_invariant_checklist.json"])
    assert invariant["summary"]["fail"] == 0
    assert invariant["summary"]["release_gate"] == "review"
    assert invariant["summary"]["external_validation_missing"] >= 1
    assert {
        "theorem_checklist.json",
        "verified_segment_evidence_array.csv",
        "verified_segment_evidence_array.jsonl",
        "verified_segment_evidence_array.parquet",
    }.isdisjoint(artifacts)
    lca_rows = list(csv.DictReader(io.StringIO(artifacts["segment_safe_taxa.csv"])))
    assert lca_rows[0]["lcaCheck"] == "pass"
    assert lca_rows[0]["recomputedSafeRank"] == "none"
    assert "graph_provenance_audit.csv" in artifacts


def test_safe_taxon_check_recomputes_lca_instead_of_comparing_alias_fields() -> None:
    shared_lineage = [
        {"rank": "family", "name": "Culicidae", "taxon_key": None},
        {"rank": "genus", "name": "Aedes", "taxon_key": None},
    ]
    hits = [
        {
            "taxon": "Aedes albopictus",
            "rank": "species",
            "lineage": [
                *shared_lineage,
                {"rank": "species", "name": "Aedes albopictus", "taxon_key": None},
            ],
        },
        {
            "taxon": "Aedes aegypti",
            "rank": "species",
            "lineage": [
                *shared_lineage,
                {"rank": "species", "name": "Aedes aegypti", "taxon_key": None},
            ],
        },
    ]
    source_alias = {"rank": "species", "name": "Aedes albopictus", "taxon_key": None}
    record = {
        "safe_taxon": source_alias,
        "candidate_taxon": source_alias,
        "top_hit": hits[0],
        "indistinguishable_hits": hits,
        "metadata_readiness": {"marker_profile": {"species_gate_pass": True}},
    }

    check = recompute_safe_taxon_lca(record)

    assert check["status"] == "fail"
    assert check["expected_safe_taxon"]["rank"] == "genus"
    assert check["expected_safe_taxon"]["name"] == "Aedes"

    record.pop("indistinguishable_hits")
    unavailable = recompute_safe_taxon_lca(record)
    assert unavailable["status"] == "not_independently_recomputed"
