# DECISION.md — Evaluaciones de arquitectura (boost/v2)

Decisiones de "build vs adopt" pedidas en el boost. Cada una con recomendación
y razón. No se cambió nada de infraestructura todavía — son decisiones.

---

## Tarea 5 — PocketBase vs SQLite (almacenamiento de sesiones)

**Estado actual:** `aiosqlite` sobre un archivo SQLite (`~/.cia-diagnose/sessions.db`),
tablas `sessions` + `rate_limits`. El `score_breakdown` completo se guarda como JSON.

**PocketBase** (pocketbase.io): backend en **un solo binario Go** — SQLite embebido +
REST API + auth + suscripciones realtime + **dashboard admin web** + file storage. MIT.

### Análisis

| Criterio | SQLite actual | PocketBase |
|----------|---------------|------------|
| Dashboard sin código (lo que David quiere) | ❌ No | ✅ Admin UI lista |
| Proceso extra a operar | 0 (embebido en el MCP) | 1 binario/servicio aparte |
| Lenguaje | Python (mismo del MCP) | Go (binario externo, API HTTP) |
| Migración de datos | — | Re-escribir `storage/sessions.py` contra su REST/SDK |
| Realtime / auth | No necesario hoy | Incluido (no lo necesitamos aún) |
| Riesgo | Bajo (ya funciona) | Medio (acopla el MCP a otro servicio) |

### Recomendación: **NO migrar el MCP a PocketBase. Mantener SQLite.**

Razón: el MCP debe seguir siendo **un solo paquete `pip install` autocontenido** (clave para
la tarea 2: el prospecto lo corre con un `pip install`, sin levantar servicios). Acoplarlo a un
PocketBase externo rompe ese modelo y agrega operación.

**PERO** el dolor real de David es legítimo: **ver los diagnósticos sin código.** Eso ya está
resuelto mejor por dos caminos que NO requieren migrar:
1. **El webhook** (ya enriquecido en boost/v2) empuja cada diagnóstico a n8n → Google Sheets /
   AXIS CRM, que es el dashboard que David ya usa.
2. Los nuevos endpoints **`/report/{id}`** (HTML visual) y **`/export/{id}?format=csv|json`**.

**Opción futura si quiere un panel propio:** levantar **PocketBase como sink de solo-lectura**
(el webhook escribe una colección `diagnoses` en PocketBase y David usa su admin UI como
visor). Eso le da el dashboard sin acoplar el almacenamiento operativo del MCP. Es aditivo, no
una migración. Recomendado solo si Sheets/AXIS se queda corto.

---

## Tarea 6 — Dub para links cortos

**Dub** (github.com/dubinc/dub): gestión de links open-core (AGPLv3 + features enterprise en
`/ee`). Dominio propio, analytics (Tinybird), QR, API REST, conversion tracking. Cloud en dub.co
o self-host (Next.js + Prisma + PlanetScale).

### Análisis para CIA

Lo que aportaría: en vez de pegar `https://cal.com/david-cia/diagnostico-ai` crudo en
WhatsApp/reportes, usar `cia.link/diagnostico` con **analytics de clics** (cuántos prospectos
abren el link de agenda, desde dónde) y **QR** para material impreso.

| A favor | En contra |
|---------|-----------|
| Atribución real: ¿qué canal trae las citas? | Otra pieza self-host (Next+Prisma+PlanetScale) o costo cloud |
| QR para flyers/eventos | AGPLv3 en el core (cuidado si se modifica y redistribuye) |
| Dominio de marca corto | El MCP no necesita Dub para funcionar — es marketing, no producto |

### Recomendación: **Sí, pero como capa de marketing, NO dentro del MCP.**

- **Corto plazo:** usar **Dub Cloud (plan free)** con un dominio corto de CIA. Cero
  infraestructura. Acortar el link de Cal.com y los del reporte. Medir conversión.
- **No** hardcodear Dub en el código del MCP: `branding.py` debe seguir apuntando a las URLs
  canónicas (Cal.com real, web real). Si más adelante se quiere, se cambia **una constante** en
  `branding.py` por el short link — está centralizado justo para eso.
- Self-host solo si el volumen justifica salir de cloud.

---

> call.md (tarea 7) → ver `INTEGRATION_GUIDE.md`.
> Evolver (tarea 8) → ver `EVOLUTION_PLAN.md`.
> Tabularis (export CSV/JSON) → **ya implementado** en `/export/{id}` (tarea 9).
