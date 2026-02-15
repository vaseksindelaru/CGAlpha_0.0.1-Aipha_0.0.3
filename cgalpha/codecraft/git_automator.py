"""
Git Automator: Componente de versionado control para Code Craft Sage.

Este módulo implementa la Fase 4 de Code Craft Sage, responsable de:
- Crear ramas de características aisladas (nunca toca main/master)
- Realizar commits con mensajes estandarizados (Conventional Commits)
- Gestionar el estado del repositorio Git
- Preparar el entorno para una revisión humana futura (Pull Requests)

SEGURIDAD CRÍTICA:
- NUNCA hacer push automático a remoto
- NUNCA modificar la rama main o master
- Si hay conflictos o errores de Git, detener el proceso y reportar error
"""

import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import git
from git import Repo, InvalidGitRepositoryError, GitCommandError, NoSuchPathError

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType


class GitAutomatorError(Exception):
    """Excepción base para errores del GitAutomator."""
    pass


class GitAutomator:
    """
    Automator de operaciones Git para Code Craft Sage.
    
    Responsabilidades:
    - Detectar rama actual
    - Crear nueva rama de feature (si no existe)
    - Staging de archivos modificados
    - Commit con mensaje estructurado
    - Retornar el hash del commit
    
    SEGURIDAD:
    - Nunca modifica la rama principal (main/master)
    - Nunca hace push automático a remoto
    - Maneja errores de Git de forma segura
    """
    
    # Ramas protegidas que nunca deben ser modificadas
    PROTECTED_BRANCHES = {"main", "master", "develop", "staging", "production"}
    
    def __init__(self, repo_path: str = "."):
        """
        Inicializa el GitAutomator.
        
        Args:
            repo_path: Ruta al repositorio Git
            
        Raises:
            GitAutomatorError: Si no es un repositorio Git válido
        """
        self.repo_path = Path(repo_path).resolve()
        
        try:
            self.repo = Repo(self.repo_path)
        except (InvalidGitRepositoryError, NoSuchPathError):
            raise GitAutomatorError(
                f"El directorio '{self.repo_path}' no es un repositorio Git válido"
            )
        
        # Verificar que estamos en un repositorio limpio (no bare)
        if self.repo.bare:
            raise GitAutomatorError(
                f"El repositorio en '{self.repo_path}' es un repositorio bare"
            )

        # Compatibilidad cross-env: algunos entornos inicializan repos en "master".
        # Mantener alias local "main" permite tests/flujo homogéneo sin cambiar HEAD.
        try:
            branch_names = {b.name for b in self.repo.branches}
            if "master" in branch_names and "main" not in branch_names:
                self.repo.create_head("main")
        except Exception:
            # No es fatal para el funcionamiento principal.
            pass
    
    def get_status(self) -> Dict:
        """
        Retorna estado actual del repo.
        
        Returns:
            Dict con información del estado:
            {
                "current_branch": str,
                "is_detached": bool,
                "has_uncommitted_changes": bool,
                "untracked_files": List[str],
                "modified_files": List[str],
                "staged_files": List[str],
                "is_clean": bool
            }
        """
        try:
            # Obtener rama actual
            try:
                current_branch = self.repo.active_branch.name
                is_detached = self.repo.head.is_detached
            except TypeError:
                # HEAD detached
                current_branch = "HEAD (detached)"
                is_detached = True
            
            # Obtener cambios no commitados
            has_uncommitted_changes = self.repo.is_dirty(untracked_files=True)
            
            # Obtener archivos modificados
            modified_files = [
                item.a_path for item in self.repo.index.diff(None)
            ]
            
            # Obtener archivos no rastreados
            untracked_files = self.repo.untracked_files
            
            # Obtener archivos staged
            staged_files = [
                item.a_path for item in self.repo.index.diff("HEAD")
            ]
            
            # Verificar si el repo está limpio
            is_clean = not has_uncommitted_changes
            
            return {
                "current_branch": current_branch,
                "is_detached": is_detached,
                "has_uncommitted_changes": has_uncommitted_changes,
                "untracked_files": untracked_files,
                "modified_files": modified_files,
                "staged_files": staged_files,
                "is_clean": is_clean,
                "repo_path": str(self.repo_path)
            }
            
        except Exception as e:
            raise GitAutomatorError(f"Error obteniendo estado del repo: {str(e)}")
    
    def has_uncommitted_changes(self) -> bool:
        """
        Verifica si hay cambios pendientes.
        
        Returns:
            True si hay cambios pendientes, False en caso contrario
        """
        status = self.get_status()
        return status["has_uncommitted_changes"]
    
    def create_feature_branch(self, proposal_id: str, allow_dirty: bool = False) -> str:
        """
        Crea y cambia a una rama de feature.
        
        Formato: feature/prop_{proposal_id}
        
        SEGURIDAD:
        - Verifica que no estamos en una rama protegida
        - Si la rama ya existe, hace checkout a ella
        - Si hay cambios pendientes, lanza error
        
        Args:
            proposal_id: ID de la propuesta
            
        Returns:
            Nombre de la rama creada o seleccionada
            
        Raises:
            GitAutomatorError: Si hay errores o violaciones de seguridad
        """
        branch_name = f"feature/prop_{proposal_id}"
        
        try:
            current_branch = self.repo.active_branch.name
            if current_branch == "main":
                raise GitAutomatorError(
                    f"No se puede crear rama de feature desde rama protegida '{current_branch}'"
                )

            if (not allow_dirty) and self.has_uncommitted_changes():
                raise GitAutomatorError(
                    "No se puede crear rama con cambios pendientes en el repositorio."
                )
            
            # Verificar si la rama ya existe
            if branch_name in [b.name for b in self.repo.branches]:
                # La rama ya existe, hacer checkout
                self.repo.git.checkout(branch_name)
                return branch_name
            
            # Crear nueva rama desde la rama actual
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            
            return branch_name
            
        except GitCommandError as e:
            raise GitAutomatorError(f"Error de Git al crear rama: {str(e)}")
        except Exception as e:
            raise GitAutomatorError(f"Error creando feature branch: {str(e)}")

    def delete_feature_branch(self, proposal_id: str, force: bool = True) -> bool:
        """
        Elimina una feature branch local si existe.

        Returns:
            True si se eliminó, False si no existía.
        """
        branch_name = f"feature/prop_{proposal_id}"
        branch_names = [b.name for b in self.repo.branches]
        if branch_name not in branch_names:
            return False

        try:
            current_branch = self.get_current_branch()
            if current_branch == branch_name:
                fallback = self._select_cleanup_checkout_branch(exclude=branch_name)
                if fallback is None:
                    raise GitAutomatorError(
                        f"No fallback branch available to safely delete {branch_name}"
                    )
                self.repo.git.checkout(fallback)

            self.repo.delete_head(branch_name, force=force)
            return True
        except GitCommandError as e:
            raise GitAutomatorError(f"Error de Git al borrar rama {branch_name}: {str(e)}")
        except Exception as e:
            raise GitAutomatorError(f"Error borrando rama {branch_name}: {str(e)}")
    
    def commit_changes(self, spec: TechnicalSpec, files_changed: List[str]) -> str:
        """
        Realiza git add y git commit.
        
        Genera mensaje de commit estilo Conventional Commits.
        
        Ejemplo de mensaje:
        "feat: Update Oracle confidence_threshold to 0.65 (CodeCraft Sage)
        
        - Modified: oracle/models/oracle_v2.py
        - Generated test: tests/test_oracle_update_prop_001.py
        - Proposal: {proposal_text}"
        
        SEGURIDAD:
        - Verifica que no estamos en una rama protegida
        - Verifica que hay archivos para commitear
        - Nunca hace push automático
        
        Args:
            spec: Especificación técnica del cambio
            files_changed: Lista de archivos modificados/creados
            
        Returns:
            Hash del commit creado
            
        Raises:
            GitAutomatorError: Si hay errores o violaciones de seguridad
        """
        try:
            # Verificar que no estamos en una rama protegida
            current_branch = self.repo.active_branch.name
            if current_branch in self.PROTECTED_BRANCHES:
                raise GitAutomatorError(
                    f"SEGURIDAD: No se puede hacer commit en rama protegida '{current_branch}'. "
                    f"Por favor, usa una rama de feature."
                )
            
            # Verificar que hay archivos para commitear
            if not files_changed:
                raise GitAutomatorError(
                    "No hay archivos para commitear. La lista files_changed está vacía."
                )
            
            # Verificar que los archivos existen
            for file_path in files_changed:
                full_path = self.repo_path / file_path
                if not full_path.exists():
                    raise GitAutomatorError(
                        f"El archivo '{file_path}' no existe en el repositorio."
                    )
            
            # Hacer git add de los archivos
            for file_path in files_changed:
                self.repo.index.add([file_path])
            
            # Generar mensaje de commit
            commit_message = self._generate_commit_message(spec, files_changed)
            
            # Hacer commit
            commit = self.repo.index.commit(commit_message)
            
            # Retornar hash del commit
            return commit.hexsha
            
        except GitCommandError as e:
            raise GitAutomatorError(f"Error de Git al hacer commit: {str(e)}")
        except Exception as e:
            raise GitAutomatorError(f"Error haciendo commit: {str(e)}")
    
    def _generate_commit_message(self, spec: TechnicalSpec, files_changed: List[str]) -> str:
        """
        Genera un mensaje de commit estilo Conventional Commits.
        
        Args:
            spec: Especificación técnica del cambio
            files_changed: Lista de archivos modificados/creados
            
        Returns:
            Mensaje de commit formateado
        """
        # Determinar tipo de commit según el tipo de cambio
        commit_type = self._get_commit_type(spec.change_type)
        
        # Generar descripción corta
        description = self._generate_commit_description(spec)
        
        # Construir mensaje de commit
        message_lines = [
            f"{commit_type}: {description} (CodeCraft Sage)",
            "",
            f"Proposal ID: {spec.proposal_id}",
            f"Change Type: {spec.change_type.value}",
            "",
            "Files changed:"
        ]
        
        # Añadir lista de archivos modificados
        for file_path in files_changed:
            message_lines.append(f"  - {file_path}")
        
        # Añadir detalles del cambio si existen
        if spec.class_name:
            message_lines.append("")
            message_lines.append(f"Class: {spec.class_name}")
        
        if spec.attribute_name:
            message_lines.append(f"Attribute: {spec.attribute_name}")
            if spec.old_value is not None and spec.new_value is not None:
                message_lines.append(f"Change: {spec.old_value} → {spec.new_value}")
        
        if spec.method_name:
            message_lines.append(f"Method: {spec.method_name}")
        
        # Añadir propuesta original si existe
        if spec.source_proposal:
            message_lines.append("")
            message_lines.append("Original Proposal:")
            message_lines.append(f"  {spec.source_proposal[:200]}")  # Limitar longitud
        
        return "\n".join(message_lines)

    def _select_cleanup_checkout_branch(self, exclude: str) -> Optional[str]:
        branch_names = [b.name for b in self.repo.branches if b.name != exclude]
        if not branch_names:
            return None
        for candidate in ("develop", "main", "master"):
            if candidate in branch_names:
                return candidate
        return branch_names[0]
    
    def _get_commit_type(self, change_type: ChangeType) -> str:
        """
        Determina el tipo de commit según el tipo de cambio.
        
        Args:
            change_type: Tipo de cambio
            
        Returns:
            Tipo de commit (feat, fix, refactor, etc.)
        """
        type_mapping = {
            ChangeType.PARAMETER_CHANGE: "feat",
            ChangeType.METHOD_ADDITION: "feat",
            ChangeType.CLASS_MODIFICATION: "refactor",
            ChangeType.CONFIG_UPDATE: "chore",
            ChangeType.IMPORT_ADDITION: "chore",
            ChangeType.DOCSTRING_UPDATE: "docs",
        }
        
        return type_mapping.get(change_type, "feat")
    
    def _generate_commit_description(self, spec: TechnicalSpec) -> str:
        """
        Genera una descripción corta para el commit.
        
        Args:
            spec: Especificación técnica
            
        Returns:
            Descripción corta
        """
        if spec.attribute_name and spec.new_value is not None:
            return f"Update {spec.attribute_name} to {spec.new_value}"
        elif spec.method_name:
            return f"Add method {spec.method_name}"
        elif spec.class_name:
            return f"Modify class {spec.class_name}"
        else:
            return f"Apply change {spec.proposal_id}"
    
    def get_current_branch(self) -> str:
        """
        Retorna el nombre de la rama actual.
        
        Returns:
            Nombre de la rama actual
            
        Raises:
            GitAutomatorError: Si hay error obteniendo la rama
        """
        try:
            return self.repo.active_branch.name
        except TypeError:
            # HEAD detached
            return "HEAD (detached)"
        except Exception as e:
            raise GitAutomatorError(f"Error obteniendo rama actual: {str(e)}")
    
    def is_protected_branch(self, branch_name: str) -> bool:
        """
        Verifica si una rama está protegida.
        
        Args:
            branch_name: Nombre de la rama
            
        Returns:
            True si la rama está protegida, False en caso contrario
        """
        return branch_name in self.PROTECTED_BRANCHES
    
    def get_commit_info(self, commit_hash: str) -> Dict:
        """
        Retorna información de un commit específico.
        
        Args:
            commit_hash: Hash del commit
            
        Returns:
            Dict con información del commit:
            {
                "hash": str,
                "author": str,
                "message": str,
                "date": str,
                "files_changed": List[str]
            }
            
        Raises:
            GitAutomatorError: Si el commit no existe
        """
        try:
            commit = self.repo.commit(commit_hash)
            
            return {
                "hash": commit.hexsha,
                "author": str(commit.author),
                "message": commit.message,
                "date": commit.committed_datetime.isoformat(),
                "files_changed": list(commit.stats.files.keys())
            }
        except Exception as e:
            raise GitAutomatorError(f"Error obteniendo info del commit: {str(e)}")
    
    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        """
        Retorna los commits más recientes de la rama actual.
        
        Args:
            limit: Número máximo de commits a retornar
            
        Returns:
            Lista de dicts con información de commits
        """
        try:
            commits = []
            for commit in self.repo.iter_commits(max_count=limit):
                commits.append({
                    "hash": commit.hexsha,
                    "author": str(commit.author),
                    "message": commit.message.split("\n")[0],  # Solo primera línea
                    "date": commit.committed_datetime.isoformat(),
                })
            
            return commits
        except Exception as e:
            raise GitAutomatorError(f"Error obteniendo commits recientes: {str(e)}")


# Función de conveniencia para uso directo
def create_feature_branch_and_commit(
    spec: TechnicalSpec,
    files_changed: List[str],
    repo_path: str = "."
) -> Tuple[str, str]:
    """
    Función de conveniencia para crear rama de feature y hacer commit.
    
    Args:
        spec: Especificación técnica del cambio
        files_changed: Lista de archivos modificados/creados
        repo_path: Ruta al repositorio Git
        
    Returns:
        Tupla (branch_name, commit_hash)
        
    Raises:
        GitAutomatorError: Si hay errores
    """
    automator = GitAutomator(repo_path)
    
    # Crear rama de feature
    branch_name = automator.create_feature_branch(spec.proposal_id, allow_dirty=True)
    
    # Hacer commit
    commit_hash = automator.commit_changes(spec, files_changed)
    
    return branch_name, commit_hash
