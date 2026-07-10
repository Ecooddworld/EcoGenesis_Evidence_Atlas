from __future__ import annotations

import subprocess

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.barcode.schemas import BarcodeCompilerRequest, SequenceRecord
from app.barcode.search_backend import run_external_search_command, validate_uploaded_reference_size
from app.main import app
from app.security import heavy_request_gate, rate_limiter


@pytest.fixture(autouse=True)
def reset_security_state(monkeypatch: pytest.MonkeyPatch) -> None:
    rate_limiter.reset()
    heavy_request_gate.reset()
    monkeypatch.setenv("API_AUDIT_LOG_ENABLED", "false")
    yield
    rate_limiter.reset()
    heavy_request_gate.reset()


def test_required_authentication_fails_closed_and_protects_mutations(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_AUTH_REQUIRED", "true")
    client = TestClient(app)

    missing_configuration = client.get("/health")
    assert missing_configuration.status_code == 503

    monkeypatch.setenv("API_AUTH_TOKEN", "test-secret")
    assert client.get("/health").status_code == 200
    assert client.post("/api/barcode/run", json={}).status_code == 401
    authorized = client.post(
        "/api/barcode/run",
        json={},
        headers={"Authorization": "Bearer test-secret"},
    )
    assert authorized.status_code == 422


def test_rate_limit_and_request_body_limit_return_explicit_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(app)
    monkeypatch.setenv("API_RATE_LIMIT_WRITE_PER_MINUTE", "1")

    assert client.post("/api/barcode/run", json={}).status_code == 422
    limited = client.post("/api/barcode/run", json={})
    assert limited.status_code == 429
    assert limited.headers["retry-after"]
    assert limited.json()["request_id"] == limited.headers["x-request-id"]

    rate_limiter.reset()
    monkeypatch.setenv("API_MAX_REQUEST_BODY_BYTES", "1024")
    oversized = client.post(
        "/api/barcode/run",
        content=b"x" * 1025,
        headers={"Content-Type": "application/json"},
    )
    assert oversized.status_code == 413
    assert "1024 byte limit" in oversized.json()["detail"]


def test_heavy_request_concurrency_gate_rejects_excess_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("API_MAX_CONCURRENT_HEAVY_REQUESTS", "1")
    assert heavy_request_gate.acquire(1) is True
    response = TestClient(app).post("/api/barcode/run", json={})
    heavy_request_gate.release()

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"


def test_upload_limits_and_public_limit_configuration(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("EVIDENCE_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("USER_REFERENCE_DATA_DIR", str(tmp_path / "references"))
    monkeypatch.setenv("API_MAX_REFERENCE_UPLOAD_BYTES", "128")
    client = TestClient(app)

    response = client.post(
        "/api/barcode/reference-datasets/upload",
        files={"file": ("oversized.fasta", b">ref\n" + b"A" * 200, "text/plain")},
    )
    assert response.status_code == 413
    assert "Reference FASTA upload exceeds 128 byte limit" in response.json()["detail"]

    limits = client.get("/api/system/limits")
    assert limits.status_code == 200
    assert limits.json()["max_reference_upload_bytes"] == 128
    assert "api_token" not in limits.json()


def test_compiler_record_sequence_and_hit_limits() -> None:
    base_record = {"sequence_id": "record", "sequence": "ACGT", "hits": []}
    with pytest.raises(ValidationError):
        BarcodeCompilerRequest(records=[base_record] * 501)

    with pytest.raises(ValidationError):
        SequenceRecord(
            sequence_id="record",
            sequence="ACGT",
            hits=[{"taxon": "Aedes", "identity": 99, "query_coverage": 99}] * 201,
        )

    with pytest.raises(ValidationError):
        SequenceRecord(sequence_id="record", sequence="A" * 100_001)


def test_reference_and_external_process_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_REFERENCE_RECORDS", "1")
    with pytest.raises(ValueError, match="limit is 1"):
        validate_uploaded_reference_size([("one", "ACGT"), ("two", "ACGT")])

    monkeypatch.setenv("BARCODE_SEARCH_TIMEOUT_SECONDS", "2")

    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr("app.barcode.search_backend.subprocess.run", timeout)
    with pytest.raises(ValueError, match="2-second execution limit"):
        run_external_search_command(["vsearch", "--version"], label="VSEARCH")
