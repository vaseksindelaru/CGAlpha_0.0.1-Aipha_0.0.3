# 📘 CONSTITUCIÓN TÉCNICA UNIFICADA: ECOSISTEMA CGALPHA & AIPHA (v0.0.3)

> **Versión del Documento:** 2.0  
> **Estado del Sistema:** Aipha v0.0.3 (Producción) | CGAlpha v0.0.1 (Laboratorio)  
> **Principio Rector:** *"El principio de separación de poderes para gestionar la complejidad extrema"*

---

## 🏛️ PARTE 1: DEFINICIÓN DE IDENTIDAD Y ESTRATEGIA

### El Principio de Separación de Poderes

Para garantizar la estabilidad operativa mientras se desarrolla inteligencia artificial avanzada, el proyecto se bifurca en **dos entidades distintas** con responsabilidades estrictamente separadas:

### 1. Aipha v0.0.3 (El Proyecto Base / El Cuerpo)

*   **Identidad:** "Legacy Mejorado". Es el chasis robusto que opera en el mercado real.
*   **Filosofía:** **"Hardened" (Blindado)**. Prioriza velocidad, seguridad del capital, atomicidad de operaciones y estabilidad del código. **No piensa, actúa**.
*   **Estado:** PRODUCCIÓN / ESTABLE

#### Componentes Clave (Arquitectura de 5 Capas):

##### **Capa 1: Infraestructura y Sistema Nervioso**
- **`aiphalab` (CLI):** Interfaz de línea de comandos. Ver **[GUIA_CLI_PANEL_CONTROL.md](./GUIA_CLI_PANEL_CONTROL.md)**. Es el "teclado" del sistema.
- **`core` (Orquestación):** El director de orquesta. Coordina el flujo de información entre capas, gestiona el ciclo de vida de las operaciones.
- **`aipha_memory` (Persistencia ACID/JSONL):** Sistema de memoria inmutable. Cada evento se registra de forma irreversible en formato JSONL para garantizar la trazabilidad completa y la capacidad de análisis forense.

##### **Capa 2: Data Preprocessor**
- **Función:** Normalización y preparación de datos en tiempo real.
- **Responsabilidad:** Transformar datos OHLCV crudos en estructuras limpias y normalizadas que alimentan a los detectores. Incluye:
  - Cálculo de indicadores base (ATR, EMA, Volumen Relativo)
  - Limpieza de datos anómalos (spikes, gaps)
  - Sincronización de múltiples temporalidades (5m, 1m)

##### **Capa 3: Trading Manager** ⭐
El **corazón operativo** del sistema. Contiene toda la lógica determinista de trading.

**3.1. Detectors (Detectores de Señal)**

Implementan la **Triple Coincidencia** en temporalidad de 5 minutos (Archivos generados en mejora post-v0.0.3):

- **`AccumulationZoneDetector`:** ✅ **[CÓDIGO GENERADO]**
  - Identifica rangos laterales (zonas de acumulación/distribución)
  - Variables: `atr_period=14`, `atr_multiplier=1.5`, `min_zone_bars=5`, `volume_threshold=1.1`
  - Lógica: Detecta clústeres de precios donde el mercado "respira" sin dirección clara
  - Output: `zone_id`, `in_accumulation_zone` (boolean)

- **`TrendDetector`:** ✅ **[CÓDIGO GENERADO]**
  - Mide la calidad de la tendencia usando regresión lineal (ZigZag + R²)
  - Variables: `zigzag_threshold=0.5%`
  - Output: `trend_id`, `trend_direction` (alcista/bajista), `trend_slope`, `trend_r_squared`
  - **Nota crítica:** Un R² alto indica tendencia limpia; un R² bajo indica caos lateral (zona de acumulación)

- **`KeyCandleDetector`:**
  - Encuentra velas de "absorción institucional" (Alto volumen + Cuerpo pequeño)
  - Variables: `volume_lookback=20`, `volume_percentile_threshold=0.90`, `body_percentile_threshold=0.30`
  - Output: `is_key_candle` (boolean), columnas auxiliares (`volume_threshold`, `body_size`, `body_percentage`)

- **`SignalCombiner`:** ✅ **[CÓDIGO GENERADO]**
  - Fusiona las señales de los tres detectores
  - Variables: `tolerance=8` (velas de ventana), `min_r_squared=0.45`
  - Output: `is_triple_coincidence` (boolean)

- **`SignalScorer`:**
  - Asigna un puntaje de calidad (0-1) a cada señal detectada
  - Ponderación: 50% calidad de zona + 50% calidad de tendencia
  - Output: `final_score`

**3.2. Barriers (Sistema de Triple Barrera)** 🎯

**`PotentialCaptureEngine`** - El motor de etiquetado ordinal:

- **Configuración Dinámica:**
  - `profit_factors=[1.0, 2.0, ...]` - Múltiplos de ATR para TPs escalonados
  - `stop_loss_factor=1.0` - SL en unidades de ATR
  - `time_limit=20` - Paciencia máxima (velas)
  - `drawdown_threshold=0.8` - Tolerancia al drawdown intra-trade
  - `atr_period=14`

- **Lógica de Etiquetado Ordinal:**
  ```
  Para cada señal:
    1. Calcular barreras dinámicas basadas en ATR
    2. Monitorear el precio tick a tick
    3. NO HACER BREAK al tocar TP (CRÍTICO para CGAlpha)
    4. Registrar la trayectoria completa:
       - MFE (Max Favorable Excursion): ¿Cuánto subió como máximo?
       - MAE (Max Adverse Excursion): ¿Cuánto bajó como máximo?
       - Resultado Ordinal: Magnitud final en ATR (0, 1, 2, 3+)
  ```

- **Innovación clave:** El sistema NO cierra la posición al tocar el primer TP. En su lugar, registra **hasta dónde llegó realmente** el movimiento. Esto permite que CGAlpha (Capa 5) analice si las barreras están configuradas de forma óptima.

##### **Capa 4: Oracle (Motor Probabilístico)**
- **Modelos:** LightGBM / RandomForest
- **Función:** Ejecución rápida de predicciones en tiempo real (< 10ms)
- **Input:** Features del detector (volumen, RSI, EMA distance, trend_r_squared)
- **Output:** `probability` (0.0-1.0) y decisión binaria tras aplicar `confidence_threshold`
- **Mejora Crítica v0.0.3:** 🛡️ **"El Registro de Rechazos"** 
  - El Oracle ahora guarda en `rejected_signals.jsonl` TODAS las predicciones que NO superaron el umbral
  - **Justificación:** Para que CGAlpha pueda analizar oportunidades perdidas (contrafactuales)

##### **Capa 5: Data Postprocessor (CGAlpha - El Enlace Causal)** 🧠

Esta capa es el **puente evolutivo** entre Aipha (ejecución) y CGAlpha (razonamiento).

**Responsabilidades:**
1. **Análisis de Trayectorias Completas:** Lee los datos MFE/MAE del `PotentialCaptureEngine`
2. **Reescritura de Memoria:** Cambia las etiquetas de entrenamiento del Oracle basándose en análisis causal
3. **Generación de Propuestas:** Envía sugerencias de configuración al `core` de Aipha

**Conexión con CGAlpha:** Esta capa **ES** la interfaz de entrada a CGAlpha. Los datos limpios y enriquecidos se transfieren al ecosistema de Laboratorios para análisis profundo.

---

### 2. CGAlpha v0.0.1 (El Cerebro Experimental)

*   **Identidad:** "Laboratorio de I+D". Es el motor de descubrimiento causal.
*   **Filosofía:** **"Experimental & Causal"**. Prioriza hallar verdades matemáticas sobre la estabilidad inmediata.
*   **Estado:** LABORATORIO (NO opera dinero real directamente)

#### Componentes Clave:

##### **A. CGA_Nexus (El Coordinador Supremo)**
El orquestador estratégico y enlace con el LLM Inventor.

**Funciones:**
1. **Recepción de Reportes:** Recibe los análisis de los 4 Labs especializados
2. **Consulta de Régimen:** Determina el estado del mercado (Alta Volatilidad, Tendencia, Lateral)
3. **Asignación de Prioridad:** Decide qué Lab debe procesar con urgencia
4. **Síntesis para LLM:** Prepara el prompt estructurado (JSON limpio) para el Inventor
5. **Autorización de Propuestas:** Valida y envía `Automatic Proposals` al CLI de Aipha

**Integración con CGA_Ops (Supervisor de Recursos):**
- **Algoritmo Determinista:** Basado en `psutil` (Python), NO es IA
- **Semáforo de Recursos:**
  - 🟢 Verde (RAM < 60%): Entrenamiento pesado permitido
  - 🟡 Amarillo (RAM > 60%): Pausa nuevos procesos
  - 🔴 Rojo (Señal de Trading detectada): **MATA** procesos de CGAlpha para liberar CPU al Cuerpo (Aipha)

##### **B. Los Laboratorios Especializados (The Labs)**

**1. SignalDetectionLab (SD) - El Cartógrafo Macro** 📊

- **Temporalidad:** 5 minutos
- **Misión:** Detectar estructura de mercado favorable (Triple Coincidencia)
- **Variables de Entrada:**
  - `volume_threshold` - Percentil dinámico (típicamente > 90%)
  - `body_percentage` - Forma de vela (< 30% para absorción)
  - `ema_trend` - Contexto de marea (por encima/debajo EMA 200)
  - `signal_side` - Dirección (1=Long, -1=Short)
- **Output:** `ActiveZone` (objeto que contiene coordenadas: `Anchor_High`, `Anchor_Low`, `Anchor_Close`, `zone_score`)

**2. ZonePhysicsLab (ZP) - El Micro-Analista** 🔬

- **Temporalidad:** 1 minuto + Ticks
- **Misión:** Estudiar la "física del precio" dentro de una `ActiveZone`
- **Variables Calculadas en Tiempo Real:**
  - **Penetration Depth (%):** Profundidad normalizada dentro de la zona
    - 0%: Toque del techo (Close de la vela clave)
    - 100%: Toque del suelo (Low de la vela clave)
    - 110%+: Falsa ruptura / Barrido de liquidez
  - **Volume Absorption:** Sumatoria de volumen mientras el precio no rompe el nivel 110%
  - **Time in Zone:** Permanencia (velas atrapadas)
- **Memoria de Zona:**
  - 1er Toque: Alta probabilidad de rebote
  - 2do Toque: Mayor probabilidad de ruptura (liquidez agotada)
- **Detección de Fakeout:**
  - Ruptura rápida (precio sale) + Retorno inmediato con volumen > ruptura = TRAMPA
- **Output:** Estado (`REBOTE_CONFIRMADO`, `FAKEOUT_DETECTADO`, `RUPTURA_LIMPIA`, `ABSORCION_EN_CURSO`)

**3. ExecutionOptimizerLab (EO) - El Puente de ML** 🎯

- **Misión:** Determinar el momento exacto de entrada y gestión dinámica de posición
- **Subsistemas:**

  **3a. Validador de Calidad de Datos (Data Quality Guardian):**
  - **Z-Score de Spread:** Rechaza datos si spread > 2σ del promedio
  - **Test de Continuidad:** Descarta si hay gap > 30% ATR
  - **Ratio Volumen/Tick:** Detecta anomalías de feed o "fat fingers"
  - **Validación de Latencia:** Marca como obsoleto si timestamp tiene retraso > Nms
  - **Filtro de Sesión:** Ignora primeros/últimos 5 min de sesión (spread errático)

  **3b. Generador de Dataset para ML:**
  - Crea el DataFrame de entrenamiento con Features:
    - **Contexto (5m):** `zone_score_5m`, `trend_r2_previo`, `time_since_creation`
    - **Cinética (1m):** `approach_slope`, `vol_acceleration`, `atr_relative_dist`
    - **Impacto (1m):** `absorption_ratio`, `micro_rsi_divergence`, `touch_depth`
  - Target: Método de Triple Barrera (1=TP, 0=SL, 0.5=Timeout)

  **3c. Gestor de Salida Dinámica (Smart Exit Logic):**
  - **Break-Even Trigger:** Mueve SL a entrada cuando se confirma Higher High en 1m
  - **Trailing Stop Estructural:** SL salta de nivel siguiendo Higher Lows (no fijo en pips)
  - **Time-Exit:** Cierra si el precio se queda lateral sin llegar a objetivo

- **Variables de Optimización:**
  - `optimal_entry_pct` - ¿Entramos al 20% o esperamos al 105% de penetración?
  - `tp_factor`, `sl_factor` - Multiplicadores dinámicos
  - `time_limit` - Paciencia máxima

**4. RiskBarrierLab (RB) - El Juez Causal** ⚖️

- **Tecnología Core:** **EconML** (Microsoft Research)
- **Algoritmo:** **DML (Double Machine Learning)**
- **Misión:** Responder la pregunta: *"¿Este resultado fue CAUSADO por mi decisión o fue SUERTE del mercado?"*

**Proceso de Inferencia Causal:**

1. **Lectura del Puente Evolutivo:** Lee `evolutionary_bridge.jsonl`
   ```json
   {
     "trade_id": "UUID",
     "config_snapshot": {"threshold": 0.65, "tp": 2.0},
     "outcome_ordinal": 3,
     "vector_evidencia": {
       "mfe_atr": 3.4,
       "mae_atr": -0.2,
       "label": 3
     },
     "causal_tags": ["high_volatility", "news_event"]
   }
   ```

2. **Cálculo de CATE (Conditional Average Treatment Effect):**
   - **Treatment (T):** El cambio de parámetro (ej. threshold 0.70 → 0.65)
   - **Outcome (Y):** El resultado observado (+3 ATR)
   - **Confounders (X):** Contexto de mercado (volatilidad, sesión, tendencia)
   
   **Fórmula Conceptual:**
   ```
   CATE = E[Y | T=1, X] - E[Y | T=0, X]
   ```
   
   Donde:
   - `E[Y | T=1, X]` = Resultado con el cambio (threshold 0.65)
   - `E[Y | T=0, X]` = Resultado SIN el cambio (threshold 0.70) ← Estimado mediante "Gemelos Estadísticos"

3. **Búsqueda de Gemelos Estadísticos:**
   - El sistema busca en la base de datos histórica trades con contexto casi idéntico (mismo RSI, Volumen, Volatilidad) donde se usó el parámetro antiguo
   - Estos trades son el "contrafactual" que permite estimar qué habría pasado

4. **DML (Double Machine Learning) - El Motor Matemático:**
   
   **Paso 1 - Limpiar el Resultado (Y):**
   - Entrena un modelo ML para predecir la ganancia usando SOLO variables de mercado (ignorando la decisión)
   - Objetivo: Capturar la "suerte" del mercado
   - Residuo: La ganancia que NO vino del mercado
   
   **Paso 2 - Limpiar la Decisión (T):**
   - Entrena un modelo para predecir la decisión usando variables de mercado
   - Objetivo: Ver si la decisión fue predecible/sesgada
   
   **Paso 3 - Regresión Final:**
   - Compara los residuos
   - Si hay correlación entre Decisión y Ganancia DESPUÉS de quitar el efecto del mercado → **Causalidad Pura**

5. **Clustering (El Traductor de Contexto):**
   - EconML dice SI funcionó (CATE > 0)
   - Clustering dice CUÁNDO funcionó (en qué condiciones de mercado)
   - Agrupa trades con CATE similar y descubre patrones:
     - "Cluster A (High Vol + Bullish): CATE = +0.85 → ÉXITO"
     - "Cluster B (Low Vol + Range): CATE = -0.3 → FALLO"

6. **Generación de Policy (El Inventor LLM):**
   - El Nexus recibe el resumen del clustering
   - Lo envía al LLM Inventor (Qwen 2.5) con el prompt:
     ```
     "CATE positivo en High Volatility. Genera una regla Python 
     para activar threshold=0.65 SOLO en ese contexto."
     ```
   - LLM Output:
     ```python
     if market_data['ATR'] > 50 and market_data['RSI'] > 60:
         return {"threshold": 0.65}
     else:
         return {"threshold": 0.70}
     ```

**Variables Críticas del RB:**
- `confidence_threshold` - Variable Semilla (el parámetro bajo estudio actual)
- `tp_factor`, `sl_factor` - Ambición y Supervivencia
- `time_limit` - Paciencia
- `break_even_trigger` - Protección

**Output:** `PolicyProposal` con score causal y justificación matemática

---

## 🔄 PARTE 4: EL PROTOCOLO DE EVOLUCIÓN (EL PUENTE EVOLUTIVO)

### 1. El Nuevo Paradigma: Del Win Rate al Delta de Eficiencia Causal

**Métrica Antigua (v0.0.2):** Win Rate (insuficiente)  
**Métrica Nueva (v0.0.3):** **Delta de Eficiencia Causal (ΔCausal)**

**Definición:**
```
ΔCausal = Éxito Total - Éxito del Mercado (Contexto) = Mérito Real de la Decisión
```

### 2. El Vector de Evidencia (Datos de Alta Fidelidad)

Aipha ya NO reporta solo "Ganado/Perdido". Reporta la **Trayectoria Completa**:

- **MFE (Max Favorable Excursion):** Máximo potencial alcanzado
- **MAE (Max Adverse Excursion):** Peor momento del trade (calidad de entrada)
- **Resultado Ordinal:** Magnitud en ATR (ej. +3.5 ATR)
- **Contexto Completo:** Volatilidad, Sesión, Tendencia en momento de entrada

### 3. Ciclo de Vida de una Propuesta Automática

**Ejemplo Real:** El cambio `confidence_threshold: 0.70 → 0.65`

**Fase 1: Crisis Silenciosa (Observación)**
- Aipha está configurado con threshold=0.70
- El Oracle predice con probabilidades 0.66, 0.68, 0.69
- Como 0.68 < 0.70 → No opera
- **Pero** el sistema sigue registrando estas señales rechazadas en `rejected_signals.jsonl` (Shadow Trading)

**Fase 2: Análisis Causal (CGAlpha Actúa)**
- RiskBarrierLab lee las señales rechazadas
- Ejecuta simulación contrafactual: *"¿Qué hubiera pasado con threshold=0.65?"*
- EconML responde: *"Habrías entrado y ganado +2 ATR promedio en 15 de esos trades"*
- Calcula CATE: **+20 ATR de beneficio perdido**

**Fase 3: Invención (LLM Genera Propuesta)**
- Nexus sintetiza: *"En régimen High Volatility, threshold=0.70 es demasiado estricto. Punto óptimo causal: 0.65"*
- LLM Output:
  ```json
  {
    "type": "AUTOMATIC",
    "component": "orchestrator",
    "parameter": "confidence_threshold",
    "new_value": 0.65,
    "reason": "AUTO-OPTIMIZATION: Causal analysis indicates missed opportunity cost in High Volatility regime.",
    "priority": "high",
    "cate_score": 0.89
  }
  ```

**Fase 4: Cuarentena (Canary Deployment)** 🐤
- Aipha recibe la propuesta
- **NO se aplica al 100% inmediatamente**
- Modo Canario:
  - Solo 10% del tamaño de posición para los primeros 5 trades
  - O Paper Trading paralelo durante 1 hora
- **Justificación:** Si la IA se equivocó, pérdidas mínimas

**Fase 5: Validación en Producción**
- Los primeros trades con 0.65 se ejecutan
- Aipha reporta resultados reales a CGAlpha
- RiskBarrierLab confirma: *"CATE se mantiene positivo (+0.85) en real"*

**Fase 6: Promoción o Rollback**
- Si CATE real ≥ CATE predicho → **PROMOCIÓN** a 100% del capital
- Si CATE real < 0 → **ROLLBACK** automático a 0.70

### 4. Mejoras Críticas (Aprendizajes de v0.0.2)

**A. El Registro de Rechazos (Punto Débil 1 Resuelto):**
- El Oracle ahora guarda TODAS las predicciones, incluso las rechazadas
- Sin esto, CGAlpha no podría analizar oportunidades perdidas

**B. Modo Canario (Punto Débil 2 Resuelto):**
- Despliegue gradual evita pérdidas catastróficas por overfitting de la IA

**C. Umbral de Inercia (Punto Débil 3 Resuelto):**
- Para aprobar un cambio automático, el Delta Causal debe ser **sustancial** (> 10%)
- Evita que el sistema cambie de configuración 50 veces al día (fricción operativa)

---

## 🎯 ESTADO ACTUAL DE LA MISIÓN (v0.0.3)

### Implementaciones Completadas:
- ✅ Triple Barrera sin `break` (Sensor Ordinal activo)
- ✅ Registro de señales rechazadas (`rejected_signals.jsonl`)
- ✅ Vector de Evidencia enriquecido (MFE/MAE/Ordinal)

### En Desarrollo:
- 🔄 RiskBarrierLab (Análisis de `confidence_threshold=0.65`)
- 🔄 Clustering + LLM Inventor
- 🔄 Canary Deployment System

### Pregunta Causal Activa:
> *"¿El cambio a threshold=0.65 CAUSÓ la mejora del Win Rate, o fue el régimen de mercado (suerte)?"*

**Hipótesis a validar:**
- **H1 (Causal):** El 0.65 permite capturar señales de calidad media-alta que el 0.70 filtraba erróneamente
- **H2 (Ruido):** Las ganancias vienen de señales con probabilidad > 0.80 que habrían entrado igual con 0.70

---

## 📊 GLOSARIO TÉCNICO

| Término | Definición |
|---------|-----------|
| **ATR** | Average True Range. Medida de volatilidad. Si ATR=$500, el mercado "respira" $500 por vela. |
| **CATE** | Conditional Average Treatment Effect. "Cuánto mejora mi resultado por mi decisión vs. suerte del mercado" |
| **DML** | Double Machine Learning. Técnica para aislar causalidad del ruido mediante doble limpieza de datos |
| **MFE/MAE** | Max Favorable/Adverse Excursion. "Cuánto subió como máximo" / "Cuánto bajó como máximo" |
| **Gemelos Estadísticos** | Trades del pasado con contexto casi idéntico, usados para estimar contrafactuales |
| **Shadow Trading** | Registro de señales que NO se ejecutaron, para análisis posterior de oportunidades perdidas |
| **Canary Deployment** | Despliegue gradual (10% de capital) para validar cambios sin riesgo catastrófico |
| **Triple Coincidencia** | Alineación simultánea de: Zona + Tendencia + Vela Clave |
| **Fakeout** | Falsa ruptura. Precio sale de zona, dispara stops y regresa inmediatamente |

---

> **Sello de Versión:** Esta constitución representa el blueprint operativo de la Fase 0.0.3, donde el Cuerpo (Aipha) aprende del Cerebro (CGAlpha) en un ciclo de mejora continua basado en evidencia matemática, no en intuición.

---

## 🗂️ ANEXO: MEJORAS IMPLEMENTADAS v0.0.3

### ✅ CAMBIOS CRÍTICOS IMPLEMENTADOS:

1. **🎯 Sensor Ordinal (PotentialCaptureEngine)**
   - ❌ **ELIMINADO:** `break` statements (líneas 94-96, 101-103) 
   - ✅ **AGREGADO:** Tracking completo (MFE/MAE/Ordinal)
   - ✅ **AGREGADO:** `profit_factors`, `drawdown_threshold`, `return_trajectories`
   - **JUSTIFICACIÓN:** Sin trayectorias completas, análisis causal imposible

2. **🏗️ Estructura CGAlpha**
   - ✅ **CREADO:** `cgalpha/` directory (separado de `data_postprocessor/`)
   - **JUSTIFICACIÓN:** Separación conceptual clara

3. **🛡️ CGA_Ops (Semáforo)**
   - ✅ **IMPLEMENTADO:** Umbrales 60%/80%, polling 5s
   - **JUSTIFICACIÓN:** Best practices producción

4. **🧠 CGA_Nexus (Coordinador)**
   - ✅ **IMPLEMENTADO:** Buffer 1000 reportes, síntesis JSON
   - **JUSTIFICACIÓN:** Compatibilidad universal LLMs

5. **⚖️ RiskBarrierLab (Placeholder)**
   - ✅ **INTERFACE:** Completa con docstrings
   - ⚠️ **LÓGICA:** Placeholder (requiere >1000 trades para EconML)
   - **JUSTIFICACIÓN:** Documentar contrato sin bloquear desarrollo

6. **🌉 Puente Evolutivo**
   - ✅ **CREADO:** `evolutionary_bridge.jsonl`
   - **JUSTIFICACIÓN:** Append incremental JSONL

### 🔒 COMPONENTES MANTENIDOS:
- ✅ Toda infraestructura Aipha v0.0.2
- ✅ Detectores (AccumulationZone, Trend, KeyCandle)
- ✅ Oracle, Core, AiphaLab, Memory

### 🗑️ ELIMINACIONES:
**NINGUNA.** Cero eliminaciones.

---

> **Última Actualización Constitución:** 2026-02-01 04:30 CET  
> **Autor:** Václav Šindelář + Claude 4.5 Sonnet (Anthropic)
