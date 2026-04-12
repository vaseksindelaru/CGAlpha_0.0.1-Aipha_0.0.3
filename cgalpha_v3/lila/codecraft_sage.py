"""
CGAlpha v3 — CodeCraft Sage (Sección 2.7 NORTH STAR)
===================================================
El motor de evolución del sistema. Transforma TechnicalSpecs en 
commits trazables tras pasar la Triple Barrera de Tests.
"""

import os
import subprocess
import json
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.lila.llm.proposer import TechnicalSpec

logger = logging.getLogger("codecraft")

@dataclass
class ExecutionResult:
    status: str             # "COMMITTED" | "REJECTED_NO_COMMIT" | "ERROR"
    proposal_id: str
    commit_sha: Optional[str] = None
    test_report_path: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()

class CodeCraftSage(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  LILA CORE — CodeCraft Sage                           ║
    ║  Pipeline de Evolución (Contrato §2.7 North Star)    ║
    ╠═══════════════════════════════════════════════════════╣
    ║  1. Parser      : TechnicalSpec -> Plan               ║
    ║  2. Modifier    : Aplicación de cambios (git feature) ║
    ║  3. TestBarrier : Triple Barrera (Pytest)             ║
    ║  4. GitPersist  : Commit con metadata causal          ║
    ║  5. CLIExpose   : Documentación de cambios            ║
    ║  6. AutoLoop    : Feedback a Proposer/Library         ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        self.project_root = os.getcwd()
        self.artifact_dir = os.path.join(self.project_root, "cgalpha_v3/data/codecraft_artifacts")
        os.makedirs(self.artifact_dir, exist_ok=True)

    def execute_proposal(self, spec: TechnicalSpec, ghost_approved: bool, human_approved: bool) -> ExecutionResult:
        """
        Punto de entrada principal para la ejecución de una propuesta aprobada.
        """
        # --- PRECONDICIONES ---
        if not (ghost_approved and human_approved):
            return ExecutionResult(status="ERROR", proposal_id="NA", error_message="Falta aprobación Dual (Ghost+Human)")
        
        if spec.causal_score_est < self.manifest.causal_score:
            return ExecutionResult(status="ERROR", proposal_id="NA", error_message=f"Causal score {spec.causal_score_est} < {self.manifest.causal_score}")

        logger.info(f"🚀 Iniciando CodeCraft para propuesta: {spec.target_attribute} ({spec.new_value})")
        
        try:
            # FASE 1: Parser
            plan = self._create_execution_plan(spec)
            
            # FASE 2: Modifier (Git Feature Branch + Patch)
            branch_name = f"feature/codecraft_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self._setup_feature_branch(branch_name)
            self._apply_patch(spec)
            
            # FASE 3: TestBarrier (Triple Barrera)
            test_report = self._run_test_barrier(spec.target_file)
            
            if not test_report["all_passed"]:
                self._rollback_to_main()
                logger.warning("❌ TestBarrier fallido. Realizando rollback.")
                return ExecutionResult(
                    status="REJECTED_NO_COMMIT",
                    proposal_id=spec.target_attribute,
                    error_message=f"Falla en tests: {test_report['summary']}"
                )

            # FASE 4: GitPersist
            commit_sha = self._persist_commit(spec, branch_name, test_report)
            
            # FASE 5 & 6: Artifacts & Feedback
            self._publish_artifacts(spec, test_report, commit_sha)
            
            return ExecutionResult(
                status="COMMITTED",
                proposal_id=spec.target_attribute,
                commit_sha=commit_sha
            )

        except Exception as e:
            logger.error(f"💥 Error crítico en CodeCraft: {str(e)}")
            self._rollback_to_main()
            return ExecutionResult(status="ERROR", proposal_id=spec.target_attribute, error_message=str(e))

    def _create_execution_plan(self, spec: TechnicalSpec) -> Dict:
        # En v3, el plan es el mismo TechnicalSpec enriquecido
        return asdict(spec)

    def _setup_feature_branch(self, branch_name: str):
        subprocess.run(["git", "checkout", "-b", branch_name], check=True, capture_output=True)

    def _apply_patch(self, spec: TechnicalSpec):
        """
        Aplica el cambio al archivo. 
        """
        import re
        with open(spec.target_file, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        found = False
        
        # Patrón para asignaciones: variable = valor (con opcional auto-reemplazo)
        # Maneja casos como self.min_confidence = 0.70
        pattern = rf"(\b{spec.target_attribute}\b\s*=\s*)([^#\n]+)"
        
        for line in lines:
            if not found and re.search(pattern, line):
                new_line = re.sub(pattern, rf"\g<1>{spec.new_value}", line)
                new_lines.append(new_line)
                found = True
                logger.info(f"✅ Parche aplicado a {spec.target_attribute}: {spec.old_value} -> {spec.new_value}")
            else:
                new_lines.append(line)
        
        if not found:
            # Si no es una asignación directa, intentamos reemplazo de texto crudo (fallback)
            logger.warning(f"⚠️ No se encontró asignación para {spec.target_attribute}. Usando reemplazo crudo.")
            content = "".join(lines)
            old_str = str(spec.old_value)
            new_str = str(spec.new_value)
            content = content.replace(old_str, new_str)
            new_lines = [content]

        with open(spec.target_file, 'w') as f:
            f.writelines(new_lines)

    def _run_test_barrier(self, target_file: str) -> Dict:
        """Triple Barrera: Tests de unidad + Integración + No-Leakage."""
        # Por ahora ejecutamos pytest sobre el directorio de tests
        result = subprocess.run(["python", "-m", "pytest", "cgalpha_v3/tests/", "-q"], capture_output=True, text=True)
        
        return {
            "all_passed": result.returncode == 0,
            "summary": result.stdout.split('\n')[-2] if result.stdout else "No output",
            "full_log": result.stdout
        }

    def _persist_commit(self, spec: TechnicalSpec, branch: str, report: Dict) -> str:
        subprocess.run(["git", "add", spec.target_file], check=True)
        msg = f"feat(evolution): {spec.reason} [ΔCausal: {spec.causal_score_est}]"
        subprocess.run(["git", "commit", "-m", msg], check=True)
        
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()

    def _rollback_to_main(self):
        subprocess.run(["git", "checkout", "main"], check=False)
        subprocess.run(["git", "stash"], check=False)

    def _publish_artifacts(self, spec: TechnicalSpec, report: Dict, sha: str):
        art_id = f"cc_{sha[:8]}"
        path = os.path.join(self.artifact_dir, f"{art_id}.json")
        with open(path, 'w') as f:
            json.dump({
                "spec": asdict(spec),
                "test_report": report,
                "commit_sha": sha,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="CodeCraftSage",
            category="evolution",
            function="Ejecutor de cambios automáticos con Triple Barrera de Tests y persistencia Git",
            inputs=["TechnicalSpec", "GhostApproval", "HumanApproval"],
            outputs=["ExecutionResult", "GitCommit"],
            causal_score=0.75 # Umbral mínimo para autorizar cambios
        )
        return cls(manifest)
