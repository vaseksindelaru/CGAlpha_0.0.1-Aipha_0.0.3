# 🏗️ CGAlpha v3: Arquitectura y Funcionamiento Profundo

¡Bienvenido al núcleo de CGAlpha v3! Este documento expande la visión general para proporcionar una comprensión técnica profunda del sistema, sus subsistemas y su evolución.

---

## 1. Arquitectura General: El Enfoque de "Control Progresivo"

CGAlpha v3 no es solo un script de trading; es una **plataforma de auditoría y ejecución distribuida**. Su arquitectura está diseñada para desacoplar la **decisión** (IA/Lila) de la **ejecución** (Orchestrator) y el **control** (Risk Layer).

### Stack Tecnológico Detallado
- **Frontend**: Vanilla JavaScript (ES6+), CSS3 (Dark Theme Premium), HTML5 Semántico.
- **Backend**: Python 3.11+ con Flask para la API REST.
- **Persistencia**: Snapshotting atómico en disco (`memory/iterations/`, `aipha_memory/`).
- **Comunicación**: Intercambio de estado mediante polling síncrono (FASE 0) con ruta de migración a WebSocket asíncrono (Fases Futuras).

---

## 2. El Flujo de Vida de una Operación

Para entender CGAlpha, hay que seguir el camino de una decisión desde que es una simple hipótesis hasta que se convierte en una estrategia activa:

### A. La Capa de Conocimiento (Lila)
1. **Ingesta**: Se añaden fuentes a la `Library`. Lila clasifica el nivel de evidencia (`ev_level`).
2. **Teoría**: Se propone un `Claim`. Lila busca en su biblioteca si hay soporte científico ("Theory Live").
3. **Memoria**: Los resultados se almacenan en la `Learning Memory`. Si un patrón se repite, escala de nivel (0a → 4).

### B. El Ciclo de Experimentación (Experiment Loop)
1. **Proposal**: Lila genera una propuesta técnica con un `ApproachType` (ej: BREAKOUT).
2. **Backtest**: Se ejecuta una validación **Walk-Forward** (mínimo 3 ventanas).
3. **Audit Gate**: El sistema verifica que no haya **Temporal Leakage**. Si el Sharpe esperado es > 1.5, se considera "Promovible".

### C. Ejecución y Protección (Risk Layer)
1. **Control Room**: El operador supervisa el estado en tiempo real.
2. **Circuit Breakers**: Si el mercado se vuelve errático (Regime Shift) o las métricas de drawdown fallan, el sistema se bloquea.
3. **Kill-Switch**: El protocolo final para detener todo flujo de capital en milisegundos.

---

## 3. Subsistemas Críticos en FASE 0

### **Lila: El "Audit Brain"**
Lila no es un simple chatbot. Es un motor de políticas de memoria. Su función es evitar que el sistema "olvide" errores pasados y asegurar que cada estrategia tenga una base científica sólida.
- **TTL (Time To Live)**: Los datos de baja calidad mueren rápido para no ensuciar el modelo.
- **Promotion Logic**: Solo lo que sobrevive a la validación rigurosa se queda en memoria permanente.

### **Risk Dashboard: El "Guardian"**
Monitorea SLOs (Service Level Objectives) técnicos y financieros.
- **Data Quality**: Monitorea el estado de los datos (Valid, Stale, Corrupted).
- **Control Cycles**: Cada clic en la GUI deja una huella digital para auditorías Forester/P3.

---

## 4. Hoja de Ruta: De FASE 0 a Producción

| Característica | FASE 0 (Actual) | FASE 1 (Live Beta) | FASE 2+ (Scalping HF) |
| :--- | :--- | :--- | :--- |
| **Datos** | Mock / Simulados | WebSocket Exchange Real | Ticks de Microestructura |
| **Ejecución** | Manual / Auditada | Híbrida (IA + Humano) | Totalmente Autónoma |
| **Latencia** | Polling (5s) | Low Latency (50-100ms) | Ultra Low Latency (15-20ms) |
| **Mecanismo** | REST API | REST + WebSocket | C++ Bindings / Zero-Copy |

---

## 5. Glosario de Términos Avanzados

- **Temporal Leakage**: El error de "mirar el futuro" durante el backtesting. CGAlpha lo detecta analizando los timestamps de las features vs los targets.
- **Walk-Forward**: Técnica de backtesting que divide los datos en múltiples ventanas de "Entrenamiento" y "Test" que se desplazan en el tiempo.
- **Regime Shift**: Cambio brusco en la naturaleza del mercado. Lila puede decidir "olvidar" estrategias que funcionaban en mercados alcistas si detecta que ahora estamos en uno bajista.

---

## 🛡️ Protocolo de Seguridad P3
Este sistema ha sido diseñado bajo estándares de **Hardening P3**. Significa que la seguridad no es opcional; está integrada en el código. Ninguna promoción de estrategia ocurre sin una validación automática de riesgos.

> [!NOTE]
> Para profundizar aún más, consulta la pestaña **"Help ?"** en la GUI, donde todos estos conceptos son buscables en tiempo real con ejemplos dinámicos.
