"""
Tests para el GitAutomator de Code Craft Sage - Fase 4.

Este archivo contiene tests unitarios para verificar que el GitAutomator
funciona correctamente y cumple con los requisitos de seguridad.

NOTA: Estos tests usan repositorios Git temporales para no afectar
el repositorio principal del proyecto.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import git

from cgalpha.codecraft.git_automator import (
    GitAutomator,
    GitAutomatorError,
    create_feature_branch_and_commit
)
from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType


@pytest.fixture
def temp_repo():
    """
    Fixture que crea un repositorio Git temporal para los tests.
    
    Returns:
        Tuple (temp_dir, repo_path)
    """
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp(prefix="codecraft_test_")
    
    # Inicializar repositorio Git
    repo = git.Repo.init(temp_dir)
    
    # Crear un archivo de ejemplo
    example_file = Path(temp_dir) / "example.py"
    example_file.write_text("""
class ExampleClass:
    def __init__(self):
        self.threshold = 0.3
""")
    
    # Hacer commit inicial
    repo.index.add(["example.py"])
    repo.index.commit("Initial commit")
    
    yield temp_dir, temp_dir
    
    # Limpiar después del test
    shutil.rmtree(temp_dir)


class TestGitAutomatorInitialization:
    """Tests para la inicialización del GitAutomator."""
    
    def test_initialization_valid_repo(self, temp_repo):
        """Verifica que el GitAutomator se inicializa correctamente con un repo válido."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        assert automator.repo_path == Path(repo_path).resolve()
        assert automator.repo is not None
        assert not automator.repo.bare
    
    def test_initialization_invalid_repo(self):
        """Verifica que se lanza error con un directorio que no es un repo Git."""
        with pytest.raises(GitAutomatorError) as exc_info:
            GitAutomator("/nonexistent/path")
        
        assert "no es un repositorio Git válido" in str(exc_info.value)
    
    def test_initialization_bare_repo(self):
        """Verifica que se lanza error con un repositorio bare."""
        temp_dir = tempfile.mkdtemp(prefix="codecraft_bare_")
        
        try:
            # Crear repo bare
            git.Repo.init(temp_dir, bare=True)
            
            with pytest.raises(GitAutomatorError) as exc_info:
                GitAutomator(temp_dir)
            
            assert "es un repositorio bare" in str(exc_info.value)
        finally:
            shutil.rmtree(temp_dir)


class TestGitAutomatorStatus:
    """Tests para los métodos de estado del GitAutomator."""
    
    def test_get_status_clean_repo(self, temp_repo):
        """Verifica que get_status retorna el estado correcto de un repo limpio."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        status = automator.get_status()
        
        assert status["current_branch"] == "master" or status["current_branch"] == "main"
        assert status["is_detached"] is False
        assert status["has_uncommitted_changes"] is False
        assert status["is_clean"] is True
        assert status["repo_path"] == repo_path
    
    def test_get_status_dirty_repo(self, temp_repo):
        """Verifica que get_status detecta cambios pendientes."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        status = automator.get_status()
        
        assert status["has_uncommitted_changes"] is True
        assert status["is_clean"] is False
        assert len(status["modified_files"]) > 0
    
    def test_get_status_untracked_files(self, temp_repo):
        """Verifica que get_status detecta archivos no rastreados."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Crear archivo nuevo
        new_file = Path(temp_dir) / "new_file.py"
        new_file.write_text("new content")
        
        status = automator.get_status()
        
        assert status["has_uncommitted_changes"] is True
        assert len(status["untracked_files"]) > 0
        assert "new_file.py" in status["untracked_files"]
    
    def test_has_uncommitted_changes_clean(self, temp_repo):
        """Verifica has_uncommitted_changes en repo limpio."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        assert automator.has_uncommitted_changes() is False
    
    def test_has_uncommitted_changes_dirty(self, temp_repo):
        """Verifica has_uncommitted_changes en repo sucio."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        assert automator.has_uncommitted_changes() is True


class TestGitAutomatorFeatureBranch:
    """Tests para la creación de ramas de feature."""
    
    def test_create_feature_branch_success(self, temp_repo):
        """Verifica la creación exitosa de una rama de feature."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        branch_name = automator.create_feature_branch("prop_001")
        
        assert branch_name == "feature/prop_prop_001"
        assert automator.get_current_branch() == "feature/prop_prop_001"
    
    def test_create_feature_branch_already_exists(self, temp_repo):
        """Verifica que se hace checkout a la rama si ya existe."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Crear rama la primera vez
        branch_name1 = automator.create_feature_branch("prop_001")
        
        # Volver a master
        automator.repo.git.checkout("master")
        
        # Crear rama la segunda vez (debe hacer checkout)
        branch_name2 = automator.create_feature_branch("prop_001")
        
        assert branch_name1 == branch_name2
        assert automator.get_current_branch() == "feature/prop_prop_001"
    
    def test_create_feature_branch_protected_branch(self, temp_repo):
        """Verifica que NO se puede crear feature branch desde rama protegida."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Cambiar a main (rama protegida)
        automator.repo.git.checkout("main")
        
        with pytest.raises(GitAutomatorError) as exc_info:
            automator.create_feature_branch("prop_001")
        
        assert "rama protegida" in str(exc_info.value).lower()
    
    def test_create_feature_branch_with_uncommitted_changes(self, temp_repo):
        """Verifica que NO se puede crear rama con cambios pendientes."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Modificar archivo sin commitear
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        with pytest.raises(GitAutomatorError) as exc_info:
            automator.create_feature_branch("prop_001")
        
        assert "cambios pendientes" in str(exc_info.value).lower()


class TestGitAutomatorCommit:
    """Tests para la funcionalidad de commit."""
    
    def test_commit_changes_success(self, temp_repo):
        """Verifica el commit exitoso de cambios."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Crear rama de feature
        automator.create_feature_branch("prop_001")
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        # Crear spec
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py",
            class_name="ExampleClass",
            attribute_name="threshold",
            old_value=0.3,
            new_value=0.5,
            data_type="float"
        )
        
        # Hacer commit
        commit_hash = automator.commit_changes(spec, ["example.py"])
        
        assert len(commit_hash) == 40  # Hash SHA-1
        assert not automator.has_uncommitted_changes()
    
    def test_commit_changes_protected_branch(self, temp_repo):
        """Verifica que NO se puede hacer commit en rama protegida."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py"
        )
        
        with pytest.raises(GitAutomatorError) as exc_info:
            automator.commit_changes(spec, ["example.py"])
        
        assert "rama protegida" in str(exc_info.value).lower()
    
    def test_commit_changes_empty_files(self, temp_repo):
        """Verifica que NO se puede hacer commit sin archivos."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Crear rama de feature
        automator.create_feature_branch("prop_001")
        
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py"
        )
        
        with pytest.raises(GitAutomatorError) as exc_info:
            automator.commit_changes(spec, [])
        
        assert "archivos para commitear" in str(exc_info.value).lower()
    
    def test_commit_changes_nonexistent_file(self, temp_repo):
        """Verifica que NO se puede hacer commit con archivo inexistente."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Crear rama de feature
        automator.create_feature_branch("prop_001")
        
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py"
        )
        
        with pytest.raises(GitAutomatorError) as exc_info:
            automator.commit_changes(spec, ["nonexistent.py"])
        
        assert "no existe" in str(exc_info.value).lower()
    
    def test_commit_message_format(self, temp_repo):
        """Verifica el formato del mensaje de commit."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Crear rama de feature
        automator.create_feature_branch("prop_001")
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py",
            class_name="ExampleClass",
            attribute_name="threshold",
            old_value=0.3,
            new_value=0.5,
            data_type="float",
            source_proposal="Update threshold to 0.5"
        )
        
        # Hacer commit
        commit_hash = automator.commit_changes(spec, ["example.py"])
        
        # Obtener info del commit
        commit_info = automator.get_commit_info(commit_hash)
        
        # Verificar formato del mensaje
        message = commit_info["message"]
        assert "feat:" in message  # Conventional Commit type
        assert "CodeCraft Sage" in message
        assert "prop_001" in message
        assert "example.py" in message
        assert "ExampleClass" in message
        assert "threshold" in message


class TestGitAutomatorCommitMessageGeneration:
    """Tests para la generación de mensajes de commit."""
    
    def test_get_commit_type_parameter_change(self):
        """Verifica el tipo de commit para PARAMETER_CHANGE."""
        automator = GitAutomator.__new__(GitAutomator)
        commit_type = automator._get_commit_type(ChangeType.PARAMETER_CHANGE)
        assert commit_type == "feat"
    
    def test_get_commit_type_method_addition(self):
        """Verifica el tipo de commit para METHOD_ADDITION."""
        automator = GitAutomator.__new__(GitAutomator)
        commit_type = automator._get_commit_type(ChangeType.METHOD_ADDITION)
        assert commit_type == "feat"
    
    def test_get_commit_type_class_modification(self):
        """Verifica el tipo de commit para CLASS_MODIFICATION."""
        automator = GitAutomator.__new__(GitAutomator)
        commit_type = automator._get_commit_type(ChangeType.CLASS_MODIFICATION)
        assert commit_type == "refactor"
    
    def test_get_commit_type_config_update(self):
        """Verifica el tipo de commit para CONFIG_UPDATE."""
        automator = GitAutomator.__new__(GitAutomator)
        commit_type = automator._get_commit_type(ChangeType.CONFIG_UPDATE)
        assert commit_type == "chore"
    
    def test_get_commit_type_docstring_update(self):
        """Verifica el tipo de commit para DOCSTRING_UPDATE."""
        automator = GitAutomator.__new__(GitAutomator)
        commit_type = automator._get_commit_type(ChangeType.DOCSTRING_UPDATE)
        assert commit_type == "docs"
    
    def test_generate_commit_description_attribute(self):
        """Verifica la descripción para cambios de atributo."""
        automator = GitAutomator.__new__(GitAutomator)
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            attribute_name="threshold",
            new_value=0.5
        )
        description = automator._generate_commit_description(spec)
        assert "threshold" in description
        assert "0.5" in description
    
    def test_generate_commit_description_method(self):
        """Verifica la descripción para adición de método."""
        automator = GitAutomator.__new__(GitAutomator)
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.METHOD_ADDITION,
            method_name="new_method"
        )
        description = automator._generate_commit_description(spec)
        assert "new_method" in description


class TestGitAutomatorUtilityMethods:
    """Tests para métodos utilitarios del GitAutomator."""
    
    def test_get_current_branch(self, temp_repo):
        """Verifica que get_current_branch retorna la rama correcta."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        branch = automator.get_current_branch()
        assert branch in ["master", "main"]
    
    def test_is_protected_branch(self):
        """Verifica la detección de ramas protegidas."""
        automator = GitAutomator.__new__(GitAutomator)
        
        assert automator.is_protected_branch("main") is True
        assert automator.is_protected_branch("master") is True
        assert automator.is_protected_branch("develop") is True
        assert automator.is_protected_branch("staging") is True
        assert automator.is_protected_branch("production") is True
        assert automator.is_protected_branch("feature/prop_001") is False
    
    def test_get_commit_info(self, temp_repo):
        """Verifica la obtención de información de un commit."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Obtener el commit inicial
        commits = list(automator.repo.iter_commits(max_count=1))
        initial_commit_hash = commits[0].hexsha
        
        commit_info = automator.get_commit_info(initial_commit_hash)
        
        assert commit_info["hash"] == initial_commit_hash
        assert "author" in commit_info
        assert "message" in commit_info
        assert "date" in commit_info
    
    def test_get_recent_commits(self, temp_repo):
        """Verifica la obtención de commits recientes."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        commits = automator.get_recent_commits(limit=5)
        
        assert len(commits) == 1  # Solo el commit inicial
        assert "hash" in commits[0]
        assert "author" in commits[0]
        assert "message" in commits[0]
        assert "date" in commits[0]


class TestGitAutomatorSecurity:
    """Tests para verificar los requisitos de seguridad."""
    
    def test_no_push_automated(self, temp_repo):
        """Verifica que NO hay método de push automático."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Verificar que no existe método push
        assert not hasattr(automator, 'push')
        assert not hasattr(automator, 'push_to_remote')
    
    def test_protected_branches_constant(self):
        """Verifica que las ramas protegidas están definidas."""
        assert "main" in GitAutomator.PROTECTED_BRANCHES
        assert "master" in GitAutomator.PROTECTED_BRANCHES
        assert "develop" in GitAutomator.PROTECTED_BRANCHES
    
    def test_commit_in_protected_branch_raises_error(self, temp_repo):
        """Verifica que commit en rama protegida lanza error."""
        temp_dir, repo_path = temp_repo
        automator = GitAutomator(repo_path)
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py"
        )
        
        # Intentar commit en main/master
        with pytest.raises(GitAutomatorError) as exc_info:
            automator.commit_changes(spec, ["example.py"])
        
        assert "rama protegida" in str(exc_info.value).lower()


class TestConvenienceFunction:
    """Tests para la función de conveniencia create_feature_branch_and_commit."""
    
    def test_convenience_function_success(self, temp_repo):
        """Verifica que la función de conveniencia funciona correctamente."""
        temp_dir, repo_path = temp_repo
        
        # Modificar archivo
        example_file = Path(temp_dir) / "example.py"
        example_file.write_text("modified content")
        
        spec = TechnicalSpec(
            proposal_id="prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="example.py",
            class_name="ExampleClass",
            attribute_name="threshold",
            old_value=0.3,
            new_value=0.5,
            data_type="float"
        )
        
        branch_name, commit_hash = create_feature_branch_and_commit(
            spec, ["example.py"], repo_path
        )
        
        assert branch_name == "feature/prop_prop_001"
        assert len(commit_hash) == 40
