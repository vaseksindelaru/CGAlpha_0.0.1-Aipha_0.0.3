
import textwrap
import tempfile
import ast
import pytest
from pathlib import Path

from cgalpha_v3.lila.codecraft_sage import CodeCraftSage
from cgalpha_v3.lila.llm.proposer import TechnicalSpec
from cgalpha_v3.domain.base_component import ComponentManifest

# ── Fixtures ────────────────────────────────────────────────────────────────

SMALL_FILE = textwrap.dedent('''
    class Calculator:
        def add(self, a, b):
            return a + b  # old implementation

        def subtract(self, a, b):
            return a - b
''').strip()

LARGE_FILE_TEMPLATE = textwrap.dedent('''
    # Padding to simulate large file
    {padding}

    class Oracle:
        def predict(self, features):
            return 0.85  # placeholder

        def train(self, X, y):
            pass
''').strip()


@pytest.fixture
def make_sage():
    def _make():
        manifest = ComponentManifest(
            name="TestSage", 
            category="evolution", 
            function="Test", 
            inputs=[], 
            outputs=[], 
            causal_score=0.8
        )
        return CodeCraftSage(manifest)
    return _make


@pytest.fixture
def small_py_file(tmp_path):
    f = tmp_path / "calculator.py"
    f.write_text(SMALL_FILE)
    return f


@pytest.fixture
def large_py_file(tmp_path):
    # 500+ líneas de padding
    padding = "\n".join(f"# line {i}" for i in range(520))
    content = LARGE_FILE_TEMPLATE.format(padding=padding)
    f = tmp_path / "oracle.py"
    f.write_text(content)
    return f


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_spec(change_type, target_file, target_attribute,
              new_code=None, old_value=0.0, new_value=0.0):
    spec = TechnicalSpec(
        change_type=change_type,
        target_file=str(target_file),
        target_attribute=target_attribute,
        old_value=old_value,
        new_value=new_value,
        reason="test",
        causal_score_est=0.9,
        confidence=0.9,
        new_code=new_code,
    )
    return spec


# ── Tests de estrategia AST ──────────────────────────────────────────────────

def test_ast_patch_replaces_function_body(small_py_file, make_sage):
    """El Sage reemplaza el cuerpo completo de un FunctionDef."""
    new_code = textwrap.dedent('''
        def add(self, a, b):
            return a + b + 1  # v2: añade margen
    ''').strip()

    spec = make_spec(
        change_type="bugfix",
        target_file=small_py_file,
        target_attribute="add",
        new_code=new_code,
    )
    sage = make_sage()
    # En v4, _apply_ast_patch toma ruta y spec (o solo spec, verificaremos después)
    # El usuario sugirió _apply_ast_patch(self, file_path, spec)
    result = sage._apply_ast_patch(spec) # Mantenemos firma compatible con actual por ahora

    assert result is True
    content = small_py_file.read_text()
    assert "añade margen" in content
    assert "old implementation" not in content
    # El resto del archivo no se toca
    assert "def subtract" in content


def test_ast_patch_preserves_indentation(small_py_file, make_sage):
    """El reemplazo mantiene la indentación correcta."""
    new_code = "    def add(self, a, b):\n        return a + b + 1"
    spec = make_spec(
        change_type="bugfix",
        target_file=small_py_file,
        target_attribute="add",
        new_code=new_code,
    )
    sage = make_sage()
    sage._apply_ast_patch(spec)

    # El archivo debe ser sintácticamente válido después del patch
    try:
        ast.parse(small_py_file.read_text())
    except SyntaxError as e:
        pytest.fail(f"Archivo inválido después del patch: {e}")


def test_ast_patch_async_function(tmp_path, make_sage):
    """El Sage maneja AsyncFunctionDef correctamente."""
    content = textwrap.dedent('''
        async def fetch_data(url):
            return None  # old
    ''').strip()
    f = tmp_path / "fetcher.py"
    f.write_text(content)

    new_code = "async def fetch_data(url):\n    return await get(url)"
    spec = make_spec(
        change_type="bugfix",
        target_file=f,
        target_attribute="fetch_data",
        new_code=new_code,
    )
    sage = make_sage()
    result = sage._apply_ast_patch(spec)

    assert result is True
    assert "await get(url)" in f.read_text()


def test_ast_patch_large_file_only_touches_target(large_py_file, make_sage):
    """En un archivo de 500+ líneas, solo se modifica el método objetivo."""
    original_lines = large_py_file.read_text().splitlines()

    new_code = textwrap.dedent('''
        def predict(self, features):
            return self.model.predict(features)  # real prediction
    ''').strip()
    spec = make_spec(
        change_type="bugfix",
        target_file=large_py_file,
        target_attribute="predict",
        new_code=new_code,
    )
    sage = make_sage()
    result = sage._apply_ast_patch(spec)

    assert result is True
    new_content = large_py_file.read_text()
    assert "real prediction" in new_content
    assert "placeholder" not in new_content
    # El padding de 520 líneas debe seguir intacto
    assert "# line 519" in new_content


def test_ast_patch_returns_false_when_method_not_found(small_py_file, make_sage):
    """Si el método no existe, retorna False sin modificar el archivo."""
    original = small_py_file.read_text()
    spec = make_spec(
        change_type="bugfix",
        target_file=small_py_file,
        target_attribute="nonexistent_method",
        new_code="def nonexistent_method(): pass",
    )
    sage = make_sage()
    result = sage._apply_ast_patch(spec)

    assert result is False
    assert small_py_file.read_text() == original  # sin modificación


def test_ast_patch_returns_false_for_invalid_python(small_py_file, make_sage):
    """Si new_code tiene sintaxis inválida, retorna False sin modificar."""
    original = small_py_file.read_text()
    spec = make_spec(
        change_type="bugfix",
        target_file=small_py_file,
        target_attribute="add",
        new_code="def add(self SYNTAX ERROR",  # inválido
    )
    sage = make_sage()
    result = sage._apply_ast_patch(spec)

    assert result is False
    assert small_py_file.read_text() == original


# ── Tests de selección de estrategia ────────────────────────────────────────

def test_strategy_selection_bugfix_uses_ast(small_py_file, make_sage, monkeypatch):
    """change_type='bugfix' con new_code presente usa estrategia AST."""
    spec = make_spec(
        change_type="bugfix",
        target_file=small_py_file,
        target_attribute="add",
        new_code="def add(self, a, b):\n    return a + b",
    )
    sage = make_sage()
    
    calls = []
    # Usamos monkeypatch para trackear la llamada sin romper la lógica
    original_ast = sage._apply_ast_patch
    def mock_ast(s):
        calls.append("ast")
        return original_ast(s)
    
    monkeypatch.setattr(sage, "_apply_ast_patch", mock_ast)

    sage._apply_patch(spec)
    assert "ast" in calls


def test_strategy_selection_parameter_uses_strreplace(tmp_path, make_sage, monkeypatch):
    """change_type='parameter' usa str.replace, no AST (a menos que falle o se fuerce)."""
    # En v4, 'parameter' cae a la estrategia 2 (Regex/String replace)
    content = "volume_threshold = 1.2\n"
    f = tmp_path / "config.py"
    f.write_text(content)

    spec = make_spec(
        change_type="parameter",
        target_file=f,
        target_attribute="volume_threshold",
        old_value=1.2,
        new_value=1.5,
    )
    sage = make_sage()
    
    # Verificamos que se aplique el cambio (la estrategia interna _apply_patch lo maneja)
    sage._apply_patch(spec)

    assert "1.5" in f.read_text()
    assert "1.2" not in f.read_text()


# ── Tests de rollback ────────────────────────────────────────────────────────

def test_rollback_on_test_failure(small_py_file, make_sage, monkeypatch):
    """Si los tests fallan después del patch, el archivo se restaura."""
    original = small_py_file.read_text()
    
    # CodeCraft v3+ requiere un entorno GIT real para rollback y feature branches
    import subprocess
    cwd = str(small_py_file.parent)
    subprocess.run(["git", "init"], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=cwd, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=cwd, check=True)
    subprocess.run(["git", "add", "."], cwd=cwd, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=cwd, check=True, capture_output=True)

    sage = make_sage()
    # Cambiar root del sage al directorio temporal
    sage.project_root = cwd
    
    # Simular que los tests fallan
    monkeypatch.setattr(sage, "_run_test_barrier",
                        lambda tf: {"all_passed": False, "summary": "failure"})
    
    # Monkeypatch para que el rollback al directorio actual (main) funcione en el subproceso
    # Sin esto, intentaría cambiar a la rama actual en el repo global del usuario
    def mock_rollback():
        subprocess.run(["git", "checkout", "master"], cwd=cwd, check=False, capture_output=True)
        subprocess.run(["git", "stash", "pop"], cwd=cwd, check=False, capture_output=True) # Intento simple
        subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=cwd, check=False, capture_output=True)

    monkeypatch.setattr(sage, "_rollback_to_main", mock_rollback)
    
    # También pipear git commands del sage al cwd temporal
    original_setup = sage._setup_feature_branch
    monkeypatch.setattr(sage, "_setup_feature_branch", 
                        lambda b: subprocess.run(["git", "checkout", "-b", b], cwd=cwd, check=True, capture_output=True))

    spec = make_spec(
        change_type="bugfix",
        target_file=str(small_py_file), # Usar ruta absoluta
        target_attribute="add",
        new_code="def add(self, a, b):\n    return 999",
    )
    
    # execute_proposal debería hacer el rollback
    result = sage.execute_proposal(spec, ghost_approved=True, human_approved=True)

    # El archivo debe estar restaurado al original
    assert small_py_file.read_text() == original
    assert result.status == "REJECTED_NO_COMMIT"
