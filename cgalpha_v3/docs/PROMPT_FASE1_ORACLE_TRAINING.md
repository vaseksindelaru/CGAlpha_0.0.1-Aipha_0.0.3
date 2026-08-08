# PROMPT MAESTRO — FASE 1: Entrenamiento Oracle + Primera Validación
## CGAlpha v3 — Triple Coincidence Strategy

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  CLASIFICACIÓN : Prompt de Ejecución — Fase 1                              ║
║  VERSIÓN       : 1.0.0                                                     ║
║  ESTADO        : PENDIENTE DE EJECUCIÓN                                    ║
║  PREREQUISITO  : Fase 0 completada (commit 47affc5, 118/118 tests)         ║
║  RESULTADO ESP : Oracle RF entrenado, Walk-Forward medido, memoria L1      ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## CONTEXTO DEL SISTEMA

Eres un asistente de código trabajando en **CGAlpha v3**, un sistema de trading algorítmico con arquitectura de 7 componentes. El sistema implementa la **Triple Coincidence Strategy**: detecta zonas por convergencia de 3 señales independientes (vela clave + acumulación + mini-tendencia), espera el **retest** del precio a la zona, captura **features de microestructura** EN el momento del retest (VWAP, OBI, CumDelta), y entrena un **Oracle (Meta-Labeling)** que predice si el retest resultará en BOUNCE o BREAKOUT.

### Estado actual (post-Fase 0)
- **Pipeline validado**: 7 componentes ensamblados y funcionales
- **Fase 0 completada**: 500 velas sintéticas procesadas, 21 retests detectados (19 BOUNCE, 2 BREAKOUT)
- **Oracle**: PLACEHOLDER — retorna confidence fija de 0.85. **NO hay modelo ML real.**
- **BinanceVisionFetcher**: PLACEHOLDER — no descarga datos reales aún.
- **AutoProposer**: PLACEHOLDER — `analyze_drift()` retorna lista vacía.
- **Tests**: 118/118 passing (~8s)
- **Último commit**: `47affc5` en branch `main`

### Directorio raíz
```
/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/
```

### Comando de inicio del servidor GUI
```bash
PYTHONPATH=. CGV3_HOST=0.0.0.0 CGV3_PORT=5000 python cgalpha_v3/gui/server.py
```

### Token de desarrollo
```
cgalpha-v3-local-dev
```

---

## REGLA DE ORO

> **Todo cambio en v3 debe:**
> 1. Pasar la suite completa de tests existentes (≥118)
> 2. Incluir tests nuevos para funcionalidad nueva
> 3. Ser documentable en `memory/iterations/`
> 4. NO romper la GUI ni los endpoints existentes

---

## OBJETIVO DE FASE 1

Transformar el sistema de un pipeline con Oracle placeholder a un **sistema con ML real** capaz de predecir BOUNCE vs BREAKOUT usando RandomForestClassifier, validar la predicción via Walk-Forward de 3 ventanas, documentar resultados en la memoria inteligente, activar el AutoProposer con datos reales, y buscar soporte teórico en la Library.

---

## ARCHIVOS CLAVE Y SUS ROLES

### Archivos que DEBES MODIFICAR:

| Archivo | Rol | Qué hacer |
|---------|-----|-----------|
| `cgalpha_v3/lila/llm/oracle.py` | OracleTrainer_v3 | Reemplazar placeholder por RandomForestClassifier real |
| `cgalpha_v3/lila/llm/proposer.py` | AutoProposer | Implementar `analyze_drift()` con lógica real de detección |
| `cgalpha_v3/infrastructure/binance_data.py` | BinanceVisionFetcher_v3 | Implementar descarga real de CSVs de Binance Vision |
| `cgalpha_v3/scripts/phase0_harvest.py` | Script de cosecha | Crear `phase1_oracle_training.py` basado en esto |

### Archivos que DEBES CREAR:

| Archivo | Propósito |
|---------|-----------|
| `cgalpha_v3/scripts/phase1_oracle_training.py` | Script principal de Fase 1 |
| `cgalpha_v3/tests/test_oracle_training.py` | Tests del Oracle RF real |
| `cgalpha_v3/tests/test_auto_proposer.py` | Tests del AutoProposer real |
| `cgalpha_v3/data/phase1_results/` | Directorio de resultados |

### Archivos de REFERENCIA (NO modificar, solo leer):

| Archivo | Contiene |
|---------|----------|
| `cgalpha_v3/docs/TripleCoincidenceStrategy_v3.md` | Contrato técnico canónico (311 líneas) |
| `LILA_v3_NORTH_STAR.md` | Documento fundacional (1335 líneas) |
| `cgalpha_v3/SYSTEM_DEEP_DIVE.md` | Filosofía arquitectónica |
| `cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py` | TripleCoincidenceDetector (929 líneas) |
| `cgalpha_v3/application/experiment_runner.py` | ExperimentRunner con Walk-Forward (507 líneas) |
| `cgalpha_v3/data/phase0_results/phase0_summary.json` | Resultados de Fase 0 |
| `cgalpha_v3/data/phase0_results/training_dataset.json` | Dataset de 21 samples |

---

## INSTRUCCIONES DETALLADAS — 5 TAREAS SECUENCIALES

---

### TAREA 1: Entrenar Oracle con RandomForestClassifier
**Archivo**: `cgalpha_v3/lila/llm/oracle.py`
**Prioridad**: P0 (bloqueante para todo lo demás)

#### Estado actual del OracleTrainer_v3:
```python
# Líneas 56-60 de oracle.py — ESTO ES LO QUE DEBES REEMPLAZAR:
# Placeholder: entrenar modelo real (sklearn, XGBoost, etc.)
# from sklearn.ensemble import RandomForestClassifier
# self.model = RandomForestClassifier(n_estimators=100, random_state=42)
# self.model.fit(X, y)
self.model = "placeholder_model_trained"
```

#### Lo que DEBES implementar:

1. **Descomentarizar y completar `train_model()`**:
   ```python
   from sklearn.ensemble import RandomForestClassifier
   from sklearn.preprocessing import LabelEncoder
   
   def train_model(self):
       if not self.training_data:
           raise ValueError("No training data loaded.")
       
       df = pd.DataFrame(self.training_data)
       
       feature_cols = [
           'vwap_at_retest', 'obi_10_at_retest', 'cumulative_delta_at_retest',
           'delta_divergence', 'atr_14', 'regime', 'direction'
       ]
       
       # Encode categoricals
       le_div = LabelEncoder()
       le_reg = LabelEncoder()
       le_dir = LabelEncoder()
       
       df['delta_divergence'] = le_div.fit_transform(df['delta_divergence'].fillna('NEUTRAL'))
       df['regime'] = le_reg.fit_transform(df['regime'].fillna('LATERAL'))
       df['direction'] = le_dir.fit_transform(df['direction'].fillna('bullish'))
       
       X = df[feature_cols].fillna(0)
       y = df['outcome'].map({'BOUNCE': 1, 'BREAKOUT': 0})
       
       self.model = RandomForestClassifier(
           n_estimators=100,
           max_depth=5,          # Prevenir overfitting con pocos samples
           min_samples_leaf=2,   # Conservador para datasets pequeños
           random_state=42,
           class_weight='balanced'  # Compensa desbalance BOUNCE/BREAKOUT
       )
       self.model.fit(X, y)
       
       # Guardar encoders para predict
       self._encoders = {
           'delta_divergence': le_div,
           'regime': le_reg,
           'direction': le_dir,
       }
       
       # Log métricas de entrenamiento
       train_accuracy = self.model.score(X, y)
       self._training_metrics = {
           'n_samples': len(df),
           'train_accuracy': round(train_accuracy, 4),
           'n_features': len(feature_cols),
           'class_distribution': y.value_counts().to_dict(),
           'feature_importances': dict(zip(feature_cols, 
               [round(x, 4) for x in self.model.feature_importances_])),
       }
   ```

2. **Implementar `predict()` real** (reemplazar placeholder):
   ```python
   def predict(self, micro, signal_data):
       if self.model is None or self.model == "placeholder_model_trained":
           # Fallback placeholder
           return OraclePrediction(
               trade_id=signal_data.get('index', 'unknown'),
               confidence=0.85,
               suggested_action="EXECUTE",
               estimated_delta_causal=0.74
           )
       
       # Extraer y encodear features
       features = pd.DataFrame([{
           'vwap_at_retest': micro.vwap,
           'obi_10_at_retest': micro.obi_10,
           'cumulative_delta_at_retest': micro.cumulative_delta,
           'delta_divergence': self._safe_encode('delta_divergence', micro.delta_divergence),
           'atr_14': micro.atr_14,
           'regime': self._safe_encode('regime', micro.regime),
           'direction': self._safe_encode('direction', signal_data.get('direction', 'bullish')),
       }])
       
       proba = self.model.predict_proba(features)[0]
       confidence = float(proba[1])  # P(BOUNCE)
       action = "EXECUTE" if confidence >= self.min_confidence else "IGNORE"
       
       return OraclePrediction(
           trade_id=signal_data.get('index', 'unknown'),
           confidence=round(confidence, 4),
           suggested_action=action,
           estimated_delta_causal=round(confidence - 0.5, 4)
       )
   ```

3. **Añadir helper `_safe_encode()`**:
   ```python
   def _safe_encode(self, field, value):
       """Encode categorical con fallback para valores no vistos."""
       if not hasattr(self, '_encoders') or field not in self._encoders:
           return 0
       le = self._encoders[field]
       if value in le.classes_:
           return le.transform([value])[0]
       return 0  # Valor por defecto para categorías no vistas
   ```

4. **Añadir método `get_training_metrics()`**:
   ```python
   def get_training_metrics(self):
       """Retorna métricas del último entrenamiento."""
       return getattr(self, '_training_metrics', None)
   ```

5. **Implementar `retrain_recursive()`**:
   ```python
   def retrain_recursive(self, training_data_path: str):
       """Re-entrena con datos nuevos desde un archivo JSON."""
       import json
       with open(training_data_path, 'r') as f:
           new_data = json.load(f)
       
       # Merge con datos existentes
       self.training_data.extend(new_data)
       
       # Re-entrenar
       self.train_model()
   ```

#### CONTRATOS que el Oracle DEBE cumplir:
- `train_model()` DEBE funcionar con ≥5 samples (dataset de Fase 0 tiene 21)
- `predict()` DEBE retornar confidence en rango [0.0, 1.0]
- `predict()` con modelo entrenado DEBE usar el modelo RF, NO el placeholder
- `predict()` sin modelo entrenado DEBE seguir retornando el placeholder (backward compatible)
- `_safe_encode()` NO debe crashear con valores categóricos no vistos

#### Dependencia de sklearn:
- `scikit-learn` ya está en las dependencias del proyecto (verificar con `pip show scikit-learn`)
- Si no está instalado: `pip install scikit-learn>=1.3.0`

---

### TAREA 2: Walk-Forward 3 ventanas — medir Sharpe neto
**Archivo nuevo**: `cgalpha_v3/scripts/phase1_oracle_training.py`
**Referencia**: `cgalpha_v3/scripts/phase0_harvest.py` (estructura similar)

#### Lo que este script DEBE hacer:

```
PASO 1: Generar datos (2000 velas, no 500 como Fase 0)
  → generate_realistic_ohlcv(n_candles=2000, seed=42)
  → generate_micro_features(df, seed=42)

PASO 2: Ejecutar TripleCoincidenceDetector.process_stream()
  → Detectar zonas y retests
  → Generar training_samples

PASO 3: Entrenar Oracle con RandomForest REAL
  → oracle.load_training_dataset(training_data)
  → oracle.train_model()
  → Imprimir training_metrics (accuracy, feature_importances)

PASO 4: Walk-Forward 3 ventanas con Oracle
  → Usar ExperimentRunner con signal_detector configurado
  → Para cada ventana:
    a) Dividir datos en train/val/oos (60/20/20)
    b) Entrenar Oracle solo con datos de train
    c) Predecir en datos de OOS
    d) Calcular: Sharpe neto, drawdown, win rate, oracle accuracy
  → NO debe haber leakage temporal (train_end < oos_start)

PASO 5: Calcular métricas agregadas
  → Sharpe neto promedio de 3 ventanas
  → Max drawdown promedio
  → Oracle accuracy promedio en OOS
  → Win rate promedio

PASO 6: Activar AutoProposer
  → Pasar métricas de PASO 5 al AutoProposer.analyze_drift()
  → Documentar propuestas generadas

PASO 7: Guardar resultados
  → cgalpha_v3/data/phase1_results/phase1_summary.json
  → cgalpha_v3/data/phase1_results/oracle_model_metrics.json
  → cgalpha_v3/data/phase1_results/walk_forward_results.json
  → cgalpha_v3/data/phase1_results/auto_proposer_output.json
```

#### Formato del Walk-Forward:
```
Datos: 2000 velas → split en 3 ventanas no solapadas

Ventana 1:  [0..665]
  train:      [0..399]    (60%)
  validation: [400..532]  (20%)
  oos:        [533..665]  (20%)

Ventana 2:  [666..1332]
  train:      [666..1065]
  validation: [1066..1198]
  oos:        [1199..1332]

Ventana 3:  [1333..2000]
  train:      [1333..1733]
  validation: [1734..1866]
  oos:        [1867..2000]
```

#### Métricas OBLIGATORIAS por ventana:
```python
{
    "window_id": 1,
    "train_samples": 45,       # # de retests en train
    "oos_samples": 12,         # # de retests en oos
    "oracle_accuracy_oos": 0.72,  # Accuracy en OOS
    "oracle_precision_oos": 0.68, # Precision BOUNCE en OOS
    "oracle_recall_oos": 0.85,    # Recall BOUNCE en OOS
    "sharpe_neto": 1.45,          # Net de fees + slippage
    "max_drawdown_pct": 3.2,
    "win_rate_pct": 58.3,
    "net_return_pct": 2.14,
    "trades": 12,
    "feature_importances": {...}  # Del modelo entrenado en train
}
```

---

### TAREA 3: Documentar resultados en memoria (nivel 0a→1)
**Archivos**: `cgalpha_v3/gui/server.py` (usar endpoint existente)

#### Qué documentar:
Al final de `phase1_oracle_training.py`, el script debe llamar a la API para ingestar en memoria:

```python
import requests

BASE = "http://localhost:5000/api"
TOKEN = "cgalpha-v3-local-dev"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# 1. Ingestar resultado como memoria nivel 0a (Meta-Cognitivo)
requests.post(f"{BASE}/learning/memory/ingest", headers=HEADERS, json={
    "content": f"Oracle RF entrenado: accuracy_oos={agg_accuracy:.4f}, "
               f"sharpe_neto_avg={agg_sharpe:.4f}, "
               f"feature_importances_top3={top3_features}",
    "field": "math",
    "level": "0a"
})

# 2. Si métricas son buenas (sharpe > 0.8), promover a nivel 1
if agg_sharpe > 0.8:
    requests.post(f"{BASE}/learning/memory/ingest", headers=HEADERS, json={
        "content": f"Walk-Forward validado: 3 ventanas OOS, "
                   f"sharpe_neto_avg={agg_sharpe:.4f}, "
                   f"max_dd_avg={agg_dd:.4f}%, "
                   f"oracle_accuracy_oos={agg_accuracy:.4f}",
        "field": "trading",
        "level": "1"
    })
```

#### También crear entry en `memory/iterations/`:
```python
iteration_dir = PROJECT_ROOT / "cgalpha_v3" / "memory" / "iterations" / datetime.now().strftime("%Y-%m-%d_%H-%M_phase1")
iteration_dir.mkdir(parents=True, exist_ok=True)

# iteration_status.json
status = {
    "phase": "1",
    "task": "Oracle Training + Walk-Forward Validation",
    "status": "completed",
    "timestamp": datetime.now().isoformat(),
    "oracle_accuracy_oos": agg_accuracy,
    "sharpe_neto_avg": agg_sharpe,
    "max_drawdown_avg": agg_dd,
    "win_rate_avg": agg_wr,
    "tests_passing": "118+N"  # N = tests nuevos
}

# iteration_summary.md
summary = f"""# Fase 1: Oracle Training + Walk-Forward
## {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Resultados
- Oracle: RandomForestClassifier (n=100, depth=5, balanced)
- Training samples: {total_samples}
- Walk-Forward: 3 ventanas OOS
- Sharpe neto avg: {agg_sharpe:.4f}
- Max DD avg: {agg_dd:.4f}%
- Oracle accuracy OOS: {agg_accuracy:.4f}
- Win rate avg: {agg_wr:.1f}%

### Feature Importances
{feature_importances_formatted}

### Decisión
{"✅ APROBADO para Fase 2" if agg_sharpe > 0.8 else "⚠️ Requiere ajuste antes de Fase 2"}
"""
```

---

### TAREA 4: AutoProposer — primera propuesta basada en datos reales
**Archivo**: `cgalpha_v3/lila/llm/proposer.py`

#### Estado actual:
```python
def analyze_drift(self, performance_metrics: Dict) -> List[TechnicalSpec]:
    # Placeholder
    return []
```

#### Lo que DEBES implementar:

```python
def analyze_drift(self, performance_metrics: Dict) -> List[TechnicalSpec]:
    """
    Analiza métricas del Oracle + Walk-Forward y propone ajustes.
    
    Reglas de drift:
    1. Si oracle_accuracy_oos < 0.60 → proponer reducir min_confidence
    2. Si max_drawdown > 5% → proponer reducir position_size
    3. Si win_rate < 50% → proponer aumentar quality_threshold del detector
    4. Si sharpe_neto < 0.5 → proponer cambiar n_estimators del RF
    5. Si feature_importance(VWAP) < 0.05 → proponer eliminar VWAP como feature
    """
    proposals = []
    
    accuracy = performance_metrics.get('oracle_accuracy_oos', 0.85)
    max_dd = performance_metrics.get('max_drawdown_pct', 0)
    win_rate = performance_metrics.get('win_rate_pct', 55)
    sharpe = performance_metrics.get('sharpe_neto', 1.0)
    importances = performance_metrics.get('feature_importances', {})
    
    # Regla 1: Accuracy baja
    if accuracy < 0.60:
        proposals.append(TechnicalSpec(
            change_type="parameter",
            target_file="cgalpha_v3/lila/llm/oracle.py",
            target_attribute="min_confidence",
            old_value=0.70,
            new_value=0.65,
            reason=f"Oracle accuracy OOS={accuracy:.2%} está por debajo del 60%. "
                   f"Reducir umbral de confianza para capturar más señales verdaderas.",
            causal_score_est=0.45,
            confidence=0.70,
        ))
    
    # Regla 2: Drawdown excesivo
    if max_dd > 5.0:
        proposals.append(TechnicalSpec(
            change_type="parameter",
            target_file="cgalpha_v3/gui/server.py",
            target_attribute="max_position_size_pct",
            old_value=2.0,
            new_value=1.0,
            reason=f"Max drawdown={max_dd:.2f}% excede 5%. "
                   f"Reducir tamaño de posición para limitar exposición.",
            causal_score_est=0.55,
            confidence=0.80,
        ))
    
    # Regla 3: Win rate bajo
    if win_rate < 50:
        proposals.append(TechnicalSpec(
            change_type="parameter",
            target_file="cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py",
            target_attribute="min_coincidence_score",
            old_value=0.50,
            new_value=0.60,
            reason=f"Win rate={win_rate:.1f}% por debajo del 50%. "
                   f"Aumentar umbral de calidad de zona para filtrar señales débiles.",
            causal_score_est=0.50,
            confidence=0.65,
        ))
    
    # Regla 4: Sharpe bajo
    if sharpe < 0.5:
        proposals.append(TechnicalSpec(
            change_type="parameter",
            target_file="cgalpha_v3/lila/llm/oracle.py",
            target_attribute="n_estimators",
            old_value=100,
            new_value=200,
            reason=f"Sharpe neto={sharpe:.4f} por debajo de 0.5. "
                   f"Aumentar complejidad del modelo para capturar patrones más sutiles.",
            causal_score_est=0.40,
            confidence=0.55,
        ))
    
    # Regla 5: Feature con importancia insignificante
    for feat, imp in importances.items():
        if imp < 0.05:
            proposals.append(TechnicalSpec(
                change_type="feature",
                target_file="cgalpha_v3/lila/llm/oracle.py",
                target_attribute=f"feature:{feat}",
                old_value=imp,
                new_value=0.0,
                reason=f"Feature '{feat}' tiene importancia={imp:.4f} (<5%). "
                       f"Candidata a eliminación para simplificar modelo.",
                causal_score_est=0.30,
                confidence=0.50,
            ))
    
    # Filtrar por score mínimo
    return [p for p in proposals if p.causal_score_est >= 0.30]
```

---

### TAREA 5: Library — buscar fuentes teóricas
**Archivo**: `cgalpha_v3/scripts/phase1_oracle_training.py` (sección final)

#### Lo que el script debe hacer al final:

```python
# Buscar en Library fuentes que respalden o contradigan los resultados
library_search_terms = [
    "Meta-Labeling",
    "RandomForest trading",
    "Walk-Forward validation",
    "microstructure features",
    "order book imbalance prediction",
]

for term in library_search_terms:
    resp = requests.get(
        f"{BASE}/library/sources",
        params={"query": term},
        headers=HEADERS
    )
    results = resp.json()
    if results.get("sources"):
        print(f"  📚 '{term}': {len(results['sources'])} fuentes encontradas")
    else:
        # Crear backlog item para buscar esta fuente
        requests.post(f"{BASE}/lila/backlog/add", headers=HEADERS, json={
            "title": f"Buscar fuente primary: {term}",
            "rationale": f"Fase 1 necesita soporte teórico para '{term}' "
                         f"pero no hay fuentes en Library.",
            "item_type": "research",
            "impact": 7,
            "risk": 3,
            "evidence_gap": 9,
        })
        print(f"  📋 '{term}': No hay fuentes → backlog item creado")

# Ingestar fuentes canónicas si no están
canonical_sources = [
    {
        "title": "Advances in Financial Machine Learning - Ch. 3: Meta-Labeling",
        "authors": ["Marcos López de Prado"],
        "year": 2018,
        "source_type": "primary",
        "venue": "journal_of_financial_economics",
        "finding": "Meta-Labeling separates the side prediction from the size prediction, "
                   "improving risk-adjusted returns by 15-30% in empirical tests.",
        "applicability": "Fundamento teórico directo del OracleTrainer_v3. "
                         "Confirma que un modelo secundario (Oracle) que predice la calidad "
                         "de una señal primaria (TripleCoincidence) es más robusto que "
                         "un modelo monolítico.",
        "tags": ["meta-labeling", "oracle", "machine-learning"],
    },
    {
        "title": "The Volume-Weighted Average Price (VWAP) as a Trading Benchmark",
        "authors": ["Berkowitz, S.", "Logue, D.", "Noser, E."],
        "year": 1988,
        "source_type": "primary",
        "venue": "journal_of_finance",
        "finding": "VWAP provides a fair benchmark for institutional execution quality "
                   "and correlates with support/resistance levels.",
        "applicability": "Fundamento para usar VWAP como feature en el Oracle. "
                         "VWAP en el retest indica si el precio está en 'valor justo' "
                         "o desviado.",
        "tags": ["vwap", "microstructure", "benchmark"],
    },
]
```

---

## TESTS OBLIGATORIOS

### `cgalpha_v3/tests/test_oracle_training.py` (CREAR):

```python
"""Tests para Oracle RF real — Fase 1"""
import pytest
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3, OraclePrediction
from cgalpha_v3.infrastructure.binance_data import MicrostructureRecord


class TestOracleRealRF:
    """Tests del Oracle con RandomForestClassifier real."""
    
    def _make_training_data(self, n=30):
        """Genera dataset sintético para tests."""
        import numpy as np
        rng = np.random.default_rng(42)
        samples = []
        for i in range(n):
            outcome = "BOUNCE" if rng.random() > 0.3 else "BREAKOUT"
            samples.append({
                'vwap_at_retest': 65000 + rng.normal(0, 2000),
                'obi_10_at_retest': rng.uniform(-0.5, 0.5),
                'cumulative_delta_at_retest': rng.normal(0, 500),
                'delta_divergence': rng.choice(["BULLISH_ABSORPTION", "BEARISH_EXHAUSTION", "NEUTRAL"]),
                'atr_14': rng.uniform(200, 800),
                'regime': rng.choice(["TREND", "LATERAL", "HIGH_VOL"]),
                'direction': rng.choice(["bullish", "bearish"]),
                'outcome': outcome,
            })
        return samples
    
    def test_train_model_real(self):
        oracle = OracleTrainer_v3.create_default()
        data = self._make_training_data(30)
        oracle.load_training_dataset(data)
        oracle.train_model()
        assert oracle.model is not None
        assert oracle.model != "placeholder_model_trained"
    
    def test_predict_with_trained_model(self):
        oracle = OracleTrainer_v3.create_default()
        data = self._make_training_data(30)
        oracle.load_training_dataset(data)
        oracle.train_model()
        
        micro = MicrostructureRecord(
            timestamp=1000, symbol="BTCUSDT",
            open=65000, high=65500, low=64800, close=65200,
            volume=1500, vwap=65100, vwap_std_1=100, vwap_std_2=200,
            obi_10=0.15, cumulative_delta=250,
            delta_divergence="BULLISH_ABSORPTION",
            atr_14=450, regime="LATERAL"
        )
        pred = oracle.predict(micro, {'index': 100, 'direction': 'bullish'})
        
        assert isinstance(pred, OraclePrediction)
        assert 0.0 <= pred.confidence <= 1.0
        assert pred.suggested_action in ("EXECUTE", "IGNORE")
    
    def test_training_metrics_available(self):
        oracle = OracleTrainer_v3.create_default()
        data = self._make_training_data(30)
        oracle.load_training_dataset(data)
        oracle.train_model()
        
        metrics = oracle.get_training_metrics()
        assert metrics is not None
        assert 'train_accuracy' in metrics
        assert 'feature_importances' in metrics
        assert metrics['n_samples'] == 30
    
    def test_safe_encode_unknown_category(self):
        oracle = OracleTrainer_v3.create_default()
        data = self._make_training_data(30)
        oracle.load_training_dataset(data)
        oracle.train_model()
        
        # Valor de categoría no visto en entrenamiento
        result = oracle._safe_encode('regime', 'UNKNOWN_REGIME')
        assert result == 0
    
    def test_backward_compatible_placeholder(self):
        """Oracle sin entrenar sigue retornando placeholder."""
        oracle = OracleTrainer_v3.create_default()
        micro = MicrostructureRecord(
            timestamp=1000, symbol="BTCUSDT",
            open=65000, high=65500, low=64800, close=65200,
            volume=1500, vwap=65100, vwap_std_1=100, vwap_std_2=200,
            obi_10=0.15, cumulative_delta=250,
            delta_divergence="NEUTRAL", atr_14=450, regime="LATERAL"
        )
        pred = oracle.predict(micro, {'index': 1})
        assert pred.confidence == 0.85  # Placeholder value
    
    def test_min_samples_threshold(self):
        """Oracle debe funcionar con ≥5 samples."""
        oracle = OracleTrainer_v3.create_default()
        data = self._make_training_data(5)
        oracle.load_training_dataset(data)
        oracle.train_model()
        assert oracle.model is not None


class TestAutoProposerReal:
    """Tests del AutoProposer con lógica de drift real."""
    
    def test_no_proposals_when_metrics_good(self):
        from cgalpha_v3.lila.llm.proposer import AutoProposer
        proposer = AutoProposer.create_default()
        metrics = {
            'oracle_accuracy_oos': 0.75,
            'max_drawdown_pct': 3.0,
            'win_rate_pct': 60,
            'sharpe_neto': 1.5,
            'feature_importances': {'vwap_at_retest': 0.25, 'obi_10_at_retest': 0.20}
        }
        proposals = proposer.analyze_drift(metrics)
        assert len(proposals) == 0
    
    def test_proposals_when_accuracy_low(self):
        from cgalpha_v3.lila.llm.proposer import AutoProposer
        proposer = AutoProposer.create_default()
        metrics = {
            'oracle_accuracy_oos': 0.50,
            'max_drawdown_pct': 3.0,
            'win_rate_pct': 55,
            'sharpe_neto': 1.0,
            'feature_importances': {}
        }
        proposals = proposer.analyze_drift(metrics)
        assert len(proposals) >= 1
        assert any(p.target_attribute == 'min_confidence' for p in proposals)
    
    def test_proposals_when_drawdown_high(self):
        from cgalpha_v3.lila.llm.proposer import AutoProposer
        proposer = AutoProposer.create_default()
        metrics = {
            'oracle_accuracy_oos': 0.70,
            'max_drawdown_pct': 8.0,
            'win_rate_pct': 55,
            'sharpe_neto': 1.0,
            'feature_importances': {}
        }
        proposals = proposer.analyze_drift(metrics)
        assert any(p.target_attribute == 'max_position_size_pct' for p in proposals)
```

---

## ORDEN DE EJECUCIÓN

```
1. ✏️  Modificar oracle.py (TAREA 1)
2. ✏️  Modificar proposer.py (TAREA 4)
3. 📝  Crear test_oracle_training.py (tests de TAREA 1 + 4)
4. ▶️  Ejecutar tests: pytest cgalpha_v3/tests/ -q (DEBE dar ≥125 passed)
5. 📝  Crear phase1_oracle_training.py (TAREA 2 + 3 + 5)
6. ▶️  Ejecutar: PYTHONPATH=. python cgalpha_v3/scripts/phase1_oracle_training.py
7. 📊  Revisar resultados en cgalpha_v3/data/phase1_results/
8. 💾  Git commit + push con mensaje descriptivo
```

---

## CRITERIOS DE ÉXITO (GATE DE FASE 1)

| Métrica | Umbral mínimo | Umbral objetivo |
|---------|---------------|-----------------|
| Tests passing | ≥ 125 (118 + 7 nuevos) | 130+ |
| Oracle accuracy OOS | > 0.55 (better than random) | > 0.65 |
| Sharpe neto OOS (avg 3 ventanas) | > 0.0 (positivo) | > 0.8 |
| Max DD OOS (avg) | < 15% | < 10% |
| AutoProposer proposals | ≥ 1 (no vacío) | 2-5 |
| Library backlog items | ≥ 2 | 5+ |
| Memoria ingestada (nivel 0a) | ≥ 1 | 3+ |
| Walk-Forward leakage | 0.00% (obligatorio) | 0.00% |

---

## NOTAS TÉCNICAS

1. **Dataset desbalanceado**: Fase 0 produjo 19 BOUNCE / 2 BREAKOUT (90/10). Usar `class_weight='balanced'` en RF. Con 2000 velas esperamos ~80-100 retests con mejor distribución.

2. **Overfitting risk**: Con pocos samples, RF con `max_depth=5` y `min_samples_leaf=2` es conservador. Si accuracy train >> accuracy OOS, reducir complejidad.

3. **Feature encoding**: Las features categóricas (`delta_divergence`, `regime`, `direction`) necesitan LabelEncoder. Guardar el encoder para usarlo en `predict()`.

4. **Walk-Forward temporal**: Las ventanas NO deben solaparse. Usar timestamps estrictos. El `check_oos_leakage()` ya existe en ExperimentRunner.

5. **BinanceVisionFetcher**: Para esta fase, seguir usando datos sintéticos (más controlados). La integración con datos reales es para Fase 2.

6. **GUI**: Los cambios en Oracle y AutoProposer se reflejan automáticamente en los endpoints `/api/oracle/config` y `/api/vault/status`. No necesitas modificar la GUI.
