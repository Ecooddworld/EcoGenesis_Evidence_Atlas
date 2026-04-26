from __future__ import annotations

from typing import Any


DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "invasive",
        "label": "Invasive watch",
        "tag": "recency weighted",
        "description": "A judge-ready fixture scenario focused on recent records, uncertainty and unsafe absence claims.",
        "form": {
            "taxon": "Aedes albopictus",
            "region_name": "Spain demo bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "fixture",
            "use_fixture": True,
            "max_records": 300,
        },
    },
    {
        "id": "gaps",
        "label": "Sampling gaps",
        "tag": "coverage weighted",
        "description": "Highlights empty/no-evidence cells and under-sampled occupied cells as survey priorities.",
        "form": {
            "taxon": "Aedes albopictus",
            "region_name": "Spain sampling gap demo",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "sampling_gaps",
            "source_mode": "fixture",
            "use_fixture": True,
            "max_records": 300,
        },
    },
    {
        "id": "quality",
        "label": "Dataset review",
        "tag": "publisher ready",
        "description": "Groups record-level quality issues by datasetKey for a Publisher Feedback Pack.",
        "form": {
            "taxon": "Aedes albopictus",
            "region_name": "Spain dataset quality demo",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "dataset_quality_review",
            "source_mode": "fixture",
            "use_fixture": True,
            "max_records": 300,
        },
    },
    {
        "id": "conservation",
        "label": "Conservation brief",
        "tag": "balanced evidence",
        "description": "Uses balanced purpose weights for a concise conservation evidence summary.",
        "form": {
            "taxon": "Aedes albopictus",
            "region_name": "Spain conservation demo",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "conservation_brief",
            "source_mode": "fixture",
            "use_fixture": True,
            "max_records": 300,
        },
    },
]

