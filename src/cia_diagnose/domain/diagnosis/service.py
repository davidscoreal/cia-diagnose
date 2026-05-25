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

    if not session_id:
        session_id = str(uuid.uuid4())[:12]

    # ── Step 1: Detect ICP ──
    icp_id = _detect_icp(context)
    benchmark = load_benchmark(icp_id)
    icp_name = benchmark.get(f"name_{lang}", benchmark.get("name_en", icp_id))

    # ── Step 2: Score each dimension ──
    dimension_scores: list[DimensionScore] = []
    all_findings: list[Finding] = []

    for dim in Dimension:
        dim_config = get_dimension_config(benchmark, dim.value)
        weight = dim_config.get("weight", 0.0)

        if weight == 0.0:
            # Skip dimensions with zero weight for this ICP
            continue

        score, findings, data_quality = _score_dimension(dim, dim_config, context, lang)

        ds = DimensionScore(
            dimension=dim,
            score=score,
            weight=weight,
            findings=findings,
            data_quality=data_quality,
        )
        dimension_scores.append(ds)
        all_findings.extend(findings)

    # ── Step 3: Calculate Revenue Leak Score ──
    total_weight = sum(ds.weight for ds in dimension_scores) or 1.0
    revenue_leak_score = sum(ds.weighted_score for ds in dimension_scores) / total_weight
    revenue_leak_score = min(100.0, max(0.0, revenue_leak_score))
    leak_category = _categorize_leak(revenue_leak_score)

    # ── Step 4: Estimate monthly leak ──
    monthly_leak = _estimate_monthly_leak(context, revenue_leak_score)

    # ── Step 5: Generate Top Actions with Triple Option ──
    top_actions = _generate_actions(all_findings, benchmark, lang)

    # ── Step 6: Generate Validation Questions ──
    dims_with_data = sum(1 for ds in dimension_scores if ds.data_quality > 0.3)
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
        company_name, icp_name, revenue_leak_score, leak_category,
        monthly_leak, dimension_scores, len(all_findings), overall_dq,
    )

    leadership_es, leadership_en = _generate_leadership_insight(
        context, dimension_scores,
    )

    return DiagnosisReport(
        company_name=company_name,
        icp_id=icp_id,
        icp_name=icp_name,
        lang=lang,
        revenue_leak_score=revenue_leak_score,
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
        session_id=session_id,
        report_url="",
    )


# ─── ICP Detection ──────────────────────────────────────────────────


def _detect_icp(context: dict[str, Any]) -> str:
    """Detect ICP from context signals. Returns icp_id."""
    industry = str(context.get("industry", "")).lower()
    pain_points = [str(p).lower() for p in context.get("pain_points", [])]
    pain_text = " ".join(pain_points)
    team_size = context.get("team_size", 0)
    software = [str(s).lower() for s in context.get("software_detected", [])]

    # Direct industry match
    icp_map = {
        "construction": "construction",
        "construcción": "construction",
        "real estate": "construction",
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
    if condition == "always":
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

    return True  # Default: triggered


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


# ─── Revenue Leak Estimation ────────────────────────────────────────


def _categorize_leak(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _estimate_monthly_leak(context: dict, leak_score: float) -> tuple[int, int]:
    """Estimate MONTHLY revenue leak in USD as proportion of declared ANNUAL revenue.

    Bug fix 2026-05-23: previously (1) only read revenue_estimate but MCP passes
    revenue_range, (2) midpoints dict only covered ≥1M, and (3) applied annual %
    to annual midpoint without dividing by 12 → inflated 'monthly' leak by 12x.
    """
    # Accept multiple field names (MCP passes revenue_range; older callers use revenue_estimate)
    rev_str = str(
        context.get("revenue_range")
        or context.get("revenue_estimate")
        or context.get("annual_revenue")
        or ""
    ).lower().replace(" ", "").replace("_", "")

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
        # Fallback: parse explicit numbers like ".5M", "500000", "1.2m"
        import re
        match = re.search(r'(\d+(?:\.\d+)?)\s*([mk])?', rev_str)
        if match:
            num = float(match.group(1))
            unit = (match.group(2) or '').lower()
            if unit == 'm':
                midpoint = int(num * 1_000_000)
            elif unit == 'k':
                midpoint = int(num * 1_000)
            elif num >= 100_000:
                midpoint = int(num)
            else:
                midpoint = int(num * 1_000_000)  # bare number assume millions
        else:
            midpoint = 1_000_000  # Default ICP entry point

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
) -> tuple[str, str]:
    """Generate bilingual summary text."""
    # Top 3 dimensions by weighted score (most leakage)
    top_dims = sorted(dimensions, key=lambda d: d.weighted_score, reverse=True)[:3]

    top_dims_es = ", ".join(d.label_es for d in top_dims)
    top_dims_en = ", ".join(d.label_en for d in top_dims)

    cat_map_es = {
        "critical": "CRÍTICO", "high": "ALTO", "medium": "MEDIO", "low": "BAJO",
    }
    cat_map_en = {
        "critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW",
    }

    summary_es = (
        f"**{company_name}** — Nivel de fuga: **{cat_map_es.get(category, category)}** "
        f"(Revenue Leak Score: {score:.0f}/100)\n\n"
        f"Se identificaron {finding_count} hallazgos en {len(dimensions)} dimensiones. "
        f"Las áreas con mayor impacto son: **{top_dims_es}**.\n\n"
    )
    if monthly_leak[1] > 0:
        summary_es += (
            f"Estimación de fuga mensual: **${monthly_leak[0]:,} – ${monthly_leak[1]:,} USD**.\n\n"
        )
    if data_quality < 0.5:
        summary_es += (
            "⚠️ La calidad de datos es limitada. Respondiendo las preguntas de validación "
            "mejoraremos significativamente la precisión del diagnóstico."
        )

    summary_en = (
        f"**{company_name}** — Leak level: **{cat_map_en.get(category, category)}** "
        f"(Revenue Leak Score: {score:.0f}/100)\n\n"
        f"Identified {finding_count} findings across {len(dimensions)} dimensions. "
        f"Highest-impact areas: **{top_dims_en}**.\n\n"
    )
    if monthly_leak[1] > 0:
        summary_en += (
            f"Estimated monthly leak: **${monthly_leak[0]:,} – ${monthly_leak[1]:,} USD**.\n\n"
        )
    if data_quality < 0.5:
        summary_en += (
            "⚠️ Data quality is limited. Answering the validation questions "
            "will significantly improve diagnosis accuracy."
        )

    return summary_es, summary_en


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
