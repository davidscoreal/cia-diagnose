"""10 Core MCPs + OSS Alternatives — the Triple Option Model.

Every recommendation in the audit report shows 3 columns:
  1. Best PAID tool (the market leader)
  2. Best OPEN SOURCE alternative (tested by CIA monthly)
  3. CIA integration service (custom, tailored, full implementation)

This is CIA's strongest differentiator: radical transparency.
No commissions, no affiliate links. CIA recommends what works.
If the free option is good enough, we say so.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Tool:
    """A single tool (paid or OSS) in the toolstack."""
    name: str
    url: str
    category: str
    is_oss: bool
    price_range: str  # "Free", "$0-49/mo", "$50-200/mo", "Custom"

    # Strengths for quick comparison
    strengths: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    # CIA's assessment (updated monthly)
    cia_rating: float = 0.0  # 1-10
    last_tested: str = ""    # ISO date string
    verdict_es: str = ""
    verdict_en: str = ""


@dataclass(frozen=True)
class ToolCategory:
    """A category with paid + OSS + CIA option."""
    id: str
    name_es: str
    name_en: str
    description_es: str
    description_en: str

    paid: Tool
    oss: Tool

    # CIA's value-add for this category
    cia_service_es: str = ""
    cia_service_en: str = ""
    cia_price_range: str = ""

    # Which processes this category addresses
    addresses_processes: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════
# 10 Core Categories — Paid + OSS + CIA
# ═══════════════════════════════════════════════════════════

TOOLSTACK: list[ToolCategory] = [
    ToolCategory(
        id="crm",
        name_es="CRM — Gestión de Relaciones",
        name_en="CRM — Relationship Management",
        description_es="Centralizar contactos, pipeline de ventas, seguimiento de clientes",
        description_en="Centralize contacts, sales pipeline, client follow-up",
        paid=Tool(
            name="HubSpot CRM",
            url="https://hubspot.com",
            category="crm",
            is_oss=False,
            price_range="Free - $800/mo",
            strengths=["Ecosistema completo", "Muy intuitivo", "Free tier generoso"],
            limitations=["Escala de precio agresiva", "Lock-in fuerte"],
            cia_rating=8.5,
            last_tested="2026-04-01",
            verdict_es="El mejor CRM para PYMES. Free tier es suficiente para empezar.",
            verdict_en="Best CRM for SMBs. Free tier is enough to start.",
        ),
        oss=Tool(
            name="Twenty CRM",
            url="https://twenty.com",
            category="crm",
            is_oss=True,
            price_range="Free (self-hosted)",
            strengths=["Open source", "Diseño moderno", "API-first", "Self-hosted"],
            limitations=["Comunidad joven", "Menos integraciones nativas"],
            cia_rating=7.5,
            last_tested="2026-04-01",
            verdict_es="Excelente para equipos técnicos que quieren control total.",
            verdict_en="Excellent for tech teams that want full control.",
        ),
        cia_service_es="Implementación, migración de datos, workflows automáticos, integraciones custom",
        cia_service_en="Implementation, data migration, automated workflows, custom integrations",
        cia_price_range="$2,000 - $8,000",
        addresses_processes=["sales_follow_up", "quote_tracking", "client_onboarding"],
    ),

    ToolCategory(
        id="payments",
        name_es="Pagos y Facturación",
        name_en="Payments & Billing",
        description_es="Cobrar, facturar, suscripciones, revenue tracking",
        description_en="Collect payments, invoice, subscriptions, revenue tracking",
        paid=Tool(
            name="Stripe",
            url="https://stripe.com",
            category="payments",
            is_oss=False,
            price_range="2.9% + $0.30/tx",
            strengths=["API excepcional", "Global", "Suscripciones built-in"],
            limitations=["Fees en LATAM más altos", "Soporte puede ser lento"],
            cia_rating=9.0,
            last_tested="2026-04-01",
            verdict_es="Estándar de la industria. Difícil de superar en features.",
            verdict_en="Industry standard. Hard to beat on features.",
        ),
        oss=Tool(
            name="BTCPay Server",
            url="https://btcpayserver.org",
            category="payments",
            is_oss=True,
            price_range="Free (self-hosted)",
            strengths=["0% fees", "Soberanía total", "Crypto + fiat"],
            limitations=["Setup técnico", "Solo crypto nativo, fiat vía plugins"],
            cia_rating=7.0,
            last_tested="2026-04-01",
            verdict_es="Ideal para quien quiere 0 fees y acepta crypto. No reemplaza Stripe para todos.",
            verdict_en="Ideal for zero fees and crypto acceptance. Doesn't replace Stripe for everyone.",
        ),
        cia_service_es="Integración con ERP, facturación automática, reconciliación, suscripciones custom",
        cia_service_en="ERP integration, automatic billing, reconciliation, custom subscriptions",
        cia_price_range="$3,000 - $12,000",
        addresses_processes=["invoicing", "invoice_follow_up", "billing_cycle"],
    ),

    ToolCategory(
        id="automation",
        name_es="Automatización de Procesos",
        name_en="Process Automation",
        description_es="Conectar apps, automatizar workflows, eliminar tareas manuales",
        description_en="Connect apps, automate workflows, eliminate manual tasks",
        paid=Tool(
            name="Make (Integromat)",
            url="https://make.com",
            category="automation",
            is_oss=False,
            price_range="Free - $299/mo",
            strengths=["Visual builder potente", "1000+ integraciones", "Precio justo"],
            limitations=["Curva de aprendizaje media", "Debugging complejo"],
            cia_rating=8.5,
            last_tested="2026-04-01",
            verdict_es="Mejor balance precio/funcionalidad del mercado.",
            verdict_en="Best price/functionality balance on the market.",
        ),
        oss=Tool(
            name="n8n",
            url="https://n8n.io",
            category="automation",
            is_oss=True,
            price_range="Free (self-hosted) / $20/mo cloud",
            strengths=["Open source", "Self-hosted", "Extensible", "400+ nodos"],
            limitations=["UI menos pulida", "Documentación irregular"],
            cia_rating=8.0,
            last_tested="2026-04-01",
            verdict_es="La mejor opción open source. CIA lo usa internamente.",
            verdict_en="The best open source option. CIA uses it internally.",
        ),
        cia_service_es="Diseño de workflows, implementación, mantenimiento, migración desde Zapier",
        cia_service_en="Workflow design, implementation, maintenance, Zapier migration",
        cia_price_range="$1,500 - $8,000",
        addresses_processes=["manual_tasks", "data_entry", "reporting", "email_management"],
    ),

    ToolCategory(
        id="sops",
        name_es="SOPs y Procesos",
        name_en="SOPs & Processes",
        description_es="Documentar, estandarizar y ejecutar procesos operativos",
        description_en="Document, standardize, and execute operational processes",
        paid=Tool(
            name="Process Street",
            url="https://process.st",
            category="sops",
            is_oss=False,
            price_range="$25 - $100/user/mo",
            strengths=["Checklists + automación", "Integraciones", "Templates"],
            limitations=["Precio sube rápido con usuarios", "Overkill para equipos pequeños"],
            cia_rating=7.5,
            last_tested="2026-04-01",
            verdict_es="Bueno para equipos medianos con procesos complejos.",
            verdict_en="Good for mid-size teams with complex processes.",
        ),
        oss=Tool(
            name="Checklist.gg",
            url="https://checklist.gg",
            category="sops",
            is_oss=True,
            price_range="Free",
            strengths=["AI-powered", "Simple", "Gratuito"],
            limitations=["Menos features de automación", "Más básico"],
            cia_rating=6.5,
            last_tested="2026-04-01",
            verdict_es="Suficiente para empezar. Migrar a Process Street cuando escales.",
            verdict_en="Enough to start. Migrate to Process Street when you scale.",
        ),
        cia_service_es="Mapeo de procesos, creación de SOPs, implementación, training del equipo",
        cia_service_en="Process mapping, SOP creation, implementation, team training",
        cia_price_range="$2,000 - $6,000",
        addresses_processes=["project_handoff", "client_onboarding", "onboarding_flow"],
    ),

    ToolCategory(
        id="communication",
        name_es="Comunicación Interna",
        name_en="Internal Communication",
        description_es="Chat de equipo, canales, integración con herramientas de trabajo",
        description_en="Team chat, channels, integration with work tools",
        paid=Tool(
            name="Slack",
            url="https://slack.com",
            category="communication",
            is_oss=False,
            price_range="Free - $12.50/user/mo",
            strengths=["Estándar de la industria", "Miles de integraciones", "Workflow Builder"],
            limitations=["Free tier limitado en historial", "Puede fragmentar comunicación"],
            cia_rating=8.5,
            last_tested="2026-04-01",
            verdict_es="Si tu equipo ya lo usa, no lo cambies. Optimiza los workflows.",
            verdict_en="If your team already uses it, don't switch. Optimize the workflows.",
        ),
        oss=Tool(
            name="Mattermost",
            url="https://mattermost.com",
            category="communication",
            is_oss=True,
            price_range="Free (self-hosted)",
            strengths=["Open source", "Self-hosted", "Compliance friendly", "API completa"],
            limitations=["Menos integraciones nativas", "Requiere mantenimiento"],
            cia_rating=7.5,
            last_tested="2026-04-01",
            verdict_es="Perfecto para empresas que necesitan control total de sus datos.",
            verdict_en="Perfect for companies that need full data control.",
        ),
        cia_service_es="Setup, integraciones con CRM/ERP, bots custom, migración",
        cia_service_en="Setup, CRM/ERP integrations, custom bots, migration",
        cia_price_range="$1,000 - $5,000",
        addresses_processes=["internal_communication", "cross_department_handoffs"],
    ),

    ToolCategory(
        id="scheduling",
        name_es="Agendamiento",
        name_en="Scheduling",
        description_es="Reserva de citas, calendario de equipo, no-show management",
        description_en="Appointment booking, team calendar, no-show management",
        paid=Tool(
            name="Calendly",
            url="https://calendly.com",
            category="scheduling",
            is_oss=False,
            price_range="Free - $16/user/mo",
            strengths=["Ultra simple", "Integraciones", "Round-robin"],
            limitations=["Features avanzados solo en planes caros", "Branding limitado free"],
            cia_rating=8.0,
            last_tested="2026-04-01",
            verdict_es="Funciona. Pero Cal.com da lo mismo gratis.",
            verdict_en="It works. But Cal.com gives the same for free.",
        ),
        oss=Tool(
            name="Cal.com",
            url="https://cal.com",
            category="scheduling",
            is_oss=True,
            price_range="Free (self-hosted) / $15/mo cloud",
            strengths=["Open source", "Feature parity con Calendly", "Self-hosted", "API"],
            limitations=["UI ligeramente menos pulida", "Soporte community-driven"],
            cia_rating=8.5,
            last_tested="2026-04-01",
            verdict_es="Nuestra recomendación #1 para scheduling. CIA lo usa.",
            verdict_en="Our #1 recommendation for scheduling. CIA uses it.",
        ),
        cia_service_es="Setup, integración con CRM, workflows de confirmación, no-show recovery",
        cia_service_en="Setup, CRM integration, confirmation workflows, no-show recovery",
        cia_price_range="$800 - $3,000",
        addresses_processes=["scheduling", "appointment_scheduling", "no_show_management"],
    ),

    ToolCategory(
        id="email_marketing",
        name_es="Email Marketing",
        name_en="Email Marketing",
        description_es="Campañas, nurture, segmentación, automatización de email",
        description_en="Campaigns, nurture, segmentation, email automation",
        paid=Tool(
            name="MailerLite",
            url="https://mailerlite.com",
            category="email_marketing",
            is_oss=False,
            price_range="Free - $18/mo",
            strengths=["Free tier generoso (1K subs)", "UI excelente", "Automaciones"],
            limitations=["Menos features enterprise", "Segmentación básica en free"],
            cia_rating=8.0,
            last_tested="2026-04-01",
            verdict_es="Mejor relación calidad/precio. CIA lo usa para sus campañas.",
            verdict_en="Best value for money. CIA uses it for its campaigns.",
        ),
        oss=Tool(
            name="Listmonk",
            url="https://listmonk.app",
            category="email_marketing",
            is_oss=True,
            price_range="Free (self-hosted)",
            strengths=["Open source", "Rendimiento alto", "Sin límites de subs"],
            limitations=["Requiere SMTP propio", "UI más técnica", "Sin landing pages"],
            cia_rating=7.0,
            last_tested="2026-04-01",
            verdict_es="Para equipos técnicos con muchos subs. Ahorro masivo vs. MailChimp.",
            verdict_en="For tech teams with many subs. Massive savings vs. MailChimp.",
        ),
        cia_service_es="Estrategia de email, setup, templates, automaciones, migración",
        cia_service_en="Email strategy, setup, templates, automations, migration",
        cia_price_range="$1,000 - $5,000",
        addresses_processes=["email_nurture", "cart_recovery", "call_handling"],
    ),

    ToolCategory(
        id="analytics",
        name_es="Analytics y SEO",
        name_en="Analytics & SEO",
        description_es="Tráfico web, keywords, posicionamiento, métricas de negocio",
        description_en="Web traffic, keywords, rankings, business metrics",
        paid=Tool(
            name="Ahrefs",
            url="https://ahrefs.com",
            category="analytics",
            is_oss=False,
            price_range="$99 - $999/mo",
            strengths=["Base de datos masiva", "Backlinks", "Content explorer"],
            limitations=["Caro para PYMES", "Curva de aprendizaje"],
            cia_rating=9.0,
            last_tested="2026-04-01",
            verdict_es="El mejor para SEO serio. Si no lo necesitas, Plausible + Google Search Console bastan.",
            verdict_en="The best for serious SEO. If you don't need it, Plausible + Google Search Console are enough.",
        ),
        oss=Tool(
            name="Plausible Analytics",
            url="https://plausible.io",
            category="analytics",
            is_oss=True,
            price_range="Free (self-hosted) / €9/mo cloud",
            strengths=["Privacy-first", "Ultra ligero", "No cookies", "GDPR compliant"],
            limitations=["Solo analytics web, no SEO", "Menos profundidad"],
            cia_rating=8.0,
            last_tested="2026-04-01",
            verdict_es="Reemplaza Google Analytics con privacidad. Combinar con GSC para SEO.",
            verdict_en="Replaces Google Analytics with privacy. Combine with GSC for SEO.",
        ),
        cia_service_es="Setup de analytics stack, dashboards custom, tracking plan, SEO audit",
        cia_service_en="Analytics stack setup, custom dashboards, tracking plan, SEO audit",
        cia_price_range="$1,500 - $6,000",
        addresses_processes=["reporting", "customer_segmentation"],
    ),

    ToolCategory(
        id="accounting",
        name_es="Contabilidad",
        name_en="Accounting",
        description_es="Contabilidad, impuestos, reportes financieros, cashflow",
        description_en="Bookkeeping, taxes, financial reports, cashflow",
        paid=Tool(
            name="QuickBooks Online",
            url="https://quickbooks.intuit.com",
            category="accounting",
            is_oss=False,
            price_range="$30 - $200/mo",
            strengths=["Estándar LATAM/US", "Integraciones bancarias", "Payroll"],
            limitations=["UI anticuada", "Precio sube con features", "Soporte variable"],
            cia_rating=7.5,
            last_tested="2026-04-01",
            verdict_es="Funcional. Si tu contador ya lo usa, quédate.",
            verdict_en="Functional. If your accountant already uses it, stay.",
        ),
        oss=Tool(
            name="Akaunting",
            url="https://akaunting.com",
            category="accounting",
            is_oss=True,
            price_range="Free (self-hosted)",
            strengths=["Open source", "Multi-moneda", "App marketplace", "Self-hosted"],
            limitations=["Menos integraciones bancarias", "Comunidad más pequeña"],
            cia_rating=6.5,
            last_tested="2026-04-01",
            verdict_es="Viable para PYMES que quieren control total. Verificar compatibilidad fiscal local.",
            verdict_en="Viable for SMBs wanting full control. Verify local tax compatibility.",
        ),
        cia_service_es="Migración contable, integraciones con banco/ERP, automatización fiscal",
        cia_service_en="Accounting migration, bank/ERP integrations, tax automation",
        cia_price_range="$2,000 - $10,000",
        addresses_processes=["invoicing", "insurance_claims", "billing_cycle"],
    ),

    ToolCategory(
        id="contracts",
        name_es="Contratos y Firmas",
        name_en="Contracts & Signatures",
        description_es="Firmas digitales, gestión de contratos, templates legales",
        description_en="Digital signatures, contract management, legal templates",
        paid=Tool(
            name="DocuSign",
            url="https://docusign.com",
            category="contracts",
            is_oss=False,
            price_range="$10 - $40/user/mo",
            strengths=["Estándar legal global", "Integraciones enterprise", "eSignature"],
            limitations=["Caro para volumen bajo", "UI compleja para admin"],
            cia_rating=8.0,
            last_tested="2026-04-01",
            verdict_es="El estándar si necesitas validez legal internacional. Overkill para PYMES.",
            verdict_en="The standard if you need international legal validity. Overkill for SMBs.",
        ),
        oss=Tool(
            name="DocuSeal",
            url="https://docuseal.co",
            category="contracts",
            is_oss=True,
            price_range="Free (self-hosted) / $10/mo cloud",
            strengths=["Open source", "Self-hosted", "API completa", "Templates"],
            limitations=["Menos reconocido legalmente", "Comunidad joven"],
            cia_rating=7.5,
            last_tested="2026-04-01",
            verdict_es="Perfecto para contratos internos y PYMES. Verificar validez legal en tu jurisdicción.",
            verdict_en="Perfect for internal contracts and SMBs. Verify legal validity in your jurisdiction.",
        ),
        cia_service_es="Templates legales, workflow de aprobación, integración con CRM",
        cia_service_en="Legal templates, approval workflow, CRM integration",
        cia_price_range="$1,000 - $4,000",
        addresses_processes=["subcontractor_coordination", "client_onboarding"],
    ),
]


# ─── Registry ────────────────────────────────────────────

TOOLSTACK_BY_ID: dict[str, ToolCategory] = {t.id: t for t in TOOLSTACK}


def get_relevant_tools(processes: list[str]) -> list[ToolCategory]:
    """Return tools relevant to the given list of leak processes.

    Sorted by number of matching processes (most relevant first).
    """
    scored: list[tuple[int, ToolCategory]] = []
    for tool_cat in TOOLSTACK:
        match_count = len(set(processes) & set(tool_cat.addresses_processes))
        if match_count > 0:
            scored.append((match_count, tool_cat))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [tc for _, tc in scored]


def get_all_tools() -> list[ToolCategory]:
    """Return all 10 tool categories."""
    return list(TOOLSTACK)
