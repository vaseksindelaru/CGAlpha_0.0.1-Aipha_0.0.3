# 🔧 PLAN DE IMPLEMENTACIÓN: CGAlpha_0.0.1 / Aipha_0.0.3

## 📋 Auditoría del Estado Actual (v0.0.2)

### ✅ Componentes Existentes que se MANTIENEN:
1. **Capa 1 (Infraestructura):**
   - `aiphalab/` (CLI) ✓
   - `core/` (Orquestación) ✓
   - `aipha_memory/` (Persistencia) ✓

2. **Capa 2 (Data Preprocessor):**
   - `data_processor/` ✓ (Requiere validación de alineación con constitución)

3. **Capa 3 (Trading Manager):**
   - `trading_manager/building_blocks/detectors/` ✓
   - `trading_manager/building_blocks/labelers/potential_capture_engine.py` ⚠️ (REQUIERE MODIFICACIÓN CRÍTICA)

4. **Capa 4 (Oracle):**
   - `oracle/` ✓ (Requiere agregar rejected_signals.jsonl)

5. **Capa 5 (Data Postprocessor - CGAlpha):**
   - `data_postprocessor/` ✓ (REQUIERE EXPANSIÓN MASIVA)

### 🚨 CAMBIOS CRÍTICOS REQUERIDOS:

#### **PRIORIDAD 1: Sensor Ordinal (Triple Barrera sin break)**
**Archivo:** `trading_manager/building_blocks/labelers/potential_capture_engine.py`
- **Problema:** Líneas 94-96 y 101-103 tienen `break` que interrumpen el tracking
- **Solución:** Eliminar breaks, registrar MFE/MAE/Ordinal completo
- **Justificación:** Sin este cambio, CGAlpha no puede analizar trayectorias

#### **PRIORIDAD 2: Registro de Rechazos (Oracle)**
**Componente:** Nuevo archivo `oracle/building_blocks/oracles/rejected_signals_tracker.py`
- **Problema:** Oracle solo guarda predicciones ejecutadas
- **Solución:** Crear tracker que guarde TODAS las predicciones
- **Justificación:** Para análisis contrafactual de oportunidades perdidas

#### **PRIORIDAD 3: CGAlpha Labs Structure**
**Directorio nuevo:** `cgalpha/`
- **Estructura:**
  ```
  cgalpha/
  ├── __init__.py
  ├── nexus/
  │   ├── coordinator.py (CGA_Nexus)
  │   └── ops.py (CGA_Ops - Semáforo de recursos)
  ├── labs/
  │   ├── __init__.py
  │   ├── signal_detection_lab.py (SD)
  │   ├── zone_physics_lab.py (ZP)
  │   ├── execution_optimizer_lab.py (EO)
  │   └── risk_barrier_lab.py (RB)
  └── README.md
  ```
- **Justificación:** Separación clara entre Aipha (ejecutor) y CGAlpha (analista)

#### **PRIORIDAD 4: Puente Evolutivo**
**Archivo nuevo:** `evolutionary_bridge.jsonl` (en `aipha_memory/`)
- **Formato:**
  ```json
  {
    "trade_id": "UUID",
    "config_snapshot": {...},
    "outcome_ordinal": 3,
    "vector_evidencia": {
      "mfe_atr": 3.4,
      "mae_atr": -0.2
    },
    "causal_tags": [...]
  }
  ```

### 🗑️ COMPONENTES A ELIMINAR:
**NINGUNO** - Todo el código actual es funcional y se integrará en la nueva arquitectura.

### 📝 DECISIONES AUTÓNOMAS:

1. **DECISIÓN:** Crear directorio `cgalpha/` separado en lugar de expandir `data_postprocessor/`
   - **Justificación:** Separación conceptual clara. CGAlpha es un proyecto "gemelo", no una subcapa de Aipha.

2. **DECISIÓN:** Mantener compatibilidad con v0.0.2
   - **Justificación:** Transición gradual. El sistema debe funcionar durante la migración.

3. **DECISIÓN:** Agregar `config_version` a `aipha_config.json`
   - **Justificación:** Trazabilidad de cambios de arquitectura.

## 🎯 ORDEN DE IMPLEMENTACIÓN:

### Fase 1: Fundamentos (CRÍTICO)
1. ✅ Modificar `potential_capture_engine.py` (Sensor Ordinal)
2. ✅ Crear `evolutionary_bridge.jsonl`
3. ✅ Agregar `rejected_signals_tracker.py`

### Fase 2: Estructura CGAlpha
4. ✅ Crear directorio `cgalpha/` con estructura base
5. ✅ Implementar CGA_Ops (Semáforo de recursos)
6. ✅ Implementar CGA_Nexus (Coordinador)

### Fase 3: Labs Especializados
7. ✅ SignalDetectionLab (wrapper de detectores existentes)
8. ✅ ZonePhysicsLab (análisis micro 1m)
9. ✅ ExecutionOptimizerLab (validador + ML dataset)
10. ✅ RiskBarrierLab (EconML integration - PLACEHOLDER)

### Fase 4: Documentación
11. ✅ README.md unificado
12. ✅ Actualizar constitución con marcadores de mejoras
13. ✅ CHANGELOG.md con todos los cambios

## 📊 MÉTRICAS DE ÉXITO:
- ✅ `potential_capture_engine.py` genera datos ordinales completos
- ✅ `evolutionary_bridge.jsonl` se puebla con cada trade
- ✅ `cgalpha/` estructura funcional y desacoplada
- ✅ Tests unitarios pasan (sin regresión)
- ✅ Sistema v0.0.2 sigue funcionando durante transición
