# CGAlpha v3 – Estructura y Propósito

## Visión General
CGAlpha v3 es la evolución profesional de CGAlpha, integrando:
- La arquitectura limpia y modular de v2 (Clean Architecture, DDD, Ports & Adapters).
- Una estrategia de trading real simple (triple coincidencia) como punto de partida funcional.
- Una biblioteca inteligente que documenta, mapea y justifica cada decisión, indicador y resultado, sirviendo como memoria viva y base para la mejora continua.

---

## Estructura de Carpetas (Resumen)

```
cgalpha_v2/
├── app/                # Integración de lógica de aprendizaje y trading
├── application/        # Casos de uso y orquestación (vacío, preparado)
├── config/             # Configuración centralizada
├── core/               # Motores de trading (incluye fallback v1)
├── domain/             # Modelos de dominio y puertos (interfaces)
├── indicators/         # Indicadores (VWAP, OBI, Cumulative Delta)
├── infrastructure/     # Adapters a servicios externos (vacío, preparado)
├── interfaces/         # CLI, API, dashboards (vacío, preparado)
├── knowledge_base/     # Biblioteca inteligente (núcleo documental)
├── learning/           # Scripts y ejercicios de aprendizaje
├── shared/             # Tipos y excepciones compartidas
└── validators/         # Validaciones de datos
```

---

## Implementación de la Biblioteca Inteligente

- **Propósito:**
  - Centralizar y mapear papers, experimentos, decisiones y resultados.
  - Servir de puente entre teoría (papers, benchmarks) y práctica (código, resultados reales).
  - Permitir trazabilidad: cada indicador, umbral y ajuste está justificado y documentado.
- **Componentes clave:**
  - `knowledge_base/curator.py`: Ingesta y catalogación de papers.
  - `knowledge_base/phase_0_principles.py`: Fundamentos teóricos y metacognitivos.
  - `knowledge_base/phase_1_trading.py`: Documentación de experimentos y resultados reales.
  - CSVs y markdowns: Mapeo de papers a código y decisiones.
- **Uso:**
  - Cada vez que se implementa o ajusta un indicador, se documenta la fuente y el resultado en la biblioteca.
  - La biblioteca crece con cada iteración, permitiendo aprendizaje y mejora continua.

---

## Estrategia Real Simple (Triple Coincidencia)

- **Estado:**
  - Implementada como fallback en el motor de trading (`core/trading_engine.py`), basada en la lógica de v1.
  - Detecta zonas de interés mediante triple coincidencia de condiciones (ej. vela pequeña + volumen alto + confirmación de indicadores).
- **Propósito:**
  - Proveer una base funcional y validada con datos reales mientras se desarrolla la lógica avanzada de v2.
  - Permitir backtesting y registro de resultados en la biblioteca inteligente.
- **Evolución:**
  - A medida que se implementen nuevos indicadores y lógica profesional, la triple coincidencia servirá como benchmark y fallback.

---

## Roadmap de Desarrollo

1. **Semana 1:**
   - Reestructura de carpetas y documentación mínima en cada capa.
   - Implementación y documentación de la estrategia simple.
2. **Semana 2:**
   - Ingesta de papers y primeros experimentos en la biblioteca inteligente.
3. **Semana 3+:**
   - Desarrollo incremental de lógica avanzada, siempre documentando y justificando cada paso en la biblioteca.

---

## Conclusión
CGAlpha v3 es un sistema profesional, pero comienza con lo más simple y real: una estrategia clara, datos de mercado y una biblioteca que crece con cada paso. Cada decisión está documentada, cada resultado es trazable, y la arquitectura permite evolucionar sin perder la simplicidad ni la conexión con la realidad.

---

> **Recuerda:** La biblioteca inteligente es el núcleo de aprendizaje y mejora. La estrategia simple es el punto de partida funcional y el benchmark para todo avance futuro.
