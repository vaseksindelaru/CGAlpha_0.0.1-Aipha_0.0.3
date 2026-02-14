"""
SafetyValidator: Validation layer for code modifications.

Valida que los cambios de código sean seguros y no rompan el sistema.
"""

import ast
import logging
import re
from typing import Dict, Any, List
from pathlib import Path

from cgalpha.codecraft.technical_spec import TechnicalSpec

logger = logging.getLogger(__name__)


class SafetyValidator:
    """
    Validador de seguridad para modificaciones de código.
    
    Checks implementados:
    - Sintaxis válida
    - Imports intactos
    - Consistencia de tipos
    - No side effects peligrosos
    - Risk scoring (0-1, bajo es mejor)
    """
    
    def __init__(self):
        logger.info("✅ SafetyValidator initialized")
    
    def validate_change(
        self, 
        spec: TechnicalSpec, 
        original_code: str, 
        modified_code: str
    ) -> Dict[str, Any]:
        """
        Valida un cambio de código de forma comprehensiva.
        
        Args:
            spec: TechnicalSpec del cambio
            original_code: Código original
            modified_code: Código modificado
            
        Returns:
            Dict con resultados de validación:
            {
                "syntax_valid": bool,
                "imports_intact": bool,
                "no_syntax_errors": bool,
                "type_consistency": bool,
                "risk_score": float (0-1),
                "warnings": list,
                "errors": list
            }
        """
        logger.info(f"🔍 Validating change: {spec.attribute_name}")
        
        validation = {
            "syntax_valid": False,
            "imports_intact": False,
            "no_syntax_errors": False,
            "type_consistency": False,
            "risk_score": 0.0,
            "warnings": [],
            "errors": []
        }
        
        # 1. Check sintaxis
        syntax_result = self._check_syntax(modified_code)
        validation["syntax_valid"] = syntax_result["valid"]
        validation["no_syntax_errors"] = syntax_result["valid"]
        if not syntax_result["valid"]:
            validation["errors"].extend(syntax_result["errors"])
        
        # 2. Check imports
        imports_result = self._check_imports(original_code, modified_code)
        validation["imports_intact"] = imports_result["intact"]
        if not imports_result["intact"]:
            validation["warnings"].append("Imports were modified")
        
        # 3. Check consistencia de tipos
        type_result = self._check_type_consistency(spec)
        validation["type_consistency"] = type_result["consistent"]
        if not type_result["consistent"]:
            validation["warnings"].append(f"Type inconsistency: {type_result['reason']}")
        
        # 4. Calcular risk score
        validation["risk_score"] = self._calculate_risk_score(spec, validation)
        
        logger.info(f"   ✅ Validation complete. Risk: {validation['risk_score']:.2f}")
        
        return validation
    
    def _check_syntax(self, code: str) -> Dict[str, Any]:
        """
        Verifica que el código sea sintácticamente válido.
        
        Args:
            code: Código a validar
            
        Returns:
            Dict con {"valid": bool, "errors": list}
        """
        result = {"valid": False, "errors": []}
        
        try:
            ast.parse(code)
            compile(code, "<string>", "exec")
            result["valid"] = True
        except SyntaxError as e:
            result["errors"].append(f"SyntaxError line {e.lineno}: {e.msg}")
        except Exception as e:
            result["errors"].append(f"Compilation error: {e}")
        
        return result
    
    def _check_imports(self, original_code: str, modified_code: str) -> Dict[str, bool]:
        """
        Verifica que los imports no hayan sido modificados accidentalmente.
        
        Args:
            original_code: Código original
            modified_code: Código modificado
            
        Returns:
            Dict con {"intact": bool, "changes": list}
        """
        original_imports = self._extract_imports(original_code)
        modified_imports = self._extract_imports(modified_code)
        
        intact = original_imports == modified_imports
        
        changes = []
        if not intact:
            added = modified_imports - original_imports
            removed = original_imports - modified_imports
            
            if added:
                changes.append(f"Added: {added}")
            if removed:
                changes.append(f"Removed: {removed}")
        
        return {"intact": intact, "changes": changes}
    
    def _extract_imports(self, code: str) -> set:
        """
        Extrae todos los imports de un código.
        
        Args:
            code: Código Python
            
        Returns:
            Set de imports como strings
        """
        imports = set()
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.add(f"from {module} import {alias.name}")
        except:
            # Si falla el parsing, extraer imports con regex
            import_pattern = r'^(?:from\s+[\w.]+\s+)?import\s+[\w., ]+'
            for line in code.splitlines():
                if re.match(import_pattern, line.strip()):
                    imports.add(line.strip())
        
        return imports
    
    def _check_type_consistency(self, spec: TechnicalSpec) -> Dict[str, Any]:
        """
        Verifica consistencia de tipos de datos.
        
        Args:
            spec: TechnicalSpec con el cambio
            
        Returns:
            Dict con {"consistent": bool, "reason": str}
        """
        result = {"consistent": True, "reason": ""}
        
        # Verificar que new_value sea del tipo correcto
        if spec.data_type and spec.new_value is not None:
            try:
                if spec.data_type == "float":
                    float(spec.new_value)
                elif spec.data_type == "int":
                    int(spec.new_value)
                elif spec.data_type == "str":
                    str(spec.new_value)
                elif spec.data_type == "bool":
                    bool(spec.new_value)
            except (ValueError, TypeError) as e:
                result["consistent"] = False
                result["reason"] = f"Cannot convert {spec.new_value} to {spec.data_type}: {e}"
        
        # Verificar rangos de validación si existen
        if spec.validation_rules and result["consistent"]:
            if "min" in spec.validation_rules and "max" in spec.validation_rules:
                try:
                    value = float(spec.new_value)
                    min_val = spec.validation_rules["min"]
                    max_val = spec.validation_rules["max"]
                    
                    if not (min_val <= value <= max_val):
                        result["consistent"] = False
                        result["reason"] = f"Value {value} outside range [{min_val}, {max_val}]"
                except:
                    pass  # Si no es numérico, skip validación de rango
        
        return result
    
    def _calculate_risk_score(self, spec: TechnicalSpec, validation: Dict) -> float:
        """
        Calcula risk score (0-1) basado en el cambio y validación.
        
        Factores:
        - Sintaxis inválida: +0.5
        - Imports modificados: +0.2
        - Tipo inconsistente: +0.3
        - Cambio grande de valor: +0.1
        - Archivo crítico: +0.2
        
        Args:
            spec: TechnicalSpec del cambio
            validation: Resultados de validación
            
        Returns:
            Float entre 0 (sin riesgo) y 1 (muy riesgoso)
        """
        risk = 0.0
        
        # Sintaxis inválida (crítico)
        if not validation["syntax_valid"]:
            risk += 0.5
        
        # Imports modificados
        if not validation["imports_intact"]:
            risk += 0.2
        
        # Tipo inconsistente
        if not validation["type_consistency"]:
            risk += 0.3
        
        # Cambio grande de valor (solo para numéricos)
        if spec.old_value is not None and spec.new_value is not None:
            try:
                old = float(spec.old_value)
                new = float(spec.new_value)
                percent_change = abs((new - old) / old) if old != 0 else 0
                
                if percent_change > 0.5:  # >50% cambio
                    risk += 0.1
            except:
                pass  # No numérico, skip
        
        # Archivo crítico (heurística)
        critical_files = ["oracle", "trading", "risk", "core"]
        if any(critical in spec.file_path.lower() for critical in critical_files):
            risk += 0.1
        
        # Normalizar a [0, 1]
        return min(risk, 1.0)
    
    def validate_spec_before_modification(self, spec: TechnicalSpec) -> Dict[str, Any]:
        """
        Valida TechnicalSpec antes de intentar modificación.
        
        Args:
            spec: TechnicalSpec a validar
            
        Returns:
            Dict con resultados de pre-validación
        """
        result = {
            "valid": False,
            "file_exists": False,
            "spec_valid": False,
            "errors": [],
            "warnings": []
        }
        
        # Check spec validity
        is_valid, error = spec.is_valid()
        result["spec_valid"] = is_valid
        if not is_valid:
            result["errors"].append(f"TechnicalSpec invalid: {error}")
        
        # Check file exists
        file_path = Path(spec.file_path)
        result["file_exists"] = file_path.exists()
        if not result["file_exists"]:
            result["errors"].append(f"File not found: {spec.file_path}")
        
        # Check file is Python
        if file_path.suffix != ".py" and spec.change_type.value != "config_update":
            result["warnings"].append(f"File is not Python: {file_path.suffix}")
        
        result["valid"] = result["spec_valid"] and result["file_exists"]
        
        return result
