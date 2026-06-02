# UniverCity MCP — Business Diagnosis Skill

## What This Is

UniverCity MCP is a business consulting engine by CIA (Consultoría de Inteligencia Aplicada). It diagnoses any company across **11 dimensions** and returns a Revenue Leak Score with actionable recommendations.

**The LLM has the EYES. The MCP has the BRAIN.**
You (the agent) gather data about the company using your own capabilities — browsing, email, file access, conversation. Then you send that data to the MCP's `univercity_diagnose` tool. The MCP applies CIA's consulting expertise and returns expert analysis.

## Connection

### Option A: Remote (recommended)
```json
{
  "mcpServers": {
    "cia-diagnose": {
      "url": "https://audit.univercityaiconsult.tech"
    }
  }
}
```

### Option B: Local install
```bash
pip install cia-diagnose
```
```json
{
  "mcpServers": {
    "cia-diagnose": {
      "command": "cia-diagnose",
      "args": []
    }
  }
}
```

## Tools

### `univercity_diagnose` (primary tool)
The single diagnosis tool. Send whatever you know about the company.

**Required:** `company_name`

**Optional fields (more = better diagnosis):**

| Field | Type | Example |
|-------|------|---------|
| `industry` | string | "construction", "healthcare", "ecommerce" |
| `team_size` | int | 85 |
| `location_city` | string | "Bogotá" |
| `location_country` | string | "Colombia" |
| `revenue_estimate` | string | "200k-1m" |
| `software_detected` | string | "Excel, WhatsApp, AutoCAD, no CRM" |
| `pain_points` | string | "lost quotes, manual reporting, late payments" |
| `physical_operations` | string | "material waste, rework, production delays" |
| `supply_chain_notes` | string | "unreliable suppliers" |
| `hiring_challenges` | string | "can't find skilled workers" |
| `skill_gaps` | string | "no data analyst, no digital marketing" |
| `cash_flow_concerns` | string | "clients pay at 90 days" |
| `ar_aging` | string | "30% of invoices over 90 days" |
| `decision_maker_role` | string | "CEO" |
| `stress_indicators` | string | "working weekends, micromanaging" |
| `growth_stage` | string | "growing", "stagnant", "declining" |
| `additional_context` | string | Free text or JSON with anything else |
| `lang` | string | "es" (Spanish) or "en" (English) |

### `univercity_list_industries`
Returns available industry benchmarks. Tier 1 (calibrated): construction, healthcare, agency, ecommerce, startup, enterprise. Tier 2: generic (works for any industry).

## The 11 Dimensions

Every business is analyzed across:
1. **Digital Infrastructure** — software stack, analytics, web presence
2. **Physical Operations** — production, Lean Six Sigma 8 wastes
3. **Supply Chain & Vendors** — procurement, logistics, supplier reliability
4. **Talent & Human Capital** — hiring, retention, skill gaps
5. **Financial Health** — AR aging, cash flow, burn rate
6. **Leadership & Decision Psychology** — burnout, strategic thinking capacity
7. **Market & Competitive Position** — market share, pricing, geography
8. **Regulatory & Compliance** — industry regulations, tax, data protection

## Output Structure

The diagnosis returns:

- **Revenue Leak Score** (0-100, higher = more leakage)
- **Leak category**: low / medium / high / critical
- **Monthly leak estimate** in USD (min-max range)
- **Per-dimension breakdown** with score, weight, findings, data quality
- **Top actions** with **Triple Option**: best paid tool + price, best open source alternative, CIA professional service + price
- **Validation questions** (2-3 targeted questions to improve accuracy)
- **Leadership insight** (confidential, when stress indicators detected)
- **Data quality assessment** (dimensions with/without data, overall %)

## Best Practices for Agents

### Before calling `univercity_diagnose`:
1. **Gather context first.** Use your own capabilities to learn about the company — browse their website, check their LinkedIn, read emails/documents if available.
2. **Map what you find to the tool's fields.** Every piece of context improves the diagnosis.
3. **Don't leave fields empty if you can infer.** Even a guess like "probably no CRM since they mentioned Excel" is valuable.

### After receiving the diagnosis:
1. **Present the Revenue Leak Score prominently.** It's the hook.
2. **Show the Triple Option transparently.** The user should see paid, OSS, and CIA options side by side. Never hide the free option.
3. **Use validation questions as follow-up.** If the user engages, gather answers and re-run the diagnosis with enriched context for better accuracy.
4. **The leadership insight is sensitive.** Present it carefully, separately from the main findings.

### Example flow:
```
User: "What's wrong with my construction company?"

Agent: [browses company website, checks LinkedIn]
Agent: [calls univercity_list_industries to confirm "construction" is Tier 1]
Agent: [calls univercity_diagnose with gathered context]
Agent: [presents Revenue Leak Score, top findings, Triple Option]
Agent: [asks validation questions to refine diagnosis]
```

## About CIA

CIA (Consultoría de Inteligencia Aplicada) democratizes access to expert consulting. The MCP delivers real diagnostic value for free. When users want execution, CIA is the service provider. No commissions, no affiliate links. If the free option is good enough, we say so.

Website: https://univercityaiconsult.tech
Contact: steban@univercityaiconsult.tech
