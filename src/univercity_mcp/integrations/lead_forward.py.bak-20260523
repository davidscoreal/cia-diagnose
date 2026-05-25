"""Lead forwarding — capture leads to Google Sheets Pipeline Comercial.

Forwards lead data via n8n webhook (if configured) or directly appends
to the Google Sheets pipeline. Also sends notification email to David.

For Summit v0.1, we use a simple webhook approach.
Post-Summit: direct Sheets API + CRM integration.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from univercity_mcp.config import Config
from univercity_mcp.storage.sessions import Session

logger = logging.getLogger("univercity-mcp.leads")


async def forward_lead(
    session: Session,
    cfg: Config,
    action: str = "diagnose",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Forward lead data to the commercial pipeline.

    Args:
        session: The audit session with all data.
        cfg: Server config (webhook URL, sheets ID, email).
        action: The action that triggered this lead capture.
                Options: "diagnose", "book_call", "share_report"
        extra: Additional data for the lead (e.g. preferred_time, target_email).

    Returns:
        dict with "success" bool and optional "error" message.
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
        **(extra or {}),
    }

    # Try n8n webhook first
    if cfg.n8n_webhook_url:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(cfg.n8n_webhook_url, json=lead_data)
                if resp.status_code < 300:
                    logger.info("Lead forwarded via n8n: %s (%s)", session.company_name, action)
                    return {"success": True, "method": "n8n"}
                else:
                    logger.warning("n8n webhook returned %d", resp.status_code)
        except Exception as e:
            logger.warning("n8n webhook failed: %s", e)

    # Fallback: log the lead (always succeeds)
    logger.info(
        "Lead captured (log): company=%s email=%s action=%s score=%.1f",
        session.company_name,
        session.contact_email,
        action,
        session.revenue_leak_score or 0,
    )
    return {"success": True, "method": "log"}


async def notify_david(
    session: Session,
    cfg: Config,
    subject: str = "",
) -> bool:
    """Send notification to David about a high-value lead.

    Triggers for qualified leads (revenue_leak_score >= 60).
    Uses n8n webhook with a different action type.
    """
    if not session.revenue_leak_score or session.revenue_leak_score < 60:
        return False

    if not cfg.n8n_webhook_url:
        logger.info(
            "High-value lead notification (no webhook): %s (leak=%.1f)",
            session.company_name, session.revenue_leak_score,
        )
        return True

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(cfg.n8n_webhook_url, json={
                "action": "notify_david",
                "subject": subject or f"High-value lead: {session.company_name}",
                "company": session.company_name,
                "email": session.contact_email,
                "leak_score": session.revenue_leak_score,
                "icp": session.icp_id,
                "to": cfg.david_email,
            })
            return True
    except Exception as e:
        logger.warning("David notification failed: %s", e)
        return False
