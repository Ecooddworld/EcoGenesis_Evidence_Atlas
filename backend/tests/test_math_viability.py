from __future__ import annotations

from app.barcode.compiler import run_barcode_compiler
from app.barcode.demo import DEFAULT_BARCODE_REQUEST
from app.barcode.math_audit import audit_pack_math
from app.barcode.schemas import BarcodeCompilerRequest
from scripts.verify_math_viability import build_math_viability_report


def test_math_viability_audit_passes_for_default_pack(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    pack = run_barcode_compiler(BarcodeCompilerRequest(**DEFAULT_BARCODE_REQUEST))
    audit = audit_pack_math(pack, scope="pytest_default_pack")

    assert audit["summary"]["status"] == "pass"
    assert audit["summary"]["failed"] == 0
    assert audit["unit_contract"]["api_identity_query_coverage"] == "percent values in [0, 100]"


def test_math_viability_report_checks_edge_cases(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))

    report = build_math_viability_report()

    assert report["summary"]["status"] == "pass"
    assert report["summary"]["packs"] == 2
    assert report["summary"]["failed"] == 0
