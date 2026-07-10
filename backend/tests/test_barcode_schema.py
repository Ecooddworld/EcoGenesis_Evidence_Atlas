from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import DEFAULT_BARCODE_REQUEST
from app.barcode.schemas import BarcodeCompilerRequest


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "barcode_evidence_pack.schema.json"


def test_generated_evidence_pack_satisfies_public_json_schema(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)

    pack = run_barcode_compiler(BarcodeCompilerRequest(**DEFAULT_BARCODE_REQUEST))
    Draft202012Validator(schema).validate(pack)

    serialized_schema = json.dumps(schema)
    assert "formal_gbif_ready" not in serialized_schema
    assert "candidate_for_gbif_validation" in serialized_schema
