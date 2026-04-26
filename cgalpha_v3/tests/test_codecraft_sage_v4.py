
import os
import ast
import pytest
from pathlib import Path
from cgalpha_v3.lila.codecraft_sage import CodeCraftSage
from cgalpha_v3.lila.llm.proposer import TechnicalSpec

@pytest.fixture
def sage():
    from cgalpha_v3.domain.base_component import ComponentManifest
    manifest = ComponentManifest(name="TestSage", category="evolution", function="Test", inputs=[], outputs=[], causal_score=0.8)
    return CodeCraftSage(manifest)

def test_apply_ast_patch_simple_assignment(sage, tmp_path):
    target_file = tmp_path / "config.py"
    target_file.write_text("volume_threshold = 1.2\nother_val = 0.5 # preserve this\n")
    
    spec = TechnicalSpec(
        change_type="parameter",
        target_file=str(target_file),
        target_attribute="volume_threshold",
        old_value=1.2,
        new_value=1.5,
        reason="Test AST patch",
        causal_score_est=0.8,
        confidence=0.9
    )
    
    success = sage._apply_ast_patch(spec)
    assert success
    
    content = target_file.read_text()
    assert "volume_threshold = 1.5" in content
    assert "other_val = 0.5" in content

def test_apply_ast_patch_with_comment(sage, tmp_path):
    target_file = tmp_path / "config.py"
    target_file.write_text("volume_threshold = 1.2 # critical threshold\n")
    
    spec = TechnicalSpec(
        change_type="parameter",
        target_file=str(target_file),
        target_attribute="volume_threshold",
        old_value=1.2,
        new_value=1.8,
        reason="Test AST patch with comment",
        causal_score_est=0.8,
        confidence=0.9
    )
    
    success = sage._apply_ast_patch(spec)
    assert success
    
    content = target_file.read_text()
    assert "volume_threshold = 1.8 # critical threshold" in content

def test_apply_ast_patch_dict_key(sage, tmp_path):
    target_file = tmp_path / "config.py"
    target_file.write_text("CONFIG = {\n    'volume_threshold': 1.2,\n    'other': 5\n}\n")
    
    spec = TechnicalSpec(
        change_type="parameter",
        target_file=str(target_file),
        target_attribute="volume_threshold",
        old_value=1.2,
        new_value=2.0,
        reason="Test AST patch dict",
        causal_score_est=0.8,
        confidence=0.9
    )
    
    success = sage._apply_ast_patch(spec)
    assert success
    
    content = target_file.read_text()
    assert "'volume_threshold': 2.0," in content
    assert "'other': 5" in content

def test_apply_ast_patch_dict_key_with_comment(sage, tmp_path):
    target_file = tmp_path / "config.py"
    target_file.write_text("CONFIG = {\n    'volume_threshold': 1.2, # test comment\n    'other': 5\n}\n")
    
    spec = TechnicalSpec(
        change_type="parameter",
        target_file=str(target_file),
        target_attribute="volume_threshold",
        old_value=1.2,
        new_value=2.5,
        reason="Test AST patch dict comment",
        causal_score_est=0.8,
        confidence=0.9
    )
    
    success = sage._apply_ast_patch(spec)
    assert success
    
    content = target_file.read_text()
    assert "'volume_threshold': 2.5, # test comment" in content
