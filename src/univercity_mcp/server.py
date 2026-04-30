"""univercity-mcp v0.2.0 — 1 tool: diagnose.

The LLM has the eyes (knows the client).
The MCP has the brain (CIA consulting expertise).

One tool. Open schema. 8 dimensions. Triple Option.
Works from Claude, GPT, Gemini, DeepSeek, Qwen, Perplexity, Cursor,
any LLM that speaks MCP.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from univercity_mcp.config import Config, load_config, SERVER_VERSION
from univercity_mcp.domain.diagnosis.service import diagnose
from univercity_mcp.domain.diagnosis.benchmarks import list_available_icps
from univercity_mcp.storage.sessions import SessionStore, SessionStatus

logger = logging.getLogger("univercity-mcp")


def build_app(cfg: Config | None = None) -> FastMCP:
    """Build and return the FastMCP application with single diagnose tool."""
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
        "univercity_mcp",
        instructions=(
            "Expert business diagnosis engine by CIA (Consultoría de Inteligencia Aplicada). "
            "Analyzes any company across 8 dimensions: digital infrastructure, physical "
            "operations, supply chain, talent, financial health, leadership psychology, "
            "market position, and regulatory compliance. Returns Revenue Leak Score with "
            "prioritized actions and triple-option recommendations (paid tool / open source "
            "alternative / CIA professional service). Works for ANY industry. "
            "Send whatever you know about the company — the more context, the better the "
            "diagnosis. v" + SERVER_VERSION
        ),
        lifespan=lifespan,
        host=cfg.http_host,
        port=cfg.http_port,
    )

    # ---- helpers ------------------------------------------------

    def _to_list(val: str) -> list[str]:
        """Parse comma/semicolon-separated string into clean list."""
        if not val:
            return []
        return [item.strip() for item in val.replace(";", ",").split(",") if item.strip()]

    # ---- THE TOOL: univercity_diagnose --------------------------

    @app.tool(
        name="univercity_diagnose",
        annotations={
            "title": "Expert Business Diagnosis",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def univercity_diagnose(
        company_name: str,
        industry: str = "",
        team_size: int = 0,
        location_city: str = "",
        location_country: str = "",
        revenue_estimate: str = "",
        software_detected: str = "",
        pain_points: str = "",
        physical_operations: str = "",
        supply_chain_notes: str = "",
        hiring_challenges: str = "",
        skill_gaps: str = "",
        cash_flow_concerns: str = "",
        ar_aging: str = "",
        decision_maker_role: str = "",
        stress_indicators: str = "",
        growth_stage: str = "",
        additional_context: str = "",
        contact_email: str = "",
        contact_name: str = "",
        lang: str = "es",
    ) -> dict[str, Any]:
        """Expert business diagnosis for any company across 8 dimensions.

        Send what you know — tools they use, team size, revenue, pain points,
        location, industry, leadership situation, cash flow, talent gaps,
        physical operations, anything. Returns Revenue Leak Score + actionable
        recommendations comparing paid software, open source alternatives,
        and professional implementation services.

        Works for ANY industry. The more context you provide, the more
        accurate and specific the diagnosis. Even minimal input (just
        company_name + industry) produces useful results.

        8 dimensions analyzed: digital, operations, supply_chain, talent,
        financial, leadership, market, regulatory.

        Args:
            company_name: Name of the company being diagnosed (required).
            industry: Industry or sector (e.g. 'construction', 'healthcare', 'ecommerce').
                Use univercity_list_industries to see calibrated benchmarks.
            team_size: Number of employees (0 if unknown).
            location_city: City where the company is based.
            location_country: Country where the company is based.
            revenue_estimate: Monthly revenue range (e.g. '50k-200k', '1m-5m', 'over_5m').
            software_detected: Comma-separated tools/software the company uses
                (e.g. 'Excel, WhatsApp, QuickBooks, no CRM').
            pain_points: Comma-separated problems described by the company
                (e.g. 'quotes get lost, manual reporting, slow hiring').
            physical_operations: Notes on physical/operational challenges
                (e.g. 'material waste, rework, production delays').
            supply_chain_notes: Notes on supply chain or vendor issues
                (e.g. 'unreliable suppliers, delivery delays').
            hiring_challenges: Notes on hiring difficulties
                (e.g. "can't find skilled workers, high turnover").
            skill_gaps: Notes on skill gaps in the team
                (e.g. 'no data analyst, no digital marketing').
            cash_flow_concerns: Notes on cash flow or payment issues
                (e.g. 'clients pay late, 60+ day invoices').
            ar_aging: Accounts receivable aging notes
                (e.g. '30%% of invoices over 90 days').
            decision_maker_role: Role of the person requesting the diagnosis
                (e.g. 'CEO', 'COO', 'VP Operations').
            stress_indicators: Signs of leadership stress or burnout
                (e.g. 'working weekends, micromanaging, decision fatigue').
            growth_stage: Current business stage
                (e.g. 'growing', 'stagnant', 'declining', 'startup', 'scaling').
            additional_context: Any other relevant information as free text or JSON.
            contact_email: Email for follow-up (optional, for lead capture).
            contact_name: Contact name (optional).
            lang: Language for the diagnosis ('es' for Spanish, 'en' for English).

        Returns:
            dict: Complete diagnosis containing:
                - company_name (str): Company analyzed
                - icp_id (str): Detected industry profile
                - revenue_leak_score (float): 0-100 score
                - estimated_monthly_leak (str): Estimated monthly revenue leak
                - dimensions (list): Per-dimension scores and findings
                - actions (list): Prioritized recommendations with triple option
                - validation_questions (list): Questions to refine the diagnosis
                - summary (str): Executive summary
                - leadership_insight (str): Leadership-specific observation

            On rate limit:
                - error (str): 'rate_limit_exceeded'
                - message_es / message_en (str): Localized error message
                - upgrade_url (str): Registration URL
        """
        # ---- Parse string inputs into lists ----
        extra = {}
        if additional_context:
            try:
                extra = json.loads(additional_context)
            except (json.JSONDecodeError, TypeError):
                extra = {"notes": additional_context}

        # ---- Build context object ----
        context: dict[str, Any] = {
            "industry": industry,
            "team_size": team_size,
            "location": {"city": location_city, "country": location_country},
            "revenue_estimate": revenue_estimate,
            "software_detected": _to_list(software_detected),
            "pain_points": _to_list(pain_points),
            "physical_operations": _to_list(physical_operations),
            "supply_chain_notes": supply_chain_notes,
            "hiring_challenges": _to_list(hiring_challenges),
            "skill_gaps": _to_list(skill_gaps),
            "cash_flow_concerns": _to_list(cash_flow_concerns),
            "ar_aging": ar_aging,
            "decision_maker_role": decision_maker_role,
            "stress_indicators": _to_list(stress_indicators),
            "growth_stage": growth_stage,
            **extra,
        }

        # Remove empty values to improve data quality calculation
        context = {k: v for k, v in context.items() if v and v != 0}

        # ---- Rate limiting ----
        ip = "cli"
        if not await store.check_rate_limit(ip, cfg.rate_limit_free):
            return {
                "error": "rate_limit_exceeded",
                "message_es": f"Límite de {cfg.rate_limit_free} diagnósticos/día alcanzado.",
                "message_en": f"Limit of {cfg.rate_limit_free} diagnoses/day reached.",
                "upgrade_url": f"{cfg.base_url}/register",
            }

        # ---- Create session ----
        session = await store.create_session(
            company_name=company_name,
            contact_name=contact_name,
            contact_email=contact_email,
            industry_hint=industry,
            ip_address=ip,
            lang=lang,
        )
        await store.increment_rate_limit(ip)

        # ---- Run diagnosis ----
        report = diagnose(
            company_name=company_name,
            context=context,
            lang=lang,
            session_id=session.id,
        )

        # ---- Persist to session ----
        session.icp_id = report.icp_id
        session.revenue_leak_score = report.revenue_leak_score
        session.status = SessionStatus.SCORED
        session.score_breakdown = report.to_dict()
        await store.update_session(session)

        # ---- Forward lead if email provided ----
        if contact_email:
            try:
                from univercity_mcp.integrations.lead_forward import forward_lead
                await forward_lead(
                    session=session,
                    cfg=cfg,
                    action="diagnose",
                    extra={"leak_score": report.revenue_leak_score},
                )
            except Exception as e:
                logger.warning("Lead forward failed: %s", e)

        return report.to_dict()

    # ---- UTILITY: univercity_list_industries --------------------

    @app.tool(
        name="univercity_list_industries",
        annotations={
            "title": "List Industry Benchmarks",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def univercity_list_industries() -> dict[str, Any]:
        """List available industry benchmarks for UniverCity diagnosis.

        Returns the industries with calibrated benchmarks (Tier 1 = premium,
        deep analysis). Any other industry works too via the generic benchmark.

        Returns:
            dict: Contains:
                - industries (list[str]): Available benchmark IDs
                    (e.g. ['construction', 'healthcare', 'agency', ...])
                - note_es (str): Spanish explanation
                - note_en (str): English explanation
        """
        icps = list_available_icps()
        return {
            "industries": icps,
            "note_es": "Cualquier industria funciona. Las de Tier 1 tienen benchmarks calibrados más profundos.",
            "note_en": "Any industry works. Tier 1 industries have deeper calibrated benchmarks.",
        }

    return app


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="univercity-mcp server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default=None,
    )
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        stream=sys.stderr,
    )

    cfg = load_config()

    if args.transport:
        cfg = Config(
            **{
                **{f.name: getattr(cfg, f.name) for f in cfg.__dataclass_fields__.values()},
                "transport": args.transport,
                **({"http_port": args.port} if args.port else {}),
            }
        )

    app = build_app(cfg)

    if cfg.transport == "stdio":
        app.run(transport="stdio")
    elif cfg.transport == "sse":
        app.run(transport="sse")
    else:
        app.run(transport="streamable-http")


if __name__ == "__main__":
    main()
