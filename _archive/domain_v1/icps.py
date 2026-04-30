"""CIA's 6 Tier-1 ICPs + Tier-2 generic — extracted from Doc02 ICP Playbook.

Each ICP has calibrated pain language (THEIR words), ROI hooks, pricing bands,
objection overrides, and vacation pitches. Tier-2 is a catch-all for any
industry not in the six — still gets full audit, just without calibrated depth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Tier(str, Enum):
    TIER_1 = "tier_1"  # 6 ICPs premium
    TIER_2 = "tier_2"  # cualquier otra industria


@dataclass(frozen=True)
class ServicePricing:
    """A single CIA service with its pricing range."""
    name: str
    price_min: int
    price_max: int
    duration: str
    focus: str


@dataclass(frozen=True)
class ICP:
    """Ideal Customer Profile with full sales context."""
    id: str
    name: str
    name_es: str
    tier: Tier
    employee_range: str  # e.g. "50-500"

    # ─── Pain language (THEIR words, from Doc02) ──────────
    pain_phrases_es: list[str] = field(default_factory=list)
    pain_phrases_en: list[str] = field(default_factory=list)
    core_pain_es: str = ""
    core_pain_en: str = ""

    # ─── Decision maker ──────────────────────────────────
    decision_maker: str = ""
    sales_cycle: str = ""

    # ─── Services & pricing ──────────────────────────────
    services: list[ServicePricing] = field(default_factory=list)

    # ─── ROI ─────────────────────────────────────────────
    roi_hook_es: str = ""
    roi_hook_en: str = ""

    # ─── Vacation pitch (Doc01 CLOSER) ───────────────────
    vacation_pitch_es: str = ""
    vacation_pitch_en: str = ""

    # ─── Unique objection for this ICP (Doc03) ───────────
    unique_objection_es: str = ""
    unique_objection_response_es: str = ""

    # ─── Processes most likely leaking revenue ───────────
    common_leak_processes: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# TIER 1 — 6 ICPs premium (Doc02)
# ═══════════════════════════════════════════════════════════

CONSTRUCTION = ICP(
    id="construction",
    name="Construction & Real Estate",
    name_es="Construcción e Inmobiliario",
    tier=Tier.TIER_1,
    employee_range="50-500",
    pain_phrases_es=[
        "se nos pierden cotizaciones entre obras",
        "no sabemos cuántas cotizaciones mandamos la semana pasada",
        "el Excel de seguimiento nadie lo actualiza",
        "los maestros no reportan avance a tiempo",
    ],
    pain_phrases_en=[
        "we lose quotes between job sites",
        "we don't know how many quotes we sent last week",
        "nobody updates the tracking spreadsheet",
        "foremen don't report progress on time",
    ],
    core_pain_es="Pipeline leakage — cotizaciones perdidas entre obras",
    core_pain_en="Pipeline leakage — lost quotes between job sites",
    decision_maker="Director de operaciones / Gerente general",
    sales_cycle="4-8 semanas",
    services=[
        ServicePricing("Revenue Leak Audit", 2_000, 5_000, "2-3 semanas",
                        "Mapear dónde se pierden cotizaciones y seguimiento"),
        ServicePricing("Predictable Revenue Architecture", 4_000, 25_000, "4-8 semanas",
                        "CRM + pipeline automatizado + alertas de seguimiento"),
    ],
    roi_hook_es="Cada cotización perdida = revenue leak directo. Si pierdes 5 al mes de $10K promedio, son $50K/mes en oportunidad perdida.",
    roi_hook_en="Every lost quote = direct revenue leak. If you lose 5/month at $10K avg, that's $50K/month in missed opportunity.",
    vacation_pitch_es="Imagina abrir tu laptop el lunes y ver exactamente cuántas cotizaciones están vivas, cuáles se enfriaron, y cuáles necesitan seguimiento hoy — sin preguntarle a nadie.",
    vacation_pitch_en="Imagine opening your laptop Monday and seeing exactly which quotes are alive, which went cold, and which need follow-up today — without asking anyone.",
    unique_objection_es="Mis maestros no van a usar software",
    unique_objection_response_es="No necesitan. El sistema captura la info de WhatsApp que ya usan. Ellos siguen igual, tú ves todo.",
    common_leak_processes=[
        "quote_tracking", "project_handoff", "progress_reporting",
        "invoice_follow_up", "subcontractor_coordination", "material_ordering",
    ],
)

HEALTHCARE = ICP(
    id="healthcare",
    name="Healthcare Clinics",
    name_es="Clínicas de Salud",
    tier=Tier.TIER_1,
    employee_range="10-200",
    pain_phrases_es=[
        "agujero negro de citas",
        "los pacientes no llegan y no avisan",
        "la facturación se atrasa semanas",
        "las llamadas perdidas son plata perdida",
    ],
    pain_phrases_en=[
        "appointment black hole",
        "patients don't show up and don't call",
        "billing is weeks behind",
        "missed calls are missed revenue",
    ],
    core_pain_es="No-shows + llamadas perdidas + ciclo de facturación lento",
    core_pain_en="No-shows + missed calls + slow billing cycle",
    decision_maker="Director médico / Administrador",
    sales_cycle="3-6 semanas",
    services=[
        ServicePricing("Revenue Leak Audit", 2_000, 5_000, "2-3 semanas",
                        "Mapear no-shows, llamadas perdidas, ciclo de facturación"),
        ServicePricing("Agentic Strategy", 5_000, 20_000, "4-8 semanas",
                        "Bot de confirmación + captura de llamadas + billing automation"),
    ],
    roi_hook_es="Cada no-show es una cita vacía que costó agendar. Si tienes 15 no-shows/semana a $80 promedio, son $4,800/mes perdidos.",
    roi_hook_en="Every no-show is an empty slot that cost money to schedule. 15 no-shows/week at $80 avg = $4,800/month lost.",
    vacation_pitch_es="Imagina que cada paciente recibe confirmación automática, cada llamada perdida se devuelve en 5 minutos, y la facturación sale el mismo día del servicio.",
    vacation_pitch_en="Imagine every patient gets auto-confirmed, every missed call returned in 5 minutes, and billing goes out same day as service.",
    unique_objection_es="Los datos de pacientes son sensibles",
    unique_objection_response_es="Totalmente. Por eso usamos sistemas HIPAA-compatible y los datos nunca salen de tu infraestructura. CIA no almacena datos de pacientes.",
    common_leak_processes=[
        "appointment_scheduling", "no_show_management", "call_handling",
        "billing_cycle", "patient_intake", "insurance_claims",
    ],
)

AGENCIES = ICP(
    id="agencies",
    name="Digital Agencies",
    name_es="Agencias Digitales",
    tier=Tier.TIER_1,
    employee_range="20-100",
    pain_phrases_es=[
        "mis márgenes se los come ChatGPT",
        "el cliente quiere más por menos",
        "no podemos escalar sin contratar",
        "cada proyecto es custom, nada se reutiliza",
    ],
    pain_phrases_en=[
        "ChatGPT is eating my margins",
        "clients want more for less",
        "we can't scale without hiring",
        "every project is custom, nothing reusable",
    ],
    core_pain_es="Commoditization por IA — márgenes comprimidos, diferenciación en riesgo",
    core_pain_en="AI commoditization — compressed margins, differentiation at risk",
    decision_maker="CEO / Director creativo",
    sales_cycle="2-4 semanas",
    services=[
        ServicePricing("Agentic Strategy", 5_000, 20_000, "4-8 semanas",
                        "Automatizar deliverables repetitivos + crear IP interna"),
        ServicePricing("Living System Retainer", 500, 3_000, "mensual",
                        "Optimización continua + nuevas automatizaciones cada mes"),
    ],
    roi_hook_es="Automatizar deliverables repetitivos = +15-25% margen neto sin contratar. Si facturas $200K/mes, eso es $30-50K extra al año.",
    roi_hook_en="Automating repetitive deliverables = +15-25% net margin without hiring. At $200K/month revenue, that's $30-50K extra/year.",
    vacation_pitch_es="Imagina que los reportes semanales de clientes se generan solos, el onboarding de proyectos toma 1 hora en vez de 1 semana, y tu equipo solo hace lo creativo.",
    vacation_pitch_en="Imagine client weekly reports generate themselves, project onboarding takes 1 hour instead of 1 week, and your team only does the creative work.",
    unique_objection_es="Si automatizamos, ¿no nos volvemos prescindibles?",
    unique_objection_response_es="Al revés. Automatizar lo repetitivo te libera para lo estratégico — que es lo que el cliente NO puede reemplazar con ChatGPT.",
    common_leak_processes=[
        "client_reporting", "project_onboarding", "content_production",
        "time_tracking", "invoicing", "proposal_creation",
    ],
)

ECOMMERCE = ICP(
    id="ecommerce",
    name="E-commerce & Retail",
    name_es="E-commerce y Retail",
    tier=Tier.TIER_1,
    employee_range="20-500",
    pain_phrases_es=[
        "70% de carritos abandonados",
        "la conversión está estancada",
        "no sabemos por qué no compran",
        "el customer journey está roto",
    ],
    pain_phrases_en=[
        "70% cart abandonment",
        "conversion is stuck",
        "we don't know why they don't buy",
        "the customer journey is broken",
    ],
    core_pain_es="Abandono de carrito + conversión estancada + journey roto",
    core_pain_en="Cart abandonment + stuck conversion + broken journey",
    decision_maker="CEO / Director de e-commerce / CMO",
    sales_cycle="3-6 semanas",
    services=[
        ServicePricing("Revenue Leak Audit", 2_000, 5_000, "2-3 semanas",
                        "Mapear puntos de fuga en el customer journey"),
        ServicePricing("Predictable Revenue Architecture", 4_000, 25_000, "4-8 semanas",
                        "Recovery flows + personalization + automated nurture"),
    ],
    roi_hook_es="Reducir abandono de carrito 10% en un store de $500K/mes = $50K/mes en revenue recuperado.",
    roi_hook_en="Reducing cart abandonment 10% on a $500K/month store = $50K/month in recovered revenue.",
    vacation_pitch_es="Imagina que cada carrito abandonado recibe un follow-up inteligente en 15 minutos, cada cliente repetido recibe ofertas personalizadas, y tu conversión sube 2-3% sin tocar el diseño.",
    vacation_pitch_en="Imagine every abandoned cart gets a smart follow-up in 15 minutes, every repeat customer gets personalized offers, and your conversion goes up 2-3% without touching the design.",
    unique_objection_es="Ya tenemos Shopify/Vtex con plugins",
    unique_objection_response_es="Los plugins resuelven pedazos. Nosotros conectamos el journey completo — desde el primer click hasta la recompra. La diferencia es la orquestación.",
    common_leak_processes=[
        "cart_recovery", "email_nurture", "customer_segmentation",
        "inventory_sync", "order_fulfillment", "return_handling",
    ],
)

STARTUPS = ICP(
    id="startups",
    name="Funded Startups (Series A-B)",
    name_es="Startups Fondeadas (Serie A-B)",
    tier=Tier.TIER_1,
    employee_range="15-100",
    pain_phrases_es=[
        "quemando runway, board pregunta por IA",
        "necesitamos mostrar tracción de IA al board",
        "el equipo es pequeño y cada hora cuenta",
        "no tenemos tiempo de evaluar herramientas",
    ],
    pain_phrases_en=[
        "burning runway, board asking about AI",
        "we need to show AI traction to the board",
        "team is small and every hour counts",
        "no time to evaluate tools",
    ],
    core_pain_es="Burn rate + presión del board por AI traction + equipo limitado",
    core_pain_en="Burn rate + board pressure for AI traction + limited team",
    decision_maker="CEO / CTO / COO",
    sales_cycle="2-4 semanas",
    services=[
        ServicePricing("Agentic Strategy", 5_000, 20_000, "4-8 semanas",
                        "Implementar IA que el board pueda ver y medir"),
        ServicePricing("Living System Retainer", 500, 3_000, "mensual",
                        "Optimización continua + métricas para el board cada mes"),
    ],
    roi_hook_es="Automatizar X proceso = Y meses extra de runway. Si reduces $15K/mes en costos operativos, extiendes runway 4 meses.",
    roi_hook_en="Automating X process = Y extra months of runway. If you cut $15K/month in ops costs, you extend runway by 4 months.",
    vacation_pitch_es="Imagina llegar al board meeting con métricas de IA implementada, costos operativos reducidos 20%, y un roadmap de automatización que impresiona a los inversionistas.",
    vacation_pitch_en="Imagine walking into the board meeting with implemented AI metrics, ops costs down 20%, and an automation roadmap that impresses investors.",
    unique_objection_es="No tenemos presupuesto para consultoría",
    unique_objection_response_es="¿Y si la consultoría se paga sola en 30 días? El audit cuesta $3K. Si procedes en 30 días, se acredita 100%. En la práctica, el audit fue gratis.",
    common_leak_processes=[
        "onboarding_flow", "customer_support", "data_pipeline",
        "reporting_to_board", "hiring_process", "product_feedback_loop",
    ],
)

ENTERPRISE = ICP(
    id="enterprise",
    name="Enterprise with Innovation Budget",
    name_es="Enterprise con Presupuesto de Innovación",
    tier=Tier.TIER_1,
    employee_range="500+",
    pain_phrases_es=[
        "purgatorio de PoC",
        "$200K en PowerPoints de Big4 y nada implementado",
        "el comité de innovación no tiene resultados que mostrar",
        "llevamos 18 meses evaluando y no hemos desplegado nada",
    ],
    pain_phrases_en=[
        "PoC purgatory",
        "$200K in Big4 PowerPoints and nothing deployed",
        "the innovation committee has no results to show",
        "we've been evaluating for 18 months and deployed nothing",
    ],
    core_pain_es="Purgatorio de PoC — presupuesto gastado, nada implementado",
    core_pain_en="PoC purgatory — budget spent, nothing implemented",
    decision_maker="VP Innovación / CTO / CDO",
    sales_cycle="6-12 semanas",
    services=[
        ServicePricing("Bespoke Systems", 30_000, 100_000, "8-16 semanas",
                        "Arquitectura custom + implementación completa + handoff"),
        ServicePricing("Living System Retainer", 1_000, 3_000, "mensual",
                        "Soporte continuo + evolución del sistema"),
    ],
    roi_hook_es="Salir del purgatorio de PoC en 90 días vs 18 meses. Un solo proceso automatizado puede ahorrar $500K/año.",
    roi_hook_en="Exit PoC purgatory in 90 days vs 18 months. A single automated process can save $500K/year.",
    vacation_pitch_es="Imagina que en 90 días tienes un sistema funcionando que el comité puede demostrar al board — no otro PowerPoint, sino software que corre.",
    vacation_pitch_en="Imagine in 90 days you have a running system the committee can demo to the board — not another PowerPoint, but software that runs.",
    unique_objection_es="¿Por qué no contratar a Accenture/McKinsey?",
    unique_objection_response_es="Accenture te cobra $200K por la recomendación. Nosotros implementamos por una fracción y el sistema queda corriendo en 90 días. Si no funciona, no pagas el siguiente milestone.",
    common_leak_processes=[
        "innovation_pipeline", "vendor_evaluation", "compliance_reporting",
        "cross_department_handoffs", "legacy_system_integration", "board_reporting",
    ],
)

# ═══════════════════════════════════════════════════════════
# TIER 2 — Generic (any industry)
# ═══════════════════════════════════════════════════════════

GENERIC = ICP(
    id="generic",
    name="Any Business",
    name_es="Cualquier Negocio",
    tier=Tier.TIER_2,
    employee_range="1-10000+",
    pain_phrases_es=[
        "perdemos tiempo en cosas que deberían ser automáticas",
        "no sé por dónde empezar a automatizar",
        "todo es manual y no escala",
    ],
    pain_phrases_en=[
        "we waste time on things that should be automatic",
        "I don't know where to start automating",
        "everything is manual and doesn't scale",
    ],
    core_pain_es="Procesos manuales que no escalan — no sabe por dónde empezar",
    core_pain_en="Manual processes that don't scale — doesn't know where to start",
    decision_maker="CEO / Founder / Director de operaciones",
    sales_cycle="2-8 semanas",
    services=[
        ServicePricing("Revenue Leak Audit", 2_000, 5_000, "2-3 semanas",
                        "Mapear procesos manuales y oportunidades de automatización"),
        ServicePricing("Predictable Revenue Architecture", 4_000, 25_000, "4-8 semanas",
                        "Diseño e implementación de automatización personalizada"),
        ServicePricing("Living System Retainer", 500, 3_000, "mensual",
                        "Optimización continua + soporte"),
    ],
    roi_hook_es="El empleado promedio gasta 4.5 horas/semana en tareas repetitivas. Automatizar las top 3 puede liberar 20+ horas/semana para tu equipo.",
    roi_hook_en="The average employee spends 4.5 hours/week on repetitive tasks. Automating the top 3 can free 20+ hours/week for your team.",
    vacation_pitch_es="Imagina que las tareas que tu equipo odia hacer — reportes, data entry, seguimiento manual — simplemente pasan solas.",
    vacation_pitch_en="Imagine the tasks your team hates — reports, data entry, manual follow-ups — just happen on their own.",
    unique_objection_es="No estamos listos para IA",
    unique_objection_response_es="No se trata de IA. Se trata de que lo que ya funciona, funcione solo. Empezamos con lo simple — cero IA si no la necesitas.",
    common_leak_processes=[
        "sales_follow_up", "client_onboarding", "invoicing",
        "reporting", "internal_communication", "scheduling",
        "data_entry", "email_management",
    ],
)

# ─── Registry ─────────────────────────────────────────────

ALL_ICPS: dict[str, ICP] = {
    icp.id: icp
    for icp in [CONSTRUCTION, HEALTHCARE, AGENCIES, ECOMMERCE, STARTUPS, ENTERPRISE, GENERIC]
}

TIER_1_IDS: set[str] = {icp.id for icp in ALL_ICPS.values() if icp.tier == Tier.TIER_1}


def detect_icp(industry_hint: str | None) -> ICP:
    """Best-effort ICP detection from a free-text industry hint.

    Returns GENERIC if no Tier-1 match is found.
    """
    if not industry_hint:
        return GENERIC

    hint = industry_hint.lower().strip()

    # Simple keyword matching — good enough for v0.1, LLM-assisted in v0.2
    _mapping: dict[str, str] = {
        "construc": "construction", "inmobili": "construction", "real estate": "construction",
        "obra": "construction", "architect": "construction",
        "clínic": "healthcare", "clinic": "healthcare", "hospital": "healthcare",
        "salud": "healthcare", "health": "healthcare", "médic": "healthcare",
        "dental": "healthcare", "doctor": "healthcare",
        "agencia": "agencies", "agency": "agencies", "digital": "agencies",
        "marketing": "agencies", "creativ": "agencies", "publicidad": "agencies",
        "ecommerce": "ecommerce", "e-commerce": "ecommerce", "retail": "ecommerce",
        "tienda": "ecommerce", "store": "ecommerce", "shop": "ecommerce",
        "cart": "ecommerce", "carrito": "ecommerce",
        "startup": "startups", "serie a": "startups", "series a": "startups",
        "serie b": "startups", "series b": "startups", "funded": "startups",
        "venture": "startups", "runway": "startups",
        "enterprise": "enterprise", "corporat": "enterprise", "fortune": "enterprise",
        "innovación": "enterprise", "innovation": "enterprise",
    }
    for keyword, icp_id in _mapping.items():
        if keyword in hint:
            return ALL_ICPS[icp_id]

    return GENERIC
