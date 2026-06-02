# EVOLUTION_PLAN.md — Auto-refinar benchmarks con Evolver (tarea 8)

## Qué es Evolver

`EvoMap/evolver`: motor de auto-evolución para agentes basado en **GEP (Genome Evolution
Protocol)**. Node.js 18+, JavaScript. En vez de modificar código, **analiza logs de runtime y
patrones de error y emite prompts estructurados** (Genes/Capsules) para guiar la siguiente
iteración, con audit trail (EvolutionEvents). Integra con Claude Code / Cursor / Codex.
Estado: core estable + features experimentales; **transicionando de open source a
source-available** (ojo licencia).

## El problema real que tenemos

Los benchmarks por industria (`benchmarks/*.yaml`) son **estimaciones calibradas a mano**:
`base_score`, `weight`, `score_boost`, severidades, condiciones de findings. No se ajustan con
datos reales. A medida que CIA hace diagnósticos y **cierra (o no) implementaciones**, deberíamos
saber qué dimensiones/findings predicen mejor la fuga real y la conversión, y recalibrar.

## ¿Evolver es la herramienta correcta? Veredicto: **todavía no.**

Evolver evoluciona **prompts de agentes**, no parámetros numéricos de un scorer determinista
basado en YAML. Nuestro motor (`service.py`) no es un agente LLM: es reglas + pesos. Meter
Evolver aquí sería forzar la herramienta. Además, "source-available" + experimental añade riesgo
de licencia/operación para un componente que tocaría el corazón del producto.

## Plan recomendado — calibración propia, ligera, en 3 fases

La infraestructura de datos **ya existe** gracias a boost/v2: cada diagnóstico se persiste en
SQLite (`score_breakdown`) y se emite por webhook con el JSON completo. Eso es el dataset.

### Fase 1 — Recolectar (ya listo, solo activar)
- Configurar `CIA_VAULT_LEAD_LOG` → un `.jsonl` append-only en el vault.
- Cada línea ya trae: `icp_id`, `revenue_leak_score`, `pain_points`, `decision_maker_role`,
  `top_actions`, `diagnosis` completo, `source`, timestamp.
- Añadir manualmente el **outcome** por sesión: ¿agendó? ¿cerró implementación? ¿monto?
  (columna en AXIS CRM, cruzada por `session_id`).

### Fase 2 — Analizar (script offline, sin tocar el server)
- Notebook/script que lea el `.jsonl` + outcomes y mida:
  - Correlación dimensión→conversión (¿qué dims con score alto predicen cierre?).
  - Findings que más aparecen en clientes que cerraron vs. los que no.
  - Calibración del `_estimate_monthly_leak` vs. fuga real reportada en implementaciones.
- Salida: propuestas de ajuste de `weight`/`base_score`/severidad por ICP.

### Fase 3 — Recalibrar (versionado, auditable)
- Aplicar ajustes a los `*.yaml` con un commit por ronda (el YAML ya es la fuente — "agregar
  industria = agregar YAML"; recalibrar = editar YAML).
- Test de regresión: un set fijo de contextos → snapshot de scores, para detectar cambios bruscos.
- Cron 1×/mes (David ya usa crones de auto-mejora en el VPS).

### ¿Dónde entra un LLM (o Evolver) después?
Cuando haya **volumen** (cientos de diagnósticos con outcome), se puede usar un LLM en Fase 2
para *proponer* nuevos findings/condiciones en lenguaje natural a partir de patrones, y — si se
quiere el marco GEP de Evolver — usarlo para versionar/auditar esas propuestas como Capsules.
Hasta entonces, **calibración estadística propia > motor de evolución de prompts.**

## Acción inmediata
- [ ] Activar `CIA_VAULT_LEAD_LOG` en el deploy.
- [ ] Añadir columna `outcome` + `session_id` en AXIS CRM.
- [ ] Crear `scripts/calibrate.py` (Fase 2) cuando haya ≥50 sesiones con outcome.
- [ ] Re-evaluar Evolver cuando su licencia se estabilice y tengamos volumen.
