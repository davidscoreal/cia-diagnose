"""Value Ladder — maps scores to recommended CIA services.

The ladder follows the 3-tier sandwich pricing model:
  1. Anchor high (Bespoke / full implementation)
  2. Present sweet spot (the service CIA WANTS them to buy)
  3. Show entry point (audit / quick win)

Every recommendation includes the 100% credit bridge:
  "If you proceed within 30 days, audit fee is credited 100%."
"""
from __future__ import annotations

from dataclasses import dataclass, field

from univercity_mcp.domain.icps import ICP, ServicePricing, Tier
from univercity_mcp.domain.scoring import ScoreBreakdown


@dataclass(frozen=True)
class Recommendation:
    """A single service recommendation with positioning."""
    service: ServicePricing
    position: str  # "anchor" | "sweet_spot" | "entry"
    reason_es: str
    reason_en: str
    credit_bridge: bool = False  # "audit credited 100% if proceed"


@dataclass(frozen=True)
class ValueLadderResult:
    """Complete value ladder for a session."""
    recommendations: list[Recommendation]
    credit_bridge_es: str
    credit_bridge_en: str
    founders_discount_active: bool = False
    founders_discount_pct: float = 0.0

    def to_dict(self) -> dict:
        return {
            "recommendations": [
                {
                    "service": r.service.name,
                    "price_range": f"${r.service.price_min:,} - ${r.service.price_max:,}",
                    "duration": r.service.duration,
                    "position": r.position,
                    "reason_es": r.reason_es,
                    "reason_en": r.reason_en,
                    "credit_bridge": r.credit_bridge,
                }
                for r in self.recommendations
            ],
            "credit_bridge_es": self.credit_bridge_es,
            "credit_bridge_en": self.credit_bridge_en,
            "founders_discount_active": self.founders_discount_active,
            "founders_discount_pct": self.founders_discount_pct,
        }


# ─── Standard credit bridge text ─────────────────────────

_CREDIT_BRIDGE_ES = (
    "Si decides proceder dentro de 30 días, el costo de la auditoría "
    "se acredita 100% al siguiente servicio. En la práctica, la auditoría fue gratis."
)
_CREDIT_BRIDGE_EN = (
    "If you proceed within 30 days, the audit cost is credited 100% to the "
    "next service. In practice, the audit was free."
)


def build_value_ladder(
    icp: ICP,
    scores: ScoreBreakdown,
    founders_active: bool = False,
    founders_discount: float = 0.35,
) -> ValueLadderResult:
    """Build the 3-tier sandwich recommendation from ICP services and scores.

    Strategy:
    - High leak + high fit → push toward Predictable Revenue / Agentic Strategy
    - High leak + low fit → push toward Revenue Leak Audit (entry)
    - Low leak + high fit → push toward Living System Retainer (ongoing)
    - Low leak + low fit → still show audit as low-risk entry
    """
    services = icp.services
    if not services:
        # Fallback: use generic services
        from univercity_mcp.domain.icps import GENERIC
        services = GENERIC.services

    recommendations: list[Recommendation] = []

    # Sort services by price_max descending to find anchor
    by_price = sorted(services, key=lambda s: s.price_max, reverse=True)

    # Find each tier
    anchor_svc = by_price[0]
    entry_svc = by_price[-1]
    sweet_spot_svc = by_price[len(by_price) // 2] if len(by_price) > 2 else anchor_svc

    # Determine emphasis based on scores
    if scores.revenue_leak_score >= 60 and scores.fit_score >= 60:
        # High leak, high fit — push sweet spot hard
        sweet_reason_es = "Tu Revenue Leak Score es alto y tu perfil encaja perfecto. Este servicio resuelve el problema central."
        sweet_reason_en = "Your Revenue Leak Score is high and your profile is a perfect fit. This service solves the core problem."
        anchor_reason_es = "Para resultados máximos: implementación completa de extremo a extremo."
        anchor_reason_en = "For maximum results: complete end-to-end implementation."
        entry_reason_es = "Si prefieres empezar despacio: auditoría con crédito 100%."
        entry_reason_en = "If you prefer to start slow: audit with 100% credit."
    elif scores.revenue_leak_score >= 60:
        # High leak, moderate/low fit — entry point
        sweet_reason_es = "Tienes fugas significativas pero empezar con una auditoría te da claridad antes de invertir más."
        sweet_reason_en = "You have significant leaks but starting with an audit gives you clarity before investing more."
        anchor_reason_es = "Cuando estés listo para la implementación completa."
        anchor_reason_en = "When you're ready for full implementation."
        entry_reason_es = "Recomendado: empieza aquí. Mapea exactamente dónde pierdes y cuánto cuesta."
        entry_reason_en = "Recommended: start here. Map exactly where you're losing and how much it costs."
    elif scores.fit_score >= 60:
        # Low leak, high fit — retainer/ongoing
        sweet_reason_es = "Tu operación está relativamente sana. Un retainer mantiene la optimización continua."
        sweet_reason_en = "Your operation is relatively healthy. A retainer keeps continuous optimization going."
        anchor_reason_es = "Si quieres dar un salto grande: implementación estratégica completa."
        anchor_reason_en = "If you want to make a big leap: full strategic implementation."
        entry_reason_es = "Auditoría para encontrar las oportunidades de mejora ocultas."
        entry_reason_en = "Audit to find hidden improvement opportunities."
    else:
        # Low everything — gentle entry
        sweet_reason_es = "Te recomendamos empezar con una auditoría para entender el terreno."
        sweet_reason_en = "We recommend starting with an audit to understand the landscape."
        anchor_reason_es = "Cuando estés listo para transformar tu operación."
        anchor_reason_en = "When you're ready to transform your operation."
        entry_reason_es = "Paso 1: mapa claro de oportunidades con crédito 100%."
        entry_reason_en = "Step 1: clear opportunity map with 100% credit."

    # Build the sandwich: anchor (high), sweet spot (mid), entry (low)
    if anchor_svc != sweet_spot_svc:
        recommendations.append(Recommendation(
            service=anchor_svc,
            position="anchor",
            reason_es=anchor_reason_es,
            reason_en=anchor_reason_en,
        ))

    recommendations.append(Recommendation(
        service=sweet_spot_svc,
        position="sweet_spot",
        reason_es=sweet_reason_es,
        reason_en=sweet_reason_en,
    ))

    if entry_svc != sweet_spot_svc:
        recommendations.append(Recommendation(
            service=entry_svc,
            position="entry",
            reason_es=entry_reason_es,
            reason_en=entry_reason_en,
            credit_bridge=True,
        ))

    return ValueLadderResult(
        recommendations=recommendations,
        credit_bridge_es=_CREDIT_BRIDGE_ES,
        credit_bridge_en=_CREDIT_BRIDGE_EN,
        founders_discount_active=founders_active,
        founders_discount_pct=founders_discount,
    )
