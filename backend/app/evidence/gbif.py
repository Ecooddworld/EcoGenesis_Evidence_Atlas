from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

import requests


USER_AGENT = "ecogenesis-evidence-atlas/0.1 (+https://github.com/oddworld666/EcoGenesis_Evidence_Atlas)"


@dataclass(frozen=True)
class NormalizedOccurrence:
    gbif_id: str
    dataset_key: str
    dataset_title: str | None
    publisher: str | None
    license: str | None
    scientific_name: str | None
    accepted_taxon_key: str | None
    taxon_key: str | None
    latitude: float | None
    longitude: float | None
    event_date: str | None
    year: int | None
    coordinate_uncertainty_m: float | None
    country: str | None
    country_code: str | None
    basis_of_record: str | None
    issues: list[str]
    raw: dict[str, Any]

    @property
    def has_valid_coordinate(self) -> bool:
        return (
            self.latitude is not None
            and self.longitude is not None
            and -90.0 <= self.latitude <= 90.0
            and -180.0 <= self.longitude <= 180.0
        )

    @property
    def species_identifier(self) -> str:
        if self.accepted_taxon_key:
            return f"taxon:{self.accepted_taxon_key}"
        if self.scientific_name:
            return f"name:{' '.join(self.scientific_name.lower().split())}"
        return "taxon:unknown"


class GBIFClient:
    def __init__(self, *, mode: str = "fixture", base_url: str | None = None, fixture_dir: Path | None = None) -> None:
        self.mode = mode
        self.base_url = (base_url or os.getenv("GBIF_BASE_URL") or "https://api.gbif.org/v1").rstrip("/")
        self.fixture_dir = fixture_dir or Path(__file__).resolve().parents[2] / "fixtures" / "gbif"

    def species_match(self, taxon: str, *, use_fixture: bool = False) -> dict[str, Any]:
        if self.mode != "online" or use_fixture:
            return {
                "usageKey": 5844304,
                "scientificName": taxon,
                "canonicalName": taxon,
                "rank": "SPECIES",
                "status": "ACCEPTED",
                "confidence": 97,
                "matchType": "EXACT",
                "source": "fixture",
            }
        response = requests.get(
            f"{self.base_url}/species/match",
            params={"name": taxon},
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        payload["source"] = "gbif_api"
        return payload

    def occurrence_search(
        self,
        *,
        taxon_key: int | None,
        bbox: list[float],
        limit: int,
        use_fixture: bool = False,
    ) -> dict[str, Any]:
        if self.mode != "online" or use_fixture:
            return json.loads((self.fixture_dir / "aedes_albopictus_spain.json").read_text(encoding="utf-8"))

        west, south, east, north = bbox
        geometry = f"POLYGON(({west} {south},{east} {south},{east} {north},{west} {north},{west} {south}))"
        params: dict[str, Any] = {
            "hasCoordinate": "true",
            "geometry": geometry,
            "limit": min(limit, 300),
        }
        if taxon_key:
            params["taxonKey"] = taxon_key
        response = requests.get(
            f"{self.base_url}/occurrence/search",
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=45,
        )
        response.raise_for_status()
        return response.json()


def normalize_occurrences(payload: dict[str, Any], *, max_records: int) -> list[NormalizedOccurrence]:
    records: list[NormalizedOccurrence] = []
    for item in (payload.get("results") or [])[:max_records]:
        if not isinstance(item, dict):
            continue
        dataset_key = str(item.get("datasetKey") or "unknown_dataset")
        latitude = _float_or_none(item.get("decimalLatitude"))
        longitude = _float_or_none(item.get("decimalLongitude"))
        event_date = item.get("eventDate") or item.get("dateIdentified")
        year = _int_or_none(item.get("year")) or _year_from_date(event_date)
        issues = item.get("issues") if isinstance(item.get("issues"), list) else []
        record = NormalizedOccurrence(
            gbif_id=str(item.get("key") or item.get("gbifID") or ""),
            dataset_key=dataset_key,
            dataset_title=item.get("datasetName") or item.get("datasetTitle"),
            publisher=item.get("publisher"),
            license=item.get("license"),
            scientific_name=item.get("scientificName"),
            accepted_taxon_key=_text_or_none(item.get("acceptedTaxonKey") or item.get("speciesKey") or item.get("taxonKey")),
            taxon_key=_text_or_none(item.get("taxonKey")),
            latitude=latitude,
            longitude=longitude,
            event_date=event_date,
            year=year,
            coordinate_uncertainty_m=_float_or_none(item.get("coordinateUncertaintyInMeters")),
            country=item.get("country"),
            country_code=item.get("countryCode"),
            basis_of_record=item.get("basisOfRecord"),
            issues=[str(issue) for issue in issues],
            raw=item,
        )
        records.append(record)
    return records


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_or_none(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _year_from_date(value: Any) -> int | None:
    if not value:
        return None
    text = str(value)
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt).year
        except ValueError:
            continue
    return None

