# UniverCity MCP — Complete Session Handover
## Date: 2026-04-30 | Author: David Lopez (CEO, CIA) + Claude Session

> **PURPOSE:** This document is a COMPLETE knowledge transfer for the next Cowork/Claude session to continue building univercity-mcp. Read this ENTIRE document before writing any code or making any decisions. It contains everything learned across ~12 hours of research, design corrections, and implementation.

---

## 1. WHAT IS THIS PROJECT

**UniverCity MCP** is a business consulting expertise engine packaged as an MCP (Model Context Protocol) server. It's the product of **CIA — Consultoría de Inteligencia Aplicada**, David Lopez's consulting company.

**The core idea:** Any person using ANY LLM (Claude, GPT, Gemini, DeepSeek, Qwen, Perplexity, Cursor, open-source models) says "help me understand what's wrong with my business" → the LLM discovers univercity-mcp via MCP registries → the LLM gathers data about the company (using its own capabilities — email access, file access, computer use, browsing) → sends that data to univercity-mcp's `diagnose` tool → receives expert analysis with Revenue Leak Score, 11-dimension breakdown, and Triple Option recommendations (paid tool / open source alternative / CIA service).

**The MCP IS the product.** Not a sales funnel for consulting. The MCP delivers REAL value for free. When the user wants execution → CIA appears as the service provider. Self-sold.

---

## 2. CRITICAL DESIGN PRINCIPLES (David's corrections — DO NOT VIOLATE)

These are decisions David made after rejecting 3 previous iterations. Each one is non-negotiable:

### 2.1 The LLM has the EYES, the MCP has the BRAIN

The MCP does NOT scrape websites, investigate companies, or collect data. The LLM does that — Claude has MCPs for Slack/Gmail/Calendar/Drive/computer use, Gemini has native Google Workspace, GPT has computer use + browsing, Perplexity has computer access. The MCP receives whatever the LLM already knows and applies CIA's consulting expertise to it.

**What was rejected:** An investigation engine (investigation.py) that scraped websites, detected tech stacks via regex patterns, and analyzed social media presence. David said: "no me gusta, estás empeorando las cosas. No estás teniendo en cuenta que el LLM YA PUEDE CONOCER TODA LA INFO DEL CLIENTE."

### 2.2 Eight dimensions, NOT just software

The v1 audit was trapped in a software mindset (CRM, ERP, analytics). Reality is MUCH wider:

1. **Digital Infrastructure** — Software stack, analytics, web presence
2. **Physical Operations** — Production, facility efficiency, Lean Six Sigma 8 wastes
3. **Supply Chain & Vendors** — Supplier reliability, procurement, logistics
4. **Talent & Human Capital** — Skill gaps, retention, hiring pipeline ($8.5T global cost)
5. **Financial Health** — AR aging (61% B2B invoices paid late), cash flow, burn rate
6. **Leadership & Decision Psychology** — Executive burnout (56%), stress reduces strategic thinking by 26%
7. **Market & Competitive Position** — Market share, pricing, geographic positioning
8. **Regulatory & Compliance** — Industry regulations, tax, data protection

**What was rejected:** Focusing only on CRM/ERP/analytics. David: "también hay problemas físicos como producción, supply chain, escasez de talento humano... hasta la psicología de la alta gerencia."

### 2.3 Each question for each user is 99% different

No fixed questionnaire. No 7 standard questions. The MCP generates dynamic validation questions based on what data is MISSING, weighted by the dimension's importance for that specific ICP.

**What was rejected:** A bank of 7 discovery questions with fixed options. David: "cada pregunta para cada usuario será 99% distinta."

### 2.4 Triple Option Model — Radical transparency

Every recommendation shows 3 paths:
- **A) Best paid tool** (market leader, with price)
- **B) Best open source alternative** (tested by CIA monthly)
- **C) CIA does it all** (custom implementation + price)

No commissions. No affiliate links. If the free option is good enough, we say so. This is CIA's strongest differentiator.

### 2.5 NOT all decision-makers use AI

Only 0.3-1% of the world population pays for AI services (~25-80M people out of 8.1B). ChatGPT has 900M weekly active users but only ~50M paid. The product must work for:
- The 0.3% power users (beachhead — they'll pay $2K for an audit)
- The 3-5% freemium tier (free diagnosis → registered → paid)
- The 96% who don't use AI yet (the product is infrastructure ready when they arrive)

### 2.6 Blockchain is the trust infrastructure

Not optional. Not Phase 3. Blockchain provides:
- Immutable audit trail (every diagnosis recorded on-chain)
- Trust without intermediaries (client verifies blockchain, not CIA's word)
- 24/7 cloud operation (smart contracts automate the pipeline)
- Tokenized access (tokens, not subscriptions)
- Data sovereignty ("your data is YOUR data" — cryptographic proof)

### 2.7 The MCP must DELIVER real value

David's words: "Lo que significa que realmente debemos volvernos expertos, la MCP app de CIA realmente debe entregar cuando le pagan." The MCP is not a teaser. The free diagnosis must be actionable enough that the user can improve their business WITHOUT hiring CIA. That's what makes them hire CIA — they see the depth and want more.

---

## 3. WHAT WAS BUILT THIS SESSION

### 3.1 VISION-v3.md (Strategic Foundation)

Location: `univercity-mcp/VISION-v3.md`

12-part research document with 74 sources. This is the canonical strategic reference:

| Part | Content |
|------|---------|
| 1 | Global opportunity by region (NA $115B, APAC $56B, EU $42B, MEA $46.7B, LATAM $14B) |
| 2 | 8 diagnostic dimensions (beyond software) |
| 3 | Blockchain as trust infrastructure (RWA $24B, 308% growth) |
| 4 | MCP architecture — LLM has eyes, MCP has brain. 1 tool design. |
| 5 | Revenue model — freemium → paid → service |
| 6 | Competitive moat (6 pillars) |
| 7 | What to build (3 phases, Summit demo May 7-8) |
| 8 | Full LLM landscape — US + China ecosystems. Adoption reality: 0.3% pay. |
| 9 | AX/AI — Agent Experience / Agent Interface design |
| 10 | Skills, plugins, connectors as distribution channels |
| 11 | Go-to-market (technical + pragmatic scenarios) |
| 12 | Innovation pipeline — DeepMind, China labs, universities, TOON, ce-mcp |

### 3.2 Code: v0.2.0 Architecture (DDD)

```
src/univercity_mcp/
  config.py                          # Unchanged from v0.1, version bumped to 0.2.0
  server.py                          # OLD v0.1 (6 tools) — preserved for reference
  server_v2.py                       # NEW v0.2 (1 tool: business_diagnose + list_industries)
  
  domain/
    diagnosis/                       # NEW — bounded context
      __init__.py
      model.py                       # Dimension, Finding, DimensionScore, TripleOption,
                                     # ValidationQuestion, DiagnosisReport — all with to_dict()
      service.py                     # diagnose() — the core engine
                                     # _detect_icp(), _score_dimension(), _generate_actions(),
                                     # _generate_validation_questions(), _generate_summary(),
                                     # _generate_leadership_insight()
      benchmarks.py                  # YAML loader with cache, list_available_icps()
      benchmarks/                    # YAML files — add industry = add file, no code changes
        construction.yaml            # Tier 1 — "se nos pierden cotizaciones"
        healthcare.yaml              # Tier 1 — "agujero negro de citas"
        agency.yaml                  # Tier 1 — "márgenes se los come ChatGPT"
        ecommerce.yaml               # Tier 1 — 70% cart abandonment
        startup.yaml                 # Tier 1 — "quemando runway"
        enterprise.yaml              # Tier 1 — "purgatorio de PoC"
        generic.yaml                 # Tier 2 — catch-all
    
    # v0.1 modules (preserved, some still useful):
    icps.py                          # 6 ICP dataclasses with full sales context — VALUABLE
    questions.py                     # Old 7-question bank — DEPRECATED by dynamic validation
    scoring.py                       # Old scoring — REPLACED by diagnosis/service.py
    value_ladder.py                  # 3-tier sandwich pricing — STILL USEFUL
    closer.py                        # CLOSER framework — STILL USEFUL
    objections.py                    # A.A.A. objection handling — STILL USEFUL
    toolstack.py                     # 10 tool categories — STILL USEFUL for Triple Option data
    toolstack_compare.py             # Comparison table builder — STILL USEFUL
    investigation.py                 # REJECTED — web scraping approach. DELETE.
    diagnosis.py                     # REPLACED by domain/diagnosis/service.py. DELETE.
  
  storage/
    sessions.py                      # SQLite session store — WORKS, used by server_v2.py
  
  reports/
    renderer.py                      # Jinja2 markdown/PDF — needs update for v0.2 schema
  
  integrations/
    lead_forward.py                  # n8n webhook + David notification — WORKS
    i18n.py                          # ES/EN strings — WORKS

tests/
  test_domain.py                     # v0.1 tests (39 unit) — still valid for preserved modules
  test_e2e.py                        # v0.1 e2e (5 tests) — needs update for server_v2
  test_v2.py                         # v0.2 tests (14 tests) — ALL PASSING
```

### 3.3 Test Results (14/14 PASSING)

```
OK 1: construction benchmark loads
OK 2: unknown falls back to generic
OK 3: 7 ICPs found
OK 4: ICP detection works (construction, healthcare, ecommerce, Spanish, empty)
OK 5: minimal diagnosis → score=63.8, dims=8
OK 6: construction ICP → Construcción e Inmobiliario, score=66.3
OK 7: rich context quality=0.71 > minimal=0.40
OK 8: 3 validation questions generated
OK 9: leadership insight generated
OK 10: to_dict has all required keys
OK 11: all 6 Tier 1 ICPs produce valid diagnoses
OK 12: all benchmark weights sum to ~1.0
OK 13: English language works
OK 14: edge cases handled
```

### 3.4 Demo Output (Constructora Andina, Bogotá)

Input: construction, 85 employees, WhatsApp+Excel+AutoCAD, "cotizaciones perdidas", material waste, clients pay at 90 days, working weekends.

Output:
- **Revenue Leak Score: 84.5/100 (CRITICAL)**
- **Monthly leak: $25,350 – $126,750 USD**
- **7 findings across 6 dimensions**
- Top actions with Triple Option:
  1. AR aging → QuickBooks ($200/mo) | InvoiceNinja (free) | CIA ($3K-$8K)
  2. No CRM → HubSpot ($45-$800/mo) | Twenty CRM (free) | CIA ($3K-$8K)
  3. No project mgmt → Procore ($375+/mo) | OpenProject (free) | CIA ($4K-$10K)
  4. Talent crisis → CIA ($2K-$10K)
  5. Leadership burnout → CIA ($2K-$10K)
- **Leadership insight:** "burnout detectado, reduce pensamiento estratégico 26%"
- **Data quality: 76% (6/11 dimensions)**
- **3 validation questions targeting missing data**

---

## 4. WHAT NEEDS TO BE DONE NEXT

### 4.1 Immediate (for Summit Demo — May 7-8)

1. **Install dependencies on VPS** — `cd ~/Projects/kairos/mcp-servers/univercity-mcp && pip install -e ".[dev]"` (needs mcp, aiosqlite, jinja2, httpx, pyyaml, pytest)
2. **Run full test suite** — `pytest tests/test_v2.py -v` (the sandbox had disk full, couldn't install deps)
3. **Replace server.py with server_v2.py** — Rename or update entry point
4. **Delete rejected files** — `investigation.py`, old `diagnosis.py`
5. **Update reports/renderer.py** — Adapt Jinja2 templates for new DiagnosisReport schema
6. **Deploy to VPS** — systemd unit, nginx proxy, port 3792
7. **Register on MCP registries** — registry.modelcontextprotocol.io, Smithery, PulseMCP
8. **Set up .well-known/mcp.json** — On univercityaiconsult.tech

### 4.2 Post-Summit (May-June)

1. **Blockchain audit trail** — Ethereum L2 or Solana for cost
2. **PDF/HTML premium reports** — Paid tier
3. **MailerLite integration** — For registered users (AXIS pipeline already exists)
4. **TOON format support** — 30-60% token reduction vs JSON (see Part 12 of VISION-v3)
5. **SKILL.md** — Distribute as agent skill in public ecosystem
6. **Claude Desktop Extension** — .mcpb package

### 4.3 Scale (Q3 2026)

1. **Tokenized access layer** — Blockchain tokens
2. **Smart contract SLAs** — CIA service automation
3. **Regional benchmarks** — LATAM, ASEAN, Africa, MENA YAML files
4. **Multi-language** — ES, EN, PT, FR
5. **Living System Retainer automation** — Smart contracts

---

## 5. CIA'S BUSINESS MODEL (for context)

### Value Ladder (Doc05)

| Step | What | Price | Duration |
|------|------|-------|----------|
| 0 | FREE — LinkedIn, newsletter, AI Readiness Scorecard | $0 | Ongoing |
| 1 | PAID DIAGNOSTIC — Revenue Leak Audit / Workshop | $1K-$5K | 1 day - 3 weeks |
| 2 | CORE — Predictable Revenue Architecture / Agentic Strategy | $4K-$25K | 4-8 weeks |
| 3 | CONTINUITY — Living System Retainer | $500-$3K/mo | Ongoing |
| 4 | BESPOKE — Blockchain-Native Systems | $30K+ | Custom |

**100% Credit Bridge:** Audit costs $3K. If client proceeds to implementation within 30 days, 100% credited. In practice, audit was free.

**3-Tier Sandwich:** Always show Foundation/Growth★/Enterprise. Anchor high first. 70%+ choose middle.

### 6 Real ICPs (Doc02)

1. **Construction & Real Estate** (50-500 emp) — pipeline leakage
2. **Healthcare Clinics** — no-show, missed calls, billing cycle
3. **Digital Agencies** (20-100p) — margin compression from AI
4. **E-commerce & Retail** (mid-market) — 70% cart abandonment
5. **Funded Startups** (Series A-B, LATAM) — burning runway
6. **Enterprise with Innovation Budget** — PoC purgatory

### Sales Framework (Doc01 — CLOSER, Hormozi)

C-Clarify, L-Label, O-Overview past attempts, S-Sell the vacation, E-Explain away objections, R-Reinforce+close.

The MCP does C, L, O automatically before David gets on the call.

### Key Assets

- Domain: univercityaiconsult.tech (paid for 2026)
- App: ai-intel-clone-8xcv.vercel.app
- Email: steban@univercityaiconsult.tech
- Proof points: McCann, Bancolombia, Colliers, Kenworth, ISUZU, Universidad de los Andes, Impetus

---

## 6. MCP ECOSYSTEM KNOWLEDGE (Critical for Development)

### What is MCP

Model Context Protocol — open JSON-RPC spec, donated to Linux Foundation's Agentic AI Foundation (Jan 2026). 97M monthly SDK downloads. Works across Claude, GPT, Gemini, DeepSeek, Qwen, open-source models.

### Key Research Papers

- **97.1% of MCP tool descriptions have quality issues** (arxiv 2602.14878). 56% have "Unclear Purpose." Fewer tools with broader descriptions = better discovery. That's why we have 1 tool, not 6.
- **MCP-Zero** (arxiv 2506.01056): Active tool discovery — agents request tools they need. 98% token reduction.
- **Semantic Tool Discovery** (arxiv 2603.20313): 92.1% precision at K=1.

### AX/AI Design Paradigm

- **AX (Agent Experience):** How the AI agent perceives/uses the MCP tool
- **AI (Agent Interface):** How the human experiences the output
- **Protocol stack:** MCP (tool connection) → A2A (agent-to-agent, Google) → AG-UI (agent-to-frontend, CopilotKit) → A2UI (agent-to-user, Google)

### TOON Format (.toon)

Token-Oriented Object Notation — 30-60% token reduction vs JSON, 73.9% accuracy vs JSON's 69.7%. Already has MCP integration (toon-context-mcp on GitHub). Feature requests open in official MCP repo. CIA should adopt this for output format.

### Skills.md Distribution

Agent Skills = deterministic knowledge injection. Not RAG, not fine-tuning. 1,000+ in public ecosystem. CIA can ship a SKILL.md that teaches any Claude Code instance how to use univercity-mcp.

### Distribution Channels

| Channel | How |
|---------|-----|
| MCP Registry | registry.modelcontextprotocol.io listing |
| Smithery | Curated directory (7K+ servers) |
| Glama | 22,470+ servers |
| .well-known/mcp.json | Auto-discovery on domain |
| Claude Desktop Extension | .mcpb package |
| SKILL.md | Public skill ecosystem |
| pip package | `pip install univercity-mcp` |
| Composio | 500+ managed integrations |

---

## 7. GLOBAL AI LANDSCAPE (for strategic context)

### US Ecosystem ("iOS model" — premium, controlled)

- Claude Max 20x: $200/mo
- GPT-4o + Computer Use
- Gemini + Google Workspace MCP (native)
- Perplexity Computer (Feb 2026)
- Salesforce Agentforce: 18,500 customers, $540M ARR

### China Ecosystem ("Android model" — open, ubiquitous)

- DeepSeek V4: 1.6T params, MIT License, Huawei chips (April 24, 2026)
- Qwen 3.6: 3B active of 35B, $0.38/M tokens, Anthropic-compatible APIs
- Kimi K2.6: 300-agent swarm orchestration
- China surpassed US in model downloads (17.1% vs 15.86%, MIT/HuggingFace)
- Deliver 75-85% of GPT-4o quality at 10-15% cost

### Innovation Pipeline

- **Google DeepMind:** AlphaEvolve (recovered 0.7% of ALL Google compute), Aletheia (autonomous proofs), Gemma 4 (Apache 2.0), Deep Research Max (MCP-native)
- **Universities:** 5 universities adopting MCP institutionally (Clarivate Nexus Connect, July 2026). Northeastern building MCP plugins for scholarly databases.
- **Open Source:** OpenEvolve (open AlphaEvolve), 22,470+ MCP servers, MCP Dev Summit NYC April 2026

### Adoption Reality

| Metric | Number |
|--------|--------|
| World population | 8.1B |
| Active AI users | ~1.1B |
| ChatGPT weekly active | 900M |
| People PAYING for AI | ~25-80M (0.3-1%) |
| ChatGPT paid | ~50M |

---

## 8. REPO STRUCTURE & PATHS

```
~/Projects/kairos/mcp-servers/univercity-mcp/     # Main repo
  VISION-v3.md                                      # Strategic document (READ FIRST)
  HANDOVER-SESSION-2026-04-30.md                    # This file
  pyproject.toml                                    # v0.2.0, entry: server_v2:main
  src/univercity_mcp/                               # Source
  tests/                                            # Tests
  reference/Doc01-05*.docx                          # CIA sales docs (5 files)

~/Projects/kairos/mcp-servers/cia-business-audit/   # OLD — DELETE THIS
~/Projects/kairos-vault/00-Context/                 # System architecture docs
```

### VPS Access

- Tailscale: `100.99.115.48` with `~/.ssh/codex_key`
- IPv4 direct (89.167.122.33) — sshd doesn't listen there
- LiteLLM proxy: `:4000`
- Dashboard: `:3000`
- kairos-api: `:3777`
- univercity-mcp will be: `:3792`

---

## 9. WHAT NOT TO DO (lessons from rejected iterations)

1. **DON'T build a web scraper/investigation engine.** The LLM already has all the data.
2. **DON'T use fixed questionnaires.** Each user is 99% different.
3. **DON'T focus only on software tools.** 11 dimensions, not just CRM/ERP.
4. **DON'T assume users are AI power users.** 99.7% don't pay for AI.
5. **DON'T ignore China's ecosystem.** DeepSeek, Qwen, Kimi are major players.
6. **DON'T forget blockchain.** It's the trust infrastructure, not a feature.
7. **DON'T make the tool description vague.** 97.1% of MCP tools have description quality issues. Ours must be crystal clear.
8. **DON'T create multiple agents.** Olivia is the single agent with N workspaces.
9. **DON'T commit secrets.** .env, .credentials/ in .gitignore.
10. **DON'T call David "Romero" or any other last name.** It's David Lopez.

---

## 10. MIROFISH — FOR PROJECTIONS

David wants the next session to install **MiroFish** (https://github.com/666ghj/MiroFish) — an open-source swarm intelligence simulation engine that spawns thousands of AI agents to simulate scenarios and predict outcomes. 33K+ GitHub stars, $4.1M funding in 24 hours.

### Installation

```bash
# Option A: Local (Mac)
git clone https://github.com/666ghj/MiroFish.git
cd MiroFish
pip install -r requirements.txt

# Option B: Offline with local LLM (Ollama)
git clone https://github.com/nikmcfly/MiroFish-Offline.git
cd MiroFish-Offline
# Requires Neo4j + Ollama
```

### Use Case for CIA

Feed MiroFish our VISION-v3.md + market data → simulate:
1. How MCP adoption curves in LATAM vs ASEAN vs Africa
2. CIA's market penetration at different pricing points
3. Blockchain adoption impact on trust/conversion
4. Competitive response from Big4 consulting firms
5. Revenue projections at different freemium conversion rates

### Key Data Points for Simulations

- TAM: $14B AI consulting → $117B by 2035 → $226B with blockchain
- MCP ecosystem: 22,470+ servers, 97M monthly SDK downloads
- Freemium conversion: 3-5% organic, 10-15% with sales-assist
- 21st.dev precedent: $10K MRR in 6 weeks, zero marketing, MCP-only
- China: 75-85% quality at 10-15% cost. CIA can serve both ecosystems.
- LATAM: 70%+ SMEs at low digital maturity. The gap IS the opportunity.

---

## 11. REFERENCE DOCS IN THE REPO

The 5 sales documents in `reference/` contain CIA's complete sales methodology:

- **Doc01** — CLOSER framework (Hormozi). How to close.
- **Doc02** — ICP Playbook. 6 ICPs with pain language, ROI hooks, pricing bands, objection handling, vacation pitches.
- **Doc03** — Objection handling (A.A.A. method).
- **Doc04** — Value ladder details.
- **Doc05** — Service pricing and credit bridge mechanism.

These are the SOURCE OF TRUTH for the business model. If there's ever a conflict between code and these docs, the docs win.

---

## 12. PHILOSOPHY (David, 2026-04-29)

- Social, human, community-first, conscious
- "Hace que las empresas se vuelvan MUY FÁCIL DE MEJORAR o de matar si es necesario"
- Integrity = depth of concept + massive action without attachment to results
- Democratize access to quality consulting (vs $200K Big4 PowerPoints)
- No estamos aquí para compararnos con el mercado. Estamos aquí para CREAR el mercado.

---

**END OF HANDOVER. Next session: read this, then continue with Section 4 (What Needs to Be Done Next).**
