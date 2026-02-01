"""
Atomic Update System - Protocolo de cambios atómicos para Aipha.
Implementa el protocolo de 5 pasos: Backup -> Diff -> Test -> Commit -> Rollback.
"""
import logging
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    CONFIG = "config"
    CODE = "code"
    HYBRID = "hybrid"

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass
class ChangeProposal:
    proposal_id: str
    title: str
    target_component: str
    impact_justification: str
    estimated_difficulty: str
    diff_content: str
    test_plan: str
    metrics: Dict[str, Any]
    priority: str = "normal"
    estimated_complexity: str = "moderate"
    status: ApprovalStatus = ApprovalStatus.PENDING

class AtomicUpdateSystem:
    """
    Implementa el protocolo de 5 pasos para actualizaciones seguras:
    1. Backup: Copia de seguridad del archivo original.
    2. Diff: Aplicación de los cambios propuestos.
    3. Test: Ejecución de la suite de pruebas.
    4. Commit: Consolidación del cambio si los tests pasan.
    5. Rollback: Restauración del backup si algo falla.
    """
    
    def __init__(self, sentinel):
        self.sentinel = sentinel
        self.backup_path: Optional[Path] = None
        self.target_path: Optional[Path] = None

    def execute(self, proposal: ChangeProposal) -> tuple:
        """
        Ejecuta el ciclo completo de actualización atómica.
        """
        self.target_path = Path(proposal.target_component.replace(".", "/") + ".py")
        
        logger.info(f"Iniciando protocolo atómico para {proposal.proposal_id} en {self.target_path}")
        
        try:
            # 1. Backup
            self._step_backup()
            
            # 2. Diff
            self._step_apply_diff(proposal.diff_content)
            
            # 3. Test
            test_passed = self._step_test(proposal.test_plan)
            
            if test_passed:
                # 4. Commit
                self._step_commit()
                msg = f"Protocolo completado: {proposal.proposal_id} aplicado y verificado."
                logger.info(msg)
                self._record_event("ATOMIC_COMMIT", proposal.proposal_id, {"msg": msg})
                return (True, msg)
            else:
                # 5. Rollback
                self._step_rollback()
                msg = f"Protocolo fallido: Tests no pasaron. Rollback ejecutado para {proposal.proposal_id}."
                logger.warning(msg)
                self._record_event("ATOMIC_ROLLBACK", proposal.proposal_id, {"msg": msg, "reason": "tests_failed"})
                return (False, msg)
                
        except Exception as e:
            if self.backup_path and self.backup_path.exists():
                self._step_rollback()
            msg = f"Error crítico en protocolo atómico: {str(e)}"
            logger.error(msg)
            self._record_event("ATOMIC_ERROR", proposal.proposal_id, {"error": str(e)})
            return (False, msg)

    def _step_backup(self):
        """Paso 1: Crear backup temporal."""
        if not self.target_path.exists():
            raise FileNotFoundError(f"No se encuentra el archivo objetivo: {self.target_path}")
        
        self.backup_path = self.target_path.with_suffix(".py.bak")
        shutil.copy2(self.target_path, self.backup_path)
        logger.info(f"Backup creado: {self.backup_path}")

    def _step_apply_diff(self, diff_content: str):
        """Paso 2: Aplicar cambios al archivo (Soporta reemplazo in-situ)."""
        content = self.target_path.read_text()
        lines = content.splitlines()
        
        diff_lines = diff_content.splitlines()
        i = 0
        while i < len(diff_lines):
            d_line = diff_lines[i]
            
            if d_line.startswith("- "):
                to_remove = d_line[2:].strip()
                # Buscar la línea en el archivo original
                found_idx = -1
                for idx, l in enumerate(lines):
                    if to_remove in l:
                        found_idx = idx
                        break
                
                if found_idx != -1:
                    # Si la siguiente línea del diff es +, es un reemplazo
                    if i + 1 < len(diff_lines) and diff_lines[i+1].startswith("+ "):
                        to_add = diff_lines[i+1][2:]
                        lines[found_idx] = to_add
                        i += 1 # Saltar la línea +
                    else:
                        # Es solo borrado
                        lines.pop(found_idx)
            elif d_line.startswith("+ "):
                # Adición pura (append al final por defecto si no es parte de un reemplazo)
                lines.append(d_line[2:])
            
            i += 1
        
        self.target_path.write_text("\n".join(lines) + "\n")
        logger.info("Diff aplicado al archivo objetivo.")

    def _step_test(self, test_plan: str) -> bool:
        """Paso 3: Ejecutar pruebas."""
        # Extraer el comando de test del plan (ej: "pytest tests/test_file.py")
        # Para la Fase 3, asumimos que el test_plan contiene la ruta del test
        test_file = test_plan.split()[-1] if " " in test_plan else test_plan
        
        logger.info(f"Ejecutando tests: {test_file}")
        result = subprocess.run(
            ["pytest", test_file, "-v"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("Tests pasaron exitosamente.")
            return True
        else:
            logger.warning(f"Tests fallaron:\n{result.stdout}")
            return False

    def _step_commit(self):
        """Paso 4: Consolidar cambios (borrar backup)."""
        if self.backup_path and self.backup_path.exists():
            self.backup_path.unlink()
            logger.info("Commit: Backup eliminado.")

    def _step_rollback(self):
        """Paso 5: Restaurar desde backup."""
        if self.backup_path and self.backup_path.exists():
            shutil.move(self.backup_path, self.target_path)
            logger.info("Rollback: Archivo original restaurado.")

    def _record_event(self, event_type: str, proposal_id: str, details: Dict):
        """Registra el evento en el ContextSentinel."""
        self.sentinel.add_action(
            agent="AtomicUpdateSystem",
            action_type=event_type,
            proposal_id=proposal_id,
            details=details
        )
