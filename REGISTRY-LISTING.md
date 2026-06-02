# MCP Registry Listing — cia-diagnose

## For registry.modelcontextprotocol.io

**Name:** cia-diagnose
**Tagline:** Expert business diagnosis engine — 11 dimensions, Revenue Leak Score, Triple Option recommendations
**Category:** Business & Consulting
**Author:** David Lopez / CIA (Consultoría de Inteligencia Aplicada)
**License:** MIT
**Repository:** https://github.com/davidscoreal/cia-diagnose
**Website:** https://univercityaiconsult.tech
**Server URL:** https://audit.univercityaiconsult.tech

### Description (for registry)

Diagnose any business across 11 dimensions — digital infrastructure, physical operations, supply chain, talent, financial health, leadership psychology, market position, and regulatory compliance. Returns a Revenue Leak Score (0-100) with monthly leak estimate in USD and prioritized Triple Option recommendations: best paid tool with price, best open source alternative, and professional CIA service.

Works for ANY industry. Tier 1 benchmarks for construction, healthcare, digital agency, ecommerce, startup, and enterprise. Bilingual (ES/EN).

One tool. Open schema. Send what you know, get expert analysis back.

### Install (stdio)
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

### Install (remote)
```json
{
  "mcpServers": {
    "cia-diagnose": {
      "url": "https://audit.univercityaiconsult.tech"
    }
  }
}
```

### Tags
business, consulting, diagnosis, revenue-leak, sme, latam, 11-dimensions, triple-option

---

## For Smithery.ai

**Server ID:** cia-diagnose
**Display Name:** CIA Diagnose — Business Diagnosis Engine
**Short Description:** Expert 11-dimension business diagnosis with Revenue Leak Score and triple-option recommendations (paid/OSS/CIA)

**Long Description:**
CIA Diagnose is a business consulting expertise engine. Any LLM that speaks MCP can diagnose a company across 11 dimensions:

1. Digital Infrastructure — software stack, analytics, web presence
2. Physical Operations — production efficiency, Lean Six Sigma 8 wastes
3. Supply Chain & Vendors — procurement, logistics, supplier reliability
4. Talent & Human Capital — hiring pipeline, retention, skill gaps ($8.5T global cost)
5. Financial Health — AR aging (61% B2B invoices paid late), cash flow, burn rate
6. Leadership & Decision Psychology — executive burnout (56%), strategic thinking -26%
7. Market & Competitive Position — market share, pricing, geographic positioning
8. Regulatory & Compliance — industry regulations, tax, data protection

The LLM gathers data. The MCP applies CIA's consulting expertise. One tool, not a wizard.

Every recommendation shows 3 transparent paths:
- Best paid tool (market leader, with price)
- Best open source alternative (tested monthly)
- CIA does it all (professional implementation, with price)

No commissions. No affiliate links. If the free option works, we say so.

**Qualifiers:** Production-ready, Bilingual (ES/EN), 14/14 tests passing
**Transport:** stdio, streamable-http
**Python:** >=3.10

### Smithery Config (smithery.yaml)
```yaml
name: cia-diagnose
displayName: "CIA Diagnose — Business Diagnosis Engine"
description: "Expert 11-dimension business diagnosis with Revenue Leak Score"
author: "CIA — Consultoría de Inteligencia Aplicada"
license: MIT
homepage: https://univercityaiconsult.tech
repository: https://github.com/davidscoreal/cia-diagnose
tags:
  - business
  - consulting
  - diagnosis
  - revenue-optimization
  - sme
transport:
  stdio:
    command: cia-diagnose
  http:
    url: https://audit.univercityaiconsult.tech
```

---

## Submission Checklist

- [ ] Push to GitHub (public repo)
- [ ] Publish to PyPI: `pip install cia-diagnose`
- [ ] Submit to registry.modelcontextprotocol.io
- [ ] Submit to Smithery.ai
- [ ] Submit to PulseMCP
- [ ] Submit to Glama.ai
- [ ] Deploy .well-known/mcp.json to univercityaiconsult.tech
- [ ] Test remote connection via Claude Desktop
- [ ] Test via GPT with MCP bridge
