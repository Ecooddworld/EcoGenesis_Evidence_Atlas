from __future__ import annotations

from copy import deepcopy
import io
import zipfile

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import GOOD_RECORD, request_with_records
from app.barcode.dwca import DNA_ROW_TYPE, build_dwca_package, deterministic_zip, validate_dwca_bytes
from app.barcode.schemas import BarcodeCompilerRequest, SequenceRecord
from app.barcode.scientific_gates import (
    ATTESTATION_SECRET_ENV,
    attest_reference_completeness,
)
from app.barcode.storage import barcode_artifact_path


def valid_pack() -> dict:
    return {
        "run": {
            "run_id": "12345678123456781234567812345678",
            "finished_at": "2026-07-10T10:00:00+00:00",
            "ruleset_version": "test-ruleset",
        },
        "summary": {"method_or_sop": "Audited molecular workflow"},
        "reference_manifest": {"doi_or_url": "https://doi.org/10.35035/doc-vf1a-nr22"},
        "request": {
            "assay_type": "single_specimen_barcode",
            "dataset_metadata": {
                "title": "DNA-derived occurrence candidates",
                "description": "A test occurrence dataset with molecular evidence.",
                "publishingOrganization": "Example Biodiversity Institute",
                "type": "occurrence",
                "license": "CC-BY 4.0",
                "contact": [{"name": "Dataset Curator", "email": "curator@example.org"}],
                "creator": ["Example Research Team"],
                "metadataProvider": ["Example Metadata Team"],
                "citation": "Example Research Team (2026). DNA-derived occurrence candidates. Example Biodiversity Institute.",
                "citationIdentifier": "https://doi.org/10.1234/example",
                "datasetID": "urn:uuid:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                "language": "eng",
            },
        },
        "records": [
            {
                "sequence_id": "seq-1",
                "publication_bucket": "gbif_ready",
                "export_state": "candidate_for_gbif_validation",
                "decision_class": "species-safe",
                "candidate_taxon": {"rank": "species", "name": "Aedes albopictus"},
                "published_taxon": {"rank": "species", "name": "Aedes albopictus", "taxon_key": 1651430},
                "top_hit": {"taxon": "Aedes albopictus", "identity": 99.8, "query_coverage": 100},
                "metadata": {
                    "occurrenceID": "urn:example:occurrence:1",
                    "eventID": "urn:example:event:1",
                    "materialSampleID": "urn:example:sample:1",
                    "basisOfRecord": "MaterialSample",
                    "eventDate": "2026-04-18",
                    "countryCode": "ES",
                    "decimalLatitude": 40.4168,
                    "decimalLongitude": -3.7038,
                    "geodeticDatum": "WGS84",
                    "coordinateUncertaintyInMeters": 50,
                    "DNA_sequence": "ACGTRYSWKMBDHVN",
                    "target_gene": "COI",
                    "target_subfragment": "COI-5P",
                    "referenceDatabase": "BOLD",
                    "methodOrSOP": "Audited molecular workflow",
                    "assayType": "single_specimen_barcode",
                },
            }
        ],
    }


def test_full_dwca_contains_core_extension_meta_and_eml() -> None:
    result = build_dwca_package(valid_pack())

    assert result["report"]["local_validation_status"] == "pass"
    assert result["report"]["release_gate"] == "blocked_external_validation"
    assert result["report"]["external_validation"]["ipt_ingestion"] == "not_run"
    assert result["contract"]["extension_row_type"] == DNA_ROW_TYPE
    assert result["contract"]["extension_foreign_keys_resolved"] is True

    with zipfile.ZipFile(io.BytesIO(result["archive"])) as archive:
        assert set(archive.namelist()) == {"occurrence.txt", "dna_derived_data.txt", "meta.xml", "eml.xml"}
        meta = archive.read("meta.xml").decode("utf-8")
        eml = archive.read("eml.xml").decode("utf-8")
        assert DNA_ROW_TYPE in meta
        assert '<coreid index="0"' in meta
        assert "http://rs.tdwg.org/dwc/terms/occurrenceID" in meta
        assert "CC-BY 4.0" in eml
        assert "Example Research Team (2026)" in eml
        assert 'packageId="urn:uuid:12345678-1234-5678-1234-567812345678"' in eml
        assert "packageId=\"urn:uuid:12345678123456781234567812345678/eml-1.xml\"" not in eml


def test_semantic_failures_block_archive() -> None:
    pack = valid_pack()
    metadata = pack["records"][0]["metadata"]
    metadata.update({
        "basisOfRecord": "DNA",
        "occurrenceStatus": "maybe",
        "eventDate": "2026-02-31",
        "decimalLatitude": 95,
        "decimalLongitude": -181,
    })

    result = build_dwca_package(pack)
    codes = {item["code"] for item in result["report"]["errors"]}

    assert result["archive"] is None
    assert result["report"]["release_gate"] == "blocked_local_validation"
    assert {
        "DWC_INVALID_BASIS_OF_RECORD",
        "DWC_INVALID_OCCURRENCE_STATUS",
        "DWC_INVALID_EVENT_DATE",
        "DWC_LATITUDE_OUT_OF_RANGE",
        "DWC_LONGITUDE_OUT_OF_RANGE",
    } <= codes


def test_roundtrip_validator_rejects_broken_extension_key() -> None:
    result = build_dwca_package(valid_pack())
    with zipfile.ZipFile(io.BytesIO(result["archive"])) as source:
        files = {name: source.read(name) for name in source.namelist()}
    dna = files["dna_derived_data.txt"].decode("utf-8").replace(
        "urn:example:occurrence:1", "urn:example:occurrence:missing", 1
    )
    files["dna_derived_data.txt"] = dna.encode("utf-8")

    validation = validate_dwca_bytes(deterministic_zip(files))

    assert validation["roundtrip"]["status"] == "fail"
    assert "DWCA_EXTENSION_FOREIGN_KEY" in {item["code"] for item in validation["errors"]}


def test_license_normalization_rejects_substring_false_positive() -> None:
    pack = valid_pack()
    pack["request"]["dataset_metadata"]["license"] = "proprietary-by40-internal"

    result = build_dwca_package(pack)

    assert result["archive"] is None
    assert "EML_UNSUPPORTED_LICENSE" in {item["code"] for item in result["report"]["errors"]}


def test_country_code_requires_real_iso_alpha2_member() -> None:
    pack = valid_pack()
    pack["records"][0]["metadata"]["countryCode"] = "ZZ"

    result = build_dwca_package(pack)

    assert result["archive"] is None
    assert "DWC_INVALID_COUNTRY_CODE" in {item["code"] for item in result["report"]["errors"]}


def test_reversed_iso_date_interval_is_rejected() -> None:
    pack = valid_pack()
    pack["records"][0]["metadata"]["eventDate"] = "2026-12-31/2026-01-01"

    result = build_dwca_package(pack)

    assert result["archive"] is None
    assert "DWC_INVALID_EVENT_DATE" in {item["code"] for item in result["report"]["errors"]}


def test_roundtrip_validator_rejects_meta_dialect_mismatch() -> None:
    files = valid_archive_files()
    files["meta.xml"] = files["meta.xml"].replace(b'fieldsTerminatedBy="\\t"', b'fieldsTerminatedBy=","', 1)

    validation = validate_dwca_bytes(deterministic_zip(files))
    codes = {item["code"] for item in validation["errors"]}

    assert validation["roundtrip"]["status"] == "fail"
    assert "DWCA_META_DIALECT_MISMATCH" in codes
    assert "DWCA_CORE_TABLE_SHAPE" in codes


def test_roundtrip_validator_rejects_eml_core_license_mismatch() -> None:
    files = valid_archive_files()
    files["eml.xml"] = files["eml.xml"].replace(
        b"http://creativecommons.org/licenses/by/4.0/legalcode",
        b"http://creativecommons.org/publicdomain/zero/1.0/legalcode",
        1,
    )

    validation = validate_dwca_bytes(deterministic_zip(files))

    assert "DWCA_LICENSE_MISMATCH" in {item["code"] for item in validation["errors"]}


def test_roundtrip_validator_rejects_eml_core_citation_mismatch() -> None:
    files = valid_archive_files()
    files["eml.xml"] = files["eml.xml"].replace(b"Example Research Team (2026)", b"Different Team (2026)", 1)

    validation = validate_dwca_bytes(deterministic_zip(files))

    assert "DWCA_CITATION_MISMATCH" in {item["code"] for item in validation["errors"]}


def test_roundtrip_validator_rejects_noncanonical_eml_package_id() -> None:
    files = valid_archive_files()
    files["eml.xml"] = files["eml.xml"].replace(
        b"urn:uuid:12345678-1234-5678-1234-567812345678",
        b"urn:uuid:12345678123456781234567812345678/eml-1.xml",
        1,
    )

    validation = validate_dwca_bytes(deterministic_zip(files))

    assert "EML_INVALID_PACKAGE_ID" in {item["code"] for item in validation["errors"]}


def test_missing_dataset_metadata_yields_report_without_archive() -> None:
    pack = valid_pack()
    pack["request"]["dataset_metadata"] = {}

    result = build_dwca_package(pack)

    assert result["archive"] is None
    assert result["contract"]["status"] == "not_run"
    assert "EML_REQUIRED_METADATA_MISSING" in {item["code"] for item in result["report"]["errors"]}
    assert result["report"]["external_validation"]["gbif_ipt_validator"] == "not_run"


def test_compiler_persists_dwca_only_for_locally_valid_candidate(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv(ATTESTATION_SECRET_ENV, "pytest-only-attestation-secret-32-bytes-minimum")
    trusted = deepcopy(GOOD_RECORD)
    trusted["reference_completeness"].update({
        "status": "audited_sufficient",
        "audit_source": "pytest server-verified reference audit fixture",
        "audit_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    })
    model = SequenceRecord(**trusted)
    candidate_species = len({hit.taxon for hit in model.hits if str(hit.rank).lower() == "species"})
    trusted["reference_completeness"]["attestation"] = attest_reference_completeness(
        model,
        candidate_species_in_hits=candidate_species,
    )
    request = request_with_records("DwC-A integration", [trusted])
    request["dataset_metadata"] = valid_pack()["request"]["dataset_metadata"]

    pack = run_barcode_compiler(BarcodeCompilerRequest(**request))
    names = {item["name"] for item in pack["exports"]}

    record = pack["records"][0]
    assert record["publication_status"] == "candidate-for-gbif-validation"
    assert record["publication_bucket"] == "validation_candidate"
    assert record["publication_status_compatibility"] == "gbif-ready"
    assert record["publication_bucket_compatibility"] == "gbif_ready"
    assert {"dwca.zip", "dwca_validation_report.json", "dwca_roundtrip_contract.json"} <= names
    assert {
        "dwc_occurrence_core_validation_candidates.csv",
        "dna_derived_extension_validation_candidates.csv",
    } <= names
    assert pack["summary"]["dwca_local_validation_status"] == "pass"
    assert pack["summary"]["dwca_release_gate"] == "blocked_external_validation"
    assert pack["dwca_validation"]["external_validation"]["ipt_ingestion"] == "not_run"
    with zipfile.ZipFile(barcode_artifact_path(pack["run"]["run_id"], "dwca.zip")) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {"occurrence.txt", "dna_derived_data.txt", "meta.xml", "eml.xml"}


def valid_archive_files() -> dict[str, bytes]:
    result = build_dwca_package(valid_pack())
    assert result["archive"] is not None
    with zipfile.ZipFile(io.BytesIO(result["archive"])) as archive:
        return {name: archive.read(name) for name in archive.namelist()}
