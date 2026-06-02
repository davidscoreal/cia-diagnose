# RESEARCH.md — de diagnósticos a papers (visión a 6-12 meses)

Meta interna de David: a lo largo de un semestre/año, acumular suficientes
diagnósticos para **publicar papers propios de CIA** sobre el estado real de las
PyMEs por industria y nicho, y tendencias en el tiempo. Este documento explica
cómo el sistema ya recolecta los datos para eso — de forma **anónima y ética**.

## El dataset

Cada `business_diagnose` se persiste (SQLite) y se emite por el webhook a todos
los sinks configurados. Si `CIA_VAULT_LEAD_LOG` apunta a un `.jsonl`, cada
diagnóstico queda como una línea con: `icp_id`, **`niche`** (nicho
hiper-específico, nuevo en v1.1.0), `health_score`, `pain_points`,
`decision_maker_role`, `top_actions`, el `diagnosis` completo (scores por las 11
dimensiones), `source`, `created_at`. Ese JSONL **es el dataset de investigación**.

## Nichos hiper-específicos + tendencias

- El campo `niche` permite ir más allá de las 9 industrias: "SaaS B2B para
  clínicas dentales", "construcción modular para retail", etc. Se captura tal
  cual y se agrega en tendencias. Así CIA entiende sub-verticales finos y detecta
  patrones (qué dimensiones fallan sistemáticamente en un nicho).
- Series de tiempo: `created_at` permite ver evolución mes a mes (¿mejora la
  salud digital de las agencias LATAM en 6 meses? ¿qué dolor crece?).

## Privacidad primero (condición para publicar)

`scripts/trends.py` produce **agregados anónimos**: elimina company_name,
contact_*, ip y session_id, y solo reporta distribuciones por industria/nicho/
dimensión y conteos de dolores. Los papers se construyen sobre estos agregados,
nunca sobre datos identificables. Los endpoints `/report` y `/export` llevan
`noindex/no-store` y los datos personales no se hornean en el paquete público.

## Flujo hacia un paper

1. **Recolectar** (activo): `CIA_VAULT_LEAD_LOG` → `.jsonl` en el vault.
2. **Agregar**: `python scripts/trends.py --log leads.jsonl --out trends.json`
   (o `--format csv`). Salida lista para pandas / NotebookLM / Tabularis.
3. **Analizar**: distribución de `health_score` por industria, dimensiones más
   débiles por nicho, dolores más frecuentes, tendencia mensual.
4. **Calibrar** (cruce con `EVOLUTION_PLAN.md`): los outcomes reales reajustan los
   benchmarks YAML — y de paso validan hipótesis para el paper.
5. **Publicar**: "Estado de la salud operativa de las PyMEs en LATAM por
   industria y nicho" — con N diagnósticos, metodología (11 dimensiones,
   triple opción), y hallazgos por sub-vertical.

## Umbrales sugeridos

- ≥ 50 diagnósticos con `outcome` etiquetado → primera calibración (EVOLUTION_PLAN).
- ≥ 200-300 diagnósticos por industria → tendencias mensuales con señal.
- ≥ 30-50 en un nicho → mini-reporte de nicho publicable.

## Acción inmediata
- [ ] Activar `CIA_VAULT_LEAD_LOG` en el deploy.
- [ ] Correr `scripts/trends.py` semanal (junto al refresh del registro de tools).
- [ ] Cuando haya volumen, abrir el notebook de análisis sobre `trends.json`.
