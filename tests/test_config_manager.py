"""Tests para Config Manager con soporte de Rollback."""

import pytest
import sys
import os
import tempfile
import json
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.config_manager import ConfigManager

@pytest.fixture
def config_manager():
    """Crea un ConfigManager con almacenamiento temporal."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        manager = ConfigManager(config_path=config_path)
        yield manager

class TestConfigManagerRollback:
    
    def test_backup_creation_on_save(self, config_manager):
        """Verifica que se crea un backup al guardar cambios."""
        # Primer guardado (automático en init)
        assert config_manager.config_path.exists()
        
        # Segundo guardado
        config_manager.set("Trading.tp_factor", 3.0)
        
        backup_dir = config_manager.config_path.parent / "backups"
        assert backup_dir.exists()
        backups = list(backup_dir.glob("config_backup_*.json"))
        assert len(backups) >= 1

    def test_rollback_to_previous_state(self, config_manager):
        """Prueba que el rollback restaura el valor anterior."""
        original_val = config_manager.get("Trading.tp_factor")
        
        # Cambiar valor (esto crea backup del original)
        config_manager.set("Trading.tp_factor", 5.0)
        assert config_manager.get("Trading.tp_factor") == 5.0
        
        # Hacer rollback
        success = config_manager.rollback()
        assert success is True
        assert config_manager.get("Trading.tp_factor") == original_val

    def test_rollback_no_backups(self):
        """Verifica comportamiento cuando no hay backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "no_backups.json"
            manager = ConfigManager(config_path=config_path)
            # No hacemos ningún set(), por lo que no hay backups
            success = manager.rollback()
            assert success is False
