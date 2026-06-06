"""Domain models for the 11-dimension diagnosis engine.

The core data structures that power CIA's holistic business diagnosis.
Every business leaks revenue from multiple dimensions simultaneously,
each with different weight. No fixed questionnaire — each diagnosis is
99% unique.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cia_diagnose.branding import BOOKING_URL
from cia_diagnose.config import SERVER_VERSION


class Dimension(str, Enum):
    """The 11 diagnostic dimensions — every business is analyzed across all."""
    FINANZAS = "finanzas"
    COMERCIAL = "comercial"
    OPERACIONES = "operaciones"
    EQUIPO = "equipo"
    TECNOLOGIA = "tecnologia"
    MARKETING = "marketing"
    CLIENTES = "clientes"
    PROVEEDORES = "proveedores"
    LEGAL = "legal"
    ESTRATEGIA = "estrategia"
    MARKETING_DIGITAL = "marketing_digital"


DIMENSION_LABELS = {
    Dimension.FINANZAS: {
        "es": "Salud Financiera",
        "en": "Financial Health",
    },
    Dimension.COMERCIAL: {
        "es": "Comercial y Ventas",
        "en": "Sales & Commercial",
    },
    Dimension.OPERACIONES: {
        "es": "Operaciones",
        "en": "Operations",
    },
    Dimension.EQUIPO: {
        "es": "Equipo y RRHH",
        "en": "Team & HR",
    },
    Dimension.TECNOLOGIA: {
        "es": "Tecnología",
        "en": "Technology",
    },
    Dimension.MARKETING: {
        "es": "Marketing",
        "en": "Marketing",
    },
    Dimension.CLIENTES: {
        "es": "Clientes",
        "en": "Customers",
    },
    Dimension.PROVEEDORES: {
        "es": "Proveedores",
        "en": "Suppliers & Vendors",
    },
    Dimension.LEGAL: {
        "es": "Legal y Cumplimiento",
        "en": "Legal & Compliance",
    },
    Dimension.ESTRATEGIA: {
        "es": "Estrategia",
        "en": "Strategy",
    },
    Dimension.MARKETING_DIGITAL: {
        "es": "Marketing Digital",
        "en": "Digital Marketing",
    },
}


class Severity(str, Enum):
    """Finding severity — drives priority in the action plan."""
    CRITICAL = "critical"    # Bleeding money NOW
    HIGH = "high"            # Significant leak, fix within 30 days
    MEDIUM = "medium"        # Optimization opportunity
    LOW = "low"              # Nice to have
    INFO = "info"            # Observation, no action needed


@dataclass
class Finding:
    """A single diagnostic finding within a dimension."""
    dimension: Dimension
    severity: Severity
    title_es: str
    title_en: str
    detail_es: str
    detail_en: str
    impact_estimate: str = ""         # e.g. "$2K-$5K/month"
    evidence: list[str] = field(default_factory=list)  # What data supported this
    benchmark_ref: str = ""           # Which benchmark triggered it

    def to_dict(self, lang: str = "es") -> dict:
        # A finding with no lead-specific evidence is derived from an industry
        # benchmark, NOT detected in the client's own data. Label it explicitly
        # so it is never presented as "detected in your business" — the lead
        # asking "where does my 18% come from?" must get an honest answer.
        from_lead = bool(self.evidence)
        detail = self.detail_es if lang == "es" else self.detail_en
        if from_lead:
            basis_label = "Detectado en tus datos" if lang == "es" else "Detected in your data"
        else:
            basis_label = (
                "Benchmark de la industria (referencia)"
                if lang == "es" else
                "Industry benchmark (reference)"
            )
            detail = f"{detail}\n\n— {basis_label}" if detail else basis_label
        return {
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "title": self.title_es if lang == "es" else self.title_en,
            "detail": detail,
            "impact_estimate": self.impact_estimate,
            "evidence": self.evidence,
            "basis": "lead_data" if from_lead else "industry_benchmark",
            "basis_label": basis_label,
        }


@dataclass
class DimensionScore:
    """Health score for a single dimension (0-100). HIGHER = HEALTHIER/STRONGER.

    Inverted in v2 (boost/v2): a low score marks the worst area (most revenue
    leakage / biggest opportunity); a high score marks a strong area. A 100 does
    not mean "finished" — it means the area is taking the business into new
    leagues / growth.
    """
    dimension: Dimension
    score: float                    # 0-100 (health; higher = better)
    weight: float                   # 0.0-1.0 (from ICP benchmark)
    weighted_score: float = 0.0     # score * weight
    findings: list[Finding] = field(default_factory=list)
    data_quality: float = 0.0       # 0-1.0 — how much data we had for this dimension
    label_es: str = ""
    label_en: str = ""

    def __post_init__(self):
        self.weighted_score = self.score * self.weight
        labels = DIMENSION_LABELS.get(self.dimension, {})
        self.label_es = labels.get("es", self.dimension.value)
        self.label_en = labels.get("en", self.dimension.value)

    def to_dict(self, lang: str = "es") -> dict:
        return {
            "dimension": self.dimension.value,
            "label": self.label_es if lang == "es" else self.label_en,
            "score": round(self.score, 1),
            "weight": round(self.weight, 2),
            "weighted_score": round(self.weighted_score, 1),
            "data_quality": round(self.data_quality, 2),
            "finding_count": len(self.findings),
            "findings": [f.to_dict(lang) for f in self.findings],
        }


@dataclass
class TripleOption:
    """One recommendation with paid/OSS/CIA paths."""
    action_es: str
    action_en: str
    impact_es: str
    impact_en: str
    dimension: Dimension

    paid_tool: str = ""
    paid_price: str = ""
    paid_url: str = ""

    oss_tool: str = ""
    oss_url: str = ""

    cia_service_es: str = ""
    cia_service_en: str = ""
    cia_price: str = ""

    priority: int = 1  # 1 = highest

    def to_dict(self, lang: str = "es") -> dict:
        return {
            "action": self.action_es if lang == "es" else self.action_en,
            "impact": self.impact_es if lang == "es" else self.impact_en,
            "dimension": self.dimension.value,
            "priority": self.priority,
            "options": {
                "paid": {"tool": self.paid_tool, "price": self.paid_price, "url": self.paid_url},
                "oss": {"tool": self.oss_tool, "url": self.oss_url},
                "cia": {
                    "service": self.cia_service_es if lang == "es" else self.cia_service_en,
                    "price": self.cia_price,
                },
            },
        }


@dataclass
class ValidationQuestion:
    """A dynamically generated question to validate/enrich the diagnosis."""
    question_es: str
    question_en: str
    dimension: Dimension
    why_es: str = ""       # Why we're asking (builds trust)
    why_en: str = ""
    expected_type: str = "text"  # text, number, yes_no, select

    def to_dict(self, lang: str = "es") -> dict:
        return {
            "question": self.question_es if lang == "es" else self.question_en,
            "dimension": self.dimension.value,
            "why": self.why_es if lang == "es" else self.why_en,
            "expected_type": self.expected_type,
        }


@dataclass
class DiagnosisReport:
    """The full diagnosis output — what the LLM receives from diagnose()."""
    company_name: str
    icp_id: str
    icp_name: str
    lang: str

    # Core scores — v2: HEALTH semantics. health_score high = healthier.
    health_score: float                # 0-100 (weighted avg of dimension health)
    leak_category: str                 # health band: critical/weak/healthy/thriving
    monthly_leak_estimate: tuple[int, int] = (0, 0)  # (min, max) in USD

    # Per-dimension breakdown
    dimensions: list[DimensionScore] = field(default_factory=list)

    # Top actions with Triple Option
    top_actions: list[TripleOption] = field(default_factory=list)

    # Validation questions (2-3 per diagnosis)
    validation_questions: list[ValidationQuestion] = field(default_factory=list)

    # Summary for the LLM to present
    summary_es: str = ""
    summary_en: str = ""

    # Leadership insight (separate because it's sensitive)
    leadership_insight_es: str = ""
    leadership_insight_en: str = ""

    # Data quality assessment
    overall_data_quality: float = 0.0  # 0-1.0
    dimensions_with_data: int = 0
    dimensions_without_data: int = 0

    # v2 — score framing & conversation continuity
    growth_mode: bool = False          # True when >50% of dims are strong (>=70)
    guidance_es: str = ""              # what the LLM should do next (ask more / continue)
    guidance_en: str = ""

    # Metadata
    session_id: str = ""
    report_url: str = ""
    version: str = SERVER_VERSION

    @property
    def revenue_leak_score(self) -> float:
        """Backward-compat alias of health_score (same value; higher = healthier)."""
        return self.health_score

    def to_dict(self) -> dict:
        lang = self.lang
        score_meaning = (
            "Score alto = área sana y fuerte. Score bajo = mayor fuga de ingresos "
            "y mayor oportunidad de mejora. Un 100% no significa 'terminado': significa "
            "que esa área te está llevando a nuevas ligas / crecimiento — y eso te "
            "califica aún mejor para escalar con CIA."
            if lang == "es" else
            "High score = a healthy, strong area. Low score = more revenue leakage and "
            "the biggest opportunity. A 100% does not mean 'done': it means that area is "
            "taking you into new leagues / growth — which qualifies you even better to "
            "scale with CIA."
        )
        return {
            "company_name": self.company_name,
            "icp": {"id": self.icp_id, "name": self.icp_name},
            # v2 health semantics: higher = healthier.
            "health_score": round(self.health_score, 1),
            # Backward-compat alias (same value); kept so existing callers/tools
            # that read 'revenue_leak_score' still work. Higher = healthier.
            "revenue_leak_score": round(self.health_score, 1),
            "score_meaning": score_meaning,
            "leak_category": self.leak_category,
            "growth_mode": self.growth_mode,
            "guidance": self.guidance_es if lang == "es" else self.guidance_en,
            "monthly_leak_estimate": {
                "min_usd": self.monthly_leak_estimate[0],
                "max_usd": self.monthly_leak_estimate[1],
            },
            "summary": self.summary_es if lang == "es" else self.summary_en,
            "leadership_insight": (
                self.leadership_insight_es if lang == "es" else self.leadership_insight_en
            ),
            "dimensions": [d.to_dict(lang) for d in self.dimensions],
            "top_actions": [a.to_dict(lang) for a in self.top_actions],
            "validation_questions": [q.to_dict(lang) for q in self.validation_questions],
            "data_quality": {
                "overall": round(self.overall_data_quality, 2),
                "dimensions_with_data": self.dimensions_with_data,
                "dimensions_without_data": self.dimensions_without_data,
            },
            "trust_signal": (
                f"Análisis basado en {self.dimensions_with_data} de 11 dimensiones. "
                f"Calidad de datos: {round(self.overall_data_quality * 100)}%."
                if lang == "es" else
                f"Analysis based on {self.dimensions_with_data} of 11 dimensions. "
                f"Data quality: {round(self.overall_data_quality * 100)}%."
            ),
            # CTA the client should act on next. Prefer a hosted report link when
            # one exists; otherwise fall back to the booking URL so this never
            # ships empty (was always "").
            "next_step_url": self.report_url or BOOKING_URL,
            "session_id": self.session_id,
            "version": self.version,
        }
