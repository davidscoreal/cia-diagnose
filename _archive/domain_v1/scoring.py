"""Revenue Leak Score + Fit Score engine.

The Revenue Leak Score (0-100) estimates how much revenue the company is
leaving on the table due to manual/broken processes. Higher = more leakage.

The Fit Score (0-100) estimates how well CIA's services map to their pain.
Higher = better fit for CIA engagement.

Both scores feed into the audit report and value ladder recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass

from univercity_mcp.domain.icps import ICP, Tier
from univercity_mcp.domain.questions import QuestionOption


@dataclass
class ScoreBreakdown:
    """Detailed scoring result with per-dimension breakdown."""
    revenue_leak_score: float  # 0-100
    fit_score: float           # 0-100

    # Per-dimension scores (0-100 each)
    pain_severity: float = 0.0
    process_leak_count: float = 0.0
    tech_maturity: float = 0.0   # inverted: lower maturity = higher leak
    readiness: float = 0.0
    budget_signal: float = 0.0

    # Metadata
    leak_category: str = ""      # low / medium / high / critical
    fit_category: str = ""       # poor / moderate / strong / ideal
    icp_multiplier: float = 1.0  # Tier 1 gets 1.15x on fit

    def to_dict(self) -> dict:
        return {
            "revenue_leak_score": round(self.revenue_leak_score, 1),
            "fit_score": round(self.fit_score, 1),
            "leak_category": self.leak_category,
            "fit_category": self.fit_category,
            "dimensions": {
                "pain_severity": round(self.pain_severity, 1),
                "process_leak_count": round(self.process_leak_count, 1),
                "tech_maturity": round(self.tech_maturity, 1),
                "readiness": round(self.readiness, 1),
                "budget_signal": round(self.budget_signal, 1),
            },
        }


def _categorize_leak(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _categorize_fit(score: float) -> str:
    if score >= 80:
        return "ideal"
    if score >= 60:
        return "strong"
    if score >= 35:
        return "moderate"
    return "poor"


def calculate_scores(
    icp: ICP,
    answers: dict[str, str | list[str] | int | float],
) -> ScoreBreakdown:
    """Calculate Revenue Leak Score and Fit Score from audit answers.

    Args:
        icp: The detected ICP for this session.
        answers: Dict of question_id → answer_value. Values can be:
            - str for dropdown/textarea/yes_no
            - list[str] for multi_select
            - int/float for slider
    """
    # ─── 1. Pain severity (from multi-select industry question) ───
    pain_answer = answers.get(f"{icp.id}_leak") or answers.get("generic_leak") or []
    if isinstance(pain_answer, str):
        pain_answer = [pain_answer]
    pain_count = len(pain_answer)
    pain_severity = min(100.0, pain_count * 18.0)  # 6 items → 100+, capped

    # ─── 2. Process leak count ────────────────────────────────────
    # Based on number of common leak processes matched
    process_leak_count = min(100.0, pain_count * 16.0)

    # ─── 3. Tech maturity (inverted — lower maturity = more leakage) ─
    tools = answers.get("current_tools", [])
    if isinstance(tools, str):
        tools = [tools]

    maturity_points = 0.0
    tool_weights = {
        "crm": 20.0, "erp": 25.0, "automation": 30.0,
        "ai_tools": 25.0, "project_mgmt": 15.0,
        "spreadsheets": 5.0, "whatsapp": 3.0, "none": 0.0,
    }
    for t in tools:
        maturity_points += tool_weights.get(t, 5.0)

    # Invert: high maturity = LOW leak from tech dimension
    tech_maturity_leak = max(0.0, 100.0 - maturity_points)

    # ─── 4. Readiness (from slider) ──────────────────────────────
    readiness_raw = answers.get("ai_readiness", 5)
    try:
        readiness_val = float(readiness_raw) if not isinstance(readiness_raw, (int, float)) else readiness_raw
    except (ValueError, TypeError):
        readiness_val = 5.0
    readiness_score = readiness_val * 10.0  # 1-10 → 10-100

    # ─── 5. Budget signal ────────────────────────────────────────
    budget = answers.get("budget_comfort", "exploring")
    budget_map = {
        "yes_defined": 95.0,
        "yes_flexible": 80.0,
        "if_roi": 70.0,
        "exploring": 50.0,
        "no_budget": 20.0,
    }
    budget_score = budget_map.get(str(budget), 50.0)

    # ─── Revenue Leak Score (weighted average) ───────────────────
    # Pain and tech maturity are the biggest drivers
    revenue_leak = (
        pain_severity * 0.35
        + process_leak_count * 0.25
        + tech_maturity_leak * 0.25
        + (100.0 - readiness_score) * 0.15  # low readiness = more leakage
    )
    revenue_leak = min(100.0, max(0.0, revenue_leak))

    # ─── Fit Score (weighted average) ────────────────────────────
    # Readiness and budget are the biggest fit drivers
    icp_multiplier = 1.15 if icp.tier == Tier.TIER_1 else 1.0

    fit = (
        pain_severity * 0.25
        + readiness_score * 0.30
        + budget_score * 0.30
        + (100.0 - tech_maturity_leak) * 0.15  # some maturity = good fit
    )
    fit = min(100.0, max(0.0, fit * icp_multiplier))

    return ScoreBreakdown(
        revenue_leak_score=revenue_leak,
        fit_score=fit,
        pain_severity=pain_severity,
        process_leak_count=process_leak_count,
        tech_maturity=tech_maturity_leak,
        readiness=readiness_score,
        budget_signal=budget_score,
        leak_category=_categorize_leak(revenue_leak),
        fit_category=_categorize_fit(fit),
        icp_multiplier=icp_multiplier,
    )


def estimate_monthly_leak(
    revenue_range: str,
    leak_score: float,
) -> tuple[int, int]:
    """Estimate monthly revenue leak in dollars (min, max).

    Uses revenue range midpoint × leak percentage.
    """
    midpoints = {
        "under_50k": 25_000,
        "50k_200k": 125_000,
        "200k_1m": 600_000,
        "1m_5m": 3_000_000,
        "over_5m": 7_500_000,
        "prefer_not": 200_000,  # conservative default
    }
    midpoint = midpoints.get(revenue_range, 200_000)

    # Leak percentage: score/100 scaled to realistic range (2-25%)
    leak_pct_min = (leak_score / 100.0) * 0.02  # conservative: 0-2%
    leak_pct_max = (leak_score / 100.0) * 0.25  # aggressive: 0-25%

    # Clamp to realistic range
    leak_pct_min = max(0.02, leak_pct_min)  # at least 2%
    leak_pct_max = min(0.25, leak_pct_max)  # at most 25%

    return (
        int(midpoint * leak_pct_min),
        int(midpoint * leak_pct_max),
    )
