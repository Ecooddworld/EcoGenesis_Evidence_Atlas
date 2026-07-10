from __future__ import annotations

from copy import deepcopy
from typing import Any


BASE_SEQUENCE = (
    "AACATTATACTTTATTTTCGGTATTTGATCTGGAATAGTCGGAACTTCACTAAGAGTTTTAGTTCGTATTGAACTTAGACATCCTGGTATATTTATTGGA"
    "AATGATCAAATTTATAATGTAATTGTTACTGCTCATGCTTTTATTATAATTTTTTTTATAGTAATACCTATCATAATTGGAGGATTTGGAAACTGACTAG"
    "TACCCTTAATACTAGGAGCCCCTGATATAGCTTTTCCTCGAATAAATAATATAAGTTTTTGAATATTACCCCCCTCTTTAACACTGCTGCTTTCTAGTTC"
    "TATAGTAGAAAACGGAGCTGGAACAGGGTGAACGGTTTATCCTCCTCTTTCTTCTAGAACAGCTCATGCTGGGGCTTCAGTTGATTTAGCAATTTTTTCT"
    "TTACATTTAGCGGGAATCTCATCTATTTTAGGAGCAGTAAATTTTATTACAACTGTAATTAATATACGATCAGCTGGTATTACTCTTGATCGACTACCTT"
    "TATTTGTGTGATCAGTAGTAATTACAGCTATTTTATTACTTCTTTCTCTACCCGTATTAGCCGGAGCTATTACTATATTATTAACAGACCGAAATTTAAA"
    "TACATCTTTTTTTGATCCAATTGGAGGGGGAGACCCTATTTTATATCAACATTTATTT"
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
        "barcode_gap": {
            "intra_max_distance": 0.009,
            "inter_min_distance": 0.018,
            "target_reference_count": 12,
            "target_specimen_count": 12,
            "intra_pair_count": 66,
            "inter_taxon_count": 4,
            "inter_reference_count": 30,
            "inter_pair_count": 360,
            "distance_method": "global_alignment_needleman_wunsch_edit_p_distance_v1",
            "minimum_aligned_sites": 600,
            "gap_ci_lower": 0.004,
            "gap_ci_upper": 0.014,
            "bootstrap_replicates": 1000,
            "bootstrap_method": "stratified specimen bootstrap regression fixture",
        },
        "diagnostic": {
            "diagnostic_kmers": ["AACATTATACTTTAT", "ACTTTATTTTCGGTA", "CGGAACTTCACTAAG"],
            "reference_total_windows": 5_000_000,
            "epsilon": 0.01,
            "target_sequence_count": 12,
            "negative_taxon_count": 4,
            "negative_sequence_count": 30,
            "conservation_fraction": 1.0,
            "canonicalized": True,
            "reverse_complement_checked": True,
            "background_scope": "synthetic regression fixture; informational only and not externally audited",
        },
        "reference_completeness": {
            "status": "not_evaluated",
            "target_taxon_reference_count": 12,
            "target_taxon_specimen_count": 12,
            "close_relative_taxa_expected": 4,
            "close_relative_taxa_represented": 4,
            "negative_reference_taxa_count": 4,
            "negative_reference_sequence_count": 30,
            "geographic_regions_count": 3,
            "audit_source": "synthetic regression fixture; informational only, unsigned and not external validation",
            "audit_sha256": None,
            "notes": "Deliberately unsigned: the built-in demo cannot unlock a scientific species gate.",
        },
        "sequence_qc": {
            "chimera_status": "pass",
            "chimera_method": "synthetic regression-fixture assertion",
            "chimera_reference_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "supplied_orientation": "forward",
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
        "label": "Synthetic Aedes candidate",
        "description": "Internal regression evidence only; unsigned reference completeness keeps scientific release and GBIF use blocked.",
        "request": request_with_records("Unsigned synthetic Aedes regression candidate", [GOOD_RECORD]),
    },
    {
        "id": "aedes-ambiguous",
        "label": "Ambiguous top hits",
        "description": "Top and competitor are statistically indistinguishable, so safe rank is genus.",
        "request": request_with_records("Aedes ambiguous COI assignment", [AMBIGUOUS_RECORD]),
    },
    {
        "id": "aedes-metadata-gap",
        "label": "Evidence and metadata gaps",
        "description": "Unsigned synthetic reference evidence and missing occurrenceID/eventDate both block downstream use.",
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
        "description": "Synthetic regression cases remain informational: unsigned completeness, ambiguity, weak coverage and metadata gaps are visible.",
        "request": request_with_records(
            "Aedes COI synthetic batch: unsigned, ambiguous, weak and metadata cases",
            [GOOD_RECORD, AMBIGUOUS_RECORD, WEAK_RECORD, MISSING_METADATA_RECORD],
        ),
    },
]


DEFAULT_BARCODE_REQUEST = BARCODE_DEMO_SCENARIOS[-1]["request"]
