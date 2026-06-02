"""Visual HTML report renderer for a diagnosis.

Self-contained: inline CSS + pure SVG charts (gauge + horizontal bars), no
external JS/CDN required. Mobile-responsive. Clean / minimalist aesthetic.
Served at GET /report/{session_id} when running in HTTP mode.

Renders from the dict produced by DiagnosisReport.to_dict() (the same object
persisted in session.score_breakdown).

Score semantics follow the engine (v2): higher health_score = HEALTHIER (better).
A low score marks the worst area / biggest opportunity. Color is driven by
`leak_category` (health band: thriving/healthy/weak/critical).
"""
from __future__ import annotations

import html
import math
from typing import Any

from . import branding

_GREEN = branding.COLOR_GREEN
_AMBER = "#EAB308"
_ORANGE = branding.COLOR_ORANGE
_RED = "#EF4444"

# leak_category (health band) → (color, label_es, label_en). Higher = better.
_CATEGORY = {
    "thriving": (_GREEN, "Excelente", "Thriving"),
    "healthy": ("#16A34A", "Sano", "Healthy"),
    "weak": (_ORANGE, "Débil — oportunidad", "Weak — opportunity"),
    "critical": (_RED, "Crítico", "Critical"),
}


def _health_color(score: float) -> str:
    """Per-value color: high health = green, low = red."""
    if score >= 80:
        return _GREEN
    if score >= 60:
        return "#16A34A"
    if score >= 35:
        return _ORANGE
    return _RED


def _esc(v: Any) -> str:
    return html.escape(str(v if v is not None else ""))


def _gauge_svg(score: float, color: str) -> str:
    """Semicircular gauge (0-100). Needle angle 180°→0°."""
    score = max(0.0, min(100.0, float(score)))
    cx, cy, r = 130, 130, 100
    # Background arc (180° to 0°)
    def pt(angle_deg: float) -> tuple[float, float]:
        a = math.radians(angle_deg)
        return cx + r * math.cos(a), cy - r * math.sin(a)
    x0, y0 = pt(180)
    x1, y1 = pt(0)
    # Value arc end
    val_angle = 180 - (score / 100.0) * 180
    vx, vy = pt(val_angle)
    large = 1 if (180 - val_angle) > 180 else 0
    # Needle
    nx, ny = pt(val_angle)
    return f"""
<svg viewBox="0 0 260 160" width="260" height="160" role="img" aria-label="Revenue Leak Score {score:.0f}">
  <path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 0 1 {x1:.1f} {y1:.1f}"
        fill="none" stroke="#E5E7EB" stroke-width="18" stroke-linecap="round"/>
  <path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 {large} 1 {vx:.1f} {vy:.1f}"
        fill="none" stroke="{color}" stroke-width="18" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="6" fill="{branding.COLOR_DARK}"/>
  <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}"
        stroke="{branding.COLOR_DARK}" stroke-width="3" stroke-linecap="round"/>
  <text x="{cx}" y="118" text-anchor="middle" font-size="34" font-weight="800"
        fill="{branding.COLOR_DARK}">{score:.0f}</text>
  <text x="{cx}" y="138" text-anchor="middle" font-size="11" fill="#6B7280">/ 100</text>
</svg>"""


def _bars(dimensions: list[dict]) -> str:
    rows = []
    # Lowest health first = biggest opportunity at the top.
    ordered = sorted(dimensions, key=lambda d: d.get("score", 0))
    for d in ordered:
        score = max(0.0, min(100.0, float(d.get("score", 0))))
        label = _esc(d.get("label") or d.get("dimension"))
        bar_color = _health_color(score)
        rows.append(f"""
  <div class="bar-row">
    <span class="bar-label">{label}</span>
    <span class="bar-track"><span class="bar-fill" style="width:{score:.0f}%;background:{bar_color}"></span></span>
    <span class="bar-val">{score:.0f}</span>
  </div>""")
    return "".join(rows)


def _action_cards(actions: list[dict], lang: str) -> str:
    if not actions:
        return ""
    cards = []
    for a in actions[:3]:
        opts = a.get("options", {})
        paid = opts.get("paid", {})
        oss = opts.get("oss", {})
        cia = opts.get("cia", {})
        action = _esc(a.get("action"))
        impact = _esc(a.get("impact"))
        prio = _esc(a.get("priority"))

        def opt(label, tool, price, url, accent):
            if not tool:
                return ""
            price_html = f" · {_esc(price)}" if price else ""
            tool_html = _esc(tool)
            if url:
                tool_html = f'<a href="{_esc(url)}" target="_blank" rel="noopener">{tool_html}</a>'
            return (f'<li><span class="opt-tag" style="background:{accent}">{label}</span>'
                    f'{tool_html}{price_html}</li>')

        paid_li = opt("PAID" if lang == "en" else "PAGA", paid.get("tool"), paid.get("price"), paid.get("url"), "#6B7280")
        oss_li = opt("OSS", oss.get("tool"), "", oss.get("url"), branding.COLOR_GREEN)
        cia_li = opt("CIA", cia.get("service"), cia.get("price"), branding.BOOKING_URL, branding.COLOR_PURPLE)
        cards.append(f"""
  <div class="card">
    <div class="card-prio">#{prio}</div>
    <h3>{action}</h3>
    <p class="card-impact">{impact}</p>
    <ul class="opts">{paid_li}{oss_li}{cia_li}</ul>
  </div>""")
    return "".join(cards)


def render_report_html(report: dict[str, Any], lang: str = "es") -> str:
    """Render a full diagnosis dict into a standalone HTML page."""
    lang = "en" if lang == "en" else "es"
    company = _esc(report.get("company_name") or ("Tu negocio" if lang == "es" else "Your business"))
    score = float(report.get("health_score") or report.get("revenue_leak_score") or 0)
    category = report.get("leak_category", "weak")
    color, cat_es, cat_en = _CATEGORY.get(category, _CATEGORY["weak"])
    growth = bool(report.get("growth_mode"))
    score_meaning = _esc(report.get("score_meaning", ""))
    cat_label = cat_es if lang == "es" else cat_en
    leak = report.get("monthly_leak_estimate", {}) or {}
    leak_min = leak.get("min_usd", 0)
    leak_max = leak.get("max_usd", 0)
    icp = (report.get("icp") or {}).get("name", "")
    summary = _esc(report.get("summary", "")).replace("\\n", "<br>")
    dims = report.get("dimensions", [])
    actions = report.get("top_actions", [])
    dq = (report.get("data_quality") or {})
    session_id = _esc(report.get("session_id", ""))
    version = _esc(report.get("version", ""))

    t = {
        "es": {
            "title": "Diagnóstico de Negocio", "score": "Business Health Score",
            "leak": "Fuga mensual estimada (áreas débiles)", "dims": "Salud por dimensión",
            "actions": "Acciones prioritarias", "cta": "Agenda con CIA",
            "cta_sub": "30 minutos, sin compromiso. Te mostramos tu diagnóstico en vivo.",
            "by": "Diagnóstico por", "dq": "Calidad de datos",
            "growth": "🚀 Modo crecimiento: la mayoría de tus áreas están fuertes. El siguiente paso es escalar a nuevas ligas.",
        },
        "en": {
            "title": "Business Diagnosis", "score": "Business Health Score",
            "leak": "Estimated monthly leak (weak areas)", "dims": "Health by dimension",
            "actions": "Priority actions", "cta": "Book with CIA",
            "cta_sub": "30 minutes, no commitment. We walk your diagnosis live.",
            "by": "Diagnosis by", "dq": "Data quality",
            "growth": "🚀 Growth mode: most of your areas are strong. The next step is scaling into new leagues.",
        },
    }[lang]

    leak_str = ""
    if leak_max:
        leak_str = f"${leak_min:,} – ${leak_max:,} USD"

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t['title']} · {company} · CIA</title>
<link rel="icon" href="/brand/favicon-32.png">
<style>
  :root {{ --purple:{branding.COLOR_PURPLE}; --dark:{branding.COLOR_DARK}; --accent:{color}; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
         color:#111827; background:#F9FAFB; line-height:1.5; }}
  .wrap {{ max-width:820px; margin:0 auto; padding:24px 18px 64px; }}
  header.top {{ display:flex; align-items:center; justify-content:space-between; gap:12px;
               padding-bottom:18px; border-bottom:1px solid #E5E7EB; margin-bottom:24px; }}
  header.top a {{ display:inline-flex; align-items:center; }}
  header.top img {{ height:46px; width:auto; }}
  header.top .date {{ color:#6B7280; font-size:13px; }}
  h1 {{ font-size:24px; margin:0 0 2px; }}
  .sub {{ color:#6B7280; font-size:14px; margin:0 0 24px; }}
  .hero {{ display:flex; flex-wrap:wrap; align-items:center; gap:20px; background:#fff;
          border:1px solid #E5E7EB; border-radius:16px; padding:22px; margin-bottom:22px; }}
  .hero .meta {{ flex:1; min-width:220px; }}
  .pill {{ display:inline-block; padding:4px 12px; border-radius:999px; color:#fff;
          font-weight:700; font-size:13px; background:var(--accent); }}
  .leak {{ font-size:22px; font-weight:800; margin:10px 0 2px; }}
  .leak-lbl {{ color:#6B7280; font-size:13px; }}
  .summary {{ background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:20px;
             margin-bottom:22px; font-size:15px; }}
  .growthbar {{ background:#ECFDF5; border:1px solid #A7F3D0; color:#065F46; border-radius:12px;
               padding:12px 16px; margin-bottom:14px; font-weight:600; font-size:14px; }}
  .meaning {{ color:#6B7280; font-size:13px; margin:0 0 20px; padding:0 2px; }}
  section h2 {{ font-size:17px; margin:26px 0 12px; }}
  .bars {{ background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:18px; }}
  .bar-row {{ display:flex; align-items:center; gap:10px; padding:5px 0; }}
  .bar-label {{ flex:0 0 38%; font-size:13px; color:#374151; }}
  .bar-track {{ flex:1; height:10px; background:#F3F4F6; border-radius:999px; overflow:hidden; }}
  .bar-fill {{ display:block; height:100%; border-radius:999px; }}
  .bar-val {{ flex:0 0 28px; text-align:right; font-size:12px; color:#6B7280; }}
  .cards {{ display:grid; grid-template-columns:1fr; gap:14px; }}
  .card {{ position:relative; background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:18px; }}
  .card-prio {{ position:absolute; top:14px; right:16px; color:var(--purple); font-weight:800; }}
  .card h3 {{ margin:0 6px 6px 0; font-size:16px; padding-right:30px; }}
  .card-impact {{ color:#6B7280; font-size:13px; margin:0 0 12px; }}
  .opts {{ list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:7px; }}
  .opts li {{ font-size:13px; }}
  .opt-tag {{ display:inline-block; min-width:46px; text-align:center; color:#fff; font-size:10px;
             font-weight:700; padding:2px 6px; border-radius:6px; margin-right:8px; }}
  .opts a {{ color:var(--purple); text-decoration:none; }}
  .cta {{ margin:30px 0 10px; background:var(--dark); color:#fff; border-radius:18px; padding:26px;
         text-align:center; }}
  .cta a.btn {{ display:inline-block; margin-top:14px; background:var(--purple); color:#fff;
               text-decoration:none; padding:13px 26px; border-radius:999px; font-weight:700; }}
  .cta p {{ margin:6px 0; }}
  footer {{ margin-top:30px; padding-top:18px; border-top:1px solid #E5E7EB; color:#6B7280;
           font-size:12px; text-align:center; }}
  footer a {{ color:var(--purple); text-decoration:none; }}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <a href="{branding.WEBSITE}" target="_blank" rel="noopener" aria-label="CIA">
      <img src="/brand/cia-monogram-dark.png" alt="CIA — Consultoría de Inteligencia Aplicada">
    </a>
    <span class="date">{t['by']} <strong>CIA</strong></span>
  </header>

  <h1>{t['title']}: {company}</h1>
  <p class="sub">{_esc(icp)} · {t['dq']}: {round(float(dq.get('overall', 0))*100)}%</p>

  <div class="hero">
    {_gauge_svg(score, color)}
    <div class="meta">
      <span class="pill">{_esc(cat_label)}</span>
      <div class="leak-lbl" style="margin-top:8px">{t['score']} · {t['dq'].lower()} {round(float(dq.get('overall', 0))*100)}%</div>
      <div class="leak">{leak_str or '—'}</div>
      <div class="leak-lbl">{t['leak']}</div>
    </div>
  </div>

  {f'<div class="growthbar">{t["growth"]}</div>' if growth else ''}
  {f'<p class="meaning">{score_meaning}</p>' if score_meaning else ''}

  {f'<div class="summary">{summary}</div>' if summary else ''}

  <section>
    <h2>{t['dims']}</h2>
    <div class="bars">{_bars(dims)}</div>
  </section>

  <section>
    <h2>{t['actions']}</h2>
    <div class="cards">{_action_cards(actions, lang)}</div>
  </section>

  <div class="cta">
    <h2 style="margin:0;color:#fff">{t['cta']}</h2>
    <p>{t['cta_sub']}</p>
    <a class="btn" href="{branding.BOOKING_URL}" target="_blank" rel="noopener">{t['cta']} →</a>
    <p style="font-size:13px;opacity:.8">{_esc(branding.CONTACT_EMAIL)}</p>
  </div>

  <footer>
    <a href="{branding.WEBSITE}" target="_blank" rel="noopener">univercityaiconsult.tech</a>
    · {_esc(branding.CONTACT_EMAIL)} · CIA v{version}<br>
    session {session_id}
  </footer>
</div>
</body>
</html>"""
