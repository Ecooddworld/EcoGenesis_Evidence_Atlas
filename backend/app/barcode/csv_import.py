from __future__ import annotations

import csv
import io
import re
from typing import Any

from pydantic import ValidationError

from .schemas import (
    BarcodeCompilerRequest,
    BarcodeGapEvidence,
    DiagnosticKmerEvidence,
    ReferenceHit,
    SequenceRecord,
    TaxonLineageItem,
)


CSV_REQUIRED_COLUMNS = ["sequenceID", "sequence"]
CSV_STRONGLY_RECOMMENDED_COLUMNS = [
    "occurrenceID",
    "eventID",
    "materialSampleID",
    "basisOfRecord",
    "scientificName",
    "eventDate",
    "marker",
    "referenceDatabase",
    "methodOrSOP",
]
METADATA_FIELDS = [
    "occurrenceID",
    "basisOfRecord",
    "scientificName",
    "eventDate",
    "marker",
    "referenceDatabase",
    "methodOrSOP",
    "countryCode",
    "decimalLatitude",
    "decimalLongitude",
    "geodeticDatum",
    "coordinateUncertaintyInMeters",
    "eventID",
    "materialSampleID",
    "assayType",
    "occurrenceStatus",
    "organismQuantity",
    "organismQuantityType",
    "DNA_sequence",
    "target_gene",
    "target_subfragment",
    "pcr_primer_forward",
    "pcr_primer_reverse",
    "seq_meth",
    "otu_class_appr",
    "otu_seq_comp_appr",
    "otu_db",
    "sop",
    "contaminationAssessment",
    "experimentalVariance",
    "quantificationCycle",
    "estimatedNumberOfCopies",
    "readCount",
    "totalReads",
]
DNA_ALPHABET = set("ACGTRYSWKMBDHVN- \t\r\n")

CSV_TEMPLATE_TEXT = """sequenceID,sequence,occurrenceID,eventID,materialSampleID,basisOfRecord,scientificName,eventDate,marker,assayType,referenceDatabase,methodOrSOP,target_gene,target_subfragment,pcr_primer_forward,pcr_primer_reverse,seq_meth,contaminationAssessment,topTaxon,topIdentity,topCoverage,topRank,topAlignedLength,secondTaxon,secondIdentity,secondCoverage,secondRank,secondAlignedLength,barcodeIntraMax,barcodeInterMin,diagnosticKmers
AALB-COI-good,ACGTTGACCTAGGCTTACGATCGTACCGATGCTAGCTAGGATCCGATCGTACGATCGTAGCTAGCATCG,urn:example:AALB-COI-good,event-aedes-001,sample-aedes-001,MaterialSample,Aedes albopictus,2026-04-18,COI-5P,single_specimen_barcode,COI Animals / BOLD public clustered reference,GBIF Sequence ID-compatible BLAST workflow,cytochrome c oxidase subunit I,COI-5P barcode region,GGWACWGGWTGAACWGTWTAYCCYCC,TAIACYTCIGGRTGICCRAARAAYCA,Illumina MiSeq,no contamination detected,Aedes albopictus,99.6,96,species,658,Aedes aegypti,98.2,95,species,625,0.009,0.018,ACGTTGACCTAGGCT|TGACCTAGGCTTACG
"""


ALIASES: dict[str, list[str]] = {
    "sequenceID": ["sequenceID", "sequenceId", "sequence_id", "id", "queryID", "queryId", "occurrenceId", "occurrenceID"],
    "sequence": ["sequence", "dnaSequence", "nucleotideSequence", "querySequence"],
    "occurrenceID": ["occurrenceID", "occurrenceId", "occurrence_id"],
    "eventID": ["eventID", "eventId", "event_id"],
    "materialSampleID": ["materialSampleID", "materialSampleId", "material_sample_id", "sampleID", "sampleId"],
    "basisOfRecord": ["basisOfRecord", "basis_of_record"],
    "scientificName": ["scientificName", "scientific_name"],
    "eventDate": ["eventDate", "event_date", "date"],
    "marker": ["marker", "gene", "locus"],
    "referenceDatabase": ["referenceDatabase", "reference_database", "database", "db"],
    "methodOrSOP": ["methodOrSOP", "method_or_sop", "method", "sop"],
    "countryCode": ["countryCode", "country_code"],
    "decimalLatitude": ["decimalLatitude", "decimal_latitude", "lat", "latitude"],
    "decimalLongitude": ["decimalLongitude", "decimal_longitude", "lon", "lng", "longitude"],
    "geodeticDatum": ["geodeticDatum", "geodetic_datum", "datum"],
    "coordinateUncertaintyInMeters": [
        "coordinateUncertaintyInMeters",
        "coordinate_uncertainty_in_meters",
        "coordinateUncertainty",
        "uncertaintyMeters",
    ],
    "assayType": ["assayType", "assay_type", "assay", "workflowType"],
    "occurrenceStatus": ["occurrenceStatus", "occurrence_status"],
    "organismQuantity": ["organismQuantity", "organism_quantity"],
    "organismQuantityType": ["organismQuantityType", "organism_quantity_type"],
    "DNA_sequence": ["DNA_sequence", "dna_sequence", "dnaSequence", "sequence"],
    "target_gene": ["target_gene", "targetGene", "target gene"],
    "target_subfragment": ["target_subfragment", "targetSubfragment", "target_sub_fragment", "targetRegion"],
    "pcr_primer_forward": ["pcr_primer_forward", "pcrPrimerForward", "forwardPrimer", "primerForward"],
    "pcr_primer_reverse": ["pcr_primer_reverse", "pcrPrimerReverse", "reversePrimer", "primerReverse"],
    "seq_meth": ["seq_meth", "seqMeth", "sequencingMethod", "sequencing_method"],
    "otu_class_appr": ["otu_class_appr", "otuClassAppr", "classificationApproach"],
    "otu_seq_comp_appr": ["otu_seq_comp_appr", "otuSeqCompAppr", "sequenceComparisonApproach"],
    "otu_db": ["otu_db", "otuDb", "referenceDatabase", "reference_database", "database", "db"],
    "sop": ["sop", "SOP", "methodOrSOP", "method_or_sop"],
    "contaminationAssessment": ["contaminationAssessment", "contamination_assessment", "negativeControlStatus"],
    "experimentalVariance": ["experimentalVariance", "experimental_variance"],
    "quantificationCycle": ["quantificationCycle", "cq", "ct", "Cq", "Ct"],
    "estimatedNumberOfCopies": ["estimatedNumberOfCopies", "estimated_number_of_copies", "copies"],
    "readCount": ["readCount", "read_count", "reads"],
    "totalReads": ["totalReads", "total_reads"],
    "topTaxon": ["topTaxon", "top_taxon", "hitTaxon", "hit_taxon", "referenceTaxon", "subjectTaxon", "matchedTaxon", "bestTaxon", "taxon", "scientificName"],
    "topIdentity": ["topIdentity", "top_identity", "hitIdentity", "hit_identity", "identity", "percentIdentity", "pident"],
    "topCoverage": ["topCoverage", "top_coverage", "hitCoverage", "hit_coverage", "queryCoverage", "query_coverage", "coverage", "qcov"],
    "topRank": ["topRank", "top_rank", "hitRank", "hit_rank", "rank", "taxonRank"],
    "topAlignedLength": ["topAlignedLength", "top_aligned_length", "hitAlignedLength", "hit_aligned_length", "alignedLength", "alignmentLength"],
    "topBitScore": ["topBitScore", "hitBitScore", "hit_bit_score", "bitScore", "bitscore"],
    "topEvalue": ["topEvalue", "hitEvalue", "hit_evalue", "evalue", "eValue"],
    "topReferenceId": ["topReferenceId", "hitReferenceId", "hit_reference_id", "referenceId", "subjectID", "subjectId"],
    "topGbifTaxonKey": ["topGbifTaxonKey", "hitGbifTaxonKey", "hit_gbif_taxon_key", "gbifTaxonKey", "usageKey", "taxonKey"],
    "secondTaxon": ["secondTaxon", "second_taxon", "competitorTaxon", "nextTaxon"],
    "secondIdentity": ["secondIdentity", "second_identity", "competitorIdentity", "nextIdentity"],
    "secondCoverage": ["secondCoverage", "second_coverage", "competitorCoverage", "nextCoverage"],
    "secondRank": ["secondRank", "second_rank", "competitorRank", "nextRank"],
    "secondAlignedLength": [
        "secondAlignedLength",
        "second_aligned_length",
        "competitorAlignedLength",
        "nextAlignedLength",
    ],
    "secondBitScore": ["secondBitScore", "competitorBitScore", "nextBitScore"],
    "secondEvalue": ["secondEvalue", "competitorEvalue", "nextEvalue"],
    "secondReferenceId": ["secondReferenceId", "competitorReferenceId", "nextReferenceId"],
    "secondGbifTaxonKey": ["secondGbifTaxonKey", "competitorGbifTaxonKey", "nextGbifTaxonKey"],
    "barcodeIntraMax": ["barcodeIntraMax", "barcode_intra_max", "intraMaxDistance", "intraMax"],
    "barcodeInterMin": ["barcodeInterMin", "barcode_inter_min", "interMinDistance", "interMin"],
    "diagnosticKmers": ["diagnosticKmers", "diagnostic_kmers", "diagnosticKmer"],
    "matchType": ["matchType", "match_type"],
}


def parse_barcode_csv(
    text: str,
    *,
    project_title: str | None = None,
    marker: str | None = None,
    reference_database: str | None = None,
    method_or_sop: str | None = None,
) -> dict[str, Any]:
    raw_rows, headers = read_csv_rows(text)
    errors: list[str] = []
    warnings: list[str] = []

    if not headers:
        return empty_result(error="CSV has no header row.")

    header_lookup = {normalize_header(header): header for header in headers if header is not None}
    missing_required_columns = [name for name in CSV_REQUIRED_COLUMNS if not has_column(header_lookup, name)]
    if missing_required_columns:
        errors.append(f"Missing required columns: {', '.join(missing_required_columns)}.")

    normalized_preview = [normalized_preview_row(row, header_lookup) for row in raw_rows[:10]]
    missing_recommended_fields = {name: 0 for name in CSV_STRONGLY_RECOMMENDED_COLUMNS}
    invalid_sequence_count = 0
    weak_or_no_hit_count = 0
    no_hit_count = 0
    records_by_sequence_id: dict[str, SequenceRecord] = {}

    if errors:
        return build_import_result(
            request=None,
            preview_rows=normalized_preview,
            records_found=len(raw_rows),
            missing_required_columns=missing_required_columns,
            missing_recommended_fields=missing_recommended_fields,
            invalid_sequence_count=invalid_sequence_count,
            weak_or_no_hit_count=weak_or_no_hit_count,
            no_hit_count=no_hit_count,
            warnings=warnings,
            errors=errors,
        )

    for index, row in enumerate(raw_rows, start=2):
        row_errors: list[str] = []
        sequence_id = value_for(row, header_lookup, "sequenceID")
        sequence = value_for(row, header_lookup, "sequence")
        if not sequence_id:
            row_errors.append(f"Row {index}: missing sequenceID value.")
        if not sequence:
            row_errors.append(f"Row {index}: missing sequence value.")
        if sequence and has_invalid_sequence_characters(sequence):
            invalid_sequence_count += 1
            row_errors.append(f"Row {index}: sequence contains unsupported DNA/IUPAC characters.")

        metadata = metadata_for_row(row, header_lookup)
        if marker and not metadata.get("marker"):
            metadata["marker"] = marker
        if reference_database and not metadata.get("referenceDatabase"):
            metadata["referenceDatabase"] = reference_database
        if method_or_sop and not metadata.get("methodOrSOP"):
            metadata["methodOrSOP"] = method_or_sop

        for field in CSV_STRONGLY_RECOMMENDED_COLUMNS:
            if not metadata.get(field):
                missing_recommended_fields[field] += 1

        hits = hits_for_row(row, header_lookup)
        if not hits:
            no_hit_count += 1
            weak_or_no_hit_count += 1
        elif is_weak_hit(hits[0]):
            weak_or_no_hit_count += 1

        errors.extend(row_errors)
        if sequence_id and sequence and not row_errors:
            new_record = SequenceRecord(
                sequence_id=sequence_id,
                sequence=sequence,
                metadata=metadata,
                hits=hits,
                barcode_gap=barcode_gap_for_row(row, header_lookup),
                diagnostic=diagnostic_for_row(row, header_lookup),
            )
            existing = records_by_sequence_id.get(sequence_id)
            if existing:
                if existing.sequence != new_record.sequence:
                    errors.append(f"Row {index}: duplicate sequenceID {sequence_id} has a different sequence value.")
                    continue
                merge_sequence_record(existing, new_record)
            else:
                records_by_sequence_id[sequence_id] = new_record

    missing_recommended_fields = {key: count for key, count in missing_recommended_fields.items() if count}
    records = list(records_by_sequence_id.values())
    if len(records) < len(raw_rows) and not errors:
        warnings.append(
            f"Detected long-format hit table: {len(raw_rows)} CSV row(s) were grouped into {len(records)} sequence record(s)."
        )
    if no_hit_count:
        warnings.append(f"{no_hit_count} row(s) have no reference hit metrics; they will compile as no-match/review.")
    if weak_or_no_hit_count:
        warnings.append(f"{weak_or_no_hit_count} row(s) are weak or no-hit and cannot become species-safe.")
    if missing_recommended_fields:
        warnings.append("Some strongly recommended GBIF/DNA fields are missing; publication readiness may be blocked.")

    request = None
    if not errors:
        try:
            request = BarcodeCompilerRequest(
                project_title=project_title or "Uploaded molecular evidence CSV",
                marker=marker or first_non_empty([record.metadata.get("marker") for record in records]) or "COI-5P",
                reference_database=reference_database
                or first_non_empty([record.metadata.get("referenceDatabase") for record in records])
                or "User-supplied reference-hit results",
                method_or_sop=method_or_sop
                or first_non_empty([record.metadata.get("methodOrSOP") for record in records])
                or "User-supplied Sequence ID / BLAST-style CSV results",
                records=records,
            )
        except ValidationError as exc:
            errors.extend(format_validation_errors(exc))

    return build_import_result(
        request=request,
        preview_rows=normalized_preview,
        records_found=len(raw_rows),
        missing_required_columns=missing_required_columns,
        missing_recommended_fields=missing_recommended_fields,
        invalid_sequence_count=invalid_sequence_count,
        weak_or_no_hit_count=weak_or_no_hit_count,
        no_hit_count=no_hit_count,
        warnings=warnings,
        errors=errors,
    )


def read_csv_rows(text: str) -> tuple[list[dict[str, str]], list[str]]:
    stream = io.StringIO(text.lstrip("\ufeff"))
    reader = csv.DictReader(stream)
    headers = list(reader.fieldnames or [])
    return [dict(row) for row in reader], headers


def empty_result(*, error: str) -> dict[str, Any]:
    return build_import_result(
        request=None,
        preview_rows=[],
        records_found=0,
        missing_required_columns=CSV_REQUIRED_COLUMNS,
        missing_recommended_fields={},
        invalid_sequence_count=0,
        weak_or_no_hit_count=0,
        no_hit_count=0,
        warnings=[],
        errors=[error],
    )


def build_import_result(
    *,
    request: BarcodeCompilerRequest | None,
    preview_rows: list[dict[str, Any]],
    records_found: int,
    missing_required_columns: list[str],
    missing_recommended_fields: dict[str, int],
    invalid_sequence_count: int,
    weak_or_no_hit_count: int,
    no_hit_count: int,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    validation = {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "records_found": records_found,
        "missing_required_columns": missing_required_columns,
        "missing_recommended_fields": missing_recommended_fields,
        "invalid_sequence_count": invalid_sequence_count,
        "weak_or_no_hit_count": weak_or_no_hit_count,
        "no_hit_count": no_hit_count,
    }
    return {
        "request": request.model_dump() if request else None,
        "preview_rows": preview_rows,
        "validation": validation,
    }


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def has_column(header_lookup: dict[str, str], canonical: str) -> bool:
    return any(normalize_header(alias) in header_lookup for alias in ALIASES[canonical])


def value_for(row: dict[str, Any], header_lookup: dict[str, str], canonical: str) -> str:
    for alias in ALIASES[canonical]:
        header = header_lookup.get(normalize_header(alias))
        if header is None:
            continue
        value = row.get(header)
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return ""


def normalized_preview_row(row: dict[str, Any], header_lookup: dict[str, str]) -> dict[str, Any]:
    fields = [
        "sequenceID",
        "scientificName",
        "eventDate",
        "marker",
        "assayType",
        "topTaxon",
        "topIdentity",
        "topCoverage",
        "secondTaxon",
        "barcodeIntraMax",
        "barcodeInterMin",
    ]
    return {field: value_for(row, header_lookup, field) for field in fields}


def metadata_for_row(row: dict[str, Any], header_lookup: dict[str, str]) -> dict[str, Any]:
    metadata = {}
    for field in METADATA_FIELDS:
        value = value_for(row, header_lookup, field)
        if value:
            metadata[field] = value
    return metadata


def merge_sequence_record(existing: SequenceRecord, new_record: SequenceRecord) -> None:
    for key, value in new_record.metadata.items():
        if value and not existing.metadata.get(key):
            existing.metadata[key] = value
    seen_hits = {hit_key(hit) for hit in existing.hits}
    for hit in new_record.hits:
        key = hit_key(hit)
        if key not in seen_hits:
            existing.hits.append(hit)
            seen_hits.add(key)
    if existing.barcode_gap is None and new_record.barcode_gap is not None:
        existing.barcode_gap = new_record.barcode_gap
    if existing.diagnostic is None and new_record.diagnostic is not None:
        existing.diagnostic = new_record.diagnostic
    elif existing.diagnostic is not None and new_record.diagnostic is not None:
        merged = list(dict.fromkeys([*existing.diagnostic.diagnostic_kmers, *new_record.diagnostic.diagnostic_kmers]))
        existing.diagnostic.diagnostic_kmers = merged


def hit_key(hit: ReferenceHit) -> tuple[Any, ...]:
    return (
        hit.reference_id,
        hit.taxon,
        hit.rank,
        round(hit.identity, 6),
        round(hit.query_coverage, 6),
    )


def hits_for_row(row: dict[str, Any], header_lookup: dict[str, str]) -> list[ReferenceHit]:
    hits = []
    top = reference_hit_for_row(row, header_lookup, prefix="top", fallback_rank=value_for(row, header_lookup, "topRank") or "species")
    if top:
        hits.append(top)
    second = reference_hit_for_row(row, header_lookup, prefix="second", fallback_rank=value_for(row, header_lookup, "secondRank") or top.rank if top else "species")
    if second:
        hits.append(second)
    return hits


def reference_hit_for_row(
    row: dict[str, Any],
    header_lookup: dict[str, str],
    *,
    prefix: str,
    fallback_rank: str,
) -> ReferenceHit | None:
    taxon = value_for(row, header_lookup, f"{prefix}Taxon")
    identity = parse_float(value_for(row, header_lookup, f"{prefix}Identity"))
    coverage = parse_float(value_for(row, header_lookup, f"{prefix}Coverage"))
    if not taxon or identity is None or coverage is None:
        return None
    rank = value_for(row, header_lookup, f"{prefix}Rank") or fallback_rank or "species"
    return ReferenceHit(
        taxon=taxon,
        rank=rank.lower(),
        identity=identity,
        query_coverage=coverage,
        aligned_length=parse_int(value_for(row, header_lookup, f"{prefix}AlignedLength")),
        bit_score=parse_float(value_for(row, header_lookup, f"{prefix}BitScore")),
        evalue=parse_float(value_for(row, header_lookup, f"{prefix}Evalue")),
        reference_id=value_for(row, header_lookup, f"{prefix}ReferenceId") or None,
        reference_database=value_for(row, header_lookup, "referenceDatabase") or None,
        gbif_taxon_key=parse_int(value_for(row, header_lookup, f"{prefix}GbifTaxonKey")),
        lineage=inferred_lineage(taxon, rank),
    )


def inferred_lineage(taxon: str, rank: str) -> list[TaxonLineageItem]:
    normalized_rank = str(rank or "species").strip().lower()
    words = [part for part in taxon.split() if part]
    if normalized_rank == "species" and len(words) >= 2:
        genus = words[0]
        return [
            TaxonLineageItem(rank="genus", name=genus),
            TaxonLineageItem(rank="species", name=" ".join(words[:2])),
        ]
    if normalized_rank == "genus":
        return [TaxonLineageItem(rank="genus", name=taxon)]
    return [TaxonLineageItem(rank=normalized_rank, name=taxon)]


def barcode_gap_for_row(row: dict[str, Any], header_lookup: dict[str, str]) -> BarcodeGapEvidence | None:
    intra = parse_float(value_for(row, header_lookup, "barcodeIntraMax"))
    inter = parse_float(value_for(row, header_lookup, "barcodeInterMin"))
    if intra is None and inter is None:
        return None
    return BarcodeGapEvidence(intra_max_distance=intra, inter_min_distance=inter)


def diagnostic_for_row(row: dict[str, Any], header_lookup: dict[str, str]) -> DiagnosticKmerEvidence | None:
    raw = value_for(row, header_lookup, "diagnosticKmers")
    if not raw:
        return None
    kmers = [item.strip().upper() for item in raw.split("|") if item.strip()]
    return DiagnosticKmerEvidence(diagnostic_kmers=kmers)


def parse_float(value: str) -> float | None:
    if not value:
        return None
    try:
        return float(str(value).replace("%", "").strip())
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def has_invalid_sequence_characters(value: str) -> bool:
    return any(char.upper() not in DNA_ALPHABET for char in value)


def is_weak_hit(hit: ReferenceHit) -> bool:
    return hit.identity < 90 or hit.query_coverage < 80


def first_non_empty(values: list[Any]) -> str | None:
    for value in values:
        if value is not None and str(value).strip() != "":
            return str(value).strip()
    return None


def format_validation_errors(exc: ValidationError) -> list[str]:
    formatted = []
    for item in exc.errors():
        location = ".".join(str(part) for part in item.get("loc", []))
        formatted.append(f"{location}: {item.get('msg', 'validation failed')}")
    return formatted
