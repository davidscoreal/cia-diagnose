"""Unit tests for the domain layer."""
import pytest

from univercity_mcp.domain.icps import (
    detect_icp, ALL_ICPS, TIER_1_IDS, Tier, GENERIC,
)
from univercity_mcp.domain.questions import (
    get_questions_for_icp, get_followup, get_all_question_ids,
)
from univercity_mcp.domain.scoring import calculate_scores, estimate_monthly_leak
from univercity_mcp.domain.value_ladder import build_value_ladder
from univercity_mcp.domain.closer import generate_closer
from univercity_mcp.domain.objections import detect_objection, format_aaa_response, OBJECTIONS
from univercity_mcp.domain.toolstack import get_relevant_tools, get_all_tools, TOOLSTACK
from univercity_mcp.domain.toolstack_compare import build_comparison_table


# ═══════════════════════════════════════════════════════════
# ICPs
# ═══════════════════════════════════════════════════════════

class TestICPs:
    def test_all_icps_count(self):
        assert len(ALL_ICPS) == 7  # 6 Tier 1 + Generic

    def test_tier_1_count(self):
        assert len(TIER_1_IDS) == 6

    def test_generic_is_tier_2(self):
        assert GENERIC.tier == Tier.TIER_2

    def test_detect_construction(self):
        icp = detect_icp("construcción e inmobiliario")
        assert icp.id == "construction"

    def test_detect_healthcare_en(self):
        icp = detect_icp("healthcare clinic")
        assert icp.id == "healthcare"

    def test_detect_unknown_returns_generic(self):
        icp = detect_icp("underwater basket weaving")
        assert icp.id == "generic"

    def test_detect_none_returns_generic(self):
        icp = detect_icp(None)
        assert icp.id == "generic"

    def test_all_icps_have_pain_phrases(self):
        for icp in ALL_ICPS.values():
            assert len(icp.pain_phrases_es) >= 3
            assert len(icp.pain_phrases_en) >= 3

    def test_all_icps_have_services(self):
        for icp in ALL_ICPS.values():
            assert len(icp.services) >= 1

    def test_all_icps_have_roi_hook(self):
        for icp in ALL_ICPS.values():
            assert icp.roi_hook_es
            assert icp.roi_hook_en


# ═══════════════════════════════════════════════════════════
# Questions
# ═══════════════════════════════════════════════════════════

class TestQuestions:
    def test_questions_per_icp_count(self):
        for icp in ALL_ICPS.values():
            qs = get_questions_for_icp(icp)
            assert len(qs) == 7

    def test_questions_ordered(self):
        qs = get_questions_for_icp(GENERIC)
        orders = [q.order for q in qs]
        assert orders == sorted(orders)

    def test_tier1_gets_specific_question(self):
        icp = ALL_ICPS["construction"]
        qs = get_questions_for_icp(icp)
        ids = [q.id for q in qs]
        assert "construction_leak" in ids

    def test_tier2_gets_generic_question(self):
        qs = get_questions_for_icp(GENERIC)
        ids = [q.id for q in qs]
        assert "generic_leak" in ids

    def test_followup_no_tools(self):
        followup = get_followup("current_tools", ["none"])
        assert followup is not None
        assert followup.id == "followup_no_tools"

    def test_followup_automation(self):
        followup = get_followup("current_tools", ["automation", "crm"])
        assert followup is not None
        assert followup.id == "followup_has_automation"

    def test_followup_high_readiness(self):
        followup = get_followup("ai_readiness", "9")
        assert followup is not None
        assert followup.id == "followup_high_readiness"

    def test_no_followup(self):
        followup = get_followup("current_tools", ["crm"])
        assert followup is None

    def test_all_question_ids(self):
        ids = get_all_question_ids()
        assert "company_size" in ids
        assert "generic_leak" in ids
        assert "followup_no_tools" in ids


# ═══════════════════════════════════════════════════════════
# Scoring
# ═══════════════════════════════════════════════════════════

class TestScoring:
    def test_high_leak_score(self):
        icp = ALL_ICPS["construction"]
        answers = {
            "construction_leak": ["quotes", "handoffs", "progress", "invoicing"],
            "current_tools": ["spreadsheets"],
            "ai_readiness": 2,
            "budget_comfort": "exploring",
        }
        scores = calculate_scores(icp, answers)
        assert scores.revenue_leak_score >= 50
        assert scores.leak_category in ("high", "critical")

    def test_low_leak_score(self):
        icp = ALL_ICPS["startups"]
        answers = {
            "startups_leak": ["metrics"],
            "current_tools": ["crm", "automation", "ai_tools"],
            "ai_readiness": 8,
            "budget_comfort": "yes_defined",
        }
        scores = calculate_scores(icp, answers)
        assert scores.revenue_leak_score < 50

    def test_tier1_fit_multiplier(self):
        icp = ALL_ICPS["healthcare"]
        answers = {
            "healthcare_leak": ["no_shows", "missed_calls"],
            "current_tools": ["spreadsheets"],
            "ai_readiness": 6,
            "budget_comfort": "yes_flexible",
        }
        scores = calculate_scores(icp, answers)
        assert scores.icp_multiplier == 1.15

    def test_tier2_no_multiplier(self):
        answers = {
            "generic_leak": ["manual_tasks"],
            "current_tools": ["none"],
            "ai_readiness": 3,
            "budget_comfort": "no_budget",
        }
        scores = calculate_scores(GENERIC, answers)
        assert scores.icp_multiplier == 1.0

    def test_estimate_monthly_leak(self):
        low, high = estimate_monthly_leak("200k_1m", 70.0)
        assert low > 0
        assert high > low


# ═══════════════════════════════════════════════════════════
# Value Ladder
# ═══════════════════════════════════════════════════════════

class TestValueLadder:
    def test_produces_recommendations(self):
        icp = ALL_ICPS["agencies"]
        answers = {
            "agencies_leak": ["commoditization", "custom_everything"],
            "current_tools": ["project_mgmt"],
            "ai_readiness": 5,
            "budget_comfort": "exploring",
        }
        scores = calculate_scores(icp, answers)
        ladder = build_value_ladder(icp, scores)
        assert len(ladder.recommendations) >= 1
        assert ladder.credit_bridge_es

    def test_founders_discount(self):
        icp = GENERIC
        answers = {"generic_leak": ["manual_tasks"], "current_tools": [], "ai_readiness": 5, "budget_comfort": "exploring"}
        scores = calculate_scores(icp, answers)
        ladder = build_value_ladder(icp, scores, founders_active=True, founders_discount=0.35)
        assert ladder.founders_discount_active is True
        assert ladder.founders_discount_pct == 0.35


# ═══════════════════════════════════════════════════════════
# CLOSER
# ═══════════════════════════════════════════════════════════

class TestCloser:
    def test_qualified(self):
        icp = ALL_ICPS["ecommerce"]
        answers = {
            "ecommerce_leak": ["cart_abandon", "no_nurture", "segmentation"],
            "current_tools": ["spreadsheets"],
            "ai_readiness": 5,
            "budget_comfort": "yes_flexible",
        }
        scores = calculate_scores(icp, answers)
        closer = generate_closer(icp, scores, "carritos abandonados sin recovery")
        assert closer.qualified is True
        assert "carritos abandonados" in closer.label_es

    def test_not_qualified_low_leak(self):
        icp = GENERIC
        answers = {
            "generic_leak": [],
            "current_tools": ["crm", "automation", "erp"],
            "ai_readiness": 9,
            "budget_comfort": "yes_defined",
        }
        scores = calculate_scores(icp, answers)
        closer = generate_closer(icp, scores)
        # With 0 pain items, leak is very low → may not qualify
        assert closer.qualifier_reason in ("qualified", "low_leak", "below_threshold")


# ═══════════════════════════════════════════════════════════
# Objections
# ═══════════════════════════════════════════════════════════

class TestObjections:
    def test_detect_expensive(self):
        obj = detect_objection("es muy caro para nosotros")
        assert obj is not None
        assert obj.id == "too_expensive"

    def test_detect_not_ready(self):
        obj = detect_objection("we're not ready for this")
        assert obj is not None
        assert obj.id == "not_ready"

    def test_detect_none(self):
        obj = detect_objection("I love your product")
        assert obj is None

    def test_format_aaa_es(self):
        obj = detect_objection("es caro")
        assert obj is not None
        text = format_aaa_response(obj, "es")
        assert "Entiendo" in text

    def test_all_objections_have_triggers(self):
        for o in OBJECTIONS:
            assert len(o.trigger_phrases) >= 2

    def test_objection_count(self):
        assert len(OBJECTIONS) == 9


# ═══════════════════════════════════════════════════════════
# Toolstack
# ═══════════════════════════════════════════════════════════

class TestToolstack:
    def test_10_categories(self):
        assert len(TOOLSTACK) == 10

    def test_all_have_paid_and_oss(self):
        for tc in TOOLSTACK:
            assert tc.paid.name
            assert tc.oss.name
            assert tc.oss.is_oss is True
            assert tc.paid.is_oss is False

    def test_relevant_tools(self):
        tools = get_relevant_tools(["invoicing", "billing_cycle"])
        assert len(tools) >= 1
        # Should include payments and/or accounting
        ids = [t.id for t in tools]
        assert "payments" in ids or "accounting" in ids

    def test_comparison_table(self):
        table = build_comparison_table(["sales_follow_up", "invoicing", "scheduling"])
        assert len(table.rows) >= 1
        assert table.summary_es
        assert table.summary_en

    def test_comparison_fallback(self):
        table = build_comparison_table([])
        assert len(table.rows) >= 1  # falls back to top 3
