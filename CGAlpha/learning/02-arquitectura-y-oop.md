---
type: learning-note
project: CGAlpha
tags: [proyecto/cgalpha, learning, fase-3, oop, arquitectura]
created: 2026-07-27
part: 2-of-5
---

# Clase Magistral: Arquitectura y OOP — El Esqueleto del Oracle

**Nivel**: S1 (Learning) — Fundamentos  
**Fase**: Fase 3 — Estructura Orientada a Objetos  
**Prerrequisito**: Clase 1 (El Viaje de un Dato)

---

## 0. Objetivo

Entender por qué el Oracle se construyó como una clase y no como funciones sueltas, y cómo esa decisión escala cuando el sistema crece de un script a un sistema de producción.

---

## 1. ¿Por qué una clase y no funciones sueltas?

### La tentación del junior

```python
modelo = None
encoders = {}

def entrenar(datos):
    global modelo, encoders
    ...

def predecir(features):
    global modelo
    ...
```

**El problema**: `modelo` y `encoders` son estado global. Dos instancias (ej: BTCUSDT + ETHUSDT) se pisarían. No puede haber aislamiento entre ellas.

### La solución con clase

```python
class OracleTrainer_v3:
    def __init__(self):
        self.model = None
        self._encoders = {}
        self._training_metrics = {}
```

Cada instancia tiene sus propios atributos completamente aislados de cualquier otra.

---

## 2. Anatomía de `__init__` y el rol de `self`

```python
class OracleTrainer_v3:
    def __init__(self):
        self.model = None
        self._encoders = {}
        self._training_metrics = {}
        self._feature_cols = [
            "vwap_at_retest", "obi_10_at_retest", "cumulative_delta_at_retest",
            "delta_divergence", "atr_14", "regime", "direction",
        ]
        self.min_confidence = 0.68
```

### 2.1 `self` es "esta instancia particular"

Cuando haces `oracle_btc = OracleTrainer_v3()`, Python crea una región de memoria separada. Cada llamada `oracle_btc.train_model()` internamente se traduce a `OracleTrainer_v3.train_model(oracle_btc, ...)`.

### 2.2 `_feature_cols` como contrato, no como parámetro configurable

La lista de 7 columnas está hardcodeada en `__init__`. Esto es una **decisión deliberada**: el contrato de features del Oracle es parte de la identidad del objeto, no un parámetro de runtime.

Un cambio a esa lista = cambio **arquitectónico** = categoría 3 en la gobernanza del proyecto.

### 2.3 Convención `_` para miembros internos

`_encoders`, `_training_metrics` — el guion bajo es convención: "esto es interno, no lo toques desde fuera". Python no lo fuerza técnicamente, es una señal de intención entre programadores.

---

## 3. `@dataclass` en acción: `OraclePrediction`

```python
@dataclass
class OraclePrediction:
    trade_id: str
    confidence: float
    suggested_action: str
    estimated_delta_causal: float
    is_placeholder: bool = False
```

### 3.1 Dataclass vs Servicio — la distinción clave

| Aspecto | OracleTrainer_v3 (servicio) | OraclePrediction (DTO) |
|---------|----------------------------|--------------------------|
| **Rol** | Comportamiento: decide, entrena, predice | Transporte: lleva el resultado de una decisión |
| **Tiene métodos** | Sí (train_model, predict, save_to_disk) | No (solo campos de datos) |
| **Lifecyle** | Long-lived, persiste entre predicciones | Efímero, nace con la predicción y muere con el log |
| **Nombre** | -er (agente de servicio) | Paquete de datos puro |

### 3.2 `is_placeholder: bool = False` — corrección estructural de BUG-4

Antes de este campo, no había forma de distinguir una predicción real del modelo del fallback hardcodeado (confidence=0.85 siempre). `is_placeholder` es la solución directa: el campo booleano corrige un bug de confiabilidad, no solo es un contenedor pasivo.

---

## 4. El patrón `create_default()`: fábricas

```python
class OracleTrainer_v3:
    @classmethod
    def create_default(cls) -> "OracleTrainer_v3":
        return cls()
```

### 4.1 ¿Por qué no llamar `OracleTrainer_v3()` directamente?

Estabilidad de la API a través del tiempo. Si dentro de 6 meses `__init__` necesita un argumento nuevo, todos los 40 lugares que usan `create_default()` se mantienen intactos. Solo cambia el método de fábrica.

### 4.2 `@classmethod` vs instancia

- `@classmethod` recibe `cls` (la clase misma), no `self` (una instancia existente)
- Permite crear nuevas instancias desde la clase, no desde un objeto
- Actúa como constructor alternativo con nombre semántico explícito

### 4.3 Principio de indirección controlada

> Interponer un punto único de creación entre "quiero un objeto" y "así es como se construye" permite cambiar cómo se construye sin tocar quién lo usa.

---

## 5. Excepciones personalizadas como contrato

```python
try:
    oracle.load_from_disk("aipha_memory/models/oracle_v3.joblib")
except IntegrityError:
    logger.critical("Modelo corrupto — cargando placeholder de emergencia")
    oracle = OracleTrainer_v3.create_default()
```

`IntegrityError` es parte del contrato público de la clase. Comunica qué comportamiento anómalo esperas y manejar, en lugar de dejar que falle en silencio.

Esto conecta con la filosofía del proyecto completa: **fallos explícitos > fallos silenciosos**. Igual que `_must_get()` del MemoryPolicyEngine en la Fase v4.

---

## 6. Mapa completo de la arquitectura del Oracle

```
OracleTrainer_v3 (Servicio - comportamiento)
├── __init__()                    ← Estado inicial aislado
├── create_default()  [classmethod] ← Fábrica, punto único de creación
├── load_training_dataset()        ← Acumula samples en memoria
├── train_model()                  ← Entrena + evalúa train/test split
├── predict()                      ← Produce...
│       ↓
│   OraclePrediction [@dataclass]  ← DTO (datos puros)
│       ├── confidence: float
│       ├── suggested_action: str
│       └── is_placeholder: bool  ← Corrige BUG-4 estructuralmente
│
├── save_to_disk()                 ← Persistencia con SHA256
└── load_from_disk()               ← Puede lanzar IntegrityError
```

---

## 🔧 Práctica con Graphify

```bash
# Ver la comunidad completa del Oracle y sus conexiones
graphify explain "OracleTrainer_v3" --graph graphify-out/graph.json

# Encontrar la ruta más corta entre detector y Oracle
graphify path "TripleCoincidenceDetector" "OracleTrainer_v3" --graph graphify-out/graph.json

# Ver qué archivos más importan al Oracle
graphify explain "oracle" --graph graphify-out/graph.json

# Explorar la cadena del pipeline completo
graphify path "generate_realistic_ohlcv" "OracleTrainer_v3" --graph graphify-out/graph.json
```

Usa estos comandos mientras lees esta clase — verás cómo los conceptos abstractos (flujo de datos, acoplamiento) tienen representación física en los nodos y aristas del grafo.