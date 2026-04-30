"""univercity-mcp server — 6 tools for the audit flow.

Tools:
  audit.start    — Start a new audit session
  audit.respond  — Submit an answer to the current question
  audit.estimate — Get Revenue Leak Score + recommendations
  audit.report   — Generate the full audit report
  audit.book_call — Book a consultation call
  audit.share    — Share the report via email
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from univercity_mcp.config import Config, load_config, SERVER_VERSION
from univercity_mcp.domain.icps import detect_icp, ALL_ICPS
from univercity_mcp.domain.questions import get_questions_for_icp, get_followup
from univercity_mcp.domain.scoring import calculate_scores, estimate_monthly_leak
from univercity_mcp.domain.value_ladder import build_value_ladder
from univercity_mcp.domain.closer import generate_closer
from univercity_mcp.domain.objections import detect_objection, format_aaa_response
from univercity_mcp.domain.toolstack_compare import build_comparison_table
from univercity_mcp.storage.sessions import SessionStore, SessionStatus

logger = logging.getLogger("univercity-mcp")


def build_app(cfg: Config | None = None) -> FastMCP:
    """Build and return the FastMCP application."""
    if cfg is None:
        cfg = load_config()

    store = SessionStore(cfg.db_path)

    @asynccontextmanager
    async def lifespan(app_instance):
        await store.initialize()
        logger.info("univercity-mcp v%s started (db=%s)", SERVER_VERSION, cfg.db_path)
        try:
            yield {}
        finally:
            await store.close()
            logger.info("univercity-mcp shutdown")

    app = FastMCP(
        "univercity-mcp",
        instructions=(
            "AI-powered business automation audit. "
            "Diagnoses revenue leaks and recommends tools (paid + open source + CIA). "
            "Open to ANY industry. v" + SERVER_VERSION
        ),
        lifespan=lifespan,
    )

    # ═══════════════════════════════════════════════════════════
    # TOOL 1: audit.start
    # ═══════════════════════════════════════════════════════════

    @app.tool()
    async def audit_start(
        company_name: str = "",
        contact_name: str = "",
        contact_email: str = "",
        industry: str = "",
        lang: str = "es",
    ) -> dict[str, Any]:
        """Start a new business automation audit session.

        Args:
            company_name: Name of the company being audited.
            contact_name: Name of the person taking the audit.
            contact_email: Email for sending the report.
            industry: Industry hint for ICP detection (e.g. "construction", "healthcare").
                      Leave empty for generic audit — works for ANY industry.
            lang: Language for the audit ("es" or "en"). Default: "es".

        Returns:
            Session ID, detected ICP info, and the first question to ask.
        """
        # Rate limiting
        ip = "cli"  # In HTTP mode, extract from request
        if not await store.check_rate_limit(ip, cfg.rate_limit_free):
            return {
                "error": "rate_limit_exceeded",
                "message_es": f"Límite de {cfg.rate_limit_free} auditorías/día alcanzado. Regístrate para más.",
                "message_en": f"Limit of {cfg.rate_limit_free} audits/day reached. Register for more.",
            }

        # Detect ICP
        icp = detect_icp(industry)

        # Create session
        session = await store.create_session(
            company_name=company_name,
            contact_name=contact_name,
            contact_email=contact_email,
            industry_hint=industry,
            ip_address=ip,
            lang=lang,
        )
        session.icp_id = icp.id
        session.status = SessionStatus.IN_PROGRESS
        await store.update_session(session)

        # Increment rate limit
        await store.increment_rate_limit(ip)

        # Get first question
        questions = get_questions_for_icp(icp)
        first_q = questions[0]

        return {
            "session_id": session.id,
            "icp": {
                "id": icp.id,
                "name": icp.name if lang == "en" else icp.name_es,
                "tier": icp.tier.value,
            },
            "total_questions": len(questions),
            "current_question": 1,
            "question": _format_question(first_q, lang),
            "message": (
                f"Auditoría iniciada para {company_name or 'tu empresa'}. "
                f"Industria detectada: {icp.name_es}. "
                f"Responde las {len(questions)} preguntas para obtener tu Revenue Leak Score."
                if lang == "es" else
                f"Audit started for {company_name or 'your company'}. "
                f"Detected industry: {icp.name}. "
                f"Answer the {len(questions)} questions to get your Revenue Leak Score."
            ),
        }

    # ═══════════════════════════════════════════════════════════
    # TOOL 2: audit.respond
    # ═══════════════════════════════════════════════════════════

    @app.tool()
    async def audit_respond(
        session_id: str,
        answer: str | list[str] | int | float = "",
    ) -> dict[str, Any]:
        """Submit an answer to the current audit question.

        Args:
            session_id: The session ID from audit.start.
            answer: The answer value. Type depends on question:
                - dropdown: string value
                - multi_select: list of string values
                - slider: integer 1-10
                - textarea: free text string
                - yes_no: "yes" or "no"

        Returns:
            Next question (or scoring results if all questions answered).
        """
        session = await store.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}
        if session.status not in (SessionStatus.IN_PROGRESS, SessionStatus.STARTED):
            return {"error": "session_not_active", "status": session.status.value}

        icp = ALL_ICPS.get(session.icp_id, ALL_ICPS["generic"])
        questions = get_questions_for_icp(icp)

        if session.current_question >= len(questions):
            return {"error": "all_questions_answered", "hint": "Call audit.estimate next"}

        # Record answer
        current_q = questions[session.current_question]
        session.answers[current_q.id] = answer

        # Check for follow-up
        followup = get_followup(current_q.id, answer)
        followup_data = None
        if followup:
            followup_data = _format_question(followup, session.lang)

        # Advance to next question
        session.current_question += 1
        await store.update_session(session)

        # If all questions answered, signal ready for scoring
        if session.current_question >= len(questions):
            return {
                "session_id": session_id,
                "status": "all_answered",
                "answers_count": len(session.answers),
                "followup": followup_data,
                "message": (
                    "Todas las preguntas contestadas. Llama audit.estimate para ver tu Revenue Leak Score."
                    if session.lang == "es" else
                    "All questions answered. Call audit.estimate to see your Revenue Leak Score."
                ),
            }

        # Return next question
        next_q = questions[session.current_question]
        return {
            "session_id": session_id,
            "current_question": session.current_question + 1,
            "total_questions": len(questions),
            "question": _format_question(next_q, session.lang),
            "followup": followup_data,
        }

    # ═══════════════════════════════════════════════════════════
    # TOOL 3: audit.estimate
    # ═══════════════════════════════════════════════════════════

    @app.tool()
    async def audit_estimate(
        session_id: str,
    ) -> dict[str, Any]:
        """Calculate Revenue Leak Score and generate recommendations.

        Call this after all questions have been answered via audit.respond.

        Args:
            session_id: The session ID.

        Returns:
            Revenue Leak Score, Fit Score, value ladder recommendations,
            CLOSER pre-qualification, and Triple Option tool comparison.
        """
        session = await store.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}

        icp = ALL_ICPS.get(session.icp_id, ALL_ICPS["generic"])

        # Calculate scores
        scores = calculate_scores(icp, session.answers)

        # Estimate monthly leak
        revenue_range = str(session.answers.get("revenue_range", "prefer_not"))
        leak_min, leak_max = estimate_monthly_leak(revenue_range, scores.revenue_leak_score)

        # Build value ladder
        ladder = build_value_ladder(
            icp, scores,
            founders_active=cfg.founders_tier_active,
            founders_discount=cfg.founders_tier_discount,
        )

        # Generate CLOSER
        biggest_pain = str(session.answers.get("biggest_pain", ""))
        closer = generate_closer(icp, scores, biggest_pain)

        # Build Triple Option comparison
        leak_processes = list(icp.common_leak_processes)
        # Add processes from pain answers
        pain_key = f"{icp.id}_leak" if icp.id != "generic" else "generic_leak"
        pain_answers = session.answers.get(pain_key, [])
        if isinstance(pain_answers, list):
            leak_processes.extend(pain_answers)
        tool_comparison = build_comparison_table(leak_processes)

        # Persist scores
        session.revenue_leak_score = scores.revenue_leak_score
        session.fit_score = scores.fit_score
        session.score_breakdown = scores.to_dict()
        session.value_ladder = ladder.to_dict()
        session.closer = closer.to_dict()
        session.tool_comparison = tool_comparison.to_dict()
        session.status = SessionStatus.SCORED
        await store.update_session(session)

        lang = session.lang
        return {
            "session_id": session_id,
            "revenue_leak_score": round(scores.revenue_leak_score, 1),
            "leak_category": scores.leak_category,
            "fit_score": round(scores.fit_score, 1),
            "fit_category": scores.fit_category,
            "estimated_monthly_leak": {
                "min": f"${leak_min:,}",
                "max": f"${leak_max:,}",
                "currency": "USD",
            },
            "icp": {
                "id": icp.id,
                "name": icp.name if lang == "en" else icp.name_es,
            },
            "value_ladder": ladder.to_dict(),
            "closer": closer.to_dict(),
            "tool_comparison": tool_comparison.to_dict(),
            "vacation_pitch": (
                icp.vacation_pitch_es if lang == "es" else icp.vacation_pitch_en
            ),
            "credit_bridge": (
                ladder.credit_bridge_es if lang == "es" else ladder.credit_bridge_en
            ),
            "qualified": closer.qualified,
        }

    # ═══════════════════════════════════════════════════════════
    # TOOL 4: audit.report
    # ═══════════════════════════════════════════════════════════

    @app.tool()
    async def audit_report(
        session_id: str,
        format: str = "md",
    ) -> dict[str, Any]:
        """Generate the full audit report.

        Args:
            session_id: The session ID (must have been scored via audit.estimate).
            format: Report format — "md" (markdown) or "pdf". Default: "md".

        Returns:
            The report content (markdown) or path to PDF file.
        """
        session = await store.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}
        if session.status == SessionStatus.STARTED or session.score_breakdown is None:
            return {"error": "not_scored", "hint": "Call audit.estimate first"}

        icp = ALL_ICPS.get(session.icp_id, ALL_ICPS["generic"])
        lang = session.lang

        # Generate markdown report
        from univercity_mcp.reports.renderer import render_report
        report_md = render_report(session, icp, lang)

        if format == "pdf":
            # PDF generation via weasyprint (optional dependency)
            try:
                from univercity_mcp.reports.renderer import render_pdf
                pdf_path = await render_pdf(report_md, session.id, cfg.report_storage)
                session.report_path = pdf_path
                session.status = SessionStatus.REPORTED
                await store.update_session(session)
                return {
                    "session_id": session_id,
                    "format": "pdf",
                    "path": pdf_path,
                    "message": (
                        "Reporte PDF generado." if lang == "es"
                        else "PDF report generated."
                    ),
                }
            except ImportError:
                return {
                    "error": "pdf_unavailable",
                    "message": "weasyprint not installed. Use format='md'.",
                    "report_md": report_md,
                }

        session.status = SessionStatus.REPORTED
        await store.update_session(session)

        return {
            "session_id": session_id,
            "format": "md",
            "report": report_md,
        }

    # ═══════════════════════════════════════════════════════════
    # TOOL 5: audit.book_call
    # ═══════════════════════════════════════════════════════════

    @app.tool()
    async def audit_book_call(
        session_id: str,
        preferred_time: str = "",
    ) -> dict[str, Any]:
        """Book a consultation call with CIA.

        Args:
            session_id: The session ID.
            preferred_time: Preferred time for the call (free text).

        Returns:
            Booking confirmation with calendar link.
        """
        session = await store.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}

        # Forward lead to pipeline
        from univercity_mcp.integrations.lead_forward import forward_lead
        lead_result = await forward_lead(
            session=session,
            cfg=cfg,
            action="book_call",
            extra={"preferred_time": preferred_time},
        )

        session.status = SessionStatus.BOOKED
        await store.update_session(session)

        lang = session.lang
        cal_url = f"{cfg.base_url}/schedule"

        return {
            "session_id": session_id,
            "status": "booked",
            "calendar_url": cal_url,
            "lead_captured": lead_result.get("success", False),
            "message": (
                f"Llamada agendada. Agenda directamente aquí: {cal_url}\n"
                f"David Lopez, CEO de CIA, te contactará personalmente."
                if lang == "es" else
                f"Call scheduled. Book directly here: {cal_url}\n"
                f"David Lopez, CIA CEO, will contact you personally."
            ),
        }

    # ═══════════════════════════════════════════════════════════
    # TOOL 6: audit.share
    # ═══════════════════════════════════════════════════════════

    @app.tool()
    async def audit_share(
        session_id: str,
        email: str = "",
    ) -> dict[str, Any]:
        """Share the audit report via email.

        Args:
            session_id: The session ID.
            email: Email to send the report to. If empty, uses the contact_email
                   from the session.

        Returns:
            Confirmation of sharing.
        """
        session = await store.get_session(session_id)
        if not session:
            return {"error": "session_not_found"}
        if session.score_breakdown is None:
            return {"error": "not_scored", "hint": "Call audit.estimate first"}

        target_email = email or session.contact_email
        if not target_email:
            return {"error": "no_email", "hint": "Provide an email address"}

        # Forward lead + share report
        from univercity_mcp.integrations.lead_forward import forward_lead
        lead_result = await forward_lead(
            session=session,
            cfg=cfg,
            action="share_report",
            extra={"target_email": target_email},
        )

        session.report_shared = True
        session.status = SessionStatus.SHARED
        await store.update_session(session)

        lang = session.lang
        return {
            "session_id": session_id,
            "status": "shared",
            "email": target_email,
            "lead_captured": lead_result.get("success", False),
            "message": (
                f"Reporte enviado a {target_email}. Revisa tu bandeja de entrada."
                if lang == "es" else
                f"Report sent to {target_email}. Check your inbox."
            ),
        }

    return app


# ─── Helpers ─────────────────────────────────────────────

def _format_question(q, lang: str) -> dict[str, Any]:
    """Format a Question for tool response."""
    result: dict[str, Any] = {
        "id": q.id,
        "label": q.label_es if lang == "es" else q.label_en,
        "ui_component": q.ui_component.value,
        "category": q.category,
    }

    if q.options:
        result["options"] = [
            {
                "value": o.value,
                "label": o.label_es if lang == "es" else o.label_en,
            }
            for o in q.options
        ]

    if q.ui_component.value == "slider":
        result["slider"] = {
            "min": q.slider_min,
            "max": q.slider_max,
            "labels": (
                list(q.slider_labels_es) if lang == "es"
                else list(q.slider_labels_en)
            ),
        }

    if q.help_es or q.help_en:
        result["help"] = q.help_es if lang == "es" else q.help_en

    return result


# ─── CLI entry point ─────────────────────────────────────

def main() -> None:
    """CLI entry point for univercity-mcp."""
    parser = argparse.ArgumentParser(description="univercity-mcp server")
    parser.add_argument(
        "--transport", choices=["stdio", "sse", "streamable-http"],
        default=None, help="Transport mode (overrides env)"
    )
    parser.add_argument("--port", type=int, default=None, help="HTTP port")
    parser.add_argument("--host", default=None, help="HTTP host")
    args = parser.parse_args()

    cfg = load_config()
    if args.transport:
        cfg = Config(**{**cfg.__dict__, "transport": args.transport})
    if args.port:
        cfg = Config(**{**cfg.__dict__, "http_port": args.port})
    if args.host:
        cfg = Config(**{**cfg.__dict__, "http_host": args.host})

    app = build_app(cfg)

    logging.basicConfig(level=logging.INFO)
    logger.info(
        "Starting univercity-mcp v%s (%s) on %s:%d",
        SERVER_VERSION, cfg.transport, cfg.http_host, cfg.http_port,
    )

    if cfg.transport == "stdio":
        app.run(transport="stdio")
    else:
        app.run(
            transport=cfg.transport,
            host=cfg.http_host,
            port=cfg.http_port,
        )


if __name__ == "__main__":
    main()
