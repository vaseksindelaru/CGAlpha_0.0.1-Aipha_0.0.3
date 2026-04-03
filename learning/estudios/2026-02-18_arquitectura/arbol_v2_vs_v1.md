# Análisis Arquitectónico: cgalpha_v2 vs (cgalpha v1 + aiphalab + core)

## Resumen Ejecutivo

cgalpha_v2 adopta **Clean Architecture** con **Bounded Contexts (DDD)**, eliminando la estructura monolítica y acoplada de v1. La nueva arquitectura separa el dominio de la infraestructura mediante **Ports & Adapters**, permitiendo testabilidad, mantenibilidad y extensibilidad profesionales.

---

## Comparación de Estructuras

### Capa Domain (Núcleo del Negocio)

| Aspecto | v1 (cgalpha + core) | v2 (cgalpha_v2) | Justificación |
|---------|---------------------|-----------------|---------------|
| Modelos | Dispersos en core/, cgalpha/ | domain/models/ | Coherencia del dominio |
| Interfaces | Implícitas, acopladas | domain/ports/ | Dependency Inversion |
| Tipos | Mezclados con lógica | shared/types.py | Single Source of Truth |
| Excepciones | core/exceptions.py (10KB) | shared/exceptions.py (11KB) | Mismo tamaño, mejor organización |

### Capa de Aplicación

**v1**: No existe. La lógica de aplicación está mezclada con infraestructura en `core/orchestrator_hardened.py` (17KB).

**v2**: `application/` vacío pero preparado para:
- Servicios de aplicación
- Use cases
- Orquestación de dominio

### Capa de Infraestructura

**v1**: 
- `cgalpha/nexus/` - Redis, task buffer
- `core/llm_providers/` - OpenAI provider
- `data_processor/` - Data fetching

**v2**: `infrastructure/` preparado para:
- Adapters que implementan Ports
- BinanceAdapter, RedisAdapter, LLMAdapter

### Capa de Configuración

**v1**: 
- `core/config_manager.py` (4.8KB)
- `core/config_validators.py` (8.9KB)
- Configuración dispersa

**v2**: 
- `config/settings.py` (3.4KB) - Configuración centralizada
- `config/paths.py` (6.8KB) - Rutas centralizadas

---

## Sistema Codecraft

**v1**: `cgalpha/codecraft/` (9 archivos, ~100KB total)
- `ast_modifier.py` (17KB)
- `git_automator.py` (18KB)
- `orchestrator.py` (21KB)
- `test_generator.py` (19KB)

**v2**: Pendiente de migrar a `interfaces/cli/codecraft/`

**Justificación**: Codecraft es una herramienta de desarrollo, no del dominio. Pertenece a la capa de interfaces.

---

## Sistema Ghost Architect

**v1**: `cgalpha/ghost_architect/simple_causal_analyzer.py` (62KB!)

**v2**: Dividido en:
- `domain/models/analysis.py` (8.8KB) - Modelos de análisis
- `domain/models/proposal.py` (7KB) - Propuestas de cambio

**Justificación**: Un archivo de 62KB viola Single Responsibility Principle. v2 separa por concepto.

---

## Sistema Nexus

**v1**: `cgalpha/nexus/` (6 archivos, ~40KB)
- `redis_client.py` (11KB)
- `task_buffer.py` (7KB)
- `coordinator.py` (5.9KB)

**v2**: Pendiente de migrar a `infrastructure/persistence/`

**Justificación**: Nexus es infraestructura de persistencia. Debe implementar Ports del dominio.

---

## Sistema Aiphalab (CLI)

**v1**: `aiphalab/commands/` (10 archivos, ~80KB)
- `librarian.py` (27KB!)
- `codecraft.py` (13KB)

**v2**: Pendiente de migrar a `interfaces/cli/`

**Justificación**: CLI es una interfaz de usuario. Pertenece a la capa de interfaces.

---

## Decisiones Arquitectónicas Clave

### 1. Clean Architecture

**Por qué se adoptó**:
- v1 tiene dependencias circulares: core/ depende de cgalpha/, cgalpha/ depende de core/
- v2 tiene dependencias unidireccionales: domain → ports ← infrastructure

```
v1 (Problemático):
core/ ←→ cgalpha/ ←→ aiphalab/

v2 (Limpio):
domain/ (centro)
   ↓
ports/ (interfaces)
   ↑
infrastructure/ (implementaciones)
```

### 2. Bounded Contexts (DDD)

**Por qué se adoptó**:
- v1 mezcla conceptos de trading, señales, y análisis en un solo módulo
- v2 separa por contexto de negocio

| Contexto | v1 | v2 |
|----------|----|----|
| Signal Detection | cgalpha/ghost_architect/ | domain/models/signal.py |
| Trading | core/trading_engine.py | domain/models/trade.py |
| Oracle | Disperso | domain/models/prediction.py |
| Causal Analysis | ghost_architect/ (62KB) | domain/models/analysis.py |

### 3. Ports & Adapters (Hexagonal)

**Por qué se adoptó**:
- v1 acopla a implementaciones concretas (Redis, OpenAI)
- v2 define interfaces (Protocol) que pueden tener múltiples implementaciones

```python
# v1 (Acoplado)
class RedisClient:
    def get_data(self): ...

# v2 (Desacoplado)
class DataPort(Protocol):
    def get_candles(self, symbol: str) -> list[Candle]: ...

class BinanceAdapter:
    def get_candles(self, symbol: str) -> list[Candle]: ...

class RedisAdapter:
    def get_candles(self, symbol: str) -> list[Candle]: ...
```

### 4. Dependency Inversion Principle

**Por qué se adoptó**:
- v1: Módulos de alto nivel dependen de bajo nivel
- v2: Ambos dependen de abstracciones

```python
# v1 (Violación DIP)
class TradingEngine:
    def __init__(self):
        self.redis = RedisClient()  # Acoplado

# v2 (DIP correcto)
class SignalDetector:
    def __init__(self, data_port: DataPort):
        self.data_port = data_port  # Inyectado
```

### 5. Separación de Responsabilidades

**Por qué se adoptó**:
- v1: `simple_causal_analyzer.py` (62KB) hace todo
- v2: Divide en modelos específicos de 6-8KB cada uno

---

## Beneficios Profesionales

### Testabilidad

**v1**: Difícil de testear por dependencias concretas
```python
# No se puede mockear fácilmente
def test_ghost_architect():
    analyzer = SimpleCausalAnalyzer()  # Depende de Redis, archivos, etc.
```

**v2**: Fácil de testear con Ports
```python
def test_signal_detector():
    mock_data = MockDataPort()  # Mock simple
    detector = SignalDetector(data_port=mock_data)
```

### Mantenibilidad

**v1**: Cambios en Redis rompen código de negocio
**v2**: Cambios en Redis solo afectan a RedisAdapter

### Extensibilidad

**v1**: Añadir Kraken requiere modificar código existente
**v2**: Añadir Kraken solo requiere nuevo KrakenAdapter

### Legibilidad

**v1**: 62KB en un archivo
**v2**: 6-8KB por archivo, cada uno con responsabilidad única

### Escalabilidad

**v1**: Monolito difícil de escalar
**v2**: Cada contexto puede escalar independientemente

---

## Migración de v1 a v2

| Componente v1 | Nueva ubicación v2 | Razón de cambio |
|---------------|-------------------|-----------------|
| core/exceptions.py | shared/exceptions.py | Dominio compartido |
| core/config_manager.py | config/settings.py | Configuración centralizada |
| cgalpha/ghost_architect/ | domain/models/analysis.py | Dominio de análisis |
| cgalpha/nexus/redis_client.py | infrastructure/persistence/ | Infraestructura |
| aiphalab/commands/ | interfaces/cli/ | Interfaz de usuario |
| core/trading_engine.py | application/trading/ | Servicio de aplicación |
| core/llm_providers/ | infrastructure/llm/ | Infraestructura externa |

---

## Problemas Resueltos

### Problema 1: Archivos Monolíticos
- v1: simple_causal_analyzer.py (62KB)
- v2: Dividido en analysis.py (8.8KB), proposal.py (7KB), signal.py (6.7KB)

### Problema 2: Dependencias Circulares
- v1: core/ depende de cgalpha/, cgalpha/ depende de core/
- v2: Dependencias unidireccionales (domain → ports ← infrastructure)

### Problema 3: Falta de Interfaces
- v1: Implementaciones concretas acopladas
- v2: Ports (Protocol) desacoplan dominio de infraestructura

### Problema 4: Configuración Dispersa
- v1: Configuración en múltiples archivos
- v2: config/settings.py centraliza todo

---

## Organización según Ruta de Aprendizaje

### Semana 1: Fundamentos Python (Hitos 1-5)

| Hito | Archivo v2 | Concepto | Líneas |
|------|-----------|----------|--------|
| 1 (Enum) | signal.py:30-35 | SignalDirection | LONG/SHORT |
| 2 (@dataclass) | signal.py:37-65 | Candle | OHLCV dataclass |
| 3 (frozen=True) | signal.py:37-65 | Value Objects | Inmutabilidad |
| 4 (__post_init__) | signal.py:66-74 | Validación | high >= low |
| 5 (NewType) | types.py:23-36 | Type aliases | SignalId, TradeId |

### Semana 2: Matemáticas (Hitos 6-10)

| Hito | Archivo v2 | Concepto |
|------|-----------|----------|
| 6 (Probabilidad) | prediction.py | Confidence |
| 7 (Media, StdDev) | trade.py | ATR calculation |
| 8 (MFE/MAE) | trade.py:53-98 | Trajectory |
| 9 (Ratios) | trade.py:88-98 | capture_efficiency |
| 10 (Repaso) | Todos | Integración |

### Semana 3: Trading (Hitos 11-15)

| Hito | Archivo v2 | Concepto |
|------|-----------|----------|
| 11 (Señales) | signal.py:167-208 | Signal class |
| 12 (ATR) | signal.py:189-191 | atr_value |
| 13 (TP/SL) | trade.py:137-139 | tp_factor, sl_factor |
| 14 (Triple Coincidence) | signal.py:127-165 | TripleCoincidenceResult |
| 15 (Repaso) | Todos | Integración |

### Semana 4: Arquitectura (Hitos 16-20)

| Hito | Archivo v2 | Concepto |
|------|-----------|----------|
| 16 (Value Objects) | signal.py, trade.py | frozen dataclass |
| 17 (Ports) | domain/ports/*.py | Protocol interfaces |
| 18 (Dependency Inversion) | bootstrap.py | Composition Root |
| 19 (Bounded Contexts) | domain/models/ | Separación por contexto |
| 20 (Proyecto Final) | Todos | Integración completa |

---

## Conclusión

cgalpha_v2 representa una mejora arquitectónica profesional significativa:

1. **Clean Architecture** - Dependencias unidireccionales
2. **Bounded Contexts** - Separación por dominio de negocio
3. **Ports & Adapters** - Desacoplamiento de infraestructura
4. **Single Responsibility** - Archivos de 6-8KB vs 62KB

**Próximos pasos**:
1. Migrar Codecraft a interfaces/cli/
2. Migrar Nexus a infrastructure/persistence/
3. Migrar Aiphalab a interfaces/cli/
4. Completar application/ con servicios de aplicación
5. Implementar adapters en infrastructure/