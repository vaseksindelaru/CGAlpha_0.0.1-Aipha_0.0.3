# ADR-EVO-TICKET-0001-1 — Encoding Determinista

## Estado
**ACEPTADO** — 2026-06-21

## Contexto
Oracle v3 (`cgalpha_v3/lila/llm/oracle.py`) utiliza `sklearn.LabelEncoder` para
convertir categorías (regime, direction, delta_divergence) a valores numéricos.
`LabelEncoder` asigna valores basados en el orden de primera aparición en el set
de entrenamiento. Esto causa:

1. **Encoding Drift**: si el dataset cambia de orden o se agregan nuevas categorías,
   los valores numéricos cambian silenciosamente. Un modelo entrenado con
   LATERAL=0, TREND=1 puede recibir LATERAL=1, TREND=0 en un dataset posterior.

2. **No-reproducibilidad**: dos sesiones de entrenamiento con los mismos datos en
   diferente orden producen modelos con semántica diferente para los mismos inputs.

3. **Imposibilidad de verificar integridad**: sin un mapa estable, no se puede
   comparar si un modelo cargado desde disco usa el mismo encoding que el actual.

## Decisión
Reemplazar `sklearn.LabelEncoder` por un mapa determinista fijo (`ENCODING_MAPS`)
definido en `cgalpha_v4/oracle_v6_skeleton.py`.

```python
ENCODING_MAPS = {
    "regime": {"UNKNOWN": 0, "LATERAL": 1, "TREND": 2, "HIGH_VOL": 3},
    "direction": {"UNKNOWN": 0, "BULLISH": 1, "BEARISH": 2},
    "delta_divergence": {"UNKNOWN": 0, "NEUTRAL": 1, "BULLISH": 2, "BEARISH": 3},
}
```

### Propiedades del mapa:
- **UNKNOWN = 0** para toda categoría: fallback seguro para valores desconocidos.
- **Uppercasing** antes del lookup: "lateral" y "LATERAL" producen el mismo valor.
- **Inmutable tras D-008**: cambiar el mapa requiere un nuevo D-ID con evidencia.

## Alternativas consideradas

### A. `OrdinalEncoder` con categories explícitas
Técnicamente determinista pero agrega dependencia de sklearn, que es innecesaria
para 3 categorías con <5 valores cada una. Un diccionario es más rápido, más simple
de testear, y no requiere fit().

### B. One-hot encoding
Expande el vector de features de 7 a ~14 dimensiones. Con 94 samples en Set A,
esto empeora la ratio features/samples del RandomForest. Descartado por riesgo
de overfitting sin beneficio demostrado.

### C. Target encoding
Introduce data leakage en meta-labeling (el encoding depende del outcome que el
Oracle intenta predecir). Descartado por violación de causalidad.

## Consecuencias
1. **Positivas**:
   - Mismos inputs → mismos floats → mismos resultados. Siempre.
   - `save/load` ahora puede verificar integridad con checksum.
   - No depende de sklearn para encoding.
   - Testeable con 100% cobertura.

2. **Negativas/Trade-offs**:
   - Agregar una nueva categoría (ej: "COMPRESSION" en regime) requiere:
     (a) modificar ENCODING_MAPS,
     (b) nuevo D-ID revocando D-008,
     (c) re-entrenar todos los modelos con el nuevo mapa.
   - Esto es intencional: la estabilidad del encoding es más valiosa que la
     flexibilidad, dado el tamaño actual del dataset (94 FULL samples).

## Referencia
- EVO-TICKET-0001 (EXECUTING → MATURITY_5 pendiente)
- Nexus §3 — D-008 (nuevo, asignado en esta sesión)
- RECONSTRUCTION_BRIEF.md §2 — Issue #2 (LabelEncoder no-determinista)
