"""Adaptive question bank for the audit flow.

Each audit session walks through 5-7 questions. Tier 1 ICPs get calibrated
questions with industry-specific pain language; Tier 2 gets intelligent
generic questions that still surface real pain points.

Questions use UI component hints so the Claude host can render appropriate
widgets (slider, dropdown, multi_select, textarea, yes_no).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from univercity_mcp.domain.icps import ICP, Tier, ALL_ICPS


# ─── UI component types ──────────────────────────────────

class UIComponent(str, Enum):
    SLIDER = "slider"           # 1-10 scale
    DROPDOWN = "dropdown"       # single select
    MULTI_SELECT = "multi_select"
    TEXTAREA = "textarea"       # free text
    YES_NO = "yes_no"


@dataclass(frozen=True)
class QuestionOption:
    """Single option for dropdown / multi_select."""
    value: str
    label_es: str
    label_en: str
    weight: float = 1.0  # scoring weight when selected


@dataclass(frozen=True)
class Question:
    """A single audit question with i18n and branching support."""
    id: str
    order: int
    label_es: str
    label_en: str
    ui_component: UIComponent
    category: str  # maps to scoring dimensions

    # Options (for dropdown / multi_select)
    options: list[QuestionOption] = field(default_factory=list)

    # Slider config
    slider_min: int = 1
    slider_max: int = 10
    slider_labels_es: tuple[str, str] = ("Muy bajo", "Muy alto")
    slider_labels_en: tuple[str, str] = ("Very low", "Very high")

    # Branching: if answer matches a value, inject follow-up question id
    branch_on: dict[str, str] = field(default_factory=dict)

    # Help text
    help_es: str = ""
    help_en: str = ""

    # Is this a follow-up (not shown by default)?
    is_followup: bool = False


# ═══════════════════════════════════════════════════════════
# SHARED QUESTIONS — used across all tiers
# ═══════════════════════════════════════════════════════════

Q_COMPANY_SIZE = Question(
    id="company_size",
    order=1,
    label_es="¿Cuántas personas trabajan en tu empresa?",
    label_en="How many people work at your company?",
    ui_component=UIComponent.DROPDOWN,
    category="profile",
    options=[
        QuestionOption("1-10", "1-10 personas", "1-10 people", 0.5),
        QuestionOption("11-50", "11-50 personas", "11-50 people", 0.8),
        QuestionOption("51-200", "51-200 personas", "51-200 people", 1.0),
        QuestionOption("201-500", "201-500 personas", "201-500 people", 1.2),
        QuestionOption("500+", "Más de 500", "More than 500", 1.5),
    ],
)

Q_CURRENT_TOOLS = Question(
    id="current_tools",
    order=2,
    label_es="¿Qué herramientas de software usan actualmente?",
    label_en="What software tools do you currently use?",
    ui_component=UIComponent.MULTI_SELECT,
    category="tech_maturity",
    options=[
        QuestionOption("crm", "CRM (HubSpot, Salesforce, Pipedrive...)", "CRM (HubSpot, Salesforce, Pipedrive...)", 1.0),
        QuestionOption("erp", "ERP (SAP, Oracle, Odoo...)", "ERP (SAP, Oracle, Odoo...)", 1.2),
        QuestionOption("spreadsheets", "Excel / Google Sheets", "Excel / Google Sheets", 0.5),
        QuestionOption("project_mgmt", "Gestión de proyectos (Asana, Monday, Trello...)", "Project management (Asana, Monday, Trello...)", 0.8),
        QuestionOption("automation", "Automatización (Zapier, Make, n8n...)", "Automation (Zapier, Make, n8n...)", 1.5),
        QuestionOption("ai_tools", "Herramientas de IA (ChatGPT, Copilot...)", "AI tools (ChatGPT, Copilot...)", 1.3),
        QuestionOption("whatsapp", "WhatsApp Business", "WhatsApp Business", 0.6),
        QuestionOption("none", "Ninguna / solo email", "None / email only", 0.3),
    ],
    help_es="Selecciona todas las que apliquen. Esto nos ayuda a entender tu punto de partida.",
    help_en="Select all that apply. This helps us understand your starting point.",
)

Q_REVENUE_RANGE = Question(
    id="revenue_range",
    order=3,
    label_es="¿Cuál es el rango de facturación mensual de tu empresa?",
    label_en="What is your company's monthly revenue range?",
    ui_component=UIComponent.DROPDOWN,
    category="profile",
    options=[
        QuestionOption("under_50k", "Menos de $50K/mes", "Under $50K/month", 0.5),
        QuestionOption("50k_200k", "$50K - $200K/mes", "$50K - $200K/month", 0.8),
        QuestionOption("200k_1m", "$200K - $1M/mes", "$200K - $1M/month", 1.0),
        QuestionOption("1m_5m", "$1M - $5M/mes", "$1M - $5M/month", 1.3),
        QuestionOption("over_5m", "Más de $5M/mes", "Over $5M/month", 1.5),
        QuestionOption("prefer_not", "Prefiero no decir", "Prefer not to say", 0.7),
    ],
    help_es="Esto ayuda a calibrar las recomendaciones a tu escala. Es confidencial.",
    help_en="This helps calibrate recommendations to your scale. It's confidential.",
)

Q_BIGGEST_PAIN = Question(
    id="biggest_pain",
    order=5,
    label_es="¿Cuál es el problema operativo más urgente que quieres resolver?",
    label_en="What is the most urgent operational problem you want to solve?",
    ui_component=UIComponent.TEXTAREA,
    category="pain",
    help_es="Describe en tus propias palabras. No hay respuesta incorrecta.",
    help_en="Describe in your own words. There's no wrong answer.",
)

Q_AI_READINESS = Question(
    id="ai_readiness",
    order=6,
    label_es="¿Qué tan listo sientes que está tu equipo para adoptar automatización o IA?",
    label_en="How ready do you feel your team is to adopt automation or AI?",
    ui_component=UIComponent.SLIDER,
    category="readiness",
    slider_min=1,
    slider_max=10,
    slider_labels_es=("No estamos listos", "Totalmente listos"),
    slider_labels_en=("Not ready at all", "Fully ready"),
    help_es="1 = 'ni idea de qué es IA' — 10 = 'ya tenemos cosas corriendo'",
    help_en="1 = 'no idea what AI is' — 10 = 'we already have things running'",
)

Q_BUDGET_COMFORT = Question(
    id="budget_comfort",
    order=7,
    label_es="¿Hay presupuesto asignado para mejorar procesos este trimestre?",
    label_en="Is there budget allocated for process improvement this quarter?",
    ui_component=UIComponent.DROPDOWN,
    category="closer",
    options=[
        QuestionOption("yes_defined", "Sí, ya está definido", "Yes, already defined", 1.5),
        QuestionOption("yes_flexible", "Sí, pero es flexible", "Yes, but it's flexible", 1.2),
        QuestionOption("exploring", "Estamos explorando", "We're exploring", 0.8),
        QuestionOption("no_budget", "No hay presupuesto aún", "No budget yet", 0.5),
        QuestionOption("if_roi", "Solo si se demuestra ROI", "Only if ROI is proven", 1.0),
    ],
    help_es="Esto nos ayuda a calibrar opciones: gratis, pagadas, y CIA.",
    help_en="This helps us calibrate options: free, paid, and CIA.",
)


# ═══════════════════════════════════════════════════════════
# TIER 1 — Industry-specific questions (order=4, the pivot)
# ═══════════════════════════════════════════════════════════

_TIER1_QUESTIONS: dict[str, Question] = {
    "construction": Question(
        id="construction_leak",
        order=4,
        label_es="¿Dónde sientes que se pierden más oportunidades en tu operación?",
        label_en="Where do you feel the most opportunities are lost in your operation?",
        ui_component=UIComponent.MULTI_SELECT,
        category="pain",
        options=[
            QuestionOption("quotes", "Cotizaciones que no se siguen", "Quotes that don't get followed up", 1.5),
            QuestionOption("handoffs", "Información que se pierde entre obras", "Info lost between job sites", 1.3),
            QuestionOption("progress", "Reportes de avance atrasados", "Delayed progress reports", 1.0),
            QuestionOption("invoicing", "Facturación lenta o errores en cobros", "Slow billing or invoicing errors", 1.2),
            QuestionOption("subcontractors", "Coordinación con subcontratistas", "Subcontractor coordination", 0.8),
            QuestionOption("materials", "Pedidos de material mal calculados", "Miscalculated material orders", 0.9),
        ],
        help_es="Selecciona las que te duelan más. Esto calibra tu Revenue Leak Score.",
        help_en="Select the ones that hurt most. This calibrates your Revenue Leak Score.",
    ),

    "healthcare": Question(
        id="healthcare_leak",
        order=4,
        label_es="¿Cuáles de estos problemas te cuestan más dinero?",
        label_en="Which of these problems cost you the most money?",
        ui_component=UIComponent.MULTI_SELECT,
        category="pain",
        options=[
            QuestionOption("no_shows", "No-shows de pacientes", "Patient no-shows", 1.5),
            QuestionOption("missed_calls", "Llamadas perdidas", "Missed calls", 1.3),
            QuestionOption("billing_delay", "Facturación atrasada semanas", "Billing delayed by weeks", 1.2),
            QuestionOption("intake", "Proceso de intake manual/lento", "Slow/manual intake process", 1.0),
            QuestionOption("insurance", "Problemas con aseguradoras", "Insurance claim issues", 0.9),
            QuestionOption("scheduling", "Agendamiento ineficiente", "Inefficient scheduling", 1.1),
        ],
        help_es="Cada uno de estos tiene un costo calculable. Selecciona los que te afectan más.",
        help_en="Each of these has a calculable cost. Select the ones affecting you most.",
    ),

    "agencies": Question(
        id="agencies_leak",
        order=4,
        label_es="¿Qué está comprimiendo tus márgenes ahora mismo?",
        label_en="What's compressing your margins right now?",
        ui_component=UIComponent.MULTI_SELECT,
        category="pain",
        options=[
            QuestionOption("commoditization", "Clientes piden más por menos (efecto ChatGPT)", "Clients want more for less (ChatGPT effect)", 1.5),
            QuestionOption("custom_everything", "Cada proyecto es custom, nada se reutiliza", "Every project is custom, nothing reusable", 1.3),
            QuestionOption("reporting", "Reportes semanales manuales a clientes", "Manual weekly client reports", 1.1),
            QuestionOption("hiring", "No puedes escalar sin contratar", "Can't scale without hiring", 1.2),
            QuestionOption("onboarding", "Onboarding de proyectos toma demasiado", "Project onboarding takes too long", 1.0),
            QuestionOption("proposals", "Propuestas toman días en hacer", "Proposals take days to create", 0.9),
        ],
        help_es="Selecciona todo lo que aplique. Esto nos muestra dónde está tu oportunidad de margen.",
        help_en="Select all that apply. This shows us where your margin opportunity is.",
    ),

    "ecommerce": Question(
        id="ecommerce_leak",
        order=4,
        label_es="¿Dónde estás perdiendo más ventas?",
        label_en="Where are you losing the most sales?",
        ui_component=UIComponent.MULTI_SELECT,
        category="pain",
        options=[
            QuestionOption("cart_abandon", "Carritos abandonados sin recovery", "Abandoned carts without recovery", 1.5),
            QuestionOption("no_nurture", "No hay nurture post-compra", "No post-purchase nurture", 1.2),
            QuestionOption("segmentation", "No segmentamos clientes", "We don't segment customers", 1.1),
            QuestionOption("inventory", "Problemas de inventario / desync", "Inventory issues / desync", 1.0),
            QuestionOption("returns", "Proceso de devoluciones costoso", "Expensive returns process", 0.9),
            QuestionOption("support", "Soporte al cliente lento", "Slow customer support", 1.0),
        ],
        help_es="Cada punto de fuga tiene un revenue leak estimable. Selecciona los más relevantes.",
        help_en="Each leak point has an estimable revenue loss. Select the most relevant ones.",
    ),

    "startups": Question(
        id="startups_leak",
        order=4,
        label_es="¿Cuál es la presión más fuerte que sientes ahora?",
        label_en="What's the strongest pressure you're feeling right now?",
        ui_component=UIComponent.MULTI_SELECT,
        category="pain",
        options=[
            QuestionOption("runway", "Burn rate alto, necesito extender runway", "High burn rate, need to extend runway", 1.5),
            QuestionOption("board_ai", "Board pregunta por IA y no tengo respuesta", "Board asking about AI and I don't have answers", 1.3),
            QuestionOption("manual_ops", "Operaciones manuales que no escalan", "Manual ops that don't scale", 1.2),
            QuestionOption("hiring_cost", "Costo de hiring para escalar", "Hiring costs to scale", 1.0),
            QuestionOption("tool_eval", "Demasiado tiempo evaluando herramientas", "Too much time evaluating tools", 0.9),
            QuestionOption("metrics", "No tenemos métricas claras de eficiencia", "No clear efficiency metrics", 1.1),
        ],
        help_es="Esto nos ayuda a diseñar la narrativa que tu board quiere escuchar.",
        help_en="This helps us design the narrative your board wants to hear.",
    ),

    "enterprise": Question(
        id="enterprise_leak",
        order=4,
        label_es="¿Qué está frenando tu iniciativa de innovación?",
        label_en="What's stalling your innovation initiative?",
        ui_component=UIComponent.MULTI_SELECT,
        category="pain",
        options=[
            QuestionOption("poc_purgatory", "PoCs que nunca llegan a producción", "PoCs that never reach production", 1.5),
            QuestionOption("big4_fatigue", "Cansancio de consultoras que solo entregan PPTs", "Tired of consultants delivering only PPTs", 1.4),
            QuestionOption("compliance", "Compliance frena todo", "Compliance blocks everything", 1.0),
            QuestionOption("silos", "Silos entre departamentos", "Cross-department silos", 1.2),
            QuestionOption("legacy", "Integración con sistemas legacy", "Legacy system integration", 1.1),
            QuestionOption("committee", "Comité de innovación sin resultados medibles", "Innovation committee with no measurable results", 1.3),
        ],
        help_es="Selecciona todo lo que aplique. Estos son los cuellos de botella que convertimos en ROI.",
        help_en="Select all that apply. These are the bottlenecks we convert into ROI.",
    ),
}

# Tier 2 — generic industry question
_TIER2_QUESTION = Question(
    id="generic_leak",
    order=4,
    label_es="¿Cuáles de estos problemas reconoces en tu empresa?",
    label_en="Which of these problems do you recognize in your company?",
    ui_component=UIComponent.MULTI_SELECT,
    category="pain",
    options=[
        QuestionOption("manual_tasks", "Tareas repetitivas que alguien hace a mano", "Repetitive tasks done manually", 1.3),
        QuestionOption("follow_up", "Seguimiento a clientes que se olvida", "Client follow-ups that get forgotten", 1.4),
        QuestionOption("data_scattered", "Datos dispersos (Excel, email, WhatsApp...)", "Scattered data (Excel, email, WhatsApp...)", 1.2),
        QuestionOption("reporting", "Reportes que toman horas en hacer", "Reports that take hours to create", 1.1),
        QuestionOption("onboarding", "Onboarding de clientes/empleados lento", "Slow client/employee onboarding", 1.0),
        QuestionOption("invoicing", "Facturación manual o atrasada", "Manual or delayed invoicing", 1.2),
        QuestionOption("communication", "Comunicación interna fragmentada", "Fragmented internal communication", 0.9),
        QuestionOption("scheduling", "Agendamiento manual", "Manual scheduling", 0.8),
    ],
    help_es="Selecciona todos los que apliquen. Esto nos ayuda a priorizar dónde empezar.",
    help_en="Select all that apply. This helps us prioritize where to start.",
)


# ═══════════════════════════════════════════════════════════
# FOLLOW-UP questions (triggered by branching)
# ═══════════════════════════════════════════════════════════

FOLLOWUP_NO_TOOLS = Question(
    id="followup_no_tools",
    order=2,
    label_es="¿Cómo gestionas tus clientes y ventas actualmente?",
    label_en="How do you currently manage your clients and sales?",
    ui_component=UIComponent.DROPDOWN,
    category="tech_maturity",
    options=[
        QuestionOption("memory", "De memoria / notas en papel", "From memory / paper notes", 0.3),
        QuestionOption("whatsapp", "WhatsApp + notas del celular", "WhatsApp + phone notes", 0.4),
        QuestionOption("basic_excel", "Excel básico", "Basic Excel", 0.5),
        QuestionOption("email_only", "Solo email", "Email only", 0.4),
    ],
    is_followup=True,
    help_es="No hay juicio aquí — necesitamos saber tu punto de partida real.",
    help_en="No judgment — we need to know your real starting point.",
)

FOLLOWUP_HAS_AUTOMATION = Question(
    id="followup_has_automation",
    order=2,
    label_es="¿Qué tienes automatizado actualmente?",
    label_en="What do you currently have automated?",
    ui_component=UIComponent.TEXTAREA,
    category="tech_maturity",
    is_followup=True,
    help_es="Cuéntanos qué automatizaciones ya tienes — Zapier, bots, scripts, lo que sea.",
    help_en="Tell us what automations you already have — Zapier, bots, scripts, anything.",
)

FOLLOWUP_HIGH_READINESS = Question(
    id="followup_high_readiness",
    order=6,
    label_es="¿Qué herramientas de IA o automatización ya están en producción?",
    label_en="What AI or automation tools are already in production?",
    ui_component=UIComponent.TEXTAREA,
    category="readiness",
    is_followup=True,
    help_es="Saber qué ya funciona nos ayuda a no reinventar la rueda.",
    help_en="Knowing what already works helps us avoid reinventing the wheel.",
)

_ALL_FOLLOWUPS: dict[str, Question] = {
    q.id: q for q in [FOLLOWUP_NO_TOOLS, FOLLOWUP_HAS_AUTOMATION, FOLLOWUP_HIGH_READINESS]
}


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════

def get_questions_for_icp(icp: ICP) -> list[Question]:
    """Return the ordered question list for a given ICP.

    Always 7 core questions. Follow-ups are injected dynamically at runtime
    based on answers (via `get_followup`).

    Order:
    1. company_size
    2. current_tools
    3. revenue_range
    4. industry-specific pain (Tier 1) or generic pain (Tier 2)
    5. biggest_pain (free text)
    6. ai_readiness
    7. budget_comfort
    """
    # Pick the industry-specific question
    if icp.tier == Tier.TIER_1 and icp.id in _TIER1_QUESTIONS:
        industry_q = _TIER1_QUESTIONS[icp.id]
    else:
        industry_q = _TIER2_QUESTION

    return sorted([
        Q_COMPANY_SIZE,
        Q_CURRENT_TOOLS,
        Q_REVENUE_RANGE,
        industry_q,
        Q_BIGGEST_PAIN,
        Q_AI_READINESS,
        Q_BUDGET_COMFORT,
    ], key=lambda q: q.order)


def get_followup(question_id: str, answer_value: str | list[str]) -> Question | None:
    """Determine if a follow-up question should be injected based on answers.

    Branching rules:
    - current_tools → "none" selected → followup_no_tools
    - current_tools → "automation" selected → followup_has_automation
    - ai_readiness → value >= 8 → followup_high_readiness
    """
    if question_id == "current_tools":
        values = answer_value if isinstance(answer_value, list) else [answer_value]
        if "none" in values:
            return FOLLOWUP_NO_TOOLS
        if "automation" in values:
            return FOLLOWUP_HAS_AUTOMATION

    if question_id == "ai_readiness":
        try:
            score = int(answer_value) if isinstance(answer_value, str) else answer_value
            if isinstance(score, (int, float)) and score >= 8:
                return FOLLOWUP_HIGH_READINESS
        except (ValueError, TypeError):
            pass

    return None


def get_all_question_ids() -> list[str]:
    """Return all question IDs (core + follow-ups) for validation."""
    core = {q.id for q in get_questions_for_icp(ALL_ICPS["generic"])}
    for icp_id in _TIER1_QUESTIONS:
        core.add(_TIER1_QUESTIONS[icp_id].id)
    followup = set(_ALL_FOLLOWUPS.keys())
    return sorted(core | followup)
