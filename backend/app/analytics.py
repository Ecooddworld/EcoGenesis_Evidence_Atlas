from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException, Request
from pydantic import BaseModel, Field


class AnalyticsPageview(BaseModel):
    path: str = Field(default="/", max_length=320)
    title: str | None = Field(default=None, max_length=180)
    referrer: str | None = Field(default=None, max_length=520)
    timezone: str | None = Field(default=None, max_length=80)


def analytics_enabled() -> bool:
    return os.getenv("ANALYTICS_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def retention_days() -> int:
    try:
        return max(1, int(os.getenv("ANALYTICS_RETENTION_DAYS", "90")))
    except ValueError:
        return 90


def database_path() -> Path:
    configured = os.getenv("ANALYTICS_DB_PATH")
    if configured:
        return Path(configured)
    data_dir = Path(os.getenv("EVIDENCE_DATA_DIR", "/data/evidence"))
    return data_dir / "analytics" / "site_analytics.sqlite3"


def now_utc() -> datetime:
    return datetime.now(UTC)


def db_connect() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=8)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pageviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            day TEXT NOT NULL,
            path TEXT NOT NULL,
            title TEXT,
            referrer_host TEXT NOT NULL,
            visitor_hash TEXT NOT NULL,
            user_agent_family TEXT NOT NULL,
            device_type TEXT NOT NULL,
            language TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pageviews_day ON pageviews(day)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pageviews_path ON pageviews(path)")
    return conn


def tracking_blocked(request: Request) -> str | None:
    headers = request.headers
    if headers.get("dnt") == "1":
        return "dnt"
    if headers.get("sec-gpc") == "1" or headers.get("x-global-privacy-control") == "1":
        return "global_privacy_control"
    return None


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def visitor_hash(request: Request, day: str) -> str:
    secret = os.getenv("ANALYTICS_HASH_SECRET") or os.getenv("ANALYTICS_ADMIN_TOKEN") or "ecogenesis-local-analytics"
    message = f"{day}:{client_ip(request)}".encode("utf-8", errors="ignore")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def normalize_path(raw_path: str) -> str:
    parsed = urlparse(raw_path or "/")
    path = parsed.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if path.startswith("/api/"):
        path = "/api"
    return path[:240]


def referrer_host(referrer: str | None) -> str:
    if not referrer:
        return "direct"
    parsed = urlparse(referrer)
    host = parsed.netloc.lower()
    return host[:120] if host else "direct"


def user_agent_family(user_agent: str) -> str:
    ua = user_agent.lower()
    if any(token in ua for token in ("bot", "crawl", "spider", "slurp", "monitor")):
        return "bot"
    if "edg/" in ua or "edge/" in ua:
        return "edge"
    if "firefox/" in ua:
        return "firefox"
    if "chrome/" in ua or "chromium/" in ua or "crios/" in ua:
        return "chrome"
    if "safari/" in ua:
        return "safari"
    return "other"


def device_type(user_agent: str) -> str:
    ua = user_agent.lower()
    if any(token in ua for token in ("bot", "crawl", "spider", "monitor")):
        return "bot"
    if "ipad" in ua or "tablet" in ua:
        return "tablet"
    if "mobile" in ua or "iphone" in ua or "android" in ua:
        return "mobile"
    if user_agent:
        return "desktop"
    return "unknown"


def primary_language(accept_language: str) -> str:
    if not accept_language:
        return "unknown"
    first = accept_language.split(",", 1)[0].strip().lower()
    if not first:
        return "unknown"
    return first.split("-", 1)[0][:12]


def purge_old_rows(conn: sqlite3.Connection, current_time: datetime | None = None) -> None:
    cutoff = (current_time or now_utc()) - timedelta(days=retention_days())
    conn.execute("DELETE FROM pageviews WHERE ts < ?", (cutoff.isoformat(),))


def record_pageview(event: AnalyticsPageview, request: Request) -> dict:
    if not analytics_enabled():
        return {"tracked": False, "reason": "disabled"}
    blocked = tracking_blocked(request)
    if blocked:
        return {"tracked": False, "reason": blocked}

    current_time = now_utc()
    day = current_time.date().isoformat()
    user_agent = request.headers.get("user-agent", "")
    row = {
        "ts": current_time.isoformat(),
        "day": day,
        "path": normalize_path(event.path),
        "title": (event.title or "")[:180],
        "referrer_host": referrer_host(event.referrer),
        "visitor_hash": visitor_hash(request, day),
        "user_agent_family": user_agent_family(user_agent),
        "device_type": device_type(user_agent),
        "language": primary_language(request.headers.get("accept-language", "")),
    }
    with db_connect() as conn:
        purge_old_rows(conn, current_time)
        conn.execute(
            """
            INSERT INTO pageviews (
                ts, day, path, title, referrer_host, visitor_hash,
                user_agent_family, device_type, language
            )
            VALUES (
                :ts, :day, :path, :title, :referrer_host, :visitor_hash,
                :user_agent_family, :device_type, :language
            )
            """,
            row,
        )
    return {"tracked": True}


def require_admin_token(token: str | None) -> None:
    expected = os.getenv("ANALYTICS_ADMIN_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="analytics dashboard token is not configured")
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="invalid analytics token")


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    value = conn.execute(sql, params).fetchone()[0]
    return int(value or 0)


def grouped_rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def analytics_summary(token: str | None) -> dict:
    require_admin_token(token)
    current_time = now_utc()
    cutoff_24h = (current_time - timedelta(hours=24)).isoformat()
    cutoff_7d = (current_time - timedelta(days=7)).isoformat()
    cutoff_30d = (current_time - timedelta(days=30)).date().isoformat()

    with db_connect() as conn:
        purge_old_rows(conn, current_time)
        totals = {
            "pageviews_24h": scalar(conn, "SELECT COUNT(*) FROM pageviews WHERE ts >= ?", (cutoff_24h,)),
            "visitors_24h": scalar(
                conn,
                "SELECT COUNT(DISTINCT visitor_hash) FROM pageviews WHERE ts >= ?",
                (cutoff_24h,),
            ),
            "pageviews_7d": scalar(conn, "SELECT COUNT(*) FROM pageviews WHERE ts >= ?", (cutoff_7d,)),
            "visitors_7d": scalar(
                conn,
                "SELECT COUNT(DISTINCT day || ':' || visitor_hash) FROM pageviews WHERE ts >= ?",
                (cutoff_7d,),
            ),
            "stored_pageviews": scalar(conn, "SELECT COUNT(*) FROM pageviews"),
        }
        daily = grouped_rows(
            conn,
            """
            SELECT day, COUNT(*) AS pageviews, COUNT(DISTINCT visitor_hash) AS visitors
            FROM pageviews
            WHERE day >= ?
            GROUP BY day
            ORDER BY day DESC
            LIMIT 30
            """,
            (cutoff_30d,),
        )
        top_pages = grouped_rows(
            conn,
            """
            SELECT path, COUNT(*) AS pageviews, COUNT(DISTINCT day || ':' || visitor_hash) AS visitors
            FROM pageviews
            WHERE ts >= ?
            GROUP BY path
            ORDER BY pageviews DESC, path ASC
            LIMIT 12
            """,
            (cutoff_7d,),
        )
        referrers = grouped_rows(
            conn,
            """
            SELECT referrer_host, COUNT(*) AS pageviews
            FROM pageviews
            WHERE ts >= ?
            GROUP BY referrer_host
            ORDER BY pageviews DESC, referrer_host ASC
            LIMIT 12
            """,
            (cutoff_7d,),
        )
        devices = grouped_rows(
            conn,
            """
            SELECT device_type, COUNT(*) AS pageviews
            FROM pageviews
            WHERE ts >= ?
            GROUP BY device_type
            ORDER BY pageviews DESC
            """,
            (cutoff_7d,),
        )
        browsers = grouped_rows(
            conn,
            """
            SELECT user_agent_family, COUNT(*) AS pageviews
            FROM pageviews
            WHERE ts >= ?
            GROUP BY user_agent_family
            ORDER BY pageviews DESC
            """,
            (cutoff_7d,),
        )
        recent = grouped_rows(
            conn,
            """
            SELECT ts, path, referrer_host, device_type, user_agent_family, language
            FROM pageviews
            ORDER BY ts DESC
            LIMIT 20
            """,
        )

    return {
        "enabled": analytics_enabled(),
        "privacy_mode": "first-party, no cookies, daily pseudonymous visitor hash, raw IP not stored",
        "retention_days": retention_days(),
        "generated_at": current_time.isoformat(),
        "totals": totals,
        "daily": daily,
        "top_pages": top_pages,
        "referrers": referrers,
        "devices": devices,
        "browsers": browsers,
        "recent": recent,
    }
