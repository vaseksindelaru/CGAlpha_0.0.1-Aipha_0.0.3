# 🧬 Master Strategy: Triple Coincidence Detector v3
## **The Simple Foundation Strategy — Triple Coincidence Implementation (North Star v3.0)**

---

### **1. Introducción: De la Absorción Pasiva a la Triple Coincidencia**

La estrategia **Triple Coincidence (TC)** representa la evolución validada de la filosofía
"Simple Foundation" de CGAlpha v3. Mientras la versión anterior se basaba en un único patrón
de absorción, la TC detecta zonas de alta probabilidad mediante la **convergencia simultánea
de tres factores independientes**, luego monitorea esas zonas esperando un retest del precio
para capturar features de microestructura en el momento óptimo y entrenar el Oracle.

**Principio Fundamental:**
> Un evento de precio es significativo cuando tres señales independientes convergen.
> La detección es solo el primer paso; la verdadera información predictiva se captura
> EN el momento del retest, no en la detección de la zona.

---

### **2. Los Tres Pilares de Detección**

#### **2.1. Pilar I: Vela Clave (Key Candle)**
Detecta velas con comportamiento anómalo que indican actividad institucional.

- **Volumen Explosivo:** Volumen > Percentil `volume_percentile_threshold` (default: 70)
  de la ventana de lookback.
- **Cuerpo Comprimido:** El cuerpo de la vela representa < `body_percentage_threshold`%
  (default: 40) del rango total (High - Low).
- **Interpretación:** Alto volumen + cuerpo pequeño = fuerza institucional absorbida
  por órdenes pasivas. El mercado "lucha" pero no avanza.

```
Morphology Score = 1 - (body_ratio / body_threshold)
Volume Score = (volume - p_threshold) / (p_max - p_threshold)
Key Candle Score = 0.6 × Volume_Score + 0.4 × Morphology_Score
```

#### **2.2. Pilar II: Zona de Acumulación (Accumulation Zone)**
Detecta regiones donde el precio consolida con volumen elevado.

- **Rango Estrecho:** ATR local < `atr_multiplier` × ATR global (compresión de rango)
- **Volumen Elevado:** Volumen promedio de la zona > `volume_threshold` × volumen global
- **Mínimo de Barras:** La zona debe mantenerse al menos `min_zone_bars` velas

```
Zone Quality = weighted_average(range_compression, volume_ratio, duration_factor)
Threshold: quality_score > quality_threshold (default: 0.45)
```

#### **2.3. Pilar III: Mini-Tendencia (Mini-Trend via ZigZag)**
Confirma dirección mediante análisis de regresión lineal sobre pivots del ZigZag.

- **R² Mínimo:** La tendencia debe explicar > `r2_min` (default: 0.45) de la varianza
  del precio. Este umbral filtra ruido y solo acepta tendencias estadísticamente
  significativas.
- **Dirección:** La pendiente (slope) determina bullish/bearish.
- **Convergencia:** La tendencia debe apuntar HACIA la zona, no alejarse de ella.

```
trend_score = R² × direction_alignment × slope_normalized
```

---

### **3. El Score de Triple Coincidencia**

Cuando los tres pilares convergen en proximidad temporal (≤ `proximity_tolerance` velas):

```
BASE_SCORE (70%):
  Zone Component   (35%): quality_normalized
  Trend Component  (35%): R² × direction × slope
  Candle Component (30%): volume_score × morphology

ADVANCED_FACTORS (30%):
  Convergence (20%): spatial_proximity / temporal_proximity
  Reliability (15%): bonus si R² > 0.75
  Potential   (15%): estimated_move_vs_ATR
```

| Rango | Interpretación |
|-------|---------------|
| < 0.5 | ⚪ Débil — zona descartada |
| 0.5 – 0.6 | 🟡 Moderada — monitoring pasivo |
| 0.6 – 0.7 | 🟠 Fuerte — zona activa para retest |
| > 0.7 | 🟢 Muy fuerte — zona premium |

---

### **4. El Flujo Correcto: De la Detección al Oracle**

```
FASE 1: DETECCIÓN
━━━━━━━━━━━━━━━━━━
  Datos OHLCV + Microestructura (Binance)
       │
       ▼
  TripleCoincidenceDetector.process_stream()
       │
       ├── detect_key_candles()     → candidatos volumétricos
       ├── detect_accumulation()    → zonas de acumulación
       ├── detect_mini_trend()      → dirección + R²
       │
       ▼
  Triple Coincidence Score > 0.45 → ActiveZone registrada

FASE 2: MONITOREO DE RETEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ActiveZone monitoreada durante max retest_timeout_bars velas
       │
       ▼
  ¿Precio re-toca la zona?
       │
       ├─ NO (timeout) → zona expirada, descartada
       │
       └─ SÍ → CAPTURAR FEATURES EN ESTE MOMENTO:
              • VWAP al nivel del retest
              • OBI (Order Book Imbalance, 10 niveles)
              • Cumulative Delta
              • Delta Divergence (absorción vs exhaustión)
              • ATR de contexto
              • Régimen de mercado (TREND | LATERAL | HIGH_VOL)

FASE 3: OUTCOME Y ENTRENAMIENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Observar outcome_lookahead_bars velas posteriores:
       │
       ├─ BOUNCE: precio respeta zona → señal válida
       │
       └─ BREAKOUT: precio rompe zona → señal inválida
       │
       ▼
  TrainingSample generado: {features_retest → outcome}
       │
       ▼
  OracleTrainer_v3.load_training_dataset()
       │
       ▼
  Oracle predice futuros retests: confidence > 0.70 → operar
```

**Key Insight:**
Las features se capturan EN el retest, no en la detección de la zona.
Esto es lo que diferencia a la TC de la Absorción v2: el Oracle no evalúa
la "calidad de la zona" sino las "condiciones del mercado en el momento
del retest". Estas son significativamente más predictivas.

---

### **5. Integración con el Pipeline de 7 Componentes**

```
[1] BinanceVisionFetcher_v3
     → OHLCV + datos de microestructura (VWAP, OBI, CumDelta)

[2] TripleCoincidenceDetector
     → Detecta zonas por triple coincidencia
     → Monitorea retests
     → Captura features EN el retest
     → Genera TrainingSamples con outcome

[3] ZonePhysicsMonitor_v3
     → Evalúa física del retest: REBOTE_CONFIRMADO vs RUPTURA_ZONA
     → 2ª confirmación antes de enviar al Oracle

[4] ShadowTrader
     → Abre posiciones virtuales (sin riesgo real)
     → Captura trayectorias MFE (Max Favorable Excursion) / MAE (Max Adverse Excursion)
     → Genera estadísticas para validación Walk-Forward

[5] OracleTrainer_v3 (Meta-Labeling)
     → Entrena modelo: [features_retest] → {BOUNCE, BREAKOUT}
     → Predice outcome de nuevos retests
     → Umbral operativo: confidence > 0.70

[6] NexusGate
     → Gate binario: PROMOTE_TO_LAYER_2 | REJECT
     → Condiciones: ΔCausal > 0, OOS coverage > 80%, human_approval

[7] AutoProposer
     → Detecta drift en métricas (win rate, drawdown, latencia)
     → Propone ajustes paramétricos con estimated_delta
     → Requiere aprobación humana
```

---

### **6. Parámetros Configurables**

| Parámetro | Default | Rango | Función |
|-----------|---------|-------|---------|
| `volume_percentile_threshold` | 70 | 50-95 | Percentil mínimo de volumen para vela clave |
| `body_percentage_threshold` | 40 | 20-60 | % máximo del cuerpo sobre rango total |
| `lookback_candles` | 30 | 10-100 | Ventana de lookback para estadísticas |
| `atr_period` | 14 | 7-30 | Periodos para cálculo de ATR |
| `atr_multiplier` | 1.5 | 1.0-3.0 | Multiplicador ATR para definir zona |
| `volume_threshold` | 1.2 | 0.8-2.0 | Ratio volumen zona vs global |
| `min_zone_bars` | 5 | 3-15 | Mínimo de barras en zona de acumulación |
| `quality_threshold` | 0.45 | 0.3-0.7 | Score mínimo para aceptar zona |
| `r2_min` | 0.45 | 0.3-0.8 | R² mínimo para aceptar tendencia |
| `proximity_tolerance` | 8 | 3-20 | Máximo velas entre los 3 eventos |
| `retest_timeout_bars` | 50 | 10-100 | Velas máx. para esperar retest |
| `outcome_lookahead_bars` | 10 | 5-30 | Velas para determinar BOUNCE/BREAKOUT |

---

### **7. Features Capturadas en el Retest**

| Feature | Tipo | Descripción |
|---------|------|-------------|
| `vwap_at_retest` | float | VWAP en el momento exacto del retest |
| `obi_10_at_retest` | float | Order Book Imbalance (10 niveles) |
| `cumulative_delta_at_retest` | float | Delta acumulado de volumen |
| `delta_divergence` | categorical | BULLISH_ABSORPTION / BEARISH_EXHAUSTION / NEUTRAL |
| `atr_14` | float | ATR de contexto (volatilidad ambiente) |
| `regime` | categorical | TREND / LATERAL / HIGH_VOL |
| `direction` | categorical | bullish / bearish |

---

### **8. Protocolo de Auditoría y Validación**

#### **8.1. Walk-Forward Validation (≥3 ventanas)**
Cada ventana contiene un periodo in-sample (entrenamiento) y out-of-sample (validación):
- **No-Leakage Gate:** Verifica que ningún feature use información futura
- **Temporal Integrity:** `train_end < oos_start` estricto
- **Resultado mínimo:** Sharpe ≥ 1.5 agregado para promoción

#### **8.2. Métricas de Performance**

| Métrica | Target | Descripción |
|---------|--------|-------------|
| Sharpe Ratio | > 2.0 | Retorno ajustado por volatilidad |
| Max Drawdown | < 10% | Pérdida máxima desde pico |
| Win Rate (retests) | > 55% | % de retests que resultan en BOUNCE |
| Oracle Accuracy | > 65% | Precisión del modelo de predicción |
| Calmar Ratio | > 2.0 | Return / Max DD anualizado |

#### **8.3. Ciclo de Mejora Continua (AutoProposer)**
1. **Detección de Drift:** Si métricas caen 2σ bajo baseline → alerta
2. **Propuesta Paramétrica:** AutoProposer sugiere ajuste con justificación
3. **Validación:** Se re-ejecuta Walk-Forward con parámetros nuevos
4. **Promoción:** Si ΔCausal > 0 + human_approval → ADN Permanente

---

### **9. Estructura de Archivos del Módulo**

```
cgalpha_v3/
├── infrastructure/signal_detector/
│   ├── __init__.py                  # Exporta TripleCoincidenceDetector
│   ├── triple_coincidence.py        # 903 líneas — Implementación completa
│   └── README.md                    # Documentación técnica del módulo
├── application/
│   ├── pipeline.py                  # TripleCoincidencePipeline (orquestador)
│   └── experiment_runner.py         # Walk-forward validation
├── lila/llm/
│   ├── oracle.py                    # OracleTrainer_v3 (Meta-Labeling)
│   └── proposer.py                  # AutoProposer
├── domain/models/
│   └── signal.py                    # ApproachType (TRIPLE_COINCIDENCE enum)
├── indicators/
│   ├── zone_monitors.py             # ZonePhysicsMonitor_v3
│   └── legacy_signals.py            # VWAP, OBI, CumDelta (indicadores base)
└── trading/
    └── shadow_trader.py             # ShadowTrader (posiciones virtuales)
```

---

### **10. Glosario Técnico**

| Término | Definición |
|---------|-----------|
| **Triple Coincidence** | Convergencia de vela clave + zona de acumulación + mini-tendencia |
| **Retest** | Retorno del precio a una zona previamente detectada |
| **ActiveZone** | Zona en monitoreo activo esperando retest |
| **RetestEvent** | Evento de retest con features de microestructura capturadas |
| **TrainingSample** | Par {features_retest, outcome} para entrenamiento del Oracle |
| **Meta-Labeling** | Técnica ML donde un modelo secundario predice si la señal primaria será exitosa |
| **ΔCausal** | Mejora neta en performance atribuible causalmente al componente |
| **BOUNCE** | El precio respeta la zona y revierte → señal exitosa |
| **BREAKOUT** | El precio rompe la zona definitivamente → señal fallida |
| **OOS** | Out-of-Sample — datos no vistos durante entrenamiento |
| **ADN Permanente** | Capa 2 de la Bóveda: componentes validados con ΔCausal > 0 |

---

### **11. Evolución desde v2**

| Aspecto | v2 (Absorción Pasiva) | v3 (Triple Coincidence) |
|---------|----------------------|------------------------|
| Detección | 1 señal (absorción) | 3 señales independientes convergentes |
| Features | Capturadas en la detección | Capturadas EN el retest |
| Oracle | Sin meta-labeling | Meta-labeling: features_retest → outcome |
| Validación | Backtesting simple | Walk-Forward ≥3 ventanas + No-Leakage |
| Parámetros | Estáticos | Adaptativos vía AutoProposer |
| Arquitectura | Monolítica | Pipeline de 7 componentes ensamblables |

---

*FIRMADO:*
**Lila (The Librarian-Architect)**
**CGAlpha v3 Control Room — Triple Coincidence Strategy v3.0**

*Este documento es el contrato técnico de la Triple Coincidence Strategy.
Sustituye al AbsorptionCandleDetector_v3.md como referencia canónica de
la Simple Foundation Strategy.*
