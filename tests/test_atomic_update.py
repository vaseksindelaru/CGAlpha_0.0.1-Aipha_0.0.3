import pytest
import tempfile
import shutil
from pathlib import Path
from core.context_sentinel import ContextSentinel
from core.atomic_update_system import AtomicUpdateSystem, ChangeProposal, ApprovalStatus

class TestAtomicUpdate:
    @pytest.fixture
    def sentinel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ContextSentinel(Path(tmpdir))

    @pytest.fixture
    def dummy_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("class Dummy:\n    def __init__(self):\n        self.value = 1\n")
            path = Path(f.name)
        yield path
        if path.exists():
            path.unlink()
        bak = path.with_suffix(".py.bak")
        if bak.exists():
            bak.unlink()

    @pytest.fixture
    def dummy_test(self):
        with tempfile.NamedTemporaryFile(suffix="_test.py", mode="w", delete=False) as f:
            f.write("def test_dummy():\n    from sys import path\n    import os\n    # Este test pasará si el archivo existe\n    assert True\n")
            path = Path(f.name)
        yield path
        if path.exists():
            path.unlink()

    def test_successful_update(self, sentinel, dummy_file, dummy_test):
        atomic = AtomicUpdateSystem(sentinel)
        
        # Crear propuesta
        proposal = ChangeProposal(
            proposal_id="TEST-001",
            title="Update Dummy",
            target_component=str(dummy_file.with_suffix("")).replace("/", "."),
            impact_justification="Test",
            estimated_difficulty="Low",
            diff_content="+         self.new_value = 2\n-         self.value = 1",
            test_plan=f"pytest {dummy_test}",
            metrics={},
            status=ApprovalStatus.APPROVED
        )
        
        # El componente target_component debe ser relativo o manejable. 
        # En el sistema real es core.something. Aquí usamos el path absoluto transformado.
        # Ajustamos el target_path en el test para que apunte al dummy_file real.
        atomic.target_path = dummy_file 
        
        success, message = atomic.execute(proposal)
        
        assert success is True
        assert "completado" in message
        
        # Verificar contenido
        content = dummy_file.read_text()
        assert "self.new_value = 2" in content
        assert "self.value = 1" not in content
        
        # Verificar que el backup se borró
        assert not dummy_file.with_suffix(".py.bak").exists()
        
        # Verificar historial
        history = sentinel.get_action_history()
        assert any(h["action_type"] == "ATOMIC_COMMIT" for h in history)

    def test_rollback_on_failure(self, sentinel, dummy_file):
        atomic = AtomicUpdateSystem(sentinel)
        
        # Crear un test que falle
        with tempfile.NamedTemporaryFile(suffix="_fail_test.py", mode="w", delete=False) as f:
            f.write("def test_fail():\n    assert False\n")
            fail_test_path = Path(f.name)
            
        proposal = ChangeProposal(
            proposal_id="TEST-FAIL",
            title="Update Dummy Fail",
            target_component=str(dummy_file.with_suffix("")).replace("/", "."),
            impact_justification="Test",
            estimated_difficulty="Low",
            diff_content="+         self.broken = True",
            test_plan=f"pytest {fail_test_path}",
            metrics={}
        )
        
        atomic.target_path = dummy_file
        original_content = dummy_file.read_text()
        
        success, message = atomic.execute(proposal)
        
        assert success is False
        assert "fallido" in message
        
        # Verificar que el contenido se restauró
        assert dummy_file.read_text() == original_content
        
        # Verificar historial
        history = sentinel.get_action_history()
        assert any(h["action_type"] == "ATOMIC_ROLLBACK" for h in history)
        
        fail_test_path.unlink()

    def test_file_not_found(self, sentinel):
        atomic = AtomicUpdateSystem(sentinel)
        proposal = ChangeProposal(
            proposal_id="TEST-NOFILE",
            title="No File",
            target_component="non_existent",
            impact_justification="Test",
            estimated_difficulty="Low",
            diff_content="",
            test_plan="pytest",
            metrics={}
        )
        
        success, message = atomic.execute(proposal)
        assert success is False
        assert "No se encuentra" in message
