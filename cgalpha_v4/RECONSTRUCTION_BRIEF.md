# CRB — Oracle v6
## cgAlpha_0.0.1 — Component Reconstruction Brief

### §1 — Propósito y lugar en el sistema
Meta-labeling. Predice si una señal ya detectada tendrá éxito (BOUNCE_STRONG/WEAK/BREAKOUT).
[TripleCoincidenceDetector] -> [Oracle] -> [ShadowTrader]

### §2 — Estado actual
- Cobertura de tests: 54.77% (v3)
- Tests pasando: N/A (v6 es reconstrucción)
- Issues conocidos:
    1. FEATURE_COLS usa nombres legacy (*_at_retest).
    2. LabelEncoder no-determinista (Encoding Drift).
    3. OracleRegressor_MAE con 0% cobertura.
    4. Métodos save/load/is_placeholder con 0% cobertura.

### §3 — Schema de interfaces (qué recibe, qué entrega)
- **Entrada (predict)**: `features_dict` (VWAP, OBI, Delta, ATR, Regime, Direction, Divergence).
- **Entrada (train)**: `List[ReentrySnapshot]` (Schema v2.0).
- **Salida**: `OraclePrediction` (trade_id, confidence, suggested_action, is_placeholder).

### §4 — Módulos protegidos dentro de este componente
- La lógica de **Meta-Labeling** (López de Prado) se mantiene como núcleo conceptual.
- El umbral de **0.70** para `EXECUTE` es una verdad inmutable (D-003).

### §5 — Deuda técnica conocida
- Acoplamiento excesivo con `pd.DataFrame` en la capa de predicción (latencia).
- Dependencia de `sklearn.LabelEncoder` que genera colisiones de categorías en updates parciales.

### §6 — Fases de reconstrucción
- **Fase A**: Reconstrucción determinista (Encoding manual + 100% coverage en save/load).
- **Fase B**: Integración con L2 Ring Buffer (features dinámicas).

### §7 — Criterios de éxito
- Cobertura de tests > 90% en `oracle_v6_skeleton.py`.
- Determinismo total en el encoding (mismos inputs -> mismos floats de entrada al modelo).
- Carga/Guarda funcional verificada con sumas de comprobación.

### §8 — Lo que NO se cambia en esta sesión
- No se cambia el modelo base (RandomForestClassifier).
- No se altera la lógica de `CalibratedClassifierCV`.
