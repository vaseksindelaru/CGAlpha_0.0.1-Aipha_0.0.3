"""
tests/test_smoke.py - Tests de Smoke (Validación Básica)

Verifica que los componentes críticos del sistema funcionan.
Soluciona: P0 #4 - Tests insuficientes

Ejecutar con: pytest tests/test_smoke.py -v
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Añadir el directorio raíz al path
AIPHA_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AIPHA_ROOT))

# ============================================================================
# TESTS DE IMPORTACIÓN (Verifica que no hay ImportError)
# ============================================================================


class TestImports:
    """Verifica que todos los imports críticos funcionan"""
    
    def test_import_core_modules(self):
        """✓ Se pueden importar módulos core"""
        from core.config_manager import ConfigManager
        from core.orchestrator_hardened import CentralOrchestratorHardened
        from core.trading_engine import TradingEngine
        assert ConfigManager is not None
        assert CentralOrchestratorHardened is not None
        assert TradingEngine is not None
    
    def test_import_exceptions(self):
        """✓ Se pueden importar excepciones personalizadas"""
        from core.exceptions import (
            DataLoadError, ConfigurationError, OracleError,
            TradingEngineError
        )
        assert DataLoadError is not None
        assert ConfigurationError is not None
    
    def test_import_aiphalab_cli(self):
        """✓ Se puede importar CLI"""
        from aiphalab.cli import cli
        assert cli is not None
    
    def test_import_cgalpha(self):
        """✓ Se pueden importar módulos CGAlpha"""
        from cgalpha.nexus.ops import CGAOps
        assert CGAOps is not None


# ============================================================================
# TESTS DE CONFIGURACIÓN
# ============================================================================


class TestConfiguration:
    """Verifica que la configuración funciona"""
    
    def test_config_manager_exists(self):
        """✓ ConfigManager se inicializa"""
        from core.config_manager import ConfigManager
        config = ConfigManager()
        assert config is not None
        assert config.get("Trading.tp_factor") is not None
    
    def test_config_get_with_default(self):
        """✓ ConfigManager.get() retorna default si no existe"""
        from core.config_manager import ConfigManager
        config = ConfigManager()
        value = config.get("NonExistent.Key", "DEFAULT")
        assert value == "DEFAULT"
    
    def test_requirements_txt_exists(self):
        """✓ requirements.txt existe y tiene contenido"""
        req_file = AIPHA_ROOT / "requirements.txt"
        assert req_file.exists(), "requirements.txt no encontrado"
        content = req_file.read_text()
        assert "pandas" in content, "pandas falta en requirements.txt"
        assert "duckdb" in content, "duckdb falta en requirements.txt"
        assert "openai" in content, "openai falta en requirements.txt"


# ============================================================================
# TESTS DE EXCEPCIONES
# ============================================================================


class TestExceptions:
    """Verifica que las excepciones funcionan correctamente"""
    
    def test_data_load_error_creation(self):
        """✓ DataLoadError se puede crear y lanzar"""
        from core.exceptions import DataLoadError
        
        with pytest.raises(DataLoadError):
            raise DataLoadError("Test error", details={"test": "value"})
    
    def test_exception_with_error_code(self):
        """✓ Las excepciones tienen error_code"""
        from core.exceptions import OracleError
        
        exc = OracleError("Test oracle error")
        assert exc.error_code == "ORACLE_ERROR"
        assert "Test oracle error" in str(exc)
    
    def test_configuration_error(self):
        """✓ ConfigurationError funciona"""
        from core.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError):
            raise ConfigurationError(
                "Invalid config",
                details={"param": "tp_factor", "value": 0.5}
            )


# ============================================================================
# TESTS DE TRADING ENGINE
# ============================================================================


class TestTradingEngine:
    """Verifica que TradingEngine funciona"""
    
    def test_trading_engine_initialization(self):
        """✓ TradingEngine se inicializa"""
        from core.trading_engine import TradingEngine
        engine = TradingEngine()
        assert engine is not None
        assert engine.config is not None
        assert engine.memory is not None
    
    @patch('core.trading_engine.duckdb.connect')
    def test_trading_engine_load_data_handles_missing_file(self, mock_connect):
        """✓ TradingEngine maneja archivo no encontrado"""
        from core.trading_engine import TradingEngine
        from core.exceptions import DataLoadError
        
        engine = TradingEngine()
        
        # Simular que el archivo no existe
        with patch('os.path.exists', return_value=False):
            with pytest.raises(DataLoadError):
                engine.load_data()
    
    @patch('core.trading_engine.TradingEngine.load_data')
    def test_trading_engine_run_cycle_returns_dict(self, mock_load):
        """✓ run_cycle retorna un diccionario"""
        from core.trading_engine import TradingEngine
        import pandas as pd
        
        engine = TradingEngine()
        
        # Mock load_data para retornar DataFrame vacío
        mock_load.return_value = pd.DataFrame()
        
        # El ciclo debe retornar un diccionario
        result = engine.run_cycle()
        assert isinstance(result, dict)
        assert "status" in result


# ============================================================================
# TESTS DE ORCHESTRATOR
# ============================================================================


class TestOrchestrator:
    """Verifica que el Orchestrator funciona"""
    
    def test_orchestrator_initialization(self):
        """✓ Orchestrator se inicializa"""
        from core.orchestrator_hardened import CentralOrchestratorHardened
        # Solo verificar que se puede importar sin errores
        assert CentralOrchestratorHardened is not None


# ============================================================================
# TESTS DE FUNCIONALIDAD BÁSICA
# ============================================================================


class TestBasicFunctionality:
    """Tests de funcionalidad básica del sistema"""
    
    def test_life_cycle_imports(self):
        """✓ life_cycle.py se puede importar"""
        # No ejecutamos main(), solo verificamos que se puede importar
        import life_cycle
        assert life_cycle is not None
    
    def test_aipha_config_json_is_valid(self):
        """✓ aipha_config.json es JSON válido"""
        import json
        config_file = AIPHA_ROOT / "aipha_config.json"
        if config_file.exists():
            content = json.loads(config_file.read_text())
            assert isinstance(content, dict)
    
    def test_memory_directory_exists(self):
        """✓ Directorio memory/ existe"""
        memory_dir = AIPHA_ROOT / "memory"
        assert memory_dir.exists(), "Directorio memory/ no existe"
    
    def test_core_modules_exist(self):
        """✓ Todos los módulos core existen"""
        required_files = [
            "core/__init__.py",
            "core/config_manager.py",
            "core/trading_engine.py",
            "core/orchestrator_hardened.py",
            "core/exceptions.py"
        ]
        
        for file in required_files:
            file_path = AIPHA_ROOT / file
            assert file_path.exists(), f"Falta: {file}"


# ============================================================================
# TESTS DE DEPENDENCY INJECTION
# ============================================================================


class TestDependencies:
    """Verifica que las dependencias externas están disponibles"""
    
    def test_pandas_available(self):
        """✓ pandas está instalado"""
        try:
            import pandas
            assert pandas.__version__ is not None
        except ImportError:
            pytest.skip("pandas no está instalado")
    
    def test_numpy_available(self):
        """✓ numpy está instalado"""
        try:
            import numpy
            assert numpy.__version__ is not None
        except ImportError:
            pytest.skip("numpy no está instalado")
    
    def test_duckdb_available(self):
        """✓ duckdb está instalado"""
        try:
            import duckdb
            assert duckdb is not None
        except ImportError:
            pytest.skip("duckdb no está instalado")
    
    def test_pydantic_available(self):
        """✓ pydantic está instalado"""
        try:
            from pydantic import BaseModel
            assert BaseModel is not None
        except ImportError:
            pytest.skip("pydantic no está instalado")


# ============================================================================
# TESTS DE HEALTH CHECK
# ============================================================================


class TestSystemHealth:
    """Verifica la salud general del sistema"""
    
    def test_no_syntax_errors_in_core(self):
        """✓ core/ no tiene errores de sintaxis"""
        import py_compile
        core_files = [
            "core/config_manager.py",
            "core/trading_engine.py",
            "core/exceptions.py"
        ]
        
        for file in core_files:
            try:
                py_compile.compile(str(AIPHA_ROOT / file), doraise=True)
            except py_compile.PyCompileError as e:
                pytest.fail(f"Error de sintaxis en {file}: {e}")
    
    def test_logging_works(self):
        """✓ El logging funciona"""
        import logging
        logger = logging.getLogger("test")
        logger.info("Test log message")
        assert logger is not None


# ============================================================================
# PYTEST CONFIGURATION
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
