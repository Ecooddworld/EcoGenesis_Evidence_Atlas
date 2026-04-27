from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
import math
from typing import Any, Iterable

from .gbif import NormalizedOccurrence


def hill_metrics(species_counts: Counter[str], target_coverage: float = 0.8) -> dict[str, Any]:
    total = int(sum(species_counts.values()))
    observed_species = int(sum(1 for count in species_counts.values() if count > 0))
    if total <= 0:
        return {
            "occurrence_count": 0,
            "species_count": 0,
            "hill_q0": 0.0,
            "hill_q1": 0.0,
            "hill_q2": 0.0,
            "shannon_entropy": 0.0,
            "simpson_concentration": 0.0,
            "good_coverage": 0.0,
            "singletons": 0,
            "doubletons": 0,
            "chao1_richness": 0.0,
            "coverage_status": "empty",
        }
    proportions = [count / total for count in species_counts.values() if count > 0]
    shannon = -sum(p * math.log(p) for p in proportions)
    simpson = sum(p * p for p in proportions)
    singletons = sum(1 for count in species_counts.values() if count == 1)
    doubletons = sum(1 for count in species_counts.values() if count == 2)
    good_coverage = max(0.0, min(1.0, 1.0 - singletons / total))
    if doubletons > 0:
        chao1 = observed_species + (singletons * singletons) / (2.0 * doubletons)
    else:
        chao1 = observed_species + (singletons * max(0, singletons - 1)) / 2.0
    return {
        "occurrence_count": total,
        "species_count": observed_species,
        "hill_q0": float(observed_species),
        "hill_q1": math.exp(shannon),
        "hill_q2": 1.0 / simpson if simpson else 0.0,
        "shannon_entropy": shannon,
        "simpson_concentration": simpson,
        "good_coverage": good_coverage,
        "singletons": singletons,
        "doubletons": doubletons,
        "chao1_richness": chao1,
        "coverage_status": "coverage_ok" if good_coverage >= target_coverage else "under_sampled",
    }


def quality_metrics(records: list[NormalizedOccurrence], *, current_year: int) -> dict[str, Any]:
    total = len(records)
    if total == 0:
        return {
            "total_records": 0,
            "valid_coordinate_rate": 0.0,
            "date_present_rate": 0.0,
            "recent_record_rate": 0.0,
            "taxon_key_rate": 0.0,
            "dataset_key_rate": 0.0,
            "license_rate": 0.0,
            "high_uncertainty_rate": 0.0,
            "missing_date_count": 0,
            "high_uncertainty_count": 0,
            "invalid_coordinate_count": 0,
            "country_coordinate_mismatch_count": 0,
        }
    valid_coords = sum(1 for record in records if record.has_valid_coordinate)
    date_present = sum(1 for record in records if record.event_date or record.year)
    recent = sum(1 for record in records if record.year is not None and record.year >= current_year - 10)
    taxon_keys = sum(1 for record in records if record.accepted_taxon_key)
    dataset_keys = sum(1 for record in records if record.dataset_key and record.dataset_key != "unknown_dataset")
    licenses = sum(1 for record in records if record.license)
    high_uncertainty = sum(1 for record in records if (record.coordinate_uncertainty_m or 0) > 10000)
    invalid_coords = total - valid_coords
    mismatch = sum(1 for record in records if "COUNTRY_COORDINATE_MISMATCH" in record.issues)
    return {
        "total_records": total,
        "valid_coordinate_rate": round(valid_coords / total, 4),
        "date_present_rate": round(date_present / total, 4),
        "recent_record_rate": round(recent / total, 4),
        "taxon_key_rate": round(taxon_keys / total, 4),
        "dataset_key_rate": round(dataset_keys / total, 4),
        "license_rate": round(licenses / total, 4),
        "high_uncertainty_rate": round(high_uncertainty / total, 4),
        "missing_date_count": total - date_present,
        "high_uncertainty_count": high_uncertainty,
        "invalid_coordinate_count": invalid_coords,
        "country_coordinate_mismatch_count": mismatch,
    }


def build_records_geojson(records: Iterable[NormalizedOccurrence]) -> dict[str, Any]:
    features = []
    for record in records:
        if not record.has_valid_coordinate:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [record.longitude, record.latitude]},
                "properties": {
                    "gbif_id": record.gbif_id,
                    "datasetKey": record.dataset_key,
                    "datasetTitle": record.dataset_title,
                    "scientificName": record.scientific_name,
                    "eventDate": record.event_date,
                    "year": record.year,
                    "coordinateUncertaintyInMeters": record.coordinate_uncertainty_m,
                    "license": record.license,
                    "issues": record.issues,
                },
            }
        )
    return {"type": "FeatureCollection", "features": features}


def build_grid_metrics(
    records: list[NormalizedOccurrence],
    bbox: list[float],
    *,
    grid_size: int = 4,
    current_year: int | None = None,
) -> dict[str, Any]:
    current_year = current_year or datetime.now(timezone.utc).year
    west, south, east, north = bbox
    width = (east - west) / grid_size
    height = (north - south) / grid_size
    cells: dict[str, dict[str, Any]] = {
        f"grid:{grid_size}:{x}:{y}": {
            "x": x,
            "y": y,
            "records": [],
            "species_counts": Counter(),
            "datasets": set(),
            "years": [],
        }
        for y in range(grid_size)
        for x in range(grid_size)
    }
    for record in records:
        if not record.has_valid_coordinate:
            continue
        if not (west <= record.longitude <= east and south <= record.latitude <= north):
            continue
        x = min(grid_size - 1, max(0, int((record.longitude - west) / width)))
        y = min(grid_size - 1, max(0, int((record.latitude - south) / height)))
        cell_id = f"grid:{grid_size}:{x}:{y}"
        bucket = cells[cell_id]
        bucket["records"].append(record)
        bucket["species_counts"][record.species_identifier] += 1
        bucket["datasets"].add(record.dataset_key)
        if record.year is not None:
            bucket["years"].append(record.year)

    features = []
    max_n = max((len(bucket["records"]) for bucket in cells.values()), default=1)
    if max_n == 0:
        max_n = 1
    for cell_id, bucket in sorted(cells.items()):
        _, _, x_text, y_text = cell_id.split(":")
        x = int(x_text)
        y = int(y_text)
        cell_west = west + x * width
        cell_east = cell_west + width
        cell_south = south + y * height
        cell_north = cell_south + height
        n = len(bucket["records"])
        metrics = hill_metrics(bucket["species_counts"])
        sampling_coverage_proxy = min(1.0, n / 5.0)
        detection_effort_proxy = math.log1p(n) / math.log1p(max_n) if max_n > 0 else 0.0
        high_uncertainty_count = sum(1 for record in bucket["records"] if (record.coordinate_uncertainty_m or 0) > 10000)
        empty_cell = n == 0
        under_sampled = not empty_cell and sampling_coverage_proxy < 0.6
        priority = _gap_priority(
            bucket=bucket,
            cells=cells,
            grid_size=grid_size,
            empty_cell=empty_cell,
            under_sampled=under_sampled,
            high_uncertainty_count=high_uncertainty_count,
            current_year=current_year,
        )
        survey_priority = empty_cell or under_sampled or priority["score"] >= 35
        properties = {
            "cell_id": cell_id,
            "occurrence_count": n,
            "dataset_count": len(bucket["datasets"]),
            "high_uncertainty_count": high_uncertainty_count,
            "min_year": min(bucket["years"]) if bucket["years"] else None,
            "max_year": max(bucket["years"]) if bucket["years"] else None,
            "sampling_coverage_proxy": round(sampling_coverage_proxy, 4),
            "empty_cell": empty_cell,
            "no_evidence_cell": empty_cell,
            "under_sampled": under_sampled,
            "survey_priority": survey_priority,
            "detection_effort_proxy": round(detection_effort_proxy, 4),
            "non_detection_risk": round(1.0 - detection_effort_proxy, 4),
            "gap_priority_score": priority["score"],
            "gap_priority_label": priority["label"],
            "gap_priority_components": priority["components"],
            "gap_priority_reasons": priority["reasons"],
            **{key: round(value, 4) if isinstance(value, float) else value for key, value in metrics.items()},
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [cell_west, cell_south],
                            [cell_east, cell_south],
                            [cell_east, cell_north],
                            [cell_west, cell_north],
                            [cell_west, cell_south],
                        ]
                    ],
                },
                "properties": properties,
            }
        )
    occupied_cell_count = sum(1 for feature in features if feature["properties"]["occurrence_count"] > 0)
    empty_cell_count = sum(1 for feature in features if feature["properties"]["empty_cell"])
    under_sampled_occupied = sum(1 for feature in features if feature["properties"]["under_sampled"])
    survey_priority_cells = sum(1 for feature in features if feature["properties"]["survey_priority"])
    top_priority_cells = [
        {
            "cell_id": feature["properties"]["cell_id"],
            "score": feature["properties"]["gap_priority_score"],
            "label": feature["properties"]["gap_priority_label"],
            "reasons": feature["properties"]["gap_priority_reasons"],
            "occurrence_count": feature["properties"]["occurrence_count"],
        }
        for feature in sorted(features, key=lambda item: item["properties"]["gap_priority_score"], reverse=True)
        if feature["properties"]["survey_priority"]
    ][:3]
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "grid_size": grid_size,
            "cell_count": len(features),
            "occupied_cell_count": occupied_cell_count,
            "empty_cell_count": empty_cell_count,
            "under_sampled_cells": under_sampled_occupied,
            "under_sampled_occupied_cells": under_sampled_occupied,
            "survey_priority_cells": survey_priority_cells,
            "top_survey_priority_cells": top_priority_cells,
            "method": "Taxon-focused grid: occurrence density, sampling coverage proxy and non-detection risk. Empty cells are not absences.",
        },
    }


def serialize_records(records: list[NormalizedOccurrence]) -> list[dict[str, Any]]:
    return [asdict(record) for record in records]


def _gap_priority(
    *,
    bucket: dict[str, Any],
    cells: dict[str, dict[str, Any]],
    grid_size: int,
    empty_cell: bool,
    under_sampled: bool,
    high_uncertainty_count: int,
    current_year: int,
) -> dict[str, Any]:
    x = bucket["x"]
    y = bucket["y"]
    records = bucket["records"]
    n = len(records)
    neighbor_buckets = [
        other
        for other in (
            cells.get(f"grid:{grid_size}:{nx}:{ny}")
            for nx in range(max(0, x - 1), min(grid_size - 1, x + 1) + 1)
            for ny in range(max(0, y - 1), min(grid_size - 1, y + 1) + 1)
            if not (nx == x and ny == y)
        )
        if other is not None
    ]
    occupied_neighbors = sum(1 for other in neighbor_buckets if other["records"])
    neighbor_evidence = occupied_neighbors / len(neighbor_buckets) if neighbor_buckets else 0.0
    if not bucket["years"]:
        recency_deficit = 1.0
    else:
        age = max(0, current_year - max(bucket["years"]))
        recency_deficit = min(1.0, age / 20.0)
    uncertainty_burden = 0.0 if n == 0 else min(1.0, high_uncertainty_count / n)
    dataset_count = len(bucket["datasets"])
    if dataset_count == 0:
        source_diversity_gap = 1.0
    elif dataset_count == 1:
        source_diversity_gap = 0.6
    elif dataset_count == 2:
        source_diversity_gap = 0.3
    else:
        source_diversity_gap = 0.0
    no_evidence = 1.0 if empty_cell else 0.0
    under_sampled_component = 0.45 if under_sampled else 0.0
    score = 100.0 * (
        0.35 * max(no_evidence, under_sampled_component)
        + 0.20 * neighbor_evidence
        + 0.20 * recency_deficit
        + 0.15 * uncertainty_burden
        + 0.10 * source_diversity_gap
    )
    reasons = []
    if empty_cell:
        reasons.append("No GBIF-mediated records returned after filters")
    if under_sampled:
        reasons.append("Occupied cell remains below sampling coverage threshold")
    if neighbor_evidence >= 0.35:
        reasons.append("Neighboring cells contain occurrence evidence")
    if recency_deficit >= 0.5:
        reasons.append("Recent temporal evidence is weak or missing")
    if uncertainty_burden >= 0.5:
        reasons.append("Coordinate uncertainty burdens cell interpretation")
    if source_diversity_gap >= 0.6:
        reasons.append("Dataset/source diversity is low")
    if not reasons:
        reasons.append("Lower survey priority under current fixture metrics")
    return {
        "score": round(score, 2),
        "label": _gap_label(score),
        "components": {
            "no_evidence": round(no_evidence, 4),
            "neighbor_evidence": round(neighbor_evidence, 4),
            "recency_deficit": round(recency_deficit, 4),
            "uncertainty_burden": round(uncertainty_burden, 4),
            "source_diversity_gap": round(source_diversity_gap, 4),
        },
        "reasons": reasons,
    }


def _gap_label(score: float) -> str:
    if score >= 60:
        return "High priority for survey"
    if score >= 35:
        return "Medium priority for survey"
    return "Low priority"
