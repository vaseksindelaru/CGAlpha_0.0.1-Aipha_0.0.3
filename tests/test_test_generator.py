"""
Tests para el TestGenerator de Code Craft Sage - Fase 3.

Este archivo contiene tests unitarios para verificar que el TestGenerator
cumple con los requisitos de la Parte 9 de la Constitución.
"""

import pytest
from pathlib import Path
from cgalpha.codecraft.test_generator import TestGenerator
from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType


class TestTestGenerator:
    """Tests para la clase TestGenerator."""
    
    def test_initialization(self):
        """Verifica que el TestGenerator se inicializa correctamente."""
        generator = TestGenerator()
        assert generator.template_dir == "cgalpha/codecraft/templates/"
        assert generator.min_coverage_threshold == 80.0
    
    def test_extract_module_path(self):
        """Verifica la extracción correcta del path del módulo."""
        generator = TestGenerator()
        
        # Test con archivo .py
        assert generator._extract_module_path("core/oracle.py") == "core.oracle"
        assert generator._extract_module_path("cgalpha/codecraft/test_generator.py") == "cgalpha.codecraft.test_generator"
        
        # Test sin extensión
        assert generator._extract_module_path("core/oracle") == "core.oracle"
    
    def test_select_template(self):
        """Verifica la selección correcta del template según el tipo de cambio."""
        generator = TestGenerator()
        
        assert generator._select_template(ChangeType.PARAMETER_CHANGE) == "parameter_change_test.j2"
        assert generator._select_template(ChangeType.METHOD_ADDITION) == "method_addition_test.j2"
        assert generator._select_template(ChangeType.CLASS_MODIFICATION) == "class_modification_test.j2"
    
    def test_prepare_template_context(self):
        """Verifica la preparación correcta del contexto para el template."""
        generator = TestGenerator()
        
        spec = TechnicalSpec(
            proposal_id="test_prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="core/oracle.py",
            class_name="OracleEngine",
            attribute_name="threshold",
            old_value=0.3,
            new_value=0.5,
            data_type="float",
            validation_rules={"min": 0.0, "max": 1.0}
        )
        
        context = generator._prepare_template_context(spec)
        
        assert context["proposal_id"] == "test_prop_001"
        assert context["module_path"] == "core.oracle"
        assert context["class_name"] == "OracleEngine"
        assert context["attribute_name"] == "threshold"
        assert context["new_value"] == 0.5
        assert context["data_type"] == "float"
    
    def test_determine_overall_status_all_passed(self):
        """Verifica que el estado es 'ready' cuando todo pasa."""
        generator = TestGenerator()
        
        status = generator._determine_overall_status(
            new_test_status="passed",
            regression_status="passed",
            coverage_percentage=85.0
        )
        
        assert status == "ready"
    
    def test_determine_overall_status_regression_failed(self):
        """Verifica que el estado es 'needs_fix' cuando la regresión falla."""
        generator = TestGenerator()
        
        status = generator._determine_overall_status(
            new_test_status="passed",
            regression_status="failed",
            coverage_percentage=85.0
        )
        
        assert status == "needs_fix"
    
    def test_determine_overall_status_new_test_failed(self):
        """Verifica que el estado es 'needs_fix' cuando el nuevo test falla."""
        generator = TestGenerator()
        
        status = generator._determine_overall_status(
            new_test_status="failed",
            regression_status="passed",
            coverage_percentage=85.0
        )
        
        assert status == "needs_fix"
    
    def test_determine_overall_status_coverage_low(self):
        """Verifica que el estado es 'needs_fix' cuando la cobertura es baja."""
        generator = TestGenerator()
        
        status = generator._determine_overall_status(
            new_test_status="passed",
            regression_status="passed",
            coverage_percentage=75.0
        )
        
        assert status == "needs_fix"
    
    def test_collect_warnings_regression_failed(self):
        """Verifica que se generan advertencias críticas cuando la regresión falla."""
        generator = TestGenerator()
        
        warnings = generator._collect_warnings(
            new_test_status="passed",
            regression_status="failed",
            coverage_percentage=85.0
        )
        
        assert len(warnings) > 0
        assert any("CRITICAL" in w and "Regression tests failed" in w for w in warnings)
    
    def test_collect_warnings_coverage_low(self):
        """Verifica que se generan advertencias críticas cuando la cobertura es baja."""
        generator = TestGenerator()
        
        warnings = generator._collect_warnings(
            new_test_status="passed",
            regression_status="passed",
            coverage_percentage=75.0
        )
        
        assert len(warnings) > 0
        assert any("CRITICAL" in w and "Coverage" in w for w in warnings)
    
    def test_collect_warnings_coverage_acceptable(self):
        """Verifica que se generan advertencias INFO cuando la cobertura es aceptable pero mejorable."""
        generator = TestGenerator()
        
        warnings = generator._collect_warnings(
            new_test_status="passed",
            regression_status="passed",
            coverage_percentage=85.0
        )
        
        assert len(warnings) > 0
        assert any("INFO" in w and "Coverage" in w for w in warnings)
    
    def test_generate_and_validate_invalid_spec(self):
        """Verifica que se maneja correctamente una especificación inválida."""
        generator = TestGenerator()
        
        # Crear spec inválido (sin proposal_id)
        spec = TechnicalSpec(
            proposal_id="",  # Inválido
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="core/oracle.py"
        )
        
        result = generator.generate_and_validate(spec, "core/oracle.py")
        
        assert result["overall_status"] == "needs_fix"
        assert "Invalid TechnicalSpec" in result["details"]["error"]
    
    def test_parse_coverage_from_output(self):
        """Verifica el parsing del porcentaje de cobertura desde el output."""
        generator = TestGenerator()
        
        # Test con output típico
        output = "TOTAL 100 50 50%"
        coverage = generator._parse_coverage_from_output(output)
        assert coverage == 50.0
        
        # Test con output más complejo
        output = "Module coverage: 75%\nTOTAL 200 50 75%"
        coverage = generator._parse_coverage_from_output(output)
        assert coverage == 75.0


class TestConstitutionCompliance:
    """Tests para verificar el cumplimiento de la Parte 9 de la Constitución."""
    
    def test_unit_test_generation(self):
        """Verifica que se generan tests unitarios (Requisito Constitución Parte 9)."""
        generator = TestGenerator()
        
        spec = TechnicalSpec(
            proposal_id="test_prop_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="core/oracle.py",
            class_name="OracleEngine",
            attribute_name="threshold",
            old_value=0.3,
            new_value=0.5,
            data_type="float"
        )
        
        test_path = generator._generate_unit_test(spec)
        
        # Verificar que el archivo se creó
        assert Path(test_path).exists()
        
        # Verificar que el archivo contiene el test esperado
        content = Path(test_path).read_text()
        assert "test_threshold_updated_to_0_5" in content
        assert "assert obj.threshold == 0.5" in content
        
        # Limpiar
        Path(test_path).unlink()
    
    def test_regression_test_method_exists(self):
        """Verifica que existe el método de tests de regresión (Requisito Constitución Parte 9)."""
        generator = TestGenerator()
        
        # Verificar que el método existe
        assert hasattr(generator, '_run_regression_tests')
        assert callable(getattr(generator, '_run_regression_tests'))
    
    def test_coverage_check_method_exists(self):
        """Verifica que existe el método de verificación de cobertura (Requisito Constitución Parte 9)."""
        generator = TestGenerator()
        
        # Verificar que el método existe
        assert hasattr(generator, '_check_coverage')
        assert callable(getattr(generator, '_check_coverage'))
    
    def test_coverage_threshold_is_80_percent(self):
        """Verifica que el umbral de cobertura es del 80% (Requisito Constitución Parte 9)."""
        generator = TestGenerator()
        
        assert generator.min_coverage_threshold == 80.0
    
    def test_triple_barrier_implementation(self):
        """Verifica la implementación de la Triple Barrera de calidad."""
        generator = TestGenerator()
        
        # Barrera 1: Unit Test
        assert hasattr(generator, '_generate_unit_test')
        assert hasattr(generator, '_run_new_test')
        
        # Barrera 2: Regression Test
        assert hasattr(generator, '_run_regression_tests')
        
        # Barrera 3: Coverage
        assert hasattr(generator, '_check_coverage')
        
        # Verificación de estado global
        assert hasattr(generator, '_determine_overall_status')
