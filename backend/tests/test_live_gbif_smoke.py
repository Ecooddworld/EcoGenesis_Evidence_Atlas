from __future__ import annotations

import os

import pytest

from app.evidence.pipeline import run_evidence_passport
from app.evidence.schemas import EvidenceRunRequest


@pytest.mark.skipif(os.getenv("RUN_LIVE_GBIF_SMOKE") != "1", reason="set RUN_LIVE_GBIF_SMOKE=1 to call the GBIF API")
def test_live_gbif_smoke_aedes_spain(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = run_evidence_passport(
        EvidenceRunRequest(
            taxon="Aedes albopictus",
            taxon_key=1651430,
            region_name="Spain GBIF bbox",
            bbox=[-10.0, 35.0, 4.5, 44.5],
            purpose="invasive_watch",
            source_mode="online",
            use_fixture=False,
            max_records=100,
        )
    )

    assert pack["source_summary"]["gbif_api_status"] == "ok"
    assert pack["passport"]["records_used"] > 0
