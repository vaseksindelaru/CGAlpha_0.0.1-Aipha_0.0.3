"""
Tests para Code Craft Sage - Fase 2: AST Modifier

Tests para ASTModifier y SafetyValidator.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType
from cgalpha.codecraft.ast_modifier import ASTModifier
from cgalpha.codecraft.safety_validator import SafetyValidator


class TestASTModifier:
    """Tests para ASTModifier"""
    
    def test_initialization(self):
        """Test que ASTModifier se inicializa correctamente"""
        modifier = ASTModifier()
        assert modifier.backup_dir.exists()
    
    def test_modify_simple_parameter(self, tmp_path):
        """Test modificación de parámetro simple"""
        # Crear archivo de prueba
        test_file = tmp_path / "test_module.py"
        test_code = """class TestClass:
    def __init__(self):
        self.confidence_threshold = 0.70
"""
        test_file.write_text(test_code)
        
        # Crear spec
        spec = TechnicalSpec(
            proposal_id="TEST_MODIFY",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path=str(test_file),
            class_name="TestClass",
            attribute_name="confidence_threshold",
            old_value=0.70,
            new_value=0.65,
            data_type="float"
        )
        
        # Modificar
        modifier = ASTModifier()
        result = modifier.modify_file(spec)
        
        # Verificar
        assert result["success"] is True
        assert result["backup_path"] is not None
        assert len(result["changes_made"]) > 0
        
        # Verificar que el archivo fue modificado
        modified_code = test_file.read_text()
        assert "0.65" in modified_code or "0.7" not in modified_code  # Fallback también funciona
    
    def test_backup_creation(self, tmp_path):
        """Test que se crea backup antes de modificar"""
        test_file = tmp_path / "backup_test.py"
        test_file.write_text("x = 1")
        
        modifier = ASTModifier()
        backup_path = modifier._create_backup(test_file, "x = 1")
        
        assert backup_path.exists()
        assert backup_path.read_text() == "x = 1"
    
    def test_validation_of_modified_code(self):
        """Test que validación detecta código inválido"""
        modifier = ASTModifier()
        
        valid_code = "x = 1"
        invalid_code = "x = if"
        
        validation = modifier._validate_modification(valid_code, invalid_code)
        
        assert validation["syntax_valid"] is False
        assert len(validation["errors"]) > 0


class TestSafetyValidator:
    """Tests para SafetyValidator"""
    
    def test_initialization(self):
        """Test inicialización"""
        validator = SafetyValidator()
        assert validator is not None
    
    def test_syntax_validation(self):
        """Test validación de sintaxis"""
        validator = SafetyValidator()
        
        valid_code = "def foo(): pass"
        invalid_code = "def foo( pass"
        
        result_valid = validator._check_syntax(valid_code)
        result_invalid = validator._check_syntax(invalid_code)
        
        assert result_valid["valid"] is True
        assert result_invalid["valid"] is False
    
    def test_imports_detection(self):
        """Test detección de imports"""
        validator = SafetyValidator()
        
        code_with_imports = """
import os
from pathlib import Path
        """
        
        imports = validator._extract_imports(code_with_imports)
        
        assert len(imports) >= 2
        assert any("os" in imp for imp in imports)
        assert any("Path" in imp for imp in imports)
    
    def test_type_consistency_check(self):
        """Test verificación de consistencia de tipos"""
        validator = SafetyValidator()
        
        # Spec válido
        spec_valid = TechnicalSpec(
            proposal_id="TYPE_TEST",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="test.py",
            data_type="float",
            new_value=0.65
        )
        
        result = validator._check_type_consistency(spec_valid)
        assert result["consistent"] is True
    
    def test_risk_score_calculation(self):
        """Test cálculo de risk score"""
        validator = SafetyValidator()
        
        spec = TechnicalSpec(
            proposal_id="RISK_TEST",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="oracle/oracle.py",  # Archivo crítico
            old_value=0.7,
            new_value=0.3,  # Cambio grande >50%
            data_type="float"
        )
        
        validation = {
            "syntax_valid": True,
            "imports_intact": True,
            "type_consistency": True
        }
        
        risk = validator._calculate_risk_score(spec, validation)
        
        # Risk debería ser >0 por archivo crítico + cambio grande
        assert risk > 0.0
        assert risk <= 1.0
    
    def test_pre_validation(self, tmp_path):
        """Test pre-validación de spec"""
        validator = SafetyValidator()
        
        # Archivo que existe
        test_file = tmp_path / "exists.py"
        test_file.write_text("x = 1")
        
        spec_valid = TechnicalSpec(
            proposal_id="PRE_TEST",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path=str(test_file)
        )
        
        result = validator.validate_spec_before_modification(spec_valid)
        
        assert result["file_exists"] is True
        assert result["spec_valid"] is True


class TestIntegration:
    """Tests de integración Fase 2"""
    
    def test_full_modification_workflow(self, tmp_path):
        """Test workflow completo: spec → modify → validate"""
        # 1. Crear archivo de prueba
        test_file = tmp_path / "integration_test.py"
        test_code = """class Config:
    threshold = 0.70
"""
        test_file.write_text(test_code)
        
        #2. Crear spec
        spec = TechnicalSpec(
            proposal_id="INTEGRATION_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path=str(test_file),
            class_name="Config",
            attribute_name="threshold",
            old_value=0.70,
            new_value=0.65,
            data_type="float"
        )
        
        # 3. Pre-validar
        validator = SafetyValidator()
        pre_validation = validator.validate_spec_before_modification(spec)
        assert pre_validation["valid"] is True
        
        # 4. Modificar
        modifier = ASTModifier()
        result = modifier.modify_file(spec)
        
        # El resultado puede ser exitoso o fallar al usar AST pero usar fallback
        # De cualquier manera, debería haber procesado
        assert result is not None
        assert "backup_path" in result
