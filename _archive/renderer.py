"""Report renderer — Markdown + optional PDF.

Generates the full audit report from session data using Jinja2 templates.
Supports ES/EN. PDF via weasyprint (optional dependency).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from univercity_mcp.domain.icps import ICP
from univercity_mcp.storage.sessions import Session

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _get_jinja_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape([]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_report(session: Session, icp: ICP, lang: str = "es") -> str:
    """Render the full audit report as Markdown.

    Falls back to inline template if template files don't exist.
    """
    ctx = _build_context(session, icp, lang)

    # Try file-based template first
    template_name = f"report_{lang}.md.j2"
    if (_TEMPLATE_DIR / template_name).exists():
        env = _get_jinja_env()
        tmpl = env.get_template(template_name)
        return tmpl.render(**ctx)

    # Fallback: inline template
    return _inline_report(ctx, lang)


async def render_pdf(markdown: str, session_id: str, storage_dir: str) -> str:
    """Render markdown report to PDF via weasyprint.

    Returns the file path of the generated PDF.
    Raises ImportError if weasyprint is not installed.
    """
    import markdown as md_lib
    from weasyprint import HTML

    html_content = md_lib.markdown(markdown, extensions=["tables", "fenced_code"])

    # Wrap in styled HTML
    full_html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
       max-width: 800px; margin: 0 auto; padding: 40px; color: #1a1a2e; }}
h1 {{ color: #16213e; border-bottom: 3px solid #0f3460; padding-bottom: 10px; }}
h2 {{ color: #0f3460; margin-top: 30px; }}
h3 {{ color: #533483; }}
table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
th {{ background-color: #0f3460; color: white; }}
tr:nth-child(even) {{ background-color: #f8f9fa; }}
.score-high {{ color: #e94560; font-weight: bold; }}
.score-medium {{ color: #f5a623; font-weight: bold; }}
.score-low {{ color: #2ecc71; font-weight: bold; }}
blockquote {{ border-left: 4px solid #0f3460; padding-left: 15px;
              color: #555; font-style: italic; }}
</style>
</head><body>{html_content}</body></html>"""

    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    pdf_path = str(Path(storage_dir) / f"audit-{session_id[:8]}.pdf")

    HTML(string=full_html).write_pdf(pdf_path)
    return pdf_path


def _build_context(session: Session, icp: ICP, lang: str) -> dict[str, Any]:
    """Build template context from session data."""
    scores = session.score_breakdown or {}
    ladder = session.value_ladder or {}
    closer = session.closer or {}
    tools = session.tool_comparison or {}
    dims = scores.get("dimensions", {})

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return {
        "lang": lang,
        "date": now,
        "company_name": session.company_name or ("Tu Empresa" if lang == "es" else "Your Company"),
        "contact_name": session.contact_name or "",
        "icp_name": icp.name_es if lang == "es" else icp.name,
        "icp_tier": icp.tier.value,
        "revenue_leak_score": scores.get("revenue_leak_score", 0),
        "leak_category": scores.get("leak_category", ""),
        "fit_score": scores.get("fit_score", 0),
        "fit_category": scores.get("fit_category", ""),
        "pain_severity": dims.get("pain_severity", 0),
        "tech_maturity": dims.get("tech_maturity", 0),
        "readiness": dims.get("readiness", 0),
        "budget_signal": dims.get("budget_signal", 0),
        "recommendations": ladder.get("recommendations", []),
        "credit_bridge": ladder.get(f"credit_bridge_{lang}", ""),
        "founders_active": ladder.get("founders_discount_active", False),
        "founders_pct": ladder.get("founders_discount_pct", 0),
        "clarify": closer.get("clarify", {}).get(lang, ""),
        "label": closer.get("label", {}).get(lang, ""),
        "overview": closer.get("overview", {}).get(lang, ""),
        "qualified": closer.get("qualified", False),
        "tool_rows": tools.get("rows", []),
        "tool_summary": tools.get(f"summary_{lang}", ""),
        "tool_totals": tools.get("totals", {}),
        "vacation_pitch": icp.vacation_pitch_es if lang == "es" else icp.vacation_pitch_en,
        "roi_hook": icp.roi_hook_es if lang == "es" else icp.roi_hook_en,
        "answers": session.answers,
    }


def _inline_report(ctx: dict, lang: str) -> str:
    """Inline Markdown report template (no Jinja2 files needed)."""
    es = lang == "es"

    # Score emoji
    leak = ctx["revenue_leak_score"]
    if leak >= 60:
        score_label = "🔴 CRÍTICO" if es else "🔴 CRITICAL"
    elif leak >= 35:
        score_label = "🟡 MEDIO" if es else "🟡 MEDIUM"
    else:
        score_label = "🟢 BAJO" if es else "🟢 LOW"

    # Build recommendations section
    recs_lines = []
    for r in ctx["recommendations"]:
        pos = r.get("position", "")
        pos_label = {"anchor": "⭐ Premium", "sweet_spot": "✅ Recomendado" if es else "✅ Recommended", "entry": "🚀 Entrada" if es else "🚀 Entry"}.get(pos, pos)
        reason = r.get(f"reason_{lang}", "")
        recs_lines.append(
            f"### {pos_label}: {r['service']}\n"
            f"- **{'Precio' if es else 'Price'}:** {r['price_range']}\n"
            f"- **{'Duración' if es else 'Duration'}:** {r['duration']}\n"
            f"- {reason}\n"
            f"{'- 💰 ' + ctx['credit_bridge'] if r.get('credit_bridge') else ''}"
        )
    recs_text = "\n\n".join(recs_lines)

    # Build tool comparison table
    tool_lines = []
    if ctx["tool_rows"]:
        if es:
            tool_lines.append("| Categoría | Pago | Open Source | CIA |")
        else:
            tool_lines.append("| Category | Paid | Open Source | CIA |")
        tool_lines.append("|---|---|---|---|")
        for row in ctx["tool_rows"]:
            cat = row.get(f"category_name_{lang}", row.get("category", ""))
            paid = row.get("paid", {})
            oss = row.get("oss", {})
            cia = row.get("cia", {})
            tool_lines.append(
                f"| **{cat}** | {paid.get('name', '')} ({paid.get('price', '')}) | "
                f"{oss.get('name', '')} ({oss.get('price', '')}) | "
                f"{cia.get('price', '')} |"
            )
    tools_table = "\n".join(tool_lines)

    # Founders discount note
    founders = ""
    if ctx["founders_active"]:
        pct = int(ctx["founders_pct"] * 100)
        founders = (
            f"\n> 🎁 **Founders Tier activo:** {pct}% de descuento para los primeros 5 clientes.\n"
            if es else
            f"\n> 🎁 **Founders Tier active:** {pct}% discount for the first 5 clients.\n"
        )

    title = "Reporte de Auditoría — Revenue Leak" if es else "Audit Report — Revenue Leak"
    subtitle = f"**{ctx['company_name']}** | {ctx['date']}"

    report = f"""# {title}

{subtitle}

---

## {"Revenue Leak Score" if not es else "Revenue Leak Score"}

**{leak}/100** — {score_label}

| {"Dimensión" if es else "Dimension"} | {"Puntaje" if es else "Score"} |
|---|---|
| {"Severidad del dolor" if es else "Pain severity"} | {ctx['pain_severity']}/100 |
| {"Madurez tecnológica" if es else "Tech maturity"} | {ctx['tech_maturity']}/100 |
| {"Preparación" if es else "Readiness"} | {ctx['readiness']}/100 |
| {"Señal de presupuesto" if es else "Budget signal"} | {ctx['budget_signal']}/100 |

**Fit Score:** {ctx['fit_score']}/100 — {ctx['fit_category']}

---

## {"Diagnóstico" if es else "Diagnosis"}

{ctx['label']}

> {ctx['roi_hook']}

---

## {"Recomendaciones — Value Ladder" if es else "Recommendations — Value Ladder"}

{recs_text}
{founders}
---

## {"Triple Option — Herramientas" if es else "Triple Option — Tools"}

{ctx['tool_summary']}

{tools_table}

---

## {"Visión — Vacation Pitch" if es else "Vision — Vacation Pitch"}

> {ctx['vacation_pitch']}

---

## {"Siguiente Paso" if es else "Next Step"}

{ctx['overview']}

{ctx['credit_bridge']}

---

*{"Generado por univercity-mcp — CIA (Consulting, Implementation & Automation)" if es else "Generated by univercity-mcp — CIA (Consulting, Implementation & Automation)"}*
*{"Cada recomendación muestra: Opción Paga + Open Source + CIA. Tú decides." if es else "Every recommendation shows: Paid + Open Source + CIA option. You decide."}*
"""
    return report
