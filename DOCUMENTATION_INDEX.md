# 📚 Índice de Documentación - Aipha v0.0.3 / CGAlpha v0.0.1

> **Última actualización:** 2026-02-01  
> **Versión del sistema:** Aipha v0.0.3 | CGAlpha v0.0.1

---

## 🎯 Documentos Principales (LÉASE PRIMERO)

1. **[README.md](./README.md)** ⭐
   - Visión general del sistema unificado
   - Guía de instalación y uso
   - Arquitectura de 5 capas
   - Roadmap v0.0.3 → v0.1.0

2. **[RESUMEN_EJECUTIVO_v0.0.3.md](./RESUMEN_EJECUTIVO_v0.0.3.md)** ⭐
   - Métricas de la refactorización
   - Decisiones autónomas justificadas
   - Estado de implementación
   - Verificación de requisitos

3. **[TECHNICAL_CONSTITUTION.md](./TECHNICAL_CONSTITUTION.md)** 📘
   - Constitución técnica completa
   - Detalle de capas 1-5 de Aipha
   - Detalle completo de CGAlpha (Nexus + Labs)
   - Protocolo de evolución
   - Glosario técnico
   - **⚠️ Este es el blueprint operativo del sistema**

---

## 📋 Documentos de Desarrollo

4. **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)**
   - Plan de implementación detallado
   - Fases 1-4 de desarrollo
   - Prioridades de componentes
   - Métricas de éxito

5. **[CHANGELOG_v0.0.3.md](./CHANGELOG_v0.0.3.md)**
   - Changelog exhaustivo con justificaciones
   - Breaking changes documentados
   - Guías de migración
   - Bugs conocidos

---

## 📖 Documentación Legacy (v0.0.2 y anteriores)

6. **[ARCHITECTURE.md](./ARCHITECTURE.md)**
   - Diseño técnico del sistema v0.0.2
   - ⚠️ Requiere actualización para v0.0.3

7. **[GUIA_CLI_PANEL_CONTROL.md](./GUIA_CLI_PANEL_CONTROL.md)**
   - Manual completo de comandos CLI
   - Panel de control en tiempo real
   - ⚠️ Pendiente: Comandos CGAlpha

8. **[RESUMEN_FINAL_COMPLETO_AIPHA_v2_1.md](./RESUMEN_FINAL_COMPLETO_AIPHA_v2_1.md)**
   - Hito de rentabilidad v2.1
   - Win Rate 56.12%
   - Estado histórico del sistema

9. **Otros documentos legacy:**
   - `FINAL_STATUS.md`
   - `IMPLEMENTATION_COMPLETE.md`
   - `IMPLEMENTATION_SUMMARY.md`
   - `ENHANCED_DIAGNOSTIC_SYSTEM.md`

---

## 🔬 Documentación de Subsistemas

### Data Processor
- **[data_processor/README.md](./data_processor/README.md)**
- **[data_processor/docs/Documentación data_system.md](./data_processor/docs/Documentación%20data_system.md)**

### Trading Manager
- **[trading_manager/README.md](./trading_manager/README.md)**

### Oracle
- **[oracle/README.md](./oracle/README.md)**
- **[oracle/docs/oracle_construction_guide.md](./oracle/docs/oracle_construction_guide.md)**

### Data Postprocessor
- **[data_postprocessor/README.md](./data_postprocessor/README.md)**
- **[data_postprocessor/docs/data_postprocessor_construction_guide.md](./data_postprocessor/docs/data_postprocessor_construction_guide.md)**

---

## 🆕 Documentación CGAlpha (v0.0.1)

### Módulos Implementados

10. **[cgalpha/nexus/ops.py](./cgalpha/nexus/ops.py)**
    - CGA_Ops: Supervisor de recursos
    - Semáforo 🟢🟡🔴
    - ✅ Funcional - Test: `python -m cgalpha.nexus.ops`

11. **[cgalpha/nexus/coordinator.py](./cgalpha/nexus/coordinator.py)**
    - CGA_Nexus: Coordinador central
    - Orquestación de Labs
    - Síntesis para LLM
    - ✅ Funcional - Test: `python -m cgalpha.nexus.coordinator`

12. **[cgalpha/labs/risk_barrier_lab.py](./cgalpha/labs/risk_barrier_lab.py)**
    - RiskBarrierLab: Análisis causal
    - ⚠️ PLACEHOLDER (interface completa, lógica pending)
    - Pendiente: Integración EconML completa

---

## 🧪 Tests

- **[tests/test_potential_capture_engine.py](./tests/test_potential_capture_engine.py)**
  - ⚠️ Requiere actualización para sensor ordinal

- **Nuevos tests requeridos (v0.0.4):**
  - `tests/test_cgalpha_nexus.py`
  - `tests/test_cga_ops.py`
  - `tests/test_evolutionary_bridge.py`

---

## 🗂️ Archivos de Configuración

- **[.env](./.env)** - Variables de entorno (⚠️ NO commitear)
- **[.env.example](./.env.example)** - Template de configuración
- **[pyproject.toml](./pyproject.toml)** - Dependencias del proyecto
- **[pytest.ini](./pytest.ini)** - Configuración de tests

---

## 📊 Archivos de Datos

- **`aipha_memory/action_history.jsonl`** - Historial inmutable de acciones
- **`aipha_memory/current_state.json`** - Estado actual del sistema
- **`aipha_memory/evolutionary_bridge.jsonl`** - 🆕 Vector de evidencia (CGAlpha)

- **`memory/` (legacy)** - Sistema de persistencia v0.0.2
  - `aipha_config.json`
  - `proposals.jsonl`
  - `quarantine.jsonl`
  - `health_events.jsonl`

---

## 📖 Cómo Navegar la Documentación

### Para Entender el Sistema (Lectura Secuencial):
1. **README.md** - Visión general
2. **TECHNICAL_CONSTITUTION.md** - Blueprint técnico
3. **RESUMEN_EJECUTIVO_v0.0.3.md** - Estado actual

### Para Desarrollar (Implementación):
1. **IMPLEMENTATION_PLAN.md** - Qué falta implementar
2. **CHANGELOG_v0.0.3.md** - Qué cambió y por qué
3. Documentación de subsistemas específicos

### Para Troubleshooting:
1. **GUIA_CLI_PANEL_CONTROL.md** - Comandos de diagnóstico
2. **ENHANCED_DIAGNOSTIC_SYSTEM.md** - Sistema de salud
3. Tests unitarios relevantes

---

## 🔄 Documentación Pendiente (v0.0.4)

- [ ] Actualizar `ARCHITECTURE.md` con arquitectura dual
- [ ] Crear `CGALPHA_LABS_GUIDE.md` (guía de Labs)
- [ ] Crear `ECONML_INTEGRATION_GUIDE.md` (cuando se implemente)
- [ ] Actualizar `GUIA_CLI_PANEL_CONTROL.md` con comandos CGAlpha
- [ ] Crear diagramas de arquitectura visual

---

> **Nota:** Los documentos marcados con ⭐ son de lectura OBLIGATORIA para entender el sistema v0.0.3.
