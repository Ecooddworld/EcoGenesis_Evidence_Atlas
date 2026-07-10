from __future__ import annotations

import calendar
import csv
from datetime import date, datetime
import hashlib
import io
import json
import re
from typing import Any
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5
import xml.etree.ElementTree as ET
import zipfile


DWC_TEXT_NS = "http://rs.tdwg.org/dwc/text/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
EML_NS = "eml://ecoinformatics.org/eml-2.1.1"
DC_NS = "http://purl.org/dc/terms/"
OCCURRENCE_ROW_TYPE = "http://rs.tdwg.org/dwc/terms/Occurrence"
DNA_ROW_TYPE = "http://rs.gbif.org/terms/1.0/DNADerivedData"
DNA_DEFINITION = "https://rs.gbif.org/extension/gbif/1.0/dna_derived_data_2024-07-11.xml"
OCCURRENCE_DEFINITION = "https://rs.gbif.org/core/dwc_occurrence_2025-07-10.xml"

DWC = "http://rs.tdwg.org/dwc/terms/"
MIXS = "https://w3id.org/mixs/"
GBIF = "http://rs.gbif.org/terms/"

OCCURRENCE_FIELDS = [
    ("occurrenceID", DWC + "occurrenceID"),
    ("basisOfRecord", DWC + "basisOfRecord"),
    ("eventID", DWC + "eventID"),
    ("materialSampleID", DWC + "materialSampleID"),
    ("scientificName", DWC + "scientificName"),
    ("taxonRank", DWC + "taxonRank"),
    ("taxonID", DWC + "taxonID"),
    ("eventDate", DWC + "eventDate"),
    ("countryCode", DWC + "countryCode"),
    ("decimalLatitude", DWC + "decimalLatitude"),
    ("decimalLongitude", DWC + "decimalLongitude"),
    ("geodeticDatum", DWC + "geodeticDatum"),
    ("coordinateUncertaintyInMeters", DWC + "coordinateUncertaintyInMeters"),
    ("occurrenceStatus", DWC + "occurrenceStatus"),
    ("organismQuantity", DWC + "organismQuantity"),
    ("organismQuantityType", DWC + "organismQuantityType"),
    ("recordedBy", DWC + "recordedBy"),
    ("samplingProtocol", DWC + "samplingProtocol"),
    ("associatedSequences", DWC + "associatedSequences"),
    ("identificationReferences", DWC + "identificationReferences"),
    ("identificationRemarks", DWC + "identificationRemarks"),
    ("datasetID", DWC + "datasetID"),
    ("datasetName", DWC + "datasetName"),
    ("bibliographicCitation", DC_NS + "bibliographicCitation"),
    ("license", DC_NS + "license"),
]

DNA_FIELDS = [
    ("DNA_sequence", GBIF + "dna_sequence"),
    ("target_gene", MIXS + "0000044"),
    ("target_subfragment", MIXS + "0000045"),
    ("pcr_primer_forward", GBIF + "pcr_primer_forward"),
    ("pcr_primer_reverse", GBIF + "pcr_primer_reverse"),
    ("seq_meth", MIXS + "0000050"),
    ("otu_class_appr", MIXS + "0000085"),
    ("otu_seq_comp_appr", MIXS + "0000086"),
    ("otu_db", MIXS + "0000087"),
    ("sop", MIXS + "0000090"),
    ("contaminationAssessment", GBIF + "miqe/contaminationAssessment"),
    ("quantificationCycle", GBIF + "miqe/quantificationCycle"),
    ("estimatedNumberOfCopies", GBIF + "miqe/estimatedNumberOfCopies"),
    ("experimentalVariance", GBIF + "miqe/experimentalVariance"),
]

BASIS_OF_RECORD = {
    "preservedspecimen": "PreservedSpecimen",
    "fossilspecimen": "FossilSpecimen",
    "livingspecimen": "LivingSpecimen",
    "humanobservation": "HumanObservation",
    "machineobservation": "MachineObservation",
    "materialsample": "MaterialSample",
    "occurrence": "Occurrence",
    "materialcitation": "MaterialCitation",
}
OCCURRENCE_STATUS = {"present", "absent"}
TAXON_RANKS = {"kingdom", "phylum", "class", "order", "family", "genus", "species", "subspecies", "unranked"}

LICENSES = {
    "cc0": ("CC0 1.0", "http://creativecommons.org/publicdomain/zero/1.0/legalcode"),
    "ccby": ("CC-BY 4.0", "http://creativecommons.org/licenses/by/4.0/legalcode"),
    "ccbync": ("CC-BY-NC 4.0", "http://creativecommons.org/licenses/by-nc/4.0/legalcode"),
}

LICENSE_ALIASES = {
    "cc0": "cc0",
    "cc010": "cc0",
    "ccby": "ccby",
    "ccby40": "ccby",
    "ccbync": "ccbync",
    "ccbync40": "ccbync",
}
LICENSE_URL_ALIASES = {
    "http://creativecommons.org/publicdomain/zero/1.0": "cc0",
    "https://creativecommons.org/publicdomain/zero/1.0": "cc0",
    "http://creativecommons.org/publicdomain/zero/1.0/legalcode": "cc0",
    "https://creativecommons.org/publicdomain/zero/1.0/legalcode": "cc0",
    "http://creativecommons.org/licenses/by/4.0": "ccby",
    "https://creativecommons.org/licenses/by/4.0": "ccby",
    "http://creativecommons.org/licenses/by/4.0/legalcode": "ccby",
    "https://creativecommons.org/licenses/by/4.0/legalcode": "ccby",
    "http://creativecommons.org/licenses/by-nc/4.0": "ccbync",
    "https://creativecommons.org/licenses/by-nc/4.0": "ccbync",
    "http://creativecommons.org/licenses/by-nc/4.0/legalcode": "ccbync",
    "https://creativecommons.org/licenses/by-nc/4.0/legalcode": "ccbync",
}

# ISO 3166-1 alpha-2, frozen locally so archive validation never depends on a
# network service or the host operating system's locale database.
ISO_ALPHA2 = frozenset(
    """AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ
    CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ DE DJ DK DM DO DZ EC EE EG EH ER ES ET FI FJ FK FM FO FR
    GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY HK HM HN HR HT HU ID IE IL IM IN IO IQ IR IS IT JE JM JO
    JP KE KG KH KI KM KN KP KR KW KY KZ LA LB LC LI LK LR LS LT LU LV LY MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR
    MS MT MU MV MW MX MY MZ NA NC NE NF NG NI NL NO NP NR NU NZ OM PA PE PF PG PH PK PL PM PN PR PS PT PW PY QA RE RO
    RS RU RW SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ TC TD TF TG TH TJ TK TL TM TN TO TR TT TV
    TW TZ UA UG UM US UY UZ VA VC VE VG VI VN VU WF WS YE YT ZA ZM ZW""".split()
)

EXPECTED_DWCA_DIALECT = {
    "encoding": "UTF-8",
    "fieldsTerminatedBy": "\\t",
    "linesTerminatedBy": "\\n",
    "fieldsEnclosedBy": '"',
    "ignoreHeaderLines": "1",
}


def build_dwca_artifacts(pack: dict[str, Any]) -> dict[str, str | bytes]:
    package = build_dwca_package(pack)
    artifacts: dict[str, str | bytes] = {
        "dwca_validation_report.json": json.dumps(package["report"], indent=2, ensure_ascii=False),
        "dwca_roundtrip_contract.json": json.dumps(package["contract"], indent=2, ensure_ascii=False),
    }
    if package["archive"] is not None:
        artifacts["dwca.zip"] = package["archive"]
    return artifacts


def build_dwca_package(pack: dict[str, Any]) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    dataset = pack.get("request", {}).get("dataset_metadata", {}) or {}
    required = ["title", "description", "publishingOrganization", "type", "license", "contact", "creator", "metadataProvider", "citation"]
    for field in required:
        if not dataset.get(field):
            errors.append(issue("EML_REQUIRED_METADATA_MISSING", f"dataset_metadata.{field} is required", "eml", field=field))

    if dataset.get("type") and str(dataset["type"]).strip().lower() != "occurrence":
        errors.append(issue("EML_UNSUPPORTED_DATASET_TYPE", "DwC-A export requires dataset_metadata.type=occurrence", "eml", field="type"))
    license_info = normalize_license(dataset.get("license"))
    if dataset.get("license") and license_info is None:
        errors.append(issue("EML_UNSUPPORTED_LICENSE", "License must be CC0 1.0, CC-BY 4.0 or CC-BY-NC 4.0", "eml", field="license"))
    for field in ("creator", "metadataProvider"):
        if dataset.get(field) and not all(str(value).strip() for value in dataset[field]):
            errors.append(issue("EML_INVALID_AGENT", f"dataset_metadata.{field} contains an empty agent", "eml", field=field))
    if dataset.get("contact") and not all(contact_name(value) for value in dataset["contact"]):
        errors.append(issue("EML_INVALID_CONTACT", "Every contact needs a name or organization", "eml", field="contact"))

    primary_eligible = [
        record for record in pack.get("records", [])
        if record.get("export_state") == "candidate_for_gbif_validation"
        and record.get("published_taxon", {}).get("rank") != "none"
    ]
    eligibility_mode = "export_state_candidate_for_gbif_validation"
    eligible = primary_eligible
    if not eligible:
        eligible = [
            record for record in pack.get("records", [])
            if record.get("publication_bucket") == "gbif_ready"
            and record.get("published_taxon", {}).get("rank") != "none"
        ]
        if eligible:
            eligibility_mode = "legacy_publication_bucket_fallback"
            warnings.append(issue(
                "DWCA_LEGACY_ELIGIBILITY_FALLBACK",
                "Eligibility used legacy publication_bucket=gbif_ready because export_state validation candidates were absent",
                "archive",
            ))
    excluded = [record.get("sequence_id") for record in pack.get("records", []) if record not in eligible]
    if not eligible:
        errors.append(issue("DWCA_NO_ELIGIBLE_RECORDS", "No record has export_state=candidate_for_gbif_validation", "archive"))
    if excluded:
        warnings.append(issue("DWCA_RECORDS_EXCLUDED", "Review/repair records are excluded from the publication archive", "archive", records=excluded))

    core_rows: list[dict[str, str]] = []
    dna_rows: list[dict[str, str]] = []
    seen: set[str] = set()
    if license_info:
        for record in eligible:
            core, dna = export_rows(record, pack, dataset, license_info[1], warnings)
            validate_semantics(core, dna, record, errors, warnings, pack)
            occurrence_id = core["occurrenceID"]
            if occurrence_id in seen:
                errors.append(issue("DWC_DUPLICATE_OCCURRENCE_ID", "occurrenceID must be unique", "core", record_id=occurrence_id, field="occurrenceID"))
            seen.add(occurrence_id)
            core_rows.append(core)
            dna_rows.append(dna)

    base_contract = {
        "contract_version": "ecogenesis-dwca-roundtrip-v1",
        "core_row_type": OCCURRENCE_ROW_TYPE,
        "occurrence_core_definition": OCCURRENCE_DEFINITION,
        "occurrence_registry_issued": "2026-02-12",
        "extension_row_type": DNA_ROW_TYPE,
        "dna_extension_definition": DNA_DEFINITION,
        "dna_extension_issued": "2024-07-11",
        "dna_extension_stability": "early_adopter_definition_subject_to_change",
        "expected_files": ["occurrence.txt", "dna_derived_data.txt", "meta.xml", "eml.xml"],
        "source_core_rows": len(core_rows),
        "source_extension_rows": len(dna_rows),
        "eligibility_mode": eligibility_mode,
        "status": "not_run",
    }
    if errors:
        return blocked_package(errors, warnings, eligible, excluded, base_contract)

    occurrence_text = write_table(core_rows, [name for name, _ in OCCURRENCE_FIELDS])
    dna_text = write_table(dna_rows, ["coreid", *[name for name, _ in DNA_FIELDS]])
    meta_xml = build_meta_xml()
    eml_xml = build_eml_xml(pack, dataset, license_info)
    files: dict[str, bytes] = {
        "occurrence.txt": occurrence_text.encode("utf-8"),
        "dna_derived_data.txt": dna_text.encode("utf-8"),
        "meta.xml": meta_xml,
        "eml.xml": eml_xml,
    }
    archive = deterministic_zip(files)
    validation = validate_dwca_bytes(archive)
    errors.extend(validation["errors"])
    warnings.extend(validation["warnings"])
    contract = {**base_contract, **validation["roundtrip"]}
    if errors:
        return blocked_package(errors, warnings, eligible, excluded, contract)

    digest = hashlib.sha256(archive).hexdigest()
    report = report_base(eligible, excluded, errors, warnings)
    report.update({
        "status": "local_validation_pass",
        "archive_created": True,
        "archive_name": "dwca.zip",
        "archive_sha256": digest,
        "archive_size_bytes": len(archive),
        "local_validation_status": "pass",
        "release_gate": "blocked_external_validation",
        "release_blockers": [
            "external GBIF/IPT validator has not been run",
            "IPT ingestion, publishing-organization endorsement and GBIF registration are not confirmed",
        ],
    })
    return {"archive": archive, "report": report, "contract": contract}


def blocked_package(errors: list[dict[str, Any]], warnings: list[dict[str, Any]], eligible: list[dict[str, Any]], excluded: list[str], contract: dict[str, Any]) -> dict[str, Any]:
    report = report_base(eligible, excluded, errors, warnings)
    report.update({
        "status": "blocked",
        "archive_created": False,
        "local_validation_status": "blocked",
        "release_gate": "blocked_local_validation",
        "release_blockers": sorted({item["message"] for item in errors}),
    })
    return {"archive": None, "report": report, "contract": contract}


def report_base(eligible: list[dict[str, Any]], excluded: list[str], errors: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "validator": "EcoGenesis local DwC-A contract validator",
        "validator_contract_version": "ecogenesis-dwca-roundtrip-v1",
        "eligible_record_count": len(eligible),
        "excluded_record_ids": excluded,
        "errors": errors,
        "warnings": warnings,
        "external_validation": {
            "gbif_ipt_validator": "not_run",
            "ipt_ingestion": "not_run",
            "gbif_registration": "not_run",
            "publication": "not_run",
        },
        "validation_scope": {
            "local": ["archive structure", "meta.xml mappings", "EML required content", "unique core keys", "extension foreign keys", "roundtrip row counts", "coordinates", "ISO dates", "basisOfRecord", "occurrenceStatus", "taxonRank", "license"],
            "not_local": ["live registry/XSD validation", "country-coordinate polygon interpretation", "GBIF backbone interpretation", "IPT ingestion", "GBIF registration/publication"],
        },
        "claim_boundary": "A local pass means the generated bytes satisfy this frozen local contract; it is not evidence of IPT ingestion or GBIF publication.",
    }


def export_rows(record: dict[str, Any], pack: dict[str, Any], dataset: dict[str, Any], license_uri: str, warnings: list[dict[str, Any]]) -> tuple[dict[str, str], dict[str, str]]:
    metadata = record["metadata"]
    occurrence_id = text(metadata.get("occurrenceID"))
    basis = BASIS_OF_RECORD.get(text(metadata.get("basisOfRecord")).lower(), text(metadata.get("basisOfRecord")))
    status = text(metadata.get("occurrenceStatus")).lower()
    taxon = record["published_taxon"]
    taxon_key = taxon.get("taxon_key")
    taxon_id = f"https://www.gbif.org/species/{taxon_key}" if taxon_key else ""
    dataset_id = text(dataset.get("datasetID")) or canonical_uuid_urn(pack["run"]["run_id"])
    citation = text(dataset.get("citation"))
    reference = text(pack.get("reference_manifest", {}).get("doi_or_url"))
    core = {
        "occurrenceID": occurrence_id,
        "basisOfRecord": basis,
        "eventID": text(metadata.get("eventID")),
        "materialSampleID": text(metadata.get("materialSampleID")),
        "scientificName": text(taxon.get("name")),
        "taxonRank": text(taxon.get("rank")).lower(),
        "taxonID": taxon_id,
        "eventDate": text(metadata.get("eventDate")),
        "countryCode": text(metadata.get("countryCode")).upper(),
        "decimalLatitude": text(metadata.get("decimalLatitude")),
        "decimalLongitude": text(metadata.get("decimalLongitude")),
        "geodeticDatum": text(metadata.get("geodeticDatum")),
        "coordinateUncertaintyInMeters": text(metadata.get("coordinateUncertaintyInMeters")),
        "occurrenceStatus": status,
        "organismQuantity": text(metadata.get("organismQuantity")),
        "organismQuantityType": text(metadata.get("organismQuantityType")),
        "recordedBy": text(metadata.get("recordedBy")),
        "samplingProtocol": text(metadata.get("samplingProtocol")),
        "associatedSequences": text(metadata.get("associatedSequences")),
        "identificationReferences": text(metadata.get("identificationReferences")) or reference,
        "identificationRemarks": identification_remarks(record, pack),
        "datasetID": dataset_id,
        "datasetName": text(dataset.get("title")),
        "bibliographicCitation": citation,
        "license": license_uri,
    }
    sop = text(metadata.get("sop"))
    if sop and not absolute_uri(sop):
        warnings.append(issue("DNA_SOP_OMITTED_NOT_URI", "sop was omitted because the registered extension term requires a URI", "extension", record_id=occurrence_id, field="sop"))
        sop = ""
    contamination = text(metadata.get("contaminationAssessment"))
    if contamination:
        contamination = "false" if contamination.lower() in {"false", "no", "not done", "0"} else "true"
    dna = {
        "coreid": occurrence_id,
        "DNA_sequence": text(metadata.get("DNA_sequence")),
        "target_gene": text(metadata.get("target_gene") or metadata.get("marker")),
        "target_subfragment": text(metadata.get("target_subfragment")),
        "pcr_primer_forward": text(metadata.get("pcr_primer_forward")),
        "pcr_primer_reverse": text(metadata.get("pcr_primer_reverse")),
        "seq_meth": text(metadata.get("seq_meth")),
        "otu_class_appr": text(metadata.get("otu_class_appr") or metadata.get("methodOrSOP")),
        "otu_seq_comp_appr": text(metadata.get("otu_seq_comp_appr")),
        "otu_db": text(metadata.get("otu_db") or metadata.get("referenceDatabase")),
        "sop": sop,
        "contaminationAssessment": contamination,
        "quantificationCycle": text(metadata.get("quantificationCycle")),
        "estimatedNumberOfCopies": text(metadata.get("estimatedNumberOfCopies")),
        "experimentalVariance": text(metadata.get("experimentalVariance")),
    }
    return core, dna


def identification_remarks(record: dict[str, Any], pack: dict[str, Any]) -> str:
    top = record.get("top_hit") or {}
    return (
        "EcoGenesis local scientific state="
        f"{record.get('scientific_decision_state', record.get('decision_class'))}; "
        f"ruleset={pack['run']['ruleset_version']}; "
        f"topHit={top.get('taxon')}; identity={top.get('identity')}; queryCoverage={top.get('query_coverage')}; "
        f"candidateRank={record.get('candidate_taxon', {}).get('rank')}; publishedRank={record.get('published_taxon', {}).get('rank')}. "
        "This row remains a validation candidate; IPT ingestion and GBIF publication are not confirmed."
    )


def validate_semantics(core: dict[str, str], dna: dict[str, str], record: dict[str, Any], errors: list[dict[str, Any]], warnings: list[dict[str, Any]], pack: dict[str, Any]) -> None:
    rid = core["occurrenceID"] or record.get("sequence_id")
    if not core["occurrenceID"]:
        errors.append(issue("DWC_EMPTY_OCCURRENCE_ID", "occurrenceID is required", "core", record_id=rid, field="occurrenceID"))
    if core["basisOfRecord"] not in BASIS_OF_RECORD.values():
        errors.append(issue("DWC_INVALID_BASIS_OF_RECORD", "basisOfRecord is not in the Darwin Core vocabulary", "core", record_id=rid, field="basisOfRecord"))
    assay = text(record.get("metadata", {}).get("assayType") or pack.get("request", {}).get("assay_type"))
    if assay in {"metabarcoding", "qpcr_ddpcr"} and core["basisOfRecord"] != "MaterialSample":
        errors.append(issue("DWC_DNA_BASIS_OF_RECORD_MISMATCH", "DNA-derived eDNA/qPCR occurrences require MaterialSample", "core", record_id=rid, field="basisOfRecord"))
    if core["occurrenceStatus"] and core["occurrenceStatus"] not in OCCURRENCE_STATUS:
        errors.append(issue("DWC_INVALID_OCCURRENCE_STATUS", "occurrenceStatus must be present or absent", "core", record_id=rid, field="occurrenceStatus"))
    if assay == "qpcr_ddpcr" and not core["occurrenceStatus"]:
        errors.append(issue("DWC_MISSING_OCCURRENCE_STATUS", "qPCR/ddPCR occurrenceStatus is required", "core", record_id=rid, field="occurrenceStatus"))
    if core["taxonRank"] not in TAXON_RANKS:
        errors.append(issue("DWC_INVALID_TAXON_RANK", "taxonRank is not in the local Darwin Core vocabulary", "core", record_id=rid, field="taxonRank"))
    if not core["scientificName"]:
        errors.append(issue("DWC_EMPTY_SCIENTIFIC_NAME", "scientificName is required", "core", record_id=rid, field="scientificName"))
    if not valid_iso_date(core["eventDate"]):
        errors.append(issue("DWC_INVALID_EVENT_DATE", "eventDate must be a real ISO 8601 date/date-time or interval", "core", record_id=rid, field="eventDate"))
    lat, lon = core["decimalLatitude"], core["decimalLongitude"]
    if bool(lat) != bool(lon):
        errors.append(issue("DWC_COORDINATE_PAIR_INCOMPLETE", "decimalLatitude and decimalLongitude must be supplied together", "core", record_id=rid))
    if lat and lon:
        try:
            if not -90 <= float(lat) <= 90:
                errors.append(issue("DWC_LATITUDE_OUT_OF_RANGE", "decimalLatitude must be between -90 and 90", "core", record_id=rid, field="decimalLatitude"))
            if not -180 <= float(lon) <= 180:
                errors.append(issue("DWC_LONGITUDE_OUT_OF_RANGE", "decimalLongitude must be between -180 and 180", "core", record_id=rid, field="decimalLongitude"))
        except ValueError:
            errors.append(issue("DWC_COORDINATE_NOT_NUMERIC", "coordinates must be numeric", "core", record_id=rid))
    uncertainty = core["coordinateUncertaintyInMeters"]
    if uncertainty:
        try:
            if float(uncertainty) <= 0:
                raise ValueError
        except ValueError:
            errors.append(issue("DWC_INVALID_COORDINATE_UNCERTAINTY", "coordinateUncertaintyInMeters must be numeric and > 0", "core", record_id=rid, field="coordinateUncertaintyInMeters"))
    if core["countryCode"] and core["countryCode"] not in ISO_ALPHA2:
        errors.append(issue("DWC_INVALID_COUNTRY_CODE", "countryCode must be an ISO 3166-1 alpha-2 code", "core", record_id=rid, field="countryCode"))
    if not dna["DNA_sequence"] or not re.fullmatch(r"[ACGTRYSWKMBDHVN]+", dna["DNA_sequence"].upper()):
        errors.append(issue("DNA_INVALID_SEQUENCE", "DNA_sequence must contain IUPAC DNA symbols", "extension", record_id=rid, field="DNA_sequence"))
    if dna["quantificationCycle"]:
        try:
            float(dna["quantificationCycle"])
        except ValueError:
            errors.append(issue("DNA_INVALID_QUANTIFICATION_CYCLE", "quantificationCycle must be decimal", "extension", record_id=rid, field="quantificationCycle"))
    if dna["estimatedNumberOfCopies"] and not re.fullmatch(r"\d+", dna["estimatedNumberOfCopies"]):
        errors.append(issue("DNA_INVALID_COPY_COUNT", "estimatedNumberOfCopies must be an integer", "extension", record_id=rid, field="estimatedNumberOfCopies"))


def build_meta_xml() -> bytes:
    ET.register_namespace("", DWC_TEXT_NS)
    ET.register_namespace("xsi", XSI_NS)
    root = ET.Element(f"{{{DWC_TEXT_NS}}}archive", {
        "metadata": "eml.xml",
        f"{{{XSI_NS}}}schemaLocation": f"{DWC_TEXT_NS} http://rs.tdwg.org/dwc/text/tdwg_dwc_text.xsd",
    })
    common = {"encoding": "UTF-8", "fieldsTerminatedBy": "\\t", "linesTerminatedBy": "\\n", "fieldsEnclosedBy": '"', "ignoreHeaderLines": "1"}
    core = ET.SubElement(root, f"{{{DWC_TEXT_NS}}}core", {**common, "rowType": OCCURRENCE_ROW_TYPE})
    files = ET.SubElement(core, f"{{{DWC_TEXT_NS}}}files")
    ET.SubElement(files, f"{{{DWC_TEXT_NS}}}location").text = "occurrence.txt"
    ET.SubElement(core, f"{{{DWC_TEXT_NS}}}id", {"index": "0"})
    for index, (_, term) in enumerate(OCCURRENCE_FIELDS):
        ET.SubElement(core, f"{{{DWC_TEXT_NS}}}field", {"index": str(index), "term": term})
    extension = ET.SubElement(root, f"{{{DWC_TEXT_NS}}}extension", {**common, "rowType": DNA_ROW_TYPE})
    files = ET.SubElement(extension, f"{{{DWC_TEXT_NS}}}files")
    ET.SubElement(files, f"{{{DWC_TEXT_NS}}}location").text = "dna_derived_data.txt"
    ET.SubElement(extension, f"{{{DWC_TEXT_NS}}}coreid", {"index": "0"})
    for index, (_, term) in enumerate(DNA_FIELDS, start=1):
        ET.SubElement(extension, f"{{{DWC_TEXT_NS}}}field", {"index": str(index), "term": term})
    return xml_bytes(root)


def build_eml_xml(pack: dict[str, Any], dataset: dict[str, Any], license_info: tuple[str, str]) -> bytes:
    ET.register_namespace("eml", EML_NS)
    ET.register_namespace("xsi", XSI_NS)
    ET.register_namespace("dc", DC_NS)
    package_id = canonical_uuid_urn(pack["run"]["run_id"])
    root = ET.Element(f"{{{EML_NS}}}eml", {
        f"{{{XSI_NS}}}schemaLocation": f"{EML_NS} http://rs.gbif.org/schema/eml-gbif-profile/1.1/eml.xsd",
        "packageId": package_id,
        "system": "EcoGenesis",
        "scope": "system",
        "{http://www.w3.org/XML/1998/namespace}lang": "en",
    })
    ds = ET.SubElement(root, "dataset")
    dataset_id = text(dataset.get("datasetID")) or package_id
    ET.SubElement(ds, "alternateIdentifier").text = dataset_id
    ET.SubElement(ds, "title", {"{http://www.w3.org/XML/1998/namespace}lang": "en"}).text = text(dataset["title"])
    for value in dataset["creator"]:
        add_agent(ds, "creator", value)
    for value in dataset["metadataProvider"]:
        add_agent(ds, "metadataProvider", value)
    publisher = ET.SubElement(ds, "associatedParty")
    ET.SubElement(publisher, "organizationName").text = text(dataset["publishingOrganization"])
    ET.SubElement(publisher, "role").text = "publisher"
    ET.SubElement(ds, "pubDate").text = pack["run"]["finished_at"][:10]
    ET.SubElement(ds, "language").text = text(dataset.get("language")) or "eng"
    abstract = ET.SubElement(ds, "abstract")
    ET.SubElement(abstract, "para").text = text(dataset["description"])
    rights = ET.SubElement(ds, "intellectualRights")
    para = ET.SubElement(rights, "para")
    para.text = f"This dataset is licensed under {license_info[0]}. "
    link = ET.SubElement(para, "ulink", {"url": license_info[1]})
    ET.SubElement(link, "citetitle").text = license_info[0]
    for value in dataset["contact"]:
        add_agent(ds, "contact", value)
    methods = ET.SubElement(ds, "methods")
    step = ET.SubElement(methods, "methodStep")
    description = ET.SubElement(step, "description")
    ET.SubElement(description, "para").text = text(pack.get("summary", {}).get("method_or_sop"))
    additional = ET.SubElement(root, "additionalMetadata")
    metadata = ET.SubElement(additional, "metadata")
    gbif = ET.SubElement(metadata, "gbif")
    ET.SubElement(gbif, "dateStamp").text = pack["run"]["finished_at"]
    ET.SubElement(gbif, "hierarchyLevel").text = "dataset"
    attrs = {"identifier": text(dataset["citationIdentifier"])} if dataset.get("citationIdentifier") else {}
    ET.SubElement(gbif, "citation", attrs).text = text(dataset["citation"])
    return xml_bytes(root)


def add_agent(parent: ET.Element, tag: str, value: Any) -> None:
    node = ET.SubElement(parent, tag)
    if isinstance(value, str):
        ET.SubElement(node, "organizationName").text = value.strip()
        return
    individual = value.get("individualName") if isinstance(value, dict) else None
    name = contact_name(value)
    organization = text(value.get("organizationName") or value.get("organization"))
    if individual or (name and not organization):
        person = ET.SubElement(node, "individualName")
        if isinstance(individual, dict) and individual.get("givenName"):
            ET.SubElement(person, "givenName").text = text(individual["givenName"])
        surname = individual.get("surName") if isinstance(individual, dict) else name
        ET.SubElement(person, "surName").text = text(surname)
    if organization:
        ET.SubElement(node, "organizationName").text = organization
    if isinstance(value, dict):
        if value.get("positionName"):
            ET.SubElement(node, "positionName").text = text(value["positionName"])
        if value.get("phone"):
            ET.SubElement(node, "phone").text = text(value["phone"])
        email = value.get("electronicMailAddress") or value.get("email")
        if email:
            ET.SubElement(node, "electronicMailAddress").text = text(email)
        url = value.get("onlineUrl") or value.get("url")
        if url:
            ET.SubElement(node, "onlineUrl").text = text(url)


def validate_dwca_bytes(archive: bytes) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    core_ids: list[str] = []
    extension_ids: list[str] = []
    missing_keys: list[str] = []
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            names = zf.namelist()
            required = {"occurrence.txt", "dna_derived_data.txt", "meta.xml", "eml.xml"}
            missing = required - set(names)
            if missing:
                errors.append(issue("DWCA_MISSING_FILE", f"Archive is missing: {', '.join(sorted(missing))}", "archive"))
                return {"errors": errors, "warnings": warnings, "roundtrip": {"status": "fail"}}
            if len(names) != len(set(names)) or any(name.startswith("/") or ".." in name.split("/") for name in names):
                errors.append(issue("DWCA_UNSAFE_OR_DUPLICATE_PATH", "Archive paths must be unique and relative", "archive"))
            meta = ET.fromstring(zf.read("meta.xml"))
            eml = ET.fromstring(zf.read("eml.xml"))
            if meta.tag != f"{{{DWC_TEXT_NS}}}archive" or meta.get("metadata") != "eml.xml":
                errors.append(issue("DWCA_INVALID_META_ROOT", "meta.xml must use the Darwin Core text namespace and metadata=eml.xml", "meta"))
            ns = {"d": DWC_TEXT_NS}
            core = meta.find("d:core", ns)
            ext = meta.find("d:extension", ns)
            if core is None or core.get("rowType") != OCCURRENCE_ROW_TYPE:
                errors.append(issue("DWCA_INVALID_CORE_ROWTYPE", "Occurrence core rowType is incorrect", "meta"))
            if ext is None or ext.get("rowType") != DNA_ROW_TYPE:
                errors.append(issue("DWCA_INVALID_DNA_ROWTYPE", "DNA-derived extension rowType is incorrect", "meta"))
            if core is not None:
                validate_meta_dialect(core, "core", errors)
                core_mapping = [(int(field.get("index", "-1")), field.get("term")) for field in core.findall("d:field", ns)]
                expected_mapping = [(index, term) for index, (_, term) in enumerate(OCCURRENCE_FIELDS)]
                core_id = core.find("d:id", ns)
                location = core.findtext("d:files/d:location", namespaces=ns)
                if core_mapping != expected_mapping or core_id is None or core_id.get("index") != "0" or location != "occurrence.txt":
                    errors.append(issue("DWCA_CORE_META_MAPPING", "Occurrence id, location or term mapping is incorrect", "meta"))
            if ext is not None:
                validate_meta_dialect(ext, "extension", errors)
                ext_mapping = [(int(field.get("index", "-1")), field.get("term")) for field in ext.findall("d:field", ns)]
                expected_mapping = [(index, term) for index, (_, term) in enumerate(DNA_FIELDS, start=1)]
                core_id = ext.find("d:coreid", ns)
                location = ext.findtext("d:files/d:location", namespaces=ns)
                if ext_mapping != expected_mapping or core_id is None or core_id.get("index") != "0" or location != "dna_derived_data.txt":
                    errors.append(issue("DWCA_DNA_META_MAPPING", "DNA coreid, location or term mapping is incorrect", "meta"))
            core_rows = read_descriptor_table(zf, "occurrence.txt", core)
            dna_rows = read_descriptor_table(zf, "dna_derived_data.txt", ext)
            expected_core_width = len(OCCURRENCE_FIELDS)
            expected_dna_width = len(DNA_FIELDS) + 1
            core_shape_ok = bool(core_rows) and core_rows[0] == [name for name, _ in OCCURRENCE_FIELDS] and all(
                len(row) == expected_core_width for row in core_rows[1:]
            )
            dna_shape_ok = bool(dna_rows) and dna_rows[0] == ["coreid", *[name for name, _ in DNA_FIELDS]] and all(
                len(row) == expected_dna_width for row in dna_rows[1:]
            )
            if not core_shape_ok:
                errors.append(issue("DWCA_CORE_TABLE_SHAPE", "Occurrence header/row width does not match meta.xml contract", "core"))
            if not dna_shape_ok:
                errors.append(issue("DWCA_EXTENSION_TABLE_SHAPE", "DNA extension header/row width does not match meta.xml contract", "extension"))
            core_ids = [row[0] for row in core_rows[1:] if row]
            extension_ids = [row[0] for row in dna_rows[1:] if row]
            if len(core_ids) != len(set(core_ids)) or any(not value for value in core_ids):
                errors.append(issue("DWCA_CORE_KEY_INTEGRITY", "Core IDs must be non-empty and unique", "core"))
            missing_keys = sorted(set(extension_ids) - set(core_ids))
            if missing_keys:
                errors.append(issue("DWCA_EXTENSION_FOREIGN_KEY", f"Extension keys missing from core: {', '.join(missing_keys)}", "extension"))
            missing_extensions = sorted(set(core_ids) - set(extension_ids))
            if missing_extensions:
                errors.append(issue("DWCA_MISSING_DNA_EXTENSION_ROW", f"Core records missing DNA extension rows: {', '.join(missing_extensions)}", "extension"))
            core_values_rows: list[dict[str, str]] = []
            if core_shape_ok and dna_shape_ok:
                dna_by_id = {row[0]: dict(zip(dna_rows[0], row)) for row in dna_rows[1:]}
                for row in core_rows[1:]:
                    core_values = dict(zip(core_rows[0], row))
                    core_values_rows.append(core_values)
                    dna_values = dna_by_id.get(core_values.get("occurrenceID", ""), {name: "" for name, _ in DNA_FIELDS})
                    validate_semantics(
                        core_values,
                        dna_values,
                        {"sequence_id": core_values.get("occurrenceID"), "metadata": {"assayType": "unknown"}},
                        errors,
                        warnings,
                        {"request": {"assay_type": "unknown"}},
                    )
                    if normalize_license(core_values.get("license")) is None:
                        errors.append(issue("DWC_UNSUPPORTED_RECORD_LICENSE", "Record license is not supported by GBIF", "core", record_id=core_values.get("occurrenceID"), field="license"))
            if eml.tag != f"{{{EML_NS}}}eml":
                errors.append(issue("EML_INVALID_ROOT", "eml.xml has the wrong EML namespace", "eml"))
            if not is_canonical_uuid_urn(eml.get("packageId")):
                errors.append(issue("EML_INVALID_PACKAGE_ID", "EML packageId must be a canonical urn:uuid identifier", "eml", field="packageId"))
            dataset = eml.find("dataset")
            required_eml = ["title", "creator", "metadataProvider", "abstract", "intellectualRights", "contact"]
            if dataset is None or any(dataset.find(field) is None for field in required_eml):
                errors.append(issue("EML_REQUIRED_CONTENT_MISSING", "eml.xml is missing required dataset content", "eml"))
            citation = eml.find("./additionalMetadata/metadata/gbif/citation")
            if citation is None or not text(citation.text):
                errors.append(issue("EML_CITATION_MISSING", "eml.xml requires a dataset citation", "eml"))
            eml_license_node = eml.find("./dataset/intellectualRights/para/ulink")
            eml_license = normalize_license(eml_license_node.get("url") if eml_license_node is not None else None)
            if eml_license is None:
                errors.append(issue("EML_LICENSE_MISSING_OR_UNSUPPORTED", "eml.xml requires a supported Creative Commons license URI", "eml"))
            if core_shape_ok:
                core_licenses = {normalize_license(row.get("license")) for row in core_values_rows}
                if eml_license is not None and core_licenses != {eml_license}:
                    errors.append(issue("DWCA_LICENSE_MISMATCH", "EML and Occurrence Core licenses must resolve to the same license", "archive"))
                eml_citation = text(citation.text) if citation is not None else ""
                core_citations = {text(row.get("bibliographicCitation")) for row in core_values_rows}
                if eml_citation and core_citations != {eml_citation}:
                    errors.append(issue("DWCA_CITATION_MISMATCH", "EML citation and Occurrence Core bibliographicCitation must match", "archive"))
    except (zipfile.BadZipFile, UnicodeDecodeError, ET.ParseError, csv.Error, LookupError, ValueError) as exc:
        errors.append(issue("DWCA_PARSE_ERROR", f"Archive cannot be parsed: {exc}", "archive"))
        return {"errors": errors, "warnings": warnings, "roundtrip": {"status": "fail"}}
    roundtrip = {
        "status": "pass" if not errors else "fail",
        "parsed_core_rows": len(core_ids),
        "parsed_extension_rows": len(extension_ids),
        "unique_core_ids": len(set(core_ids)),
        "extension_foreign_keys_resolved": not missing_keys,
        "core_ids_sha256": hashlib.sha256(json.dumps(core_ids, sort_keys=True).encode()).hexdigest(),
    }
    return {"errors": errors, "warnings": warnings, "roundtrip": roundtrip}


def validate_meta_dialect(descriptor: ET.Element, scope: str, errors: list[dict[str, Any]]) -> None:
    observed = {field: descriptor.get(field) for field in EXPECTED_DWCA_DIALECT}
    if observed != EXPECTED_DWCA_DIALECT:
        errors.append(
            issue(
                "DWCA_META_DIALECT_MISMATCH",
                f"{scope} text dialect does not match the supported UTF-8 TSV contract",
                "meta",
                observed=observed,
                expected=EXPECTED_DWCA_DIALECT,
            )
        )


def read_descriptor_table(zf: zipfile.ZipFile, location: str, descriptor: ET.Element | None) -> list[list[str]]:
    attributes = EXPECTED_DWCA_DIALECT if descriptor is None else {
        field: descriptor.get(field, default) for field, default in EXPECTED_DWCA_DIALECT.items()
    }
    encoding = attributes["encoding"]
    delimiter = decode_meta_character(attributes["fieldsTerminatedBy"])
    quotechar = decode_meta_character(attributes["fieldsEnclosedBy"])
    if len(delimiter) != 1 or len(quotechar) != 1:
        raise ValueError("DwC-A delimiter and enclosing character must each decode to one character")
    content = zf.read(location).decode(encoding)
    return list(csv.reader(io.StringIO(content), delimiter=delimiter, quotechar=quotechar))


def decode_meta_character(value: str) -> str:
    supported = {r"\t": "\t", r"\n": "\n", r"\r": "\r", r"\\": "\\"}
    return supported.get(value, value)


def write_table(rows: list[dict[str, str]], fields: list[str]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def deterministic_zip(files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, files[name])
    return output.getvalue()


def normalize_license(value: Any) -> tuple[str, str] | None:
    supplied = text(value).strip().lower().rstrip("/")
    if not supplied:
        return None
    key = LICENSE_URL_ALIASES.get(supplied)
    if key is None:
        compact = re.sub(r"[^a-z0-9]", "", supplied)
        key = LICENSE_ALIASES.get(compact)
    return LICENSES.get(key) if key else None


def valid_iso_date(value: str) -> bool:
    if not value:
        return False
    try:
        parts = value.split("/")
        if len(parts) not in {1, 2}:
            return False
        ranges = [parse_iso_endpoint(endpoint) for endpoint in parts]
        if len(ranges) == 2 and ranges[0][0] > ranges[1][1]:
            return False
        return True
    except ValueError:
        return False


def parse_iso_endpoint(value: str) -> tuple[date, date]:
    if re.fullmatch(r"\d{4}", value):
        year = int(value)
        return date(year, 1, 1), date(year, 12, 31)
    if re.fullmatch(r"\d{4}-\d{2}", value):
        parsed = datetime.strptime(value, "%Y-%m")
        last_day = calendar.monthrange(parsed.year, parsed.month)[1]
        return date(parsed.year, parsed.month, 1), date(parsed.year, parsed.month, last_day)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        parsed_date = date.fromisoformat(value)
        return parsed_date, parsed_date
    parsed_datetime = datetime.fromisoformat(value.replace("Z", "+00:00"))
    parsed_date = parsed_datetime.date()
    return parsed_date, parsed_date


def canonical_uuid_urn(value: Any) -> str:
    supplied = text(value)
    try:
        identifier = UUID(supplied.removeprefix("urn:uuid:"))
    except (ValueError, AttributeError):
        identifier = uuid5(NAMESPACE_URL, f"https://ecogenesis.local/runs/{supplied}")
    return f"urn:uuid:{identifier}"


def is_canonical_uuid_urn(value: Any) -> bool:
    supplied = text(value)
    if not supplied.startswith("urn:uuid:"):
        return False
    uuid_text = supplied.removeprefix("urn:uuid:")
    try:
        return f"urn:uuid:{UUID(uuid_text)}" == supplied
    except ValueError:
        return False


def absolute_uri(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https", "urn"} and bool(parsed.netloc or parsed.scheme == "urn")


def contact_name(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if not isinstance(value, dict):
        return ""
    individual = value.get("individualName")
    if isinstance(individual, dict):
        return text(individual.get("surName") or individual.get("givenName"))
    return text(individual or value.get("name") or value.get("surName") or value.get("organizationName") or value.get("organization"))


def xml_bytes(root: ET.Element) -> bytes:
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def issue(code: str, message: str, scope: str, **details: Any) -> dict[str, Any]:
    return {"code": code, "message": message, "scope": scope, **{key: value for key, value in details.items() if value not in (None, "", [])}}
