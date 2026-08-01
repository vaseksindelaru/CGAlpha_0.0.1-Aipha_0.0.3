---
type: learning-note
project: CGAlpha
tags: [proyecto/cgalpha, learning, fase-4, pandas, sklearn, ml]
created: 2026-07-27
part: 3-of-5
---

# Clase Magistral: Manipulación de Datos y ML — Pandas + Scikit-Learn

**Nivel**: S1 (Learning) — Fundamentos  
**Fase**: Fase 4 — Motor Cuantitativo  
**Prerrequisito**: Clase 2 (Arquitectura y OOP)

---

## 0. Objetivo

Entender cómo una tabla de números se convierte en la probabilidad de que un precio rebote o rompa una zona — y por qué cada línea del pipeline es una decisión de riesgo, no solo una decisión técnica.

---

## 1. El DataFrame como contrato, no como tabla bonita

### 1.1 Construcción del feature matrix

```python
X = df[self._feature_cols]
X = X.apply(pd.to_numeric, errors="coerce")
X = X.fillna(0.0)
```

Cada línea resuelve un problema distinto:

| Línea | Problema que resuelve | Decisión de riesgo |
|-------|------------------------|---------------------|
| `df[self._feature_cols]` | Si faltan columnas → KeyError inmediato | Prefiere explotar aquí a continuar con datos faltantes silenciosos |
| `apply(pd.to_numeric, errors="coerce")` | Valores sucios (strings, None) del WebSocket real | `coerce` convierte lo imposible a NaN en vez de detener el pipeline |
| `fillna(0.0)` | NaN de la coerción previa | **Asume que 0 es razonable para todas las columnas** — sesgo silencioso (ver discusión) |

### 1.2 La trampa de `fillna(0.0)`

Para `obi_10_at_retest`, 0.0 no significa "dato faltante" — significa **equilibrio perfecto entre compradores y vendedores**. El proyecto documenta esta como área de mejora futura: imptación específica por columna o usar XGBoost que maneja NaN nativamente.

---

## 2. LabelEncoder: traducción de categorías a números

### 2.1 Cómo funciona

```python
encoder = LabelEncoder()
X["regime"] = encoder.fit_transform(X["regime"])
self._encoders["regime"] = encoder  # guardado para inferencia futura
```

`fit_transform` es dos operaciones:
1. **fit**: examina valores únicos, los ordena alfabéticamente → HIGH_VOL=0, LATERAL=1, TREND=2
2. **transform**: aplica ese mapeo a los datos reales

### 2.2 La trampa oculta (ya documentada como debilidad)

El mapeo depende del **orden alfabético de los valores en ese entrenamiento específico**. Si un reentrenamiento aparece "HIGH_VOL" que no existía antes, el orden cambia: el HIGH_VOL=0 que antes era LATERAL ahora significa otra cosa. El modelo no se queja — simplemente predice con significado desplazado.

Por eso se guarda `self._encoders["regime"]`. En inferencia, debe reusarse el encoder del entrenamiento — nunca crear uno nuevo.

### 2.3 Solución estructural futura

Reemplazar LabelEncoder por columnas binarias deterministas: `is_trending_up`, `is_trending_down`, `is_lateral`. Más verboso, pero elimina la dependencia del orden alfabético y la fragilidad entre reentrenamientos.

---

## 3. train_test_split: la diferencia entre memorizar y aprender

### 3.1 El problema antes de la corrección (BUG-1)

```python
# ANTES (BUG-1): modelo evaluado sobre los mismos datos que entrenó
model.fit(X, y)
train_accuracy = model.score(X, y)  # 98%+ — memorización, no aprendizaje
```

Esto es como dar al estudiante las preguntas del examen + respuestas, y luego evaluarlo con exactamente esas preguntas.

### 3.2 La corrección

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model.fit(X_train, y_train)
train_accuracy = model.score(X_train, y_train)  # 85% — modelo memorizó ~85%
test_accuracy = model.score(X_test, y_test)      # 68% — generalización real
```

### 3.3 Cada parámetro merece diseción

| Parámetro | Valor | Resuelve |
|-----------|-------|----------|
| `test_size=0.2` | 20% reserved | El "examen que el estudiante jamás estudió" |
| `random_state=42` | fijo | Reproducibilidad de la división — comparaciones justas entre experimentos |
| `stratify=y` | proporción de clases | Con datos 94%/6% BOUNCE/BREAKOUT, asegura ambos conjuntos mantienen esa proporción |

### 3.4 Limitación honesta (documentada por el proyecto)

Con 98 muestras y proporción 94/6, el test set termina con solo 5-6 ejemplos de BREAKOUT. `test_accuracy` es matemáticamente más honesto pero estadísticamente inestable — exactamente por qué el proyecto priorizó recolectar más datos reales antes que seguir ajustando hiperparámetros.

---

## 4. RandomForestClassifier: por qué esos hiperparámetros

```python
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=5,
    min_samples_leaf=2,
    random_state=42,
    class_weight="balanced",
)
```

| Parámetro | Valor | Razón | Decisión de riesgo |
|-----------|-------|-------|---------------------|
| `n_estimators=100` | 100 árboles | Estabiliza predicciones por promedio (bagging) | Punto de equilibrio entre costo computacional y estabilidad |
| `max_depth=5` | 5 niveles | Limita memorización — regularización | Sacrifica capacidad de ajuste por mejor generalización |
| `min_samples_leaf=2` | 2 muestras mínimo | Previene hojas basadas en un único ejemplo | Protección adicional contra overfitting |
| `random_state=42` | fijo | Reproducibilidad del "aleatorio" | El modelo es determinista con mismo seed |
| `class_weight="balanced"` | balanceado | Pondera errores sobre BREAKOUT más pesadamente | Sin esto, predecir siempre BOUNCE daría 94% accuracy — trampa estadística |

### Limitación documentada

`class_weight="balanced"` no es solución mágica con 6 ejemplos de BREAKOUT en todo el dataset. Ningún truco de ponderación puede inventar información que no existe — el modelo solo puede aprender de lo poco que vio.

---

## 5. `predict_proba` — el Oracle no dice "sí" o "no"

```python
proba = self.model.predict_proba(features)[0]
confidence = self._bounce_probability(proba)
action = "EXECUTE" if confidence >= self.min_confidence else "IGNORE"
```

### 5.1 `predict_proba()` vs `predict()`

- `predict()` → binario duro (0 o 1, BREAKOUT o BOUNCE) — sin matices
- `predict_proba()` → probabilidad continua ([0.32, 0.68]) — 32% BREAKOUT, 68% BOUNCE

### 5.2 El umbral de confianza como palanca de control

`self.min_confidence = 0.68` — el operador puede ajustar sin reentrenar:
- Más conservador: subir a 0.75 → solo ejecutar cuando el modelo está muy seguro
- Más agresivo: bajar a 0.60 → ejecutar ante señales más débiles

### 5.3 Protección Cat.3

`min_oracle_confidence` está protegido por la gobernanza del EvolutionOrchestrator: cualquier propuesta que baje el umbral por debajo de 0.70 escala automáticamente a Categoría 3 (requiere sesión humana completa).

---

## 6. Mapa completo: de la tabla cruda a la decisión

```
DataFrame crudo (training_samples aplanados)
    ↓
X = df[self._feature_cols]                    ← contrato de 7 columnas
    ↓
pd.to_numeric(errors="coerce") + fillna(0.0)   ← limpieza tolerante a ruido
    ↓
LabelEncoder por columna categórica             ← ⚠️ orden alfabético, guardar encoder
    ↓
train_test_split(stratify=y, random_state=42)  ← separar memorizar de aprender
    ↓
RandomForestClassifier(class_weight="balanced") ← comité de 100 árboles, regularizado
    ↓
model.predict_proba(features)                    ← probabilidad continua, no binario
    ↓
confidence >= min_confidence (0.68)              ← umbral protegido Cat.3
    ↓
"EXECUTE" o "IGNORE"                              ← decisión final al ShadowTrader
```

---

## 🔧 Práctica con Graphify

```bash
# Ver qué tan conectado está el pipeline de ML en el grafo
graphify explain "RandomForestClassifier" --graph graphify-out/graph.json

# Explorar la comunidad del pipeline completo
graphify cluster-only .

# Ver las conexiones del testing con el ML
graphify explain "test_oracle_training" --graph graphify-out/graph.json

# Generar el reporte actualizado
graphify update .
graphify cluster-only .
```

El grafo te permite ver visualmente que cada línea del pipeline es un nodo con conexiones reales a otros módulos — no es un flujo abstracto sino estructura concreta que puedes recorrer.