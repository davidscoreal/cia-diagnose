# UniverCity MCP — Plan Maestro v1

**Fecha:** 2026.04.29
**Autor:** Claude (sintetizado de Doc01-05, spec original, research MCP ecosystem, código Layer 1)
**Demo target:** AI Summit Bogotá 7-8 mayo 2026 (8 días)
**Repo:** `~/Projects/kairos/mcp-servers/univercity-mcp/`

---

## 1. QUÉ ES ESTO (y qué NO es)

**ES:** Un MCP server público que ES el producto de CIA. Cualquier persona, cualquier industria, cualquier país, desde cualquier LLM (Claude, ChatGPT, Gemini, Copilot, Cursor), dice "quiero automatizar mi negocio" y el LLM descubre univercity-mcp. El MCP entrega valor REAL gratis — diagnóstico, mapa de fugas, recomendaciones accionables con números. El mundo es el mercado.

**NO ES:** Una herramienta limitada a 6 industrias. NO es un formulario que genera un lead. NO es un quiz genérico. NO es una demo de tecnología. Es experticia empaquetada, abierta a todos.

**Modelo de profundidad (no de exclusión):**
- **Tier 1 — 6 ICPs core:** Construcción, Healthcare, Agencias, E-commerce, Startups, Enterprise. Experiencia premium: pain language calibrado, pricing por industria, objeciones específicas, benchmarks reales. Estos son los que mejor pagan, más necesitan, y más hay en LATAM — por eso CIA los conoce a fondo.
- **Tier 2 — Cualquier otra industria:** Recibe el audit completo con recomendaciones de calidad, Triple Option (Paid/OSS/CIA), y roadmap accionable. Sin pain language específico ni benchmarks de industria — pero con toda la lógica de Revenue Leak, toolstack, y valor real.
- **Evolución natural:** Las industrias Tier 2 que generen más interacción se promueven a Tier 1 con el tiempo. Data intelligence decide cuáles. El mercado le dice a CIA dónde profundizar.

**Diferencia con lo que se construyó antes (cia-business-audit v0.1.0 — MUERTO):**

| Antes (mal) | Ahora (bien) |
|-------------|-------------|
| Solo recomendaba herramientas pagadas | Triple Option: Paid / Open Source / CIA — usuario decide |
| 4 industrias genéricas cerradas | Abierto a TODAS las industrias, 6 ICPs con profundidad premium |
| Scoring genérico 0-100 | Mapping a servicios reales + pricing real |
| "Recomendaciones" vagas | Value Ladder completo (Free→$5K→$25K→$3K/mo→$30K+) |
| Lead form al final | Freemium cálido: valor gratis → cuenta → ejecución pagada |
| Solo Claude | Cross-LLM: Registry + Smithery + .well-known + .mcpb |

---

## 2. FLUJO DE USUARIO COMPLETO

```
1. Usuario en cualquier LLM: "quiero automatizar mi negocio"
2. LLM descubre univercity-mcp vía Registry/Smithery/.well-known
3. MCP: diagnóstico GRATIS — 5-7 preguntas adaptativas por ICP
   └─ Usa pain language REAL del ICP (Doc02)
   └─ Detecta industria automáticamente
   └─ Output: score + ahorro estimado + mapa de fugas + roadmap 30/60/90
4. Usuario impresionado: "esto es exactamente mi problema"
5. MCP ofrece reporte PDF completo → requiere cuenta gratis en univercityaiconsult.tech
6. Usuario crea cuenta (OAuth 2.1 PKCE) → acceso limitado pero funcional
7. Con cuenta: reportes PDF, links compartibles, historial, benchmarks de industria
8. Cuando quiere EJECUCIÓN → CIA aparece como servicio natural
   └─ 100% credit bridge: audit $3K, si procede en 30 días → crédito total
   └─ 3-tier sandwich: Foundation/Growth⭐/Enterprise
9. Cada interacción genera market intelligence (NO se vende — trust layer)
```

---

## 3. INDUSTRIAS — Abierto a todos, profundo en 6

**El MCP no rechaza a nadie.** Un restaurante, un despacho de abogados, una ONG, una fábrica — todos reciben un audit de calidad con Triple Option. La diferencia es la profundidad.

### Tier 1 — 6 ICPs premium (pain language calibrado, benchmarks, pricing específico)

Seleccionados por data: los que mejor pagan, más necesitan, y más hay en LATAM. Cada ICP tiene su propio flujo de preguntas, pain language, y recomendaciones:

### ICP 1: Construcción & Real Estate (50-500 emp)
- **Pain:** "se nos pierden cotizaciones entre obras"
- **Foco MCP:** pipeline leakage, coordinación multi-obra, cotizaciones perdidas
- **Servicio CIA:** Revenue Leak Audit ($2K-$5K) → Predictable Revenue Architecture ($4K-$25K)
- **ROI hook:** "cada cotización perdida = $X en revenue leak"

### ICP 2: Clínicas Healthcare
- **Pain:** "agujero negro de citas"
- **Foco MCP:** no-shows, llamadas perdidas, ciclo de facturación
- **Servicio CIA:** Revenue Leak Audit → Agentic Strategy ($5K-$20K)
- **ROI hook:** "cada no-show = $Y perdido × Z pacientes/mes"

### ICP 3: Agencias Digitales (20-100p)
- **Pain:** "mis márgenes se los come ChatGPT"
- **Foco MCP:** commoditization fear, márgenes comprimidos, diferenciación
- **Servicio CIA:** Agentic Strategy → Living System Retainer ($500-$3K/mo)
- **ROI hook:** "automatizar deliverables repetitivos = +X% margen neto"

### ICP 4: E-commerce & Retail (mid-market)
- **Pain:** 70% cart abandonment, conversión stuck
- **Foco MCP:** abandono de carrito, conversión, customer journey roto
- **Servicio CIA:** Revenue Leak Audit → Predictable Revenue Architecture
- **ROI hook:** "reducir abandono 10% = $X/mes en revenue recuperado"

### ICP 5: Startups Funded (Series A-B, LATAM)
- **Pain:** "quemando runway, board pregunta por IA"
- **Foco MCP:** burn rate, board pressure, necesidad de mostrar AI traction
- **Servicio CIA:** Agentic Strategy → Living System Retainer
- **ROI hook:** "automatizar X proceso = Y meses extra de runway"

### ICP 6: Enterprise con Innovation Budget
- **Pain:** "purgatorio de PoC", "$200K PowerPoint de Big4"
- **Foco MCP:** PoC purgatory, ROI de innovación no demostrado
- **Servicio CIA:** Bespoke ($30K+) → Blockchain-Native Systems
- **ROI hook:** "salir del purgatorio de PoC en 90 días vs 18 meses"

### Tier 2 — Cualquier otra industria (abierto, genérico inteligente)

Restaurantes, despachos legales, manufactura, logística, educación, ONGs, agricultura, fitness, real estate residencial, contabilidad, seguros, turismo, salud mental... cualquiera.

Reciben:
- **Audit completo** con preguntas genéricas de automatización (no pain language calibrado)
- **Revenue Leak Map** basado en procesos universales (ventas, onboarding, facturación, comunicación)
- **Triple Option** completo (Paid/OSS/CIA) — la recomendación de herramientas funciona para todos
- **Roadmap 30/60/90** accionable
- **Value Ladder general** de CIA (sin pricing calibrado por industria)

Lo que NO reciben (hasta que se promuevan a Tier 1):
- Pain language específico de su industria
- Benchmarks de industria validados
- Pricing calibrado por vertical
- Objeciones y respuestas específicas de su sector

**Promoción automática:** cuando una industria Tier 2 acumula suficientes interacciones (umbral configurable), CIA la estudia, calibra pain language + pricing, y la promueve a Tier 1. El mercado le dice a CIA dónde profundizar.

---

## 4. SURFACE DE TOOLS (rediseñada)

### 4.1 `audit.start(lang?)` — FREE
Inicia sesión. Detecta industria del contexto conversacional del LLM.
- Si es Tier 1 (6 ICPs): preguntas con **pain language real** de Doc02.
- Si es Tier 2 (cualquier otra): preguntas genéricas inteligentes de automatización.
- Si no detecta industria: pregunta abierta, clasifica después.

### 4.2 `audit.respond(session_id, question_id, answer)` — FREE
Registra respuesta, devuelve siguiente pregunta.
Branching adaptativo: las preguntas cambian según ICP + respuestas previas.
5-7 preguntas, no más. Cada una con UI (slider/dropdown/multi-select/textarea).

### 4.3 `audit.estimate(session_id)` — FREE
Computa estimaciones basadas en:
- Benchmarks reales por ICP (no inventados)
- Value Ladder mapping: qué servicio de CIA aplica y a qué precio
- ROI estimado en lenguaje del ICP
- Mapa de fugas de revenue (Revenue Leak Map)

### 4.4 `audit.report(session_id, format)` — FREE (md/interactive) | REGISTRADO (pdf)
Genera reporte. Formatos:
- `md` / `interactive` → gratis, sin registro
- `pdf` → requiere cuenta en univercityaiconsult.tech (OAuth 2.1)

Estructura del reporte:
1. Executive summary con score + ahorro
2. Revenue Leak Map (las fugas reales del negocio)
3. Análisis por área con plan accionable
4. Roadmap 30/60/90 (con o sin CIA — honesto)
5. Comparativo antes/después
6. **Si fit ≥ 70%:** "CIA puede ejecutar esto. 100% credit bridge: audit $3K, credited if you proceed."
7. **Si fit < 70%:** recomendaciones honestas fuera de CIA. Credibilidad > venta.

### 4.5 `audit.book_call(session_id, contact)` — REGISTRADO
Lead capture con consentimiento explícito.
Forward a: Google Sheets Pipeline Comercial + n8n + email David.
Pre-call: el MCP ya hizo C, L, O del CLOSER (Doc01) — David entra en S, E, R.

### 4.6 `audit.share(session_id, kind)` — REGISTRADO
Link público 30 días para compartir con equipo. No indexable.

### 4.7 (v0.2) `audit.execute(session_id, milestone)` — PAGADO
Ejecución guiada de los primeros pasos del roadmap.
Aquí es donde el MCP ENTREGA valor real cuando le pagan.
Trackeado por milestones. Layer 1 verifica completitud.

---

## 5. FREEMIUM MODEL

### Tier FREE (sin registro)
- `audit.start`, `audit.respond`, `audit.estimate`, `audit.report(md|interactive)`
- Rate limit: 5 audits/IP/día
- Valor completo: diagnóstico + estimados + roadmap en markdown

### Tier REGISTERED (cuenta gratis en univercityaiconsult.tech)
- Todo FREE +
- `audit.report(pdf)` con marca CIA
- `audit.book_call` — agendar discovery
- `audit.share` — links compartibles
- Historial de audits
- Rate limit: 50/día

### Tier PAID (post-engagement)
- Todo REGISTERED +
- `audit.execute` — ejecución guiada
- Benchmarks detallados de industria
- Acceso a datos propios históricos

### Implementación técnica del gating
- **OAuth 2.1 Authorization Code + PKCE** para registro en univercityaiconsult.tech
- **JWT con `sub` claim** para identificar usuario across sesiones
- **Scopes en JWT:** `audit:free` (default), `audit:registered`, `audit:paid`
- **401 challenge con `WWW-Authenticate`** cuando tool requiere scope superior
- El LLM muestra al usuario: "Para el PDF, crea una cuenta gratis en univercityaiconsult.tech"

---

## 6. ANTI-RESELLER (Cap/Protección)

Problema: consultores que usen univercity-mcp para vender los servicios de CIA como propios.

Solución multi-capa:
1. **Email tracking:** JWT sub = email → DB persiste historial por usuario
2. **IP tracking:** rate limit + detección de patrones (muchas audits distintas = posible reseller)
3. **Company clustering:** si múltiples audits del mismo dominio de email → flag para review
4. **Watermark en PDFs:** metadata con session_id + usuario que generó
5. **Terms of Service:** uso comercial del output requiere atribución a CIA

---

## 7. DISCOVERABILITY (el nuevo SEO)

### 7.1 MCP Registry (registry.modelcontextprotocol.io)
- PR a GitHub con listing
- Instructions del server deben incluir: "Use this when a business wants to automate operations, diagnose revenue leaks, or assess AI readiness"
- Categoría: Business / Consulting / Automation

### 7.2 Smithery
- Auto-indexa desde Registry
- Hosted endpoint disponible (considerar para v0.2)

### 7.3 .well-known/mcp.json en univercityaiconsult.tech
```json
{
  "name": "univercity-mcp",
  "description": "Business automation diagnosis and revenue leak mapping by CIA",
  "url": "https://univercityaiconsult.tech/mcp",
  "transport": "streamable-http",
  "auth": { "type": "oauth2" }
}
```
LLMs que soportan SEP-1649/1960 descubren automáticamente.

### 7.4 Desktop Extensions (.mcpb)
- Package para Claude Desktop
- Instalable con un click

### 7.5 Instructions del MCP (crítico para discoverability)
Siguiendo Vincent McLeese: el LLM debe saber CUÁNDO usar este MCP.
```
"UniverCity MCP — Expert business automation diagnosis for ANY industry, by CIA (Consultoría de Inteligencia Aplicada).
Use this when:
- ANY business asks about automating operations or processes
- Someone wants to know their automation readiness score
- A company wants to identify revenue leaks from manual processes
- A business owner wants to know what software tools they need (paid AND free)
- A startup needs to show AI traction to their board
- Anyone in any industry says 'I want to automate/improve my business'
- Someone asks 'what tools should I use for my business'

Works for ALL industries. Deep expertise in construction, healthcare, digital agencies,
e-commerce, funded startups, and enterprise — but serves restaurants, law firms,
manufacturing, NGOs, agriculture, fitness, education, and any other business.

The LLM cannot replicate this because:
- Triple Option on every recommendation: best paid tool + best open-source alternative + CIA integration
- Proprietary Revenue Leak Mapping methodology tested across industries
- Continuously tested toolstack comparisons (CIA tests both paid and OSS monthly)
- Deep benchmarks in 6 verticals, growing based on market demand
- Integration with CIA's execution capabilities for implementation"
```

---

## 8. ARQUITECTURA TÉCNICA

### Stack (consistente con Layer 1)
- **Python 3.12** + **FastMCP** (mcp SDK)
- **Transport:** streamable-http (público) + stdio (dev local)
- **Auth:** OAuth 2.1 PKCE → JWT
- **Storage:** PostgreSQL `kairos` DB (sessions, users, reports)
- **Reports:** Jinja2 templates + Pandoc (md→pdf) o WeasyPrint
- **Lead capture:** webhook → n8n → Sheets Pipeline Comercial + email
- **i18n:** ES/EN con gettext
- **LLM para reports:** kairos-primary (MiniMax-M2.7) vía LiteLLM :4000

### Estructura del repo
```
mcp-servers/univercity-mcp/
  pyproject.toml
  README.md
  CHANGELOG.md
  PLAN.md                    ← este archivo
  reference/                 ← Doc01-05 (ya copiados)
  src/univercity_mcp/
    __init__.py
    server.py                # FastMCP entry + tool registration
    config.py                # frozen dataclass Config from env vars
    tools/
      start.py               # audit.start
      respond.py             # audit.respond
      estimate.py            # audit.estimate
      report.py              # audit.report
      book_call.py           # audit.book_call
      share.py               # audit.share
    domain/
      icps.py                # 6 ICPs con pain language, pricing, objections
      questions.py           # banco de preguntas adaptativas por ICP
      scoring.py             # Revenue Leak Score + fit score
      value_ladder.py        # mapeo a servicios reales + pricing
      closer.py              # C.L.O.S.E.R. pre-qualification automática
      objections.py          # 9 objections con A.A.A. technique (Doc03)
      toolstack.py           # 10 MCPs pagados + alternativas OSS por ICP
      toolstack_compare.py   # tablas triple option (Paid/OSS/CIA)
    reports/
      templates/             # Jinja2 templates ES/EN
      renderer.py            # Pandoc/WeasyPrint wrapper
    storage/
      sessions.py            # PostgreSQL ORM (sessions, answers, scores)
      users.py               # user accounts, tiers, history
    auth/
      oauth.py               # OAuth 2.1 PKCE flow
      jwt.py                 # JWT generation/validation, scope gating
    integrations/
      lead_forward.py        # Sheets + n8n + email
      lightrag.py            # benchmarks de industria
    i18n/
      es.po                  # traducciones español
      en.po                  # traducciones inglés
  tests/
    test_icps.py
    test_questions.py
    test_scoring.py
    test_value_ladder.py
    test_e2e.py
  deployment/
    univercity-mcp.service   # systemd unit
    nginx-public.conf        # reverse proxy
```

### Port: 3792 (consistente con spec original)

### Config pattern (igual que Layer 1)
```python
@dataclass(frozen=True)
class Config:
    transport: str = "stdio"
    http_host: str = "0.0.0.0"       # público, no 127.0.0.1
    http_port: int = 3792
    db_url: str = ""                  # PostgreSQL connection string
    oauth_issuer: str = ""            # univercityaiconsult.tech
    oauth_client_id: str = ""
    jwt_secret: str = ""
    litellm_url: str = "http://127.0.0.1:4000"
    n8n_webhook_url: str = ""
    sheets_pipeline_id: str = "1kLqINL3W_SZ1_XLAbpZVGkzIn-Mjo5EkWtenu5uusF4"
    david_email: str = "lopezdsteban@gmail.com"
    rate_limit_free: int = 5          # audits/IP/día
    rate_limit_registered: int = 50
    report_storage: str = "/var/lib/univercity-mcp/reports"
```

---

## 9. SALES KNOWLEDGE EMBEDIDO (Doc01-05)

El MCP no solo diagnostica — tiene el DNA de ventas de CIA:

### Del CLOSER Script (Doc01)
- **C (Clarify):** `audit.start` + `audit.respond` = las preguntas
- **L (Label):** `audit.estimate` clasifica el problema del usuario
- **O (Overview):** preguntas sobre intentos previos ("¿has intentado automatizar antes?")
- **S (Sell the vacation):** `audit.report` muestra el "después" — no las features de CIA
- **E (Explain objections):** Doc03 embedido — 9 objections con scripts A.A.A.
- **R (Reinforce):** `audit.book_call` con prueba social (McCann, Bancolombia, Colliers)

### Del Value Ladder (Doc05)
- **Founders Tier:** 30-40% off para primeros 5 clientes (config flag)
- **100% Credit Bridge:** el audit de $3K se acredita si proceden en 30 días
- **3-Tier Sandwich:** siempre mostrar Foundation/Growth⭐/Enterprise
- **10× Value Rule:** si el ahorro estimado es $28K/año, el servicio de $3K es 9.3× ROI

### De la Objection Bible (Doc03)
Las 9 objeciones más comunes con respuesta A.A.A. (Acknowledge-Associate-Ask):
1. "Necesito pensarlo" → "Totalmente, ¿qué específicamente te gustaría evaluar?"
2. "Muy caro" → 10× value reframe
3. "Necesito aprobación del socio" → 3-way meeting offer
4. "Ya probamos IA" → "¿Qué fue diferente? Muchos clientes vienen de malas experiencias"
5. "No hay presupuesto" → "¿Y si el audit se paga solo en 30 días?"
6. "Mándame propuesta" → "Claro, pero antes — ¿qué necesitas ver para decidir?"
7. "¿Garantía?" → milestone-based payment + Layer 1 verification
8. "¿Por qué no Accenture?" → speed + cost + results comparison
9. "Estoy muy ocupado" → "Exactamente — por eso necesitas automatizar"

Estas respuestas se usan en `audit.report` cuando hay objeciones implícitas en las respuestas del usuario.

---

## 10. TRIPLE OPTION MODEL — Paid / Open Source / CIA

### La diferenciación más fuerte del producto

Cada recomendación del audit presenta 3 caminos. No 1. No 2. Tres:

| Columna | Qué es | Quién paga | Ejemplo |
|---------|--------|-----------|---------|
| **A. Pagado** | La mejor herramienta comercial para ese problema | El cliente | Calendly $16/mo |
| **B. Open Source** | La mejor alternativa gratuita, probada por CIA | El cliente (gratis) | Cal.com self-hosted $0 |
| **C. CIA** | Integración completa + configuración + workflows custom | El cliente paga a CIA | CIA configura todo + automations |

### Por qué esto destruye a la competencia

Accenture cobra $200K por un PowerPoint que recomienda Salesforce (porque son partners con comisión). McKinsey recomienda SAP porque tienen practice de implementación. Cada consultor del mundo tiene incentivo oculto para recomendar herramientas caras.

CIA llega y dice: "Salesforce cuesta $150/user/mes. Twenty CRM es open-source y hace el 75% por $0. Aquí tienes ambos comparados para TU caso. Nosotros ya probamos los dos. Tú decides."

Eso genera **confianza radical**. Si CIA recomienda lo gratis cuando lo gratis funciona, el cliente SABE que cuando CIA recomienda lo pagado, es porque realmente lo necesita. Y cuando el problema se pone complejo y elige la opción C — ya confía.

### Los 10 MCPs que cubren 80% de los 6 ICPs

Seleccionados por cobertura Pareto. CIA no paga ninguna licencia. El cliente usa su propia cuenta.

| # | MCP | Categoría | Precio | ICPs que cubre |
|---|-----|-----------|--------|----------------|
| 1 | **HubSpot** | CRM | Freemium | Constr, Health, Agency, Ecomm, Startup |
| 2 | **Stripe** | Pagos | Pay/use | Todos los 6 |
| 3 | **Make** (ex-Integromat) | Automatización | Freemium | Todos los 6 |
| 4 | **Process Street** | SOPs/Checklists | Paid | Constr, Health, Agency, Startup, Enterprise |
| 5 | **Slack** | Comunicación | Freemium | Agency, Ecomm, Startup, Enterprise |
| 6 | **Calendly** | Scheduling | Freemium | Constr, Health, Agency, Startup, Enterprise |
| 7 | **MailerLite** | Email marketing | Freemium | Constr, Health, Agency, Ecomm, Startup |
| 8 | **Ahrefs** | SEO/Analytics | Paid | Agency, Ecomm, Startup |
| 9 | **QuickBooks** | Contabilidad | Paid | Constr, Health, Agency, Ecomm, Startup |
| 10 | **DocuSign** | Contratos | Paid | Constr, Agency, Startup, Enterprise |

Cada uno con su alternativa open-source probada por CIA:

| Pagado | Open Source probado | Cobertura OSS |
|--------|-------------------|---------------|
| HubSpot | Twenty CRM | 70% |
| Stripe | (sin alternativa real — pero BTCPay para crypto) | N/A |
| Make | n8n (self-hosted) | 85% |
| Process Street | Checklist.gg / Markdown SOPs | 60% |
| Slack | Mattermost / Rocket.Chat | 80% |
| Calendly | Cal.com (self-host) | 80% |
| MailerLite | Listmonk (self-host) | 65% |
| Ahrefs | Plausible + Google Search Console | 50% |
| QuickBooks | Akaunting / ERPNext | 60% |
| DocuSign | DocuSeal (open-source) | 75% |

### El flywheel de testing continuo

1. **CIA prueba herramientas constantemente** — equipo interno usa y evalúa paid vs open-source cada mes. Datos reales de uso, no reviews de G2.
2. **El audit.report siempre tiene las 3 opciones actualizadas** — "Cal.com sacó v4.2 con MCP nativo → ahora cubre 90%, ya no necesitas Calendly." Valor que evoluciona.
3. **El retainer ($500-$3K/mo) se justifica solo** — "este mes te ahorramos $200/mo migrando de Calendly a Cal.com que ya probamos." El retainer se paga con los ahorros que genera.
4. **Data intelligence se enriquece** — CIA sabe cuáles herramientas REALMENTE funcionan por ICP, no por marketing, sino por uso real. Eso es IP que nadie más tiene.

### Cómo se implementa en el MCP

En `audit.report`, cada recomendación tiene esta estructura:

```
FUGA: "Ping-pong de citas — $1,200/mes en tiempo perdido"

  A. PAGADO: Calendly ($10-16/user/mo)
     - MCP nativo en Registry ✓
     - Setup: 15 min
     - Cubre: 95% del problema
     - Best for: equipos >5, multi-timezone

  B. OPEN SOURCE: Cal.com ($0 self-host / $12/mo cloud)
     - Probado por CIA: ene 2026
     - Setup: 30 min (cloud) / 2h (self-host)
     - Cubre: 80% del problema
     - Best for: equipos ≤5, cost-sensitive

  C. CIA LO HACE: Incluido en engagement ($4K-$25K)
     - Setup: 0 — CIA configura todo
     - + workflow automático post-booking
     - + nurture sequence + reminder AI
     - Cubre: 100% + lo que no sabías que necesitabas
```

### Archivos nuevos en el repo

```
src/univercity_mcp/
  domain/
    toolstack.py              # 10 MCPs pagados + alternativas OSS
    toolstack_comparisons.py  # tablas de comparación por ICP
    toolstack_updates.py      # tracking de versiones/cambios
```

---

## 10b. DATA INTELLIGENCE LAYER

Cada interacción con univercity-mcp genera datos valiosos:

- **Distribución de industrias** que buscan automatización
- **Pain points más frecuentes** por vertical
- **Budget ranges** reales del mercado
- **Conversion rates** por ICP (audit → book_call → engagement)
- **Preguntas que generan más engagement** (tiempo de respuesta)
- **Tool adoption rates** — qué herramientas eligen los clientes (A, B, o C) por ICP
- **OSS vs Paid preference** — correlación con tamaño de empresa y budget

**Trust layer:** "Tus datos son TUS datos. No vendemos datos de nuestros usuarios."

Esto se implementa como analytics internos, nunca expuestos externamente.
El valor para CIA: product-market fit en tiempo real, pricing calibration, ICP refinement, toolstack intelligence.

---

## 11. TIMELINE PARA AI SUMMIT (8 días)

### Día 1-2 (abr 29-30): Foundation
- [ ] Scaffold del repo (pyproject.toml, src/, tests/)
- [ ] `config.py` con frozen dataclass
- [ ] `server.py` con FastMCP + 6 tools registradas (stubs)
- [ ] `domain/icps.py` con los 6 ICPs completos (pain, pricing, objections)
- [ ] `domain/questions.py` con banco de preguntas adaptativas

### Día 3-4 (may 1-2): Core Logic
- [ ] `domain/scoring.py` — Revenue Leak Score calculation
- [ ] `domain/value_ladder.py` — mapping a servicios + pricing
- [ ] `tools/start.py` + `tools/respond.py` — flujo de preguntas funcional
- [ ] `tools/estimate.py` — cálculo de ahorro + fit score
- [ ] `storage/sessions.py` — PostgreSQL (o SQLite para dev local)

### Día 3-4 (may 1-2): Reports
- [ ] `reports/templates/` — Jinja2 templates ES/EN
- [ ] `reports/renderer.py` — md + pdf generation
- [ ] `tools/report.py` — genera reporte completo

### Día 5 (may 3): Integration
- [ ] `tools/book_call.py` + `integrations/lead_forward.py`
- [ ] `tools/share.py` — link compartible
- [ ] Rate limiting por IP
- [ ] i18n básico ES/EN

### Día 6 (may 4): Auth (puede ser post-Summit para v0.1)
- [ ] OAuth 2.1 flow con univercityaiconsult.tech (si hay tiempo)
- [ ] JWT scope gating
- [ ] Fallback: email-based registration simple para Summit

### Día 7 (may 5-6): Testing + Polish
- [ ] Tests unitarios (ICPs, scoring, value_ladder)
- [ ] Test e2e: sesión completa start→report en < 90s
- [ ] Demo script para AI Summit
- [ ] systemd service + nginx config (deploy a VPS)

### Día 8 (may 7): AI Summit
- [ ] Demo live: 5 empresas hacen audit → 5 reportes → ≥1 lead opt-in
- [ ] Recoger feedback real

### Post-Summit (v0.2)
- OAuth 2.1 completo si no se hizo
- Registry + Smithery publication
- .well-known/mcp.json en univercityaiconsult.tech
- `audit.execute` para ejecución guiada
- LightRAG benchmarks reales
- Dashboard analytics de interacciones

---

## 12. DECISIONES QUE DAVID DEBE TOMAR

Las 8 del §12 de la spec original siguen vigentes, más estas nuevas:

| # | Decisión | Recomendación | Impacto |
|---|----------|---------------|---------|
| 1 | ¿Marketplace público o privado para Summit? | Privado (link directo) → público post-Summit | Controla exposición inicial |
| 2 | ¿Subdomain? audit.univercityaiconsult.tech vs /audit | Subdomain — más limpio | DNS + cert |
| 3 | ¿LLM para reports? kairos-primary vs Claude | kairos-primary v0.1, A/B test v0.2 | Consistencia vs calidad |
| 4 | ¿Calendly o Cal.com para book_call? | Cal.com (open source) | Self-host futuro |
| 5 | ¿Auth para Summit? OAuth completo vs email simple | Email simple para Summit, OAuth post | Velocidad de build |
| 6 | ¿Founders Tier activo para Summit? | Sí, 30-40% off primeros 5 | Cierre en Summit |
| 7 | ¿Nombre en Registry? univercity-mcp vs cia-business-audit | univercity-mcp | Brand consistency |
| 8 | ¿Storage para Summit? PostgreSQL vs SQLite | SQLite local para Summit, PG post | Simplifica deploy |
| 9 | ¿El audit es gratis o el free tier tiene límite de detalle? | Gratis completo, PDF requiere cuenta | Maximiza valor percibido |
| 10 | ¿Voice demo en Summit? (Olivia lee el reporte) | Sí, como wow factor, no como MVP feature | Impresiona, no bloquea |

---

## 13. ACCEPTANCE CRITERIA (v0.1 Summit-ready)

1. Sesión completa (start → 6 respuestas → estimate → report) en < 90 segundos
2. Preguntas usan pain language REAL del ICP detectado
3. Estimados de ahorro son creíbles (basados en rangos reales de Doc02/05)
4. Reporte tiene valor INDEPENDIENTE de contratar a CIA
5. Report muestra Value Ladder con 3-tier sandwich cuando fit ≥ 70%
6. Report es honesto cuando fit < 70% — recomienda alternativas
7. ES y EN funcional
8. Rate limit funciona (6to audit/día → 429)
9. book_call llega a Pipeline Comercial Sheet en < 30s
10. Demo en Summit: 5 audits live → 5 reportes → ≥1 lead

---

## 14. FILOSOFÍA FUNDACIONAL

> "La MCP app de CIA realmente debe entregar cuando le pagan."
> — David Lopez, 2026.04.29

### El origen

David siempre supo qué necesitaba cada empresa. Miraba un negocio y podía decir: "aquí les falta X software, aquí hay un open-source que hace lo mismo gratis." Pero saber no es suficiente sin acción. Lo que cambió: integridad — profundidad conceptual + acción masiva, sin obsesionarse con resultados.

UniverCity MCP es esa habilidad empaquetada y escalada. Lo que David hacía en una conversación con un CEO, ahora lo hace el MCP con miles de empresas simultáneamente. Gratis. Con freemium cálido. Y con la capa CIA para quien quiere el traje a medida.

### El enfoque es social, humano, comunitario

Esto no es un SaaS que extrae valor. Es una herramienta que **hace que las empresas se vuelvan muy fáciles de mejorar** — o de matar si es necesario. Transparencia radical: "tu negocio tiene estas fugas, aquí están las herramientas gratuitas para taparlas, y si quieres que alguien lo haga por ti, aquí estamos."

Eso cambia el mercado porque:
- Democratiza el acceso a consultoría de calidad (antes costaba $200K de Big4)
- Muestra las opciones reales (pagadas Y gratuitas) sin comisiones ocultas
- Genera confianza radical — el usuario sabe que CIA no tiene incentivo para recomendar lo caro
- Crea comunidad: empresas que mejoraron con el audit gratis se vuelven evangelistas naturales

### Principios no negociables

1. **Valor real primero, monetización después.** El audit gratis debe ser tan bueno que el usuario se sienta en deuda moral.
2. **Honestidad sobre fit.** Si el negocio no encaja con CIA, decirlo. Recomendar alternativas. La credibilidad construye el funnel.
3. **Triple opción siempre.** Pagado / Open Source / CIA. El usuario decide. Nunca empujar una opción.
4. **Tus datos son TUS datos.** Market intelligence se genera internamente pero nunca se vende ni se expone. La confianza es el activo más valioso.
5. **Consciencia > crecimiento.** Escalar responsablemente. El enfoque es social, humano, natural, consciente. Growth que destruye confianza no es growth.
6. **Entregar cuando le pagan.** Si alguien paga, resultados trackeables. Constantemente. El ICP se ampliará — hay que estar preparados para ENTREGAR.
7. **Evolucionar con el mercado.** Testing continuo de herramientas. Lo que funciona hoy puede no funcionar mañana. CIA se mantiene al día para que el cliente no tenga que hacerlo.
