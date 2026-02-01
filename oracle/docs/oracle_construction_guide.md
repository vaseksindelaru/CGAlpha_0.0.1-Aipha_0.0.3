# Guía de Construcción: Oracle

Esta guía detalla cómo extender y perfeccionar la capa de inteligencia de Aipha.

## 1. El Concepto del Oráculo
El Oráculo no es un sistema de trading por sí mismo, sino un **validador**. Su trabajo es observar una señal ya detectada y decidir si las condiciones del mercado favorecen que esa señal llegue a su objetivo (TP) o falle (SL).

---

## 2. Ingeniería de Características (Features)
La calidad del Oráculo depende totalmente de las características que le entreguemos.
- **Features de Momento**: `volume_ratio`, `body_percentage`.
- **Features de Contexto**: `hour_of_day`.
- **Sugerencia de Mejora**: Añadir indicadores técnicos (RSI, MACD) o la tendencia de las últimas 10 velas como nuevas características.

---

## 3. Entrenamiento y Overfitting
En el ejemplo de prueba, el Win Rate subió al 90%. **¡Cuidado!** Esto puede ser síntoma de *overfitting* (sobreajuste) debido al pequeño tamaño del dataset.

### Mejores Prácticas:
1.  **Más Datos**: Entrena con al menos 1-2 años de datos de diferentes símbolos.
2.  **Validación Cruzada**: Usa `TimeSeriesSplit` de scikit-learn para una evaluación más realista.
3.  **Fuera de Muestra**: Siempre prueba el modelo con datos que nunca vio durante el entrenamiento.

---

## 4. Persistencia del Modelo
Usamos `joblib` para guardar el modelo entrenado. Esto permite que la estrategia en tiempo real cargue el modelo instantáneamente sin necesidad de re-entrenar.

```python
# Guardar
joblib.dump(model, 'oracle/models/mi_modelo.joblib')

# Cargar
model = joblib.load('oracle/models/mi_modelo.joblib')
```

---

## 5. Integración en la Estrategia
La integración debe ser "limpia". La estrategia llama al `OracleEngine.predict()` y usa el resultado para filtrar la lista de eventos (`t_events`).

```python
# Ejemplo de filtrado:
valid_signals = t_events[predictions == 1]
```

---

## 6. Próximos Pasos
- **Meta-Labeling**: Investigar el concepto de Meta-Labeling de Marcos López de Prado para mejorar el diseño del Oráculo.
- **Modelos Avanzados**: Probar `XGBoost` o `LightGBM` para capturar relaciones no lineales más complejas.
- **Probabilidades**: En lugar de solo predecir 1 o -1, usar `predict_proba()` y solo operar si la probabilidad de éxito es > 70%.
