from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StrictInt, field_validator


Rank = Literal[
    "kingdom",
    "phylum",
    "class",
    "order",
    "family",
    "genus",
    "species",
    "none",
    "unranked",
]

AssayType = Literal[
    "single_specimen_barcode",
    "metabarcoding",
    "qpcr_ddpcr",
    "custom_targeted",
    "unknown",
]

MAX_SEQUENCE_BASES = 100_000
MAX_SEARCH_SEQUENCE_BASES = 25_000
MAX_RECORDS_PER_COMPILER_RUN = 500
MAX_HITS_PER_RECORD = 200


# Holdout metrics cross an external trust boundary. Keep numbers strict so JSON
# strings and booleans cannot be silently coerced into scientific measurements,
# and reject NaN/infinities before they can be signed into a manifest. ``None``
# remains representable so an incomplete informational manifest can be returned;
# the scientific release gate rejects it fail-closed.
FiniteMetricFloat = Annotated[float, Field(strict=True, allow_inf_nan=False)]
HoldoutMetricValue = StrictInt | FiniteMetricFloat | None


class TaxonLineageItem(BaseModel):
    rank: Rank | str
    name: str = Field(min_length=1, max_length=500)
    taxon_key: int | None = Field(default=None, ge=1)


class ReferenceHit(BaseModel):
    taxon: str = Field(min_length=1, max_length=500)
    rank: Rank | str = "species"
    identity: float = Field(ge=0, le=100, description="Percent identity, e.g. 99.6")
    query_coverage: float = Field(ge=0, le=100, description="Percent query coverage, e.g. 96")
    aligned_length: int | None = Field(default=None, ge=1)
    query_start: int | None = Field(default=None, ge=1)
    query_end: int | None = Field(default=None, ge=1)
    reference_start: int | None = Field(default=None, ge=1)
    reference_end: int | None = Field(default=None, ge=1)
    strand: Literal["forward", "reverse", "unknown"] = "unknown"
    mismatch_count: int | None = Field(default=None, ge=0)
    gap_count: int | None = Field(default=None, ge=0)
    bit_score: float | None = None
    evalue: float | None = None
    reference_id: str | None = Field(default=None, max_length=500)
    reference_database: str | None = Field(default=None, max_length=1_000)
    gbif_taxon_key: int | None = Field(default=None, ge=1)
    lineage: list[TaxonLineageItem] = Field(default_factory=list, max_length=32)


class BarcodeGapEvidence(BaseModel):
    intra_max_distance: float | None = Field(default=None, ge=0, le=1)
    inter_min_distance: float | None = Field(default=None, ge=0, le=1)
    target_reference_count: int | None = Field(default=None, ge=0)
    target_specimen_count: int | None = Field(default=None, ge=0)
    intra_pair_count: int | None = Field(default=None, ge=0)
    inter_taxon_count: int | None = Field(default=None, ge=0)
    inter_reference_count: int | None = Field(default=None, ge=0)
    inter_pair_count: int | None = Field(default=None, ge=0)
    distance_method: str | None = None
    minimum_aligned_sites: int | None = Field(default=None, ge=0)
    gap_ci_lower: float | None = Field(default=None, ge=-1, le=1)
    gap_ci_upper: float | None = Field(default=None, ge=-1, le=1)
    bootstrap_replicates: int | None = Field(default=None, ge=0)
    bootstrap_method: str | None = None


class DiagnosticKmerEvidence(BaseModel):
    diagnostic_kmers: list[str] = Field(default_factory=list, max_length=10_000)
    reference_total_windows: int | None = Field(default=None, ge=1)
    epsilon: float = Field(default=0.01, gt=0, lt=1)
    alpha: float = Field(default=0.01, gt=0, lt=1)
    k: int | None = Field(default=None, ge=1, le=64)
    target_sequence_count: int | None = Field(default=None, ge=0)
    negative_taxon_count: int | None = Field(default=None, ge=0)
    negative_sequence_count: int | None = Field(default=None, ge=0)
    conservation_fraction: float | None = Field(default=None, ge=0, le=1)
    canonicalized: bool = False
    reverse_complement_checked: bool = False
    background_scope: str | None = None


class EvidenceAttestation(BaseModel):
    """Short-lived, domain-separated attestation issued by a configured trusted process.

    The signature is an HMAC over the canonical evidence payload plus every field in
    this envelope except ``signature``.  The signing secret is server configuration;
    it is never part of an API request, response or repository fixture.
    """

    version: Literal["ecogenesis-evidence-attestation-v1"] = "ecogenesis-evidence-attestation-v1"
    algorithm: Literal["hmac-sha256"] = "hmac-sha256"
    purpose: Literal["external_holdout", "reference_completeness"]
    key_id: str = Field(min_length=1, max_length=200)
    issued_at: str = Field(min_length=1, max_length=100)
    expires_at: str = Field(min_length=1, max_length=100)
    nonce: str = Field(pattern=r"^[0-9a-fA-F]{32,128}$")
    payload_sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    signature: str = Field(pattern=r"^[0-9a-fA-F]{64}$")


class ReferenceCompletenessEvidence(BaseModel):
    status: Literal["audited_sufficient", "incomplete", "not_evaluated"] = "not_evaluated"
    target_taxon_reference_count: int | None = Field(default=None, ge=0)
    target_taxon_specimen_count: int | None = Field(default=None, ge=0)
    close_relative_taxa_expected: int | None = Field(default=None, ge=0)
    close_relative_taxa_represented: int | None = Field(default=None, ge=0)
    negative_reference_taxa_count: int | None = Field(default=None, ge=0)
    negative_reference_sequence_count: int | None = Field(default=None, ge=0)
    geographic_regions_count: int | None = Field(default=None, ge=0)
    audit_source: str | None = None
    audit_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    notes: str | None = None
    attestation: EvidenceAttestation | None = None


class SequenceQCEvidence(BaseModel):
    chimera_status: Literal["pass", "fail", "not_evaluated"] = "not_evaluated"
    chimera_method: str | None = None
    chimera_reference_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    supplied_orientation: Literal["forward", "reverse", "unknown"] = "unknown"


class ExternalValidationManifest(BaseModel):
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    source: str = Field(min_length=1)
    doi_or_url: str = Field(min_length=1)
    license: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    holdout: bool
    thresholds_frozen_before_holdout: bool
    ground_truth_independent: bool
    specimen_backed: bool
    generated_from_demo_fixtures: bool = False
    record_count: int = Field(ge=1)
    unique_case_count: int = Field(ge=1)
    marker_families: list[str] = Field(min_length=1)
    taxonomic_groups: list[str] = Field(min_length=1)
    evaluated_at: str = Field(min_length=1)
    harness_version: str = Field(min_length=1)
    compiler_contract_sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    metrics: dict[str, HoldoutMetricValue] = Field(default_factory=dict)
    baseline_metrics: dict[str, HoldoutMetricValue] = Field(default_factory=dict)
    strata: dict[str, dict[str, dict[str, HoldoutMetricValue]]] = Field(default_factory=dict)
    attestation: EvidenceAttestation | None = None


class SequenceRecord(BaseModel):
    sequence_id: str = Field(min_length=1, max_length=500)
    sequence: str = Field(min_length=1, max_length=MAX_SEQUENCE_BASES)
    metadata: dict[str, Any] = Field(default_factory=dict)
    hits: list[ReferenceHit] = Field(default_factory=list, max_length=MAX_HITS_PER_RECORD)
    barcode_gap: BarcodeGapEvidence | None = None
    diagnostic: DiagnosticKmerEvidence | None = None
    reference_completeness: ReferenceCompletenessEvidence | None = None
    sequence_qc: SequenceQCEvidence | None = None

    @field_validator("sequence")
    @classmethod
    def normalize_sequence(cls, value: str) -> str:
        compact = "".join(value.split()).upper()
        if not compact:
            raise ValueError("sequence cannot be empty")
        invalid = sorted(set(compact) - set("ACGTRYSWKMBDHVN-"))
        if invalid:
            raise ValueError(f"sequence contains unsupported characters: {''.join(invalid)}")
        return compact.replace("-", "")


class DatasetMetadata(BaseModel):
    title: str | None = None
    description: str | None = None
    publishingOrganization: str | None = None
    type: str | None = None
    license: str | None = None
    contact: list[dict[str, Any]] = Field(default_factory=list)
    creator: list[str] = Field(default_factory=list)
    metadataProvider: list[str] = Field(default_factory=list)
    citation: str | None = None
    citationIdentifier: str | None = None
    datasetID: str | None = None
    language: str = "eng"
    metadataLanguage: str = "eng"


class ReferenceManifest(BaseModel):
    db_name: str
    db_version: str | None = None
    source: str = "user_supplied"
    accessed_at: str | None = None
    doi_or_url: str | None = None
    license: str | None = None
    sha256: str | None = None


class BarcodeCompilerRequest(BaseModel):
    project_title: str = Field(default="Aedes albopictus COI publication check", min_length=2, max_length=500)
    marker: str = Field(default="COI-5P", min_length=2, max_length=200)
    marker_profile: str | None = Field(default=None, description="Optional marker profile id, e.g. coi_full_barcode")
    assay_type: AssayType = "single_specimen_barcode"
    reference_database: str = Field(default="COI Animals / BOLD public clustered reference", min_length=2, max_length=1_000)
    method_or_sop: str = Field(default="GBIF Sequence ID-compatible BLAST workflow with deterministic rank gates", min_length=2, max_length=10_000)
    ruleset_version: str = Field(default="barcode-gbif-compiler-v2", max_length=200)
    dataset_metadata: DatasetMetadata = Field(default_factory=DatasetMetadata)
    reference_manifest: ReferenceManifest | None = None
    external_validation_manifest: ExternalValidationManifest | None = None
    records: list[SequenceRecord] = Field(min_length=1, max_length=MAX_RECORDS_PER_COMPILER_RUN)


class BarcodeCompilerCreated(BaseModel):
    run_id: str
    status: str
    summary: dict[str, Any]
    exports: list[dict[str, Any]]


class BarcodeReferenceSearchRequest(BaseModel):
    sequence_id: str = Field(default="query-sequence", min_length=1, max_length=500, pattern=r"^[^\r\n>]+$")
    sequence: str = Field(min_length=1, max_length=MAX_SEARCH_SEQUENCE_BASES)
    reference_dataset: str = Field(default="aedes_coi_mini", min_length=1, max_length=200)
    backend: Literal["auto", "vsearch", "blastn", "python-local"] = "auto"
    max_hits: int = Field(default=5, ge=1, le=25)
    compile: bool = True
    project_title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BarcodeFragmentGraphRequest(BaseModel):
    sequence_id: str = Field(default="fragment-001", min_length=1, max_length=500, pattern=r"^[^\r\n>]+$")
    sequence: str = Field(min_length=1, max_length=MAX_SEARCH_SEQUENCE_BASES)
    reference_dataset: str = Field(default="ncbi_aedes_coi_small", min_length=1, max_length=200)
    backend: Literal["auto", "vsearch", "blastn", "python-local"] = "auto"
    max_hits: int = Field(default=50, ge=1, le=200)
