# Clase: Enum

## PYTHON_TUTOR: Enum en Python

### ¿Qué es?
Un **Enum** (Enumeración) es un conjunto de constantes con nombre. En lugar de usar números mágicos o strings, usamos nombres legibles que representan valores fijos.

### Sintaxis Básica
```python
from enum import Enum

class Direccion(Enum):
    LONG = "long"
    SHORT = "short"
```

### Acceso a Valores
```python
# Acceder al enum
print(Direccion.LONG)           # <Direccion.LONG: 'long'>
print(Direccion.LONG.value)     # 'long'
print(Direccion.LONG.name)      # 'LONG'

# Comparación
if Direccion.LONG == Direccion.LONG:
    print("Son iguales")

# Iteración
for d in Direccion:
    print(f"{d.name} = {d.value}")
# LONG = long
# SHORT = short
```

### Ejemplo de Trading (CGAlpha v2)
```python
from enum import Enum

class SignalDirection(Enum):
    """Dirección de una señal de trading."""
    LONG = "long"   # Comprar
    SHORT = "short" # Vender

class TradeOutcome(Enum):
    """Resultado de un trade en múltiplos de ATR."""
    STRONG_LOSS = "strong_loss"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    WIN = "win"
    STRONG_WIN = "strong_win"

# Uso en una señal
direccion = SignalDirection.LONG
print(f"Señal: {direccion.value}")  # Señal: long
```

### Errores Comunes
```python
# MAL: Usar strings directamente
direccion = "long"  # ¿Qué pasa si escribes "Long" o "LONG"?

# BIEN: Usar Enum
direccion = SignalDirection.LONG  # Sin ambigüedad
```

---

## MATH_TUTOR: Enum y Conjuntos

### Concepto Matemático
Un **Enum** es matemáticamente equivalente a un **conjunto finito** donde cada elemento tiene un nombre único.

### Formalización
```
Sea E un Enum con valores v₁, v₂, ..., vₙ

E = {v₁, v₂, ..., vₙ}

donde cada vᵢ es único y pertenece a E
```

### Propiedades de Conjunto
```python
from enum import Enum

class SignalDirection(Enum):
    LONG = "long"
    SHORT = "short"

# El Enum define un conjunto finito
# E = {LONG, SHORT}

# Pertenencia (como en conjuntos)
print(SignalDirection.LONG in SignalDirection)  # True
print("long" in [d.value for d in SignalDirection])  # True

# Cardinalidad
print(len(SignalDirection))  # 2
```

### Aplicación: Probabilidad sobre Enum
```python
# Probabilidad de cada dirección en histórico
historico = [SignalDirection.LONG, SignalDirection.LONG, 
             SignalDirection.SHORT, SignalDirection.LONG]

def probabilidad_direccion(historico: list, direccion: SignalDirection) -> float:
    """P(direccion) = count(direccion) / total"""
    total = len(historico)
    count = sum(1 for d in historico if d == direccion)
    return count / total

print(f"P(LONG) = {probabilidad_direccion(historico, SignalDirection.LONG):.2f}")
# P(LONG) = 0.75
```

---

## TRADING_EXPERT: Enum para Trading

### ¿Por qué Enum para LONG/SHORT?

**Problema con strings:**
```python
# MAL: Strings son peligrosos
direccion = "long"   # ¿Y si escribes "Long"?
if direccion == "LONG":  # ¡No coincide!
    print("Error silencioso")
```

**Solución con Enum:**
```python
# BIEN: Enum es seguro
from cgalpha_v2.domain.models.signal import SignalDirection

direccion = SignalDirection.LONG
if direccion == SignalDirection.LONG:  # Siempre funciona
    print("Entrada larga")
```

### Beneficios en Trading Algorítmico

| Aspecto | String | Enum |
|---------|--------|------|
| Typos | `"l0ng"` silencioso | Error en compile-time |
| Autocomplete | No | Sí |
| Documentación | Implícita | Explícita |
| Validación | Manual | Automática |

### Código en CGAlpha v2
```python
# signal.py
class SignalDirection(Enum):
    LONG = "long"
    SHORT = "short"

@dataclass(frozen=True)
class Signal:
    signal_id: str
    direction: SignalDirection  # No es string, es Enum
    entry_price: float
    confidence: float

# Uso
senal = Signal(
    signal_id="SIG_001",
    direction=SignalDirection.LONG,  # Type-safe
    entry_price=65000.0,
    confidence=0.85
)

# Lógica de trading
if senal.direction == SignalDirection.LONG:
    take_profit = senal.entry_price + atr * 2.0
    stop_loss = senal.entry_price - atr * 1.0
else:  # SHORT
    take_profit = senal.entry_price - atr * 2.0
    stop_loss = senal.entry_price + atr * 1.0
```

### Consideraciones de Riesgo
- **Siempre** valida que el Enum tenga todos los valores posibles
- **Nunca** conviertas Enum a string y viceversa manualmente
- **Usa** `.value` solo para serialización (API, DB)

---

## ARCHITECT: ¿Dónde vive SignalDirection?

### Decisión de Diseño
`SignalDirection` vive en `cgalpha_v2/domain/models/signal.py`

### Justificación

**1. Bounded Context: Signal Detection**
```
SignalDirection pertenece al contexto de "Signal Detection"
porque define la dirección de una señal detectada.
```

**2. Ubicación en la Arquitectura**
```
cgalpha_v2/
  domain/
    models/
      signal.py      ← SignalDirection vive aquí
      trade.py       ← TradeOutcome vive aquí
```

**3. Dependencias**
```
signal.py no depende de nada externo
trade.py puede importar SignalDirection de signal.py
```

### Código de Referencia
```python
# domain/models/signal.py
from enum import Enum

class SignalDirection(Enum):
    """Direction of a detected trading signal."""
    LONG = "long"
    SHORT = "short"

# domain/models/trade.py
from cgalpha_v2.domain.models.signal import SignalDirection

class TradeOutcome(Enum):
    """Ordinal classification of trade result."""
    STRONG_LOSS = "strong_loss"
    LOSS = "loss"
    BREAKEVEN = "breakeven"
    WIN = "win"
    STRONG_WIN = "strong_win"
```

### Alternativas Descartadas

| Alternativa | Por qué no |
|-------------|------------|
| `shared/types.py` | SignalDirection es del dominio, no un tipo genérico |
| `shared/enums.py` | Rompe bounded contexts |
| String literal | Pierde type-safety |

### Ejercicio
¿Por qué `TradeOutcome` está en `trade.py` y no en `signal.py`?

---

## Ejercicios

### 1. PYTHON_TUTOR
Crea un Enum `OrderType` con valores: MARKET, LIMIT, STOP_LIMIT.

```python
# Tu código aquí
from enum import Enum

class OrderType(Enum):
    # ...
    pass
```

### 2. MATH_TUTOR
Dado el histórico de trades, calcula P(WIN) usando TradeOutcome.

```python
historico = [
    TradeOutcome.WIN, TradeOutcome.WIN, TradeOutcome.LOSS,
    TradeOutcome.WIN, TradeOutcome.BREAKEVEN, TradeOutcome.WIN
]

# Calcula P(WIN)
```

### 3. TRADING_EXPERT
Explica qué pasa si usas `direccion = "long"` en lugar de `SignalDirection.LONG`.

### 4. ARCHITECT
¿Dónde ubicarías un enum `Exchange` con valores BINANCE, KRAKEN, COINBASE?