"""Single source of truth for CIA branding — links, contact, taglines, assets.

Every public-facing URL, email, and signature lives here. Change once, applies
everywhere (tool outputs, HTML report, webhook, README generation).
"""
from __future__ import annotations

from pathlib import Path

# ─── Identity ────────────────────────────────────────────────────────
COMPANY_NAME = "C.I.A — Consultoría de Inteligencia Aplicada"
COMPANY_SHORT = "CIA"

# ─── Canonical links (verified with David 2026-06-02) ────────────────
WEBSITE = "https://www.univercityaiconsult.tech/"
BOOKING_URL = "https://cal.com/david-cia/diagnostico-ai"
CONTACT_EMAIL = "steban@univercityaiconsult.tech"
CEO_NAME = "David Lopez"

# ─── Brand colors (from univercityaiconsult.tech) ────────────────────
COLOR_PURPLE = "#7D34F4"   # primary
COLOR_DARK = "#080808"     # background
COLOR_ORANGE = "#F97316"   # accent / warning
COLOR_GREEN = "#22C55E"    # accent / positive

# ─── Brand assets ────────────────────────────────────────────────────
# When pip-installed, hatch ships brand/ inside the package (cia_diagnose/brand).
# When running from the source tree, fall back to the repo-root brand/.
_PKG_BRAND = Path(__file__).resolve().parent / "brand"
_REPO_BRAND = Path(__file__).resolve().parent.parent.parent / "brand"
_BRAND_DIR = _PKG_BRAND if _PKG_BRAND.exists() else _REPO_BRAND
MONOGRAM_LIGHT = _BRAND_DIR / "cia-monogram-light.png"  # white, for dark bg
MONOGRAM_DARK = _BRAND_DIR / "cia-monogram-dark.png"    # black, for light bg
WORDMARK = _BRAND_DIR / "cia-wordmark.png"              # silver gothic

# ─── Taglines ────────────────────────────────────────────────────────
TAGLINE_ES = "Inteligencia artificial aplicada a negocios reales. Desde América Latina para el mundo."
TAGLINE_EN = "Applied artificial intelligence for real businesses. From Latin America to the world."


def header_line(lang: str = "es") -> str:
    """Signature line shown at the TOP of a diagnosis."""
    if lang == "en":
        return f"Diagnosis by {COMPANY_NAME} | {WEBSITE}"
    return f"Diagnóstico por {COMPANY_NAME} | {WEBSITE}"


def booking_cta(lang: str = "es") -> str:
    """Call-to-action shown after the Revenue Leak Score."""
    if lang == "en":
        return (
            f"Want to review this with a consultant? Book a free 30 min: "
            f"{BOOKING_URL} | {CONTACT_EMAIL}"
        )
    return (
        f"¿Quieres revisar esto con un consultor? Agenda 30 min gratis: "
        f"{BOOKING_URL} | {CONTACT_EMAIL}"
    )


def closing_line(lang: str = "es") -> str:
    """Professional sign-off at the END of a diagnosis."""
    if lang == "en":
        return (
            f"Diagnosis courtesy of {COMPANY_SHORT}. If you see opportunities, "
            f"book with no commitment: {BOOKING_URL}"
        )
    return (
        f"Diagnóstico cortesía de {COMPANY_SHORT}. Si ves oportunidades, "
        f"agenda sin compromiso: {BOOKING_URL}"
    )


def signature(lang: str = "es") -> dict[str, str]:
    """Full branding block embedded in tool outputs."""
    return {
        "header": header_line(lang),
        "booking_cta": booking_cta(lang),
        "closing": closing_line(lang),
        "website": WEBSITE,
        "booking_url": BOOKING_URL,
        "contact_email": CONTACT_EMAIL,
    }
