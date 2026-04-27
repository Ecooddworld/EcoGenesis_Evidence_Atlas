from __future__ import annotations

from typing import Any


DEMO_SCENARIOS: list[dict[str, Any]] = [
    {
        "id": "invasive",
        "label": "Invasive risk",
        "tag": "Aedes albopictus · Spain",
        "description": "Attempts live GBIF records for an invasive species case. If GBIF is unavailable, old fixture records are not reused.",
        "form": {
            "taxon": "Aedes albopictus",
            "taxon_key": 1651430,
            "region_name": "Spain live GBIF bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "online_with_empty_fallback",
            "use_fixture": False,
            "max_records": 300,
        },
    },
    {
        "id": "gaps",
        "label": "Forest gaps",
        "tag": "Quercus robur · W Europe",
        "description": "Runs a live GBIF query for a common tree taxon and ranks survey-priority grid cells.",
        "form": {
            "taxon": "Quercus robur",
            "taxon_key": 2878688,
            "region_name": "Western Europe live bbox",
            "bbox": [-10.0, 42.0, 12.0, 56.0],
            "purpose": "sampling_gaps",
            "source_mode": "online_with_empty_fallback",
            "use_fixture": False,
            "max_records": 300,
        },
    },
    {
        "id": "quality",
        "label": "Data review",
        "tag": "Lynx pardinus · Iberia",
        "description": "Uses live GBIF records to group quality issues by datasetKey for a Publisher Feedback Pack.",
        "form": {
            "taxon": "Lynx pardinus",
            "taxon_key": 2435261,
            "region_name": "Iberian Peninsula live bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "dataset_quality_review",
            "source_mode": "online_with_empty_fallback",
            "use_fixture": False,
            "max_records": 300,
        },
    },
    {
        "id": "offline",
        "label": "Offline sample",
        "tag": "stable regression data",
        "description": "Uses the deterministic offline fixture for no-network testing and regression checks.",
        "form": {
            "taxon": "Aedes albopictus",
            "taxon_key": 1651430,
            "region_name": "Spain offline fixture bbox",
            "bbox": [-10.0, 35.0, 4.5, 44.5],
            "purpose": "invasive_watch",
            "source_mode": "fixture",
            "use_fixture": True,
            "max_records": 300,
        },
    },
]


REGION_PRESETS: list[dict[str, Any]] = [
    {
        "id": "spain",
        "label": "Spain",
        "region_name": "Spain live GBIF bbox",
        "bbox": [-10.0, 35.0, 4.5, 44.5],
        "description": "Compact judge demo extent with strong live GBIF coverage.",
    },
    {
        "id": "iberian",
        "label": "Iberian Peninsula",
        "region_name": "Iberian Peninsula live bbox",
        "bbox": [-10.0, 35.0, 4.5, 44.5],
        "description": "Useful for Iberian conservation and dataset quality tests.",
    },
    {
        "id": "western-europe",
        "label": "Western Europe",
        "region_name": "Western Europe live bbox",
        "bbox": [-10.0, 42.0, 12.0, 56.0],
        "description": "Broader tree, plant and bird sampling-gap experiments.",
    },
    {
        "id": "mediterranean",
        "label": "Western Mediterranean",
        "region_name": "Western Mediterranean live bbox",
        "bbox": [-6.5, 34.5, 16.0, 46.5],
        "description": "Coastal and island corridor tests for invasive-watch workflows.",
    },
    {
        "id": "north-america",
        "label": "North America",
        "region_name": "North America test bbox",
        "bbox": [-130.0, 24.0, -60.0, 55.0],
        "description": "Large-area smoke test; keep max records moderate for responsive demos.",
    },
]


POPULAR_TAXA: list[dict[str, Any]] = [
    {
        "usageKey": 1651430,
        "scientificName": "Aedes albopictus",
        "canonicalName": "Aedes albopictus",
        "rank": "SPECIES",
        "status": "ACCEPTED",
        "kingdom": "Animalia",
        "family": "Culicidae",
        "confidence": 100,
        "source": "curated_demo",
    },
    {
        "usageKey": 2878688,
        "scientificName": "Quercus robur L.",
        "canonicalName": "Quercus robur",
        "rank": "SPECIES",
        "status": "ACCEPTED",
        "kingdom": "Plantae",
        "family": "Fagaceae",
        "confidence": 100,
        "source": "curated_demo",
    },
    {
        "usageKey": 2435261,
        "scientificName": "Lynx pardinus (Temminck, 1827)",
        "canonicalName": "Lynx pardinus",
        "rank": "SPECIES",
        "status": "ACCEPTED",
        "kingdom": "Animalia",
        "family": "Felidae",
        "confidence": 100,
        "source": "curated_demo",
    },
    {
        "usageKey": 1341976,
        "scientificName": "Apis mellifera Linnaeus, 1758",
        "canonicalName": "Apis mellifera",
        "rank": "SPECIES",
        "status": "ACCEPTED",
        "kingdom": "Animalia",
        "family": "Apidae",
        "confidence": 100,
        "source": "curated_demo",
    },
    {
        "usageKey": 5231190,
        "scientificName": "Passer domesticus (Linnaeus, 1758)",
        "canonicalName": "Passer domesticus",
        "rank": "SPECIES",
        "status": "ACCEPTED",
        "kingdom": "Animalia",
        "family": "Passeridae",
        "confidence": 100,
        "source": "curated_demo",
    },
]
