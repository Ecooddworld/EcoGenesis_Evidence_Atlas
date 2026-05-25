from __future__ import annotations

from copy import deepcopy
from typing import Any


BASE_SEQUENCE = (
    "ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCG"
    "GATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGTAGCTAGGCTAGCTAGCATCGATCGTACGAT"
    "CGTAGCTAGCTAGGATCGATCGTACGATCGTAGCTAGCATCGATCGTACCGTAGCTAGCTAGGCTAGCT"
    "AGGATCGATCGTAGCTAGGCTAGCTAGCATCGATCGTACGATCGTAGCTAGCTAGGATCGATCGTACGA"
    "TCGTAGCTAGCATCGATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGTAGCTAGGCTAGCTAG"
    "CATCGATCGTACGATCGTAGCTAGCTAGGATCGATCGTACGATCGTAGCTAGCATCGATCGTACCGTAG"
    "CTAGCTAGGCTAGCTAGGATCGATCGTAGCTAGGCTAGCTAGCATCGATCGTACGATCGTAGCTAGCTA"
    "GGATCGATCGTACGATCGTAGCTAGCATCGATCGTACCGTAGCTAGCTAGGCTAGCTAGGATCGATCGT"
    "AGCTAGGCTAGCTAGCATCGATCGTACGATCGTAGCTAGCTAGGATCGATCGTACGATCGTAGCTAGCA"
)


AEDES_ALBOPICTUS_LINEAGE = [
    {"rank": "kingdom", "name": "Animalia"},
    {"rank": "phylum", "name": "Arthropoda"},
    {"rank": "class", "name": "Insecta"},
    {"rank": "order", "name": "Diptera"},
    {"rank": "family", "name": "Culicidae"},
    {"rank": "genus", "name": "Aedes"},
    {"rank": "species", "name": "Aedes albopictus", "taxon_key": 1651430},
]


AEDES_AEGYPTI_LINEAGE = [
    {"rank": "kingdom", "name": "Animalia"},
    {"rank": "phylum", "name": "Arthropoda"},
    {"rank": "class", "name": "Insecta"},
    {"rank": "order", "name": "Diptera"},
    {"rank": "family", "name": "Culicidae"},
    {"rank": "genus", "name": "Aedes"},
    {"rank": "species", "name": "Aedes aegypti", "taxon_key": 1651431},
]


def base_metadata(sequence_id: str) -> dict[str, Any]:
    return {
        "occurrenceID": f"urn:ecogenesis:demo:{sequence_id}",
        "basisOfRecord": "MaterialSample",
        "scientificName": "Aedes albopictus",
        "eventDate": "2026-04-18",
        "countryCode": "ES",
        "decimalLatitude": 40.4168,
        "decimalLongitude": -3.7038,
        "geodeticDatum": "WGS84",
        "coordinateUncertaintyInMeters": 50,
        "methodOrSOP": "GBIF Sequence ID-compatible COI BLAST workflow; ruleset barcode-gbif-compiler-v2",
    }


def top_hit(identity: float, coverage: float, *, taxon: str = "Aedes albopictus", lineage: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "taxon": taxon,
        "rank": "species",
        "identity": identity,
        "query_coverage": coverage,
        "aligned_length": 658,
        "bit_score": identity * coverage,
        "evalue": 1e-120,
        "reference_id": f"BOLD:{taxon.replace(' ', '_')}",
        "reference_database": "COI Animals / BOLD public clustered reference",
        "gbif_taxon_key": 1651430 if taxon == "Aedes albopictus" else 1651431,
        "lineage": lineage or AEDES_ALBOPICTUS_LINEAGE,
    }


def sequence_record(sequence_id: str, hits: list[dict[str, Any]], *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "sequence_id": sequence_id,
        "sequence": BASE_SEQUENCE,
        "metadata": metadata if metadata is not None else base_metadata(sequence_id),
        "hits": hits,
        "barcode_gap": {"intra_max_distance": 0.009, "inter_min_distance": 0.018},
        "diagnostic": {
            "diagnostic_kmers": ["ACGTTGACCTAGGCT", "TGACCTAGGCTTACG", "GCTTACGATCGTACC"],
            "reference_total_windows": 5_000_000,
            "epsilon": 0.01,
        },
    }


GOOD_RECORD = sequence_record(
    "AALB-COI-good",
    [
        top_hit(99.6, 96),
        top_hit(98.2, 95, taxon="Aedes aegypti", lineage=AEDES_AEGYPTI_LINEAGE),
    ],
)


AMBIGUOUS_RECORD = sequence_record(
    "AALB-COI-ambiguous",
    [
        top_hit(99.4, 96),
        top_hit(99.3, 96, taxon="Aedes aegypti", lineage=AEDES_AEGYPTI_LINEAGE),
    ],
)


WEAK_RECORD = sequence_record(
    "AALB-COI-short",
    [
        top_hit(99.5, 72),
    ],
)


MISSING_METADATA_RECORD = sequence_record(
    "AALB-COI-metadata-gap",
    [top_hit(99.6, 96)],
    metadata={
        "basisOfRecord": "MaterialSample",
        "scientificName": "Aedes albopictus",
        "countryCode": "ES",
        "methodOrSOP": "GBIF Sequence ID-compatible COI BLAST workflow; ruleset barcode-gbif-compiler-v2",
    },
)


def request_with_records(title: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "project_title": title,
        "marker": "COI-5P",
        "reference_database": "COI Animals / BOLD public clustered reference",
        "method_or_sop": "GBIF Sequence ID-compatible BLAST workflow with deterministic rank gates",
        "ruleset_version": "barcode-gbif-compiler-v2",
        "records": deepcopy(records),
    }


BARCODE_DEMO_SCENARIOS = [
    {
        "id": "aedes-good",
        "label": "Species-safe Aedes",
        "description": "All molecular and GBIF-readiness gates pass.",
        "request": request_with_records("Aedes albopictus species-safe COI record", [GOOD_RECORD]),
    },
    {
        "id": "aedes-ambiguous",
        "label": "Ambiguous top hits",
        "description": "Top and competitor are statistically indistinguishable, so safe rank is genus.",
        "request": request_with_records("Aedes ambiguous COI assignment", [AMBIGUOUS_RECORD]),
    },
    {
        "id": "aedes-metadata-gap",
        "label": "Taxon safe, publication blocked",
        "description": "Molecular evidence passes, but occurrenceID/eventDate are missing.",
        "request": request_with_records("Aedes COI record with missing GBIF metadata", [MISSING_METADATA_RECORD]),
    },
    {
        "id": "aedes-weak",
        "label": "Weak coverage",
        "description": "High identity with short coverage is blocked from species-level publication.",
        "request": request_with_records("Aedes short-fragment weak coverage check", [WEAK_RECORD]),
    },
    {
        "id": "mixed-batch",
        "label": "Mixed batch",
        "description": "One run showing species-safe, genus-safe, weak and not-publishable outcomes.",
        "request": request_with_records(
            "Aedes COI batch: safe, ambiguous, weak and metadata cases",
            [GOOD_RECORD, AMBIGUOUS_RECORD, WEAK_RECORD, MISSING_METADATA_RECORD],
        ),
    },
]


DEFAULT_BARCODE_REQUEST = BARCODE_DEMO_SCENARIOS[-1]["request"]
