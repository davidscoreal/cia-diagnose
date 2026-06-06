"""Tests for boost/v2 additions:
- branding single source of truth
- lead_forward accepts session=None (B2) + source + rich fields (tarea 1)
- HTML report rendering (tarea 4)
- HTTP custom routes /report /export /healthz /brand (tareas 4 & 9)
- business_diagnose output carries the brand signature (tarea 3)
"""
from __future__ import annotations

import dataclasses

import httpx
import pytest

from cia_diagnose import branding
from cia_diagnose.config import load_config
from cia_diagnose.server import build_app
from cia_diagnose.integrations.lead_forward import forward_lead
from cia_diagnose import report_html
from cia_diagnose.domain.diagnosis.service import diagnose, _generate_guidance, _categorize_health


# ─── Health-score semantics (B6 fix: high = good) ────────────────────

def test_health_semantics_direction():
    """More problems → LOWER health score (worse). Inversion is correct."""
    worse = diagnose("Bad", {"industry": "construction",
                             "software_detected": ["excel", "whatsapp"],
                             "pain_points": ["cotizaciones perdidas", "reportes manuales",
                                             "clientes pagan tarde"]})
    d = worse.to_dict()
    assert "health_score" in d and "score_meaning" in d
    assert "revenue_leak_score" in d  # backward-compat alias
    assert d["revenue_leak_score"] == d["health_score"]
    assert "growth_mode" in d and "guidance" in d
    # Heavy problems → low health band
    assert d["leak_category"] in ("critical", "weak")
    # 100% framing is explained
    assert "nuevas ligas" in d["score_meaning"].lower()


def test_categorize_health_bands():
    assert _categorize_health(90) == "thriving"
    assert _categorize_health(20) == "critical"


# ─── Curated tool registry (best of the best, per industry × area) ───

def test_tool_registry_industry_override():
    from cia_diagnose import tools_registry
    assert "operaciones" in tools_registry.list_areas()
    generic = [t["name"] for t in tools_registry.tools_for("operaciones")]
    constr = [t["name"] for t in tools_registry.tools_for("operaciones", "construction")]
    assert "n8n" in generic
    assert "Procore" in constr  # industry override applied
    assert constr != generic
    # provenance present
    assert all("why_best" in t and "tier" in t for t in tools_registry.tools_for("finanzas"))
    assert tools_registry.best_pick("finanzas", "paid")["name"] == "QuickBooks"


def test_guidance_modes():
    ask_es, ask_en = _generate_guidance(0.2, False)
    assert "validation_questions" in ask_es and "validation_questions" in ask_en
    grow_es, _ = _generate_guidance(0.9, True)
    assert "no cierres" in grow_es.lower() or "crecimiento" in grow_es.lower()


@pytest.fixture
def isolated_app(tmp_path):
    """App with an isolated temp DB and an effectively-unlimited rate limit so
    tests never collide with each other or with the real ~/.cia-diagnose DB."""
    cfg = dataclasses.replace(
        load_config(),
        db_path=str(tmp_path / "test.db"),
        rate_limit_free=100000,
    )
    return build_app(cfg)


# ─── Branding ────────────────────────────────────────────────────────

def test_branding_canonical_links():
    assert branding.BOOKING_URL == "https://cal.com/david-cia/diagnostico-ai"
    assert branding.CONTACT_EMAIL == "steban@univercityaiconsult.tech"
    assert branding.WEBSITE.startswith("https://www.univercityaiconsult.tech")
    sig = branding.signature("es")
    assert branding.BOOKING_URL in sig["booking_cta"]
    assert "cal.com/cia-consulting" not in sig["booking_cta"]  # old URL gone


# ─── lead_forward (B2 + tarea 1) ─────────────────────────────────────

async def test_forward_lead_accepts_none_session():
    cfg = load_config()
    # Must NOT raise (previously AttributeError on session.id)
    res = await forward_lead(
        session=None, cfg=cfg, action="export_report", source="mcp_remote",
        extra={"company": "Acme", "email": "x@y.com", "score": 42,
               "top_actions": ["CRM"], "pain_points": ["leads"]},
    )
    assert res["success"] is True


async def test_forward_lead_promotes_rich_fields(monkeypatch):
    """When a vault log is configured, the written payload carries the rich fields."""
    import tempfile, os, json
    cfg = load_config()
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    object.__setattr__(cfg, "vault_lead_log", path)  # frozen dataclass

    class _S:
        id = "sid-1"; company_name = "Acme"; contact_name = ""; contact_email = ""
        industry_hint = "agency"; icp_id = "agency"; revenue_leak_score = 55.0
        lang = "es"; created_at = "2026-06-02T00:00:00Z"
        class status:  # noqa
            value = "scored"

    await forward_lead(
        session=_S(), cfg=cfg, action="diagnose", source="mcp_local",
        extra={"pain_points": ["x"], "decision_maker_role": "CEO",
               "top_actions": ["A", "B"], "diagnosis": {"k": 1}},
    )
    payload = json.loads(open(path).read().splitlines()[-1])
    os.remove(path)
    assert payload["source"] == "mcp_local"
    assert payload["decision_maker_role"] == "CEO"
    assert payload["top_actions"] == ["A", "B"]
    assert payload["pain_points"] == ["x"]
    assert payload["diagnosis"] == {"k": 1}


# ─── HTML report (tarea 4) ───────────────────────────────────────────

def test_render_report_html_minimal():
    report = {
        "company_name": "Demo Co", "health_score": 67.0, "revenue_leak_score": 67.0, "leak_category": "healthy",
        "monthly_leak_estimate": {"min_usd": 1000, "max_usd": 5000},
        "icp": {"id": "construction", "name": "Construcción"},
        "summary": "Resumen", "dimensions": [
            {"dimension": "operaciones", "label": "Operaciones", "score": 70, "weight": .25,
             "weighted_score": 17.5, "finding_count": 2},
        ],
        "top_actions": [{"action": "Implementar CRM", "impact": "x", "priority": 1,
                         "dimension": "tecnologia", "options": {
                             "paid": {"tool": "HubSpot", "price": "$45", "url": "https://h.com"},
                             "oss": {"tool": "Twenty", "url": "https://twenty.com"},
                             "cia": {"service": "Impl", "price": "$5K"}}}],
        "data_quality": {"overall": 0.4}, "session_id": "abc", "version": "1.0.0",
    }
    html = report_html.render_report_html(report, "es")
    assert "<svg" in html  # gauge
    assert branding.BOOKING_URL in html
    assert "www.univercityaiconsult.tech" in html
    assert "Demo Co" in html


# ─── business_diagnose signature (tarea 3) ───────────────────────────

async def test_diagnose_output_has_signature(isolated_app):
    app = isolated_app
    async with app._mcp_server.lifespan(app._mcp_server):
        res = await app.call_tool("business_diagnose", {
            "company_name": "SigCo", "industry": "agency", "lang": "es"})
    data = res[1] if isinstance(res, tuple) else res
    assert "cia" in data
    assert data["cia"]["booking_url"] == branding.BOOKING_URL
    assert data["version"] == "1.2.0"  # B5: single version source


# ─── HTTP routes (tareas 4 & 9) ──────────────────────────────────────

async def test_roi_projector_zero_revenue(isolated_app):
    app = isolated_app
    async with app._mcp_server.lifespan(app._mcp_server):
        res = await app.call_tool("roi_projector", {"monthly_revenue": 0, "revenue_leak_score": 30})
    d = res[1] if isinstance(res, tuple) else res
    assert d.get("need_revenue") is True


async def test_roi_projector_healthy_reframes(isolated_app):
    app = isolated_app
    async with app._mcp_server.lifespan(app._mcp_server):
        res = await app.call_tool("roi_projector", {
            "monthly_revenue": 100000, "revenue_leak_score": 90, "team_size": 5, "lang": "es"})
    d = res[1] if isinstance(res, tuple) else res
    # Healthy business gets growth framing, not catastrophic-leak urgency.
    assert "nuevas ligas" in d["insight_es"].lower()


def test_lang_normalization_pt_falls_to_es():
    # Non-es/en lang must not produce mixed-language / crash.
    d = diagnose("X", {"industry": "construction"}, lang="pt").to_dict()
    # normalized to es → Spanish score_meaning
    assert "área" in d["score_meaning"] or "score" in d["score_meaning"].lower()


def test_bare_number_revenue_not_inflated():
    from cia_diagnose.domain.diagnosis.service import _estimate_monthly_leak
    lo, hi = _estimate_monthly_leak({"revenue_estimate": "50000"}, 50)
    # 50000 must be read as $50k, not $50k * 1e6
    assert hi < 50_000  # monthly leak from a 50k/yr business is tiny, not millions


async def test_export_has_private_headers(isolated_app):
    app = isolated_app
    async with app._mcp_server.lifespan(app._mcp_server):
        res = await app.call_tool("business_diagnose", {
            "company_name": "HdrCo", "industry": "agency", "niche": "B2B SaaS dental", "lang": "es"})
        data = res[1] if isinstance(res, tuple) else res
        sid = data["session_id"]
    http_app = app.streamable_http_app()
    async with http_app.router.lifespan_context(http_app):
        tr = httpx.ASGITransport(app=http_app)
        async with httpx.AsyncClient(transport=tr, base_url="http://t") as c:
            r = await c.get(f"/report/{sid}")
            assert r.headers.get("X-Robots-Tag", "").startswith("noindex")
            assert "no-store" in r.headers.get("Cache-Control", "")


def test_trends_aggregation(tmp_path):
    import json
    import importlib.util
    log = tmp_path / "leads.jsonl"
    rows = [
        {"action": "diagnose", "icp_id": "agency", "niche": "dental saas", "health_score": 40,
         "created_at": "2026-06-01T00:00:00Z", "pain_points": ["leads"],
         "company_name": "SECRET Inc", "contact_email": "x@y.com",
         "diagnosis": {"dimensions": [{"dimension": "finanzas", "score": 30}]}},
        {"action": "diagnose", "icp_id": "agency", "niche": "dental saas", "health_score": 60,
         "created_at": "2026-06-02T00:00:00Z",
         "diagnosis": {"dimensions": [{"dimension": "finanzas", "score": 50}]}},
    ]
    log.write_text("\n".join(json.dumps(r) for r in rows))
    spec = importlib.util.spec_from_file_location(
        "trends", "/Users/testtst/Projects/cia-diagnose/scripts/trends.py")
    trends = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trends)
    agg = trends.aggregate(str(log))
    assert agg["total_diagnoses"] == 2
    assert agg["by_industry"]["agency"] == 2
    assert agg["by_niche"]["dental saas"] == 2
    assert agg["health_by_industry"]["agency"]["mean"] == 50.0
    # PII must NOT leak into aggregates
    blob = json.dumps(agg)
    assert "SECRET" not in blob and "x@y.com" not in blob


async def test_http_routes(isolated_app):
    app = isolated_app
    async with app._mcp_server.lifespan(app._mcp_server):
        res = await app.call_tool("business_diagnose", {
            "company_name": "RouteCo", "industry": "healthcare", "lang": "es"})
        data = res[1] if isinstance(res, tuple) else res
        sid = data["session_id"]

    http_app = app.streamable_http_app()
    async with http_app.router.lifespan_context(http_app):
        tr = httpx.ASGITransport(app=http_app)
        async with httpx.AsyncClient(transport=tr, base_url="http://t") as c:
            assert (await c.get("/healthz")).status_code == 200
            r = await c.get(f"/report/{sid}")
            assert r.status_code == 200 and "<svg" in r.text
            assert (await c.get(f"/export/{sid}?format=json")).status_code == 200
            csv = await c.get(f"/export/{sid}?format=csv")
            assert csv.status_code == 200 and csv.text.startswith("company,")
            assert (await c.get("/brand/favicon-32.png")).status_code == 200
            assert (await c.get("/report/does-not-exist")).status_code == 404
            assert (await c.get("/brand/evil.png")).status_code == 404
