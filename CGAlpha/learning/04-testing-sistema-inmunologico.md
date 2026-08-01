---
type: learning-note
project: CGAlpha
tags: [proyecto/cgalpha, learning, fase-5, testing, pytest]
created: 2026-07-27
part: 4-of-5
---

# Clase Magistral: Testing — El Sistema Inmunológico del Código

**Nivel**: S1 (Learning) — Fundamentos  
**Fase**: Fase 5 — Sistema Inmunológico  
**Prerrequisito**: Clases 1-4

---

## 0. Objetivo

Entender por qué no basta con "probarlo a mano" y cómo los tests actúan como guardias activos que protegen el sistema contra regresiones automáticas — incluyendo cambios propuestos por auto-evolución (CodeCraftSage).

---

## 1. El problema de fondo

Corriges `_determine_outcome()` y lo pruebas a mano. Una semana después, un cambio en `triple_coincidence.py` rompe silenciosamente esa lógica. El Oracle sigue corriendo, produciendo números que parecen razonables pero están equivocados.

Esto es una **regresión**: un comportamiento correcto que se rompe como efecto colateral de un cambio no relacionado. La única defensa real es tener comprobaciones automáticas que se ejecuten **cada vez que algo cambia**, no solo cuando alguien se acuerda de probarlo.

### 1.1 La Triple Barrera de CodeCraftSage

```
[1] AutoProposer genera un TechnicalSpec
        ↓
[2] Orchestrator clasifica: Cat.1, Cat.2, o Cat.3
        ↓
[3] Si Cat.1: CodeCraftSage aplica el patch directamente
        ↓
[4] python -m pytest cgalpha_v3/tests/ -q  ← LA TRIPLE BARRERA
        ↓
    ¿Todos los tests pasan?
        ├── SÍ → git commit, cambio aceptado permanentemente
        └── NO → rollback automático, cambio descartado
```

Cuando ves "217 passed", "192 passed" en las sesiones documentadas — no era ceremonia burocrática. Era el sistema inmunológico funcionando.

---

## 2. Anatomía de un test con pytest

### 2.1 Estructura mínima

```python
def test_oracle_predict_returns_confidence_between_zero_and_one():
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(sample_training_data())
    oracle.train_model()

    prediction = oracle.predict(sample_micro_record(), sample_signal_data())

    assert 0.0 <= prediction.confidence <= 1.0
```

`assert` es una palabra reservada de Python. Si la expresión es `False`, lanza `AssertionError`. pytest la captura, reporta el test como fallido, y **continúa con los demás** — no detiene toda la suite.

### 2.2 Los nombres importan

`test_oracle_predict_returns_confidence_between_zero_and_one` — el nombre ya dice exactamente qué se rompió cuando falla. No necesitas leer el código del test para entenderlo.

Compara con un test llamado `test_oracle_general` que verifica 15 cosas: cuando falla, tienes que leer todo su contenido para descubrir cuál de las 15 aserciones no se cumplió.

---

## 3. El patrón Arrange-Act-Assert

```python
def test_prediction_is_deterministic(trained_oracle):
    # ARRANGE — prepara el escenario
    # (trained_oracle es una fixture, ver abajo)

    # ACT — ejecuta la acción que quieres verificar
    p1 = trained_oracle.predict(sample_micro_record(), sample_signal_data())
    p2 = trained_oracle.predict(sample_micro_record(), sample_signal_data())

    # ASSERT — verifica el resultado
    assert p1.confidence == p2.confidence
```

Un test bien escrito verifica **una sola cosa**. Si falla, el nombre de la función te dice exactamente qué se rompió sin necesidad de leer el código.

---

## 4. Fixtures: el arte de no repetir la preparación

```python
@pytest.fixture
def trained_oracle():
    oracle = OracleTrainer_v3.create_default()
    samples = [...]  # datos de prueba realistas
    oracle.load_training_dataset(samples)
    oracle.train_model()
    return oracle
```

### 4.1 Convención de nombres = cableado automático

Cuando una función de test declara un parámetro llamado `trained_oracle`, pytest busca una función decorada con `@pytest.fixture` que se llame exactamente `trained_oracle`, la ejecuta, e inyecta su retorno. No hay import explícito entre ellos — la conexión es el nombre compartido.

### 4.2 `tmp_path`: sandbox desechable

```python
def test_save_and_load_preserves_predictions(trained_oracle, tmp_path):
    original_prediction = trained_oracle.predict(sample_micro_record(), sample_signal_data())

    save_path = tmp_path / "oracle_test.joblib"
    trained_oracle.save_to_disk(str(save_path))

    reloaded_oracle = OracleTrainer_v3.create_default()
    reloaded_oracle.load_from_disk(str(save_path))
    reloaded_prediction = reloaded_oracle.predict(sample_micro_record(), sample_signal_data())

    assert original_prediction.confidence == reloaded_prediction.confidence
```

`tmp_path` es una fixture de pytest — entrega un directorio temporal único que se destruye automáticamente después. Esto previene la contaminación del sistema de archivos y la mezcla de datos de test con datos de producción.

Este test verifica algo que fue literalmente uno de los bugs del proyecto: `save_to_disk()` y `load_from_disk()` existían pero nunca se llamaban desde el flujo real. Un test así los habría hecho visibles desde el principio.

---

## 5. Testing de aleatoriedad: el caso del Random Forest

### 5.1 El problema

Si el modelo tiene componentes aleatorios (bootstrap sampling, feature subsetting), ¿cómo escribir un test que no falle aleatoriamente?

### 5.2 La respuesta: `random_state=42`

Fijar la semilla hace que el comportamiento "aleatorio" sea completamente determinista. El test `test_prediction_is_deterministic` verifica reproducibilidad estructural: mismo input + mismo seed + mismo estado = mismo output, siempre.

### 5.3 Qué probar y qué no

- **Unit tests**: reproducibilidad estructural (dado X, produce Y)
- **Walk-forward validation + OOS metrics**: calidad estadística — eso es un proceso de evaluación separado, no una aserción binaria de pasa/falla

---

## 6. Simulando el mundo exterior: mocks

### 6.1 El problema

`ShadowTrader` depende de `BRIDGE_PATH` — una ruta real en el sistema de archivos. Probarlo escribiendo en producción contaminaría datos reales.

### 6.2 La solución: `monkeypatch`

```python
def test_shadow_trader_writes_to_bridge_on_open_trade(tmp_path, monkeypatch):
    bridge_path = tmp_path / "bridge.jsonl"
    monkeypatch.setattr(
        "cgalpha_v3.trading.shadow_trader.BRIDGE_PATH", str(bridge_path)
    )

    trader = ShadowTrader.create_default()
    trader.open_shadow_trade(
        entry_price=97250.0,
        direction=1,
        atr=85.0,
        signal_data={"oracle_confidence": 0.82}
    )

    assert bridge_path.exists()
    assert "97250.0" in bridge_path.read_text()
```

`monkeypatch` sustituye temporalmente una constante/función del código real, durante la duración exacta del test, revirtiendo automáticamente al terminar. Es una forma de aislar el test del mundo exterior sin modificar el código.

Esto conecta con el bug documentado de contaminación entre datos de verificación (`entry_price: 100.01` sintético mezclado con datos reales en el bridge).

---

## 7. La Triple Barrera en el contexto completo

La Triple Barrera no es un concepto nuevo que se aplica al final — es algo que ya funcionó durante todo el desarrollo de cgAlpha_0.0.1. Cada fix de bug (BUG-1 a BUG-8) terminó con:

1. Aplicar el cambio
2. `pytest cgalpha_v3/tests/ -q`
3. Solo `git commit` si el conteo de tests pasados se mantenía o aumentaba
4. Si bajó → rollback automático

Esto es lo que hace posible la promesa central del sistema: que un agente pueda proponer mejoras, aplicarlas, y confiar en que no se está destruyendo en el proceso — no por fe, sino porque cada cambio pasa por verificación mecánica objetiva.

---

## 8. Los ocho bugs como lecciones convertidas en código

| Bug | Lección aprendida | Test correspondiente |
|-----|---------------------|----------------------|
| BUG-1 | `train_test_split` > evaluar sobre datos de entrenamiento | Test de train/test accuracy gap |
| BUG-2 | Método existente que nunca se llama = peor que no existir | Test de integración save/load |
| BUG-3 | `class_weight` no salva datasets insuficientes | Test con clase minoritaria escasa |
| BUG-4 | Un DTO necesita campo booleano de confianza | Test de `is_placeholder` |
| BUG-5 | Umbral arbitrario (0.5%) indistinguible de ruido | Test de calibración contra percentiles reales |
| BUG-6-8 | [Completar con documentación posterior] | [Tests pendientes] |

> **Regla**: un bug corregido sin un test que lo proteja es una lección que el sistema tendrá que aprender otra vez, probablemente en el peor momento posible.

---

## 🔧 Práctica con Graphify

```bash
# Ver la comunidad de tests
graphify explain "test_oracle_training" --graph graphify-out/graph.json

# Mapear qué tests protegen qué módulos
graphify path "test_oracle_training" "oracle.py" --graph graphify-out/graph.json

# Ver la comunidad de testing en el grafo general
graphify cluster-only .

# Explorar relación entre tests y bugs
graphify explain "test_deferred_outcome_monitor" --graph graphify-out/graph.json
```

El grafo de tests te muestra qué módulos están cubiertos y cuáles tienen puntos ciegos — una forma directa de priorizar dónde escribir tests nuevos.