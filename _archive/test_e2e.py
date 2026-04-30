"""End-to-end test — full audit flow from start to report."""
import asyncio
import os
import tempfile

import pytest

from univercity_mcp.config import Config
from univercity_mcp.storage.sessions import SessionStore, SessionStatus
from univercity_mcp.domain.icps import detect_icp, ALL_ICPS
from univercity_mcp.domain.questions import get_questions_for_icp
from univercity_mcp.domain.scoring import calculate_scores, estimate_monthly_leak
from univercity_mcp.domain.value_ladder import build_value_ladder
from univercity_mcp.domain.closer import generate_closer
from univercity_mcp.domain.toolstack_compare import build_comparison_table
from univercity_mcp.reports.renderer import render_report


@pytest.fixture
def tmp_db():
    with tempfile.TemporaryDirectory(dir="/tmp") as d:
        yield os.path.join(d, "test.db")


@pytest.fixture
def cfg(tmp_db):
    return Config(
        db_path=tmp_db,
        report_storage=os.path.join(os.path.dirname(tmp_db), "reports"),
        n8n_webhook_url="",
        founders_tier_active=True,
        founders_tier_discount=0.35,
        rate_limit_free=3,
    )


class TestFullAuditFlow:
    """Test the complete audit flow at the domain+storage level."""

    @pytest.mark.asyncio
    async def test_construction_flow(self, cfg):
        """Full flow for a construction company — start to report."""
        store = SessionStore(cfg.db_path)
        await store.initialize()

        # 1. Create session + detect ICP
        icp = detect_icp("construcción")
        assert icp.id == "construction"

        session = await store.create_session(
            company_name="Constructora Test",
            contact_name="Juan",
            contact_email="juan@test.com",
            industry_hint="construcción",
            lang="es",
        )
        session.icp_id = icp.id
        session.status = SessionStatus.IN_PROGRESS
        assert session.id

        # 2. Get questions
        questions = get_questions_for_icp(icp)
        assert len(questions) == 7

        # 3. Record answers
        answers = {
            "company_size": "51-200",
            "current_tools": ["crm", "spreadsheets"],
            "revenue_range": "200k_1m",
            "construction_leak": ["quotes", "handoffs", "invoicing"],
            "biggest_pain": "Se nos pierden cotizaciones entre obras",
            "ai_readiness": 7,
            "budget_comfort": "yes_flexible",
        }
        session.answers = answers
        session.current_question = len(questions)

        # 4. Calculate scores
        scores = calculate_scores(icp, answers)
        assert scores.revenue_leak_score > 0
        assert scores.leak_category in ("low", "medium", "high", "critical")
        assert scores.fit_score > 0
        assert scores.icp_multiplier == 1.15  # Tier 1

        leak_min, leak_max = estimate_monthly_leak("200k_1m", scores.revenue_leak_score)
        assert leak_max > leak_min > 0

        # 5. Build value ladder
        ladder = build_value_ladder(icp, scores, founders_active=True, founders_discount=0.35)
        assert len(ladder.recommendations) >= 1
        assert ladder.founders_discount_active

        # 6. Generate CLOSER
        closer = generate_closer(icp, scores, "cotizaciones perdidas")
        assert closer.label_es
        assert closer.overview_es

        # 7. Build Triple Option comparison
        table = build_comparison_table(list(icp.common_leak_processes))
        assert len(table.rows) >= 1

        # 8. Persist to session
        session.revenue_leak_score = scores.revenue_leak_score
        session.fit_score = scores.fit_score
        session.score_breakdown = scores.to_dict()
        session.value_ladder = ladder.to_dict()
        session.closer = closer.to_dict()
        session.tool_comparison = table.to_dict()
        session.status = SessionStatus.SCORED
        await store.update_session(session)

        # 9. Verify persistence
        loaded = await store.get_session(session.id)
        assert loaded is not None
        assert loaded.status == SessionStatus.SCORED
        assert loaded.revenue_leak_score == scores.revenue_leak_score
        assert loaded.score_breakdown is not None
        assert loaded.value_ladder is not None

        # 10. Generate report
        report = render_report(loaded, icp, "es")
        assert "Revenue Leak Score" in report
        assert "Constructora Test" in report
        assert "Triple Option" in report
        assert "cotizaciones" in report.lower()

        await store.close()

    @pytest.mark.asyncio
    async def test_generic_flow(self, cfg):
        """Flow for an unknown industry (Tier 2)."""
        store = SessionStore(cfg.db_path)
        await store.initialize()

        icp = detect_icp("manufacturing widgets")
        assert icp.id == "generic"
        assert icp.tier.value == "tier_2"

        session = await store.create_session(
            company_name="Acme Corp",
            industry_hint="manufacturing widgets",
            lang="en",
        )
        session.icp_id = icp.id

        answers = {
            "company_size": "11-50",
            "current_tools": ["spreadsheets", "whatsapp"],
            "revenue_range": "50k_200k",
            "generic_leak": ["manual_tasks", "follow_up", "data_scattered"],
            "biggest_pain": "Everything is done manually",
            "ai_readiness": 4,
            "budget_comfort": "exploring",
        }
        session.answers = answers

        scores = calculate_scores(icp, answers)
        assert scores.icp_multiplier == 1.0  # Tier 2
        assert scores.revenue_leak_score > 0

        ladder = build_value_ladder(icp, scores)
        closer = generate_closer(icp, scores, "Everything is done manually")
        table = build_comparison_table(list(icp.common_leak_processes))

        session.revenue_leak_score = scores.revenue_leak_score
        session.fit_score = scores.fit_score
        session.score_breakdown = scores.to_dict()
        session.value_ladder = ladder.to_dict()
        session.closer = closer.to_dict()
        session.tool_comparison = table.to_dict()
        session.status = SessionStatus.SCORED
        await store.update_session(session)

        report = render_report(session, icp, "en")
        assert "Acme Corp" in report
        assert "Revenue Leak Score" in report

        await store.close()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, cfg):
        """Verify rate limiting works."""
        store = SessionStore(cfg.db_path)
        await store.initialize()

        ip = "test-ip-123"

        # Should be allowed initially
        assert await store.check_rate_limit(ip, cfg.rate_limit_free) is True

        # Increment up to limit
        for i in range(cfg.rate_limit_free):
            await store.increment_rate_limit(ip)

        # Should now be blocked
        assert await store.check_rate_limit(ip, cfg.rate_limit_free) is False

        # Different IP should still be allowed
        assert await store.check_rate_limit("other-ip", cfg.rate_limit_free) is True

        await store.close()

    @pytest.mark.asyncio
    async def test_session_persistence(self, cfg):
        """Verify full session round-trip through SQLite."""
        store = SessionStore(cfg.db_path)
        await store.initialize()

        session = await store.create_session(
            company_name="Persist Co",
            contact_email="test@persist.co",
        )
        sid = session.id

        # Update with data
        session.answers = {"q1": "a1", "q2": ["a", "b"]}
        session.revenue_leak_score = 72.5
        session.fit_score = 65.3
        session.status = SessionStatus.SCORED
        await store.update_session(session)

        # Reload
        loaded = await store.get_session(sid)
        assert loaded is not None
        assert loaded.company_name == "Persist Co"
        assert loaded.answers == {"q1": "a1", "q2": ["a", "b"]}
        assert loaded.revenue_leak_score == 72.5
        assert loaded.status == SessionStatus.SCORED

        await store.close()

    @pytest.mark.asyncio
    async def test_report_both_languages(self, cfg):
        """Verify report renders in both ES and EN."""
        store = SessionStore(cfg.db_path)
        await store.initialize()

        icp = ALL_ICPS["healthcare"]
        session = await store.create_session(company_name="Clinica Test")
        session.icp_id = icp.id
        session.answers = {
            "healthcare_leak": ["no_shows", "missed_calls"],
            "current_tools": ["spreadsheets"],
            "ai_readiness": 5,
            "budget_comfort": "yes_flexible",
            "revenue_range": "200k_1m",
        }

        scores = calculate_scores(icp, session.answers)
        session.revenue_leak_score = scores.revenue_leak_score
        session.fit_score = scores.fit_score
        session.score_breakdown = scores.to_dict()
        session.value_ladder = build_value_ladder(icp, scores).to_dict()
        session.closer = generate_closer(icp, scores).to_dict()
        session.tool_comparison = build_comparison_table(list(icp.common_leak_processes)).to_dict()

        report_es = render_report(session, icp, "es")
        report_en = render_report(session, icp, "en")

        assert "Diagnóstico" in report_es
        assert "Diagnosis" in report_en
        assert "Clinica Test" in report_es
        assert "Clinica Test" in report_en

        await store.close()
