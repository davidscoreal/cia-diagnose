# TOOLS_REGISTRY.md — "lo mejor de lo mejor" por área e industria

David preguntó: *"sobre las opciones pagas y open source... ¿cómo encuentra lo
mejor de lo mejor? ¿buenas preguntas y buena búsqueda? además de tener lista
propia nuestra por área que se actualiza semanalmente."* — Aquí está el diseño.

## Cómo se eligen las herramientas (honesto)

El MCP es **determinista**: NO hace búsqueda web en vivo en cada llamada (sería
lento y no reproducible). En su lugar, las recomendaciones salen de una **lista
curada por CIA**, versionada en el repo:

```
src/cia_diagnose/tools_registry/
├── areas.yaml                 # default: mejor free/OSS/paga por área (11 áreas)
└── by_industry/
    └── construction.yaml      # overrides específicos por ICP (ej. Procore)
```

Cada entrada lleva **procedencia**:
- `tier`: free | oss | paid
- `why_best_es` / `why_best_en`: por qué CIA la eligió
- `last_reviewed` (a nivel de archivo): cuándo se revisó por última vez

La selección es por **área** y, cuando existe, por **industria** (override). El
loader (`tools_registry/__init__.py`) toma el override del ICP si existe, si no
el default del área. Esto alimenta tanto `tools_recommend` como las opciones
paga/OSS del **Triple Option** y de `action_plan`.

### ¿Entonces qué hace "lo mejor"?
Curación humana de CIA basada en implementaciones reales — no "lo más popular".
La búsqueda y las "buenas preguntas" entran en el **refresh semanal**, no en
tiempo de llamada.

## Refresh semanal

`scripts/refresh_tools.py` es el andamiaje del proceso:
1. **Valida** el registro (campos requeridos, tiers correctos).
2. **Marca como stale** los archivos cuyo `last_reviewed` supera la cadencia.
3. Reporta qué refrescar — el humano (o un agente LLM con WebSearch) investiga y
   actualiza los YAML: mete ganadores nuevos, saca obsoletos, refresca `why_best`
   y sube `last_reviewed`. Commit con fecha → auditable.

```bash
python scripts/refresh_tools.py --stale-days 7 --today 2026-06-09
```

### Automatización futura (opcional)
Un cron semanal en el VPS de David puede:
- Correr `refresh_tools.py` para detectar stale.
- Lanzar un agente con WebSearch que proponga cambios por área/industria
  (GitHub stars/actividad, releases recientes, pricing, deprecaciones).
- Abrir un PR con los cambios para revisión humana (mantiene la curación).

## Agregar industria o área
- Nueva industria: crear `by_industry/<icp>.yaml` con solo las áreas a
  especializar (lo demás cae al default). El `<icp>` debe coincidir con el id de
  `domain/diagnosis/benchmarks/<icp>.yaml`.
- Nueva área: agregarla en `areas.yaml` (y, si aplica, como dimensión del motor).

## Conexión con el diagnóstico
Cuando el negocio está sano (`growth_mode`), `tools_recommend` sigue aportando
valor: muestra las 3 opciones (free/OSS/paga) + la opción CIA basada en productos
reales de https://www.univercityaiconsult.tech/ — y el lead se sigue capturando.
