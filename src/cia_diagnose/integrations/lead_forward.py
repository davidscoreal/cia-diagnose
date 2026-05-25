"""Lead forwarding — fan-out to n8n + Telegram + vault log.

Patched 2026-05-23: added Telegram direct sink + vault log sink.
Runs UNCONDITIONALLY on every diagnose (not only when email provided).
"""
from __future__ import annotations

import json as _json
import logging
from pathlib import Path as _Path
from typing import Any

import httpx

from cia_diagnose.config import Config
from cia_diagnose.storage.sessions import Session

logger = logging.getLogger("univercity-mcp.leads")


async def forward_lead(
    session: Session,
    cfg: Config,
    action: str = "diagnose",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Forward lead data to ALL configured sinks (n8n + Telegram + vault log).

    Always returns success=True; individual sinks are best-effort.
    """
    lead_data = {
        "session_id": session.id,
        "action": action,
        "company_name": session.company_name,
        "contact_name": session.contact_name,
        "contact_email": session.contact_email,
        "industry": session.industry_hint,
        "icp_id": session.icp_id,
        "revenue_leak_score": session.revenue_leak_score,
        "status": session.status.value,
        "lang": session.lang,
        "created_at": session.created_at,
        "extra": extra or {},
    }

    methods_succeeded: list[str] = []

    # Sink 1: n8n webhook (if configured)
    if cfg.n8n_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(cfg.n8n_webhook_url, json=lead_data)
                if resp.status_code < 300:
                    logger.info(
                        "Lead forwarded via n8n: %s (%s)",
                        session.company_name, action,
                    )
                    methods_succeeded.append("n8n")
                else:
                    logger.warning(
                        "n8n webhook returned %d: %s",
                        resp.status_code, resp.text[:200],
                    )
        except Exception as e:
            logger.warning("n8n webhook failed: %s", e)

    # Sink 2: Telegram direct (bypasses n8n)
    if cfg.telegram_bot_token and cfg.telegram_chat_id:
        try:
            score = lead_data.get("revenue_leak_score", "?")
            company = lead_data.get("company_name") or "?"
            icp = lead_data.get("icp_id") or "?"
            contact = (
                lead_data.get("contact_email")
                or lead_data.get("contact_name")
                or "(sin contacto)"
            )
            leak_score = (lead_data.get("extra") or {}).get("leak_score", score)
            sid = lead_data.get("session_id") or "?"
            text_lines = [
                "#diagnostic · MCP intake",
                "",
                "\U0001F3E2 " + str(company),
                "\U0001F3F7️ ICP: " + str(icp),
                "\U0001F4DE " + str(contact),
                "\U0001F3AF Score: " + str(leak_score) + "/100",
                "⚡ Action: " + str(action),
                "\U0001F517 session: " + str(sid),
            ]
            text = "\n".join(text_lines)
            payload: dict[str, Any] = {
                "chat_id": cfg.telegram_chat_id,
                "text": text,
                "disable_web_page_preview": True,
            }
            if cfg.telegram_thread_id:
                try:
                    payload["message_thread_id"] = int(cfg.telegram_thread_id)
                except (TypeError, ValueError):
                    pass
            tg_url = (
                "https://api.telegram.org/bot"
                + cfg.telegram_bot_token
                + "/sendMessage"
            )
            async with httpx.AsyncClient(timeout=10.0) as client:
                tresp = await client.post(tg_url, json=payload)
                if tresp.status_code < 300:
                    logger.info("Lead notified via Telegram: %s", company)
                    methods_succeeded.append("telegram")
                else:
                    logger.warning(
                        "Telegram returned %d: %s",
                        tresp.status_code, tresp.text[:200],
                    )
        except Exception as e:
            logger.warning("Telegram forward failed: %s", e)

    # Sink 3: Vault log file (append-only jsonl) — always-on local sink
    if cfg.vault_lead_log:
        try:
            log_path = _Path(cfg.vault_lead_log)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(_json.dumps(lead_data, default=str) + "\n")
            methods_succeeded.append("vault_log")
        except Exception as e:
            logger.warning("Vault log write failed: %s", e)

    logger.info(
        "Lead captured: company=%s email=%s action=%s score=%.1f sinks=%s",
        session.company_name,
        session.contact_email,
        action,
        session.revenue_leak_score or 0,
        ",".join(methods_succeeded) or "none",
    )
    return {"success": True, "methods": methods_succeeded or ["log"]}


async def notify_david(
    session: Session,
    cfg: Config,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Stub kept for backward compatibility — primary path is forward_lead."""
    logger.info(
        "notify_david called for %s (stub)",
        session.company_name,
    )
    return {"success": True}
