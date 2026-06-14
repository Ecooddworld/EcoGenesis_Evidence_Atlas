from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from math import exp, log, sqrt
from typing import Mapping, Optional, Sequence


@dataclass(frozen=True)
class MarkerProfile:
    marker_id: str
    identity_min: float = 0.99
    coverage_min: float = 0.80
    min_aligned_length: int = 80
    species_claim_allowed: bool = True
    se_min: float = 0.0
    epsilon_alg: float = 0.0
    epsilon_marker: float = 0.0
    z_alpha: float = 1.96
    kmer_alpha: float = 0.01
    kmer_support_min: int = 1
    rci2_species_min: Optional[float] = None


@dataclass(frozen=True)
class Hit:
    hit_id: str
    taxon: str
    identity: float
    query_coverage: float
    aligned_length: int
    bit_score: float = 0.0
    e_value: float = 1.0

    @property
    def mismatch_rate(self) -> float:
        return 1.0 - self.identity


@dataclass(frozen=True)
class GateVector:
    exact: bool
    ambiguity_lca: bool
    barcode_gap: bool
    diagnostic_kmer: bool
    marker_profile: bool
    assay: bool
    rci2: bool = True

    @property
    def species_hard_pass(self) -> bool:
        return all(
            (
                self.exact,
                self.ambiguity_lca,
                self.barcode_gap,
                self.diagnostic_kmer,
                self.marker_profile,
                self.assay,
                self.rci2,
            )
        )


class Taxonomy:
    def __init__(self, parent: Mapping[str, Optional[str]], rank: Optional[Mapping[str, str]] = None):
        self.parent = dict(parent)
        self.rank = dict(rank or {})

    def ancestors(self, taxon: str) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        cur: Optional[str] = taxon
        while cur is not None and cur not in seen:
            out.append(cur)
            seen.add(cur)
            cur = self.parent.get(cur)
        return out

    def lca(self, taxa: Sequence[str]) -> Optional[str]:
        taxa = [taxon for taxon in taxa if taxon]
        if not taxa:
            return None
        ancestor_lists = [self.ancestors(taxon) for taxon in taxa]
        first = ancestor_lists[0]
        other_sets = [set(items) for items in ancestor_lists[1:]]
        for ancestor in first:
            if all(ancestor in items for items in other_sets):
                return ancestor
        return None


DNA_ALPHABET = set("ACGTN")
_RC = str.maketrans("ACGTNacgtn", "TGCANtgcan")


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + exp(-value))


def mismatch_se(hit: Hit, profile: MarkerProfile) -> float:
    if hit.aligned_length <= 0:
        return 1.0
    distance = hit.mismatch_rate
    se = sqrt(max(0.0, distance * (1.0 - distance)) / hit.aligned_length)
    return max(se, profile.se_min)


def exact_gate(hit: Hit, profile: MarkerProfile) -> bool:
    return (
        hit.identity >= profile.identity_min
        and hit.query_coverage >= profile.coverage_min
        and hit.aligned_length >= profile.min_aligned_length
    )


def ambiguity_boundary(top: Hit, competitor: Hit, profile: MarkerProfile) -> float:
    return (
        profile.z_alpha * sqrt(mismatch_se(top, profile) ** 2 + mismatch_se(competitor, profile) ** 2)
        + profile.epsilon_alg
        + profile.epsilon_marker
    )


def is_indistinguishable(top: Hit, competitor: Hit, profile: MarkerProfile) -> bool:
    delta = competitor.mismatch_rate - top.mismatch_rate
    return delta <= ambiguity_boundary(top, competitor, profile)


def choose_top_hit(hits: Sequence[Hit]) -> Optional[Hit]:
    if not hits:
        return None
    return sorted(hits, key=lambda hit: (hit.mismatch_rate, -hit.query_coverage, -hit.bit_score, hit.e_value))[0]


def uncertainty_set(hits: Sequence[Hit], profile: MarkerProfile) -> list[Hit]:
    top = choose_top_hit(hits)
    if top is None:
        return []
    return [hit for hit in hits if hit is top or is_indistinguishable(top, hit, profile)]


def safe_taxon(hits: Sequence[Hit], taxonomy: Taxonomy, profile: MarkerProfile) -> Optional[str]:
    return taxonomy.lca([hit.taxon for hit in uncertainty_set(hits, profile)])


def barcode_gap_pass(intra_max_distance: float, inter_min_distance: float, gamma: float = 0.0) -> tuple[bool, float]:
    gap = inter_min_distance - intra_max_distance
    return gap > gamma, gap


def diagnostic_p_false_positive(diagnostic_kmer_count_in_taxon: int, query_window_count: int, k: int) -> float:
    if k <= 0 or query_window_count <= 0 or diagnostic_kmer_count_in_taxon <= 0:
        return 0.0 if diagnostic_kmer_count_in_taxon <= 0 else 1.0
    p_one = min(1.0, diagnostic_kmer_count_in_taxon / (4.0**k))
    return 1.0 - (1.0 - p_one) ** query_window_count


def diagnostic_gate(support_count: int, p_false_positive: float, profile: MarkerProfile) -> bool:
    return support_count >= profile.kmer_support_min and p_false_positive <= profile.kmer_alpha


def weighted_geomean(values: Mapping[str, float], weights: Optional[Mapping[str, float]] = None, eps: float = 1e-9) -> float:
    if not values:
        return 0.0
    resolved_weights = dict(weights or {key: 1.0 for key in values})
    denominator = sum(max(0.0, resolved_weights.get(key, 0.0)) for key in values)
    if denominator <= 0:
        return 0.0
    return exp(sum(resolved_weights.get(key, 0.0) * log(clamp(value) + eps) for key, value in values.items()) / denominator)


def rci2_score(
    species_coverage: float,
    close_relative_coverage: float,
    depth_coverage: float,
    region_coverage: float,
    provenance_quality: float,
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    return weighted_geomean(
        {
            "species": species_coverage,
            "close": close_relative_coverage,
            "depth": depth_coverage,
            "region": region_coverage,
            "provenance": provenance_quality,
        },
        weights,
    )


def segment_evidence_score(
    gates: GateVector,
    identity: float,
    coverage: float,
    barcode_gap: float,
    kmer_p_false_positive: float,
    rci2: float,
    assay_score: float,
    marker_score: float,
    uncertainty_penalty: float,
    profile: MarkerProfile,
    weights: Optional[Mapping[str, float]] = None,
) -> float:
    if not gates.species_hard_pass:
        return 0.0
    identity_norm = clamp((identity - profile.identity_min) / max(1e-9, 1.0 - profile.identity_min))
    coverage_norm = clamp((coverage - profile.coverage_min) / max(1e-9, 1.0 - profile.coverage_min))
    gap_norm = sigmoid(barcode_gap / 0.01) if barcode_gap is not None else 0.0
    kmer_norm = 1.0 - min(1.0, kmer_p_false_positive / max(profile.kmer_alpha, 1e-12))
    return weighted_geomean(
        {
            "identity": identity_norm,
            "coverage": coverage_norm,
            "barcode_gap": gap_norm,
            "kmer": kmer_norm,
            "rci2": rci2,
            "assay": assay_score,
            "marker": marker_score,
            "uncertainty": uncertainty_penalty,
        },
        weights,
    )


def cross_marker_consensus(marker_safe_taxa: Mapping[str, str], taxonomy: Taxonomy) -> Optional[str]:
    return taxonomy.lca(list(marker_safe_taxa.values()))


def assert_no_species_safe_hard_gate_violation(decisions: Sequence[Mapping[str, object]]) -> None:
    gate_names = ["exact", "ambiguity_lca", "barcode_gap", "diagnostic_kmer", "marker_profile", "assay", "rci2"]
    for row in decisions:
        if row.get("decision_class") == "species-safe":
            failed = [gate for gate in gate_names if not bool(row.get(gate))]
            if failed:
                raise AssertionError(f"species-safe hard gate violation for {row.get('id')}: {failed}")


def normalize_sequence(seq: str, ambiguity_policy: str = "keep_N") -> str:
    if seq is None:
        raise ValueError("sequence is None")
    normalized = "".join(str(seq).split()).upper()
    if ambiguity_policy == "keep_N":
        return "".join(ch if ch in DNA_ALPHABET else "N" for ch in normalized)
    if ambiguity_policy == "reject":
        bad = sorted(set(normalized) - DNA_ALPHABET)
        if bad:
            raise ValueError(f"invalid DNA symbols: {bad}")
        return normalized
    raise ValueError(f"unknown ambiguity_policy={ambiguity_policy}")


def reverse_complement(seq: str) -> str:
    return normalize_sequence(seq).translate(_RC)[::-1]


def canonical_segment(seq: str, strand_policy: str = "as_is", ambiguity_policy: str = "keep_N") -> str:
    normalized = normalize_sequence(seq, ambiguity_policy=ambiguity_policy)
    if strand_policy == "as_is":
        return normalized
    if strand_policy == "canonical_min":
        return min(normalized, reverse_complement(normalized))
    raise ValueError(f"unknown strand_policy={strand_policy}")


def segment_hash(seq: str, start: int, end: int, ruleset_version: str, strand_policy: str = "as_is") -> str:
    if start < 0 or end <= start:
        raise ValueError("invalid segment coordinates")
    canonical = canonical_segment(seq, strand_policy=strand_policy)
    payload = f"{canonical}|{start}|{end}|{ruleset_version}|{strand_policy}"
    return sha256(payload.encode("utf-8")).hexdigest()


def kmers(seq: str, k: int) -> set[str]:
    normalized = normalize_sequence(seq)
    if k <= 0:
        raise ValueError("k must be positive")
    if len(normalized) < k:
        return set()
    return {normalized[index : index + k] for index in range(len(normalized) - k + 1)}


def jaccard_kmers(a: str, b: str, k: int) -> float:
    ka, kb = kmers(a, k), kmers(b, k)
    if not ka and not kb:
        return 1.0
    union = ka | kb
    if not union:
        return 0.0
    return len(ka & kb) / len(union)


def cluster_equivalent(a: str, b: str, k: int = 5, theta_jaccard: float = 0.90) -> bool:
    return canonical_segment(a, "canonical_min") == canonical_segment(b, "canonical_min") or jaccard_kmers(a, b, k) >= theta_jaccard


def taxonomic_entropy(probabilities: Mapping[str, float]) -> float:
    values = [p for p in probabilities.values() if p > 0]
    if not values:
        return 0.0
    total = sum(values)
    ps = [p / total for p in values]
    if len(ps) == 1:
        return 0.0
    return -sum(p * log(p) for p in ps) / log(len(ps))


def specificity(probabilities: Mapping[str, float]) -> float:
    return max(0.0, min(1.0, 1.0 - taxonomic_entropy(probabilities)))


def sharedness(probabilities: Mapping[str, float], p_min: float = 0.05) -> int:
    total = sum(max(0.0, p) for p in probabilities.values())
    if total <= 0:
        return 0
    return sum(1 for p in probabilities.values() if p / total > p_min)


def species_specific_allowed(probabilities_by_species: Mapping[str, float], p_min: float = 0.05) -> bool:
    return sharedness(probabilities_by_species, p_min=p_min) <= 1


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "raw": {"normalized", "blocked"},
    "normalized": {"verified_segment", "blocked"},
    "verified_segment": {"taxon_supported", "taxon_ambiguous", "shared_segment", "blocked"},
    "taxon_supported": {"clade_specific", "annotation_attached", "blocked"},
    "taxon_ambiguous": {"shared_segment", "blocked"},
    "shared_segment": {"annotation_attached", "blocked"},
    "clade_specific": {"annotation_attached", "blocked"},
    "annotation_attached": {"trait_associated", "function_hypothesis", "experimentally_supported", "contradicted", "blocked"},
    "trait_associated": {"function_hypothesis", "contradicted", "blocked"},
    "function_hypothesis": {"experimentally_supported", "contradicted", "blocked"},
    "experimentally_supported": {"deprecated", "contradicted"},
    "contradicted": {"deprecated"},
    "blocked": {"normalized", "verified_segment", "deprecated"},
    "deprecated": set(),
}


def transition_allowed(src: str, dst: str) -> bool:
    return dst in ALLOWED_TRANSITIONS.get(src, set())


def evidence_claim_valid(claim: Mapping[str, object]) -> bool:
    required = ["claim_id", "claim_type", "claim_state", "evidence_type", "source_id", "provenance_hash"]
    if any(not claim.get(key) for key in required):
        return False
    if claim.get("claim_state") == "experimentally_supported" and claim.get("evidence_type") not in {
        "direct_experiment",
        "curated_experimental",
    }:
        return False
    return True


def ai_output_allowed(output: Mapping[str, object]) -> bool:
    if output.get("writes_verified_graph_fact"):
        return False
    if output.get("claim_state") in {"experimentally_supported", "taxon_supported", "clade_specific"} and output.get("source") == "ai_only":
        return False
    return True


def graph_provenance_complete(nodes: Sequence[Mapping[str, object]], edges: Sequence[Mapping[str, object]]) -> bool:
    for obj in list(nodes) + list(edges):
        if not obj.get("provenance_hash"):
            return False
    return True


def preserve_claim_states_for_ai_export(rows: Sequence[Mapping[str, object]]) -> bool:
    for row in rows:
        if not row.get("claim_state"):
            return False
        if row.get("ai_label") == "fact" and row.get("claim_state") in {
            "weak_hypothesis",
            "function_hypothesis",
            "statistically_associated",
        }:
            return False
    return True


def benjamini_hochberg(pvalues: Sequence[float], alpha: float = 0.05) -> list[bool]:
    if not pvalues:
        return []
    m = len(pvalues)
    indexed = sorted(enumerate(pvalues), key=lambda item: item[1])
    kmax = -1
    for rank, (_idx, pvalue) in enumerate(indexed, start=1):
        if pvalue <= (rank / m) * alpha:
            kmax = rank
    passed = [False] * m
    if kmax >= 1:
        cutoff = indexed[kmax - 1][1]
        passed = [pvalue <= cutoff for pvalue in pvalues]
    return passed
