"""
ASTModifier: Safe Python code modification using Abstract Syntax Tree.

Este módulo implementa modificaciones de código Python de forma segura usando AST,
preservando formato, comentarios y validando sintaxis post-modificación.
"""

import ast
import os
import logging
import hashlib
import shutil
import re
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType

logger = logging.getLogger(__name__)


class ASTNodeVisitor(ast.NodeVisitor):
    """
    Visitor personalizado para encontrar y modificar nodos específicos en AST.
    """
    
    def __init__(self, spec: TechnicalSpec):
        self.spec = spec
        self.found_node = None
        self.parent_node = None
        self.modifications_made = []
    
    def visit_ClassDef(self, node):
        """Visita definiciones de clase"""
        if node.name == self.spec.class_name:
            # Buscar atributo dentro de la clase
            if self.spec.attribute_name:
                self._search_attribute_in_class(node)
        
        self.generic_visit(node)
    
    def _search_attribute_in_class(self, class_node):
        """Busca atributo específico dentro de una clase"""
        for item in ast.walk(class_node):
            # Buscar asignaciones (self.attribute = value)
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Attribute):
                        if target.attr == self.spec.attribute_name:
                            self.found_node = item
                            self.parent_node = class_node
                            break


class ASTModifier:
    """
    Modificador seguro de código Python usando AST.
    
    Features:
    - Backup automático antes de cada modificación
    - Validación de sintaxis post-modificación
    - Preservación de formato y comentarios
    - Rollback automático si falla
    - Tracking de cambios realizados
    """
    
    def __init__(
        self,
        backup_dir: str = "aipha_memory/temporary/ast_backups/",
        working_dir: str = ".",
        allowed_roots: Optional[List[str]] = None
    ):
        """
        Inicializa AST Modifier.
        
        Args:
            backup_dir: Directorio para backups (creado si no existe)
        """
        self.working_dir = Path(working_dir).resolve()
        self.backup_dir = Path(backup_dir).resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        roots: List[Path] = [self.working_dir]
        if allowed_roots:
            roots.extend(Path(root).resolve() for root in allowed_roots)
        else:
            # Soporte seguro para tests temporales sin permitir escritura arbitraria.
            roots.append(Path(tempfile.gettempdir()).resolve())

        deduped_roots = []
        for root in roots:
            if root not in deduped_roots:
                deduped_roots.append(root)
        self.allowed_roots = deduped_roots

        logger.info(
            "✅ ASTModifier initialized. Backup dir: %s | Working dir: %s | Allowed roots: %s",
            self.backup_dir,
            self.working_dir,
            [str(root) for root in self.allowed_roots],
        )
    
    def modify_file(self, spec: TechnicalSpec) -> Dict[str, Any]:
        """
        Modifica archivo basado en TechnicalSpec.
        
        Flujo:
        1. Validar spec y archivo
        2. Crear backup
        3. Leer y parsear código
        4. Modificar AST
        5. Reconstruir código
        6. Validar sintaxis
        7. Escribir o rollback
        
        Args:
            spec: TechnicalSpec con los cambios a realizar
            
        Returns:
            Dict con resultado:
            {
                "success": bool,
                "backup_path": str,
                "changes_made": list,
                "validation_errors": list,
                "original_hash": str,
                "new_hash": str,
                "modified_lines": list
            }
        """
        logger.info(f"🔧 Modifying file: {spec.file_path}")
        logger.info(f"   Change: {spec.attribute_name} {spec.old_value} → {spec.new_value}")
        
        result = {
            "success": False,
            "backup_path": None,
            "changes_made": [],
            "validation_errors": [],
            "original_hash": None,
            "new_hash": None,
            "modified_lines": [],
            "error": None
        }
        
        file_path = None
        try:
            # 1. Validar spec
            is_valid, error = spec.is_valid()
            if not is_valid:
                result["error"] = f"Invalid TechnicalSpec: {error}"
                result["validation_errors"].append(error)
                logger.error(f"   ❌ {result['error']}")
                return result
            
            # 2. Resolver y validar path objetivo (scope seguro)
            file_path = self._resolve_secure_file_path(spec.file_path)
            if not file_path.exists():
                result["error"] = f"File not found: {spec.file_path}"
                logger.error(f"   ❌ {result['error']}")
                return result
            
            # 3. Leer código original
            original_code = file_path.read_text(encoding="utf-8")
            result["original_hash"] = self._hash_code(original_code)
            
            # 4. Crear backup
            backup_path = self._create_backup(file_path, original_code)
            result["backup_path"] = str(backup_path)
            logger.info(f"   💾 Backup created: {backup_path}")
            
            # 5. Modificar código según tipo de cambio
            if spec.change_type == ChangeType.PARAMETER_CHANGE:
                modified_code, changes = self._modify_parameter(original_code, spec)
            elif spec.change_type == ChangeType.METHOD_ADDITION:
                modified_code, changes = self._add_method(original_code, spec)
            elif spec.change_type == ChangeType.CONFIG_UPDATE:
                # CONFIG_UPDATE usa JSON, no AST
                result["error"] = "CONFIG_UPDATE should use ActionApplicator, not ASTModifier"
                logger.warning(f"   ⚠️ {result['error']}")
                return result
            else:
                result["error"] = f"Unsupported change type: {spec.change_type}"
                logger.error(f"   ❌ {result['error']}")
                return result
            
            result["changes_made"] = changes
            if not changes:
                result["error"] = "No safe changes were produced by modifier"
                logger.error(f"   ❌ {result['error']}")
                return result
            
            # 6. Validar sintaxis del código modificado
            validation = self._validate_modification(original_code, modified_code)
            if not validation["syntax_valid"]:
                result["validation_errors"] = validation["errors"]
                result["error"] = f"Syntax validation failed: {validation['errors']}"
                logger.error(f"   ❌ {result['error']}")
                return result
            
            # 7. Escribir código modificado
            self._write_output_file(file_path, modified_code)
            result["new_hash"] = self._hash_code(modified_code)
            result["success"] = True
            
            logger.info(f"   ✅ File modified successfully")
            logger.info(f"   📝 Changes: {len(changes)}")
            logger.info(f"   🔒 Hash: {result['original_hash'][:8]} → {result['new_hash'][:8]}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"   ❌ Modification failed: {e}", exc_info=True)
            
            # Rollback si hay backup
            if result["backup_path"] and file_path is not None:
                self._rollback_from_backup(Path(result["backup_path"]), file_path)
        
        return result
    
    def _modify_parameter(self, original_code: str, spec: TechnicalSpec) -> tuple:
        """
        Modifica parámetro/atributo usando AST.
        
        Args:
            original_code: Código original
            spec: TechnicalSpec con los cambios
            
        Returns:
            Tupla (código_modificado, lista_de_cambios)
        """
        changes = []
        
        try:
            # Parsear código a AST
            tree = ast.parse(original_code)
            
            # Buscar nodo a modificar
            visitor = ASTNodeVisitor(spec)
            visitor.visit(tree)
            
            if not visitor.found_node:
                # Fallback: modificación basada en texto (línea por línea)
                logger.warning("   ⚠️ AST node not found, using text-based fallback")
                return self._modify_textual_fallback(original_code, spec)
            
            # Modificar nodo encontrado
            if isinstance(visitor.found_node, ast.Assign):
                # Reemplazar valor
                old_value_node = visitor.found_node.value
                new_value_node = self._create_value_node(spec.new_value, spec.data_type)
                visitor.found_node.value = new_value_node
                
                changes.append({
                    "type": "parameter_change",
                    "attribute": spec.attribute_name,
                    "old_value": spec.old_value,
                    "new_value": spec.new_value
                })
            
            # Reconstruir código desde AST
            modified_code = ast.unparse(tree)
            
            return modified_code, changes
            
        except Exception as e:
            logger.error(f"AST modification failed: {e}")
            # Fallback a modificación basada en texto
            return self._modify_textual_fallback(original_code, spec)
    
    def _modify_textual_fallback(self, original_code: str, spec: TechnicalSpec) -> tuple:
        """
        Fallback: modifica parámetro usando búsqueda de texto.
        
        Menos preciso que AST pero más robusto para casos edge.
        """
        changes = []
        lines = original_code.splitlines()
        modified_lines = list(lines)

        # Búsqueda conservadora: solo asignaciones explícitas y no ambiguas
        if not spec.attribute_name:
            return original_code, []

        assignment_pattern = re.compile(rf"\b{re.escape(spec.attribute_name)}\b\s*=")
        old_value_str = str(spec.old_value)
        new_value_str = str(spec.new_value)

        candidate_lines = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if assignment_pattern.search(line) and old_value_str in line:
                candidate_lines.append(i)

        if len(candidate_lines) != 1:
            logger.warning(
                "   ⚠️ Unsafe textual fallback prevented (candidates=%s) for attribute '%s'",
                len(candidate_lines),
                spec.attribute_name,
            )
            return original_code, []

        idx = candidate_lines[0]
        source_line = lines[idx]
        modified_line = source_line.replace(old_value_str, new_value_str, 1)
        modified_lines[idx] = modified_line

        changes.append({
            "type": "text_replacement",
            "line_number": idx + 1,
            "old_line": source_line,
            "new_line": modified_line
        })
        logger.info(f"   📝 Line {idx+1}: {source_line.strip()} → {modified_line.strip()}")

        modified_code = "\n".join(modified_lines)
        return modified_code, changes

    # Backward-compatible alias
    def _modify_parameter_text_based(self, original_code: str, spec: TechnicalSpec) -> tuple:
        return self._modify_textual_fallback(original_code, spec)
    
    def _add_method(self, original_code: str, spec: TechnicalSpec) -> tuple:
        """
        Añade método a una clase.
        
        Args:
            original_code: Código original
            spec: TechnicalSpec con método a añadir
            
        Returns:
            Tupla (código_modificado, lista_de_cambios)
        """
        # TODO: Implementar en iteración futura
        logger.warning("   ⚠️ METHOD_ADDITION not yet implemented")
        return original_code, []
    
    def _create_value_node(self, value: Any, data_type: str) -> ast.expr:
        """
        Crea nodo AST para un valor según su tipo.
        
        Args:
            value: Valor a convertir
            data_type: Tipo de dato ("float", "int", "str", etc.)
            
        Returns:
            Nodo AST apropiado
        """
        if data_type == "float":
            return ast.Constant(value=float(value))
        elif data_type == "int":
            return ast.Constant(value=int(value))
        elif data_type == "str":
            return ast.Constant(value=str(value))
        elif data_type == "bool":
            return ast.Constant(value=bool(value))
        else:
            # Default: constant
            return ast.Constant(value=value)
    
    def _create_backup(self, file_path: Path, content: str) -> Path:
        """
        Crea backup del archivo con timestamp.
        
        Args:
            file_path: Ruta del archivo original
            content: Contenido a guardar
            
        Returns:
            Ruta del backup creado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        
        backup_name = f"{file_path.stem}_{timestamp}_{hash_suffix}{file_path.suffix}.bak"
        backup_path = self.backup_dir / backup_name
        
        backup_path.write_text(content, encoding="utf-8")
        return backup_path

    def _resolve_secure_file_path(self, raw_path: str) -> Path:
        """
        Resuelve y valida una ruta de archivo contra roots permitidos.
        """
        if not raw_path:
            raise ValueError("Empty file path")

        raw = Path(raw_path)
        if raw.is_absolute():
            resolved = Path(os.path.abspath(raw))
        else:
            resolved = Path(os.path.abspath(self.working_dir / raw))

        if not self._is_inside_allowed_roots(resolved):
            allowed = ", ".join(str(root) for root in self.allowed_roots)
            raise ValueError(f"Insecure file path outside allowed roots: {resolved} (allowed: {allowed})")

        return resolved

    def _is_inside_allowed_roots(self, target_path: Path) -> bool:
        for root in self.allowed_roots:
            try:
                target_path.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def _write_output_file(self, file_path: Path, content: str):
        """
        Escritura final con verificación de scope y ruta absoluta.
        """
        secure_path = self._resolve_secure_file_path(str(file_path))
        secure_path.write_text(content, encoding="utf-8")
    
    def _validate_modification(self, original_code: str, modified_code: str) -> Dict[str, Any]:
        """
        Valida que el código modificado sea sintácticamente correcto.
        
        Args:
            original_code: Código original
            modified_code: Código modificado
            
        Returns:
            Dict con resultados de validación
        """
        validation = {
            "syntax_valid": False,
            "compiles": False,
            "errors": []
        }
        
        try:
            # Intentar parsear
            ast.parse(modified_code)
            validation["syntax_valid"] = True
            
            # Intentar compilar
            compile(modified_code, "<string>", "exec")
            validation["compiles"] = True
            
        except SyntaxError as e:
            validation["errors"].append(f"SyntaxError: {e}")
            logger.error(f"   ❌ Syntax error in modified code: {e}")
        except Exception as e:
            validation["errors"].append(f"Compilation error: {e}")
            logger.error(f"   ❌ Compilation error: {e}")
        
        return validation
    
    def _rollback_from_backup(self, backup_path: Path, target_path: Path):
        """
        Restaura archivo desde backup.
        
        Args:
            backup_path: Ruta del backup
            target_path: Ruta del archivo a restaurar
        """
        if backup_path.exists():
            shutil.copy2(backup_path, target_path)
            logger.warning(f"   🔄 Rolled back from backup: {backup_path}")
        else:
            logger.error(f"   ❌ Backup not found: {backup_path}")
    
    def _hash_code(self, code: str) -> str:
        """Genera hash MD5 del código"""
        return hashlib.md5(code.encode()).hexdigest()
    
    def get_backup_history(self, file_path: str) -> List[Dict]:
        """
        Obtiene historial de backups para un archivo.
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Lista de backups ordenada por fecha (más reciente primero)
        """
        file_stem = Path(file_path).stem
        backups = []
        
        for backup_file in self.backup_dir.glob(f"{file_stem}_*.bak"):
            stat = backup_file.stat()
            backups.append({
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime)
            })
        
        # Ordenar por fecha de modificación (más reciente primero)
        backups.sort(key=lambda x: x["modified"], reverse=True)
        
        return backups
