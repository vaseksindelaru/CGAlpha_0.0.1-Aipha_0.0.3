# 🎯 Guía de Triple Coincidencia en 5 Minutos

**Versión:** 1.0 (Implementada Feb 2, 2026)  
**Estado:** ✅ OPERATIVO  
**Temporalidad:** 5 minutos (conforme a Constitución v0.0.3)

---

## 📋 Resumen Ejecutivo

La **Triple Coincidencia** es el primer filtro de calidad del sistema Aipha. Requiere que **tres condiciones independientes** ocurran simultáneamente en un marco de 5 minutos:

1. **Vela Clave (Key Candle):** Alto volumen + cuerpo pequeño = absorción institucional
2. **Zona de Acumulación:** Mercado lateralizado = consolidación  
3. **Tendencia Estructurada:** R² > 0.45 = no es ruido puro

Cuando estas 3 coinciden, generan una señal de **ENTRADA** potencial.

---

## 🚀 Ejecución Rápida (3 pasos)

### **Paso 1: Descargar Datos de 5 Minutos**
```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
python3 data_processor/acquire_data.py --interval 5m
```

**Esperar:**
- ~2-3 minutos (depende de conexión)
- Verás: `✅ Éxito: ~8900 velas obtenidas (5M).`

### **Paso 2: Ejecutar la Estrategia**
```bash
python3 trading_manager/strategies/proof_strategy.py
```

**Esperar:**
- ~30-60 segundos
- Verás estadísticas de Triple Coincidencia y Win Rate

### **Paso 3: Revisar Resultados**
Los resultados se guardan automáticamente en:
- **Memoria:** `memory/performance_metrics.jsonl`
- **Historial:** `memory/action_history.jsonl`

---

## 📊 Entendiendo la Salida

### **Ejemplo de Salida Típica:**

```
============================================================
INICIANDO PROOF STRATEGY - TRIPLE COINCIDENCIA EN 5 MINUTOS
============================================================

✅ Datos cargados: 8900 velas de 5m de 2024-01-01 a 2024-01-31

--- EJECUTANDO DETECTORES DE TRIPLE COINCIDENCIA ---

1️⃣  Detectando zonas de acumulación...
   ✅ 350 barras en zona de acumulación (3.93%)
   
2️⃣  Detectando tendencia (R² y Slope)...
   ✅ R² promedio: 0.520
   
3️⃣  Detectando velas clave (volumen + cuerpo pequeño)...
   ✅ 45 velas clave detectadas (0.51%)

--- COMBINANDO SEÑALES (TRIPLE COINCIDENCIA) ---
✅ 12 TRIPLE COINCIDENCIAS detectadas en 5m (0.13%)

--- ETIQUETANDO 12 SEÑALES CON TRIPLE BARRIER METHOD ---

============================================================
RESULTADOS FINALES - ESTRATEGIA DE 5 MINUTOS
============================================================

  Total Señales Etiquetadas: 12
  Take Profit (TP hit): 8          ← Las barreras de TP se tocaron
  Stop Loss (SL hit): 3            ← Las barreras de SL se tocaron
  Neutral (Time Limit): 1          ← Timeout (max 20 velas)

  🎯 Win Rate (TP vs Total): 66.67%
  
✅ Métrica registrada en memoria del sistema.
============================================================
✅ PROOF STRATEGY COMPLETADA
============================================================
```

### **Interpretación de Métricas:**

| Métrica | Significado | Rango Típico |
|---------|------------|--------------|
| **Triple Coincidencias** | Señales válidas encontradas | 5-20 por mes |
| **Win Rate** | % de operaciones en TP vs total | 50-75% |
| **TP Hit** | Precio tocó objetivo de ganancia | >50% es bueno |
| **SL Hit** | Precio tocó stop loss | <50% es mejor |
| **Neutral** | Se agotó tiempo máximo | <10% es ideal |

---

## 🔧 Configuración de Parámetros

### **Ajustar Sensibilidad (core/config_manager.py o aipha_config.json):**

```python
# VELA CLAVE - Detectores de Absorción Institucional
"volume_lookback": 20,                    # Períodos para percentil (↑ = menos velas clave)
"volume_percentile_threshold": 90,        # Percentil de volumen (↑ = más estricto)
"body_percentile_threshold": 30,          # Max cuerpo % (↓ = más pequeño = más estricto)

# ZONA DE ACUMULACIÓN
"atr_period": 14,                         # Período de ATR
"atr_multiplier": 1.5,                    # Ancho de zona (↑ = zonas más amplias)

# TENDENCIA
"trend_lookback": 20,                     # Ventana de regresión
"min_r_squared": 0.45,                    # Calidad mínima (↑ = tendencia más limpia)

# TRIPLE COINCIDENCIA
"tolerance_bars": 8,                      # Ventana de tolerancia (↑ = más flexible)

# BARRERAS DINÁMICAS (ATR)
"tp_factor": 2.0,                         # TP = 2 x ATR (↑ = objetivo más lejano, ↓ = más cercano)
"sl_factor": 1.0,                         # SL = 1 x ATR
"time_limit": 20,                         # Máximo velas esperadas (↑ = más paciencia)
```

### **Ejemplos de Ajustes:**

**Mayor Precisión (Menos Falsas Señales):**
```python
volume_percentile_threshold: 95            # Solo volumen extremo
body_percentile_threshold: 20              # Cuerpos muy pequeños
min_r_squared: 0.60                        # Tendencia muy limpia
```

**Mayor Frecuencia (Más Señales):**
```python
volume_percentile_threshold: 75            # Volumen moderado
body_percentile_threshold: 40              # Cuerpos moderados
min_r_squared: 0.35                        # Tendencia débil OK
```

---

## 🧪 Opciones Avanzadas

### **Ejecutar con Datos 1H (Para Backtesting):**
```bash
# Modificar manualmente en proof_strategy.py:
# Cambiar línea ~160 de:
#   table_name = ensure_5m_data_exists(db_path, force_redownload=False)
# A:
#   table_name = "btc_1h_data"  # Usar 1H en lugar de 5M
```

### **Descargar Múltiples Meses:**
Editar en `data_processor/acquire_data.py`:
```python
def acquire_historical_data_5m():
    start_date = date(2024, 1, 1)     # ← Cambiar mes inicio
    end_date = date(2024, 3, 31)      # ← Cambiar mes fin
```

### **Ejecutar Contra Otro Par (ej. ETH/USD):**
Editar en `data_processor/acquire_data.py`:
```python
symbol="ETHUSDT",  # ← Cambiar símbolo
```

---

## 📈 Análisis de Resultados

### **¿Dónde se guardan los datos de salida?**

1. **Rendimiento General:**
   - Archivo: `memory/performance_metrics.jsonl`
   - Contiene: win_rate_5m, componente, timeframe, etc.

2. **Historial de Acciones:**
   - Archivo: `memory/action_history.jsonl`
   - Contiene: Cada evento (detector run, etiquetado, etc.)

3. **Configuración Utilizada:**
   - Archivo: `aipha_config.json`
   - Contiene: Parámetros aplicados en la última ejecución

### **Leer Métricas Programáticamente:**

```python
import json
from core.memory_manager import MemoryManager

memory = MemoryManager()

# Obtener última métrica
metrics = memory.read_metrics(filter_component="Trading")
for metric in metrics:
    print(f"Metric: {metric['metric_name']} = {metric['value']}")
```

---

## ⚙️ Solución de Problemas

### **Error: "Tabla 'btc_5m_data' no encontrada"**
```bash
# Ejecutar descarga:
python3 data_processor/acquire_data.py --interval 5m
```

### **Error: "No se detectaron Triple Coincidencias"**
- Los parámetros son muy estrictos
- Solución: Reducir `min_r_squared` o `volume_percentile_threshold`

### **Win Rate muy bajo (<40%)**
- Las barreras pueden estar mal calibradas
- Aumentar `tp_factor` o reducir `sl_factor`

### **No descarga datos de Binance**
```bash
# Verificar conexión:
python3 -c "import requests; requests.get('https://api.binance.com/api/v3/time')"

# Si falla, revisar:
- Conexión a Internet
- VPN (algunos países bloquean Binance)
- Proxy (si aplica)
```

---

## 📚 Referencia de Arquitectura

```
DATA PROCESSOR (5 minutos)
         ↓
    DuckDB (btc_5m_data)
         ↓
TRADING MANAGER
  ├─ AccumulationZoneDetector
  ├─ TrendDetector
  ├─ KeyCandleDetector
  └─ SignalCombiner (TRIPLE COINCIDENCIA)
         ↓
POTENTIAL CAPTURE ENGINE
  ├─ Barreras Dinámicas (ATR)
  ├─ Registra MFE/MAE
  └─ Etiqueta (TP/SL/Neutral)
         ↓
MEMORY MANAGER
  ├─ performance_metrics.jsonl
  └─ action_history.jsonl
         ↓
    CGALPHA LABS
  (Análisis Causal)
```

---

## 🎓 Próximas Lecturas

- [UNIFIED_CONSTITUTION_v0.0.3.md](../UNIFIED_CONSTITUTION_v0.0.3.md) - Especificación completa
- [data_processor/docs/](../data_processor/docs/) - Sistema de datos
- [core/config_manager.py](../core/config_manager.py) - Gestión de configuración

---

**Última Actualización:** 2 de febrero de 2026  
**Versión del Sistema:** v0.1.0 Production-Ready
