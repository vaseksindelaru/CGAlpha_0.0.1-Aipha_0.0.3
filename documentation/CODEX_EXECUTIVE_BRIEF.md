# Codex Executive Brief

## 1. Problema y Tesis
El principal riesgo de un sistema autónomo no es la lentitud, sino la amnesia operativa.
Sin memoria ejecutable, los errores históricos regresan en forma de regresiones.

## 2. Solución
Codex actúa como memoria constitucional de CGAlpha.
El Kernel (`codex_kernel.py`) valida entradas antes de persistirlas.

Invariantes clave:
- Inmutabilidad histórica
- Blindaje canónico de IDs críticos
- Esquema v4 obligatorio con contexto de inyección (`harness_inject_when`)

## 3. Método de Implementación
Orden de despliegue:
1. Tests de integridad
2. Seeding fundacional (Decisiones/Bugs)
3. Seeding de Lecciones
4. Seeding de Features y Reglas operativas

Regla de verdad técnica:
- Si una regla no tiene evidencia en código, no puede declararse como activa.

## 4. Integración Operativa (Harness)
El Harness construye un `World Model Packet` por tarea.
Este packet transforma memoria estática en restricciones activas para el agente.

Semántica:
- Prohibido: acción no permitida por política
- Inalcanzable: acción removida del espacio de decisión

## 5. Criterios de Éxito (Go/No-Go)
- 100% de entradas nuevas validadas por Kernel + tests
- 0 mutaciones históricas ilegales aceptadas
- 100% de reglas críticas con evidencia verificable
- Registro de inyección del Harness por ejecución

## 6. Impacto Esperado
CGAlpha pasa de “acumular cambios” a “acumular criterio verificable”.
La continuidad técnica deja de depender de memoria humana y pasa a ser auditable por diseño.
