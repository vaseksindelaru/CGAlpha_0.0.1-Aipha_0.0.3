# 💡 GUÍA PRÁCTICA DE MEJORAS - EJEMPLOS DE IMPLEMENTACIÓN

## 1. REPARAR requirements.txt (P0 - CRÍTICA)

### Problema Actual
```txt
psutil==7.2.2
```
❌ Falta TODA la base del sistema.

### Solución Completa

**Paso 1: Generar requirements.txt completo**
```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
pip freeze > requirements_full.txt
# Luego editar para remover .venv entries
```

**Paso 2: requirements.txt Actualizado**
```txt
# Core Dependencies
click>=8.0.0
pandas>=1.3.0
numpy>=1.20.0
scikit-learn>=0.24.0
duckdb>=0.5.0
rich>=10.0.0
pydantic>=2.0.0
joblib>=1.0.0
psutil>=5.8.0

# LLM Integration
openai>=1.0.0
requests>=2.28.0

# Optional but recommended
pytest>=7.0.0
pytest-cov>=4.0.0
python-dotenv>=0.21.0
```

**Paso 3: Verificación**
```bash
pip install -r requirements.txt
python life_cycle.py --help  # Debe funcionar sin errores
```

---

## 2. MEJORAR MANEJO DE ERRORES (P0 - CRÍTICA)

### Antes ❌
```python
# trading_engine.py (línea ~45)
def load_data(self, source: str = "duckdb") -> pd.DataFrame:
    try:
        conn = duckdb.connect(db_path)
        df = conn.execute(f"SELECT * FROM {table_name} ORDER BY Open_Time").df()
        conn.close()
        return df
    except Exception as e:
        logger.error(f"Error cargando datos: {e}")
        return pd.DataFrame()  # ❌ Falla silenciosa
```

### Después ✅
```python
# core/exceptions.py (NUEVO)
class AiphaException(Exception):
    """Base exception para Aipha"""
    pass

class DataLoadError(AiphaException):
    """Falla al cargar datos"""
    pass

class ConfigurationError(AiphaException):
    """Configuración inválida"""
    pass

class OracleError(AiphaException):
    """Falla del Oracle/ML"""
    pass


# trading_engine.py (MEJORADO)
import logging
from pathlib import Path
from core.exceptions import DataLoadError

logger = logging.getLogger("TradingEngine")

def load_data(self, source: str = "duckdb") -> pd.DataFrame:
    """
    Carga datos de mercado con reintentos y fallback.
    
    Args:
        source: Backend de datos ("duckdb", "csv", "api")
    
    Returns:
        DataFrame con OHLCV
    
    Raises:
        DataLoadError: Si fallan todos los reintentos
    """
    max_retries = 3
    retry_delay = 2  # segundos
    
    for attempt in range(max_retries):
        try:
            if source == "duckdb":
                return self._load_from_duckdb()
            elif source == "csv":
                return self._load_from_csv()
            else:
                raise DataLoadError(f"Fuente desconocida: {source}")
                
        except FileNotFoundError as e:
            logger.error(f"Intento {attempt+1}/{max_retries}: Archivo no encontrado: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise DataLoadError(f"No se pudo cargar datos tras {max_retries} intentos") from e
                
        except Exception as e:
            logger.error(f"Intento {attempt+1}/{max_retries}: Error inesperado: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise DataLoadError(f"Error fatal cargando datos: {e}") from e
    
    # Nunca debe llegar aquí
    raise DataLoadError("Estado indeterminado")

def _load_from_duckdb(self) -> pd.DataFrame:
    """Implementación DuckDB específica"""
    db_path = "data_processor/data/aipha_data.duckdb"
    
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Base de datos no existe: {db_path}")
    
    try:
        conn = duckdb.connect(db_path)
        df = conn.execute(
            "SELECT * FROM btc_1h_data ORDER BY Open_Time LIMIT 10000"
        ).df()
        conn.close()
        
        if df.empty:
            raise DataLoadError("DataFrame vacío desde DuckDB")
        
        df['Open_Time'] = pd.to_datetime(df['Open_Time'])
        df = df.set_index('Open_Time')
        
        logger.info(f"✓ Datos cargados: {len(df)} filas")
        return df
        
    except duckdb.Error as e:
        raise DataLoadError(f"DuckDB error: {e}") from e
```

---

## 3. VALIDACIÓN CON PYDANTIC (P1 - IMPORTANTE)

### Antes ❌
```python
# config_manager.py
def set(self, key_path: str, value: Any) -> None:
    parts = key_path.split(".")
    val = self._config
    for part in parts[:-1]:
        if part not in val:
            val[part] = {}
        val = val[part]
    val[parts[-1]] = value
    self.save_config(self._config)  # ¿Validado? ¡NO!
```

### Después ✅
```python
# core/config_validators.py (NUEVO/MEJORADO)
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any

class TradingConfig(BaseModel):
    """Configuración validada del Trading Engine"""
    atr_period: int = Field(14, ge=5, le=200, description="Período ATR")
    tp_factor: float = Field(2.0, gt=0.1, lt=10.0, description="Factor TP (múltiplos ATR)")
    sl_factor: float = Field(1.0, gt=0.01, lt=5.0)
    time_limit: int = Field(24, ge=1, le=500)
    volume_percentile_threshold: int = Field(90, ge=50, le=99)
    body_percentile_threshold: int = Field(25, ge=10, le=50)
    
    @field_validator('tp_factor')
    @classmethod
    def tp_must_be_greater_than_sl(cls, v, info):
        if hasattr(info, 'data'):
            sl = info.data.get('sl_factor', 1.0)
            if v <= sl:
                raise ValueError('TP factor debe ser > SL factor')
        return v


class OracleConfig(BaseModel):
    """Configuración del Oracle"""
    confidence_threshold: float = Field(0.70, ge=0.0, le=1.0)
    n_estimators: int = Field(100, ge=10, le=1000)
    model_path: str = Field("oracle/models/proof_oracle.joblib")


class AiphaConfigValidator(BaseModel):
    """Configuración completa de Aipha"""
    Trading: TradingConfig = Field(default_factory=TradingConfig)
    Oracle: OracleConfig = Field(default_factory=OracleConfig)
    
    class Config:
        validate_assignment = True


# config_manager.py (MEJORADO)
class ConfigManager:
    def __init__(self, config_path: Path = Path("memory/aipha_config.json")):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load_initial_config()
        self._validator = AiphaConfigValidator(**self._config)

    def set(self, key_path: str, value: Any) -> None:
        """Establece un valor con validación"""
        parts = key_path.split(".")
        val = self._config
        
        # Aplicar cambio
        for part in parts[:-1]:
            if part not in val:
                val[part] = {}
            val = val[part]
        val[parts[-1]] = value
        
        # ✅ VALIDAR ANTES DE GUARDAR
        try:
            validated = AiphaConfigValidator(**self._config)
            self.save_config(self._config)
            logger.info(f"✓ Configuración válida: {key_path} = {value}")
        except Exception as e:
            logger.error(f"❌ Configuración inválida: {e}")
            # Revertir cambio
            del val[parts[-1]]
            raise ConfigurationError(f"Valor inválido para {key_path}: {e}") from e
```

---

## 4. REFACTORIZAR CLI EN MÓDULOS (P1 - IMPORTANTE)

### Estructura Actual ❌
```
aiphalab/
├── cli.py (1,649 líneas - MONOLÍTICO)
└── formatters.py
```

### Estructura Mejorada ✅
```
aiphalab/
├── cli.py (300 líneas - solo router)
├── commands/
│   ├── __init__.py
│   ├── status.py (200 líneas)
│   ├── cycle.py (250 líneas)
│   ├── config.py (200 líneas)
│   ├── history.py (150 líneas)
│   └── debug.py (150 líneas)
└── formatters.py (ya existe)
```

### Implementación

**aiphalab/cli.py (REFACTORIZADO)**
```python
#!/usr/bin/env python3
"""
AiphaLab CLI - Punto de entrada principal
Delega comandos a módulos especializados
"""

import click
import sys
from pathlib import Path

# Add Aipha root to path
AIPHA_ROOT = Path(__file__).resolve().parent.parent
if str(AIPHA_ROOT) not in sys.path:
    sys.path.insert(0, str(AIPHA_ROOT))

from aiphalab.commands.status import status_group
from aiphalab.commands.cycle import cycle_group
from aiphalab.commands.config import config_group
from aiphalab.commands.history import history_group


@click.group()
@click.option('--dry-run', is_flag=True, help='Simular sin persistir')
@click.pass_context
def cli(ctx, dry_run):
    """🦅 AiphaLab CLI - Control System Aipha v0.0.3"""
    ctx.ensure_object(dict)
    ctx.obj['dry_run'] = dry_run
    if dry_run:
        click.secho("⚠️  DRY-RUN MODE", fg='yellow', bold=True)


# Registrar groups
cli.add_command(status_group, name='status')
cli.add_command(cycle_group, name='cycle')
cli.add_command(config_group, name='config')
cli.add_command(history_group, name='history')


if __name__ == '__main__':
    cli()
```

**aiphalab/commands/status.py (NUEVO)**
```python
"""Comandos de estado del sistema"""

import click
from rich.console import Console
from core.context_sentinel import ContextSentinel

console = Console()


@click.group()
def status_group():
    """Ver estado del sistema"""
    pass


@status_group.command('show')
def show_status():
    """Mostrar estado actual"""
    try:
        sentinel = ContextSentinel()
        state = sentinel.query_memory('current_state') or {}
        
        console.print("[bold]Estado del Sistema:[/bold]")
        console.print(f"  Estado: {state.get('status', 'Unknown')}")
        console.print(f"  Ciclos: {state.get('cycle_count', 0)}")
        console.print(f"  Operaciones: {state.get('operations_count', 0)}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


@status_group.command('health')
def health_check():
    """Verificar salud del sistema"""
    from core.health_monitor import HealthMonitor
    
    try:
        monitor = HealthMonitor()
        health = monitor.get_overall_health()
        
        level_colors = {
            'healthy': 'green',
            'degraded': 'yellow',
            'warning': 'orange',
            'critical': 'red'
        }
        
        color = level_colors.get(health['level'], 'white')
        console.print(f"[{color}]Salud: {health['level'].upper()}[/{color}]")
        console.print(f"Detalles: {health.get('message', 'N/A')}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
```

**aiphalab/commands/cycle.py (NUEVO)**
```python
"""Comandos de ciclo de trading"""

import click
import asyncio
from core.orchestrator_hardened import CentralOrchestratorHardened, CycleType

@click.group()
def cycle_group():
    """Gestionar ciclos de trading"""
    pass

@cycle_group.command('run')
def run_cycle():
    """Ejecutar un ciclo de mejora"""
    orchestrator = CentralOrchestratorHardened()
    click.echo("Ejecutando ciclo...")
    
    try:
        asyncio.run(orchestrator.run_improvement_cycle(CycleType.USER))
        click.echo("✓ Ciclo completado")
    except Exception as e:
        click.secho(f"✗ Error: {e}", fg='red')
```

---

## 5. MODULARIZAR LLM ASSISTANT (P1 - IMPORTANTE)

### Antes ❌
```python
# core/llm_assistant.py (895 líneas)
# - API calls
# - Parsing
# - Retry logic
# - Todas mezcladas
```

### Después ✅
```
core/
├── llm_assistant.py (200 líneas - interfaz)
└── llm_providers/
    ├── __init__.py
    ├── base.py (interfaz abstracta)
    ├── openai_provider.py (provider OpenAI)
    └── claude_provider.py (provider Claude)
```

**core/llm_providers/base.py (NUEVO)**
```python
"""Interfaz base para proveedores LLM"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any

class LLMProvider(ABC):
    """Interfaz para proveedores LLM"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
    
    @abstractmethod
    def complete(self, prompt: str, system: str = None) -> str:
        """Generar completion"""
        pass
    
    @abstractmethod
    def chat(self, messages: List[Dict]) -> str:
        """Chat con historial"""
        pass


class RetryPolicy:
    """Política de reintentos con backoff exponencial"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Ejecutar función con reintentos"""
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"Reintentando en {delay}s (intento {attempt+1}/{self.max_retries})")
                time.sleep(delay)
```

**core/llm_providers/openai_provider.py (NUEVO)**
```python
"""Proveedor OpenAI"""

import openai
import logging
from core.llm_providers.base import LLMProvider, RetryPolicy

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """Implementación OpenAI"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        openai.api_key = api_key
        self.retry_policy = RetryPolicy(max_retries=3)
    
    def complete(self, prompt: str, system: str = None) -> str:
        """Generar completion"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        return self.retry_policy.execute_with_retry(
            self._call_openai,
            messages
        )
    
    def _call_openai(self, messages):
        """Llamada interna a OpenAI"""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response['choices'][0]['message']['content']


class RateLimiter:
    """Rate limiting para evitar throttling"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self.last_call = 0
    
    def wait_if_needed(self):
        """Esperar si es necesario"""
        import time
        elapsed = time.time() - self.last_call
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_call = time.time()
```

---

## 6. AÑADIR TYPE HINTS (P1 - IMPORTANTE)

### Antes ❌
```python
def run_cycle(self):
    df = self.load_data()
    signals = df[df['is_triple_coincidence']]
    return {"status": "success"}
```

### Después ✅
```python
def run_cycle(self) -> Dict[str, Any]:
    """
    Ejecuta un ciclo completo de trading.
    
    Returns:
        Dict con status, señales encontradas y trayectorias guardadas
    
    Raises:
        DataLoadError: Si falla la carga de datos
    """
    df: pd.DataFrame = self.load_data()
    
    signals: pd.DataFrame = df[df['is_triple_coincidence']]
    
    result: Dict[str, Any] = {
        "status": "success",
        "signals_found": len(signals),
        "trajectories_saved": 0
    }
    
    return result
```

---

## 7. LOGGING DE PERFORMANCE (P2 - DESEABLE)

**core/performance_tracker.py (NUEVO)**
```python
"""Instrumentación de performance"""

import time
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)


def track_performance(threshold_ms: float = 100):
    """Decorador para tracking de performance
    
    Args:
        threshold_ms: Alerta si excede este tiempo
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            if elapsed_ms > threshold_ms:
                logger.warning(
                    f"⏱️ {func.__name__} took {elapsed_ms:.2f}ms "
                    f"(threshold: {threshold_ms}ms)"
                )
            else:
                logger.debug(f"⏱️ {func.__name__} took {elapsed_ms:.2f}ms")
            
            return result
        return wrapper
    return decorator


# Uso
@track_performance(threshold_ms=500)
def run_cycle(self):
    # ... código ...
```

---

## 8. TESTS DE INTEGRACIÓN (P1 - IMPORTANTE)

**tests/integration/test_lifecycle.py (NUEVO)**
```python
"""Tests de integración del lifecycle completo"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from life_cycle import main
from core.trading_engine import TradingEngine
from core.orchestrator_hardened import CentralOrchestratorHardened


class TestLifecycle:
    """Tests del ciclo de vida completo"""
    
    @pytest.fixture
    def temp_memory(self):
        """Crear directorio temporal para memory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_orchestrator_initializes(self):
        """Verificar que Orchestrator se inicializa"""
        orchestrator = CentralOrchestratorHardened()
        assert orchestrator is not None
        assert orchestrator.state is not None
    
    def test_trading_engine_loads(self):
        """Verificar que TradingEngine se carga"""
        engine = TradingEngine()
        assert engine is not None
        assert engine.config is not None
    
    @patch('data_processor.data.aipha_data.duckdb')
    def test_full_cycle(self, mock_db):
        """Teste el ciclo completo (mocked)"""
        # Setup
        engine = TradingEngine()
        
        # Mock de datos
        mock_db.connect.return_value.execute.return_value.df.return_value = (
            self._create_mock_dataframe()
        )
        
        # Execute
        result = engine.run_cycle()
        
        # Assert
        assert result['status'] in ['success', 'neutral', 'error']
    
    def _create_mock_dataframe(self):
        """Crear DataFrame mock para testing"""
        import pandas as pd
        return pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [101, 102, 103],
            'Low': [99, 100, 101],
            'Close': [100.5, 101.5, 102.5],
            'Volume': [1000, 1100, 1200],
        })
```

---

## 🎯 RESUMEN DE CAMBIOS

| Cambio | Líneas | Tiempo | Impacto |
|--------|--------|--------|--------|
| Fijar requirements.txt | 10 | 30 min | 🔴 CRÍTICO |
| Excepciones personalizadas | 50 | 2 hrs | 🔴 ALTO |
| Validación Pydantic | 150 | 3 hrs | 🟠 ALTO |
| Refactorizar CLI | 400 | 8 hrs | 🟠 MEDIO |
| Modularizar LLM | 300 | 6 hrs | 🟠 MEDIO |
| Type hints | +1000 | 16 hrs | 🟠 MEDIO |
| Performance tracking | 100 | 4 hrs | 🟡 BAJO |
| Tests integración | 300 | 12 hrs | 🟠 ALTO |

**Total estimado:** 60-80 horas de desarrollo  
**Beneficio:** Código production-ready, mantenible, testeable

---

**Implementar esto incrementalmente garantizará un sistema robusto y escalable.**
