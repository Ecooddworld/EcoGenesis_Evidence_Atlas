from __future__ import annotations

from typing import Any

from .schemas import BarcodeCompilerRequest, ReferenceHit, SequenceRecord


MARKER_PROFILES: dict[str, dict[str, Any]] = {
    "coi_full_barcode": {
        "id": "coi_full_barcode",
        "label": "COI full barcode / COI-5P",
        "marker_family": "COI",
        "identity_species_min": 99.0,
        "coverage_species_min": 80.0,
        "identity_close_min": 90.0,
        "coverage_close_min": 80.0,
        "min_aligned_length": 500,
        "max_aligned_length": 800,
        "species_claim_allowed": True,
        "coding_marker": True,
        "target_gene": "cytochrome c oxidase subunit I",
        "target_subfragment": "COI-5P barcode region",
        "claim_caveat": "Species claims still require ambiguity/LCA, barcode-gap and diagnostic k-mer gates.",
    },
    "coi_mini_barcode": {
        "id": "coi_mini_barcode",
        "label": "COI mini-barcode",
        "marker_family": "COI",
        "identity_species_min": 99.0,
        "coverage_species_min": 95.0,
        "identity_close_min": 95.0,
        "coverage_close_min": 80.0,
        "min_aligned_length": 60,
        "max_aligned_length": 350,
        "species_claim_allowed": True,
        "coding_marker": True,
        "target_gene": "cytochrome c oxidase subunit I",
        "target_subfragment": "COI mini-barcode fragment",
        "claim_caveat": "Mini-barcodes require stronger coverage and explicit reference/diagnostic evidence.",
    },
    "its_fungi": {
        "id": "its_fungi",
        "label": "ITS fungal barcode",
        "marker_family": "ITS",
        "identity_species_min": 98.5,
        "coverage_species_min": 85.0,
        "identity_close_min": 90.0,
        "coverage_close_min": 80.0,
        "min_aligned_length": 120,
        "max_aligned_length": 900,
        "species_claim_allowed": True,
        "coding_marker": False,
        "target_gene": "internal transcribed spacer",
        "target_subfragment": "ITS barcode region",
        "claim_caveat": "ITS is not translated as protein; species output depends on reference coverage and curation.",
    },
    "s16_full_or_near_full": {
        "id": "s16_full_or_near_full",
        "label": "16S full or near-full marker",
        "marker_family": "16S",
        "identity_species_min": 99.5,
        "coverage_species_min": 90.0,
        "identity_close_min": 97.0,
        "coverage_close_min": 80.0,
        "min_aligned_length": 900,
        "max_aligned_length": 1800,
        "species_claim_allowed": True,
        "coding_marker": False,
        "target_gene": "16S rRNA",
        "target_subfragment": "16S full or near-full region",
        "claim_caveat": "16S species claims are conservative and require reference-library caveats.",
    },
    "s16_short_amplicon": {
        "id": "s16_short_amplicon",
        "label": "16S short amplicon",
        "marker_family": "16S",
        "identity_species_min": 99.5,
        "coverage_species_min": 95.0,
        "identity_close_min": 97.0,
        "coverage_close_min": 80.0,
        "min_aligned_length": 80,
        "max_aligned_length": 600,
        "species_claim_allowed": False,
        "coding_marker": False,
        "target_gene": "16S rRNA",
        "target_subfragment": "short 16S amplicon",
        "claim_caveat": "Short 16S amplicons are treated as safe-rank evidence, not automatic species evidence.",
    },
    "custom_research": {
        "id": "custom_research",
        "label": "Custom research marker",
        "marker_family": "custom",
        "identity_species_min": 99.0,
        "coverage_species_min": 80.0,
        "identity_close_min": 90.0,
        "coverage_close_min": 80.0,
        "min_aligned_length": 1,
        "max_aligned_length": None,
        "species_claim_allowed": False,
        "coding_marker": False,
        "target_gene": "custom marker",
        "target_subfragment": "user supplied marker",
        "claim_caveat": "Custom markers require an explicit profile before species-level export is allowed.",
    },
}


ASSAY_PROFILES: dict[str, dict[str, Any]] = {
    "single_specimen_barcode": {
        "id": "single_specimen_barcode",
        "label": "Single-specimen barcode",
        "required_fields": [],
        "recommended_fields": ["eventID", "materialSampleID", "pcr_primer_forward", "pcr_primer_reverse", "seq_meth"],
        "publication_blocking": False,
        "claim_caveat": "The record is interpreted as sequence-derived occurrence evidence, not direct ecological abundance.",
    },
    "metabarcoding": {
        "id": "metabarcoding",
        "label": "Metabarcoding / eDNA batch",
        "required_fields": [],
        "recommended_fields": [
            "eventID",
            "materialSampleID",
            "readCount",
            "totalReads",
            "pcr_primer_forward",
            "pcr_primer_reverse",
            "contaminationAssessment",
            "methodOrSOP",
        ],
        "publication_blocking": False,
        "claim_caveat": "Without controls and replicate/QC metadata, detections remain molecular evidence, not confirmed living presence.",
    },
    "qpcr_ddpcr": {
        "id": "qpcr_ddpcr",
        "label": "Targeted qPCR / ddPCR detection",
        "required_fields": ["occurrenceStatus", "contaminationAssessment", "methodOrSOP"],
        "recommended_fields": [
            "eventID",
            "materialSampleID",
            "experimentalVariance",
            "quantificationCycle",
            "estimatedNumberOfCopies",
            "pcr_primer_forward",
            "pcr_primer_reverse",
        ],
        "publication_blocking": True,
        "claim_caveat": "Targeted detections require explicit occurrenceStatus and contamination/control evidence.",
    },
    "custom_targeted": {
        "id": "custom_targeted",
        "label": "Custom targeted assay",
        "required_fields": ["methodOrSOP"],
        "recommended_fields": ["eventID", "materialSampleID", "contaminationAssessment"],
        "publication_blocking": False,
        "claim_caveat": "Custom targeted assays need a supplied SOP and external validation for formal claims.",
    },
    "unknown": {
        "id": "unknown",
        "label": "Unknown assay",
        "required_fields": [],
        "recommended_fields": ["eventID", "materialSampleID", "methodOrSOP"],
        "publication_blocking": False,
        "claim_caveat": "Assay type was not supplied; ecological and monitoring claims require review.",
    },
}


DNA_EXTENSION_HIGH_PRIORITY_FIELDS = [
    "eventID",
    "materialSampleID",
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
]


def select_marker_profile(
    request: BarcodeCompilerRequest,
    record: SequenceRecord,
    top_hit: ReferenceHit | None,
) -> dict[str, Any]:
    if request.marker_profile and request.marker_profile in MARKER_PROFILES:
        return dict(MARKER_PROFILES[request.marker_profile])
    marker = str(record.metadata.get("marker") or request.marker or "").lower()
    span = aligned_span(record, top_hit)
    if "coi" in marker or "cox1" in marker:
        return dict(MARKER_PROFILES["coi_mini_barcode" if span < 350 else "coi_full_barcode"])
    if "its" in marker:
        return dict(MARKER_PROFILES["its_fungi"])
    if "16s" in marker or "rrs" in marker:
        return dict(MARKER_PROFILES["s16_short_amplicon" if span < 600 else "s16_full_or_near_full"])
    return dict(MARKER_PROFILES["custom_research"])


def aligned_span(record: SequenceRecord, top_hit: ReferenceHit | None) -> int:
    return int(top_hit.aligned_length or len(record.sequence) or 0) if top_hit else len(record.sequence)


def marker_profile_readiness(
    request: BarcodeCompilerRequest,
    record: SequenceRecord,
    top_hit: ReferenceHit | None,
) -> dict[str, Any]:
    profile = select_marker_profile(request, record, top_hit)
    span = aligned_span(record, top_hit)
    min_len = profile.get("min_aligned_length") or 1
    max_len = profile.get("max_aligned_length")
    length_pass = span >= min_len and (max_len is None or span <= max_len)
    species_gate_pass = bool(profile["species_claim_allowed"]) and length_pass
    blockers: list[str] = []
    warnings: list[str] = []
    if not length_pass:
        blockers.append(f"marker profile blocked species claim: aligned length {span} outside {min_len}-{max_len or 'open'} bp for {profile['id']}")
    if not profile["species_claim_allowed"]:
        blockers.append(f"marker profile blocked species claim: {profile['id']} is configured for safe-rank review, not automatic species export")
    if len(record.sequence) < span:
        warnings.append("input sequence is shorter than supplied aligned_length; length gates use the supplied alignment span")
    return {
        "profile_id": profile["id"],
        "profile_label": profile["label"],
        "marker_family": profile["marker_family"],
        "coding_marker": profile["coding_marker"],
        "target_gene": profile["target_gene"],
        "target_subfragment": profile["target_subfragment"],
        "identity_species_min": profile["identity_species_min"],
        "coverage_species_min": profile["coverage_species_min"],
        "identity_close_min": profile["identity_close_min"],
        "coverage_close_min": profile["coverage_close_min"],
        "aligned_span": span,
        "min_aligned_length": min_len,
        "max_aligned_length": max_len,
        "length_pass": length_pass,
        "species_claim_allowed": bool(profile["species_claim_allowed"]),
        "species_gate_pass": species_gate_pass,
        "profile_blockers": blockers,
        "profile_warnings": warnings,
        "claim_caveat": profile["claim_caveat"],
    }


def assay_type_for(request: BarcodeCompilerRequest, metadata: dict[str, Any]) -> str:
    raw = str(metadata.get("assayType") or request.assay_type or "single_specimen_barcode").strip().lower()
    normalized = raw.replace("-", "_").replace(" ", "_")
    aliases = {
        "single": "single_specimen_barcode",
        "barcode": "single_specimen_barcode",
        "single_specimen": "single_specimen_barcode",
        "edna": "metabarcoding",
        "metabarcode": "metabarcoding",
        "metabarcoding_edna": "metabarcoding",
        "qpcr": "qpcr_ddpcr",
        "ddpcr": "qpcr_ddpcr",
        "targeted": "custom_targeted",
    }
    return aliases.get(normalized, normalized if normalized in ASSAY_PROFILES else "unknown")


def assay_gate_readiness(request: BarcodeCompilerRequest, metadata: dict[str, Any]) -> dict[str, Any]:
    assay_type = assay_type_for(request, metadata)
    profile = ASSAY_PROFILES[assay_type]
    required_missing = [field for field in profile["required_fields"] if is_missing(metadata.get(field))]
    recommended_missing = [field for field in profile["recommended_fields"] if is_missing(metadata.get(field))]
    pass_required = not required_missing
    blockers = []
    if profile["publication_blocking"] and required_missing:
        blockers.append(f"assay gate blocked publication: missing {', '.join(required_missing)} for {assay_type}")
    actions = []
    if required_missing or recommended_missing:
        actions.append("Add assay evidence fields: controls, primers, replicate/QC or qPCR/ddPCR quantification metadata as applicable.")
    return {
        "assay_type": assay_type,
        "assay_label": profile["label"],
        "assay_required_missing": required_missing,
        "assay_recommended_missing": recommended_missing,
        "assay_gate_pass": pass_required,
        "assay_publication_blocking": bool(profile["publication_blocking"]),
        "assay_blockers": blockers,
        "assay_actions": actions,
        "claim_caveat": profile["claim_caveat"],
    }


def dna_extension_readiness(metadata: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in DNA_EXTENSION_HIGH_PRIORITY_FIELDS if is_missing(metadata.get(field))]
    return {
        "dna_extension_high_priority_fields": DNA_EXTENSION_HIGH_PRIORITY_FIELDS,
        "dna_extension_high_priority_missing": missing,
        "dna_extension_high_priority_pass": not missing,
    }


def is_missing(value: Any) -> bool:
    return value is None or str(value).strip() == ""
