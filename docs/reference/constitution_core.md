# Constitution Core (Operativo)

Este archivo resume la parte operativa no negociable de la constitución para uso diario.

## 1. Principio Rector

- Evolución incremental, nunca reescritura destructiva.
- Primero estabilidad (`tests` + seguridad), luego nuevas capacidades.

## 2. Separación de Roles

- **Aipha (Cuerpo):** ejecución robusta.
- **CGAlpha (Cerebro):** análisis causal y estrategia.

No mezclar responsabilidades sin puente explícito (`bridge` y gates).

## 3. Memoria y Trazabilidad

- `aipha_memory/operational/`: operación diaria.
- `aipha_memory/evolutionary/`: aprendizaje y evidencia causal.

Toda decisión relevante debe quedar trazable.

## 4. Seguridad de Cambios de Código

- Sin escrituras fuera de scope del repo.
- Validación obligatoria antes de aplicar cambios.
- Rollback obligatorio cuando falla validación.
- No saltar barreras de test/regresión.

## 5. Política de Ejecución

- Sin pasar a Live/Hybrid si no hay calidad de datos y causalidad suficiente.
- En duda: `HOLD`, no `PROCEED`.

Ver gates exactos en `docs/reference/gates.md`.

## 6. Política de Documentación

- Documentación canónica en `docs/`.
- Históricos en `docs/archive/`.
- Evitar duplicación: una fuente operativa por tema.

## 7. Política de Versiones

- Estado oficial de versiones en `VERSION.md`.
- No declarar versiones en múltiples archivos sin sincronización.
