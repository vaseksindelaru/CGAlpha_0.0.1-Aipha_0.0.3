# Plan de Aprendizaje Python + CGAlpha v2
## "Preparación para Colaboradores" - Junior Developer Training Program

**Meta**: Convertirse en colaborador efectivo del equipo que reconstruye CGAlpha bajo tutela de LLM potente

**Filosofía**: "Onboarding para proyecto real" - aprender como si fueras a unirte a un equipo de desarrollo de sistemas de trading algorítmico

---

## 0. CONCEPTO TEÓRICO

### El "Concurso de Colaboradores"

Imagina que CGAlpha es un proyecto open-source prestigioso. Un LLM potente (Claude/GPT-4) actúa como **Senior Architect**. Tú eres el **Junior Developer** que quiere unirse al equipo.

**Tu misión**: Demostrar que puedes:
1. Leer y entender código existente
2. Implementar nuevas funcionalidades siguiendo patrones establecidos
3. Escribir tests que protejan el sistema
4. Comunicarte efectivamente con el equipo (documentación, commits, preguntas)

### Estructura del "Equipo"

```
+-------------------+     +-------------------+     +-------------------+
|   SENIOR ARCHITECT|     |   CODE AGENTS     |     |   JUNIOR DEV      |
|   (LLM Potente)   |     |   (Especializados)|     |   (TÚ)            |
+-------------------+     +-------------------+     +-------------------+
| - Diseña arquitect|     | - Python Tutor    |     | - Aprende         |
| - Revisa código   |     | - Math Tutor      |     | - Implementa      |
| - Aprueba cambios |     | - Trading Tutor   |     | - Pregunta        |
| - Mentoría        |     | - Code Reviewer   |     | - Documenta       |
+-------------------+     +-------------------+     +-------------------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   |
                          +--------v--------+
                          |   CGAlpha v2    |
                          |   (Codebase)    |
                          +-----------------+
```

---

## 1. AGENTES IA DISPONIBLES

### Vieja Escuela vs Nueva Escuela

| Aspecto | Vieja Escuela | Nueva Escuela (IA) |
|---------|---------------|-------------------|
| Aprender Python | Libros, cursos | LLM que explica con ejemplos de TU proyecto |
| Aprender Trading | Artículos, papers | Agente especializado en trading algorítmico |
| Aprender Matemáticas | Textbooks | Tutor que conecta conceptos con código |
| Code Review | Peer review | Agente que revisa en tiempo real |
| Debugging | Print statements | Agente que analiza stack traces |

### Agentes Especializados para CGAlpha

| Agente | Especialidad | Cuándo usarlo |
|--------|-------------|---------------|
| **PYTHON_TUTOR** | Sintaxis, patrones, best practices | "¿Cómo funciona @dataclass?" |
| **MATH_TUTOR** | Probabilidad, estadística, vectores | "¿Qué es distribución normal?" |
| **TRADING_EXPERT** | Mercados, señales, risk management | "¿Qué es una zona de acumulación?" |
| **CODE_REVIEWER** | Calidad, patrones, mejoras | "Revisa mi implementación" |
| **ARCHITECT** | Diseño, arquitectura, decisiones | "¿Cómo estructurar este servicio?" |

### Cómo Invocar Agentes (Propuesta CLI)

```bash
# Preguntar a agente específico
cgalpha ask python "¿Por qué usar frozen=True en dataclass?"
cgalpha ask math "Explícame probabilidad condicional para trading"
cgalpha ask trading "¿Qué es ATR y cómo se usa para barriers?"
cgalpha ask architect "¿Debería SignalDetector ser una clase o función?"

# Revisión de código
cgalpha review cgalpha_v2/application/services/signal_detector.py

# Sesión de aprendizaje guiada
cgalpha learn --agent python --topic dataclass
cgalpha learn --agent math --topic probability
cgalpha learn --agent trading --topic signal-detection
```

---

## 2. RUTINA DIARIA: "JUNIOR DEV WORKDAY"

### Estructura de 45-60 minutos

```
+---------------------------------------------------------------+
|  FASE 1: STANDUP (5 min)                                      |
|  +-- Revisar estado de v1: check_phase7.sh --with-analyze   |
|  +-- Actualizar daily_log.jsonl                              |
|  +-- ¿Qué hice ayer? ¿Qué haré hoy? ¿Bloqueos?               |
+---------------------------------------------------------------+
|  FASE 2: CODE READING (15 min) - "Estudio de código legacy"  |
|  +-- Leer 1 archivo de v1 o v2                               |
|  +-- Anotar patrones, preguntas, dudas                       |
|  +-- Preguntar a agente especializado                        |
+---------------------------------------------------------------+
|  FASE 3: IMPLEMENTATION (20 min) - "Sprint work"             |
|  +-- Implementar funcionalidad pequeña                       |
|  +-- O hacer ejercicio de Python                             |
|  +-- Escribir test para lo implementado                       |
+---------------------------------------------------------------+
|  FASE 4: CODE REVIEW (10 min) - "Pull Request simulation"    |
|  +-- Auto-revisión o pedir revisión a agente                 |
|  +-- Documentar aprendizajes                                  |
|  +-- Commit con mensaje descriptivo                          |
+---------------------------------------------------------------+
```

### Daily Log Estructurado

```jsonl
{"date": "2026-02-16", "standup": {"yesterday": "Leí signal.py", "today": "Implementar TrendDetector", "blockers": "No entiendo R-squared"}, "phase7": {"status": "HOLD_V03", "blind_test_ratio": 1.0, "order_book_coverage": 0.0}, "code_reading": {"file": "signal.py", "patterns": ["dataclass", "Enum"], "questions": ["¿Por qué SignalDirection es Enum?"]}, "implementation": {"task": "TrendDetector stub", "status": "in_progress", "test_written": false}, "learnings": ["Los Enums hacen el código más legible", "R-squared mide calidad de trend"], "next_day": "Terminar TrendDetector y escribir test"}
```

---

## 3. CURSO DE MATEMÁTICAS PARA TRADING

### Módulos Requeridos

| Módulo | Conceptos | Aplicación en CGAlpha |
|--------|-----------|----------------------|
| **M1: Probabilidad** | Distribuciones, probabilidad condicional, Bayes | Oracle predictions, confidence thresholds |
| **M2: Estadística** | Media, desviación estándar, correlación | ATR, volatility, signal quality |
| **M3: Vectores** | Operaciones, normas, similitud | Feature vectors, embeddings |
| **M4: Series Temporales** | Tendencias, estacionalidad, autocorrelación | Trend detection, market cycles |
| **M5: Álgebra Lineal** | Matrices, eigenvalues, SVD | PCA para features, covariance |

### Ejercicios por Módulo

#### M1: Probabilidad

```python
# Ejercicio: Calcular probabilidad de señal ganadora
# Dado: histórico de trades con señales

from cgalpha_v2.domain.models import TradeRecord, TradeOutcome

def calculate_win_probability(trades: list[TradeRecord], signal_type: str) -> float:
    """
    Calcula P(WIN | signal_type) usando datos históricos.
    
    P(A|B) = P(A y B) / P(B)
    
    Donde:
    - A = trade con outcome WIN
    - B = trade con signal_type específico
    """
    # Tu implementación aquí
    pass

# Preguntas para MATH_TUTOR:
# - ¿Qué es probabilidad condicional?
# - ¿Cómo se relaciona con el teorema de Bayes?
# - ¿Por qué es importante para trading?
```

#### M2: Estadística

```python
# Ejercicio: Calcular ATR (Average True Range)
# ATR es una medida de volatilidad

from cgalpha_v2.domain.models import Candle

def calculate_atr(candles: list[Candle], period: int = 14) -> float:
    """
    ATR = EMA(True Range, period)
    
    True Range = max(
        High - Low,
        abs(High - Previous Close),
        abs(Low - Previous Close)
    )
    
    EMA = Exponential Moving Average
    """
    # Tu implementación aquí
    pass

# Preguntas para MATH_TUTOR:
# - ¿Qué es una media móvil exponencial?
# - ¿Por qué ATR mide volatilidad?
# - ¿Cómo se usa para stop-loss y take-profit?
```

#### M3: Vectores

```python
# Ejercicio: Feature vector para predicción

from cgalpha_v2.domain.models import Candle, Feature
import numpy as np

def extract_features(candle: Candle) -> np.ndarray:
    """
    Extrae features de una vela como vector numérico.
    
    Features típicas:
    - body_percentage: (close - open) / (high - low)
    - upper_wick: (high - max(open, close)) / (high - low)
    - lower_wick: (min(open, close) - low) / (high - low)
    - volume_ratio: volume / average_volume
    
    Normalizar a [0, 1] o [-1, 1]
    """
    # Tu implementación aquí
    pass

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    mide similitud entre dos vectores.
    
    cos(ø) = (v1 · v2) / (||v1|| * ||v2||)
    
    Resultado: [-1, 1] donde 1 = idénticos
    """
    # Tu implementación aquí
    pass

# Preguntas para MATH_TUTOR:
# - ¿Qué es un vector en el contexto de ML?
# - ¿Por qué normalizar features?
# - ¿Qué significa cosine similarity para trading?
```

---

## 4. RUTA DE APRENDIZAJE: "ONBOARDING CURRICULUM"

### Semana 1-2: Onboarding Básico

| Día | Python | Matemáticas | Trading | CGAlpha |
|-----|--------|-------------|---------|---------|
| 1 | `dataclass`, `frozen` | Probabilidad básica | ¿Qué es una señal? | Leer `signal.py` |
| 2 | `Enum`, `typing` | P(A|B) condicional | Tipos de señales | Leer `trade.py` |
| 3 | `Protocol` | Distribución normal | Zonas de acumulación | Leer `ports/` |
| 4 | Excepciones | Media, std dev | ATR, volatilidad | Leer `exceptions.py` |
| 5 | Repaso + Quiz | Repaso + Quiz | Repaso + Quiz | Implementar stub |

**Ejercicio Semana 1**: Crear `MarketSnapshot` dataclass con validación

```python
# Tu tarea: Implementar MarketSnapshot
# Requisitos:
# 1. Debe ser frozen dataclass
# 2. Debe validar que price > 0
# 3. Debe tener timestamp, symbol, price, volume

from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class MarketSnapshot:
    # Tu implementación aquí
    pass

# Enviar para revisión con: cgalpha review market_snapshot.py
```

### Semana 3-4: Signal Detection Team

| Día | Python | Matemáticas | Trading | Implementación |
|-----|--------|-------------|---------|----------------|
| 1 | List comprehensions | True Range | ATR calculation | `ATRLabeler` |
| 2 | Generators | EMA | Moving averages | `TrendDetector` |
| 3 | `filter()`, `map()` | R-squared | Trend quality | `TrendDetector` |
| 4 | Clases, `__init__` | Vectores | Feature extraction | `AccumulationZoneDetector` |
| 5 | Métodos, `self` | Similitud | Pattern matching | `SignalCombiner` |

**Ejercicio Semana 3**: Implementar `ATRLabeler`

```python
# Tu tarea: Implementar calculador de ATR
# Requisitos:
# 1. Usar dataclass para configuración (period)
# 2. Implementar calculate(candles) -> float
# 3. Manejar caso de datos insuficientes
# 4. Escribir test con datos sintéticos

from cgalpha_v2.domain.models import Candle

@dataclass
class ATRLabeler:
    period: int = 14
    
    def calculate(self, candles: list[Candle]) -> float:
        # Tu implementación aquí
        pass

# Test:
def test_atr_labeler():
    # Crear candles sintéticos
    # Verificar que ATR > 0
    pass
```

### Semana 5-6: Oracle Team

| Día | Python | Matemáticas | Trading | Implementación |
|-----|--------|-------------|---------|----------------|
| 1 | Dict comprehensions | Bayes | Predicción probabilística | `PredictionContext` |
| 2 | `defaultdict` | Features | Feature engineering | `FeatureExtractor` |
| 3 | `dataclass` anidados | Normalización | Feature scaling | `FeatureNormalizer` |
| 4 | Pydantic | Correlación | Feature selection | `FeatureSelector` |
| 5 | Validación | Overfitting | Model validation | `OracleValidator` |

### Semana 7-8: Causal Analysis Team

| Día | Python | Matemáticas | Trading | Implementación |
|-----|--------|-------------|---------|----------------|
| 1 | Herencia | Causalidad | Análisis de patrones | `PatternDetector` |
| 2 | Composición | Hipótesis | Hipótesis testing | `HypothesisGenerator` |
| 3 | DI | Confounders | Confounding factors | `CausalInference` |
| 4 | Factory pattern | Intervenciones | What-if analysis | `RecommendationEngine` |
| 5 | Strategy pattern | Counterfactuals | Scenario analysis | `GhostArchitect` |

---

## 5. SISTEMA DE EVALUACIÓN

### Niveles de Competencia

| Nivel | Python | Matemáticas | Trading | CGAlpha |
|-------|--------|-------------|---------|---------|
| **Junior I** | dataclass, Enum, Protocol | Probabilidad básica | Señales, ATR | Leer código |
| **Junior II** | Clases, métodos, DI | Estadística, vectores | Trend, acumulación | Implementar servicios |
| **Mid I** | Patrones, async | Series temporales | Oracle, predicción | Diseñar componentes |
| **Mid II** | Arquitectura | Causalidad | Risk management | Liderar módulos |

### Evaluación por Agente

```bash
# Evaluar nivel actual
cgalpha eval python    # Quiz de Python
cgalpha eval math      # Quiz de matemáticas
cgalpha eval trading   # Quiz de trading
cgalpha eval overall   # Evaluación completa

# Resultado ejemplo:
# Python: Junior II (65%)
# Math: Junior I (45%)
# Trading: Beginner (30%)
# Overall: Junior I - Ready for Signal Detection team
```

### Criterios de Promoción

| Promoción | Requisitos |
|-----------|------------|
| Junior I -> Junior II | 3 servicios implementados, 80% tests passing |
| Junior II -> Mid I | 1 módulo completo, code review aprobado |
| Mid I -> Mid II | Diseño arquitectónico aprobado por ARCHITECT |

---

## 6. INTEGRACIÓN CON V1: "PRODUCTION SUPPORT"

### Tu Rol en v1

Como Junior Developer, también tienes responsabilidades en el sistema en producción (v1):

| Tarea | Frecuencia | Comando |
|-------|------------|---------|
| Health check | Diario | `check_phase7.sh --with-analyze` |
| Métricas | Diario | Guardar en daily_log.jsonl |
| Bug reports | Según necesidad | Documentar en `.context/issues/` |
| Mejoras menores | Semanal | Solo con aprobación de ARCHITECT |

### Mejoras Permitidas (Riesgo Bajo)

```python
# Ejemplos de mejoras que un Junior puede hacer en v1:

# 1. Añadir logging
logger.debug(f"Signal detected: {signal}")

# 2. Mejorar mensajes de error
raise ConfigurationError(
    f"Invalid threshold {value}. Must be between 0 and 1",
    details={"parameter": "confidence_threshold", "value": value}
)

# 3. Añadir métricas
metrics.record("signal_detected", signal_type=signal.type.value)

# 4. Documentar funciones
def calculate_atr(candles: list[Candle], period: int = 14) -> float:
    """
    Calculate Average True Range.
    
    Args:
        candles: List of OHLCV candles
        period: EMA period (default 14)
    
    Returns:
        ATR value in price units
    
    Raises:
        ValueError: If len(candles) < period + 1
    """
```

### Mejoras Prohibidas (Requieren Aprobación)

- Cambiar arquitectura de módulos
- Modificar interfaces públicas
- Cambiar lógica de trading core
- Refactoring grande

---

## 7. COMANDOS CLI PROPUESTOS

### Comandos de Aprendizaje

```bash
# Sesiones de aprendizaje
cgalpha learn python <topic>      # Aprender concepto Python
cgalpha learn math <topic>        # Aprender concepto matemático
cgalpha learn trading <topic>     # Aprender concepto trading

# Preguntas a agentes
cgalpha ask <agent> "<question>"  # Preguntar a agente específico

# Evaluación
cgalpha eval [python|math|trading]  # Evaluación de conocimientos
cgalpha progress                    # Ver progreso actual

# Daily workflow
cgalpha daily --start              # Iniciar día (standup)
cgalpha daily --log "<entry>"      # Añadir entrada
cgalpha daily --end                # Terminar día (summary)

# Code review
cgalpha review <file>              # Solicitar revisión
cgalpha review --list              # Ver revisiones pendientes
```

### Comandos de Desarrollo

```bash
# Crear nuevo componente
cgalpha new service <name>         # Crear servicio nuevo
cgalpha new model <name>           # Crear modelo nuevo
cgalpha new test <name>            # Crear test nuevo

# Tests
cgalpha test <module>              # Ejecutar tests
cgalpha test --coverage            # Con cobertura

# Commits (con plantilla)
cgalpha commit                     # Commit guiado
```

---

## 8. PRÓXIMOS PASOS INMEDIATOS

### Configuración Inicial

1. **Crear estructura de aprendizaje**:
   ```bash
   mkdir -p cgalpha_v2/learning/{exercises,notes,solutions}
   mkdir -p .context/daily_logs
   ```

2. **Crear daily_log.jsonl**:
   ```bash
   touch .context/daily_logs/daily_log.jsonl
   ```

3. **Primer standup**:
   ```bash
   ./scripts/check_phase7.sh --with-analyze
   # Guardar métricas
   ```

### Semana 1: Onboarding

| Día | Actividad |
|-----|-----------|
| 1 | Leer este plan completo. Preguntas a ARCHITECT |
| 2 | Leer `cgalpha_v2/domain/models/signal.py`. Preguntas a PYTHON_TUTOR |
| 3 | Ejercicio: crear `MarketSnapshot` dataclass |
| 4 | Leer `cgalpha_v2/domain/models/trade.py`. Preguntas a TRADING_EXPERT |
| 5 | Quiz de evaluación inicial |

---

## 9. PERFIL DEL ESTUDIANTE

**Nivel**: Básico
**Preferencia**: Aprender haciendo
**Objetivo**: Programar Python mientras construye CGAlpha v2

---

## 10. RUTINA DIARIA DETALLADA (Nivel Básico - Aprender Haciendo)

### Estructura de Clase: 45-60 minutos

```
+---------------------------------------------------------------+
|  MIN 0-5: WARM-UP                                             |
|  +-- Ejecutar: ./scripts/check_phase7.sh --with-analyze      |
|  +-- Ver métricas: blind_test_ratio, order_book_coverage     |
|  +-- Pensar: "¿Qué significa HOLD_V03 hoy?"                  |
+---------------------------------------------------------------+
|  MIN 5-20: CODE READING (15 min)                              |
|  +-- Abrir 1 archivo de cgalpha_v2/                          |
|  +-- Leer en voz alta (o mentalmente)                        |
|  +-- Subrayar lo que NO entiendes                            |
|  +-- Preguntar al LLM: "¿Qué significa X?"                   |
+---------------------------------------------------------------+
|  MIN 20-45: HANDS-ON (25 min)                                 |
|  +-- Ejercicio pequeño relacionado con el archivo            |
|  +-- Escribir código, ejecutar, ver errores                  |
|  +-- Corregir, intentar de nuevo                             |
|  +-- Celebrar cuando funcione                                |
+---------------------------------------------------------------+
|  MIN 45-60: WRAP-UP (15 min)                                  |
|  +-- Guardar progreso en daily_log.jsonl                     |
|  +-- Escribir: "Hoy aprendí..."                              |
|  +-- Commit (si hay código nuevo)                            |
+---------------------------------------------------------------+
```

### Ejemplo de Clase Día 1

**MIN 0-5: WARM-UP**
```bash
./scripts/check_phase7.sh --with-analyze
# Observa: blind_test_ratio = 1.0, order_book_coverage = 0.0
# Conclusión: HOLD_V03 - falta data de order book
```

**MIN 5-20: CODE READING**
```python
# Abrir: cgalpha_v2/domain/models/signal.py

# Leer línea por línea:
@dataclass(frozen=True)  # ¿Qué es @dataclass? ¿Qué es frozen?
class Signal:            # ¿Qué es una clase?
    symbol: str          # ¿Qué es str?
    direction: SignalDirection  # ¿De dónde viene esto?
    confidence: float    # ¿Por qué float y no int?
    
# Preguntas para el LLM:
# - "¿Qué es @dataclass?"
# - "¿Por qué frozen=True?"
# - "¿Qué significa symbol: str?"
```

**MIN 20-45: HANDS-ON**
```python
# Ejercicio: Crear tu primer dataclass

# Paso 1: Abrir archivo nuevo
# cgalpha_v2/learning/exercises/mi_primer_dataclass.py

# Paso 2: Escribir (copiar y modificar)
from dataclasses import dataclass

@dataclass
class MiSenal:
    simbolo: str
    precio: float

# Paso 3: Ejecutar
python cgalpha_v2/learning/exercises/mi_primer_dataclass.py

# Paso 4: Añadir frozen=True y ver qué pasa
@dataclass(frozen=True)
class MiSenal:
    simbolo: str
    precio: float

# Paso 5: Intentar modificar y ver error
s = MiSenal("BTC", 65000)
s.precio = 66000  # ¡Error! ¿Por qué?
```

**MIN 45-60: WRAP-UP**
```jsonl
{"date": "2026-02-17", "day": 1, "warmup": {"phase7": "HOLD_V03", "metrics": {"blind_test_ratio": 1.0, "order_book_coverage": 0.0}}, "code_reading": {"file": "signal.py", "lines_read": 50, "concepts_found": ["dataclass", "frozen", "class"]}, "questions_asked": ["¿Qué es @dataclass?", "¿Por qué frozen=True?"], "hands_on": {"exercise": "mi_primer_dataclass.py", "completed": true, "errors_encountered": ["FrozenInstanceError"], "learnings": ["frozen hace el objeto inmutable", "no puedo modificar atributos de dataclass frozen"]}, "next_day": "Aprender sobre Enum y SignalDirection"}
```

### Plan Semanal (Semana 1)

| Día | Archivo a Leer | Concepto Python | Ejercicio |
|-----|----------------|-----------------|-----------|
| 1 | `signal.py` | `@dataclass` | Crear `MiSenal` |
| 2 | `signal.py` | `frozen=True` | Intentar modificar frozen |
| 3 | `types.py` | `Enum` | Crear `MiDireccion` (LONG/SHORT) |
| 4 | `signal.py` | Tipos (`str`, `float`, `int`) | Añadir tipos correctos |
| 5 | `trade.py` | Repaso + Quiz | Mini-test de la semana |

---

## 11. FORMATO TRANSFERIBLE A CUALQUIER LLM

### Estructura de Datos para Transferencia

```
.context/
├── learning_progress.json     # Progreso general (machine-readable)
├── daily_logs/
│   └── daily_log.jsonl        # Logs diarios (append-only)
├── exercises/
│   ├── completed/             # Ejercicios completados
│   └── pending/               # Ejercicios pendientes
└── questions/
    └── questions.jsonl        # Preguntas hechas + respuestas
```

### learning_progress.json

```json
{
  "student": {
    "level": "beginner",
    "start_date": "2026-02-17",
    "current_week": 1,
    "current_day": 1
  },
  "python_skills": {
    "dataclass": {"status": "learning", "exercises_completed": 0, "confidence": 0},
    "enum": {"status": "pending", "exercises_completed": 0, "confidence": 0},
    "protocol": {"status": "pending", "exercises_completed": 0, "confidence": 0},
    "exceptions": {"status": "pending", "exercises_completed": 0, "confidence": 0}
  },
  "math_skills": {
    "probability": {"status": "pending", "confidence": 0},
    "statistics": {"status": "pending", "confidence": 0},
    "vectors": {"status": "pending", "confidence": 0}
  },
  "trading_skills": {
    "signals": {"status": "pending", "confidence": 0},
    "atr": {"status": "pending", "confidence": 0},
    "trends": {"status": "pending", "confidence": 0}
  },
  "cgalpha_comprehension": {
    "signal_detection": {"files_read": [], "understood": false},
    "oracle": {"files_read": [], "understood": false},
    "causal_analysis": {"files_read": [], "understood": false}
  },
  "last_updated": "2026-02-17T00:00:00Z"
}
```

### questions.jsonl

```jsonl
{"timestamp": "2026-02-17T12:30:00Z", "question": "¿Qué es @dataclass?", "context": "signal.py:15", "answer": "Un decorador que genera automáticamente __init__, __repr__, etc.", "understood": true}
{"timestamp": "2026-02-17T12:35:00Z", "question": "¿Por qué frozen=True?", "context": "signal.py:15", "answer": "Hace la clase inmutable. No se pueden modificar atributos después de crear.", "understood": true}
```

### Cualquier LLM puede continuar:

```bash
# Prompt para nuevo LLM:
"Lee .context/learning_progress.json y .context/daily_logs/daily_log.jsonl.
 El estudiante está en día X, semana Y.
 Continúa la enseñanza desde donde se quedó.
 Sigue el formato establecido en LEARNING_PLAN.md."
```

---

## 12. TRANSFORMACIÓN CLI → PÁGINA WEB

### Arquitectura Propuesta

```
+-------------------+         +-------------------+         +-------------------+
|   CLI (Actual)    |         |   API Layer       |         |   Web Page        |
+-------------------+         +-------------------+         +-------------------+
| cgalpha learn     |  ---->  | FastAPI/Flask     |  ---->  | React/Vue/Svelte  |
| cgalpha ask       |         |                   |         |                   |
| cgalpha eval      |         | REST endpoints    |         | Dashboard UI      |
| cgalpha daily     |         | JSON responses    |         | Progress charts   |
+-------------------+         +-------------------+         +-------------------+
          |                           |                           |
          +---------------------------+---------------------------+
                                      |
                             +--------v--------+
                             | .context/ (data)|
                             +-----------------+
```

### Endpoints API Propuestos

```python
# api/learning.py

@app.get("/api/progress")
async def get_progress():
    """Retorna learning_progress.json"""
    return load_json(".context/learning_progress.json")

@app.get("/api/daily-log")
async def get_daily_log(date: str = None):
    """Retorna entradas del daily log"""
    return load_jsonl(".context/daily_logs/daily_log.jsonl", date)

@app.post("/api/ask")
async def ask_agent(agent: str, question: str):
    """Envía pregunta a agente IA"""
    # PYTHON_TUTOR, MATH_TUTOR, TRADING_EXPERT
    return {"answer": agent_response}

@app.post("/api/complete-exercise")
async def complete_exercise(exercise_id: str, code: str):
    """Marca ejercicio como completado"""
    # Actualiza learning_progress.json
    return {"status": "completed"}

@app.get("/api/next-lesson")
async def get_next_lesson():
    """Retorna la siguiente lección basada en progreso"""
    return {"file": "signal.py", "concept": "Enum", "exercise": "create_direction_enum"}
```

### Diseño de Página Web (Prompt para Vibe Coding)

```markdown
# Prompt para crear página web de aprendizaje CGAlpha

Crea una página web de dashboard para el plan de aprendizaje de CGAlpha.

## Datos de entrada (JSON)
- learning_progress.json: Progreso del estudiante
- daily_log.jsonl: Historial de actividades
- questions.jsonl: Preguntas y respuestas

## Páginas requeridas

### 1. Dashboard Principal
- Tarjeta con nivel actual (Beginner/Intermediate/Advanced)
- Barra de progreso de Python skills
- Última actividad
- Botón "Continuar lección"

### 2. Página de Lección
- Código a leer (syntax highlighting)
- Explicación del concepto
- Editor de código para ejercicio
- Botón "Ejecutar" (envía a API)
- Feedback del agente

### 3. Página de Progreso
- Gráfico de progreso por semana
- Lista de ejercicios completados
- Métricas: archivos leídos, preguntas hechas, ejercicios

### 4. Página de Preguntas
- Historial de preguntas
- Filtrar por agente (Python/Math/Trading)
- Buscar en preguntas

## Estilo
- Tema oscuro (estilo VS Code)
- Colores: verde para éxito, rojo para error, azul para info
- Fuente monospace para código
- Responsive (mobile-first)

## Tech stack sugerido
- Svelte + Vite (simple y rápido)
- Chart.js para gráficos
- Monaco Editor para código
- Tailwind CSS para estilos
```

### Estructura de Archivos Web

```
cgalpha_web/
├── src/
│   ├── routes/
│   │   ├── +page.svelte          # Dashboard
│   │   ├── lesson/
│   │   │   └── +page.svelte      # Lección del día
│   │   ├── progress/
│   │   │   └── +page.svelte      # Progreso
│   │   └── questions/
│   │       └── +page.svelte      # Historial preguntas
│   ├── lib/
│   │   ├── api.ts                # Llamadas a API
│   │   └── stores.ts             # Estado global
│   └── app.html
├── static/
│   └── favicon.png
└── package.json
```

### Beneficios de la Web

| Aspecto | CLI | Web |
|---------|-----|-----|
| Visualización | Texto | Gráficos, charts |
| Código | Editor externo | Monaco editor integrado |
| Historial | cat archivo | Búsqueda, filtros |
| Progreso | JSON crudo | Barras, círculos |
| Accesibilidad | Terminal | Cualquier dispositivo |
| Compartir | No | Sí (URL) |

---

## 13. PRÓXIMOS PASOS INMEDIATOS

### Hoy (Día 1)

1. **Crear estructura de archivos**:
   ```bash
   mkdir -p .context/daily_logs
   mkdir -p .context/exercises/{completed,pending}
   mkdir -p .context/questions
   touch .context/learning_progress.json
   touch .context/daily_logs/daily_log.jsonl
   touch .context/questions/questions.jsonl
   ```

2. **Inicializar learning_progress.json**:
   ```bash
   # Copiar el JSON de la sección 11
   ```

3. **Primera clase**:
   - Leer `cgalpha_v2/domain/models/signal.py`
   - Preguntar: "¿Qué es @dataclass?"
   - Ejercicio: Crear `mi_primer_dataclass.py`

### Mañana (Día 2)

- Continuar con `signal.py`
- Concepto: `frozen=True`
- Ejercicio: Intentar modificar dataclass frozen

### Esta Semana

- Completar Semana 1 del plan
- 5 días de ejercicios
- 1 archivo de CGAlpha leído por día
- 1 concepto de Python por día

---

**Este plan está diseñado para ser transferible a cualquier LLM. Solo necesitas compartir los archivos en `.context/` y el nuevo LLM puede continuar exactamente donde dejaste.**