# PROMPT: Análisis Arquitectónico de CGAlpha v2 vs v1

## Tu Rol
Eres el **ARCHITECT** - un experto en arquitectura de software, diseño limpio, y patrones de diseño. Tu especialidad es explicar decisiones arquitectónicas y justificar mejoras técnicas.

---

## Contexto del Proyecto

**CGAlpha** es un proyecto dual que combina:
- **cgalpha/** - Sistema de trading algorítmico
- **aipha/** (aiphalab/) - Sistema de orquestación con LLM

Ambos funcionan juntos bajo el nombre unificado **CGAlpha**.

---

## Tu Tarea

Genera un análisis completo del árbol de directorios de **cgalpha_v2** comparándolo con **cgalpha v1 + aiphalab**, justificando cada decisión de diseño desde una perspectiva profesional.

---

## Estructura de cgalpha_v2 (NUEVA)

```
cgalpha_v2/
├── __init__.py
├── bootstrap.py                    # Composition Root
├── application/                    # Servicios de aplicación
├── config/
│   ├── __init__.py
│   ├── paths.py                    # Rutas centralizadas
│   └── settings.py                 # Configuración global
├── domain/
│   ├── __init__.py
│   ├── models/                     # Value Objects & Entities
│   │   ├── __init__.py
│   │   ├── analysis.py             # Causal Analysis context
│   │   ├── config.py               # Configuration context
│   │   ├── health.py               # Health Check context
│   │   ├── prediction.py           # Oracle context
│   │   ├── proposal.py             # Evolution context
│   │   ├── signal.py               # Signal Detection context
│   │   └── trade.py                # Trading context
│   └── ports/                      # Interfaces (Protocol)
│       ├── __init__.py
│       ├── config_port.py
│       ├── data_port.py
│       ├── llm_port.py
│       ├── memory_port.py
│       └── prediction_port.py
├── infrastructure/                 # Adaptadores concretos
├── interfaces/                     # CLI, API, UI
├── learning/
│   └── exercises/
└── shared/
    ├── __init__.py
    ├── exceptions.py               # Excepciones del dominio
    └── types.py                    # NewType aliases
```

---

## Estructura de cgalpha v1 (ANTERIOR)

```
cgalpha/
├── __init__.py
├── orchestrator.py                 # Orchestrador monolítico
├── codecraft/                      # Sistema de auto-modificación
│   ├── __init__.py
│   ├── ast_modifier.py             # Modificación de AST
│   ├── git_automator.py            # Automatización Git
│   ├── orchestrator.py             # Otro orchestrador
│   ├── proposal_generator.py       # Generación de propuestas
│   ├── proposal_parser.py          # Parsing de propuestas
│   ├── safety_validator.py         # Validación de seguridad
│   ├── technical_spec.py           # Especificaciones técnicas
│   ├── test_generator.py           # Generación de tests
│   └── templates/
├── ghost_architect/
│   ├── __init__.py
│   ├── simple_causal_analyzer.py   # Análisis causal (62KB!)
│   └── templates/
├── labs/
│   ├── __init__.py
│   └── risk_barrier_lab.py         # Experimentos
└── nexus/
    ├── __init__.py
    ├── applicator.py
    ├── coordinator.py
    ├── ops.py
    ├── redis_client.py
    └── task_buffer.py
```

---

## Estructura de aiphalab (ANTERIOR - parte de Aipha)

```
aiphalab/
├── __init__.py
├── cli.py                          # CLI básico
├── cli_v2.py                       # CLI mejorado
├── dashboard.py                    # Dashboard web
├── formatters.py                   # Formateo de salida
└── commands/
    ├── __init__.py
    ├── base.py                     # Comando base
    ├── codecraft.py                # Comandos codecraft
    ├── config.py                   # Comandos config
    ├── cycle.py                    # Comandos cycle
    ├── debug.py                    # Comandos debug
    ├── docs.py                     # Comandos docs
    ├── history.py                  # Comandos history
    ├── librarian.py                # Comandos librarian (27KB!)
    └── status.py                   # Comandos status
```

---

## Estructura de core/ (ANTERIOR - compartido)

```
core/
├── __init__.py
├── atomic_update_system.py
├── change_evaluator.py
├── config_manager.py
├── config_validators.py
├── context_sentinel.py
├── exceptions.py
├── execution_queue.py
├── health_monitor.py
├── llm_assistant_v2.py
├── memory_manager.py
├── orchestrator_hardened.py
├── performance_logger.py
├── quarantine_manager.py
├── trading_engine.py
├── type_hints_generator.py
└── llm_providers/
    ├── __init__.py
    ├── base.py
    ├── openai_provider.py
    └── rate_limiter.py
```

---

## Formato de Respuesta Esperado

```markdown
# Análisis Arquitectónico: cgalpha_v2 vs (cgalpha v1 + aiphalab + core)

## Resumen Ejecutivo
{2-3 líneas resumiendo la mejora principal}

## Comparación de Estructuras

### Capa Domain (Núcleo del Negocio)
| Aspecto | v1 (cgalpha + core) | v2 (cgalpha_v2) | Justificación |
|---------|---------------------|-----------------|---------------|
| Modelos | Dispersos en core/ | domain/models/ | {por qué mejoró} |
| Interfaces | Implícitas | domain/ports/ | {por qué mejoró} |

### Capa de Aplicación
{explicación de la diferencia}

### Capa de Infraestructura
{explicación de la diferencia}

### Capa de Configuración
{explicación de la diferencia}

### Sistema Codecraft
{cómo se integra en v2}

### Sistema Ghost Architect
{cómo se integra en v2}

### Sistema Nexus
{cómo se integra en v2}

### Sistema Aiphalab (CLI)
{cómo se integra en v2}

## Decisiones Arquitectónicas Clave

### 1. Clean Architecture
{por qué se adoptó y qué mejora}

### 2. Bounded Contexts (DDD)
{por qué se adoptó y qué mejora}

### 3. Ports & Adapters (Hexagonal)
{por qué se adoptó y qué mejora}

### 4. Dependency Inversion Principle
{por qué se adoptó y qué mejora}

### 5. Separación de Responsabilidades
{por qué se adoptó y qué mejora}

## Beneficios Profesionales

### Testabilidad
{cómo mejoró con ejemplos concretos}

### Mantenibilidad
{cómo mejoró con ejemplos concretos}

### Extensibilidad
{cómo mejoró con ejemplos concretos}

### Legibilidad
{cómo mejoró con ejemplos concretos}

### Escalabilidad
{cómo mejoró con ejemplos concretos}

## Migración de v1 a v2

| Componente v1 | Nueva ubicación v2 | Razón de cambio |
|---------------|-------------------|-----------------|
| core/exceptions.py | shared/exceptions.py | {razón} |
| core/config_manager.py | config/settings.py | {razón} |
| cgalpha/ghost_architect/ | domain/models/analysis.py | {razón} |
| aiphalab/commands/ | interfaces/cli/ | {razón} |
| ... | ... | ... |

## Problemas Resueltos

### Problema 1: Archivos Monolíticos
- v1: simple_causal_analyzer.py (62KB)
- v2: Dividido en modelos específicos

### Problema 2: Dependencias Circulares
- v1: core/ depende de cgalpha/, cgalpha/ depende de core/
- v2: Dependencias unidireccionales

### Problema 3: Falta de Interfaces
- v1: Implementaciones concretas acopladas
- v2: Ports (Protocol) desacoplan

## Conclusión
{resumen de la mejora profesional y próximos pasos}

---

## Organización según Ruta de Aprendizaje

Organiza tu respuesta según los 20 hitos de aprendizaje definidos en `learning/RUTA.md`:

### Semana 1: Fundamentos Python (Hitos 1-5)
Relaciona cada archivo de cgalpha_v2 con los conceptos:
- Hito 1 (Enum): `signal.py:30-35` - SignalDirection
- Hito 2 (@dataclass): `signal.py:37-65` - Candle
- Hito 3 (frozen=True): `signal.py:37-65` - Value Objects
- Hito 4 (__post_init__): `signal.py:66-74` - Validación
- Hito 5 (NewType): `types.py:23-36` - Type aliases

### Semana 2: Matemáticas (Hitos 6-10)
Relaciona con:
- `trade.py` - Trajectory, MFE/MAE
- `prediction.py` - Probabilidad, confidence

### Semana 3: Trading (Hitos 11-15)
Relaciona con:
- `signal.py` - Signal, TripleCoincidenceResult
- `trade.py` - TradeRecord, TradeOutcome

### Semana 4: Arquitectura (Hitos 16-20)
Relaciona con:
- `domain/models/` - Value Objects
- `domain/ports/` - Ports (Interfaces)
- `bootstrap.py` - Dependency Inversion
- Estructura completa - Bounded Contexts
```

---

## Restricciones

- Usar terminología técnica precisa (DDD, Clean Architecture, SOLID)
- Incluir diagramas ASCII cuando sea útil
- Justificar cada decisión con principios de ingeniería de software
- Máximo 10000 palabras en total
- Enfocarse en beneficios profesionales, no solo estéticos
- Mencionar archivos específicos con sus tamaños cuando sea relevante
- **Organizar según los 20 hitos de aprendizaje**