# AUDIT.md — Estado actual de `cia-diagnose` (pre-boost v2)

> Auditoría hecha **antes de tocar nada**, sobre `main` (commit `68740c9`).
> Branch de trabajo: `boost/v2`. Fecha: 2026-06-02.
> Objetivo: entender el flujo completo y dejar por escrito qué funciona, qué está
> roto y qué falta, antes de implementar el boost.

---

## 1. Qué es y cómo está organizado

MCP server en Python (FastMCP del SDK `mcp>=1.0.0`). Paquete `cia_diagnose` bajo `src/`.

```
src/cia_diagnose/
├── server.py            (1208 líneas) — 9 tools MCP, entrypoint CLI, transporte
├── config.py            — Config dataclass + load_config() desde env vars CIA_*
├── domain/diagnosis/
│   ├── service.py       (973) — EL MOTOR: diagnose(), ICP detection, scoring, leak
│   ├── model.py         (273) — Dimension(11), Severity, Finding, DimensionScore,
│   │                            TripleOption, ValidationQuestion, DiagnosisReport
│   ├── benchmarks.py     — loader YAML con cache + fallback genérico
│   └── benchmarks/*.yaml — 9 industrias (construction, healthcare, agency,
│                           ecommerce, startup, enterprise, restaurant,
│                           real_estate, generic)
├── integrations/
│   ├── lead_forward.py   — fan-out a n8n + Telegram + vault log (jsonl)
│   ├── telegram_alerts.py— alerta "llamada caliente" (NO se usa en el flujo MCP)
│   └── i18n.py           — strings ES/EN estáticos (poco usados)
└── storage/sessions.py   — SQLite async (aiosqlite): sessions + rate_limits
```

Hay `_archive/` (v1 viejo) y varios `*.bak-*` **committeados dentro de `src/`** (basura que ensucia el paquete — ver §5).

---

## 2. El flujo real (de `business_diagnose` a la salida)

1. **`server.py::business_diagnose`** recibe ~22 parámetros sueltos (company_name,
   industry, team_size, software_detected, pain_points, …, `lang`).
2. Los parsea: strings separados por coma → listas (`_to_list`), arma un `context: dict`,
   quita vacíos.
3. **Rate limit**: `store.check_rate_limit(ip, cfg.rate_limit_free)` — pero `ip` está
   **hardcodeado a `"cli"`** (línea 226). En HTTP remoto **todos los clientes comparten
   el mismo bucket "cli"** → el límite de 5/día es global, no por usuario. ⚠️
4. Crea `session` en SQLite, incrementa rate limit.
5. **`service.py::diagnose(context)`** — el cerebro:
   - `_detect_icp` por industria → pain language → software → `generic`.
   - `load_benchmark(icp_id)` (YAML, cacheado).
   - Itera las 11 `Dimension`; para cada una con `weight>0`: `_score_dimension`
     (base_score + signals + findings por condición + ajustes por keywords de pain).
   - **Revenue Leak Score** = promedio ponderado de scores (0-100).
   - `_estimate_monthly_leak` (anual→mensual; bug 12x ya corregido el 2026-05-23).
   - `_generate_actions` → Top 5 `TripleOption` (paid/oss/cia desde el YAML).
   - `_generate_validation_questions` (2-3, prioriza dims con poca data + peso alto).
   - Summary bilingüe + leadership insight.
6. Persiste `score_breakdown` (el `to_dict()`) en la sesión, status=SCORED.
7. **`forward_lead`** (incondicional): n8n + Telegram + vault log.
8. Devuelve `report.to_dict()`.

Las otras 8 tools (`quick_scan`, `list_industries`, `tools_recommend`, `action_plan`,
`roi_projector`, `case_studies`, `contact_cia`, `export_report`) son **stateless** y
devuelven contenido estático/calculado en memoria. No tocan la sesión salvo
`export_report` (que intenta forward_lead — y está roto, ver §4).

---

## 3. Las preguntas que pediste, respondidas

**¿El webhook `CIA_N8N_WEBHOOK` está implementado o es variable vacía?**
→ **Implementado y funcional.** `lead_forward.forward_lead()` hace POST a `cfg.n8n_webhook_url`
si está configurada, y además dispara Telegram directo + escribe un jsonl en `vault_lead_log`.
Corre **incondicionalmente** en cada `business_diagnose` (parche 2026-05-23). Por defecto la
env var viene vacía → no falla, solo loguea. **PERO** el payload NO incluye lo que pediste en
la tarea 1: faltan `top_actions`, `pain_points`, `decision_maker_role`, el JSON completo del
diagnóstico, ni el campo `source: "mcp_remote"|"mcp_local"`. Ver tarea 1 del boost.

**¿Dónde se guarda la sesión?**
→ SQLite vía `aiosqlite`, ruta `cfg.db_path` (default `~/.cia-diagnose/sessions.db`).
Tablas: `sessions` (todo el breakdown como JSON en `score_breakdown`) y `rate_limits`.

**¿Cómo se construye el Revenue Leak Score?**
→ Promedio ponderado de los scores por dimensión (`weighted_score = score*weight`,
sumados y divididos por el peso total). Cada dimensión parte de `base_score` del YAML y se
ajusta por signals, findings y keywords de pain. Score alto = más fuga.

**¿De dónde salen los benchmarks?**
→ De los 9 YAML en `domain/diagnosis/benchmarks/`. "Agregar industria = agregar YAML".
Definen weights, signals, defaults (base_score), findings (con `action` = triple opción).

**¿Cómo funciona el server HTTP? ¿Qué endpoints tiene?**
→ Usa `FastMCP(...).run(transport="streamable-http"|"sse"|"stdio")`. **NO hay endpoints
HTTP custom.** Solo expone el endpoint MCP estándar (`/mcp` para streamable-http). **No existe
`/report/{id}` ni `/export/{id}`** — las tareas 4 y 9 requieren añadir rutas custom
(FastMCP permite `@app.custom_route(...)` / montar Starlette). Hay que verificarlo al implementar.

**¿Hay generación de reportes / HTML?**
→ **No.** `jinja2` está en `dependencies` de `pyproject.toml` pero **no se usa en ningún lado**
(grep vacío). `export_report` devuelve un dict estructurado para que el LLM lo formatee, nada más.
No hay HTML, ni D3, ni gauge. La tarea 4 es 100% nueva.

---

## 4. 🔴 Bugs y bloqueadores (orden de gravedad)

| # | Severidad | Hallazgo |
|---|-----------|----------|
| B1 | 🔴 BLOQUEANTE GTM | **`pip install cia-diagnose` da 404 — el paquete NO está en PyPI.** Solo existe `univercity-mcp` (v0.2.1) publicado. TODO el prompt de prospecto de la tarea 2 (`pip install cia-diagnose`) **falla hoy**. Hay que publicar `cia-diagnose` en PyPI (release → workflow `publish.yml` ya existe) o el go-to-market no funciona. Necesita tu acción (credenciales/release PyPI). |
| B2 | 🔴 | **`export_report` pasa `session=None` a `forward_lead`**, que de inmediato hace `session.id`, `session.company_name`, etc. → `AttributeError`. Se traga en el `try/except` y loguea warning, pero **el lead de export NUNCA se captura**. La función `forward_lead` necesita aceptar `session=None`. |
| B3 | 🟠 | **Rate limit usa `ip="cli"` hardcodeado.** En HTTP remoto el límite de 5/día es **global compartido**, no por cliente. Un prospecto consume el cupo de todos. Hay que sacar la IP real del request en modo HTTP. |
| B4 | 🟠 | **URL de Cal.com inconsistente y errónea.** El código usa `https://cal.com/cia-consulting` (server.py:1037, 1136). Tú indicas `https://cal.com/cia-consultoria`. Difieren. Hay que unificar a la correcta. |
| B5 | 🟠 | **`DiagnosisReport.version = "0.2.0"`** hardcodeado (model.py:238) mientras `SERVER_VERSION="1.0.0"`. La salida reporta versión vieja. |
| B6 | 🟠 | **Semántica del score contradictoria.** El motor trata `revenue_leak_score` alto = **más fuga (peor)** (`model.py` "Higher = more leakage", `_categorize_leak`: ≥80 critical). Pero `roi_projector` (`leak_pct=(100-score)/200`) y `export_report` (score<30 "crisis", >90 "excelente") tratan score alto = **mejor**. Hay que decidir la dirección canónica. (No lo "arreglé" para no romper tu modelo mental; el reporte HTML sigue al motor vía `leak_category`.) |

---

## 5. 🟡 Inconsistencias / deuda (no rompen, pero confunden)

- **`server.json`** quedó en branding viejo: `name: univercity-mcp`, `version: 0.2.1`,
  repo `github.com/davidscoreal/univercity-mcp`, remote `mcp.univercityaiconsult.tech`,
  package PyPI `univercity-mcp`. Desalineado con `pyproject` (`cia-diagnose` v1.0.0).
- **`README.md`** desactualizado: título "v0.2.1"; sección "11 Dimensions" lista 8 nombres
  viejos en inglés (`digital, operations, supply_chain, talent, financial, leadership,
  market, regulatory`) — NO son las 11 dimensiones reales (en español). La tabla de tools
  solo muestra 2 de las 9. No tiene el prompt simple de prospecto (tarea 2).
- **`.well-known/mcp.json`** está **vacío** (0 bytes).
- **Licencia contradictoria**: `pyproject.toml` dice `MIT`; `README.md` dice "Proprietary".
- **Archivos `.bak-*` committeados dentro de `src/`** (`config.py.bak-…`, `service.py.bak-…`,
  `server.py.bak-…`, `lead_forward.py.bak-…`) → se empaquetarían en el wheel. Borrar.
- **`telegram_alerts.py`** usa env vars `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` (sin prefijo
  `CIA_`) y no se invoca desde el flujo. Código muerto o a re-cablear.
- **`i18n.py`** apenas se usa; el server tiene los textos inline (`*_es`/`*_en`).
- **`__init__.py`** docstring dice "for ANY industry" — ok, pero la versión vive en 4 sitios
  distintos (`__init__`=1.0.0, `pyproject`=1.0.0, `server.py SERVER_VERSION`=1.0.0,
  `model.py`=0.2.0, `server.json`=0.2.1, `README`=0.2.1). **Fuente única de verdad pendiente.**
- **`contact_cia.whatsapp = "+57 300 000 0000"`** es placeholder.
- **Branding**: no existe carpeta `brand/` ni logos (tarea inicial del prompt).
- Web referida como `univercityaiconsult.tech` (sin `www`); tú usas `www.` — unificar.

---

## 6. Tests y build

- `tests/test_v2.py` (472 líneas) cubre bien el **motor** (benchmarks, ICP, scoring, leak,
  diagnosis e2e, serialización, edge cases). **No** cubre: tools del server (todas), webhook,
  rate limit, ni nada HTTP. `conftest.py` presente.
- No pude correr la suite todavía (requiere instalar deps: `mcp`, `aiosqlite`, `pyyaml`, `httpx`,
  `jinja2`). Pendiente: crear venv y correr `pytest` como baseline antes de cambiar nada.
- `pyproject` declara entrypoint `cia-diagnose = cia_diagnose.server:main`. `requires-python>=3.10`
  (este Mac tiene system Python 3.9.6 → hay que usar un venv 3.10+ o `uv`).

---

## 7. Mapa tarea-del-boost → estado actual

| Tarea boost | Estado hoy | Esfuerzo |
|-------------|-----------|----------|
| 0. Logos en `brand/` clickeables → web | No existe `brand/` | Nuevo |
| 1. Webhook captura leads | Existe pero payload incompleto + bug B2 + sin `source` | Ampliar |
| 2. Prompt simple prospecto (`pip install`) | **Bloqueado por B1 (no está en PyPI)** + falta en README | Crítico |
| 3. Branding en output del diagnóstico | Parcial (contact_cia tiene links); falta firma consistente en `business_diagnose`/export | Medio |
| 4. Reporte HTML visual (`/report/{id}`) | **No existe** (sin HTML, sin rutas HTTP) | Grande/nuevo |
| 5. PocketBase vs SQLite | SQLite hoy; decisión a documentar en DECISION.md | Doc |
| 6. Dub links cortos | No existe; evaluar en DECISION.md | Doc |
| 7. Integración call.md | No existe; plan en INTEGRATION_GUIDE.md | Doc |
| 8. Evolver auto-evolución benchmarks | No existe; plan en EVOLUTION_PLAN.md | Doc |
| 9. Export CSV/JSON (`/export/{id}`) | **No existe** (sin rutas HTTP) | Grande/nuevo |

---

## 8. Recomendación de orden (respetando tu prioridad)

1. **Baseline**: venv 3.10+, instalar deps, correr `pytest` → confirmar verde antes de tocar.
2. **B1 (PyPI)**: decisión tuya — publicar `cia-diagnose`. Sin esto la tarea 2 es humo.
3. Tarea 1 (webhook completo + fix B2) — bajo riesgo, alto valor.
4. Tarea 2 (prompt simple en README) — depende de B1.
5. Tarea 3 (branding output) — barato.
6. Limpieza §5 (server.json, README, .bak, versión única, licencia).
7. Tarea 4 (HTML `/report`) y 9 (`/export`) — requieren capa HTTP custom; agrupar.
8. Tareas 5-8: documentos de decisión/plan (DECISION.md, INTEGRATION_GUIDE.md, EVOLUTION_PLAN.md).

> Nada de lo anterior se ha modificado aún. Este archivo es solo la foto del estado actual.
