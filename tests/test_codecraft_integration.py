"""
Integration Tests para Code Craft Sage - Fase 5.

Este archivo contiene tests de extremo a extremo para verificar que
el pipeline completo funciona correctamente.

NOTA: Estos tests usan repositorios Git temporales para no afectar
el repositorio principal del proyecto.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import git

from cgalpha.codecraft.orchestrator import CodeCraftOrchestrator, execute_pipeline


@pytest.fixture
def temp_repo():
    """
    Fixture que crea un repositorio Git temporal para los tests.
    
    Returns:
        Tuple (temp_dir, repo_path)
    """
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp(prefix="codecraft_integration_test_")
    
    # Inicializar repositorio Git
    repo = git.Repo.init(temp_dir)
    
    # Crear un archivo de ejemplo
    example_file = Path(temp_dir) / "example_module.py"
    example_file.write_text("""
class ExampleClass:
    \"\"\"Example class for Code Craft Sage integration tests.\"\"\"
    
    def __init__(self):
        self.threshold = 0.3
        self.confidence = 0.5
    
    def process(self, data):
        \"\"\"Process data with current threshold.\"\"\"
        return data * self.threshold
""")
    
    # Crear directorio tests
    tests_dir = Path(temp_dir) / "tests"
    tests_dir.mkdir(exist_ok=True)
    
    # Crear archivo __init__.py
    (tests_dir / "__init__.py").write_text("")
    
    # Hacer commit inicial
    repo.index.add(["example_module.py", "tests/__init__.py"])
    repo.index.commit("Initial commit: Add example module")
    
    yield temp_dir, temp_dir
    
    # Limpiar después del test
    shutil.rmtree(temp_dir)


class TestCodeCraftOrchestratorIntegration:
    """Tests de integración para el CodeCraftOrchestrator."""
    
    def test_execute_pipeline_success(self, temp_repo):
        """Verifica la ejecución exitosa del pipeline completo."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update the threshold parameter in ExampleClass from 0.3 to 0.65"
        
        # Ejecutar pipeline
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar resultado
        assert result["status"] == "success"
        assert result["branch_name"].startswith("feature/prop_")
        assert result["commit_hash"] is not None
        assert len(result["commit_hash"]) == 40
        
        # Verificar historial del pipeline
        pipeline_history = result.get("pipeline_history", [])
        assert len(pipeline_history) == 4  # 4 fases
        
        # Cada fase debe haber sido exitosa
        for phase_info in pipeline_history:
            assert phase_info.get("status") == "success"
    
    def test_execute_pipeline_timing(self, temp_repo):
        """Verifica que el timing de cada fase se registra correctamente."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        timing = result.get("timing", {})
        
        # Verificar que cada fase tiene timing
        assert "phase1_parsing" in timing
        assert "phase2_modification" in timing
        assert "phase3_validation" in timing
        assert "phase4_git" in timing
        
        # Verificar que los tiempos son positivos
        for phase_time in timing.values():
            assert phase_time >= 0
    
    def test_execute_pipeline_proposal_id(self, temp_repo):
        """Verifica que se puede especificar un proposal_id."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        custom_id = "custom_test_id"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text, proposal_id=custom_id)
        
        # Verificar que se usó el ID personalizado
        assert result["proposal_id"] == custom_id
        assert result["branch_name"] == f"feature/prop_{custom_id}"
    
    def test_execute_pipeline_no_rollback_on_success(self, temp_repo):
        """Verifica que no se hace rollback si el pipeline tiene éxito."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar que no se hizo rollback
        changes = result.get("changes_summary", {})
        assert changes.get("rollback_performed") is False
    
    def test_convenience_function(self, temp_repo):
        """Verifica la función de conveniencia execute_pipeline."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        result = execute_pipeline(proposal_text, working_dir=repo_path)
        
        assert result["status"] == "success"
        assert result["branch_name"] is not None
    
    def test_get_status(self, temp_repo):
        """Verifica el método get_status del orchestrator."""
        temp_dir, repo_path = temp_repo
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        status = orchestrator.get_status()
        
        # Verificar estructura del estado
        assert "status" in status
        assert "working_dir" in status
        assert "git_status" in status
        assert "components" in status
        
        # Verificar componentes
        components = status.get("components", {})
        assert components.get("parser") == "ready"
        assert components.get("modifier") == "ready"
        assert components.get("test_generator") == "ready"
        assert components.get("git_automator") == "ready"
    
    def test_backup_creation(self, temp_repo):
        """Verifica que se crea un backup antes de modificar."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar historial de fase 2 (modificación)
        pipeline_history = result.get("pipeline_history", [])
        phase2_info = pipeline_history[1]  # Fase 2
        
        assert phase2_info.get("phase") == 2
        assert "backup_path" in phase2_info.get("details", {})
    
    def test_pipeline_creates_git_commit(self, temp_repo):
        """Verifica que el pipeline crea un commit Git."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar que se creó un commit
        assert result.get("commit_hash") is not None
        
        # Verificar que el commit existe en el repo
        repo = git.Repo(repo_path)
        commit = repo.commit(result["commit_hash"])
        assert commit is not None
        
        # Verificar mensaje del commit
        assert "CodeCraft Sage" in commit.message
        assert "feat:" in commit.message
    
    def test_pipeline_creates_feature_branch(self, temp_repo):
        """Verifica que el pipeline crea una rama de feature."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar nombre de rama
        branch_name = result.get("branch_name")
        assert branch_name is not None
        assert branch_name.startswith("feature/prop_")
        
        # Verificar que la rama existe
        repo = git.Repo(repo_path)
        branches = [b.name for b in repo.branches]
        assert branch_name in branches
    
    def test_pipeline_generates_test(self, temp_repo):
        """Verifica que el pipeline genera un test."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = "Update threshold to 0.5"
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar resultado de tests
        test_results = result.get("test_results", {})
        assert test_results.get("new_test_status") == "passed"
        assert test_results.get("new_test_path") is not None


class TestCodeCraftOrchestratorErrors:
    """Tests para manejo de errores del Orchestrator."""
    
    def test_invalid_proposal(self, temp_repo):
        """Verifica manejo de propuesta inválida."""
        temp_dir, repo_path = temp_repo
        
        proposal_text = ""  # Propuesta vacía
        
        orchestrator = CodeCraftOrchestrator(working_dir=repo_path)
        result = orchestrator.execute_pipeline(proposal_text)
        
        # Verificar que el pipeline falló
        assert result["status"] == "failed"
        
        # Verificar que hay errores
        errors = result.get("errors", [])
        assert len(errors) > 0


class TestCodeCraftOrchestratorCLI:
    """Tests para verificar integración con CLI."""
    
    def test_cli_command_registered(self):
        """Verifica que el comando CLI está registrado."""
        from aiphalab.commands import codecraft_group
        
        assert codecraft_group is not None
        assert hasattr(codecraft_group, 'commands')
    
    def test_apply_command_exists(self):
        """Verifica que el comando apply existe."""
        from aiphalab.commands.codecraft import apply
        
        assert apply is not None
        assert callable(apply)
    
    def test_status_command_exists(self):
        """Verifica que el comando status existe."""
        from aiphalab.commands.codecraft import status
        
        assert status is not None
        assert callable(status)
