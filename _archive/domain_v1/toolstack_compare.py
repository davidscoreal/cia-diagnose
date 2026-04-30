"""Triple Option comparison formatter.

Generates the comparison table that appears in every audit report:
for each relevant tool category, shows Paid vs OSS vs CIA side by side.

This is the heart of CIA's differentiator — radical transparency.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from univercity_mcp.domain.toolstack import ToolCategory, get_relevant_tools


@dataclass(frozen=True)
class TripleOptionRow:
    """One row in the comparison table."""
    category_id: str
    category_name_es: str
    category_name_en: str

    # Paid column
    paid_name: str
    paid_price: str
    paid_rating: float
    paid_verdict_es: str
    paid_verdict_en: str

    # OSS column
    oss_name: str
    oss_price: str
    oss_rating: float
    oss_verdict_es: str
    oss_verdict_en: str

    # CIA column
    cia_service_es: str
    cia_service_en: str
    cia_price: str

    # Meta
    relevance_score: int = 0  # how many leak processes this addresses


@dataclass(frozen=True)
class TripleOptionTable:
    """Complete comparison table for the report."""
    rows: list[TripleOptionRow]
    total_paid_estimate: str
    total_oss_estimate: str
    total_cia_estimate: str
    summary_es: str
    summary_en: str

    def to_dict(self) -> dict:
        return {
            "rows": [
                {
                    "category": r.category_id,
                    "category_name_es": r.category_name_es,
                    "category_name_en": r.category_name_en,
                    "paid": {
                        "name": r.paid_name,
                        "price": r.paid_price,
                        "rating": r.paid_rating,
                        "verdict_es": r.paid_verdict_es,
                        "verdict_en": r.paid_verdict_en,
                    },
                    "oss": {
                        "name": r.oss_name,
                        "price": r.oss_price,
                        "rating": r.oss_rating,
                        "verdict_es": r.oss_verdict_es,
                        "verdict_en": r.oss_verdict_en,
                    },
                    "cia": {
                        "service_es": r.cia_service_es,
                        "service_en": r.cia_service_en,
                        "price": r.cia_price,
                    },
                }
                for r in self.rows
            ],
            "totals": {
                "paid": self.total_paid_estimate,
                "oss": self.total_oss_estimate,
                "cia": self.total_cia_estimate,
            },
            "summary_es": self.summary_es,
            "summary_en": self.summary_en,
        }


def build_comparison_table(
    leak_processes: list[str],
    max_rows: int = 5,
) -> TripleOptionTable:
    """Build the Triple Option comparison table for relevant tools.

    Args:
        leak_processes: List of process IDs from the ICP's common_leak_processes
                        + any detected from answers.
        max_rows: Maximum number of tool categories to show (top N by relevance).

    Returns:
        TripleOptionTable ready for report rendering.
    """
    relevant = get_relevant_tools(leak_processes)[:max_rows]

    if not relevant:
        # Fallback: show top 3 most universal tools
        from univercity_mcp.domain.toolstack import TOOLSTACK
        relevant = TOOLSTACK[:3]

    rows: list[TripleOptionRow] = []
    for tc in relevant:
        match_count = len(set(leak_processes) & set(tc.addresses_processes))
        rows.append(TripleOptionRow(
            category_id=tc.id,
            category_name_es=tc.name_es,
            category_name_en=tc.name_en,
            paid_name=tc.paid.name,
            paid_price=tc.paid.price_range,
            paid_rating=tc.paid.cia_rating,
            paid_verdict_es=tc.paid.verdict_es,
            paid_verdict_en=tc.paid.verdict_en,
            oss_name=tc.oss.name,
            oss_price=tc.oss.price_range,
            oss_rating=tc.oss.cia_rating,
            oss_verdict_es=tc.oss.verdict_es,
            oss_verdict_en=tc.oss.verdict_en,
            cia_service_es=tc.cia_service_es,
            cia_service_en=tc.cia_service_en,
            cia_price=tc.cia_price_range,
            relevance_score=match_count,
        ))

    # Sort by relevance
    rows.sort(key=lambda r: r.relevance_score, reverse=True)

    # Estimate totals (rough)
    total_paid = "Varies by plan"
    total_oss = "$0 (self-hosted)"
    total_cia = f"${sum(_parse_min_price(tc.cia_price_range) for tc in relevant):,} - ${sum(_parse_max_price(tc.cia_price_range) for tc in relevant):,}"

    n = len(rows)
    summary_es = (
        f"Analizamos {n} categorías de herramientas relevantes para tu operación. "
        f"Cada una muestra 3 opciones: la mejor herramienta paga del mercado, "
        f"la mejor alternativa open source (probada por CIA), y nuestro servicio "
        f"de implementación personalizada. Tú decides qué camino tomar."
    )
    summary_en = (
        f"We analyzed {n} tool categories relevant to your operation. "
        f"Each shows 3 options: the best paid tool on the market, "
        f"the best open source alternative (tested by CIA), and our "
        f"custom implementation service. You decide which path to take."
    )

    return TripleOptionTable(
        rows=rows,
        total_paid_estimate=total_paid,
        total_oss_estimate=total_oss,
        total_cia_estimate=total_cia,
        summary_es=summary_es,
        summary_en=summary_en,
    )


def _parse_min_price(price_range: str) -> int:
    """Extract minimum price from a range like '$1,000 - $5,000'."""
    try:
        part = price_range.split("-")[0].strip()
        return int(part.replace("$", "").replace(",", "").strip())
    except (ValueError, IndexError):
        return 0


def _parse_max_price(price_range: str) -> int:
    """Extract maximum price from a range like '$1,000 - $5,000'."""
    try:
        parts = price_range.split("-")
        part = parts[-1].strip()
        return int(part.replace("$", "").replace(",", "").strip())
    except (ValueError, IndexError):
        return 0
