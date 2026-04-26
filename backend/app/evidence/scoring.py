from __future__ import annotations

from typing import Any


PURPOSE_LABELS = {
    "conservation_brief": "Conservation brief",
    "invasive_watch": "Invasive watch",
    "sampling_gaps": "Sampling gap analysis",
    "dataset_quality_review": "Dataset quality review",
}

PURPOSE_WEIGHTS = {
    "conservation_brief": {
        "spatial_accuracy": 0.30,
        "temporal_recency": 0.20,
        "taxonomic_confidence": 0.20,
        "sampling_coverage": 0.20,
        "citation_provenance": 0.10,
        "issue_explainability": 0.00,
    },
    "invasive_watch": {
        "spatial_accuracy": 0.25,
        "temporal_recency": 0.35,
        "taxonomic_confidence": 0.15,
        "sampling_coverage": 0.15,
        "citation_provenance": 0.10,
        "issue_explainability": 0.00,
    },
    "sampling_gaps": {
        "spatial_accuracy": 0.20,
        "temporal_recency": 0.10,
        "taxonomic_confidence": 0.15,
        "sampling_coverage": 0.45,
        "citation_provenance": 0.10,
        "issue_explainability": 0.00,
    },
    "dataset_quality_review": {
        "spatial_accuracy": 0.25,
        "temporal_recency": 0.10,
        "taxonomic_confidence": 0.20,
        "sampling_coverage": 0.10,
        "citation_provenance": 0.20,
        "issue_explainability": 0.15,
    },
}


def readiness_score(quality: dict[str, Any], grid: dict[str, Any], *, purpose: str, match_confidence: float) -> dict[str, Any]:
    spatial = max(0.0, quality["valid_coordinate_rate"] * 100.0 - quality["high_uncertainty_rate"] * 35.0)
    temporal = quality["date_present_rate"] * 70.0 + quality["recent_record_rate"] * 30.0
    taxonomy = quality["taxon_key_rate"] * 70.0 + min(100.0, match_confidence) * 0.30
    if grid["features"]:
        sampling = sum(feature["properties"]["sampling_coverage_proxy"] for feature in grid["features"]) / len(grid["features"]) * 100.0
    else:
        sampling = 0.0
    provenance = (quality["dataset_key_rate"] * 0.65 + quality["license_rate"] * 0.35) * 100.0
    issue_explainability = 100.0 if quality["total_records"] else 0.0

    components = {
        "spatial_accuracy": round(spatial, 2),
        "temporal_recency": round(temporal, 2),
        "taxonomic_confidence": round(taxonomy, 2),
        "sampling_coverage": round(sampling, 2),
        "citation_provenance": round(provenance, 2),
        "issue_explainability": round(issue_explainability, 2),
    }
    weights = PURPOSE_WEIGHTS[purpose]
    score = sum(components[key] * weight for key, weight in weights.items())
    return {
        "purpose": purpose,
        "purpose_label": PURPOSE_LABELS[purpose],
        "score": round(max(0.0, min(100.0, score)), 2),
        "components": components,
        "weights": weights,
        "interpretation": _interpret(score),
    }


def purpose_score_matrix(quality: dict[str, Any], grid: dict[str, Any], *, match_confidence: float) -> dict[str, Any]:
    return {
        purpose: readiness_score(quality, grid, purpose=purpose, match_confidence=match_confidence)
        for purpose in PURPOSE_LABELS
    }


def _interpret(score: float) -> str:
    if score >= 80:
        return "High readiness: evidence is strong for the selected purpose, with remaining caveats documented."
    if score >= 60:
        return "Moderate readiness: useful evidence, but caveats and verification steps matter."
    if score >= 40:
        return "Limited readiness: use for triage and planning, not as a standalone conclusion."
    return "Low readiness: the data are primarily useful for identifying gaps and corrective actions."
