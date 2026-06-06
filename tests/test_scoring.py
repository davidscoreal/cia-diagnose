"""T13 — defensible & responsive scoring.

Ported from 02-tests/scoring_responsiveness_tests.py (handoff 2026-06-05).
The score must be traceable to the prospect's own data, vary with reality, and
fall back to a PRELIMINARY read (never a hard verdict) when data is thin.
"""
from __future__ import annotations

import pytest

from cia_diagnose.domain.diagnosis.service import diagnose

COMMON = {"industry": "agencia de marketing digital", "team_size": 12}

HEALTHY = {**COMMON, "revenue_range": "1m-5m",
    "gross_margin_pct": 32, "ar_days": 28, "cash_runway_months": 9,
    "on_time_on_budget_pct": 90, "reporting": "automated", "documented_processes": "most",
    "founder_dependency": "low", "annual_turnover_pct": 8, "billable_utilization_pct": 70,
    "integration_level": "integrated", "ai_adoption": "systematic",
    "core_systems": ["HubSpot", "Looker", "Asana"],
    "lead_source_concentration": "diversified", "conversion_rate_pct": 30, "cac_ltv_known": True,
    "documented_plan": "clear", "revenue_concentration_pct": 15}

STRUGGLING = {**COMMON, "revenue_range": "200k-1m",
    "gross_margin_pct": 12, "ar_days": 80, "cash_runway_months": 1,
    "on_time_on_budget_pct": 50, "reporting": "manual", "documented_processes": "none",
    "founder_dependency": "high", "annual_turnover_pct": 40, "billable_utilization_pct": 45,
    "integration_level": "siloed", "ai_adoption": "none", "core_systems": ["Excel"],
    "lead_source_concentration": "single", "conversion_rate_pct": 8, "cac_ltv_known": False,
    "documented_plan": "none", "revenue_concentration_pct": 60}

SPARSE = {**COMMON, "revenue_range": "200k-1m"}  # almost no data → preliminary


@pytest.fixture(scope="module")
def healthy():
    return diagnose("Healthy Co", context=HEALTHY, lang="es").to_dict()


@pytest.fixture(scope="module")
def struggling():
    return diagnose("Struggling Co", context=STRUGGLING, lang="es").to_dict()


@pytest.fixture(scope="module")
def sparse():
    return diagnose("Sparse Co", context=SPARSE, lang="es").to_dict()


# A1 / A2 — the score MOVES with reality.
def test_healthy_scores_high(healthy):
    assert healthy["health_score"] >= 65, healthy["health_score"]


def test_struggling_scores_low(struggling):
    assert struggling["health_score"] <= 40, struggling["health_score"]


# A3 — meaningful spread between a healthy and a burning agency.
def test_spread_is_meaningful(healthy, struggling):
    spread = healthy["health_score"] - struggling["health_score"]
    assert spread >= 30, spread


# A4 — the verdict itself differs.
def test_verdict_varies(healthy, struggling):
    assert healthy["leak_category"] != struggling["leak_category"]
    assert healthy["verdict"] != struggling["verdict"]


# A5 — traceability: every SCORED dimension carries a basis.
@pytest.mark.parametrize("fixture", ["healthy", "struggling"])
def test_scored_dimensions_have_basis(fixture, request):
    report = request.getfixturevalue(fixture)
    scored = [d for d in report["dimensions"] if d["status"] == "scored"]
    assert scored, "expected at least one scored dimension"
    for d in scored:
        assert d["basis"], f"dimension {d['dimension']} scored without basis"
        for b in d["basis"]:
            assert "→" in b and "/100" in b  # "metric: value (vs bench) → NN/100"


# A6 — thin data ⇒ preliminary, low confidence, follow-up questions.
def test_sparse_is_preliminary(sparse):
    assert sparse["confidence"] < 0.6, sparse["confidence"]
    assert sparse["data_gaps"], "expected data_gaps with follow-up questions"
    assert sparse["verdict"] == "preliminary"
    for gap in sparse["data_gaps"]:
        assert gap["question_es"] and gap["dimension"]


# Rich data ⇒ high confidence, no preliminary flag.
def test_healthy_is_confident(healthy):
    assert healthy["confidence"] >= 0.6
    assert healthy["verdict"] == healthy["leak_category"]


# C1 — "always" benchmark findings surface as industry_context, labelled, and do
# NOT drag the healthy agency down.
def test_industry_context_is_separated(healthy):
    assert healthy["industry_context"], "benchmark refs should be surfaced"
    for item in healthy["industry_context"]:
        assert item["basis"] == "benchmark"
        assert item["label"]
    # Despite industry benchmarks screaming "margins fell to 18%", a healthy
    # agency that reported 32% margin still scores high.
    assert healthy["health_score"] >= 65


# Backward-compat: the report still carries the v2 keys + the new ones.
def test_report_shape(healthy):
    for key in ("health_score", "revenue_leak_score", "leak_category", "top_actions",
                "validation_questions", "confidence", "verdict", "data_gaps",
                "industry_context"):
        assert key in healthy
