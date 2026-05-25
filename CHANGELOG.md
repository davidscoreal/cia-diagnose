# Changelog

## v0.2.0 (2026-04-30)

### Architecture overhaul
- Single `business_diagnose` tool replaces 6-tool wizard (audit_start/respond/estimate/report/book_call/share)
- "LLM has EYES, MCP has BRAIN" — open schema, no fixed questionnaire
- Each diagnosis is 99% unique per user

### New features
- 11-dimension analysis: digital, operations, supply_chain, talent, financial, leadership, market, regulatory, customer_experience, data_intelligence, automation_maturity
- YAML-driven ICP benchmarks (7 industries: construction, healthcare, agency, ecommerce, startup, enterprise, generic)
- Triple Option: paid tool + OSS alternative + CIA service with prices on every recommendation
- Revenue Leak Score with monthly leak estimation
- Dynamic validation questions
- Leadership psychology dimension
- `list_industries` utility tool
- `.well-known/mcp.json` auto-discovery manifest
- SKILL.md for agent skill distribution
- Registry listings (MCP Registry, Smithery, PulseMCP, Glama)

### Infrastructure
- FastMCP with lifespan management
- Rate limiting (5 free/day per IP)
- SQLite session storage (PostgreSQL post-Summit)
- n8n webhook lead capture
- Streamable HTTP + stdio transport support
- systemd + nginx deployment configs

### Removed
- Fixed 7-question questionnaire (replaced by dynamic validation)
- 6-tool wizard flow
- Investigation/scraping layer
- fit_score (replaced by revenue_leak_score)

## v0.1.0 (2026-04-29)

- Initial 6-tool wizard: audit_start, respond, estimate, report, book_call, share
- Fixed 7-question bank with UI component hints
- ICP detection with 6 profiles
- ScoreBreakdown with fit_score + revenue_leak_score
- CLOSER pre-qualification (C, L, O stages)
- Value ladder sandwich pricing
- Toolstack comparison (10 categories)
- A.A.A. objection handling (9 responses)
