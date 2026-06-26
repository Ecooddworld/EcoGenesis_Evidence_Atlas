from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

import requests

from .demo import POPULAR_TAXA


USER_AGENT = "ecogenesis-evidence-atlas/0.1 (+https://ecooddworld.eu)"


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
                "usageKey": 1651430,
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

    def species_by_key(self, taxon_key: int, *, taxon: str | None = None, use_fixture: bool = False) -> dict[str, Any]:
        if self.mode != "online" or use_fixture:
            match = next((item for item in POPULAR_TAXA if item.get("usageKey") == taxon_key), None)
            return match or {
                "usageKey": taxon_key,
                "scientificName": taxon or str(taxon_key),
                "canonicalName": taxon or str(taxon_key),
                "rank": "SPECIES",
                "status": "ACCEPTED",
                "confidence": 100,
                "matchType": "SELECTED_KEY",
                "source": "fixture",
            }
        response = requests.get(
            f"{self.base_url}/species/{taxon_key}",
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        payload["usageKey"] = payload.get("key") or taxon_key
        payload["confidence"] = 100
        payload["matchType"] = "SELECTED_KEY"
        payload["status"] = payload.get("taxonomicStatus") or payload.get("status")
        payload["source"] = "gbif_api"
        return payload

    def species_suggest(self, query: str, *, limit: int = 10, use_fixture: bool = False) -> list[dict[str, Any]]:
        clean_query = " ".join(query.split())
        if self.mode != "online" or use_fixture or len(clean_query) < 2:
            return _fixture_suggestions(clean_query, limit)
        response = requests.get(
            f"{self.base_url}/species/suggest",
            params={"q": clean_query, "limit": min(max(limit, 1), 20)},
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        response.raise_for_status()
        suggestions = [_normalize_taxon_suggestion(item) for item in response.json() if isinstance(item, dict)]
        ranked = [item for item in suggestions if item.get("usageKey") and item.get("scientificName")]
        return ranked[:limit] or _fixture_suggestions(clean_query, limit)

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

    def dataset_by_key(self, dataset_key: str, *, use_fixture: bool = False) -> dict[str, Any]:
        if self.mode != "online" or use_fixture or not dataset_key or dataset_key == "unknown_dataset":
            return {}
        response = requests.get(
            f"{self.base_url}/dataset/{dataset_key}",
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        payload["source"] = "gbif_api"
        return payload

    def organization_by_key(self, organization_key: str, *, use_fixture: bool = False) -> dict[str, Any]:
        if self.mode != "online" or use_fixture or not organization_key:
            return {}
        response = requests.get(
            f"{self.base_url}/organization/{organization_key}",
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        payload["source"] = "gbif_api"
        return payload


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


def _fixture_suggestions(query: str, limit: int) -> list[dict[str, Any]]:
    clean_query = query.lower().strip()
    rows = POPULAR_TAXA
    if clean_query:
        rows = [
            item
            for item in POPULAR_TAXA
            if clean_query in str(item.get("scientificName", "")).lower()
            or clean_query in str(item.get("canonicalName", "")).lower()
            or clean_query in str(item.get("family", "")).lower()
        ]
    return [dict(item) for item in rows[:limit]]


def _normalize_taxon_suggestion(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "usageKey": item.get("key") or item.get("usageKey") or item.get("nubKey"),
        "scientificName": item.get("scientificName") or item.get("canonicalName"),
        "canonicalName": item.get("canonicalName") or item.get("scientificName"),
        "rank": item.get("rank"),
        "status": item.get("taxonomicStatus") or item.get("status"),
        "kingdom": item.get("kingdom"),
        "family": item.get("family"),
        "confidence": 100 if item.get("key") else None,
        "source": "gbif_api",
    }


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
