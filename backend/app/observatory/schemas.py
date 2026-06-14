from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


ObservatoryMode = Literal["live_gbif_small", "offline_demo", "cached_snapshot"]


class ObservatoryRunRequest(BaseModel):
    mode: ObservatoryMode = Field(
        default="live_gbif_small",
        description="Small live GBIF demo with fixture fallback, deterministic offline demo, or cached snapshot replay.",
    )
    taxon: str = Field(default="Aedes albopictus", min_length=2)
    taxon_key: int = Field(default=1651430, ge=1)
    bbox: list[float] = Field(default_factory=lambda: [-9.5, 35.5, 4.5, 44.5])
    limit: int = Field(default=50, ge=1, le=300)
    ruleset_version: str = Field(default="GSIG-OBS-1.0+barcode-gbif-compiler-v2")
    force_fixture: bool = Field(default=False)

    @field_validator("mode", mode="before")
    @classmethod
    def normalize_mode(cls, value: str) -> str:
        aliases = {
            "live-gbif-small": "live_gbif_small",
            "offline-demo": "offline_demo",
            "cached-snapshot": "cached_snapshot",
        }
        return aliases.get(value, value)

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, value: list[float]) -> list[float]:
        if len(value) != 4:
            raise ValueError("bbox must contain [west, south, east, north]")
        west, south, east, north = value
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("bbox must be a valid WGS84 bounding box")
        return value


class ObservatoryRunCreated(BaseModel):
    run_id: str
    status: str
    summary: dict
    exports: list[dict]
