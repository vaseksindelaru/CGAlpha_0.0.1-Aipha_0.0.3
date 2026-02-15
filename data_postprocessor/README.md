# Aipha Data Postprocessor (Self-Improvement)

Este nivel del sistema Aipha es el responsable de cerrar el bucle de retroalimentación, permitiendo que el sistema aprenda de sus propios errores y se adapte dinámicamente a las condiciones del mercado.

## 🎯 Propósito
El **Data Postprocessor** actúa como el mecanismo de "aprendizaje por refuerzo" o auto-mejora. Su función es analizar los resultados de las estrategias (Trading Manager) y los filtros (Oracle) para proponer y aplicar ajustes paramétricos que optimicen el rendimiento futuro.

## 🏗️ Estructura de Directorios

```text
data_postprocessor/
├── building_blocks/
│   └── self_improvement/
│       └── adaptive_barrier.py # Lógica de barreras auto-ajustables
├── strategies/
│   └── self_improvement_loop.py # Demostración del ciclo de aprendizaje
├── docs/                         # Reservado para documentación nueva del módulo
└── README.md
```

## 🧩 Componentes Clave

### 1. Adaptive ATR Barrier (`adaptive_barrier.py`)
Inspirado en el concepto de `atr_tracer.py`, este componente permite que la distancia de las barreras de salida (Stop Loss / Take Profit) no sea estática.
- **Mecanismo**: Si un trade se cierra negativamente pero el análisis posterior determina que fue debido a "ruido" (el precio se recuperó después de tocar la barrera), el sistema incrementa su **multiplicador de ATR**.
- **Resultado**: El sistema se vuelve más tolerante en regímenes de alta volatilidad, evitando salidas prematuras innecesarias.

### 2. Ciclo de Retroalimentación (Feedback Loop)
El Data Postprocessor introduce la capacidad de procesar un diccionario de `feedback`:
- `outcome`: Resultado numérico del trade (1.0, -1.0, 0.0).
- `reason`: Clasificación cualitativa del resultado ('noise', 'trend', 'neutral').

## 🚀 Filosofía de Auto-Mejora
A diferencia de una optimización tradicional de parámetros (backtesting masivo), el Data Postprocessor propone una **mejora atómica y continua**. El sistema no espera a tener miles de trades para cambiar; aprende de cada evento significativo, ajustando su sensibilidad en tiempo real.

## 📈 Impacto en el Sistema
Al integrar el Data Postprocessor con el Trading Manager, el sistema no solo predice mejor (gracias al Oracle), sino que también sobrevive mejor a las fluctuaciones erráticas del mercado mediante la adaptación de sus barreras de protección.

## 🔁 Contrato de Feedback y Ciclo de Aprendizaje

Contrato mínimo de feedback:
- `outcome`: resultado cuantitativo del trade (`1.0`, `-1.0`, `0.0`)
- `reason`: clasificación causal (`noise`, `trend`, `neutral`)

Flujo operativo consolidado:
1. Calcular barreras con el estado actual.
2. Clasificar el resultado post-evento (ej. pérdida por ruido).
3. Ajustar multiplicador cuando corresponde (`noise` negativo).
4. Revalidar que el nuevo margen reduce salidas prematuras.

Parámetro crítico:
- `sensitivity` controla la velocidad de adaptación.
  - alto: aprende rápido pero puede sobrerreaccionar,
  - bajo: estable pero lento para adaptarse.

## ✅ Notas de Construcción (Consolidadas)

La guía técnica histórica fue consolidada en este README.
Se conserva solo como referencia en:
- `docs/archive/module_guides/data_postprocessor_construction_guide.md`
