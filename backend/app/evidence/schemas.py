from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


Purpose = Literal[
    "conservation_brief",
    "invasive_watch",
    "sampling_gaps",
    "dataset_quality_review",
]

SourceMode = Literal[
    "fixture",
    "online",
    "online_with_fixture_fallback",
    "online_with_empty_fallback",
]


class EvidenceRunRequest(BaseModel):
    taxon: str = Field(default="Aedes albopictus", min_length=2)
    taxon_key: int | None = Field(default=None, ge=1)
    region_name: str = Field(default="Spain GBIF bbox", min_length=2)
    bbox: list[float] = Field(default=[-10.0, 35.0, 4.5, 44.5], min_length=4, max_length=4)
    purpose: Purpose = "invasive_watch"
    source_mode: SourceMode | None = None
    use_fixture: bool = False
    max_records: int = Field(default=300, ge=1, le=2000)

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[float]) -> list[float]:
        west, south, east, north = value
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise ValueError("bbox longitude values must be within [-180, 180]")
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise ValueError("bbox latitude values must be within [-90, 90]")
        if west >= east or south >= north:
            raise ValueError("bbox must be [west, south, east, north]")
        return value


class EvidenceRunCreated(BaseModel):
    run_id: str
    status: str
    passport: dict
    exports: list[dict]
