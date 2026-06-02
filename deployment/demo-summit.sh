#!/usr/bin/env bash
# ─── Demo script for AI Summit Bogotá — May 7-8, 2026 ───
# cia-diagnose v0.2.0 — Single tool architecture
#
# Usage:
#   ./deployment/demo-summit.sh [es|en]

set -euo pipefail

LANG="${1:-es}"
SERVER="http://127.0.0.1:3792"

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  cia-diagnose v0.2.0 — Demo AI Summit Bogotá"
echo "  Idioma: $LANG"
echo "  Architecture: 1 tool (univercity_diagnose) + 8 dimensions"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check server
if curl -sf "$SERVER/health" > /dev/null 2>&1; then
    echo "✅ Server running at $SERVER"
else
    echo "⚠️  Server not running at $SERVER"
    echo "   Start with: cia-diagnose --transport streamable-http"
    echo "   Or: CIA_TRANSPORT=streamable-http cia-diagnose"
    echo ""
fi

echo ""
echo "📋 v0.2 Demo flow (single tool, NOT 6-step wizard):"
echo ""
echo "  1. LLM gathers context (browsing, conversation, files)"
echo "  2. LLM calls univercity_diagnose with everything it knows"
echo "  3. MCP returns Revenue Leak Score + 8-dimension analysis"
echo "  4. LLM presents findings with Triple Option"
echo "  5. User answers validation questions → re-run for refinement"
echo ""

if [ "$LANG" == "es" ]; then
    echo "🎯 Escenario: Constructora Andina, 85 empleados, Bogotá"
    echo ""
    echo "── Llamada a univercity_diagnose ──"
    echo ""
    cat <<'JSON'
{
  "tool": "univercity_diagnose",
  "args": {
    "company_name": "Constructora Andina",
    "industry": "construcción",
    "team_size": 85,
    "location_city": "Bogotá",
    "location_country": "Colombia",
    "revenue_estimate": "200k-1m",
    "software_detected": "Excel, WhatsApp, AutoCAD, no CRM",
    "pain_points": "cotizaciones perdidas, reporting manual, desperdicios",
    "physical_operations": "desperdicio de material, retrabajo",
    "hiring_challenges": "no encontramos maestros calificados",
    "cash_flow_concerns": "clientes pagan a 90 días",
    "ar_aging": "30% facturas vencidas 60+ días",
    "decision_maker_role": "Director General",
    "stress_indicators": "trabaja fines de semana, micromanagement",
    "growth_stage": "growing",
    "contact_email": "demo@constructora-andina.co",
    "lang": "es"
  }
}
JSON
    echo ""
    echo "── Resultado esperado ──"
    echo ""
    echo "  Revenue Leak Score: ~84.5/100 (CRITICAL)"
    echo "  Fuga mensual estimada: \$25,350 – \$126,750 USD"
    echo "  7 hallazgos en 6 dimensiones"
    echo ""
    echo "  Top actions (Triple Option):"
    echo "  1. AR aging → QuickBooks (\$200/mo) | InvoiceNinja (free) | CIA (\$3K-\$8K)"
    echo "  2. Sin CRM → HubSpot (\$45-\$800/mo) | Twenty CRM (free) | CIA (\$3K-\$8K)"
    echo "  3. Sin project mgmt → Procore (\$375+/mo) | OpenProject (free) | CIA (\$4K-\$10K)"
    echo "  4. Crisis de talento → CIA (\$2K-\$10K)"
    echo "  5. Burnout liderazgo → CIA (\$2K-\$10K)"
    echo ""
    echo "  Leadership insight: burnout detectado → reduce pensamiento estratégico 26%"
    echo "  Data quality: 76% (6/8 dimensiones con datos)"
    echo "  3 preguntas de validación para refinar diagnóstico"
else
    echo "🎯 Scenario: Constructora Andina, 85 employees, Bogotá"
    echo ""
    echo "── univercity_diagnose call ──"
    echo ""
    echo "  (Same JSON as Spanish, with lang: 'en')"
    echo ""
    echo "── Expected output ──"
    echo ""
    echo "  Revenue Leak Score: ~84.5/100 (CRITICAL)"
    echo "  Monthly leak: \$25,350 – \$126,750 USD"
    echo "  7 findings across 6 dimensions"
    echo "  Triple Option recommendations with paid/OSS/CIA paths"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Key differentiators to demo:"
echo "  • 1 tool, not a wizard — LLM drives the conversation"
echo "  • 8 dimensions — not just software (operations, talent, leadership)"
echo "  • Triple Option — radical transparency (paid/OSS/CIA)"
echo "  • Dynamic questions — 99% unique per user"
echo "  • Any LLM — Claude, GPT, Gemini, DeepSeek, Qwen"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "  Server: $SERVER"
echo "  Public: https://audit.univercityaiconsult.tech"
echo "  Docs:   https://univercityaiconsult.tech/.well-known/mcp.json"
echo ""
