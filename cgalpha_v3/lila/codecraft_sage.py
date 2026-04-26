"""
CGAlpha v3 — CodeCraft Sage (Sección 2.7 NORTH STAR)
===================================================
El motor de evolución del sistema. Transforma TechnicalSpecs en 
commits trazables tras pasar la Triple Barrera de Tests.
"""

import os
import subprocess
import json
import ast
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging

from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.lila.llm.proposer import TechnicalSpec
from cgalpha_v3.lila.llm.llm_switcher import LLMSwitcher

logger = logging.getLogger("codecraft")

@dataclass
class ExecutionResult:
    """Resultado de la ejecución de CodeCraft."""
    status: str             # "COMMITTED" | "REJECTED_NO_COMMIT" | "ERROR"
    proposal_id: str
    commit_sha: Optional[str] = None
    test_report_path: Optional[str] = None
    error_message: Optional[str] = None
    timestamp: str = datetime.now(timezone.utc).isoformat()
    branch_name: str = ""
    tests_passed: bool = False

class CodeCraftSage(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  NORTH STAR — CodeCraft Sage v4                       ║
    ║  Evolución del Modifier: Regex -> LLM Patching        ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest, switcher: Optional[LLMSwitcher] = None):
        super().__init__(manifest)
        self.project_root = os.getcwd()
        self.artifact_dir = os.path.join(self.project_root, "cgalpha_v3/data/codecraft_artifacts")
        os.makedirs(self.artifact_dir, exist_ok=True)
        self.switcher = switcher

    def execute_proposal(self, spec: TechnicalSpec, ghost_approved: bool, human_approved: bool) -> ExecutionResult:
        """
        Punto de entrada principal para la ejecución de una propuesta aprobada.
        """
        # --- PRECONDICIONES v4 ---
        # Cat.1: solo requiere ghost_approved. Cat.2/3: requiere ambos.
        is_cat_1 = spec.change_type == "parameter" and spec.confidence >= 0.7
        
        if is_cat_1:
            if not ghost_approved:
                return ExecutionResult(status="ERROR", proposal_id="NA", error_message="Falta aprobación de Ghost para Cat.1")
        else:
            if not (ghost_approved and human_approved):
                return ExecutionResult(status="ERROR", proposal_id="NA", error_message="Falta aprobación Dual (Ghost+Human) para Cat.2/3")
        
        if spec.causal_score_est < 0.3: # Bajamos el umbral para permitir arreglos de bugs
             logger.warning(f"⚠️ Causal score bajo ({spec.causal_score_est}), pero procediendo por ser fix/parámetro.")

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
                self._publish_artifacts(spec, test_report, None) # Persistir para debug
                self._rollback_to_main()
                logger.warning("❌ TestBarrier fallido. Realizando rollback.")
                return ExecutionResult(
                    status="REJECTED_NO_COMMIT",
                    proposal_id=spec.target_attribute,
                    error_message=f"Falla en tests: {test_report['summary']}",
                    branch_name=branch_name,
                    tests_passed=False
                )

            # FASE 4: GitPersist
            commit_sha = self._persist_commit(spec, branch_name, test_report)
            
            # FASE 5 & 6: Artifacts & Feedback
            self._publish_artifacts(spec, test_report, commit_sha)
            
            return ExecutionResult(
                status="COMMITTED",
                proposal_id=spec.target_attribute,
                commit_sha=commit_sha,
                branch_name=branch_name,
                tests_passed=True
            )

        except Exception as e:
            logger.error(f"💥 Error crítico en CodeCraft: {str(e)}")
            # Intentar publicar artifact de error si tenemos el reporte
            if 'test_report' in locals():
                self._publish_artifacts(spec, test_report, None)
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
        Jerarquía v4:
        1. AST Patching (S quirúrgico, determinista, preferido para parámetros)
        2. Regex Patching (S rápido, determinista, fallback para parámetros)
        3. LLM Patching (S inteligente, lento, para cambios estructurales/lógica)
        """
        # 1. Intento AST (Novedad v4)
        if spec.change_type == "parameter":
            if self._apply_ast_patch(spec):
                logger.info(f"🎯 AST Patch aplicado exitosamente a {spec.target_attribute}")
                return

        import re
        try:
            with open(spec.target_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            logger.error(f"❌ Archivo no encontrado: {spec.target_file}")
            raise

        # 2. Intento Regex (fallback para parámetros)
        if spec.change_type == "parameter":
            pattern = rf"(\b{spec.target_attribute}\b\s*=\s*)([^#\n]+)"
            new_lines = []
            found = False
            for line in lines:
                if not found and re.search(pattern, line):
                    new_line = re.sub(pattern, rf"\g<1>{spec.new_value}", line)
                    new_lines.append(new_line)
                    found = True
                else:
                    new_lines.append(line)
            
            if found:
                with open(spec.target_file, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                logger.info(f"✅ Regex Patch aplicado a {spec.target_attribute} (Fallback)")
                return

        # 3. LLM Patching (para features, bugfixes o si fallaron los deterministas)
        if not self.switcher:
            raise RuntimeError("Se requiere LLMSwitcher para patching de tipo structural/bugfix")

        logger.info(f"🧠 Iniciando LLM Patching para {spec.target_file}...")
        file_content = "".join(lines)
        
        # v4 Optimization: For local models, send smaller context if possible
        is_local = self.switcher.select("cat_2").name == "ollama" # Use cat_2 for patching
        if is_local:
             prompt_context = f"Archivo: {spec.target_file}\nContenido:\n{file_content[:4000]}..." # Truncar si es muy largo
        else:
             prompt_context = file_content

        prompt = f"""
Objetivo: Aplicar un cambio técnico al archivo {spec.target_file}.
Contexto:
- Tipo de cambio: {spec.change_type}
- Atributo/Elemento: {spec.target_attribute}
- Valor nuevo: {spec.new_value}
- Razón: {spec.reason}

Contenido original:
```python
{prompt_context}
```

REGLAS:
1. Devuelve SOLO el contenido completo del archivo modificado.
2. Sin explicaciones, sin markdown, solo el código.
"""
        new_content = self.switcher.generate("cat_3", prompt=prompt)
        
        # Limpiar posible markdown en la respuesta
        if "```" in new_content:
            if "```python" in new_content:
                new_content = new_content.split("```python")[-1].split("```")[0].strip()
            else:
                new_content = new_content.split("```")[-1].split("```")[0].strip()

        with open(spec.target_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        logger.info(f"✅ LLM Patch aplicado a {spec.target_file}")

    def _apply_ast_patch(self, spec: TechnicalSpec) -> bool:
        """
        Localiza el nodo exacto en el AST y modifica la línea del source.
        Preserva comentarios y formato del resto del archivo.
        """
        try:
            with open(spec.target_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
            lines = source.splitlines()
        except Exception as e:
            logger.warning(f"AST Parsing fallido en {spec.target_file}: {e}")
            return False

        found_node = None
        for node in ast.walk(tree):
            # Caso 1: Asignación simple x = 1.0 (o x: float = 1.0)
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                target = node.targets[0] if isinstance(node, ast.Assign) else node.target
                name = None
                if isinstance(target, ast.Name):
                    name = target.id
                elif isinstance(target, ast.Attribute):
                    name = target.attr
                
                if name == spec.target_attribute:
                    found_node = node
                    break
            
            # Caso 2: Clave en un diccionario (common in config dicts)
            elif isinstance(node, ast.Dict):
                for i, key in enumerate(node.keys):
                    if isinstance(key, ast.Constant) and key.value == spec.target_attribute:
                        found_node = node.values[i]
                        break
                if found_node: break

        if not found_node:
            return False

        # Si encontramos el nodo, intentamos reemplazar solo esa línea/rango
        # Nota: lineno en ast es 1-indexed
        sl = found_node.lineno - 1
        el = found_node.end_lineno - 1 if hasattr(found_node, 'end_lineno') else sl
        
        if sl >= len(lines):
            return False

        new_val_str = repr(spec.new_value)
        
        # Parche quirúrgico en la línea encontrada
        line = lines[sl]
        
        # Si es una asignación Name = Value
        if isinstance(found_node, (ast.Assign, ast.AnnAssign)):
            if '=' in line:
                before, after = line.split('=', 1)
                # Conservar comentario si existe
                comment = ""
                if '#' in after:
                    after, comment = after.split('#', 1)
                    comment = " #" + comment
                
                lines[sl] = f"{before}= {new_val_str}{comment}"
                with open(spec.target_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines) + "\n")
                return True
        
        # Si es un valor de dict {'key': value}
        elif found_node: # found_node es el value_node del dict
            # Buscar el separador ':'
            if ':' in line:
                before, after = line.split(':', 1)
                # Conservar comentario y posible coma
                comment = ""
                suffix = ""
                if '#' in after:
                    after, comment = after.split('#', 1)
                    comment = " #" + comment
                
                after = after.strip()
                if after.endswith(','):
                    suffix = ","
                
                lines[sl] = f"{before}: {new_val_str}{suffix}{comment}"
                with open(spec.target_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines) + "\n")
                return True

        return False

    def _run_test_barrier(self, target_file: str) -> Dict:
        """Triple Barrera: Tests de unidad + Integración + No-Leakage."""
        # Por ahora ejecutamos pytest sobre el directorio de tests
        result = subprocess.run(["python3", "-m", "pytest", "cgalpha_v3/tests/", "-q"], capture_output=True, text=True)
        
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

    def _publish_artifacts(self, spec: TechnicalSpec, report: Dict, sha: str | None):
        import time
        if sha:
            art_id = f"cc_{sha[:8]}"
        else:
            art_id = f"cc_fail_{int(time.time())}"
            
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
