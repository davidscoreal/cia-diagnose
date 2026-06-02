# CIA Diagnose v1.1.1

<!-- mcp-name: io.github.davidscoreal/cia-diagnose -->

**Expert business diagnosis engine** by [CIA — Consultoría de Inteligencia Aplicada](https://www.univercityaiconsult.tech/).

Analyzes any company across **11 dimensions** and returns a **Revenue Leak Score** with prioritized, triple-option recommendations (paid tool / open-source / CIA service). Works from Claude, ChatGPT, Gemini, DeepSeek, Cursor — any LLM that speaks MCP.

> 📅 Book a free 30-min diagnosis review: **https://cal.com/david-cia/diagnostico-ai**
> ✉️ steban@univercityaiconsult.tech · 🌐 https://www.univercityaiconsult.tech/

---

## 🚀 For prospects — copy & paste this into any AI

You don't need to know what an "MCP" is. Open **Claude, ChatGPT, or any AI assistant** and paste this:

```text
Quiero un diagnóstico profesional de mi negocio.

Usa la herramienta de diagnóstico de CIA (Consultoría de Inteligencia
Aplicada) — se instala con: pip install cia-diagnose

Pasos:
1. Pregúntame sobre mi empresa: industria, tamaño del equipo, qué
   software uso, qué dolores tengo, cómo manejo proveedores, flujo de
   caja, etc.
2. Cuando tengas suficiente contexto, corre el diagnóstico. Si te falta
   información, pregúntame primero — no adivines.
3. Muéstrame mi Business Health Score (0-100, más alto = más sano; bajo =
   área con mayor oportunidad) y las acciones prioritarias con 3 opciones
   cada una (herramienta paga, alternativa gratuita, servicio profesional
   de CIA con precio).
4. Si el diagnóstico muestra oportunidades, quiero agendar una llamada
   gratuita con CIA: https://cal.com/david-cia/diagnostico-ai — o
   escribir a steban@univercityaiconsult.tech

Más info: https://www.univercityaiconsult.tech/
```

If your AI can connect MCP servers, it will use CIA Diagnose automatically. If not, `pip install cia-diagnose` is the universal fallback any code-capable assistant can run.

---

## Architecture — "LLM has EYES, MCP has BRAIN"

The LLM gathers data from the user (the eyes). CIA Diagnose applies CIA consulting expertise (the brain) — ICP detection, 11-dimension scoring, revenue-leak estimation, and triple-option recommendations. No scraping. No fixed questionnaire. Each diagnosis is unique.

## The 9 tools (the full value journey)

| Tool | Description |
|------|-------------|
| `quick_scan` | FREE instant 3-problem scan. No context needed — hook the client. |
| `business_diagnose` | Full **11-dimension** analysis + Revenue Leak Score + triple-option actions. Forwards the lead to CIA. |
| `list_industries` | Available industry benchmarks. |
| `tools_recommend` | Free & open-source tools per weak dimension. |
| `action_plan` | 30 / 60 / 90-day prioritized roadmap. |
| `roi_projector` | ROI calculator — DIY vs CIA-guided vs full implementation. |
| `case_studies` | Before/after transformation stories by industry. |
| `contact_cia` | Services catalog, pricing, and booking link. |
| `export_report` | Shareable structured report for the client's team. |

## The 11 dimensions

`finanzas`, `comercial`, `operaciones`, `equipo`, `tecnologia`, `marketing`, `clientes`, `proveedores`, `legal`, `estrategia`, `marketing_digital`.

## Scoring — Business Health Score (0-100, higher = healthier)

The headline `health_score` is **inverted from a leak score**: **high = healthy/strong**, **low = the worst area / biggest revenue-leak opportunity**. A 100 doesn't mean "done" — it means that area is taking the business into **new leagues / growth**, which qualifies it even better for CIA. The output also returns `score_meaning`, `growth_mode` (true when most areas are strong — the conversation continues toward scaling), and `guidance` for the calling LLM (ask more vs. present + 3 options). `revenue_leak_score` is kept as a backward-compatible alias (same value).

## Triple Option + curated tool registry

Every recommendation shows three paths: the best **paid tool**, the best **open-source alternative**, and the **CIA professional service** — with prices. The free/OSS/paid picks come from CIA's **curated registry** (`tools_registry/`, by area and per-industry), refreshed weekly. Each tool carries `why_best`. Pass `industry` to `tools_recommend` for industry-specific picks. See [`TOOLS_REGISTRY.md`](TOOLS_REGISTRY.md).

## Quick Start

### Install
```bash
pip install cia-diagnose      # or: uvx cia-diagnose
```

### Run (stdio — local)
```bash
cia-diagnose
```

### Run (HTTP — remote)
```bash
CIA_TRANSPORT=streamable-http cia-diagnose --transport streamable-http --port 3792
```
HTTP mode also serves:
- `GET /report/{session_id}` — visual HTML diagnosis report (gauge + breakdown + actions).
- `GET /export/{session_id}?format=csv|json` — export the diagnosis for Sheets / Tabularis.
- `GET /healthz` — health check.

### Claude Desktop config
```json
{
  "mcpServers": {
    "cia-diagnose": { "command": "uvx", "args": ["cia-diagnose"] }
  }
}
```

### Remote (Streamable HTTP)
```json
{
  "mcpServers": {
    "cia-diagnose": { "url": "https://audit.univercityaiconsult.tech/mcp" }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CIA_TRANSPORT` | `stdio` | Transport: `stdio`, `sse`, `streamable-http` |
| `CIA_HTTP_PORT` | `3792` | HTTP port for remote mode |
| `CIA_DB_PATH` | `~/.cia-diagnose/sessions.db` | SQLite database path |
| `CIA_N8N_WEBHOOK` | (empty) | n8n webhook URL for lead capture |
| `CIA_TELEGRAM_BOT_TOKEN` / `CIA_TELEGRAM_CHAT_ID` | (empty) | Direct Telegram lead alerts |
| `CIA_VAULT_LEAD_LOG` | (empty) | Append-only JSONL path for every lead intake |
| `CIA_RATE_FREE` | `5` | Free diagnoses per **client IP** per day |
| `CIA_LANG` | `es` | Default language (`es`/`en`) |

Every completed `business_diagnose` forwards the lead (company, industry, team_size, revenue_leak_score, top_actions, pain_points, decision_maker_role, the full diagnosis JSON, `source`, timestamp) to all configured sinks. Missing config never fails the diagnosis — it just logs and continues.

## Industry Benchmarks (YAML-driven)

Add an industry = add a YAML in `src/cia_diagnose/domain/diagnosis/benchmarks/`. No code changes.
Current: construction, healthcare, agency, ecommerce, startup, enterprise, restaurant, real_estate, generic.

## Brand assets

`brand/` holds the official CIA logos (monogram light/dark, gothic wordmark, favicons). Wherever a logo appears it links to **https://www.univercityaiconsult.tech/**.

## License

**MIT** — © 2026 CIA — Consultoría de Inteligencia Aplicada (David Lopez). See [`LICENSE`](LICENSE).
