# CIA Diagnose v0.2.1

<!-- mcp-name: io.github.davidscoreal/cia-diagnose -->

**Expert business diagnosis engine** by [CIA — Consultoría de Inteligencia Aplicada](https://univercityaiconsult.tech).

Analyzes any company across **11 dimensions** and returns a Revenue Leak Score with prioritized, triple-option recommendations. Works from Claude, GPT, Gemini, DeepSeek, Cursor — any LLM that speaks MCP.

## Architecture

**"LLM has EYES, MCP has BRAIN."**

The LLM gathers data from the user (the eyes). CIA Diagnose applies CIA consulting expertise (the brain) — ICP detection, dimension scoring, revenue leak estimation, and triple-option recommendations. No scraping. No fixed questionnaire. Each diagnosis is unique.

## Tools

| Tool | Description |
|------|-------------|
| `business_diagnose` | Full 11-dimension diagnosis. Send company context, get Revenue Leak Score + actions. |
| `list_industries` | Returns available industry benchmarks (construction, healthcare, agency, ecommerce, startup, enterprise, generic). |

## 8 Dimensions

digital, operations, supply_chain, talent, financial, leadership, market, regulatory

## Triple Option

Every recommendation shows three paths: the best **paid tool**, the best **open source alternative**, and the **CIA professional service** — with prices. Radical transparency.

## Quick Start

### Install

```bash
pip install cia-diagnose
```

### Run (stdio — local)

```bash
cia-diagnose
```

### Run (HTTP — remote)

```bash
CIA_TRANSPORT=streamable-http cia-diagnose --transport streamable-http --port 3792
```

### Claude Desktop config

```json
{
  "mcpServers": {
    "cia-diagnose": {
      "command": "uvx",
      "args": ["cia-diagnose"]
    }
  }
}
```

### Remote (Streamable HTTP)

```json
{
  "mcpServers": {
    "cia-diagnose": {
      "url": "https://audit.univercityaiconsult.tech/mcp"
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CIA_TRANSPORT` | `stdio` | Transport: stdio, sse, streamable-http |
| `CIA_HTTP_PORT` | `3792` | HTTP port for remote mode |
| `CIA_DB_PATH` | `~/.cia-diagnose/sessions.db` | SQLite database path |
| `CIA_N8N_WEBHOOK` | (empty) | n8n webhook for lead capture |
| `CIA_RATE_FREE` | `5` | Free diagnoses per IP per day |
| `CIA_LANG` | `es` | Default language (es/en) |

## Industry Benchmarks (YAML-driven)

Add an industry = add a YAML file in `src/cia_diagnose/domain/diagnosis/benchmarks/`. No code changes needed.

Current benchmarks: construction, healthcare, agency, ecommerce, startup, enterprise, generic.

## Value Ladder

Free diagnosis → Paid diagnostic (\$1K-\$5K) → Core implementation (\$4K-\$25K) → Retainer (\$500-\$3K/mo) → Bespoke (\$30K+)

100% Credit Bridge: audit cost credited if client proceeds within 30 days.

## License

Proprietary — CIA (Consultoría de Inteligencia Aplicada). All rights reserved.
