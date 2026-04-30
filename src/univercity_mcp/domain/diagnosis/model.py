"""Domain models for the 8-dimension diagnosis engine.

The core data structures that power CIA's holistic business diagnosis.
Every business leaks revenue from multiple dimensions simultaneously,
each with different weight. No fixed questionnaire — each diagnosis is
99% unique.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Dimension(str, Enum):
    """The 8 diagnostic dimensions — every business is analyzed across all."""
    DIGITAL = "digital"
    OPERATIONS = "operations"
    SUPPLY_CHAIN = "supply_chain"
    TALENT = "talent"
    FINANCIAL = "financial"
    LEADERSHIP = "leadership"
    MARKET = "market"
    REGULATORY = "regulatory"


DIMENSION_LABELS = {
    Dimension.DIGITAL: {
        "es": "Infraestructura Digital",
        "en": "Digital Infrastructure",
    },
    Dimension.OPERATIONS: {
        "es": "Operaciones Físicas",
        "en": "Physical Operations",
    },
    Dimension.SUPPLY_CHAIN: {
        "es": "Cadena de Suministro",
        "en": "Supply Chain & Vendors",
    },
    Dimension.TALENT: {
        "es": "Talento y Capital Humano",
        "en": "Talent & Human Capital",
    },
    Dimension.FINANCIAL: {
        "es": "Salud Financiera",
        "en": "Financial Health",
    },
    Dimension.LEADERSHIP: {
        "es": "Liderazgo y Psicología Decisional",
        "en": "Leadership & Decision Psychology",
    },
    Dimension.MARKET: {
        "es": "Posición de Mercado",
        "en": "Market & Competitive Position",
    },
    Dimension.REGULATORY: {
        "es": "Regulatorio y Cumplimiento",
        "en": "Regulatory & Compliance",
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
        return {
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "title": self.title_es if lang == "es" else self.title_en,
            "detail": self.detail_es if lang == "es" else self.detail_en,
            "impact_estimate": self.impact_estimate,
            "evidence": self.evidence,
        }


@dataclass
class DimensionScore:
    """Score for a single dimension (0-100). Higher = more leakage."""
    dimension: Dimension
    score: float                    # 0-100
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

    # Core scores
    revenue_leak_score: float          # 0-100 (weighted avg of dimensions)
    leak_category: str                 # low/medium/high/critical
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

    # Metadata
    session_id: str = ""
    report_url: str = ""
    version: str = "0.2.0"

    def to_dict(self) -> dict:
        lang = self.lang
        return {
            "company_name": self.company_name,
            "icp": {"id": self.icp_id, "name": self.icp_name},
            "revenue_leak_score": round(self.revenue_leak_score, 1),
            "leak_category": self.leak_category,
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
                f"Análisis basado en {self.dimensions_with_data} de 8 dimensiones. "
                f"Calidad de datos: {round(self.overall_data_quality * 100)}%."
                if lang == "es" else
                f"Analysis based on {self.dimensions_with_data} of 8 dimensions. "
                f"Data quality: {round(self.overall_data_quality * 100)}%."
            ),
            "next_step_url": self.report_url,
            "session_id": self.session_id,
            "version": self.version,
        }
