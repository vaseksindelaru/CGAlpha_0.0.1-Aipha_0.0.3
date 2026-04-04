# GUI — Control Room (cgalpha_v3)

## Propósito
Sala de control viva y nativa de CGAlpha v3. No es una herramienta externa: es parte del producto.
El usuario observa, interviene y decide desde esta interfaz desde el primer minuto.

## Paneles activos

| Panel | Descripción |
|-------|-------------|
| Mission Control | Estado global, fase actual, kill-switch, rollback |
| Market Live | Feed Binance + Data Quality status |
| Library — Lila | Estado de biblioteca, búsqueda, ficha e ingesta |
| Theory Live | Fuentes de decisiones clasificadas |
| Experiment Loop | Propuesta activa + métricas netas post-fricción |
| Risk Dashboard | Drawdown, circuit breakers, historial de incidentes |
| User Participation | Decisiones abiertas, interruptores, registro |

## Inputs / Outputs

- **Inputs:** eventos del sistema (via WebSocket o polling), usuario (clicks, formularios)
- **Outputs:** comandos al sistema (kill-switch, rollback, parámetros de riesgo), eventos en `memory/iterations/`

## Contratos

- `GET /api/status` → `gui_status_snapshot` JSON
- `POST /api/kill-switch/arm|confirm|reset` → flujo 2 pasos + rearme
- `GET /api/rollback/list` → snapshots disponibles
- `POST /api/rollback/restore` → restauración verificable por hash
- `GET /api/library/status` → snapshot de biblioteca Lila
- `GET /api/library/sources` → búsqueda/filtro de fuentes
- `GET /api/library/sources/<source_id>` → detalle de fuente
- `POST /api/library/ingest` → ingesta de fuente desde GUI
- `POST /api/library/claims/validate` → detección runtime `primary_source_gap`
- `GET /api/theory/live` → snapshot Theory Live (biblioteca + backlog adaptativo)
- `GET/POST /api/lila/backlog` → lista/creación de backlog adaptativo
- `POST /api/lila/backlog/<item_id>/resolve` → resolución de backlog item
- `GET /api/experiment/status` → estado del Experiment Loop
- `POST /api/experiment/propose` → proposal con fricciones por defecto activas
- `POST /api/experiment/run` → ejecución con walk-forward y no-leakage
- `GET /api/events` → stream de eventos (SSE o WebSocket)

## Dependencias

- Python ≥3.11
- `flask` o `fastapi` + `uvicorn`
- `python-socketio` o SSE para eventos en tiempo real
- Autenticación: token Bearer o usuario/contraseña (`.env`)

## Estado actual

🚧 FASE 0/1 — Mission Control + Market Live (mock) + Risk Dashboard operativos.
Library MVP de Lila conectado a backend (estado, búsqueda, ficha, ingesta y claim validation).
Theory Live conectado a snapshot real de Lila y backlog adaptativo.
Experiment Loop conectado a runner real con métricas netas post-fricción.

- Trazabilidad activa: cada ciclo mutante de control (`kill-switch`, `risk/params`) genera automáticamente
  `iteration_summary.md` + `iteration_status.json` en `memory/iterations/`.

## Próximo incremento

- Conectar feed Binance real (tras Data Quality Gates activos)
- Extender Theory Live con panel de contradicciones y puente hacia Experiment Loop
- Conectar Experiment Loop con dataset de mercado real y trazabilidad en knowledge_base/experiments

## Seguridad

⚠️ **NO exponer en red sin `AUTH_TOKEN` configurado en `.env`**
