# Domain — cgalpha_v3

## Propósito
Capa de dominio puro de CGAlpha v3. No depende de infraestructura ni de frameworks externos.
Define los modelos de negocio y los puertos (interfaces) que la aplicación necesita.

## Inputs / Outputs

- **Inputs:** datos en bruto de adaptadores, comandos de la capa de aplicación
- **Outputs:** modelos de dominio tipados, validaciones de invariantes de negocio

## Contratos

- `Signal`: señal de trading con `approach_type` obligatorio (Sección O)
- `Proposal`: propuesta de cambio con `risk_assessment` obligatorio (Sección M)
- `MemoryEntry`: entrada del sistema de memoria con nivel 0a-4 (Sección D)
- `DataPort`: interfaz para obtener datos de mercado
- `RiskPort`: interfaz para evaluar y aplicar reglas de riesgo
- `LibraryPort`: interfaz para consultar la biblioteca de Lila

## Dependencias

Solo librería estándar de Python + `dataclasses` + `typing`.

## Estado actual

🚧 FASE 0 — modelos base definidos, puertos esbozados.

## Próximo incremento

- Implementar validaciones de invariantes (signal quality score, approach_type enum)
- Conectar `MemoryEntry` con tabla de transiciones de niveles
