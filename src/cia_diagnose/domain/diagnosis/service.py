"""Diagnosis service — the core intelligence engine.

Takes whatever context the LLM provides + ICP benchmark → produces
a DiagnosisReport with Revenue Leak Score, per-dimension findings,
Triple Option recommendations, and dynamic validation questions.

This is the BRAIN. The LLM has the EYES.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from .model import (
    Dimension,
    DimensionScore,
    DiagnosisReport,
    Finding,
    Severity,
    TripleOption,
    ValidationQuestion,
)
from .benchmarks import load_benchmark, get_dimension_config

logger = logging.getLogger("cia-diagnose.diagnosis")


def diagnose(
    company_name: str,
    context: dict[str, Any] | None = None,
    lang: str = "es",
    session_id: str = "",
) -> DiagnosisReport:
    """Run holistic diagnosis across 11 dimensions.

    Args:
        company_name: Name of the company.
        context: Whatever the LLM knows — flexible schema.
        lang: "es" or "en".
        session_id: Optional session ID for tracking.

    Returns:
        DiagnosisReport with scores, findings, actions, and validation questions.
    """
    if context is None:
        context = {}

    lang = "en" if lang == "en" else "es"  # only es/en supported

    if not session_id:
        session_id = str(uuid.uuid4())[:12]

    # ── Step 1: Detect ICP ──
    icp_id = _detect_icp(context)
    benchmark = load_benchmark(icp_id)
    icp_name = benchmark.get(f"name_{lang}", benchmark.get("name_en", icp_id))

    # ── Step 2: Score each weighted dimension (T13: defensible, intake-driven) ──
    dimension_scores: list[DimensionScore] = []
    all_findings: list[Finding] = []
    industry_context: list[dict] = []
    data_gaps: list[dict] = []

    for dim in Dimension:
        dim_config = get_dimension_config(benchmark, dim.value)
        weight = dim_config.get("weight", 0.0)

        if weight == 0.0:
            # Skip dimensions with zero weight for this ICP
            continue

        # Legacy pass still runs — it produces the display findings and lets us
        # split "always"/benchmark findings into industry_context (which, per C1,
        # do NOT move the score). legacy_health is only a fallback.
        leak, findings, data_quality = _score_dimension(dim, dim_config, context, lang)
        legacy_health = min(100.0, max(0.0, 100.0 - leak))
        real_findings, ctx_items = _split_findings(dim, dim_config, findings, lang)
        industry_context.extend(ctx_items)

        # Defensible score from the prospect's OWN numbers vs benchmark (C3).
        status, intake_score, basis, coverage = _score_dimension_defensible(dim, context, lang)

        if status == "scored":
            health = intake_score
            data_quality = max(data_quality, coverage)
        elif real_findings:
            # No structured intake, but real (condition-triggered, non-benchmark)
            # findings fired from the prospect's data. Defensible enough to score.
            # NB: we deliberately do NOT trust legacy data_quality here — it is
            # inflated by "always" benchmark findings and would fake confidence.
            status = "scored"
            health = legacy_health
            basis = (
                [(f.title_es if lang == "es" else f.title_en) for f in real_findings]
                or [("datos cualitativos del negocio" if lang == "es" else "qualitative business data")]
            )
        else:
            # Nothing to stand on for this dimension → don't fabricate a verdict.
            health = legacy_health  # shown for context, excluded from the composite
            q = _DATA_GAP_QUESTIONS.get(dim)
            if q:
                data_gaps.append({
                    "dimension": dim.value,
                    "question_es": q["es"],
                    "question_en": q["en"],
                })

        ds = DimensionScore(
            dimension=dim,
            score=health,
            weight=weight,
            findings=findings,
            data_quality=data_quality,
            status=status,
            basis=basis,
        )
        dimension_scores.append(ds)
        all_findings.extend(findings)

    # ── Step 3: Composite Business Health Score over dims WITH data + confidence ──
    total_weight = sum(ds.weight for ds in dimension_scores) or 1.0
    scored_dims = [ds for ds in dimension_scores if ds.status == "scored"]
    covered_weight = sum(ds.weight for ds in scored_dims)
    confidence = covered_weight / total_weight if total_weight else 0.0

    if scored_dims and covered_weight > 0:
        health_score = sum(ds.score * ds.weight for ds in scored_dims) / covered_weight
    else:
        # No dimension had usable data → neutral placeholder, flagged preliminary.
        health_score = 50.0
    health_score = min(100.0, max(0.0, health_score))
    leak_category = _categorize_health(health_score)
    # C4: can't defend a hard sentence on thin data.
    verdict = "preliminary" if confidence < 0.6 else leak_category

    # Growth mode: >50% of dims WITH data are strong (>=70 health).
    strong = sum(1 for ds in scored_dims if ds.score >= 70)
    growth_mode = bool(scored_dims) and strong > len(scored_dims) / 2

    # ── Step 4: Estimate monthly leak (from the inverse of health) ──
    monthly_leak = _estimate_monthly_leak(context, 100.0 - health_score)

    # ── Step 5: Generate Top Actions with Triple Option ──
    top_actions = _generate_actions(all_findings, benchmark, lang)

    # ── Step 6: Generate Validation Questions ──
    dims_with_data = sum(1 for ds in dimension_scores if ds.status == "scored")
    dims_without_data = len(dimension_scores) - dims_with_data
    validation_questions = _generate_validation_questions(
        dimension_scores, context, lang,
    )

    # ── Step 7: Generate Summary ──
    overall_dq = (
        sum(ds.data_quality * ds.weight for ds in dimension_scores) / total_weight
        if total_weight > 0 else 0.0
    )

    summary_es, summary_en = _generate_summary(
        company_name, icp_name, health_score, leak_category,
        monthly_leak, dimension_scores, len(all_findings), overall_dq,
        growth_mode,
    )

    # C4: with thin data we present a PRELIMINARY read, not a hard verdict.
    if verdict == "preliminary":
        n_gaps = len(data_gaps)
        summary_es = (
            f"⚠️ **Lectura preliminar** (confianza {round(confidence * 100)}%): faltan datos "
            f"en {n_gaps} dimensión(es). Respondé las preguntas de seguimiento para un "
            f"diagnóstico defendible.\n\n" + summary_es
        )
        summary_en = (
            f"⚠️ **Preliminary read** (confidence {round(confidence * 100)}%): {n_gaps} "
            f"dimension(s) lack data. Answer the follow-up questions for a defensible "
            f"diagnosis.\n\n" + summary_en
        )

    leadership_es, leadership_en = _generate_leadership_insight(
        context, dimension_scores,
    )

    guidance_es, guidance_en = _generate_guidance(overall_dq, growth_mode)

    return DiagnosisReport(
        company_name=company_name,
        icp_id=icp_id,
        icp_name=icp_name,
        lang=lang,
        health_score=health_score,
        leak_category=leak_category,
        monthly_leak_estimate=monthly_leak,
        dimensions=dimension_scores,
        top_actions=top_actions,
        validation_questions=validation_questions,
        summary_es=summary_es,
        summary_en=summary_en,
        leadership_insight_es=leadership_es,
        leadership_insight_en=leadership_en,
        overall_data_quality=overall_dq,
        dimensions_with_data=dims_with_data,
        dimensions_without_data=dims_without_data,
        growth_mode=growth_mode,
        guidance_es=guidance_es,
        guidance_en=guidance_en,
        confidence=confidence,
        verdict=verdict,
        data_gaps=data_gaps,
        industry_context=industry_context,
        session_id=session_id,
        report_url="",
    )


# ─── ICP Detection ──────────────────────────────────────────────────


def _detect_icp(context: dict[str, Any]) -> str:
    """Detect ICP from context signals. Returns icp_id."""
    industry = str(context.get("industry", "")).lower()
    pain_points = [str(p).lower() for p in context.get("pain_points", [])]
    pain_text = " ".join(pain_points)
    software = [str(s).lower() for s in context.get("software_detected", [])]

    # Direct industry match
    icp_map = {
        "construction": "construction",
        "construcción": "construction",
        "inmobiliario": "construction",
        "healthcare": "healthcare",
        "salud": "healthcare",
        "clínica": "healthcare",
        "clinic": "healthcare",
        "hospital": "healthcare",
        "agency": "agency",
        "agencia": "agency",
        "digital agency": "agency",
        "marketing": "agency",
        "creative": "agency",
        "ecommerce": "ecommerce",
        "e-commerce": "ecommerce",
        "retail": "ecommerce",
        "tienda": "ecommerce",
        "commerce": "ecommerce",
        "startup": "startup",
        "fintech": "startup",
        "saas": "startup",
        "enterprise": "enterprise",
        "corporativo": "enterprise",
        "multinational": "enterprise",
        "restaurant": "restaurant",
        "restaurante": "restaurant",
        "food": "restaurant",
        "comida": "restaurant",
        "gastronomy": "restaurant",
        "gastronomía": "restaurant",
        "real_estate": "real_estate",
        "real estate": "real_estate",
        "inmobiliaria": "real_estate",
        "bienes raíces": "real_estate",
        "property": "real_estate",
    }

    for keyword, icp_id in icp_map.items():
        if keyword in industry:
            return icp_id

    # Pain-language detection
    pain_signals = {
        "construction": ["cotizaciones", "obras", "maestros", "planos", "quotes", "job site"],
        "healthcare": ["citas", "no-show", "pacientes", "appointments", "patients", "billing"],
        "agency": ["márgenes", "chatgpt", "clientes", "margins", "retainer", "scope creep"],
        "ecommerce": ["carrito", "abandono", "conversión", "cart", "checkout", "inventory"],
        "startup": ["runway", "board", "investors", "burn", "series", "fundraising"],
        "enterprise": ["poc", "powerpoint", "big4", "vendor", "innovation", "compliance"],
    }

    best_match = "generic"
    best_score = 0

    for icp_id, signals in pain_signals.items():
        match_count = sum(1 for s in signals if s in pain_text or s in industry)
        if match_count > best_score:
            best_score = match_count
            best_match = icp_id

    # Software detection hints
    software_text = " ".join(software)
    if "procore" in software_text or "plangrid" in software_text:
        return "construction"
    if "epic" in software_text or "cerner" in software_text:
        return "healthcare"
    if "shopify" in software_text or "woocommerce" in software_text:
        return "ecommerce"

    return best_match


# ─── Dimension Scoring ──────────────────────────────────────────────


def _score_dimension(
    dim: Dimension,
    config: dict[str, Any],
    context: dict[str, Any],
    lang: str,
) -> tuple[float, list[Finding], float]:
    """Score a single dimension. Returns (score, findings, data_quality)."""
    defaults = config.get("defaults", {})
    base_score = defaults.get("base_score", 50.0)
    score = base_score
    findings: list[Finding] = []
    data_points_found = 0
    data_points_checked = 0
    
    # ── Apply signals ──
    signals = config.get("signals", [])
    for signal in signals:
        data_points_checked += 1
        field_name = signal.get("field", "")
        field_value = context.get(field_name)
        
        if field_value is None:
            continue
            
        data_points_found += 1
        matched = _evaluate_signal(signal, field_value)
        if matched:
            boost = signal.get("score_boost", 0)
            score += boost
            
    # ── Generate findings from config ──
    finding_configs = config.get("findings", {})
    if isinstance(finding_configs, dict):
        for finding_id, fc in finding_configs.items():
            data_points_checked += 1
            condition = fc.get("condition", "")
            
            triggered = _evaluate_finding_condition(condition, context)
            if triggered:
                data_points_found += 1
                severity = Severity(fc.get("severity", "medium"))
                finding = Finding(
                    dimension=dim,
                    severity=severity,
                    title_es=fc.get("title_es", finding_id),
                    title_en=fc.get("title_en", finding_id),
                    detail_es=fc.get("detail_es", ""),
                    detail_en=fc.get("detail_en", ""),
                    impact_estimate=fc.get("impact", ""),
                    benchmark_ref=finding_id,
                )
                findings.append(finding)
                
                # Apply severity-based score adjustment
                severity_boost = {
                    Severity.CRITICAL: 15,
                    Severity.HIGH: 10,
                    Severity.MEDIUM: 5,
                    Severity.LOW: 2,
                    Severity.INFO: 0,
                }
                score += severity_boost.get(severity, 0)
                
    # ── Context-based scoring adjustments ──
    score = _apply_context_adjustments(dim, score, context)
    
    # Clamp
    score = min(100.0, max(0.0, score))
    
    # Data quality
    data_quality = (data_points_found / max(data_points_checked, 1))
    
    # Boost data quality if we have context fields relevant to this dimension
    relevant_fields = _get_relevant_fields(dim)
    context_coverage = sum(1 for f in relevant_fields if context.get(f) is not None)
    if relevant_fields:
        data_quality = max(data_quality, context_coverage / len(relevant_fields))
        
    return score, findings, data_quality

def _evaluate_signal(signal: dict, field_value: Any) -> bool:
    """Evaluate a single signal against a field value."""
    if "contains_any" in signal:
        targets = signal["contains_any"]
        if isinstance(field_value, list):
            return any(str(t).lower() in [str(v).lower() for v in field_value] for t in targets)
        return any(str(t).lower() in str(field_value).lower() for t in targets)

    if "greater_than" in signal:
        try:
            return float(field_value) > float(signal["greater_than"])
        except (ValueError, TypeError):
            return False

    if "equals_any" in signal:
        targets = signal["equals_any"]
        return str(field_value).lower() in [str(t).lower() for t in targets]

    if "is_not_empty" in signal:
        if isinstance(field_value, (list, dict)):
            return len(field_value) > 0
        return bool(field_value)

    return False


def _evaluate_finding_condition(condition: str, context: dict) -> bool:
    """Evaluate a finding condition string against context."""
    # A missing/blank condition is an unconditional benchmark finding (like
    # "always"): it is created so _split_findings can route it to industry_context,
    # but it does NOT move the score. Avoids warn-spam for condition-less findings.
    if not str(condition).strip() or condition == "always":
        return True

    if " not in " in condition:
        parts = condition.split(" not in ")
        if len(parts) == 2:
            value = parts[0].strip()
            field = parts[1].strip()
            field_data = context.get(field, [])
            if isinstance(field_data, list):
                return value not in [str(v).lower() for v in field_data]
            return value not in str(field_data).lower()

    if " in " in condition:
        parts = condition.split(" in ")
        if len(parts) == 2:
            value = parts[0].strip()
            field = parts[1].strip()
            field_data = context.get(field, [])
            if isinstance(field_data, list):
                return value in [str(v).lower() for v in field_data]
            return value in str(field_data).lower()

    if "is not empty" in condition:
        field = condition.replace("is not empty", "").strip()
        field_data = context.get(field)
        if isinstance(field_data, (list, dict)):
            return len(field_data) > 0
        return bool(field_data)

    # T13/C2: a condition we cannot evaluate must NOT fire. Previously this
    # returned True, so almost every finding triggered → constant ~critical score.
    logger.warning("Unparseable finding condition, not triggering: %r", condition)
    return False


def _apply_context_adjustments(
    dim: Dimension, score: float, context: dict,
) -> float:
    """Apply context-based adjustments that aren't in YAML signals."""
    pain_points = [str(p).lower() for p in context.get("pain_points", [])]
    pain_text = " ".join(pain_points)

    dimension_pain_keywords = {
        Dimension.TECNOLOGIA: ["software", "sistema", "crm", "erp", "digital", "tech", "tool", "integracion", "datos"],
        Dimension.OPERACIONES: ["proceso", "manual", "lento", "waste", "process", "slow", "operaciones"],
        Dimension.PROVEEDORES: ["proveedor", "supply", "vendor", "delivery", "shipping", "cadena"],
        Dimension.EQUIPO: ["contratar", "talento", "hire", "talent", "turnover", "skills", "equipo", "rrhh"],
        Dimension.FINANZAS: ["flujo", "cash", "cobrar", "deuda", "invoice", "payment", "margen", "costos"],
        Dimension.ESTRATEGIA: ["estrategia", "vision", "plan", "escalabilidad", "growth", "scale"],
        Dimension.MARKETING: ["competencia", "competition", "market", "pricing", "customers", "marca"],
        Dimension.CLIENTES: ["clientes", "retencion", "churn", "lifetime", "nps", "satisfaccion"],
        Dimension.COMERCIAL: ["ventas", "leads", "conversion", "pipeline", "ticket", "ciclo"],
        Dimension.LEGAL: ["regulacion", "compliance", "legal", "audit", "regulation", "contratos"],
        Dimension.MARKETING_DIGITAL: ["seo", "google", "redes", "social", "email", "ads", "contenido"],
    }

    keywords = dimension_pain_keywords.get(dim, [])
    pain_matches = sum(1 for kw in keywords if kw in pain_text)
    if pain_matches > 0:
        score += min(20, pain_matches * 7)

    return score


def _get_relevant_fields(dim: Dimension) -> list[str]:
    """Get context fields relevant to a dimension."""
    field_map = {
        Dimension.TECNOLOGIA: ["software_detected", "website_url", "social_presence", "integrations"],
        Dimension.OPERACIONES: ["physical_operations", "team_size", "process_notes"],
        Dimension.PROVEEDORES: ["supply_chain_notes", "vendor_count"],
        Dimension.EQUIPO: ["hiring_challenges", "skill_gaps", "team_size", "rotacion"],
        Dimension.FINANZAS: ["cash_flow_concerns", "ar_aging", "revenue_estimate", "margins"],
        Dimension.ESTRATEGIA: ["stress_indicators", "growth_stage", "decision_maker_role", "vision"],
        Dimension.MARKETING: ["industry", "location", "competitors"],
        Dimension.CLIENTES: ["churn_rate", "retention", "nps", "clientes_perdidos"],
        Dimension.COMERCIAL: ["leads_volume", "conversion_rate", "ticket_promedio", "pipeline"],
        Dimension.LEGAL: ["industry", "location", "contracts"],
        Dimension.MARKETING_DIGITAL: ["seo_score", "social_followers", "email_list", "ads_spend"],
    }
    return field_map.get(dim, [])


# ─── T13: Defensible, intake-driven dimension scoring ───────────────


def _lin_higher(v: float, lo: float, hi: float) -> float:
    """Linear 0-100 where lo→0 and hi→100 (higher input = healthier)."""
    if hi == lo:
        return 50.0
    return max(0.0, min(100.0, (v - lo) / (hi - lo) * 100.0))


def _lin_lower(v: float, good: float, bad: float) -> float:
    """Linear 0-100 where good→100 and bad→0 (lower input = healthier)."""
    if bad == good:
        return 50.0
    return max(0.0, min(100.0, (bad - v) / (bad - good) * 100.0))


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_core_systems(value: Any) -> float | None:
    """Tooling maturity from the systems the prospect actually runs."""
    items = value if isinstance(value, list) else [value]
    text = " ".join(str(i).lower() for i in items if i)
    if not text:
        return None
    categories = {
        "crm": ("hubspot", "salesforce", "pipedrive", "zoho", "close", "copper"),
        "bi": ("looker", "tableau", "power bi", "powerbi", "metabase"),
        "pm": ("asana", "monday", "jira", "clickup", "trello", "notion"),
        "automation": ("zapier", "make.com", "make ", "n8n", "workato"),
    }
    covered = sum(1 for kws in categories.values() if any(k in text for k in kws))
    return max(0.0, min(100.0, 20.0 + 25.0 * covered))


_ENUM_SCORES: dict[str, dict[str, float]] = {
    "reporting": {"manual": 15, "semi": 55, "automated": 95},
    "documented_processes": {"none": 15, "some": 55, "most": 90},
    "founder_dependency": {"low": 90, "med": 50, "medium": 50, "high": 15},
    "integration_level": {"siloed": 15, "partial": 55, "integrated": 92},
    "ai_adoption": {"none": 12, "adhoc": 50, "ad-hoc": 50, "systematic": 92},
    "lead_source_concentration": {"single": 18, "few": 55, "diversified": 90},
    "documented_plan": {"none": 15, "loose": 50, "clear": 90},
}


def _enum_metric(field: str):
    table = _ENUM_SCORES[field]
    return lambda v: table.get(str(v).strip().lower())


def _bool_metric(value: Any) -> float | None:
    if isinstance(value, bool):
        return 85.0 if value else 25.0
    s = str(value).strip().lower()
    if s in ("true", "yes", "si", "sí", "1"):
        return 85.0
    if s in ("false", "no", "0"):
        return 25.0
    return None


# Per-dimension intake metrics (INTAKE-SCHEMA.md). Each: (field, scorer, label_es,
# label_en, bench_note). scorer(value) -> 0..100 health sub-score, or None.
_INTAKE_METRICS: dict[Dimension, list[tuple]] = {
    Dimension.FINANZAS: [
        ("gross_margin_pct", lambda v: _lin_higher(n, 10, 35) if (n := _num(v)) is not None else None,
         "margen bruto", "gross margin", "bench 28%"),
        ("ar_days", lambda v: _lin_lower(n, 30, 90) if (n := _num(v)) is not None else None,
         "días de cobro", "AR days", "bench 45d"),
        ("cash_runway_months", lambda v: _lin_higher(n, 1, 6) if (n := _num(v)) is not None else None,
         "runway de caja", "cash runway", "min 3 meses"),
    ],
    Dimension.OPERACIONES: [
        ("on_time_on_budget_pct", lambda v: _lin_higher(n, 50, 90) if (n := _num(v)) is not None else None,
         "entregas a tiempo/presupuesto", "on-time/on-budget", "bench 85%"),
        ("reporting", _enum_metric("reporting"), "reporting a clientes", "client reporting", "manual→automatizado"),
        ("documented_processes", _enum_metric("documented_processes"),
         "procesos documentados", "documented processes", "none→most"),
    ],
    Dimension.EQUIPO: [
        ("founder_dependency", _enum_metric("founder_dependency"),
         "dependencia del dueño", "founder dependency", "low es mejor"),
        ("annual_turnover_pct", lambda v: _lin_lower(n, 10, 40) if (n := _num(v)) is not None else None,
         "rotación anual", "annual turnover", "bench 15%"),
        ("billable_utilization_pct", lambda v: _lin_higher(n, 45, 75) if (n := _num(v)) is not None else None,
         "utilización facturable", "billable utilization", "min 55%"),
    ],
    Dimension.TECNOLOGIA: [
        ("integration_level", _enum_metric("integration_level"),
         "integración de sistemas", "system integration", "siloed→integrated"),
        ("ai_adoption", _enum_metric("ai_adoption"), "adopción de IA", "AI adoption", "none→systematic"),
        ("core_systems", _score_core_systems, "stack de sistemas", "core systems", "CRM+BI+PM+automation"),
    ],
    Dimension.MARKETING: [
        ("lead_source_concentration", _enum_metric("lead_source_concentration"),
         "concentración de canales", "lead-source concentration", "single→diversified"),
        ("conversion_rate_pct", lambda v: _lin_higher(n, 8, 30) if (n := _num(v)) is not None else None,
         "conversión lead→cliente", "lead→client conversion", "bench por industria"),
        ("cac_ltv_known", _bool_metric, "conoce CAC/LTV", "knows CAC/LTV", "sí es mejor"),
    ],
    Dimension.ESTRATEGIA: [
        ("documented_plan", _enum_metric("documented_plan"),
         "plan a 12 meses", "12-month plan", "none→clear"),
        ("revenue_concentration_pct", lambda v: _lin_lower(n, 15, 50) if (n := _num(v)) is not None else None,
         "concentración de ingresos", "revenue concentration", ">40% es riesgo"),
    ],
}


# Follow-up question per dimension when its intake data is missing (data_gaps).
_DATA_GAP_QUESTIONS: dict[Dimension, dict[str, str]] = {
    Dimension.FINANZAS: {
        "es": "¿Cuál es tu margen bruto promedio por proyecto y a cuántos días cobrás?",
        "en": "What's your average gross margin per project and your AR days?"},
    Dimension.OPERACIONES: {
        "es": "¿Qué % de proyectos entregás a tiempo y en presupuesto? ¿El reporting es manual o automatizado?",
        "en": "What % of projects ship on time/on budget? Is reporting manual or automated?"},
    Dimension.EQUIPO: {
        "es": "Si el dueño desaparece 2 semanas, ¿la operación sigue sola? ¿Cuál es la rotación anual?",
        "en": "If the owner is gone 2 weeks, does the operation run itself? What's your annual turnover?"},
    Dimension.TECNOLOGIA: {
        "es": "¿Tus sistemas están integrados y usás IA de forma sistemática? ¿Qué CRM/herramientas usás?",
        "en": "Are your systems integrated and is AI use systematic? What CRM/tools do you run?"},
    Dimension.MARKETING: {
        "es": "¿De dónde vienen tus clientes — un canal o varios — y conocés tu CAC y LTV?",
        "en": "Where do clients come from — one channel or several — and do you know your CAC and LTV?"},
    Dimension.ESTRATEGIA: {
        "es": "¿Tenés un plan a 12 meses con métricas? ¿Qué % de ingresos viene de tu cliente más grande?",
        "en": "Do you have a 12-month plan with metrics? What % of revenue is your largest client?"},
}


def _fmt_raw(raw: Any, lang: str) -> str:
    if isinstance(raw, bool):
        return ("sí" if raw else "no") if lang == "es" else ("yes" if raw else "no")
    if isinstance(raw, list):
        return ", ".join(str(x) for x in raw)
    return str(raw)


def _score_dimension_defensible(
    dim: Dimension, context: dict, lang: str,
) -> tuple[str, float | None, list[str], float]:
    """Score a dimension from the prospect's own intake vs benchmark (T13/C3).

    Returns (status, score|None, basis, coverage). status is "scored" when at
    least one intake metric was provided, else "insufficient_data".
    """
    metrics = _INTAKE_METRICS.get(dim, [])
    sub_scores: list[float] = []
    basis: list[str] = []
    for field_name, scorer, label_es, label_en, bench in metrics:
        if field_name not in context:
            continue
        raw = context.get(field_name)
        if raw is None or raw == "" or raw == []:
            continue
        s = scorer(raw)
        if s is None:
            continue
        sub_scores.append(s)
        label = label_es if lang == "es" else label_en
        basis.append(f"{label}: {_fmt_raw(raw, lang)} (vs {bench}) → {round(s)}/100")
    if not sub_scores:
        return "insufficient_data", None, [], 0.0
    score = sum(sub_scores) / len(sub_scores)
    coverage = len(sub_scores) / len(metrics) if metrics else 0.0
    return "scored", score, basis, coverage


def _split_findings(
    dim: Dimension, dim_config: dict, findings: list[Finding], lang: str,
) -> tuple[list[Finding], list[dict]]:
    """Split a dimension's findings into data-triggered vs industry benchmark refs.

    T13/C1: findings whose condition is "always" (or unevaluable) are industry
    context — labelled references that do NOT move the score.
    """
    real: list[Finding] = []
    ctx: list[dict] = []
    fconfigs = dim_config.get("findings", {}) or {}
    for f in findings:
        fc = fconfigs.get(f.benchmark_ref, {}) if isinstance(fconfigs, dict) else {}
        cond = str(fc.get("condition", "")).strip().lower()
        if cond in ("", "always"):
            ctx.append({
                "dimension": dim.value,
                "title": f.title_es if lang == "es" else f.title_en,
                "basis": "benchmark",
                "label": ("Benchmark de industria (referencia)" if lang == "es"
                          else "Industry benchmark (reference)"),
            })
        else:
            real.append(f)
    return real, ctx


# ─── Revenue Leak Estimation ────────────────────────────────────────


def _categorize_health(score: float) -> str:
    """Health band (v2: higher = healthier)."""
    if score >= 80:
        return "thriving"
    if score >= 60:
        return "healthy"
    if score >= 35:
        return "weak"
    return "critical"


# Backwards-compatible alias (old name, old leak-direction semantics) kept for
# any external import. Prefer _categorize_health.
def _categorize_leak(score: float) -> str:
    return _categorize_health(100.0 - score)


def _estimate_monthly_leak(context: dict, leak_score: float) -> tuple[int, int]:
    """Estimate MONTHLY revenue leak in USD as proportion of declared ANNUAL revenue.

    Bug fix 2026-05-23: previously (1) only read revenue_estimate but MCP passes
    revenue_range, (2) midpoints dict only covered ≥1M, and (3) applied annual %
    to annual midpoint without dividing by 12 → inflated 'monthly' leak by 12x.

    Hardening 2026-06-05: the fallback parser grabbed only the FIRST number, so
    "0-200k" → $0 (demo-killer), en-dash dropdown values diverged from hyphen
    ones, two-sided ranges took the floor instead of the midpoint, and the 1M
    default rendered an absurd ~$15k/mo leak for pre-revenue leads. Now: unicode
    dashes are normalised, every bound is parsed, ranges use the midpoint,
    open-low bands use the ceiling, pre-revenue anchors to a credible run-rate,
    and the estimate can never collapse to $0. Invariants in tests/test_leak_estimate.py.
    """
    # Accept multiple field names (MCP passes revenue_range; older callers use revenue_estimate)
    raw = str(
        context.get("revenue_range")
        or context.get("revenue_estimate")
        or context.get("annual_revenue")
        or ""
    ).lower()
    # Normalise unicode dashes (en/em/minus) to ASCII hyphen so dropdown values
    # like "USD 200k – 1M" parse identically to "200k-1m" (dash-invariance).
    for _dash in ("–", "—", "−"):
        raw = raw.replace(_dash, "-")
    rev_str = (
        raw.replace(" ", "").replace("_", "").replace(",", "")
        .replace("usd", "").replace("$", "")
    )

    # Annual revenue midpoints (USD). Cover the full ICP \M-\M business range
    # plus pre-ICP and beyond for accurate downsell/upsell estimates.
    midpoints = {
        "under100k":         50_000,
        "100k-500k":        300_000,
        "100k-1m":          550_000,
        "200k-1m":          600_000,
        "500k-1m":          750_000,
        "500k-2m":        1_250_000,
        "1m-5m":          3_000_000,
        "1m-10m":         5_500_000,
        "2m-10m":         6_000_000,
        "5m-10m":         7_500_000,
        "10m-50m":       25_000_000,
        "10m+":          15_000_000,
        "over10m":       15_000_000,
        "over_10m":      15_000_000,
    }
    midpoint = 0
    for key, val in midpoints.items():
        if key in rev_str:
            midpoint = val
            break

    if midpoint == 0:
        # Fallback parser: extract every numeric bound, then decide the annual
        # figure. Handles ranges ("0-200k", "50k-200k"), open-low bands
        # ("menos de 50k"), single amounts ("1.2m", "500000") and pre-revenue.
        import re

        pre_markers = (
            "preingreso", "pre-ingreso", "prerevenue", "pre-revenue",
            "preseed", "pre-seed", "validando", "validacion",
            "siningreso", "noingreso", "ideastage", "idea-stage", "mvp",
        )
        is_pre_revenue = any(mk in rev_str for mk in pre_markers)

        amounts: list[float] = []
        for num_s, unit in re.findall(r"(\d+(?:\.\d+)?)([km]?)", rev_str):
            n = float(num_s)
            if unit == "m":
                n *= 1_000_000
            elif unit == "k":
                n *= 1_000
            elif n < 1_000:
                n *= 1_000_000  # small bare number (e.g. "1.5") = millions
            amounts.append(n)

        positive = [a for a in amounts if a > 0]
        open_low = (
            "menos" in rev_str or "under" in rev_str or "lessthan" in rev_str
            or "hasta" in rev_str or "<" in rev_str
            or rev_str.startswith("0-")
            or (bool(amounts) and min(amounts) == 0)
        )

        if is_pre_revenue or not positive:
            # pre-revenue/unparseable → conservative assumed run-rate. (Was 1M,
            # which rendered an absurd ~$15k/mo leak for a pre-revenue lead.)
            midpoint = 100_000
        elif open_low:
            midpoint = max(positive)                        # "0-200k" → ceiling
        elif len(positive) >= 2:
            midpoint = (min(positive) + max(positive)) / 2  # range → midpoint
        else:
            midpoint = positive[0]                          # single explicit amount

    # A weak score must never read $0 — self-contradiction on the demo (INV1).
    midpoint = max(int(round(midpoint)), 50_000)

    # Annual leak percentage by score (0-100):
    #   0  → 2-5%  annual revenue lost (minimum operational waste)
    #   100 → 25%  annual revenue lost (catastrophic failure)
    pct_min = 0.02 + (leak_score / 100.0) * 0.23
    pct_max = 0.05 + (leak_score / 100.0) * 0.20

    annual_leak_min = midpoint * pct_min
    annual_leak_max = midpoint * pct_max

    # Convert annual → monthly so the field name matches the value
    monthly_min = int(round(annual_leak_min / 12.0))
    monthly_max = int(round(annual_leak_max / 12.0))

    return (monthly_min, monthly_max)


# ─── Action Generation ──────────────────────────────────────────────


def _generate_actions(
    findings: list[Finding],
    benchmark: dict[str, Any],
    lang: str,
) -> list[TripleOption]:
    """Generate top Triple Option actions from findings."""
    # Sort by severity
    severity_order = {
        Severity.CRITICAL: 0, Severity.HIGH: 1,
        Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4,
    }
    sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 5))

    actions: list[TripleOption] = []
    seen_dimensions = set()

    for i, finding in enumerate(sorted_findings[:5]):  # Top 5 actions
        # Get Triple Option from benchmark config
        dim_config = get_dimension_config(benchmark, finding.dimension.value)
        finding_configs = dim_config.get("findings", {})
        fc = finding_configs.get(finding.benchmark_ref, {})
        action_config = fc.get("action", {})

        paid = action_config.get("paid", {})
        oss = action_config.get("oss", {})
        cia = action_config.get("cia", {})

        action = TripleOption(
            action_es=finding.title_es,
            action_en=finding.title_en,
            impact_es=finding.detail_es[:200] if finding.detail_es else "",
            impact_en=finding.detail_en[:200] if finding.detail_en else "",
            dimension=finding.dimension,
            paid_tool=paid.get("tool", ""),
            paid_price=paid.get("price", ""),
            paid_url=paid.get("url", ""),
            oss_tool=oss.get("tool", ""),
            oss_url=oss.get("url", ""),
            cia_service_es=cia.get("service_es", "Implementación y optimización por CIA"),
            cia_service_en=cia.get("service_en", "Implementation and optimization by CIA"),
            cia_price=cia.get("price", "$2K-$10K"),
            priority=i + 1,
        )
        actions.append(action)
        seen_dimensions.add(finding.dimension)

    return actions


# ─── Validation Questions ───────────────────────────────────────────


def _generate_validation_questions(
    dimension_scores: list[DimensionScore],
    context: dict[str, Any],
    lang: str,
) -> list[ValidationQuestion]:
    """Generate 2-3 targeted questions to improve diagnosis quality."""
    questions: list[ValidationQuestion] = []

    # Find dimensions with lowest data quality but high weight
    scored = sorted(
        dimension_scores,
        key=lambda ds: ds.data_quality - ds.weight,  # Low quality + high weight = ask first
    )

    question_templates = {
        Dimension.TECNOLOGIA: ValidationQuestion(
            question_es="¿Qué herramientas digitales usa tu equipo día a día? (CRM, ERP, Excel, WhatsApp, ninguno)",
            question_en="What digital tools does your team use daily? (CRM, ERP, Excel, WhatsApp, none)",
            dimension=Dimension.TECNOLOGIA,
            why_es="Esto nos permite medir tu madurez digital y encontrar los puntos exactos donde se pierden oportunidades.",
            why_en="This lets us measure your digital maturity and find the exact points where opportunities are lost.",
            expected_type="text",
        ),
        Dimension.OPERACIONES: ValidationQuestion(
            question_es="¿Cuáles son los 2-3 procesos más manuales o lentos de tu operación?",
            question_en="What are the 2-3 most manual or slow processes in your operation?",
            dimension=Dimension.OPERACIONES,
            why_es="Los procesos manuales son la fuente #1 de fugas de ingreso. Lean Six Sigma identifica 8 tipos de desperdicio — necesitamos saber cuáles aplican.",
            why_en="Manual processes are the #1 source of revenue leaks. Lean Six Sigma identifies 8 types of waste — we need to know which apply.",
            expected_type="text",
        ),
        Dimension.PROVEEDORES: ValidationQuestion(
            question_es="¿Cómo manejas las compras y proveedores? ¿Tienes sistema centralizado?",
            question_en="How do you manage purchasing and vendors? Do you have a centralized system?",
            dimension=Dimension.PROVEEDORES,
            why_es="48% de líderes de supply chain reportan impacto significativo de AI. Sin visibilidad, las compras duplicadas y precios inflados son invisibles.",
            why_en="48% of supply chain leaders report significant AI impact. Without visibility, duplicate purchases and inflated prices are invisible.",
            expected_type="text",
        ),
        Dimension.EQUIPO: ValidationQuestion(
            question_es="¿Cuántas posiciones tienes abiertas ahora mismo? ¿Cuánto tiempo llevan sin cubrirse?",
            question_en="How many open positions do you have right now? How long have they been unfilled?",
            dimension=Dimension.EQUIPO,
            why_es="El gap de talento le cuesta a la economía global $8.5T en ingresos no realizados. Cada posición vacía es dinero que no se genera.",
            why_en="The talent gap costs the global economy $8.5T in unrealized revenue. Every vacant position is money not being generated.",
            expected_type="text",
        ),
        Dimension.FINANZAS: ValidationQuestion(
            question_es="¿Cuántos días en promedio tardan tus clientes en pagarte? ¿Tienes facturas vencidas 60+ días?",
            question_en="How many days on average do your clients take to pay you? Do you have invoices overdue 60+ days?",
            dimension=Dimension.FINANZAS,
            why_es="61% de facturas B2B se pagan tarde. La probabilidad de cobro cae a ~50% a los 6 meses. Este dato solo puede cambiar completamente tu diagnóstico.",
            why_en="61% of B2B invoices are paid late. Collection probability drops to ~50% at 6 months. This data point alone can completely change your diagnosis.",
            expected_type="text",
        ),
        Dimension.ESTRATEGIA: ValidationQuestion(
            question_es="¿Cómo describirías el nivel de estrés de la alta gerencia en este momento? ¿Trabajan fines de semana?",
            question_en="How would you describe the stress level of senior leadership right now? Do they work weekends?",
            dimension=Dimension.ESTRATEGIA,
            why_es="56% de líderes experimentan burnout. El estrés crónico reduce la capacidad de pensamiento estratégico en 26%. Esto afecta TODAS las demás dimensiones.",
            why_en="56% of leaders experience burnout. Chronic stress reduces strategic thinking capacity by 26%. This affects ALL other dimensions.",
            expected_type="text",
        ),
        Dimension.COMERCIAL: ValidationQuestion(
            question_es="¿Cuántos leads nuevos recibes al mes y cuántos se convierten en clientes?",
            question_en="How many new leads do you receive per month and how many convert to customers?",
            dimension=Dimension.COMERCIAL,
            why_es="La tasa de conversión comercial revela fugas directas de ingreso. Sin este dato, no podemos calcular el costo real de oportunidades perdidas.",
            why_en="Commercial conversion rate reveals direct revenue leaks. Without this data, we cannot calculate the real cost of lost opportunities.",
            expected_type="text",
        ),
        Dimension.MARKETING: ValidationQuestion(
            question_es="¿Cuánto inviertes en marketing al mes y cómo mides el retorno?",
            question_en="How much do you invest in marketing per month and how do you measure the return?",
            dimension=Dimension.MARKETING,
            why_es="Sin medición clara del ROI de marketing, es imposible saber si el presupuesto genera clientes o se desperdicia.",
            why_en="Without clear marketing ROI measurement, it's impossible to know if the budget generates customers or is wasted.",
            expected_type="text",
        ),
        Dimension.CLIENTES: ValidationQuestion(
            question_es="¿Tienes un proceso formal para medir la satisfacción del cliente? ¿Cuál es tu tasa de retención?",
            question_en="Do you have a formal process to measure customer satisfaction? What is your retention rate?",
            dimension=Dimension.CLIENTES,
            why_es="Retener un cliente cuesta 5-7x menos que adquirir uno nuevo. La satisfacción del cliente es el predictor #1 de ingresos recurrentes.",
            why_en="Retaining a customer costs 5-7x less than acquiring a new one. Customer satisfaction is the #1 predictor of recurring revenue.",
            expected_type="text",
        ),
        Dimension.LEGAL: ValidationQuestion(
            question_es="¿Tienes contratos estandarizados con clientes y proveedores? ¿Has tenido disputas legales recientes?",
            question_en="Do you have standardized contracts with clients and vendors? Have you had recent legal disputes?",
            dimension=Dimension.LEGAL,
            why_es="Los riesgos legales no gestionados pueden generar pérdidas inesperadas. Contratos débiles son una fuente invisible de fuga de ingresos.",
            why_en="Unmanaged legal risks can generate unexpected losses. Weak contracts are an invisible source of revenue leakage.",
            expected_type="text",
        ),
        Dimension.MARKETING_DIGITAL: ValidationQuestion(
            question_es="¿Tienes presencia activa en redes sociales y campañas digitales? ¿Mides los resultados?",
            question_en="Do you have an active presence on social media and digital campaigns? Do you measure the results?",
            dimension=Dimension.MARKETING_DIGITAL,
            why_es="El marketing digital sin métricas es gasto, no inversión. Necesitamos saber tu madurez digital para identificar oportunidades de crecimiento.",
            why_en="Digital marketing without metrics is spending, not investing. We need to know your digital maturity to identify growth opportunities.",
            expected_type="text",
        ),
    }

    for ds in scored[:3]:
        if ds.data_quality < 0.5 and ds.dimension in question_templates:
            questions.append(question_templates[ds.dimension])

    # If we have fewer than 2 questions, add generic high-value ones
    if len(questions) < 2:
        if "revenue_estimate" not in context or not context["revenue_estimate"]:
            questions.append(ValidationQuestion(
                question_es="¿Cuál es el rango de ingresos mensuales de la empresa? (Esto nos permite calcular el impacto real de cada fuga)",
                question_en="What is the company's monthly revenue range? (This lets us calculate the real impact of each leak)",
                dimension=Dimension.FINANZAS,
                why_es="Sin este dato, las estimaciones de impacto son genéricas. Con él, podemos decirte exactamente cuánto dinero pierdes.",
                why_en="Without this data, impact estimates are generic. With it, we can tell you exactly how much money you're losing.",
                expected_type="select",
            ))

    return questions[:3]  # Max 3


# ─── Summary Generation ─────────────────────────────────────────────


def _generate_summary(
    company_name: str,
    icp_name: str,
    score: float,
    category: str,
    monthly_leak: tuple[int, int],
    dimensions: list[DimensionScore],
    finding_count: int,
    data_quality: float,
    growth_mode: bool = False,
) -> tuple[str, str]:
    """Generate bilingual summary text (v2: health semantics, high = good)."""
    # Worst (lowest health) = priority areas; best (highest health) = strengths.
    by_health = sorted(dimensions, key=lambda d: d.score)
    worst = by_health[:3]
    best = list(reversed(by_health))[:3]

    worst_es = ", ".join(d.label_es for d in worst)
    worst_en = ", ".join(d.label_en for d in worst)
    best_es = ", ".join(d.label_es for d in best)
    best_en = ", ".join(d.label_en for d in best)

    cat_map_es = {
        "thriving": "EXCELENTE", "healthy": "SANO", "weak": "DÉBIL", "critical": "CRÍTICO",
    }
    cat_map_en = {
        "thriving": "THRIVING", "healthy": "HEALTHY", "weak": "WEAK", "critical": "CRITICAL",
    }

    summary_es = (
        f"**{company_name}** — Salud del negocio: **{cat_map_es.get(category, category)}** "
        f"(Business Health Score: {score:.0f}/100 — más alto es mejor)\n\n"
        f"Se identificaron {finding_count} hallazgos en {len(dimensions)} dimensiones. "
        f"Mayor oportunidad de mejora (menor score): **{worst_es}**. "
        f"Áreas más fuertes: **{best_es}**.\n\n"
    )
    summary_en = (
        f"**{company_name}** — Business health: **{cat_map_en.get(category, category)}** "
        f"(Business Health Score: {score:.0f}/100 — higher is better)\n\n"
        f"Identified {finding_count} findings across {len(dimensions)} dimensions. "
        f"Biggest opportunity (lowest score): **{worst_en}**. "
        f"Strongest areas: **{best_en}**.\n\n"
    )
    if monthly_leak[1] > 0 and not growth_mode:
        summary_es += (
            f"Fuga de ingresos mensual estimada en las áreas débiles: "
            f"**${monthly_leak[0]:,} – ${monthly_leak[1]:,} USD**.\n\n"
        )
        summary_en += (
            f"Estimated monthly revenue leak in the weak areas: "
            f"**${monthly_leak[0]:,} – ${monthly_leak[1]:,} USD**.\n\n"
        )
    if growth_mode:
        summary_es += (
            "🚀 La mayoría de tus áreas están fuertes — estás en **modo crecimiento**. "
            "Aquí el foco no es tapar fugas sino entrar a nuevas ligas: escalar lo que ya "
            "funciona. CIA puede ayudarte a acelerar ese salto.\n\n"
        )
        summary_en += (
            "🚀 Most of your areas are strong — you're in **growth mode**. The focus here "
            "isn't plugging leaks but entering new leagues: scaling what already works. "
            "CIA can help you accelerate that jump.\n\n"
        )
    if data_quality < 0.5:
        summary_es += (
            "⚠️ La calidad de datos es limitada. Responde las preguntas de validación "
            "para afinar significativamente la precisión del diagnóstico."
        )
        summary_en += (
            "⚠️ Data quality is limited. Answer the validation questions to "
            "significantly sharpen the diagnosis accuracy."
        )

    return summary_es, summary_en


def _generate_guidance(data_quality: float, growth_mode: bool) -> tuple[str, str]:
    """Tell the calling LLM what to do next (ask more vs. keep the conversation going)."""
    if data_quality < 0.4:
        return (
            "Tienes poca información del negocio. ANTES de presentar los números como "
            "definitivos, hazle al cliente las validation_questions para llenar las áreas "
            "sin datos; luego vuelve a correr business_diagnose con ese contexto.",
            "You have little information about the business. BEFORE presenting the numbers "
            "as final, ask the client the validation_questions to fill the data gaps, then "
            "re-run business_diagnose with that context.",
        )
    if growth_mode:
        return (
            "El negocio está mayormente sano. No cierres la conversación: muestra las 3 "
            "opciones (open source, paga, CIA) para optimizar y proponle el salto de "
            "crecimiento. Sigue recogiendo datos (más contexto = mejor calificación del lead).",
            "The business is mostly healthy. Do NOT end the conversation: show the 3 options "
            "(open source, paid, CIA) to optimize and propose the growth jump. Keep gathering "
            "data (more context = better lead qualification).",
        )
    return (
        "Presenta el Business Health Score, las áreas de menor score (mayor oportunidad) y "
        "las 3 opciones por acción. Invita a agendar con CIA.",
        "Present the Business Health Score, the lowest-score areas (biggest opportunity) and "
        "the 3 options per action. Invite to book with CIA.",
    )


def _generate_leadership_insight(
    context: dict[str, Any],
    dimensions: list[DimensionScore],
) -> tuple[str, str]:
    """Generate leadership-specific insight (sensitive, separate from main summary)."""
    stress = context.get("stress_indicators", [])
    growth = str(context.get("growth_stage", "")).lower()

    if not stress and growth not in ("stagnant", "declining", "crisis"):
        return "", ""

    insight_es = "**Insight de Liderazgo (confidencial):** "
    insight_en = "**Leadership Insight (confidential):** "

    if stress:
        insight_es += (
            "Se detectaron indicadores de estrés en la alta gerencia. "
            "56% de líderes experimentan burnout, lo que reduce la capacidad "
            "de pensamiento estratégico en 26%. Esto puede estar amplificando "
            "los problemas en otras dimensiones."
        )
        insight_en += (
            "Stress indicators detected in senior leadership. "
            "56% of leaders experience burnout, reducing strategic "
            "thinking capacity by 26%. This may be amplifying "
            "issues in other dimensions."
        )
    elif growth in ("stagnant", "declining", "crisis"):
        insight_es += (
            f"La empresa reporta un estado de '{growth}'. En estas condiciones, "
            "las decisiones de inversión suelen retrasarse, creando un ciclo negativo. "
            "CIA recomienda un workshop de alineamiento estratégico antes de implementación técnica."
        )
        insight_en += (
            f"The company reports a '{growth}' state. In these conditions, "
            "investment decisions tend to be delayed, creating a negative cycle. "
            "CIA recommends a strategic alignment workshop before technical implementation."
        )

    return insight_es, insight_en


# ─── Quick Scan (Free, No LLM) ─────────────────────────────────────────


def quick_scan(
    company_name: str,
    problem_description: str,
    lang: str = "es",
) -> dict[str, Any]:
    """Run a lightweight free quick scan — no LLM, no API needed.

    Uses keyword matching on the problem description to identify
    up to 3 generic pain points from the business context.

    Args:
        company_name: Name of the company
        problem_description: Free text description of the problem
        lang: Language code (es/en)

    Returns:
        dict with scan results — 3 generic problems + CTA
    """
    text = problem_description.lower()

    # ── Keyword → Problem mapping ────────────────────────────────────────
    pain_patterns = [
        {
            "keywords": ["leads", "clientes", "prospectos", "ventas", "no vende", "convierte", "crm", "pipeline", "cerrar"],
            "problem": {
                "es": "Fuga en Comercial y Ventas",
                "en": "Sales & Revenue Leak",
                "detail": "El negocio tiene tráfico o contactos pero no convierte en ventas. Esto suele ser fuga de dinero invisible.",
                "dimension": "comercial",
            },
            "impact_range": ("$500", "$5,000+"),
        },
        {
            "keywords": ["equipo", "personas", "rrhh", "contratar", "rotación", "staff", "personal", "empleado", "contratación"],
            "problem": {
                "es": "Brecha de Equipo y Capacidades",
                "en": "Team Skill Gap",
                "detail": "El equipo actual no tiene las capacidades para escalar lo que el negocio necesita.",
                "dimension": "equipo",
            },
            "impact_range": ("$200", "$2,000+"),
        },
        {
            "keywords": ["software", "herramientas", "sistema", "automatiz", "integr", "crm", "erp", "datos", "digital", "tech"],
            "problem": {
                "es": "Fragmentación de Tecnología",
                "en": "Technology Fragmentation",
                "detail": "El negocio usa múltiples herramientas que no se hablan entre sí, generando trabajo manual y datos aislados.",
                "dimension": "tecnologia",
            },
            "impact_range": ("$300", "$3,000+"),
        },
        {
            "keywords": ["flujo", "caja", "dinero", "factura", "cobro", "pago", "cash", "liquidez", "pagar", "cobrar"],
            "problem": {
                "es": "Fuga de Flujo de Caja",
                "en": "Cash Flow Leak",
                "detail": "El dinero entra pero se escapa por lugares que no se ven. Sin control, el crecimiento se frena.",
                "dimension": "finanzas",
            },
            "impact_range": ("$500", "$5,000+"),
        },
        {
            "keywords": ["marketing", "contenido", "redes", "social", "instagram", "facebook", "posicionamiento", "seo", "publicidad", "ads"],
            "problem": {
                "es": "Marketing sin Sistema",
                "en": "Unsystematic Marketing",
                "detail": "El negocio publica sin estrategia y sin medir resultados. Gasto en marketing sin retorno claro.",
                "dimension": "marketing",
            },
            "impact_range": ("$200", "$2,000+"),
        },
        {
            "keywords": ["operaciones", "proceso", "eficiencia", "lento", "cuello", "botella", "operar", "escalabilidad", "automatizar"],
            "problem": {
                "es": "Operaciones sin Escala",
                "en": "Unscalable Operations",
                "detail": "Los procesos dependen de personas específicas o de trabajo manual, imposibles de escalar.",
                "dimension": "operaciones",
            },
            "impact_range": ("$300", "$3,000+"),
        },
        {
            "keywords": ["clientes", "abandono", "churn", "retener", "lealtad", "regresa", "fideliz", "cliente perdido"],
            "problem": {
                "es": "Alta Fuga de Clientes",
                "en": "High Customer Churn",
                "detail": "Los clientes llegan pero no regresan. Cada cliente perdido es dinero que se fue para siempre.",
                "dimension": "clientes",
            },
            "impact_range": ("$500", "$5,000+"),
        },
        {
            "keywords": ["proveedor", "vendor", "dependencia", "entrega", "inventario", "cadena", "supply", "compras"],
            "problem": {
                "es": "Dependencia de Proveedores",
                "en": "Vendor Dependence",
                "detail": "El negocio depende de uno o pocos proveedores, creando riesgo de operación si fallan.",
                "dimension": "proveedores",
            },
            "impact_range": ("$200", "$2,000+"),
        },
        {
            "keywords": ["legal", "contrato", "abogado", "jurídico", "demanda", "riesgo legal", "compliance", "regulación"],
            "problem": {
                "es": "Riesgo Legal y Cumplimiento",
                "en": "Legal & Compliance Risk",
                "detail": "El negocio opera sin protocolos legales claros, exponiéndose a riesgos evitables.",
                "dimension": "legal",
            },
            "impact_range": ("$500", "$10,000+"),
        },
        {
            "keywords": ["estrategia", "visión", "plan", "crecimiento", "escala", "dirección", "competitivo", "diferenciación"],
            "problem": {
                "es": "Sin Estrategia Clara de Crecimiento",
                "en": "No Clear Growth Strategy",
                "detail": "El negocio opera día a día sin visión clara de hacia dónde va. Las decisiones no son consistentes.",
                "dimension": "estrategia",
            },
            "impact_range": ("$1,000", "$10,000+"),
        },
        {
            "keywords": ["web", "google", "seo", "sem", "página", "presencia online", "digital presence", "buscador"],
            "problem": {
                "es": "Presencia Digital Débil",
                "en": "Weak Digital Presence",
                "detail": "El negocio no aparece donde los clientes potenciales buscan. Perdés oportunidades diarias.",
                "dimension": "marketing_digital",
            },
            "impact_range": ("$200", "$2,000+"),
        },
    ]

    # ── Match keywords against description ──────────────────────────────
    matched_problems = []
    for pattern in pain_patterns:
        score = sum(1 for kw in pattern["keywords"] if kw in text)
        if score > 0:
            matched_problems.append((score, pattern))

    # Sort by number of matched keywords
    matched_problems.sort(key=lambda x: x[0], reverse=True)
    top_problems = [p[1] for p in matched_problems[:3]]

    # If fewer than 3 matched, fill with generic top problems
    if len(top_problems) < 3:
        generic_problems = [
            p for p in pain_patterns
            if p not in top_problems
        ]
        for gp in generic_problems[:3 - len(top_problems)]:
            top_problems.append(gp)

    # ── Build problems list ─────────────────────────────────────────────
    problems = []
    for i, p in enumerate(top_problems, 1):
        problems.append({
            "number": i,
            "title": p["problem"]["es"],
            "title_en": p["problem"]["en"],
            "dimension": p["problem"]["dimension"],
            "detail": p["problem"]["detail"],
            "impact_range": p["impact_range"],
            "confidence": min(90, 50 + (i == 1 and 30) + (i == 2 and 15)),
        })

    # ── CTA ────────────────────────────────────────────────────────────
    if lang == "es":
        cta_text = "¿Quieres saber cuánto dinero estás perdiendo exactamente? Agenda un Deep Scan de 11 dimensiones sin costo. El costo del diagnóstico se descuenta de tu primera implementación."
        cta_button = "Agenda tu Deep Scan"
        note = "Este análisis cubre las 11 dimensiones de un negocio. El Deep Scan cubre cada una con datos específicos y un plan de acción priorizado."
    else:
        cta_text = "Want to know exactly how much money you're losing? Schedule a free 11-dimension Deep Scan. The cost of the diagnosis is deducted from your first implementation."
        cta_button = "Schedule Deep Scan"
        note = "This analysis covers 11 business dimensions. The Deep Scan covers each one with specific data and a prioritized action plan."

    return {
        "company_name": company_name,
        "scan_type": "quick_scan",
        "problems_found": len(problems),
        "problems": problems,
        "cta": cta_text,
        "cta_button": cta_button,
        "trust_note": note,
        "lang": lang,
    }
