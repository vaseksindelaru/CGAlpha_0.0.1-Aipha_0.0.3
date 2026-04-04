# cgalpha_v2/application/

## Propósito
Capa de aplicación (Use Cases / Application Services).
Orquesta el dominio sin contener lógica de negocio. Únicamente coordina puertos, servicios de dominio y adapters para satisfacer casos de uso concretos.

## Inputs / Outputs y contratos
- **Inputs:** comandos desde interfaces/ (CLI, GUI, API)
- **Outputs:** eventos de dominio, DTOs de respuesta, actualizaciones a puertos de infraestructura
- **Contrato:** un servicio de aplicación no debe importar directamente clases de infrastructure/

## Dependencias
- `cgalpha_v2/domain/` — modelos y puertos
- `cgalpha_v2/shared/` — tipos y excepciones comunes

## Estado actual
`EN CONSTRUCCIÓN` — carpeta vacía pendiente de migración de lógica de orquestación desde `core/orchestrator_hardened.py` y `cgalpha/orchestrator.py`.

## Próximo incremento planificado
- `application/change_proposer/service.py` — orquesta el loop de propuestas científicas
- `application/trading/service.py` — orquesta sesión de trading con Risk Management Layer
- `application/library/lila_service.py` — orquesta ingesta y búsqueda en biblioteca
