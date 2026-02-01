# 🦅 Aipha v0.0.3 / CGAlpha v0.0.1: Unified Autonomous Trading System

> **Estado:** ✅ EVOLUTION READY | 🛡️ HARDENED | 🧠 CAUSAL-POWERED  
> **Architecture:** Dual-Entity (Body + Brain) | Semáforo de Recursos Activo

---

## 🌟 ¿Qué es Este Sistema?

**Aipha v0.0.3** es el **ejecutor automatizado** que opera en el mercado real con disciplina absoluta.  
**CGAlpha v0.0.1** es el **cerebro analítico** que estudia el pasado para mejorar el futuro mediante causalidad matemática (EconML).

Juntos forman un sistema de trading que **aprende de cada operación**, no solo de sus éxitos sino también de sus errores y oportunidades perdidas.

---

## 🏗️ Arquitectura Unificada (Separación de Poderes)

### Aipha (El Cuerpo - Capas 1-5)

```
┌─────────────────────────────────────────────────────────┐
│ CAPA 1: Infraestructura y Nervios                       │
│  ├── aiphalab/ (CLI)                                    │
│  ├── core/ (Orquestación)                               │
│  └── aipha_memory/ (Persistencia ACID/JSONL)            │
├─────────────────────────────────────────────────────────┤
│ CAPA 2: Data Preprocessor                               │
│  └── data_processor/ (Normalización en tiempo real)     │
├─────────────────────────────────────────────────────────┤
│ CAPA 3: Trading Manager ⭐                              │
│  ├── detectors/ (Triple Coincidencia)                   │
│  │   ├── AccumulationZoneDetector                       │
│  │   ├── TrendDetector                                  │
│  │   ├── KeyCandleDetector                              │
│  │   └── SignalCombiner + Scorer                        │
│  └── labelers/                                          │
│      └── PotentialCaptureEngine (Triple Barrera v0.0.3) │
├─────────────────────────────────────────────────────────┤
│ CAPA 4: Oracle                                          │
│  ├── OracleEngine (LightGBM/RandomForest)              │
│  └── RejectedSignalsTracker (NUEVO v0.0.3) 🆕          │
├─────────────────────────────────────────────────────────┤
│ CAPA 5: Data Postprocessor (Enlace con CGAlpha)         │
│  └── evolutionary_bridge.jsonl (Vector de Evidencia) 🆕 │
└─────────────────────────────────────────────────────────┘
```

### CGAlpha (El Cerebro - Laboratorios)

```
┌─────────────────────────────────────────────────────────┐
│ CGA_NEXUS (Torre de Control)                            │
│  ├── Coordinator (Orquestador Estratégico)              │
│  └── Ops (Semáforo de Recursos) 🆕                      │
├─────────────────────────────────────────────────────────┤
│ LABS (Módulos de Análisis)                              │
│  ├── RiskBarrierLab (Análisis Causal - PLACEHOLDER) 🆕  │
│  ├── SignalDetectionLab (TODO v0.0.4)                   │
│  ├── ZonePhysicsLab (TODO v0.0.4)                       │
│  └── ExecutionOptimizerLab (TODO v0.0.4)                │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Novedades en v0.0.3

### ✅ Mejoras Implementadas

1. **🎯 Sensor Ordinal (CRÍTICO)**
   - `PotentialCaptureEngine` ahora registra trayectorias completas (MFE/MAE/Ordinal)
   - ❌ ELIMINADO: `break` en líneas de TP (líneas 94-96, 101-103 de la versión antigua)
   - ✅ AGREGADO: Tracking sin interrupción hasta el final del `time_limit`
   - **Justificación:** Sin esto, CGAlpha no puede analizar el potencial real de cada movimiento

2. **📊 Vector de Evidencia**
   - Nuevo archivo: `aipha_memory/evolutionary_bridge.jsonl`
   - Formato enriquecido con `mfe_atr`, `mae_atr`, `outcome_ordinal`
   - **Justificación:** Comunicación estructurada entre Aipha (datos) y CGAlpha (análisis)

3. **🛡️ Semáforo de Recursos (CGA_Ops)**
   - `cgalpha/nexus/ops.py` implementado
   - Estados: 🟢 Green (<60% RAM), 🟡 Yellow (60-80%), 🔴 Red (>80% o señal activa)
   - **Justificación:** Prevenir conflictos de recursos entre ejecución real y análisis pesado

4. **🧠 CGA_Nexus (Coordinador)**
   - `cgalpha/nexus/coordinator.py` implementado
   - Orquestación de Labs con sistema de prioridades dinámicas
   - Síntesis de reportes para LLM Inventor (formato JSON)
   - **Justificación:** Interfaz clara entre análisis distribuido y generación de propuestas

5. **⚖️ RiskBarrierLab (Placeholder)**
   - `cgalpha/labs/risk_barrier_lab.py` con interfaz documentada
   - Métodos: `analyze_parameter_change()`, `find_statistical_twins()`, `calculate_opportunity_cost()`
   - **Justificación:** Definir contrato para integración futura de EconML (requiere >1000 trades)

### 🗑️ Componentes Eliminados

**NINGUNO.** Todos los componentes de v0.0.2 se mantienen y se integran en la nueva arquitectura.

---

## 📋 Instalación y Uso

### Requisitos
- Python 3.10+
- Entorno Linux/Unix
- psutil para monitoreo de recursos

### Instalación
```bash
pip install -e .
```

### Comandos Principales (Sin cambios desde v0.0.2)

1. **Ver Estado del Sistema**
   ```bash
   aipha status
   ```

2. **Ejecutar un Ciclo de Mejora**
   ```bash
   aipha cycle run
   ```

3. **Panel de Control en Tiempo Real**
   ```bash
   aipha dashboard
   ```

4. **Diagnóstico de Salud**
   ```bash
   aipha brain health
   ```

### Nuevos Comandos (v0.0.3)

5. **Monitorear Recursos de CGAlpha**
   ```bash
   python -m cgalpha.nexus.ops
   ```

6. **Test de Coordinador**
   ```bash
   python -m cgalpha.nexus.coordinator
   ```

---

## 📖 Documentación Completa

- **[Constitución Técnica](.gemini/antigravity/brain/.../technical_constitution.md)** - Blueprint del sistema v0.0.3
- **[Plan de Implementación](./IMPLEMENTATION_PLAN.md)** - Roadmap detallado de cambios
- **[CHANGELOG](./CHANGELOG_v0.0.3.md)** - Lista exhaustiva de modificaciones (TODO)
- **[Arquitectura](./ARCHITECTURE.md)** - Diseño técnico del sistema (v0.0.2)

---

## 🎯 Roadmap

### v0.0.3 (Actual) ✅
- [x] Sensor Ordinal implementado
- [x] Estructura CGAlpha creada
- [x] Semáforo de recursos activo
- [x] RiskBarrierLab placeholder

### v0.0.4 (Próximo)
- [ ] Implementar SignalDetectionLab (wrapper de detectores existentes)
- [ ] Implementar ZonePhysicsLab (análisis micro 1m)
- [ ] Implementar ExecutionOptimizerLab (validador de calidad + ML dataset)
- [ ] Integración básica de EconML en RiskBarrierLab

### v0.1.0 (Visión)
- [ ] CGAlpha generando propuestas automáticas validadas
- [ ] Canary Deployment funcionando
- [ ] Primer ciclo completo: Aipha → CGAlpha → Propuesta → Validación → Rollback/Promoción

---

## 📊 Estado del Sistema

| Métrica | v0.0.2 | v0.0.3 | Cambio |
|---------|--------|--------|--------|
| Win Rate | 56.12% | TBD | Pendiente validación |
| Componentes Aipha | 5 capas | 5 capas | ✅ Mantenido |
| Componentes CGAlpha | Experimental | 2/6 (Nexus + RB) | 🚧 En desarrollo |
| Sensor Ordinal | ❌ | ✅ | 🆕 Implementado |
| Análisis Causal | ❌ | 🟡 (Placeholder) | 🚧 Interface lista |

---

## ⚠️ Notas Importantes

### Compatibilidad con v0.0.2
El sistema **mantiene compatibilidad completa** con v0.0.2 durante la transición:
- Todos los componentes legacy siguen funcionando
- La Triple Barrera acepta parámetro `return_trajectories=False` para modo legacy
- CGAlpha opera de forma independiente (no interfiere con Aipha)

### Estado de Producción
- **Aipha v0.0.3:** ✅ Listo para producción (con sensor ordinal activo)
- **CGAlpha v0.0.1:** 🧪 Experimental (solo Nexus y RiskBarrierLab placeholder)

---

## 🤝 Contribuir

Ver [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md) para el roadmap actual.

---

## 📜 Licencia

*Proyecto educacional/investigación - Václav Šindelář*

---

> **Última actualización:** 2026-02-01  
> **Versión del documento:** 2.0 (reescrito para v0.0.3/CGAlpha_0.0.1)
