"""
ContextSentinel - Sistema de memoria persistente entre ejecuciones
FASE 1 - AIPHA 0.0.2

Propósito:
- Guardar acciones (append-only en JSONL)
- Guardar estado (mutable en JSON)
- Recuperar información entre ejecuciones

Archivos:
- current_state.json: Estado mutable (key-value)
- action_history.jsonl: Histórico append-only
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Action:
    """Representa una acción registrada en el historial"""
    timestamp: str
    agent: str
    action_type: str
    proposal_id: Optional[str] = None
    status: str = "success"
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario (para JSONL)"""
        return asdict(self)

class ContextSentinel:
    """
    Memoria persistente del sistema Aipha.
    """

    def __init__(self, storage_root: Optional[Path] = None):
        """
        Inicializar ContextSentinel.
        """
        if storage_root is None:
            storage_root = Path.cwd() / "memory"
        
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

        # Structure Update: Use 'operational' subdirectory
        self.operational_dir = self.storage_root / "operational"
        self.operational_dir.mkdir(parents=True, exist_ok=True)
        
        self.action_history_file = self.operational_dir / "action_history.jsonl"
        self.state_file = self.operational_dir / "current_state.json"
        
        logger.info(f"ContextSentinel inicializado en: {self.storage_root}")
        
        # Inicializar archivos si no existen
        self._initialize_files()

    def _initialize_files(self) -> None:
        """Crear archivos de almacenamiento si no existen."""
        if not self.action_history_file.exists():
            self.action_history_file.touch()
        
        if not self.state_file.exists():
            self.state_file.write_text(json.dumps({}, indent=2))

    def add_memory(self, key: str, value: Dict[str, Any]) -> None:
        """Guardar en memoria (estado mutable)"""
        try:
            current_state = self._load_state()
            current_state[key] = value
            self.state_file.write_text(json.dumps(current_state, indent=2))
            
            self.add_action(
                agent="ContextSentinel",
                action_type="MEMORY_ADD",
                details={"key": key}
            )
        except Exception as e:
            logger.error(f"Error guardando memoria [{key}]: {e}")
            raise

    def query_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Recuperar de memoria"""
        try:
            state = self._load_state()
            return state.get(key)
        except Exception as e:
            logger.error(f"Error leyendo memoria [{key}]: {e}")
            return None

    def get_memory_keys(self) -> List[str]:
        """Obtener todas las claves almacenadas"""
        try:
            state = self._load_state()
            return list(state.keys())
        except Exception as e:
            logger.error(f"Error listando claves: {e}")
            return []

    def add_action(self, agent: str, action_type: str, proposal_id: Optional[str] = None, 
                   status: str = "success", details: Optional[Dict[str, Any]] = None) -> None:
        """Registrar acción (append-only)"""
        try:
            action = Action(
                timestamp=datetime.now(timezone.utc).isoformat(),
                agent=agent,
                action_type=action_type,
                proposal_id=proposal_id,
                status=status,
                details=details or {}
            )
            with open(self.action_history_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(action.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Error registrando acción: {e}")
            raise

    def get_action_history(self) -> List[Dict[str, Any]]:
        """Recuperar historial completo"""
        actions = []
        try:
            if not self.action_history_file.exists():
                return actions
            with open(self.action_history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            actions.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            return actions
        except Exception as e:
            logger.error(f"Error leyendo historial: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Obtener estadísticas"""
        history = self.get_action_history()
        memory_keys = self.get_memory_keys()
        
        actions_by_type = {}
        actions_by_agent = {}
        
        for action in history:
            atype = action.get('action_type', 'UNKNOWN')
            agent = action.get('agent', 'UNKNOWN')
            actions_by_type[atype] = actions_by_type.get(atype, 0) + 1
            actions_by_agent[agent] = actions_by_agent.get(agent, 0) + 1
            
        return {
            "total_actions": len(history),
            "actions_by_type": actions_by_type,
            "actions_by_agent": actions_by_agent,
            "memory_keys_count": len(memory_keys),
            "memory_keys": memory_keys
        }

    def get_proposal(self, proposal_id: str) -> Optional[Any]:
        """Recuperar una propuesta específica por ID con robustez"""
        proposals_file = self.storage_root.parent / "memory" / "proposals.jsonl"
        if not proposals_file.exists():
            return None
        
        try:
            with open(proposals_file, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    try:
                        data = json.loads(clean_line)
                        if data.get('proposal_id') == proposal_id:
                            # Mock object for compatibility
                            class Proposal:
                                def __init__(self, d):
                                    self.id = d.get('proposal_id')
                                    self.title = d.get('reason', 'Sin título')
                                    self.target_component = d.get('component')
                                    self.parameter = d.get('parameter')
                                    self.new_value = d.get('new_value')
                                    self.impact_justification = d.get('reason')
                            return Proposal(data)
                    except json.JSONDecodeError:
                        continue
            return None
        except Exception as e:
            logger.debug(f"Error discreto leyendo propuesta {proposal_id}: {e}")
            return None

    def get_last_approved_proposal(self) -> Optional[Any]:
        """Obtener la última propuesta aprobada o pendiente de evaluación con robustez"""
        proposals_file = self.storage_root.parent / "memory" / "proposals.jsonl"
        if not proposals_file.exists():
            return None
        
        try:
            last_valid = None
            with open(proposals_file, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    try:
                        data = json.loads(clean_line)
                        # Consideramos válidas las que no han sido aplicadas aún
                        if not data.get('applied', False):
                            last_valid = data
                    except json.JSONDecodeError:
                        continue
            
            if last_valid:
                return self.get_proposal(last_valid.get('proposal_id'))
            return None
        except Exception as e:
            logger.debug(f"Error discreto buscando última propuesta: {e}")
            return None

    def _load_state(self) -> Dict[str, Any]:
        """Cargar estado desde JSON"""
        try:
            if not self.state_file.exists():
                return {}
            content = self.state_file.read_text()
            return json.loads(content) if content.strip() else {}
        except json.JSONDecodeError:
            return {}

    def update_proposal_status(self, proposal_id: str, status: str) -> bool:
        """Actualizar el estado de una propuesta en proposals.jsonl"""
        proposals_file = self.storage_root.parent / "memory" / "proposals.jsonl"
        if not proposals_file.exists():
            return False
        
        try:
            proposals = []
            updated = False
            with open(proposals_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    data = json.loads(line)
                    if data.get('proposal_id') == proposal_id:
                        data['status'] = status
                        updated = True
                    proposals.append(data)
            
            if updated:
                with open(proposals_file, 'w', encoding='utf-8') as f:
                    for p in proposals:
                        f.write(json.dumps(p) + '\n')
                return True
            return False
        except Exception as e:
            logger.error(f"Error actualizando estado de propuesta: {e}")
            return False

    def log_event(self, event_data: Dict[str, Any]) -> None:
        """Wrapper de compatibilidad para add_action"""
        self.add_action(
            agent="System",
            action_type=event_data.get('type', 'EVENT'),
            details=event_data
        )

def create_sentinel(storage_path: Optional[str] = None) -> ContextSentinel:
    """Factory para crear instancia"""
    return ContextSentinel(Path(storage_path) if storage_path else None)
