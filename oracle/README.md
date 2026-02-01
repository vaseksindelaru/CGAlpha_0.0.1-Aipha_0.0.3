# Aipha Oracle

Este nivel del sistema Aipha introduce inteligencia artificial para filtrar y validar las señales generadas por las capas inferiores.

## 🎯 Propósito
El **Oracle** actúa como un filtro de calidad. Su objetivo es reducir los falsos positivos (señales que terminan en Stop Loss) mediante el uso de modelos de Machine Learning que aprenden de los datos históricos.

## 🏗️ Estructura de Directorios

```text
oracle/
├── building_blocks/
│   ├── features/         # Ingeniería de características (feature_engineer.py)
│   └── oracles/          # Motores de ML (oracle_engine.py)
├── strategies/           # Entrenamiento e integración
│   ├── train_proof_oracle.py # Script de entrenamiento
│   └── proof_strategy_v2.py  # Estrategia filtrada por IA
├── models/               # Modelos entrenados (.joblib)
├── docs/                 # Guías técnicas
└── README.md             # Este archivo
```

## 🧩 Componentes Implementados

### 1. Feature Engineer (`feature_engineer.py`)
Transforma los datos crudos de una vela clave en un vector de características:
- `body_percentage`: Tamaño relativo del cuerpo.
- `volume_ratio`: Intensidad del volumen respecto al umbral.
- `relative_range`: Volatilidad de la vela.
- `hour_of_day`: Estacionalidad horaria.

### 2. Oracle Engine (`oracle_engine.py`)
Un envoltorio sobre `scikit-learn` que gestiona un modelo de **Random Forest**. Permite entrenar, predecir y persistir el conocimiento del oráculo.

### 3. Proof Strategy V2 (`proof_strategy_v2.py`)
La evolución de la estrategia original. Ahora, antes de validar una señal, consulta al Oráculo. Solo si el modelo predice un resultado positivo (1), la señal se considera válida.

## 📊 Resultados de la Prueba
En la verificación inicial con datos de BTCUSDT (1h):
- **Sin Oráculo**: Win Rate ~40%.
- **Con Oráculo (V2)**: Win Rate **90.91%** (filtrando 138 señales originales a 55 señales validadas).

## 🚀 Cómo entrenar y ejecutar
1. **Entrenar**: `python3 oracle/strategies/train_proof_oracle.py`
2. **Ejecutar**: `python3 oracle/strategies/proof_strategy_v2.py`
