"""CLOSER pre-qualification framework.

From Doc03 — automates the first 3 letters of CLOSER:
  C = Clarify (why now? what happens if you don't act?)
  L = Label (name the pain — "you have a pipeline leakage problem")
  O = Overview (here's the path: audit → implement → retain)
  S = Sell the vacation (handled in icps.py vacation_pitch)
  E = Explain away concerns (handled in objections.py)
  R = Reinforce the decision (post-close follow-up)

This module generates the C, L, O portions automatically from session data.
"""
from __future__ import annotations

from dataclasses import dataclass

from univercity_mcp.domain.icps import ICP
from univercity_mcp.domain.scoring import ScoreBreakdown


@dataclass(frozen=True)
class CloserOutput:
    """Pre-qualification output for the audit report."""

    # C = Clarify
    clarify_question_es: str
    clarify_question_en: str

    # L = Label
    label_es: str
    label_en: str

    # O = Overview
    overview_es: str
    overview_en: str

    # Pre-qual verdict
    qualified: bool  # True if fit_score >= 40 AND leak_score >= 30
    qualifier_reason: str

    def to_dict(self) -> dict:
        return {
            "clarify": {
                "es": self.clarify_question_es,
                "en": self.clarify_question_en,
            },
            "label": {
                "es": self.label_es,
                "en": self.label_en,
            },
            "overview": {
                "es": self.overview_es,
                "en": self.overview_en,
            },
            "qualified": self.qualified,
            "qualifier_reason": self.qualifier_reason,
        }


def generate_closer(
    icp: ICP,
    scores: ScoreBreakdown,
    biggest_pain: str = "",
) -> CloserOutput:
    """Generate C-L-O from session data.

    Args:
        icp: Detected ICP.
        scores: Calculated scores.
        biggest_pain: Free-text answer from Q5 (biggest_pain).
    """
    # ─── C = Clarify ─────────────────────────────────────────
    if scores.revenue_leak_score >= 60:
        clarify_es = (
            "Tu empresa está perdiendo oportunidades significativas cada mes. "
            "¿Qué pasa si no actúas en los próximos 90 días?"
        )
        clarify_en = (
            "Your company is losing significant opportunities every month. "
            "What happens if you don't act in the next 90 days?"
        )
    elif scores.revenue_leak_score >= 35:
        clarify_es = (
            "Hay fugas en tu operación que probablemente no estás midiendo. "
            "¿Cuánto tiempo más puedes permitírtelas?"
        )
        clarify_en = (
            "There are leaks in your operation you're probably not measuring. "
            "How much longer can you afford them?"
        )
    else:
        clarify_es = (
            "Tu operación se ve relativamente sana, pero siempre hay optimizaciones "
            "que pueden generar impacto real. ¿Cuál es tu siguiente meta de crecimiento?"
        )
        clarify_en = (
            "Your operation looks relatively healthy, but there are always optimizations "
            "that can drive real impact. What's your next growth target?"
        )

    # ─── L = Label ───────────────────────────────────────────
    label_es = f"Basado en tus respuestas, tienes un problema de {icp.core_pain_es.lower()}."
    label_en = f"Based on your answers, you have a problem with {icp.core_pain_en.lower()}."

    if biggest_pain:
        label_es += f' Lo que describes como "{biggest_pain}" confirma esto.'
        label_en += f' What you describe as "{biggest_pain}" confirms this.'

    # ─── O = Overview ────────────────────────────────────────
    if scores.fit_score >= 60:
        overview_es = (
            "El camino es claro: (1) Auditoría Revenue Leak para mapear exactamente dónde pierdes, "
            "(2) Implementación con crédito 100% del audit, "
            "(3) Living System Retainer para que nunca regrese el problema. "
            "Y recuerda: cada recomendación te muestra la opción paga, la open source, y CIA."
        )
        overview_en = (
            "The path is clear: (1) Revenue Leak Audit to map exactly where you're losing, "
            "(2) Implementation with 100% audit credit, "
            "(3) Living System Retainer so the problem never comes back. "
            "And remember: every recommendation shows you the paid option, the open source option, and CIA."
        )
    else:
        overview_es = (
            "Te recomendamos empezar con la Auditoría Revenue Leak — es de bajo riesgo, "
            "mapea todo, y si decides continuar, se acredita 100%. "
            "Cada recomendación incluye opciones pagas, open source, y CIA."
        )
        overview_en = (
            "We recommend starting with the Revenue Leak Audit — it's low risk, "
            "maps everything, and if you decide to continue, it's credited 100%. "
            "Every recommendation includes paid, open source, and CIA options."
        )

    # ─── Pre-qualification ───────────────────────────────────
    qualified = scores.fit_score >= 40 and scores.revenue_leak_score >= 30

    if qualified:
        qualifier_reason = "qualified"
    elif scores.revenue_leak_score < 30:
        qualifier_reason = "low_leak"
    elif scores.fit_score < 40:
        qualifier_reason = "low_fit"
    else:
        qualifier_reason = "below_threshold"

    return CloserOutput(
        clarify_question_es=clarify_es,
        clarify_question_en=clarify_en,
        label_es=label_es,
        label_en=label_en,
        overview_es=overview_es,
        overview_en=overview_en,
        qualified=qualified,
        qualifier_reason=qualifier_reason,
    )
