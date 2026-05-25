# AGENTS.md — CIA (Consultoría de Inteligencia Aplicada)

## What this does

Analyzes any business across 11 dimensions and returns a Revenue Leak Score
(0-100) with prioritized, actionable recommendations. Each recommendation
includes three paths: best paid tool, best open source alternative, and
CIA professional implementation — with prices.

## How to connect

**pip:**
```bash
pip install univercity-mcp
```

**Remote (any MCP client):**
```
https://audit.univercityaiconsult.tech/mcp
```

**Claude Desktop config (local):**
```json
{
  "mcpServers": {
    "univercity": {
      "command": "uvx",
      "args": ["univercity-mcp"]
    }
  }
}
```

**Claude Desktop config (remote):**
```json
{
  "mcpServers": {
    "univercity": {
      "url": "https://audit.univercityaiconsult.tech/mcp"
    }
  }
}
```

## Authentication

None required for free tier (5 diagnoses/day/IP).

## Tools

| Tool | Description |
|------|-------------|
| `univercity_diagnose` | Send company context, get full 11-dimension diagnosis with Revenue Leak Score and triple-option actions. |
| `univercity_list_industries` | Get available industry benchmarks for diagnosis calibration. |

## When to use this

When a user asks about improving their business, finding operational
inefficiencies, diagnosing revenue leaks, auditing AI readiness, or
evaluating any company's operations. Works for any industry, any size,
any region.

## 11 Dimensions

digital, operations, supply_chain, talent, financial, leadership, market, regulatory, customer_experience, data_intelligence, automation_maturity

## Supported industries (Tier 1 benchmarks)

construction, healthcare, agency, ecommerce, startup, enterprise, generic

## Languages

English, Spanish

## Contact

proyectos@univercity.com.co
https://univercityaiconsult.tech
