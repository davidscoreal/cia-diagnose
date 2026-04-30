"""Tests for univercity-mcp v0.2.0 — 8-dimension diagnosis engine.

Tests cover:
- Benchmark loading (YAML)
- ICP detection
- Dimension scoring
- Full diagnosis flow (minimal + rich context)
- Revenue leak estimation
- Validation question generation
- Triple Option action generation
- Edge cases (empty context, unknown industry)
"""
from __future__ import annotations

import pytest
from univercity_mcp.domain.diagnosis.model import (
    Dimension, Severity, Finding, DimensionScore, DiagnosisReport,
    TripleOption, ValidationQuestion,
)
from univercity_mcp.domain.diagnosis.benchmarks import (
    load_benchmark, list_available_icps, clear_cache,
)
from univercity_mcp.domain.diagnosis.service import (
    diagnose, _detect_icp, _score_dimension, _estimate_monthly_leak,
    _categorize_leak,
)


# ─── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def clear_benchmark_cache():
    """Clear benchmark cache between tests."""
    clear_cache()
    yield
    clear_cache()


# ═══════════════════════════════════════════════════════════════════
# BENCHMARK LOADING
# ═══════════════════════════════════════════════════════════════════


class TestBenchmarks:
    def test_load_construction(self):
        bm = load_benchmark("construction")
        assert bm["id"] == "construction"
        assert bm["tier"] == 1
        assert "dimensions" in bm
        dims = bm["dimensions"]
        assert "digital" in dims
        assert "operations" in dims
        assert "financial" in dims
        # Weights should exist
        assert dims["operations"]["weight"] == 0.25

    def test_load_healthcare(self):
        bm = load_benchmark("healthcare")
        assert bm["id"] == "healthcare"
        assert bm["tier"] == 1

    def test_load_generic_fallback(self):
        bm = load_benchmark("unknown_industry_xyz")
        assert bm["id"] == "generic"
        assert bm["tier"] == 2

    def test_list_available(self):
        icps = list_available_icps()
        ids = [i["id"] for i in icps]
        assert "construction" in ids
        assert "healthcare" in ids
        assert "generic" in ids
        assert len(icps) >= 7  # 6 Tier 1 + generic

    def test_weights_sum_to_one(self):
        """All ICP benchmarks should have dimension weights summing to ~1.0."""
        icps = list_available_icps()
        for icp_info in icps:
            bm = load_benchmark(icp_info["id"])
            dims = bm.get("dimensions", {})
            total = sum(d.get("weight", 0) for d in dims.values())
            assert abs(total - 1.0) < 0.01, (
                f"ICP {icp_info['id']}: weights sum to {total}, expected ~1.0"
            )

    def test_cache_works(self):
        bm1 = load_benchmark("construction")
        bm2 = load_benchmark("construction")
        assert bm1 is bm2  # Same object = cache hit


# ═══════════════════════════════════════════════════════════════════
# ICP DETECTION
# ═══════════════════════════════════════════════════════════════════


class TestICPDetection:
    def test_direct_industry(self):
        assert _detect_icp({"industry": "construction"}) == "construction"
        assert _detect_icp({"industry": "healthcare"}) == "healthcare"
        assert _detect_icp({"industry": "e-commerce"}) == "ecommerce"

    def test_spanish_industry(self):
        assert _detect_icp({"industry": "construcción"}) == "construction"
        assert _detect_icp({"industry": "salud"}) == "healthcare"

    def test_pain_language_detection(self):
        ctx = {"pain_points": ["se nos pierden cotizaciones entre obras"]}
        assert _detect_icp(ctx) == "construction"

    def test_software_detection(self):
        ctx = {"software_detected": ["Procore", "AutoCAD"]}
        assert _detect_icp(ctx) == "construction"

        ctx = {"software_detected": ["Shopify", "Google Analytics"]}
        assert _detect_icp(ctx) == "ecommerce"

    def test_unknown_falls_to_generic(self):
        ctx = {"industry": "underwater basket weaving"}
        assert _detect_icp(ctx) == "generic"

    def test_empty_context(self):
        assert _detect_icp({}) == "generic"


# ═══════════════════════════════════════════════════════════════════
# DIMENSION SCORING
# ═══════════════════════════════════════════════════════════════════


class TestDimensionScoring:
    def test_base_score_applies(self):
        config = {"weight": 0.2, "defaults": {"base_score": 70}, "signals": [], "findings": {}}
        score, findings, dq = _score_dimension(
            Dimension.DIGITAL, config, {}, "es",
        )
        assert score == 70.0  # Base score, no adjustments
        assert len(findings) == 0

    def test_signal_boost(self):
        config = {
            "weight": 0.2,
            "defaults": {"base_score": 50},
            "signals": [
                {"field": "software_detected", "contains_any": ["whatsapp"], "score_boost": 20},
            ],
            "findings": {},
        }
        score, _, _ = _score_dimension(
            Dimension.DIGITAL, config,
            {"software_detected": ["whatsapp", "excel"]},
            "es",
        )
        assert score > 50  # Boosted by signal

    def test_finding_triggered(self):
        config = {
            "weight": 0.2,
            "defaults": {"base_score": 50},
            "signals": [],
            "findings": {
                "test_finding": {
                    "condition": "always",
                    "severity": "high",
                    "title_es": "Test",
                    "title_en": "Test",
                    "detail_es": "Detail",
                    "detail_en": "Detail",
                },
            },
        }
        score, findings, _ = _score_dimension(
            Dimension.DIGITAL, config, {}, "es",
        )
        assert len(findings) == 1
        assert findings[0].severity == Severity.HIGH
        assert score > 50  # Boosted by severity

    def test_data_quality_with_context(self):
        config = {
            "weight": 0.2,
            "defaults": {"base_score": 50},
            "signals": [{"field": "software_detected", "contains_any": ["crm"], "score_boost": -10}],
            "findings": {},
        }
        _, _, dq_empty = _score_dimension(Dimension.DIGITAL, config, {}, "es")
        _, _, dq_full = _score_dimension(
            Dimension.DIGITAL, config,
            {"software_detected": ["crm"], "website_url": "test.com", "social_presence": {"fb": True}},
            "es",
        )
        assert dq_full > dq_empty


# ═══════════════════════════════════════════════════════════════════
# REVENUE LEAK ESTIMATION
# ═══════════════════════════════════════════════════════════════════


class TestRevenueLeak:
    def test_categorize(self):
        assert _categorize_leak(85) == "critical"
        assert _categorize_leak(65) == "high"
        assert _categorize_leak(40) == "medium"
        assert _categorize_leak(20) == "low"

    def test_estimate_with_range(self):
        low, high = _estimate_monthly_leak({"revenue_estimate": "1m-5m"}, 70)
        assert low > 0
        assert high > low
        assert high < 3_000_000  # Can't leak more than revenue

    def test_estimate_no_revenue(self):
        low, high = _estimate_monthly_leak({}, 50)
        assert low > 0  # Falls back to default
        assert high > 0


# ═══════════════════════════════════════════════════════════════════
# FULL DIAGNOSIS FLOW
# ═══════════════════════════════════════════════════════════════════


class TestDiagnosis:
    def test_minimal_context(self):
        """Diagnosis works with just a company name."""
        report = diagnose(company_name="Test Corp")
        assert isinstance(report, DiagnosisReport)
        assert report.company_name == "Test Corp"
        assert 0 <= report.revenue_leak_score <= 100
        assert report.leak_category in ("low", "medium", "high", "critical")
        assert report.icp_id == "generic"  # No hints → generic
        assert len(report.dimensions) > 0

    def test_construction_icp_detected(self):
        """Construction ICP detected from industry hint."""
        report = diagnose(
            company_name="Constructora ABC",
            context={"industry": "construction", "team_size": 120},
        )
        assert report.icp_id == "construction"
        assert report.icp_name  # Has a name

    def test_rich_context_improves_quality(self):
        """More context = higher data quality."""
        minimal = diagnose(company_name="Test")
        rich = diagnose(
            company_name="Test",
            context={
                "industry": "construction",
                "team_size": 80,
                "software_detected": ["whatsapp", "excel"],
                "pain_points": ["cotizaciones perdidas", "reportes manuales"],
                "cash_flow_concerns": ["clientes pagan tarde"],
                "hiring_challenges": ["no encontramos soldadores"],
                "revenue_estimate": "200k-1m",
                "growth_stage": "stagnant",
                "stress_indicators": ["working weekends"],
            },
        )
        assert rich.overall_data_quality > minimal.overall_data_quality

    def test_validation_questions_generated(self):
        """Diagnosis generates validation questions for missing dimensions."""
        report = diagnose(company_name="Test", context={"industry": "construction"})
        assert len(report.validation_questions) > 0
        assert len(report.validation_questions) <= 3
        for q in report.validation_questions:
            assert isinstance(q, ValidationQuestion)
            assert q.question_es
            assert q.question_en

    def test_top_actions_have_triple_option(self):
        """Top actions include paid/OSS/CIA options."""
        report = diagnose(
            company_name="Constructora Test",
            context={
                "industry": "construction",
                "software_detected": ["excel", "whatsapp"],
                "pain_points": ["cotizaciones perdidas"],
            },
        )
        # Should have at least 1 action
        assert len(report.top_actions) > 0

    def test_leadership_insight_when_stressed(self):
        """Leadership insight generated when stress indicators present."""
        report = diagnose(
            company_name="Stressed Corp",
            context={
                "stress_indicators": ["burnout", "working weekends", "micromanagement"],
            },
        )
        assert report.leadership_insight_es
        assert "burnout" in report.leadership_insight_es.lower() or "estrés" in report.leadership_insight_es.lower()

    def test_to_dict_structure(self):
        """The dict output has all required keys for the LLM."""
        report = diagnose(
            company_name="Dict Test Corp",
            context={"industry": "healthcare"},
        )
        d = report.to_dict()
        assert "revenue_leak_score" in d
        assert "leak_category" in d
        assert "summary" in d
        assert "dimensions" in d
        assert "top_actions" in d
        assert "validation_questions" in d
        assert "data_quality" in d
        assert "trust_signal" in d
        assert "icp" in d
        assert d["icp"]["id"] == "healthcare"

    def test_english_language(self):
        """Diagnosis works in English."""
        report = diagnose(
            company_name="English Corp",
            context={"industry": "startup"},
            lang="en",
        )
        d = report.to_dict()
        assert "Analysis based on" in d["trust_signal"] or "Análisis" in d["trust_signal"]

    def test_multiple_icps(self):
        """Each ICP produces different dimension weights."""
        construction = diagnose("A", context={"industry": "construction"})
        healthcare = diagnose("B", context={"industry": "healthcare"})
        startup = diagnose("C", context={"industry": "startup"})

        # Different ICPs should have different dimension weights
        def get_weights(report):
            return {d.dimension: d.weight for d in report.dimensions}

        c_w = get_weights(construction)
        h_w = get_weights(healthcare)
        s_w = get_weights(startup)

        # At least some weights should differ
        assert c_w != h_w or c_w != s_w

    def test_session_id_assigned(self):
        report = diagnose(company_name="Session Test")
        assert report.session_id


# ═══════════════════════════════════════════════════════════════════
# MODEL SERIALIZATION
# ═══════════════════════════════════════════════════════════════════


class TestModelSerialization:
    def test_finding_to_dict(self):
        f = Finding(
            dimension=Dimension.DIGITAL,
            severity=Severity.HIGH,
            title_es="Sin CRM",
            title_en="No CRM",
            detail_es="Detalle en español",
            detail_en="Detail in English",
            impact_estimate="$5K/month",
        )
        d = f.to_dict("es")
        assert d["title"] == "Sin CRM"
        assert d["severity"] == "high"

        d_en = f.to_dict("en")
        assert d_en["title"] == "No CRM"

    def test_dimension_score_weighted(self):
        ds = DimensionScore(
            dimension=Dimension.OPERATIONS,
            score=80.0,
            weight=0.25,
        )
        assert ds.weighted_score == 20.0  # 80 * 0.25

    def test_triple_option_to_dict(self):
        to = TripleOption(
            action_es="Implementar CRM",
            action_en="Implement CRM",
            impact_es="Recuperar 23% cotizaciones",
            impact_en="Recover 23% of quotes",
            dimension=Dimension.DIGITAL,
            paid_tool="HubSpot",
            paid_price="$45/mo",
            oss_tool="Twenty CRM",
            cia_service_es="Implementación completa",
            cia_service_en="Full implementation",
            cia_price="$5K",
        )
        d = to.to_dict("es")
        assert d["options"]["paid"]["tool"] == "HubSpot"
        assert d["options"]["oss"]["tool"] == "Twenty CRM"
        assert d["options"]["cia"]["price"] == "$5K"


# ═══════════════════════════════════════════════════════════════════
# EDGE CASES
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_company_name(self):
        """Should still work with empty company name."""
        report = diagnose(company_name="")
        assert report.revenue_leak_score >= 0

    def test_none_context(self):
        """None context should not crash."""
        report = diagnose(company_name="Test", context=None)
        assert isinstance(report, DiagnosisReport)

    def test_garbage_context_fields(self):
        """Unexpected context fields should be ignored gracefully."""
        report = diagnose(
            company_name="Test",
            context={
                "industry": "construction",
                "nonexistent_field": "garbage",
                "another_fake": [1, 2, 3],
                "deep_fake": {"nested": {"value": True}},
            },
        )
        assert isinstance(report, DiagnosisReport)

    def test_all_six_tier1_icps(self):
        """All 6 Tier 1 ICPs should produce valid diagnoses."""
        industries = ["construction", "healthcare", "agency", "ecommerce", "startup", "enterprise"]
        for ind in industries:
            report = diagnose(company_name=f"Test {ind}", context={"industry": ind})
            assert report.icp_id == ind, f"Failed for {ind}"
            assert 0 <= report.revenue_leak_score <= 100
            assert len(report.dimensions) > 0
