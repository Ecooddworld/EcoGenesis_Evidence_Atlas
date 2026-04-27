from __future__ import annotations

from typing import Any


DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "invasive",
        "label": "Live invasive watch",
        "tag": "real GBIF query",
        "description": "Attempts live GBIF records for an invasive species case, with fixture fallback only if the API is unavailable.",
        "form": {
            "taxon": "Aedes albopictus",
            "region_name": "Spain live GBIF bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "online_with_fixture_fallback",
            "use_fixture": False,
            "max_records": 300,
        },
    },
    {
        "id": "gaps",
        "label": "Live oak gaps",
        "tag": "editable taxon",
        "description": "Runs a live GBIF query for a common tree taxon and ranks survey-priority grid cells.",
        "form": {
            "taxon": "Quercus robur",
            "region_name": "Western Europe live bbox",
            "bbox": [-10.0, 42.0, 12.0, 56.0],
            "purpose": "sampling_gaps",
            "source_mode": "online_with_fixture_fallback",
            "use_fixture": False,
            "max_records": 300,
        },
    },
    {
        "id": "quality",
        "label": "Live dataset review",
        "tag": "publisher ready",
        "description": "Uses live GBIF records to group quality issues by datasetKey for a Publisher Feedback Pack.",
        "form": {
            "taxon": "Lynx pardinus",
            "region_name": "Iberian Peninsula live bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "dataset_quality_review",
            "source_mode": "online_with_fixture_fallback",
            "use_fixture": False,
            "max_records": 300,
        },
    },
    {
        "id": "offline",
        "label": "Offline fixture",
        "tag": "reproducible fallback",
        "description": "Uses the deterministic offline fixture for no-network testing and regression checks.",
        "form": {
            "taxon": "Aedes albopictus",
            "region_name": "Spain offline fixture bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "fixture",
            "use_fixture": True,
            "max_records": 300,
        },
    },
]
