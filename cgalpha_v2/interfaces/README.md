# cgalpha_v2/interfaces/

## Propósito
Capa de interfaces de usuario: GUI, CLI y API. Es el único punto de entrada humano o externo al sistema.
No contiene lógica de negocio; delega a `application/` para toda operación.

## Inputs / Outputs y contratos
- **Inputs:** acciones humanas (clic en GUI, comando CLI, request HTTP) o llamadas de sistemas externos
- **Outputs:** representaciones visuales o JSON del estado del sistema
- **Contrato:** interfaces NO importan directamente desde `domain/` ni `infrastructure/`. Solo de `application/`.

## Dependencias
- `cgalpha_v2/application/` — servicios de aplicación a orquestar
- Flask (GUI server, solo en entorno de desarrollo)

## Módulos activos (Fase 0)
| Módulo | Estado |
|--------|--------|
| `gui/` | ✅ Fase 0 — Control Room HTML + GUI Server |
| `cli/` | 🔲 Pendiente — migración de aiphalab/ |

## Estado actual
`EN CONSTRUCCIÓN` — módulo GUI implementado en Fase 0.

## Próximo incremento planificado
- `interfaces/cli/` — comandos alineados con GUI Control Room y Lila
- `interfaces/api/` — endpoints REST para integración externa
