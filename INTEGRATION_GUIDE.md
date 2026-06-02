# INTEGRATION_GUIDE.md — CIA Diagnose × call.md (tarea 7)

## Qué es call.md

App de escritorio (Electron + React 19 + TS, MCP SDK 1.0.0) que **graba llamadas con
transcripción en tiempo real** (audio dual-canal yo/ellos vía VideoDB por WebSocket) y corre
"agent loops" antes/durante/después de la llamada. Repo: `video-db/call.md`.

**Lo clave para nosotros:** call.md es a la vez **cliente y host de MCP**. En
*Settings → MCP Servers* se conectan servidores MCP (stdio local o HTTP remoto), y su
**"MCP agent" detecta automáticamente** durante la llamada cuándo hace falta una herramienta y
la dispara, mostrando el resultado inline. Además tiene **webhooks post-llamada** (n8n/Zapier/CRM).

## Por qué encaja con CIA Diagnose

CIA Diagnose **ya es un servidor MCP** con transporte stdio y streamable-http. No hay que
construir integración nueva: call.md lo consume tal cual. Durante la llamada de seguimiento,
mientras David habla con el prospecto, el agent de call.md puede llamar `quick_scan` →
`business_diagnose` → `roi_projector` y mostrar el **Revenue Leak Score en vivo**.

## Plan de integración (sin tocar el core del MCP)

### Opción A — Local (stdio), recomendada para empezar
David corre el MCP local y lo registra en call.md:
```json
// call.md → Settings → MCP Servers
{
  "cia-diagnose": { "command": "uvx", "args": ["cia-diagnose"] }
}
```
- Cero red, cero deploy. La sesión queda en el SQLite local de David.
- Al terminar la llamada, abre `/report/{session_id}`… pero en stdio no hay HTTP. Para ver el
  reporte HTML en vivo, usar la Opción B.

### Opción B — Remoto (streamable-http), para reporte visual en vivo
```json
{ "cia-diagnose": { "url": "https://audit.univercityaiconsult.tech/mcp" } }
```
- Durante la llamada, el agent corre `business_diagnose` → devuelve `session_id`.
- David abre **`https://audit.univercityaiconsult.tech/report/{session_id}`** en pantalla
  compartida: gauge + desglose + acciones, con el botón "Agenda con CIA". Cierre en vivo.
- `export` (`/export/{id}?format=csv`) para mandarle al prospecto sus datos.

### Flujo recomendado "llamada caliente"
1. **Antes:** call.md genera preguntas de prep desde el contexto del prospecto.
2. **Durante:** el agent dispara `quick_scan` con lo que se va diciendo → 3 dolores visibles.
   Cuando hay contexto suficiente → `business_diagnose` → Score en vivo.
3. **Pantalla:** abrir el reporte HTML (`/report/{id}`) y recorrer las 3 acciones triple-opción.
4. **Después:** webhook de call.md → n8n (mismo n8n que ya recibe `CIA_N8N_WEBHOOK`) para
   consolidar transcripción + diagnóstico en AXIS CRM. Nuestro webhook ya manda
   `pain_points`, `decision_maker_role`, `top_actions`, `revenue_leak_score`, `source` y el
   JSON completo — listo para cruzar con la transcripción.

## Qué falta (acción)
- [ ] Probar call.md con el MCP en stdio (Opción A) en una llamada de prueba.
- [ ] Confirmar que el deploy remoto `audit.univercityaiconsult.tech` sirve `/mcp` **y** las
      nuevas rutas `/report` `/export` (mismo proceso, mismo puerto).
- [ ] Opcional: que el webhook de call.md y el de CIA Diagnose escriban al **mismo** flujo n8n
      con un `correlation_id` (p.ej. el `session_id`) para unir llamada ↔ diagnóstico.

## Riesgos
- Servidores MCP autenticados pueden no estar disponibles en runs headless de call.md — el MCP
  de CIA es público (sin auth en `/report` `/export` `/healthz`), así que no aplica.
- `audit.univercityaiconsult.tech` debe exponer el puerto HTTP del MCP (3792) detrás de nginx.
  La conf `deployment/nginx-univercity.conf` apunta a esto — revisar que enrute `/mcp`, `/report`,
  `/export`, `/brand`, `/healthz`.
