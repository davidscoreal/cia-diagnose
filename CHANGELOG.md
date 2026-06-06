# Changelog

## v1.2.0 (2026-06-06) — Defensible scoring (T13)

The Business Health Score was effectively constant (~30/CRÍTICO for almost any
input: a deliberately healthy agency and a burning one both scored ~30, spread
0.0). It is now **traceable, responsive, and benchmark-as-yardstick**.

### Changed (score behaviour — hence the minor bump)
- **Score is computed from the prospect's own intake vs benchmark**, per
  dimension, each producing a `basis` (e.g. `"margen bruto: 32 (vs bench 28%) →
  88/100"`). Healthy agency now scores ~93 (thriving), a struggling one ~10
  (critical) — spread ~83.
- **`_evaluate_finding_condition` defaults to `False`** for unparseable
  conditions (was `True`, so almost everything fired and floored the score).
- **`"always"` / benchmark findings no longer move the score.** They are
  surfaced separately as `industry_context`, labelled "Benchmark de industria
  (referencia)" — the yardstick, never the prospect's own number.
- **Composite = weighted average of dimensions WITH data only.** Dimensions
  without data are `status: "insufficient_data"`, excluded, and become
  follow-up questions.

### Added (output keys — additive, backward-compatible)
- `confidence` — share of weight backed by the prospect's real data.
- `verdict` — `"preliminary"` when `confidence < 0.6` (no hard sentence on thin
  data); otherwise the health band.
- `data_gaps` — `[{dimension, question_es, question_en}]` driving the
  one-question-at-a-time follow-up flow.
- `industry_context` — benchmark references that inform but don't score.
- per dimension: `status` and `basis`.
- Optional deep-intake fields (INTAKE-SCHEMA): `gross_margin_pct`, `ar_days`,
  `cash_runway_months`, `on_time_on_budget_pct`, `reporting`,
  `documented_processes`, `founder_dependency`, `annual_turnover_pct`,
  `billable_utilization_pct`, `integration_level`, `ai_adoption`,
  `core_systems`, `lead_source_concentration`, `conversion_rate_pct`,
  `cac_ltv_known`, `documented_plan`, `revenue_concentration_pct`. All optional;
  the engine runs on partial data and asks for the rest.
- `tests/test_scoring.py` — responsiveness + defensibility invariants.

### Unchanged
- MCP tool signature, the triple-option (`options`) shape, and the existing
  report keys. The leak estimate (`tests/test_leak_estimate.py`) stays green.

## v1.1.2 (2026-06-05)

### Fixed
- **Revenue-leak parser (`_estimate_monthly_leak`) — demo-killer.** The fallback
  parser grabbed only the first number, so:
  - `"0-200k"` returned **$0/mo** while the report screamed "CRÍTICO" — a self-
    contradiction live in front of a lead.
  - en-dash dropdown values (`"USD 200k – 1M"`) diverged from their hyphen
    equivalents (`"200k-1m"`) → different leak for the same band.
  - two-sided ranges (`"50k-200k"`) took the floor instead of the midpoint.
  - the `1_000_000` default rendered an absurd **~$15k/mo** leak for pre-revenue
    leads.
  Now unicode dashes are normalised, every bound is parsed, ranges use the
  midpoint, open-low bands use the ceiling, pre-revenue anchors to a credible
  run-rate, and the estimate can never collapse to $0.

### Changed
- **Benchmark findings are labelled.** A finding with no lead-specific
  `evidence` is now flagged `basis: "industry_benchmark"` with a visible
  `"Benchmark de la industria (referencia)"` label, so reference findings are
  never presented as detected in the client's own data.
- **`next_step_url` no longer ships empty.** It falls back to the configured
  booking URL (`branding.BOOKING_URL`) when no hosted report URL is set.

### Added
- `tests/test_leak_estimate.py` — acceptance invariants for the leak estimate
  (no-$0, dash-invariance, midpoint, pre-revenue bounded, monotonicity) plus
  reference-value spot checks.

## v1.1.1 (2026-06-02)

- **License changed to MIT** (was Proprietary in 1.1.0). `pyproject` now declares
  SPDX `MIT` + `license-files`; `LICENSE` is the MIT text; README updated. Open
  source. (1.1.0 was the first PyPI release under the `cia-diagnose` name and
  carried Proprietary metadata; PyPI versions are immutable, so 1.1.1 republishes
  with MIT — install `cia-diagnose>=1.1.1` for the MIT build.)

## v1.1.0 (2026-06-02) — boost/v2

### Fixed (bugs found in audit — see AUDIT.md)
- **B2:** `export_report` passed `session=None` to `forward_lead`, which crashed
  on `session.id` (`AttributeError`) and silently dropped the lead. `forward_lead`
  now accepts `session=None` and reads from `extra`.
- **B3:** rate limit used a hardcoded `ip="cli"` → in HTTP mode the 5/day limit was
  **global, shared across all clients**. Now derives the real client IP
  (`X-Forwarded-For` → socket peer) via the FastMCP `Context`; stdio stays `cli`.
- **B4:** Cal.com booking URL was `cal.com/cia-consulting` (wrong) → now the
  canonical `cal.com/david-cia/diagnostico-ai`, centralized in `branding.py`.
- **B5:** `DiagnosisReport.version` was hardcoded `0.2.0` → now reads `SERVER_VERSION`.

### Added
- `branding.py` — single source of truth for links, contact, brand colors, taglines,
  and the diagnosis signature (header / booking CTA / closing). Used everywhere.
- **Lead webhook enriched** (tarea 1): payload now carries `source`
  (`mcp_local`/`mcp_remote`), `team_size`, `pain_points`, `decision_maker_role`,
  `top_actions`, `estimated_monthly_leak`, and the **full diagnosis JSON**.
- **Brand signature in tool output** (tarea 3): `business_diagnose` and
  `export_report` return a `cia` block (header, booking CTA, closing, links).
- **Visual HTML report** (tarea 4): `report_html.py` — SVG gauge + dimension bars +
  triple-option cards + CTA, mobile-responsive, no external JS. Served at
  `GET /report/{session_id}` in HTTP mode.
- **Export endpoints** (tarea 9): `GET /export/{session_id}?format=json|csv` for
  Sheets / Tabularis, plus `GET /healthz` and `GET /brand/{asset}`.
- `brand/` — official CIA logos (monogram light/dark, gothic wordmark, favicons),
  all linking to the website.
- Prospect copy-paste prompt in `README.md` (tarea 2).
- `AUDIT.md`, `DECISION.md` (PocketBase/SQLite + Dub), `INTEGRATION_GUIDE.md`
  (call.md), `EVOLUTION_PLAN.md` (Evolver).
- `tests/test_boost_v2.py` — 6 tests (branding, B2, rich webhook, HTML render,
  signature, HTTP routes). Suite: **44 passing**.

### Changed / cleanup
- `SessionStore.initialize()` is now idempotent (HTTP custom routes live outside the
  MCP per-session lifespan and must self-initialize the store).
- `README.md` rewritten: correct v1.0.0, all 9 tools, the real 11 Spanish dimensions,
  prospect prompt, HTTP endpoints, env vars.
- `server.json` realigned to `cia-diagnose` v1.0.0 (was stale `univercity-mcp` 0.2.1).
- Removed committed `*.bak-*` files from `src/`.
- `contact_cia` no longer exposes the personal Gmail or a placeholder WhatsApp.

### boost/v2 — round 2 (2026-06-02, after David review)
- **B6 RESOLVED — score inverted to Business Health Score** (high = healthier,
  low = worst area / biggest opportunity). Engine now computes per-dimension and
  overall **health**; `_categorize_health` bands = thriving/healthy/weak/critical.
  `health_score` is the headline; `revenue_leak_score` kept as a same-value alias
  (object property + dict key) so `roi_projector`/`export_report` (which already
  assumed high=good) stay correct. Added `score_meaning` (incl. "100% = entering
  new leagues / growth"), `growth_mode`, and `guidance` (tells the LLM to ASK
  first when data is thin, and to keep the conversation going when healthy).
- **Up-front elicitation + continuity** baked into FastMCP `instructions` and the
  `business_diagnose` docstring.
- **Curated tool registry** (`tools_registry/`): best free/OSS/paid per **area ×
  industry** with provenance (`tier`, `why_best`, `last_reviewed`). Replaces the
  inline `_TOOL_DB`. `tools_recommend` gains an `industry` param; `action_plan`
  uses it too. `scripts/refresh_tools.py` + `TOOLS_REGISTRY.md` document the
  **weekly refresh** process. (Construction industry override seeded.)
- **License RESOLVED — Proprietary.** Added `LICENSE` (per CIA's
  Términos de Licencia de Software e IA); `pyproject` now `license = {file=...}`.
- **All `univercity-mcp` references purged** from the live tree (SKILL.md,
  AGENTS.md, REGISTRY-LISTING.md, deployment/* renamed to `cia-diagnose.*`,
  scripts, tests). Historical narrative docs moved to `_archive/`.
- **Lint:** `src/` is now ruff-clean (removed pre-existing dead vars / dup dict
  key / unused imports). Tests: **48 passing**.
- **PyPI:** publishing `cia-diagnose` v1.0.0 via GitHub Release → trusted
  publishing (OIDC) in `publish.yml`. Wheel ships brand assets + registry + YAMLs.

### boost/v2 — round 3 (2026-06-02, security audit + bug hunt + research)
Security (from a dedicated audit — nothing dangerous was committed; these are hardening):
- Removed hardcoded **personal Gmail** and **Google Sheet ID** from `config.py`
  defaults (no PII baked into the public wheel; set via `CIA_DAVID_EMAIL`/`CIA_SHEETS_ID`).
- Default bind flipped `0.0.0.0` → **`127.0.0.1`** (the report/export routes are
  unauthenticated; the VPS opts into 0.0.0.0 behind nginx).
- `/report` and `/export` now send `X-Robots-Tag: noindex` + `Cache-Control:
  private, no-store` (capability-URL hardening; session ids are uuid4).
- Removed `scripts/hostinger_dns.py` and the whole `_archive/` (leaked VPS IPs,
  ports, internal paths/model name — recon, not credentials). Dropped internal
  `kairos-primary` default. Hardened the systemd unit (DynamicUser, no root,
  ProtectSystem/Home, PrivateTmp).
Bugs (from an adversarial hunt):
- ROI/summary coherence: a **healthy business is no longer told it's leaking
  catastrophically** — `roi_projector` reframes to growth when score ≥ 70 and
  `_generate_summary` drops the leak line in growth_mode. `roi_projector` guards
  `monthly_revenue <= 0`.
- `lead_forward` adds `score_semantics: "health_higher_is_better"` so downstream
  CRM/Sheets don't misread the (now health) score.
- `lang` normalized to es/en in `diagnose()` and the tools (no JSON/HTML mismatch).
- `_estimate_monthly_leak`: bare numbers ≥1000 read as literal currency (was ×1e6).
Research / niche (David's emphasis):
- New `niche` field on `business_diagnose` (hyper-specific sub-vertical), captured
  in the webhook for niche targeting + trend analysis.
- `scripts/trends.py` (anonymized aggregation of the vault log → trends, no PII)
  and `RESEARCH.md` — the path to CIA's own papers.
- Tests: **54 passing**.

### Known issues (flagged)
- `.well-known/mcp.json` is empty — left as-is to avoid guessing the registry
  domain-verification schema.
- Benchmark **calibration**: the engine still skews toward finding leaks (exact-match
  finding conditions), so many businesses score low until benchmarks are recalibrated
  with real outcome data — see `EVOLUTION_PLAN.md`.

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
