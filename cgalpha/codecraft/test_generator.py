"""
Test Generator: Componente dual de Code Craft Sage para generación y validación de tests.

Este módulo implementa la Fase 3 de Code Craft Sage, responsable de:
1. Generar tests unitarios específicos para cambios (usando Jinja2 Templates)
2. Ejecutar la suite de tests existente para validar NO REGRESIÓN (Regression Test)
3. Verificar la cobertura de código (Coverage > 80%)

Constitución Compliance (Parte 9):
- Unit Tests: Generados automáticamente para cada cambio
- Integration Tests: Ejecutados (tests existentes)
- Regression Tests: Validados antes de aprobar cambios
- Coverage: Mínimo 80% requerido
"""

import os
import subprocess
import json
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType


class TestGenerator:
    """
    Generador y ejecutor de tests para Code Craft Sage.
    
    Responsabilidades:
    - Generar archivos de test unitario específicos para cambios
    - Ejecutar pytest para detectar regresiones
    - Verificar cobertura de código
    - Reportar estado global de validación
    """
    
    def __init__(self, template_dir: str = "cgalpha/codecraft/templates/", working_dir: str = "."):
        """
        Inicializa el TestGenerator.
        
        Args:
            template_dir: Directorio donde se encuentran los templates Jinja2
        """
        self.working_dir = Path(working_dir).resolve()
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.min_coverage_threshold = 80.0  # 80% mínimo según Constitución Parte 9
        
    def generate_and_validate(self, spec: TechnicalSpec, modified_file_path: str) -> Dict:
        """
        Genera test nuevo y ejecuta suite de validación completa.
        
        Este es el método principal que orquesta todo el proceso de validación:
        1. Genera el test unitario específico para el cambio
        2. Ejecuta el nuevo test para verificar que pasa
        3. Ejecuta tests de regresión (tests existentes)
        4. Verifica cobertura de código
        5. Retorna estado global
        
        Args:
            spec: Especificación técnica del cambio
            modified_file_path: Ruta al archivo modificado
            
        Returns:
            Dict con estado de validación:
            {
                "new_test_path": str,
                "new_test_status": "passed"|"failed",
                "regression_status": "passed"|"failed",
                "coverage_percentage": float,
                "overall_status": "ready"|"needs_fix",
                "details": {
                    "new_test_output": str,
                    "regression_output": str,
                    "coverage_output": str,
                    "warnings": List[str]
                }
            }
        """
        # Validar spec
        is_valid, error_msg = spec.is_valid()
        if not is_valid:
            return {
                "new_test_path": None,
                "new_test_status": "failed",
                "regression_status": "failed",
                "coverage_percentage": 0.0,
                "overall_status": "needs_fix",
                "details": {
                    "error": f"Invalid TechnicalSpec: {error_msg}",
                    "warnings": []
                }
            }
        
        # Paso 1: Generar test unitario
        new_test_path = self._generate_unit_test(spec)
        
        # Paso 2: Ejecutar nuevo test
        new_test_status, new_test_output = self._run_new_test(new_test_path)
        
        # Paso 3: Ejecutar tests de regresión (CRÍTICO según Constitución)
        target_module = self._extract_module_path(modified_file_path)
        related_test_paths = self._find_related_tests(target_module)
        regression_status, regression_output = self._run_regression_tests(
            target_module,
            test_paths=related_test_paths
        )
        
        # Paso 4: Verificar cobertura
        coverage_targets = [new_test_path] + related_test_paths
        coverage_percentage, coverage_output = self._check_coverage(
            target_module,
            test_paths=coverage_targets
        )
        
        # Paso 5: Determinar estado global
        overall_status = self._determine_overall_status(
            new_test_status,
            regression_status,
            coverage_percentage
        )
        
        # Recopilar advertencias
        warnings = self._collect_warnings(
            new_test_status,
            regression_status,
            coverage_percentage
        )
        
        return {
            "new_test_path": new_test_path,
            "new_test_status": new_test_status,
            "regression_status": regression_status,
            "coverage_percentage": coverage_percentage,
            "overall_status": overall_status,
            "details": {
                "new_test_output": new_test_output,
                "regression_output": regression_output,
                "coverage_output": coverage_output,
                "warnings": warnings
            }
        }
    
    def _generate_unit_test(self, spec: TechnicalSpec) -> str:
        """
        Genera el archivo del test unitario específico.
        
        Args:
            spec: Especificación técnica del cambio
            
        Returns:
            Ruta al archivo de test generado
        """
        # Seleccionar template según tipo de cambio
        template_name = self._select_template(spec.change_type)
        
        try:
            template = self.env.get_template(template_name)
        except TemplateNotFound:
            # Fallback a template genérico
            template = self.env.get_template("parameter_change_test.j2")
        
        # Preparar contexto para el template
        context = self._prepare_template_context(spec)
        
        # Renderizar template
        test_content = template.render(**context)
        
        # Determinar ruta de salida
        test_filename = f"test_{spec.proposal_id}.py"
        test_dir = self.working_dir / "tests" / "generated"
        test_dir.mkdir(parents=True, exist_ok=True)
        test_path = test_dir / test_filename
        
        # Escribir archivo
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        return str(test_path.relative_to(self.working_dir))
    
    def _select_template(self, change_type: ChangeType) -> str:
        """
        Selecciona el template apropiado según el tipo de cambio.
        
        Args:
            change_type: Tipo de cambio
            
        Returns:
            Nombre del template a usar
        """
        template_mapping = {
            ChangeType.PARAMETER_CHANGE: "parameter_change_test.j2",
            ChangeType.METHOD_ADDITION: "method_addition_test.j2",
            ChangeType.CLASS_MODIFICATION: "class_modification_test.j2",
            ChangeType.CONFIG_UPDATE: "config_update_test.j2",
            ChangeType.IMPORT_ADDITION: "import_addition_test.j2",
            ChangeType.DOCSTRING_UPDATE: "docstring_update_test.j2",
        }
        
        return template_mapping.get(change_type, "parameter_change_test.j2")
    
    def _prepare_template_context(self, spec: TechnicalSpec) -> Dict:
        """
        Prepara el contexto para renderizar el template Jinja2.
        
        Args:
            spec: Especificación técnica
            
        Returns:
            Diccionario con contexto para el template
        """
        # Extraer module_path desde file_path
        module_path = self._extract_module_path(spec.file_path)
        
        context = {
            "proposal_id": spec.proposal_id,
            "module_path": module_path,
            "class_name": spec.class_name or "UnknownClass",
            "attribute_name": spec.attribute_name or "unknown_attribute",
            "method_name": spec.method_name or "unknown_method",
            "old_value": spec.old_value,
            "new_value": spec.new_value,
            "data_type": spec.data_type or "Any",
            "validation_rules": spec.validation_rules or {},
            "timestamp": datetime.now().isoformat(),
            "change_type": spec.change_type.value,
        }
        
        return context
    
    def _extract_module_path(self, file_path: str) -> str:
        """
        Extrae el path del módulo desde la ruta del archivo.
        
        Args:
            file_path: Ruta al archivo (ej: "core/oracle.py")
            
        Returns:
            Path del módulo (ej: "core.oracle")
        """
        # Remover extensión .py
        if file_path.endswith('.py'):
            file_path = file_path[:-3]
        
        # Convertir / a .
        module_path = file_path.replace('/', '.').replace('\\', '.')
        
        return module_path
    
    def _run_new_test(self, test_path: str) -> Tuple[str, str]:
        """
        Ejecuta el test recién generado.
        
        Args:
            test_path: Ruta al archivo de test
            
        Returns:
            Tupla (status, output) donde status es "passed" o "failed"
        """
        try:
            result = subprocess.run(
                ["pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.working_dir),
                env=self._build_subprocess_env()
            )
            
            output = result.stdout + result.stderr
            
            if result.returncode == 0:
                return "passed", output
            else:
                return "failed", output
                
        except subprocess.TimeoutExpired:
            return "failed", "Test execution timed out"
        except Exception as e:
            return "failed", f"Error running test: {str(e)}"
    
    def _run_regression_tests(self, target_module: str, test_paths: Optional[List[str]] = None) -> Tuple[str, str]:
        """
        Ejecuta pytest en el módulo objetivo para detectar fallos.
        
        CRÍTICO: Este método cumple el requisito de "Regression Tests" de la Constitución.
        El sistema NO debe permitir un cambio si rompe aunque sea UNO de los tests existentes.
        
        Args:
            target_module: Path del módulo a testear (ej: "core.oracle")
            
        Returns:
            Tupla (status, output) donde status es "passed" o "failed"
        """
        try:
            # Buscar tests existentes relacionados con el módulo
            if test_paths is None:
                test_paths = self._find_related_tests(target_module)
            
            if not test_paths:
                # No hay tests existentes para este módulo
                return "passed", "No existing tests found for regression check"
            
            # Ejecutar pytest sobre los tests existentes
            cmd = ["pytest", "-v", "--tb=short"] + test_paths
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.working_dir),
                env=self._build_subprocess_env()
            )
            
            output = result.stdout + result.stderr
            
            # CRÍTICO: Si falla CUALQUIER test, regresión falla
            if result.returncode == 0:
                return "passed", output
            else:
                return "failed", output
                
        except subprocess.TimeoutExpired:
            return "failed", "Regression tests execution timed out"
        except Exception as e:
            return "failed", f"Error running regression tests: {str(e)}"
    
    def _find_related_tests(self, target_module: str) -> List[str]:
        """
        Busca archivos de tests relacionados con el módulo objetivo.
        
        Args:
            target_module: Path del módulo (ej: "core.oracle")
            
        Returns:
            Lista de rutas a archivos de tests
        """
        test_paths = []
        tests_dir = self.working_dir / "tests"
        
        if not tests_dir.exists():
            return test_paths
        
        # Buscar tests que coincidan con el módulo
        module_name = target_module.split('.')[-1]
        
        # Buscar en tests/ y subdirectorios
        for test_file in tests_dir.rglob("test_*.py"):
            # Excluir tests generados (solo queremos tests existentes)
            if "generated" in str(test_file):
                continue
            
            # Verificar si el test está relacionado con el módulo
            test_content = test_file.read_text(encoding="utf-8", errors="ignore")
            if module_name in test_content or target_module in test_content:
                test_paths.append(str(test_file.relative_to(self.working_dir)))
        
        return test_paths
    
    def _check_coverage(self, target_module: str, test_paths: Optional[List[str]] = None) -> Tuple[float, str]:
        """
        Ejecuta pytest --cov y retorna el porcentaje.
        
        Args:
            target_module: Path del módulo a verificar cobertura
            
        Returns:
            Tupla (coverage_percentage, output)
        """
        try:
            # Ejecutar pytest con coverage
            cmd = [
                "pytest",
                "--cov=" + target_module,
                "--cov-report=term-missing",
                "--cov-report=json",
                "-q"
            ]
            if test_paths:
                cmd.extend(test_paths)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self.working_dir),
                env=self._build_subprocess_env()
            )
            
            output = result.stdout + result.stderr
            
            # Intentar leer el reporte JSON
            coverage_percentage = 0.0
            try:
                coverage_file = self.working_dir / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file, 'r', encoding='utf-8') as f:
                        coverage_data = json.load(f)
                    
                    # Extraer cobertura total
                    totals = coverage_data.get("totals", {})
                    coverage_percentage = totals.get("percent_covered", 0.0)
                    
                    # Limpiar archivo temporal
                    coverage_file.unlink()
            except Exception:
                # Si no podemos leer el JSON, intentar parsear del output
                coverage_percentage = self._parse_coverage_from_output(output)
            
            return coverage_percentage, output
            
        except subprocess.TimeoutExpired:
            return 0.0, "Coverage check timed out"
        except Exception as e:
            return 0.0, f"Error checking coverage: {str(e)}"
    
    def _parse_coverage_from_output(self, output: str) -> float:
        """
        Parsea el porcentaje de cobertura desde el output de pytest-cov.
        
        Args:
            output: Output de pytest --cov
            
        Returns:
            Porcentaje de cobertura (0.0-100.0)
        """
        # Buscar patrones como "TOTAL 100 50 50%"
        import re
        
        # Patrón para buscar porcentaje al final de línea
        pattern = r'(\d+)%'
        matches = re.findall(pattern, output)
        
        if matches:
            # Tomar el último match (usualmente es el TOTAL)
            return float(matches[-1])
        
        return 0.0
    
    def _determine_overall_status(
        self,
        new_test_status: str,
        regression_status: str,
        coverage_percentage: float
    ) -> str:
        """
        Determina el estado global de validación.
        
        Args:
            new_test_status: Estado del nuevo test
            regression_status: Estado de tests de regresión
            coverage_percentage: Porcentaje de cobertura
            
        Returns:
            "ready" si todo está OK, "needs_fix" si hay problemas
        """
        # CRÍTICO: Regresión falla = needs_fix (Constitución Parte 9)
        if regression_status != "passed":
            return "needs_fix"
        
        # Nuevo test debe pasar
        if new_test_status != "passed":
            return "needs_fix"
        
        # Cobertura debe ser >= 80%
        if coverage_percentage < self.min_coverage_threshold:
            return "needs_fix"
        
        return "ready"
    
    def _collect_warnings(
        self,
        new_test_status: str,
        regression_status: str,
        coverage_percentage: float
    ) -> List[str]:
        """
        Recopila advertencias basadas en el estado de validación.
        
        Args:
            new_test_status: Estado del nuevo test
            regression_status: Estado de tests de regresión
            coverage_percentage: Porcentaje de cobertura
            
        Returns:
            Lista de mensajes de advertencia
        """
        warnings = []
        
        if regression_status != "passed":
            warnings.append(
                "CRITICAL: Regression tests failed. "
                "Change breaks existing functionality. "
                "This violates Constitution Part 9 requirements."
            )
        
        if new_test_status != "passed":
            warnings.append(
                "WARNING: New unit test failed. "
                "The generated test does not validate the change correctly."
            )
        
        if coverage_percentage < self.min_coverage_threshold:
            warnings.append(
                f"CRITICAL: Coverage ({coverage_percentage:.1f}%) is below "
                f"required threshold ({self.min_coverage_threshold}%). "
                "This violates Constitution Part 9 requirements."
            )
        elif coverage_percentage < 90.0:
            warnings.append(
                f"INFO: Coverage ({coverage_percentage:.1f}%) is acceptable "
                f"but could be improved (target: 90%+)."
            )
        
        return warnings

    def _build_subprocess_env(self) -> Dict[str, str]:
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        if existing_pythonpath:
            env["PYTHONPATH"] = f"{self.working_dir}{os.pathsep}{existing_pythonpath}"
        else:
            env["PYTHONPATH"] = str(self.working_dir)
        return env


# Función de conveniencia para uso directo
def generate_and_validate_tests(spec: TechnicalSpec, modified_file_path: str) -> Dict:
    """
    Función de conveniencia para generar y validar tests.
    
    Args:
        spec: Especificación técnica del cambio
        modified_file_path: Ruta al archivo modificado
        
    Returns:
        Dict con estado de validación
    """
    generator = TestGenerator()
    return generator.generate_and_validate(spec, modified_file_path)
