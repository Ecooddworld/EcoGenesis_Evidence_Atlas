from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import asdict, dataclass
import hmac
import logging
import os
import re
import threading
import time
from typing import Deque
from uuid import uuid4

from fastapi import UploadFile
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


LOGGER = logging.getLogger("ecogenesis.security")
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
HEAVY_MUTATION_PATHS = {
    "/api/barcode/search",
    "/api/barcode/fragment-graph",
    "/api/barcode/run",
    "/api/barcode/run-csv",
    "/api/evidence/run",
    "/api/observatory/run-demo",
}


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        LOGGER.warning("Ignoring invalid integer configuration %s=%r", name, raw)
        return default
    if value < minimum or (maximum is not None and value > maximum):
        LOGGER.warning("Ignoring out-of-range configuration %s=%r", name, raw)
        return default
    return value


@dataclass(frozen=True)
class SecuritySettings:
    auth_required: bool
    auth_configured: bool
    auth_protect_run_reads: bool
    api_token: str | None
    read_rate_limit_per_minute: int
    write_rate_limit_per_minute: int
    max_request_body_bytes: int
    max_csv_upload_bytes: int
    max_reference_upload_bytes: int
    max_concurrent_heavy_requests: int
    reference_uploads_enabled: bool
    trust_proxy_headers: bool
    audit_log_enabled: bool

    @classmethod
    def from_env(cls) -> "SecuritySettings":
        token = os.getenv("API_AUTH_TOKEN", "").strip() or None
        required = _env_bool("API_AUTH_REQUIRED", False)
        return cls(
            auth_required=required,
            auth_configured=bool(token),
            auth_protect_run_reads=_env_bool("API_AUTH_PROTECT_RUN_READS", False),
            api_token=token,
            read_rate_limit_per_minute=_env_int("API_RATE_LIMIT_READ_PER_MINUTE", 600, maximum=100_000),
            write_rate_limit_per_minute=_env_int("API_RATE_LIMIT_WRITE_PER_MINUTE", 120, maximum=100_000),
            max_request_body_bytes=_env_int(
                "API_MAX_REQUEST_BODY_BYTES",
                12 * 1024 * 1024,
                minimum=1024,
                maximum=1024 * 1024 * 1024,
            ),
            max_csv_upload_bytes=_env_int(
                "API_MAX_CSV_UPLOAD_BYTES",
                2 * 1024 * 1024,
                minimum=128,
                maximum=256 * 1024 * 1024,
            ),
            max_reference_upload_bytes=_env_int(
                "API_MAX_REFERENCE_UPLOAD_BYTES",
                10 * 1024 * 1024,
                minimum=128,
                maximum=512 * 1024 * 1024,
            ),
            max_concurrent_heavy_requests=_env_int(
                "API_MAX_CONCURRENT_HEAVY_REQUESTS",
                4,
                minimum=1,
                maximum=128,
            ),
            reference_uploads_enabled=_env_bool("REFERENCE_UPLOADS_ENABLED", True),
            trust_proxy_headers=_env_bool("TRUST_PROXY_HEADERS", False),
            audit_log_enabled=_env_bool("API_AUDIT_LOG_ENABLED", True),
        )

    def validate(self) -> None:
        if self.auth_required and not self.api_token:
            raise RuntimeError("API_AUTH_REQUIRED is true but API_AUTH_TOKEN is not configured")

    def public_configuration(self) -> dict[str, object]:
        payload = asdict(self)
        payload.pop("api_token", None)
        payload["authentication"] = (
            "required"
            if self.auth_required
            else "optional_configured" if self.auth_configured else "optional_disabled"
        )
        return payload


class SlidingWindowRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, *, limit: int, now: float | None = None) -> tuple[bool, int, int]:
        if limit <= 0:
            return True, 0, 0
        current = time.monotonic() if now is None else now
        cutoff = current - 60.0
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(61 - (current - events[0])))
                return False, 0, retry_after
            events.append(current)
            return True, max(0, limit - len(events)), 0

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


rate_limiter = SlidingWindowRateLimiter()


class ConcurrencyGate:
    def __init__(self) -> None:
        self._active = 0
        self._lock = threading.Lock()

    def acquire(self, limit: int) -> bool:
        with self._lock:
            if self._active >= limit:
                return False
            self._active += 1
            return True

    def release(self) -> None:
        with self._lock:
            self._active = max(0, self._active - 1)

    def reset(self) -> None:
        with self._lock:
            self._active = 0


heavy_request_gate = ConcurrencyGate()


class ApiSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = SecuritySettings.from_env()
        request_id = request.headers.get("x-request-id", "")
        if not REQUEST_ID_PATTERN.fullmatch(request_id):
            request_id = uuid4().hex

        started = time.monotonic()
        status_code = 500
        client_id = _client_identifier(request, settings)
        heavy_slot_acquired = False
        try:
            configuration_error = _configuration_error(settings)
            if configuration_error:
                status_code = 503
                return _json_error(status_code, configuration_error, request_id=request_id)

            body_error = _body_size_error(request, settings)
            if body_error:
                status_code = 413
                return _json_error(status_code, body_error, request_id=request_id)

            auth_error = _authentication_error(request, settings)
            if auth_error:
                status_code = 401
                return _json_error(
                    status_code,
                    auth_error,
                    request_id=request_id,
                    headers={"WWW-Authenticate": "Bearer"},
                )

            limit = (
                settings.write_rate_limit_per_minute
                if request.method.upper() in UNSAFE_METHODS
                else settings.read_rate_limit_per_minute
            )
            bucket = "write" if request.method.upper() in UNSAFE_METHODS else "read"
            allowed, remaining, retry_after = rate_limiter.check(f"{client_id}:{bucket}", limit=limit)
            if not allowed:
                status_code = 429
                return _json_error(
                    status_code,
                    "request rate limit exceeded",
                    request_id=request_id,
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                    },
                )

            if request.method.upper() in UNSAFE_METHODS and request.url.path in HEAVY_MUTATION_PATHS:
                heavy_slot_acquired = heavy_request_gate.acquire(settings.max_concurrent_heavy_requests)
                if not heavy_slot_acquired:
                    status_code = 503
                    return _json_error(
                        status_code,
                        "heavy-request concurrency limit reached; retry later",
                        request_id=request_id,
                        headers={"Retry-After": "5"},
                    )

            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            return response
        finally:
            if heavy_slot_acquired:
                heavy_request_gate.release()
            if settings.audit_log_enabled:
                LOGGER.info(
                    "request_id=%s client=%s method=%s path=%s status=%s duration_ms=%s",
                    request_id,
                    client_id,
                    request.method,
                    request.url.path,
                    status_code,
                    round((time.monotonic() - started) * 1000, 2),
                )


def _configuration_error(settings: SecuritySettings) -> str | None:
    try:
        settings.validate()
    except RuntimeError as exc:
        LOGGER.error("Security configuration error: %s", exc)
        return "API authentication is required but not configured"
    return None


def _body_size_error(request: Request, settings: SecuritySettings) -> str | None:
    raw_length = request.headers.get("content-length")
    if raw_length is None:
        return None
    try:
        content_length = int(raw_length)
    except ValueError:
        return "invalid Content-Length header"
    if content_length < 0:
        return "invalid Content-Length header"
    if content_length > settings.max_request_body_bytes:
        return f"request body exceeds {settings.max_request_body_bytes} byte limit"
    return None


def _authentication_error(request: Request, settings: SecuritySettings) -> str | None:
    is_api_mutation = request.method.upper() in UNSAFE_METHODS and request.url.path.startswith("/api/")
    is_protected_read = (
        settings.auth_protect_run_reads
        and request.method.upper() in {"GET", "HEAD"}
        and _is_runtime_artifact_path(request.url.path)
    )
    if not is_api_mutation and not is_protected_read:
        return None
    if not settings.auth_required:
        return None
    supplied = _supplied_token(request)
    if not supplied or not settings.api_token or not hmac.compare_digest(supplied, settings.api_token):
        return "valid bearer token required for mutation endpoints"
    return None


def _supplied_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token.strip():
        return token.strip()
    legacy_header = request.headers.get("x-api-key", "").strip()
    return legacy_header or None


def _client_identifier(request: Request, settings: SecuritySettings) -> str:
    if settings.trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for", "")
        proxy_appended = forwarded.rsplit(",", 1)[-1].strip()
        if proxy_appended:
            return proxy_appended[:128]
    if request.client:
        return str(request.client.host)[:128]
    return "unknown"


def _is_runtime_artifact_path(path: str) -> bool:
    return "/runs" in path or "/exports" in path


def _json_error(
    status_code: int,
    detail: str,
    *,
    request_id: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response_headers = {"X-Request-ID": request_id, "X-Content-Type-Options": "nosniff"}
    response_headers.update(headers or {})
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "request_id": request_id},
        headers=response_headers,
    )


async def read_upload_limited(file: UploadFile, *, max_bytes: int, label: str) -> bytes:
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        await file.close()
        from fastapi import HTTPException

        raise HTTPException(status_code=413, detail=f"{label} exceeds {max_bytes} byte limit")
    return content
