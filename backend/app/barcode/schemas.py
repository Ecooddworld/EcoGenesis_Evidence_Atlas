from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


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


class TaxonLineageItem(BaseModel):
    rank: Rank | str
    name: str = Field(min_length=1)
    taxon_key: int | None = Field(default=None, ge=1)


class ReferenceHit(BaseModel):
    taxon: str = Field(min_length=1)
    rank: Rank | str = "species"
    identity: float = Field(ge=0, le=100, description="Percent identity, e.g. 99.6")
    query_coverage: float = Field(ge=0, le=100, description="Percent query coverage, e.g. 96")
    aligned_length: int | None = Field(default=None, ge=1)
    bit_score: float | None = None
    evalue: float | None = None
    reference_id: str | None = None
    reference_database: str | None = None
    gbif_taxon_key: int | None = Field(default=None, ge=1)
    lineage: list[TaxonLineageItem] = Field(default_factory=list)


class BarcodeGapEvidence(BaseModel):
    intra_max_distance: float | None = Field(default=None, ge=0, le=1)
    inter_min_distance: float | None = Field(default=None, ge=0, le=1)


class DiagnosticKmerEvidence(BaseModel):
    diagnostic_kmers: list[str] = Field(default_factory=list)
    reference_total_windows: int | None = Field(default=None, ge=1)
    epsilon: float = Field(default=0.01, gt=0, lt=1)
    alpha: float = Field(default=0.01, gt=0, lt=1)
    k: int | None = Field(default=None, ge=1, le=64)


class SequenceRecord(BaseModel):
    sequence_id: str = Field(min_length=1)
    sequence: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    hits: list[ReferenceHit] = Field(default_factory=list)
    barcode_gap: BarcodeGapEvidence | None = None
    diagnostic: DiagnosticKmerEvidence | None = None

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


class ReferenceManifest(BaseModel):
    db_name: str
    db_version: str | None = None
    source: str = "user_supplied"
    accessed_at: str | None = None
    doi_or_url: str | None = None
    license: str | None = None
    sha256: str | None = None


class BarcodeCompilerRequest(BaseModel):
    project_title: str = Field(default="Aedes albopictus COI publication check", min_length=2)
    marker: str = Field(default="COI-5P", min_length=2)
    marker_profile: str | None = Field(default=None, description="Optional marker profile id, e.g. coi_full_barcode")
    assay_type: AssayType = "single_specimen_barcode"
    reference_database: str = Field(default="COI Animals / BOLD public clustered reference", min_length=2)
    method_or_sop: str = Field(default="GBIF Sequence ID-compatible BLAST workflow with deterministic rank gates", min_length=2)
    ruleset_version: str = Field(default="barcode-gbif-compiler-v2")
    dataset_metadata: DatasetMetadata = Field(default_factory=DatasetMetadata)
    reference_manifest: ReferenceManifest | None = None
    records: list[SequenceRecord] = Field(min_length=1)


class BarcodeCompilerCreated(BaseModel):
    run_id: str
    status: str
    summary: dict[str, Any]
    exports: list[dict[str, Any]]


class BarcodeReferenceSearchRequest(BaseModel):
    sequence_id: str = Field(default="query-sequence", min_length=1)
    sequence: str = Field(min_length=1)
    reference_dataset: str = Field(default="aedes_coi_mini", min_length=1)
    backend: Literal["auto", "vsearch", "blastn", "python-local"] = "auto"
    max_hits: int = Field(default=5, ge=1, le=25)
    compile: bool = True
    project_title: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
