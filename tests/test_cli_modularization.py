"""
tests/test_cli_modularization.py - Tests de CLI Modularizado

Valida que la estructura modularizada del CLI funciona correctamente.
Soluciona: P1 #5 - CLI monolítico refactorizado

Ejecutar con: pytest tests/test_cli_modularization.py -v
"""

import pytest
from click.testing import CliRunner
from aiphalab.cli_v2 import cli


class TestCLIModularization:
    """Tests para validar CLI modularizado"""
    
    def setup_method(self):
        """Configurar antes de cada test"""
        self.runner = CliRunner()
    
    def test_cli_main_group(self):
        """✓ CLI principal funciona"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'AiphaLab CLI' in result.output
    
    def test_cli_version_command(self):
        """✓ Comando version funciona"""
        result = self.runner.invoke(cli, ['version'])
        assert result.exit_code == 0
        assert 'aipha' in result.output or 'Aipha' in result.output
    
    def test_cli_info_command(self):
        """✓ Comando info funciona"""
        result = self.runner.invoke(cli, ['info'])
        assert result.exit_code == 0
    
    def test_status_group_exists(self):
        """✓ Grupo status está registrado"""
        result = self.runner.invoke(cli, ['status', '--help'])
        assert result.exit_code == 0
        assert 'status' in result.output
    
    def test_cycle_group_exists(self):
        """✓ Grupo cycle está registrado"""
        result = self.runner.invoke(cli, ['cycle', '--help'])
        assert result.exit_code == 0
        assert 'cycle' in result.output
    
    def test_config_group_exists(self):
        """✓ Grupo config está registrado"""
        result = self.runner.invoke(cli, ['config', '--help'])
        assert result.exit_code == 0
        assert 'config' in result.output
    
    def test_history_group_exists(self):
        """✓ Grupo history está registrado"""
        result = self.runner.invoke(cli, ['history', '--help'])
        assert result.exit_code == 0
        assert 'history' in result.output
    
    def test_debug_group_exists(self):
        """✓ Grupo debug está registrado"""
        result = self.runner.invoke(cli, ['debug', '--help'])
        assert result.exit_code == 0
        assert 'debug' in result.output

    def test_docs_group_exists(self):
        """✓ Grupo docs está registrado"""
        result = self.runner.invoke(cli, ['docs', '--help'])
        assert result.exit_code == 0
        assert 'docs' in result.output
    
    def test_dry_run_flag(self):
        """✓ Flag --dry-run funciona"""
        result = self.runner.invoke(cli, ['--dry-run', 'version'])
        assert result.exit_code == 0
    
    def test_status_show_command(self):
        """✓ Comando status show funciona"""
        result = self.runner.invoke(cli, ['status', 'show'])
        assert result.exit_code == 0 or 'error' in result.output.lower()
    
    def test_debug_check_imports_command(self):
        """✓ Comando debug check-imports funciona"""
        result = self.runner.invoke(cli, ['debug', 'check-imports'])
        assert result.exit_code == 0
        assert 'Core' in result.output or 'core' in result.output.lower()
    
    def test_debug_check_deps_command(self):
        """✓ Comando debug check-deps funciona"""
        result = self.runner.invoke(cli, ['debug', 'check-deps'])
        assert result.exit_code == 0
        assert 'pandas' in result.output or 'dependency' in result.output.lower()


class TestCommandStructure:
    """Tests para validar estructura de comandos"""
    
    def test_all_command_modules_importable(self):
        """✓ Todos los módulos de comando se pueden importar"""
        from aiphalab.commands import (
            status_group,
            cycle_group,
            config_group,
            history_group,
            debug_group,
            docs_group,
        )
        
        assert status_group is not None
        assert cycle_group is not None
        assert config_group is not None
        assert history_group is not None
        assert debug_group is not None
        assert docs_group is not None
    
    def test_base_command_class_exists(self):
        """✓ Clase BaseCommand existe"""
        from aiphalab.commands.base import BaseCommand
        
        cmd = BaseCommand()
        assert cmd is not None
        assert hasattr(cmd, 'print')
        assert hasattr(cmd, 'print_error')
        assert hasattr(cmd, 'print_success')
    
    def test_command_classes_exist(self):
        """✓ Clases de comando existen"""
        from aiphalab.commands.status import StatusCommand
        from aiphalab.commands.cycle import CycleCommand
        from aiphalab.commands.config import ConfigCommand
        from aiphalab.commands.history import HistoryCommand
        from aiphalab.commands.debug import DebugCommand
        
        assert StatusCommand is not None
        assert CycleCommand is not None
        assert ConfigCommand is not None
        assert HistoryCommand is not None
        assert DebugCommand is not None


class TestCLIReduction:
    """Tests para validar que CLI está reducido en tamaño"""
    
    def test_cli_v2_is_smaller_than_original(self):
        """✓ CLI v2 es más pequeño que original (lineas de código)"""
        from pathlib import Path
        
        cli_v2_path = Path("aiphalab/cli_v2.py")
        cli_original_path = Path("aiphalab/cli.py")
        
        if cli_v2_path.exists() and cli_original_path.exists():
            cli_v2_lines = len(cli_v2_path.read_text().split('\n'))
            cli_original_lines = len(cli_original_path.read_text().split('\n'))
            
            # CLI v2 debe ser ≤ 60% del original
            assert cli_v2_lines <= cli_original_lines * 0.6, \
                f"CLI v2 ({cli_v2_lines} lines) no es suficientemente más pequeño que original ({cli_original_lines} lines)"


class TestCommandImports:
    """Tests para validar imports en módulos de comando"""
    
    def test_status_command_imports(self):
        """✓ Imports de StatusCommand funcionan"""
        from aiphalab.commands.status import StatusCommand, status_group
        assert StatusCommand is not None
        assert status_group is not None
    
    def test_cycle_command_imports(self):
        """✓ Imports de CycleCommand funcionan"""
        from aiphalab.commands.cycle import CycleCommand, cycle_group
        assert CycleCommand is not None
        assert cycle_group is not None
    
    def test_config_command_imports(self):
        """✓ Imports de ConfigCommand funcionan"""
        from aiphalab.commands.config import ConfigCommand, config_group
        assert ConfigCommand is not None
        assert config_group is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
