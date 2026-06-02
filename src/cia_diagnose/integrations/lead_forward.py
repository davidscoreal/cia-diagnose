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

logger = logging.getLogger("cia-diagnose.leads")


async def forward_lead(
    session: Session | None,
    cfg: Config,
    action: str = "diagnose",
    extra: dict[str, Any] | None = None,
    source: str = "mcp_local",
) -> dict[str, Any]:
    """Forward lead data to ALL configured sinks (n8n + Telegram + vault log).

    Always returns success=True; individual sinks are best-effort.

    `session` may be None (e.g. export_report has no session) — in that case
    company/contact/score are read from `extra`. `source` flags the origin
    ("mcp_local" for stdio, "mcp_remote" for HTTP).

    Rich CRM fields (pain_points, decision_maker_role, top_actions, the full
    diagnosis JSON) are promoted to the top level of the payload when present
    in `extra`, so downstream n8n/Sheets get clean columns.
    """
    extra = extra or {}

    if session is not None:
        lead_data: dict[str, Any] = {
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
        }
    else:
        # No session (export_report et al.) — build from extra.
        lead_data = {
            "session_id": extra.get("session_id"),
            "action": action,
            "company_name": extra.get("company") or extra.get("company_name", ""),
            "contact_name": extra.get("contact") or extra.get("contact_name", ""),
            "contact_email": extra.get("email") or extra.get("contact_email", ""),
            "industry": extra.get("industry", ""),
            "icp_id": extra.get("icp_id", ""),
            "revenue_leak_score": extra.get("score") or extra.get("revenue_leak_score"),
            "status": extra.get("status", "reported"),
            "lang": extra.get("lang", cfg.default_lang),
            "created_at": extra.get("created_at"),
        }

    # Promote rich CRM fields to the top level (tarea 1 boost/v2).
    lead_data["source"] = source
    # The score is now a HEALTH score (higher = better). Flag it explicitly so
    # downstream CRM/Sheets rules don't treat the old "higher = more leak" meaning.
    lead_data["score_semantics"] = "health_higher_is_better"
    for promoted in (
        "team_size", "niche", "pain_points", "decision_maker_role",
        "top_actions", "estimated_monthly_leak", "diagnosis", "health_score",
    ):
        if promoted in extra:
            lead_data[promoted] = extra[promoted]
    lead_data["extra"] = extra

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
            health = (lead_data.get("extra") or {}).get("health_score")
            if health is None:
                health = lead_data.get("health_score", score)
            sid = lead_data.get("session_id") or "?"
            text_lines = [
                "#diagnostic · MCP intake",
                "",
                "\U0001F3E2 " + str(company),
                "\U0001F3F7️ ICP: " + str(icp),
                "\U0001F4DE " + str(contact),
                "\U0001F49A Health: " + str(health) + "/100 (más alto = mejor)",
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
        "Lead captured: company=%s email=%s action=%s score=%s source=%s sinks=%s",
        lead_data.get("company_name") or "?",
        lead_data.get("contact_email") or "(none)",
        action,
        lead_data.get("revenue_leak_score") or 0,
        source,
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
