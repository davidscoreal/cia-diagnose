"""Basic i18n for ES/EN — static strings used across the system.

For v0.2, strings cover the single-tool diagnosis flow.
Post-Summit: proper i18n framework.
"""
from __future__ import annotations

STRINGS: dict[str, dict[str, str]] = {
    # --- Diagnosis flow (v0.2) ------------------------------------
    "diagnosis_started": {
        "es": "Diagnóstico de negocio iniciado. Analizando dimensiones...",
        "en": "Business diagnosis started. Analyzing dimensions...",
    },
    "diagnosis_complete": {
        "es": "Diagnóstico completado. Revisa tu Revenue Leak Score y las recomendaciones.",
        "en": "Diagnosis complete. Review your Revenue Leak Score and recommendations.",
    },
    "rate_limited": {
        "es": "Has alcanzado el límite de diagnósticos gratuitos por hoy. Regístrate para más.",
        "en": "You've reached the free diagnosis limit for today. Register for more.",
    },

    # --- Scores ---------------------------------------------------
    "leak_critical": {
        "es": "Tu empresa tiene fugas de revenue significativas que necesitan atención urgente.",
        "en": "Your company has significant revenue leaks that need urgent attention.",
    },
    "leak_high": {
        "es": "Hay oportunidades claras de mejora en tu operación.",
        "en": "There are clear improvement opportunities in your operation.",
    },
    "leak_medium": {
        "es": "Tu operación tiene áreas de optimización que podrían generar ahorro.",
        "en": "Your operation has optimization areas that could generate savings.",
    },
    "leak_low": {
        "es": "Tu operación está relativamente sana. Busquemos optimizaciones de alto impacto.",
        "en": "Your operation is relatively healthy. Let's find high-impact optimizations.",
    },

    # --- CTA ------------------------------------------------------
    "book_cta": {
        "es": "¿Quieres agendar una llamada de 15 min para revisar tu diagnóstico?",
        "en": "Want to schedule a 15-min call to review your diagnosis?",
    },
    "share_cta": {
        "es": "¿Quieres recibir el diagnóstico completo por email?",
        "en": "Want to receive the complete diagnosis by email?",
    },
    "credit_bridge": {
        "es": "Si decides proceder dentro de 30 días, el costo del diagnóstico se acredita 100%.",
        "en": "If you proceed within 30 days, the diagnosis cost is credited 100%.",
    },

    # --- Triple Option --------------------------------------------
    "triple_option_intro": {
        "es": "Cada recomendación muestra 3 opciones: la mejor herramienta paga, la mejor open source, y el servicio CIA.",
        "en": "Each recommendation shows 3 options: the best paid tool, the best open source, and the CIA service.",
    },

    # --- Errors ---------------------------------------------------
    "session_not_found": {
        "es": "Sesión no encontrada. Inicia un nuevo diagnóstico.",
        "en": "Session not found. Start a new diagnosis.",
    },
    "input_error": {
        "es": "Datos insuficientes. Proporciona al menos el nombre de la empresa.",
        "en": "Insufficient data. Provide at least the company name.",
    },
}


def t(key: str, lang: str = "es") -> str:
    """Get translated string. Falls back to ES if key/lang not found."""
    entry = STRINGS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("es", key))
