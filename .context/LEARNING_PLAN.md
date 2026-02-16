# Plan de Aprendizaje Python + CGAlpha v2

**Objetivo**: Aprender Python programando CGAlpha v2 mientras se mantiene v1 operativo

**Filosofía**: "Aprender haciendo" - cada concepto de Python se aprende implementando funcionalidad real

---

## 1. DIAGNÓSTICO INICIAL

### ¿Qué nivel de Python tienes?

| Nivel | Descripción | Indicadores |
|-------|-------------|-------------|
| **Beginner** | Sintaxis básica, variables, funciones | ¿Puedes escribir un script que lea un archivo CSV? |
| **Intermediate** | Clases, módulos, excepciones | ¿Entiendes `@dataclass`, `@property`, `try/except`? |
| **Advanced** | Decoradores, generators, async | ¿Has usado `asyncio`, `contextmanager`, metaclasses? |

### ¿Qué conceptos de CGAlpha dominas?

| Componente | Comprensión | Código leído |
|------------|-------------|--------------|
| Signal Detection | ¿? | ¿? |
| Oracle/Prediction | ¿? | ¿? |
| Causal Analysis | ¿? | ¿? |
| CodeCraft | ¿? | ¿? |

---

## 2. RUTINA DIARIA DE APRENDIZAJE (Propuesta)

### Estructura de 30-45 minutos

```
+-------------------------------------------------------------+
|  FASE 1: V1 OPERATIONS (10 min)                             |
|  +-- Ejecutar check_phase7.sh --with-analyze               |
|  +-- Guardar métricas: blind_test_ratio, order_book_coverage|
|  +-- Revisar decisiones (HOLD/PROCEED)                      |
|  +-- Anotar observaciones en .context/daily_log.jsonl       |
+-------------------------------------------------------------+
|  FASE 2: PYTHON CONCEPT (15 min)                            |
|  +-- Leer 1 concepto de Python                              |
|  +-- Ejercicio pequeño (no relacionado con CGAlpha)         |
|  +-- Ejemplo: "Hoy aprendí sobre @dataclass"                |
+-------------------------------------------------------------+
|  FASE 3: CGAlpha CODE EXPLORATION (15 min)                  |
|  +-- Leer 1 archivo de v1 o v2                              |
|  +-- Identificar patrones de Python usados                  |
|  +-- Preguntas al LLM sobre el código                       |
+-------------------------------------------------------------+
```

### Integración con CLI (Propuesta)

```bash
# Comando propuesto: cgalpha learn
cgalpha learn --concept dataclass        # Explica concepto con ejemplos de CGAlpha
cgalpha learn --file cgalpha_v2/domain/models/signal.py  # Analiza archivo
cgalpha learn --quiz                     # Quiz sobre lo aprendido hoy
cgalpha learn --progress                 # Muestra progreso de aprendizaje
```

---

## 3. RUTA DE APRENDIZAJE POR COMPONENTES

### Fase A: Fundamentos de Python (2-4 semanas)

| Semana | Concepto Python | Archivo CGAlpha para practicar |
|--------|-----------------|--------------------------------|
| 1 | `dataclass`, `frozen=True` | `cgalpha_v2/domain/models/signal.py` |
| 2 | `Enum`, `typing` | `cgalpha_v2/shared/types.py` |
| 3 | `Protocol`, interfaces | `cgalpha_v2/domain/ports/data_port.py` |
| 4 | Excepciones custom | `cgalpha_v2/shared/exceptions.py` |

**Ejercicio por semana**:
1. Crear un nuevo modelo `MarketSnapshot` en v2
2. Añadir un nuevo tipo `MarketRegime` (Enum)
3. Crear un nuevo port `NotificationPort`
4. Crear una excepción `MarketClosedError`

### Fase B: Estructuras de Datos (3-4 semanas)

| Semana | Concepto Python | Archivo CGAlpha para practicar |
|--------|-----------------|--------------------------------|
| 5 | List comprehensions, generators | Detectores de señales |
| 6 | `dict`, `defaultdict`, `Counter` | Análisis de trades |
| 7 | `dataclasses` anidados | Configuración anidada |
| 8 | `pydantic` (validación) | Settings con validación |

### Fase C: Programación Orientada a Objetos (4-6 semanas)

| Semana | Concepto Python | Archivo CGAlpha para practicar |
|--------|-----------------|--------------------------------|
| 9-10 | Clases, herencia, composición | Servicios de dominio |
| 11-12 | Dependency Injection | Bootstrap, composición |
| 13-14 | Patrones de diseño (Strategy, Factory) | Detectores como strategies |

---

## 4. SISTEMA ACTOR-CRITIC PARA APRENDIZAJE

### Propuesta: Roles Adaptados

| Rol | LLM | Función en Aprendizaje |
|-----|-----|------------------------|
| **MENTOR** | LLM Avanzado (Claude/GPT-4) | Diseña ejercicios, explica conceptos avanzados |
| **TUTOR** | LLM Local (Ollama) | Responde preguntas rápidas, revisa código |
| **STUDENT** | Tú | Implementa, pregunta, practica |

### Flujo de Aprendizaje Actor-Critic

```
MENTOR (Avanzado)          TUTOR (Local)           STUDENT (Tú)
      |                         |                       |
      |-- 1. Diseñar ejercicio ->|                       |
      |                         |                       |
      |                         |-- 2. Presentar ------>|
      |                         |    ejercicio          |
      |                         |                       |
      |                         |<- 3. Preguntas -------|
      |                         |    (ayuda)            |
      |                         |                       |
      |                         |    4. Implementar --->|
      |                         |                       |
      |<- 5. Revisar código ----|<- 6. Enviar código --|
      |                         |                       |
      |-- 7. Feedback --------->|-- 8. Explicar ------>|
      |    (aprobar/mejorar)    |    correcciones      |
```

### Implementación en CLI

```bash
# Iniciar sesión de aprendizaje
cgalpha learn --start dataclass

# TUTOR (local) presenta ejercicio
# STUDENT implementa
# STUDENT pide revisión
cgalpha learn --submit my_solution.py

# MENTOR (avanzado) revisa cuando esté disponible
cgalpha learn --review
```

---

## 5. INTEGRACIÓN CON V1: RUTINA DIARIA V03

### Mejoras a v1 que NO afectan v2

| Mejora | Impacto en v1 | Riesgo para v2 |
|--------|---------------|----------------|
| Añadir logging detallado | Bajo | Ninguno |
| Mejorar mensajes de error | Bajo | Ninguno |
| Añadir métricas nuevas | Bajo | Ninguno |
| Refactorizar funciones pequeñas | Medio | Bajo |
| Cambiar arquitectura | Alto | Requiere consulta |

### Propuesta: Daily Log en `.context/`

```jsonl
{"date": "2026-02-16", "phase7_status": "HOLD_V03", "blind_test_ratio": 1.0, "order_book_coverage": 0.0, "python_concept": "dataclass", "file_read": "signal.py", "questions": ["¿Por qué frozen=True?"], "notes": "Entendí que frozen hace el objeto inmutable"}
```

### Comando CLI para Daily Log

```bash
cgalpha daily --log "Hoy aprendí dataclass, leí signal.py"
cgalpha daily --metrics  # Guarda métricas de phase7
cgalpha daily --summary  # Resumen de la semana
```

---

## 6. EVALUACIÓN CRÍTICA DE TUS PROPUESTAS

### Propuesta 1: CLI para Aprendizaje Continuo

**Ventajas**:
- Integración natural con flujo de trabajo
- Historial de aprendizaje en `.context/`
- Progreso medible

**Riesgos**:
- Sobrecargar la CLI con funciones no esenciales
- Distracción del objetivo principal (trading)

**Recomendación**: Implementar como comando `cgalpha learn` separado, opcional

### Propuesta 2: Actor-Critic en Aprendizaje con LLM Local

**Ventajas**:
- Aprovecha recursos existentes
- Feedback inmediato del TUTOR local
- Revisión profunda del MENTOR avanzado

**Riesgos**:
- Coordinación entre LLMs puede ser compleja
- Calidad del TUTOR local limitada

**Recomendación**: Implementar en fases:
1. Fase 1: Solo TUTOR local para preguntas rápidas
2. Fase 2: Añadir MENTOR para revisiones semanales
3. Fase 3: Sistema completo Actor-Critic

---

## 7. PLAN DE IMPLEMENTACIÓN

### Semana 1-2: Fundamentos

1. **Instalar dependencias de aprendizaje**:
   ```bash
   pip install jupyter ipython pytest pytest-cov
   ```

2. **Crear entorno de práctica**:
   ```
   cgalpha_v2/
   +-- learning/
       +-- exercises/      # Ejercicios de Python
       +-- notebooks/      # Jupyter notebooks
       +-- solutions/      # Soluciones propias
   ```

3. **Rutina diaria**:
   - Ejecutar `check_phase7.sh`
   - Leer 1 archivo de v2
   - Hacer 1 ejercicio de Python
   - Anotar en daily log

### Semana 3-4: Primer Componente

1. **Elegir componente**: Signal Detection (más simple)
2. **Leer código existente**: `cgalpha/ghost_architect/simple_causal_analyzer.py`
3. **Implementar en v2**: `cgalpha_v2/application/services/signal_detector.py`
4. **Tests**: Escribir tests para el nuevo código

---

## 8. MÉTRICAS DE PROGRESO

### Python Skills

| Concepto | Fecha aprendido | Ejercicio completado | Aplicado en CGAlpha |
|----------|-----------------|---------------------|---------------------|
| dataclass | | | |
| Enum | | | |
| Protocol | | | |
| Exceptions | | | |

### CGAlpha Comprensión

| Componente | Código leído | Entendido | Implementado en v2 |
|------------|--------------|-----------|---------------------|
| Signal Detection | | | |
| Oracle | | | |
| Causal Analysis | | | |
| CodeCraft | | | |

---

## 9. PRÓXIMOS PASOS INMEDIATOS

1. **Configurar credenciales Git** para push
2. **Decidir**: ¿Empezar con Fase A (Fundamentos) o directamente con Signal Detection?
3. **Crear** directorio `cgalpha_v2/learning/`
4. **Implementar** comando `cgalpha learn` básico (opcional)

---

**Pregunta para ti**: ¿Prefieres empezar con ejercicios de Python puro (Fase A) o quieres aprender Python mientras implementas Signal Detection en v2 (enfoque "aprender haciendo")?