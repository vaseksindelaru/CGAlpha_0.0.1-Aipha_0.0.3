# RUTA.md - Plan de Aprendizaje Python + CGAlpha v2

## CGALPHA V2 - AVANCE DEL LLM AVANZADO

El LLM avanzado construyó la **Foundation** de cgalpha_v2:

### Domain Models (Value Objects)
| Archivo | Contenido |
|---------|-----------|
| `signal.py` | Candle, SignalDirection, DetectorVerdict, Signal |
| `trade.py` | TradeOutcome, Trajectory, TradeRecord |
| `prediction.py` | Predicciones del Oracle |
| `config.py` | Configuración de trading |
| `health.py` | Health checks |

### Domain Ports (Interfaces)
| Archivo | Contenido |
|---------|-----------|
| `config_port.py` | Puerto de configuración |
| `data_port.py` | Puerto de datos |
| `llm_port.py` | Puerto de LLM |
| `memory_port.py` | Puerto de memoria |
| `prediction_port.py` | Puerto de predicciones |

### Shared
| Archivo | Contenido |
|---------|-----------|
| `types.py` | SignalId, TradeId, Confidence, ATRMultiple |
| `exceptions.py` | Excepciones del dominio |

---

## RUTA DE 20 HITOS

### SEMANA 1: Fundamentos Python
| Día | Hito | Archivo cgalpha_v2 | Líneas |
|-----|------|-------------------|--------|
| 1 | **Enum** | signal.py | 30-35 |
| 2 | **@dataclass** | signal.py | 37-65 |
| 3 | **frozen=True** | signal.py | 37-65 |
| 4 | **__post_init__** | signal.py | 66-74 |
| 5 | **NewType** | types.py | 23-36 |

### SEMANA 2: Matemáticas para Trading
| Día | Hito | Concepto | Aplicación |
|-----|------|----------|------------|
| 6 | **Probabilidad** | P(A|B) | Confidence en Signal |
| 7 | **Media, StdDev** | Estadística básica | ATR calculation |
| 8 | **MFE/MAE** | Excursiones | Trajectory en TradeRecord |
| 9 | **Ratios** | Proporciones | capture_efficiency |
| 10 | **Repaso Matemáticas** | Quiz | Integración |

### SEMANA 3: Trading Concepts
| Día | Hito | Concepto | Archivo |
|-----|------|----------|---------|
| 11 | **Señales** | ¿Qué es una señal? | Signal class |
| 12 | **ATR** | Volatilidad | atr_value en Signal |
| 13 | **TP/SL** | Barriers | tp_factor, sl_factor |
| 14 | **Triple Coincidence** | Fusión de detectores | TripleCoincidenceResult |
| 15 | **Repaso Trading** | Quiz | Integración |

### SEMANA 4: Arquitectura
| Día | Hito | Concepto | Archivo |
|-----|------|----------|---------|
| 16 | **Value Objects** | Inmutabilidad | signal.py, trade.py |
| 17 | **Ports** | Interfaces | ports/*.py |
| 18 | **Dependency Inversion** | DI | bootstrap.py |
| 19 | **Bounded Contexts** | DDD | domain/models/ |
| 20 | **Proyecto Final** | Integración | Todos |

---

## DETALLE DE HITOS

### Hito 1: Enum
**Problemas:**
- PYTHON: ¿Qué es Enum y cómo se declara?
- MATH: ¿Cómo se relaciona Enum con conjuntos?
- TRADING: ¿Por qué Enum para LONG/SHORT?
- ARCH: ¿Dónde debe vivir SignalDirection?

**Código de referencia:**
```python
class SignalDirection(Enum):
    LONG = "long"
    SHORT = "short"
```

---

### Hito 2: @dataclass
**Problemas:**
- PYTHON: ¿Qué es @dataclass y qué genera?
- MATH: ¿Cómo se relaciona con estructuras algebraicas?
- TRADING: ¿Por qué dataclass para Candle?
- ARCH: ¿Value Object vs Entity?

**Código de referencia:**
```python
@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
```

---

### Hito 3: frozen=True
**Problemas:**
- PYTHON: ¿Qué hace frozen=True?
- MATH: ¿Inmutabilidad en matemáticas?
- TRADING: ¿Por qué señales inmutables?
- ARCH: ¿Value Object pattern?

**Código de referencia:**
```python
@dataclass(frozen=True)
class Signal:
    signal_id: str
    direction: SignalDirection
    # No se puede modificar después de crear
```

---

### Hito 4: __post_init__
**Problemas:**
- PYTHON: ¿Qué es __post_init__?
- MATH: ¿Validación de invariantes?
- TRADING: ¿Validar que high >= low?
- ARCH: ¿Dónde va la validación?

**Código de referencia:**
```python
def __post_init__(self) -> None:
    if self.high < self.low:
        raise ValueError("high debe ser >= low")
```

---

### Hito 5: NewType
**Problemas:**
- PYTHON: ¿Qué es NewType?
- MATH: ¿Tipos vs valores?
- TRADING: ¿Por qué SignalId vs str?
- ARCH: ¿Seguridad de tipos?

**Código de referencia:**
```python
SignalId = NewType("SignalId", str)
TradeId = NewType("TradeId", str)
Confidence = NewType("Confidence", float)
```

---

### Hito 6: Probabilidad
**Problemas:**
- PYTHON: ¿Cómo calcular probabilidades en Python?
- MATH: ¿P(A|B) probabilidad condicional?
- TRADING: ¿Confidence como probabilidad?
- ARCH: ¿Dónde va la lógica probabilística?

---

### Hito 7: Media, StdDev
**Problemas:**
- PYTHON: ¿statistics module?
- MATH: ¿Media, desviación estándar?
- TRADING: ¿ATR como media de rangos?
- ARCH: ¿Servicio de cálculo?

---

### Hito 8: MFE/MAE
**Problemas:**
- PYTHON: ¿Cómo trackear MFE/MAE?
- MATH: ¿Máximos y mínimos de series?
- TRADING: ¿Qué es MFE/MAE?
- ARCH: ¿Trajectory como value object?

---

### Hito 9: Ratios
**Problemas:**
- PYTHON: ¿Cómo calcular ratios?
- MATH: ¿Proporciones y porcentajes?
- TRADING: ¿capture_efficiency?
- ARCH: ¿Property vs método?

---

### Hito 10: Repaso Matemáticas
**Problemas:**
- PYTHON: Integración de conceptos
- MATH: Quiz de repaso
- TRADING: Aplicación integrada
- ARCH: Diseño de calculadora

---

### Hito 11-15: Trading Concepts
(Se detallarán en los guiones específicos)

---

### Hito 16-20: Arquitectura
(Se detallarán en los guiones específicos)

---

## CÓMO USAR ESTA RUTA

1. El estudiante abre la interfaz
2. Ve el hito actual en PROGRESS.md
3. Solicita clase al LLM avanzado
4. Estudia y completa el hito
5. Avanza al siguiente