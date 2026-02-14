"""
CodeCraftOrchestrator: Director del pipeline de Code Craft Sage.

Este módulo implementa la Fase 5 de Code Craft Sage, responsable de:
- Ejecutar el pipeline secuencial: Fase 1 -> Fase 2 -> Fase 3 -> Fase 4
- Manejar el flujo de datos entre fases
- Implementar lógica de rollback total ante fallo
- Generar un reporte final unificado
"""

import json
import logging
import shutil
import time
import uuid
import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any

from cgalpha.codecraft.proposal_parser import ProposalParser
from cgalpha.codecraft.ast_modifier import ASTModifier
from cgalpha.codecraft.test_generator import TestGenerator
from cgalpha.codecraft.git_automator import GitAutomator
from cgalpha.codecraft.technical_spec import TechnicalSpec

logger = logging.getLogger(__name__)


class CodeCraftError(Exception):
    """Excepción base para errores del Orchestrator."""
    pass


class CodeCraftOrchestrator:
    """
    Orchestrator principal de Code Craft Sage.

    Responsable de orquestar el pipeline completo de 4 fases:
    1. ProposalParser - Parsear propuesta
    2. ASTModifier - Modificar código
    3. TestGenerator - Generar y validar tests
    4. GitAutomator - Crear rama y hacer commit
    """

    def __init__(self, working_dir: str = ".", auto_rollback: bool = True):
        self.working_dir = Path(working_dir).resolve()
        self.auto_rollback = auto_rollback

        backup_dir = self.working_dir / "aipha_memory" / "temporary" / "ast_backups"

        # Forzamos modo heurístico por defecto para comportamiento determinista offline.
        self.parser = ProposalParser(llm_assistant=False)
        self.modifier = ASTModifier(
            backup_dir=str(backup_dir),
            working_dir=str(self.working_dir),
            allowed_roots=[str(self.working_dir)],
        )
        templates_dir = Path(__file__).resolve().parent / "templates"
        self.test_generator = TestGenerator(
            template_dir=str(templates_dir),
            working_dir=str(self.working_dir),
        )
        self.git_automator = GitAutomator(str(self.working_dir))

        self.current_proposal_id: Optional[str] = None
        self.backup_path: Optional[str] = None
        self.pipeline_history: list = []

    def execute_pipeline(self, proposal_text: str, proposal_id: str = None) -> Dict:
        timing: Dict[str, float] = {}
        errors = []
        pipeline_history = []
        current_phase = 0
        spec: Optional[TechnicalSpec] = None

        if proposal_id is None:
            proposal_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        self.current_proposal_id = proposal_id

        try:
            # ========================================
            # FASE 1: Proposal Parser
            # ========================================
            current_phase = 1
            phase_start = time.time()
            pipeline_history.append({
                "phase": 1,
                "name": "ProposalParser",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })

            spec = self.parser.parse(proposal_text)
            spec.proposal_id = proposal_id
            self._resolve_spec_file_path(spec, proposal_text)
            self._enrich_spec_from_source(spec, proposal_text)

            timing["phase1_parsing"] = time.time() - phase_start
            pipeline_history[-1]["status"] = "success"
            pipeline_history[-1]["duration"] = timing["phase1_parsing"]
            pipeline_history[-1]["details"] = {
                "file_path": spec.file_path,
                "class_name": spec.class_name,
                "change_type": spec.change_type.value
            }

            # ========================================
            # FASE 2: AST Modifier
            # ========================================
            current_phase = 2
            phase_start = time.time()
            pipeline_history.append({
                "phase": 2,
                "name": "ASTModifier",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })

            self.backup_path = self._create_backup(spec.file_path)
            modification_result = self.modifier.modify_file(spec)

            if not modification_result.get("success", False):
                error_msg = modification_result.get("error", "Unknown error")
                errors.append({
                    "phase": 2,
                    "type": "modification_failed",
                    "message": f"AST modification failed: {error_msg}"
                })
                pipeline_history[-1]["status"] = "failed"
                pipeline_history[-1]["details"] = modification_result

                if self.auto_rollback and self.backup_path:
                    self._rollback(spec.file_path)

                branch_deleted = self._cleanup_feature_branch(proposal_id)
                pipeline_history.append({
                    "phase": "cleanup",
                    "name": "BranchCleanup",
                    "status": "success" if branch_deleted else "skipped",
                    "timestamp": datetime.now().isoformat(),
                    "details": {"branch_deleted": branch_deleted}
                })

                self._log_error_to_bridge(
                    proposal_id=proposal_id,
                    phase=2,
                    error_type="modification_failed",
                    message=error_msg,
                    details=modification_result,
                )

                return self._build_result(
                    status="failed",
                    proposal_id=proposal_id,
                    errors=errors,
                    timing=timing,
                    pipeline_history=pipeline_history
                )

            modified_file_path = spec.file_path
            timing["phase2_modification"] = time.time() - phase_start
            pipeline_history[-1]["status"] = "success"
            pipeline_history[-1]["duration"] = timing["phase2_modification"]
            pipeline_history[-1]["details"] = {
                "modified_file": modified_file_path,
                "backup_path": self.backup_path
            }

            # ========================================
            # FASE 3: Test Generator & Validator
            # ========================================
            current_phase = 3
            phase_start = time.time()
            pipeline_history.append({
                "phase": 3,
                "name": "TestGenerator",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })

            validation_result = self.test_generator.generate_and_validate(spec, modified_file_path)

            timing["phase3_validation"] = time.time() - phase_start
            pipeline_history[-1]["duration"] = timing["phase3_validation"]
            pipeline_history[-1]["details"] = {
                "new_test_status": validation_result.get("new_test_status"),
                "regression_status": validation_result.get("regression_status"),
                "coverage_percentage": validation_result.get("coverage_percentage"),
                "overall_status": validation_result.get("overall_status")
            }

            if validation_result.get("overall_status") != "ready":
                pipeline_history[-1]["status"] = "failed"
                errors.append({
                    "phase": 3,
                    "type": "validation_failed",
                    "message": "Validación de tests falló",
                    "details": validation_result
                })

                if self.auto_rollback:
                    self._rollback(spec.file_path)
                    pipeline_history.append({
                        "phase": "rollback",
                        "name": "Rollback",
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                        "details": {"backup_restored": True}
                    })

                cache_cleanup = self._cleanup_session_cache(proposal_text, proposal_id)
                pipeline_history.append({
                    "phase": "cleanup",
                    "name": "RedisCacheCleanup",
                    "status": "success" if cache_cleanup["deleted"] >= 0 else "failed",
                    "timestamp": datetime.now().isoformat(),
                    "details": cache_cleanup
                })

                self._log_error_to_bridge(
                    proposal_id=proposal_id,
                    phase=3,
                    error_type="validation_failed",
                    message="Validation failed",
                    details=validation_result,
                )

                return self._build_result(
                    status="failed",
                    proposal_id=proposal_id,
                    test_results=validation_result,
                    errors=errors,
                    timing=timing,
                    pipeline_history=pipeline_history
                )

            pipeline_history[-1]["status"] = "success"

            # ========================================
            # FASE 4: Git Automator
            # ========================================
            current_phase = 4
            phase_start = time.time()
            pipeline_history.append({
                "phase": 4,
                "name": "GitAutomator",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            })

            files_changed = [modified_file_path]
            if validation_result.get("new_test_path"):
                files_changed.append(validation_result["new_test_path"])

            branch_name = self.git_automator.create_feature_branch(proposal_id)
            commit_hash = self.git_automator.commit_changes(spec, files_changed)

            timing["phase4_git"] = time.time() - phase_start
            pipeline_history[-1]["status"] = "success"
            pipeline_history[-1]["duration"] = timing["phase4_git"]
            pipeline_history[-1]["details"] = {
                "branch_name": branch_name,
                "commit_hash": commit_hash,
                "files_committed": files_changed
            }

            return self._build_result(
                status="success",
                proposal_id=proposal_id,
                branch_name=branch_name,
                commit_hash=commit_hash,
                test_results=validation_result,
                timing=timing,
                pipeline_history=pipeline_history
            )

        except Exception as e:
            error_payload = {
                "phase": current_phase if current_phase else "unknown",
                "type": type(e).__name__,
                "message": str(e)
            }
            errors.append(error_payload)

            if spec and self.backup_path and self.auto_rollback and current_phase >= 2:
                try:
                    self._rollback(spec.file_path)
                    pipeline_history.append({
                        "phase": "rollback",
                        "name": "Rollback",
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                        "details": {"backup_restored": True}
                    })
                except Exception as rollback_error:
                    errors.append({
                        "phase": "rollback",
                        "type": type(rollback_error).__name__,
                        "message": str(rollback_error)
                    })

            if current_phase == 2:
                deleted = self._cleanup_feature_branch(proposal_id)
                pipeline_history.append({
                    "phase": "cleanup",
                    "name": "BranchCleanup",
                    "status": "success" if deleted else "skipped",
                    "timestamp": datetime.now().isoformat(),
                    "details": {"branch_deleted": deleted}
                })
            elif current_phase >= 3:
                cache_cleanup = self._cleanup_session_cache(proposal_text, proposal_id)
                pipeline_history.append({
                    "phase": "cleanup",
                    "name": "RedisCacheCleanup",
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "details": cache_cleanup
                })

            self._log_error_to_bridge(
                proposal_id=proposal_id,
                phase=current_phase if current_phase else -1,
                error_type=type(e).__name__,
                message=str(e),
                details={"errors": errors},
            )

            return self._build_result(
                status="failed",
                proposal_id=proposal_id,
                errors=errors,
                timing=timing,
                pipeline_history=pipeline_history
            )

    def _resolve_project_path(self, file_path: str) -> Optional[Path]:
        path = Path(file_path)
        resolved = path.resolve() if path.is_absolute() else (self.working_dir / path).resolve()
        try:
            resolved.relative_to(self.working_dir)
            return resolved
        except ValueError:
            return None

    def _resolve_spec_file_path(self, spec: TechnicalSpec, proposal_text: str):
        resolved = self._resolve_project_path(spec.file_path)
        if resolved and resolved.exists():
            spec.file_path = str(resolved.relative_to(self.working_dir))
            return

        inferred = self._infer_target_file(spec, proposal_text)
        if inferred is not None:
            spec.file_path = str(inferred.relative_to(self.working_dir))
            return

        raise CodeCraftError(f"No target file found for proposal within working_dir: {spec.file_path}")

    def _infer_target_file(self, spec: TechnicalSpec, proposal_text: str) -> Optional[Path]:
        py_files = [
            p for p in self.working_dir.rglob("*.py")
            if ".git" not in p.parts and "generated" not in p.parts
        ]

        if spec.class_name:
            class_marker = f"class {spec.class_name}"
            for file_path in py_files:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if class_marker in content:
                    return file_path

        if spec.attribute_name:
            attr_marker = spec.attribute_name
            for file_path in py_files:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if attr_marker in content:
                    return file_path

        tokens = [tok for tok in proposal_text.lower().split() if len(tok) >= 5]
        for file_path in py_files:
            stem = file_path.stem.lower()
            if any(tok in stem for tok in tokens):
                return file_path

        if len(py_files) == 1:
            return py_files[0]

        return None

    def _enrich_spec_from_source(self, spec: TechnicalSpec, proposal_text: str):
        resolved = self._resolve_project_path(spec.file_path)
        if resolved is None or not resolved.exists() or resolved.suffix != ".py":
            return

        try:
            code = resolved.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(code)
        except Exception:
            return

        if not spec.class_name:
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    spec.class_name = node.name
                    break

        if spec.attribute_name and spec.old_value is None:
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute) and target.attr == spec.attribute_name:
                            spec.old_value = node.value.value
                            break
                        if isinstance(target, ast.Name) and target.id == spec.attribute_name:
                            spec.old_value = node.value.value
                            break
                if spec.old_value is not None:
                    break

    def _cleanup_feature_branch(self, proposal_id: str) -> bool:
        try:
            return self.git_automator.delete_feature_branch(proposal_id, force=True)
        except Exception as exc:
            logger.warning("Branch cleanup failed for %s: %s", proposal_id, exc)
            return False

    def _cleanup_session_cache(self, proposal_text: str, proposal_id: str) -> Dict[str, Any]:
        deleted = 0
        errors = []

        redis_client = getattr(self.parser, "redis", None)
        if not redis_client:
            return {"deleted": 0, "errors": ["redis_not_available"]}

        try:
            if not redis_client.is_connected():
                return {"deleted": 0, "errors": ["redis_disconnected"]}

            parse_cache_key = self.parser._get_cache_key(proposal_text)
            for key in [
                parse_cache_key,
                f"codecraft:session:{proposal_id}",
                f"codecraft:session:{proposal_id}:spec",
            ]:
                if redis_client.delete_system_state(key):
                    deleted += 1

            deleted += redis_client.delete_keys_by_pattern(f"state:codecraft:session:{proposal_id}:*")
        except Exception as exc:
            errors.append(str(exc))

        return {"deleted": deleted, "errors": errors}

    def _log_error_to_bridge(
        self,
        proposal_id: str,
        phase: int,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        bridge_path = self.working_dir / "aipha_memory" / "evolutionary" / "bridge.jsonl"
        bridge_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "timestamp": datetime.now().isoformat(),
            "event": "codecraft_pipeline_error",
            "proposal_id": proposal_id,
            "phase": phase,
            "error_type": error_type,
            "message": message,
            "details": details or {},
        }

        with bridge_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _create_backup(self, file_path: str) -> Optional[str]:
        source = self._resolve_project_path(file_path)
        if source is None or not source.exists():
            return None

        backup_dir = self.working_dir / "aipha_memory" / "temporary" / "ast_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{source.stem}_{timestamp}_{uuid.uuid4().hex[:8]}{source.suffix}.bak"
        backup_path = backup_dir / backup_filename

        shutil.copy2(source, backup_path)
        return str(backup_path)

    def _rollback(self, file_path: str) -> bool:
        if not self.backup_path:
            return False

        source = Path(self.backup_path)
        target = self._resolve_project_path(file_path)
        if target is None:
            return False

        if source.exists():
            shutil.copy2(source, target)
            return True
        return False

    def _build_result(
        self,
        status: str,
        proposal_id: str,
        branch_name: str = None,
        commit_hash: str = None,
        test_results: Dict = None,
        errors: list = None,
        timing: dict = None,
        pipeline_history: list = None
    ) -> Dict:
        result = {
            "status": status,
            "proposal_id": proposal_id,
            "timestamp": datetime.now().isoformat(),
            "errors": errors or [],
            "timing": timing or {},
            "pipeline_history": pipeline_history or []
        }

        if branch_name:
            result["branch_name"] = branch_name

        if commit_hash:
            result["commit_hash"] = commit_hash

        if test_results:
            result["test_results"] = test_results

        result["changes_summary"] = {
            "total_phases": 4,
            "phases_completed": len([p for p in (pipeline_history or []) if p.get("status") == "success"]),
            "rollback_performed": any(p.get("phase") == "rollback" for p in (pipeline_history or []))
        }

        return result

    def get_status(self) -> Dict:
        try:
            git_status = self.git_automator.get_status()
        except Exception:
            git_status = {"error": "No es un repositorio Git"}

        return {
            "status": "available",
            "current_proposal_id": self.current_proposal_id,
            "working_dir": str(self.working_dir),
            "auto_rollback": self.auto_rollback,
            "git_status": git_status,
            "components": {
                "parser": "ready",
                "modifier": "ready",
                "test_generator": "ready",
                "git_automator": "ready"
            }
        }


def execute_pipeline(proposal_text: str, proposal_id: str = None, working_dir: str = ".") -> Dict:
    orchestrator = CodeCraftOrchestrator(working_dir)
    return orchestrator.execute_pipeline(proposal_text, proposal_id)
