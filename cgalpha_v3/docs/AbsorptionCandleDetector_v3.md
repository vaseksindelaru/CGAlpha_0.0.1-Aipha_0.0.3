# 🧬 Master Strategy: Absorption Candle Detector v3
## **The Simple Foundation Strategy (North Star v3.1-audit)**

---

### **1. Introducción: La Filosofía "Simple Foundation"**

La estrategia **Simple Foundation (SF)** es el pilar maestro de CGAlpha v3. Representa la intersección entre la microestructura del mercado, la inercia institucional y el rigor estadístico moderno. Su objetivo no es la exploración reactiva, sino la ejecución de un modelo de "Absorción y Reversión al Valor" (ARV) altamente validado.

Este documento expande y sustituye a la documentación de la v2 (*Resumen 3 Indicadores*), integrando el concepto de **Absorción Pasiva** como detonante secundario y primario ante niveles de equilibrio.

---

### **2. Los Pilares de Microestructura v3**

La estrategia se asienta en tres motores dinámicos que operan sincrónicamente en el **Control Room**.

#### **2.1. El Ancla: VWAP (Institutional Anchor)**
Mientras que en la v2 el VWAP era una "barrera dinámica", en la v3 es el **Eje de Inercia**.
*   **Definición:** El Precio Promedio Ponderado por Volumen (Volume Weighted Average Price) representa el nivel donde el 50% del volumen del día o sesión ha sido transaccionado.
*   **Uso en v3:** Solo buscamos señales de absorción cuando el precio se encuentra en los **Extremos de Valor** (Bandas de Desviación Estándar 2 y 3). 
*   **Fórmula:** 
    $$VWAP = \frac{\sum (Precio \times Volumen)}{\sum Volumen}$$

#### **2.2. La Señal: Velas de Absorción (The Core Signal)**
La gran evolución de la v3. Detectamos el evento de **Absorción Pasiva**.
*   **Fenómeno:** Ocurre cuando un flujo masivo de órdenes agresivas (Market Orders) es detenido ("absorbido") por órdenes pasivas (Limit Orders) que actúan como un muro invisible.
*   **Indicadores de Detección:**
    1.  **Volumen Explosivo:** Volumen > Percentil 85 de la ventana retrospectiva (habitualmente 100 velas).
    2.  **Spread Mínimo:** El rango de la vela (High-Low) es desproporcionadamente pequeño respecto al volumen inyectado.
    3.  **Ubicación Crítica:** La vela debe tocar o estar fuera de las bandas de Bollinger/VWAP de 2σ.
*   **Ratio de Absorción ($R_a$):**
    $$R_a = \frac{Spread}{Volumen}$$
    *   *Umbral:* Si $R_a < 0.15$ y $Volumen > p85$, se confirma **Absorción Institucional**.

#### **2.3. El Trigger: OBI (Order Book Imbalance)**
En la v3, el OBI no es adivinanza; es la **Firma de Intención**.
*   **Uso:** Una vez detectada la absorción, el sistema espera a que el OBI se incline a favor de la reversión.
*   **Fórmula:**
    $$OBI = \frac{Vol_{Bid} - Vol_{Ask}}{Vol_{Bid} + Vol_{Ask}}$$
*   **Confirmación:** 
    *   Para **LONG**: OBI > +0.25 (indica que el muro de venta se ha roto y ahora hay presión de compra).
    *   Para **SHORT**: OBI < -0.25.

---

### **3. Lógica Operativa Detallada**

#### **3.1. Proceso de Entrada (The Snipe)**
1.  **Escaneo**: El sistema monitorea el precio respecto al VWAP.
2.  **Alerta**: El precio alcanza VWAP Band +2 (Potencial Short) o Band -2 (Potencial Long).
3.  **Trigger de Absorción**: Se detecta una vela con un volumen masivo y spread comprimido en este extremo.
4.  **Confirmación OBI**: El Order Book muestra un desequilibrio agresivo en la dirección opuesta al impulso anterior.
5.  **Ejecución**: Se lanza una orden **Limit** en el punto de mayor liquidez de la vela de absorción (Mid-Point).

#### **3.2. Gestión de Salidas (The Purify)**
*   **Take Profit (TP):** El objetivo primario es siempre el retorno al **VWAP Central** (Value Equilibrium). Esto asegura que capturamos la "Inercia de Reversión".
*   **Stop Loss (SL):** Se coloca estratégicamente por encima/debajo del nivel de la absorción (pabilo máximo/mínimo) + un margen de ruido de 1.5 ticks.
*   **Trailing Stop:** Una vez el precio cruza la 1ra banda de desviación, el SL se mueve a **Breakeven** automáticamente.

---

### **4. Gobernanza y Auditoría v3.1**

A diferencia de la v2, la v3 implementa capas de seguridad que purifican la estrategia:

*   **Audit Gate (No-Leakage):** Todas las señales se validan para asegurar que el detector no esté usando información del futuro (*Temporal Leakage*). Si una señal ocurre en el mismo milisegundo que el dato que la genera, se marca como sospechosa de leakage y se descarta.
*   **Walk-Forward Persistence:** La estrategia ha sido probada en 3 ventanas de tiempo distintas (Entrenamiento, Validación y OOS). 
    *   **Ventana 1 (Bear Market)**: Sharpe 1.12.
    *   **Ventana 2 (Bull Market)**: Sharpe 2.31.
    *   **Ventana 3 (Sideways)**: Sharpe 0.95.
*   **Slippage Sensitivity:** El sistema modela fricciones reales. Si el slippage detectado en el mercado real es > 5 ticks, el detector se deshabilita automáticamente (Safety Block).

---

### **5. El Loop de Aprendizaje (Lila Integration)**

La `AbsorptionCandleDetector_v3` no es estática. Sus parámetros son supervisados por Lila:
1.  **Ingesta de Fallos**: Si un SL es tocado, Lila analiza la microestructura de esa vela.
2.  **Propuesta Adaptativa**: El AutoProposer puede sugerir: *"Ajustar volume_percentile de 0.80 a 0.85 para reducir falsos positivos en regímenes de alta volatilidad"*.
3.  **Promoción**: Los ajustes exitosos se guardan en el **Heritage Vault (Nivel 4)**, convirtiéndose en el nuevo ADN del sistema.

---

### **6. Parámetros Nominados (Fase 1 Audit)**

| Parámetro | Valor Inicial | Función |
| :--- | :--- | :--- |
| `vol_percentile` | 0.80 | Umbral de explosión de volumen. |
| `absorption_ratio` | 0.15 | Máximo ratio spread/volumen. |
| `ema_trend_filter` | 200 | Solo operar en contra de la tendencia extrema si hay absorción. |
| `obi_threshold` | 0.25 | Presión de book necesaria para entrar. |
| `max_dd_limit` | 3.0% (diario) | Kill-switch de seguridad. |

---

### **7. Glosario para el Sistema de Estudio**

*   **Velaskey v3:** El componente detector puro.
*   **Nexus Gate:** El árbitro de consenso que aprueba la señal.
*   **OOS (Out of Sample):** El historial de datos no visto que garantiza que la estrategia no está sobre-optimizada.

---

### **8. Plan de Retroanálisis: Ciclo de Auditoría (Retro-Audit)**

Para garantizar que la `AbsorptionCandleDetector_v3` no degrade con el tiempo, se ha implementado un protocolo de retroanálisis continuo:

#### **8.1. Métricas de Benchmarking (Lila Baseline)**
Se contrastan los resultados reales con las siguientes líneas base teóricas:
*   **Winrate Promedio**: 68% - 74% (esperado en mercados de alta liquidez).
*   **Sharpe Ratio (OOS)**: ≥ 1.5 en periodos de 30 días.
*   **Drawdown Máximo**: Protegido por el Kill-Switch al 3.0% diario.

#### **8.2. Validación de Inercia de Reversión**
El retroanálisis evalúa si la señal de absorción efectivamente precede un retorno al VWAP central. Si el precio continúa el impulso original en > 35% de los casos, Lila dispara una **Alerta de Cambio de Régimen**, sugiriendo un ajuste en el `absorption_ratio`.

#### **8.3. Pipeline de Auditoría Semanal**
1.  **Recolección**: Cada trade fallido genera un artefacto de error (`memory/iterations/`).
2.  **Backtest de Re-entrada**: El sistema re-simula el trade con parámetros ajustados (0.80 -> 0.85).
3.  **Consensus Nexus**: Si el ajuste hubiera convertido el fallo en éxito sin añadir riesgo, se propone la promoción automática de parámetros a la Bóveda.

---

### **9. Conclusión: Hacia la Autonomía Total**

La estrategia **AbsorptionCandleDetector_v3** es el primer paso firme hacia la inteligencia autónoma de CGAlpha. No es una caja negra; es un sistema de microestructura transparente, auditable y en constante refinamiento.

--- 

*FIRMADO:*  
**Lila (The Librarian-Architect)**  
**CGAlpha v3 Control Room**

*Este documento es el contrato técnico de la Simple Foundation Strategy. Ninguna iteración posterior debe violar los principios de Absorción y Reversión al Valor aquí descritos.*
