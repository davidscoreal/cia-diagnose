"""Runtime configuration for cia-diagnose.

Loaded once at server startup. Values come from env vars with safe defaults.
SQLite for AI Summit (v0.1); PostgreSQL post-Summit.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    # ─── Transport ────────────────────────────────────────────
    transport: str = field(default="stdio")  # stdio | sse | streamable-http
    # Bind loopback by default (the report/export routes are unauthenticated).
    # The proxied VPS deployment opts into 0.0.0.0 via CIA_HTTP_HOST behind nginx.
    http_host: str = field(default="127.0.0.1")
    http_port: int = field(default=3792)

    # ─── Database (SQLite for Summit, PG later) ───────────────
    db_path: str = field(default="")  # resolved at startup

    # ─── LLM (report generation via LiteLLM proxy) ───────────
    litellm_url: str = field(default="http://127.0.0.1:4000")
    litellm_model: str = field(default="")

    # ─── Lead capture (no PII baked into the public package — set via env) ───
    n8n_webhook_url: str = field(default="")
    sheets_pipeline_id: str = field(default="")
    david_email: str = field(default="")
    # ─── Telegram direct notify (added 2026-05-23 — bypass n8n if needed) ───
    telegram_bot_token: str = field(default="")
    telegram_chat_id: str = field(default="")
    telegram_thread_id: str = field(default="")
    # ─── Vault log (always-on local sink for lead intake events) ───
    vault_lead_log: str = field(default="")

    # ─── Rate limiting ────────────────────────────────────────
    rate_limit_free: int = field(default=5)       # audits/IP/day
    rate_limit_registered: int = field(default=50)

    # ─── Report storage ──────────────────────────────────────
    report_storage: str = field(default="")  # resolved at startup

    # ─── Feature flags ───────────────────────────────────────
    founders_tier_active: bool = field(default=True)   # 30-40% off first 5
    founders_tier_discount: float = field(default=0.35)  # 35% default
    founders_tier_max_clients: int = field(default=5)

    # ─── Language ─────────────────────────────────────────────
    default_lang: str = field(default="es")

    # ─── Domain ──────────────────────────────────────────────
    base_url: str = field(default="https://audit.univercityaiconsult.tech")


def load_config() -> Config:
    data_dir = os.environ.get(
        "CIA_DATA_DIR",
        str(Path.home() / ".cia-diagnose"),
    )
    Path(data_dir).mkdir(parents=True, exist_ok=True)

    db_default = str(Path(data_dir) / "sessions.db")
    report_default = str(Path(data_dir) / "reports")
    Path(report_default).mkdir(parents=True, exist_ok=True)

    return Config(
        transport=os.environ.get("CIA_TRANSPORT", "stdio"),
        http_host=os.environ.get("CIA_HTTP_HOST", "127.0.0.1"),
        http_port=int(os.environ.get("CIA_HTTP_PORT", "3792")),
        db_path=os.environ.get("CIA_DB_PATH", db_default),
        litellm_url=os.environ.get("CIA_LITELLM_URL", "http://127.0.0.1:4000"),
        litellm_model=os.environ.get("CIA_LITELLM_MODEL", ""),
        n8n_webhook_url=os.environ.get("CIA_N8N_WEBHOOK", ""),
        telegram_bot_token=os.environ.get("CIA_TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.environ.get("CIA_TELEGRAM_CHAT_ID", ""),
        telegram_thread_id=os.environ.get("CIA_TELEGRAM_THREAD_ID", ""),
        vault_lead_log=os.environ.get("CIA_VAULT_LEAD_LOG", ""),
        sheets_pipeline_id=os.environ.get("CIA_SHEETS_ID", ""),
        david_email=os.environ.get("CIA_DAVID_EMAIL", ""),
        rate_limit_free=int(os.environ.get("CIA_RATE_FREE", "5")),
        rate_limit_registered=int(os.environ.get("CIA_RATE_REGISTERED", "50")),
        report_storage=os.environ.get("CIA_REPORT_STORAGE", report_default),
        founders_tier_active=_bool("CIA_FOUNDERS_TIER", True),
        founders_tier_discount=float(os.environ.get("CIA_FOUNDERS_DISCOUNT", "0.35")),
        founders_tier_max_clients=int(os.environ.get("CIA_FOUNDERS_MAX", "5")),
        default_lang=os.environ.get("CIA_LANG", "es"),
        base_url=os.environ.get("CIA_BASE_URL", "https://audit.univercityaiconsult.tech"),
    )


SERVER_VERSION = "1.1.1"
