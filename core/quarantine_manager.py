"""
core/quarantine_manager.py - Gestor de Cuarentena

Registra parámetros fallidos y evita re-propuesta de valores problemáticos.
Implementa "Lista Negra" con expiración temporal.
"""

import json
import time
import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


@dataclass
class QuarantinedParameter:
    """Parámetro en cuarentena"""
    parameter: str
    failed_value: any
    error_reason: str
    quarantine_timestamp: float
    expiry_timestamp: float
    attempt_count: int = 1
    last_failed_at: float = None
    resolution: str = None  # Cómo resolver el problema


class QuarantineManager:
    """
    Gestor de parámetros en cuarentena
    
    Características:
    - Registra fallos de health-check
    - Previene re-proposición de valores problemáticos
    - Expiración automática (24h default)
    - Historial de intentos
    - Sugerencias de resolución
    """
    
    def __init__(self, memory_path: str = "memory"):
        self.memory_path = Path(memory_path)
        self.quarantine_file = self.memory_path / "quarantine.jsonl"
        self.quarantine_cache = []
        self.default_quarantine_duration = 24 * 3600  # 24 horas
        
        # Crear archivo si no existe
        self.quarantine_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.quarantine_file.exists():
            self.quarantine_file.touch()
        
        # Cargar quarantine actual
        self._reload_cache()
        
        logger.info(f"✅ QuarantineManager inicializado")
    
    def quarantine_parameter(
        self,
        parameter: str,
        failed_value: any,
        error_reason: str,
        resolution: str = None,
        duration_seconds: int = None
    ) -> QuarantinedParameter:
        """
        Poner parámetro en cuarentena
        
        Argumentos:
            parameter: Nombre del parámetro (ej: 'n_estimators')
            failed_value: Valor que falló (ej: 200)
            error_reason: Razón del fallo (ej: 'Out of Memory')
            resolution: Sugerencia de resolución
            duration_seconds: Duración de la cuarentena (default: 24h)
        
        Retorna:
            QuarantinedParameter: Objeto con metadata de cuarentena
        """
        
        if duration_seconds is None:
            duration_seconds = self.default_quarantine_duration
        
        now = time.time()
        expiry = now + duration_seconds
        
        # Buscar si ya existe en cuarentena
        existing = self._find_quarantined(parameter, failed_value)
        
        if existing:
            # Actualizar intento
            logger.info(
                f"⚠️ Parámetro {parameter}={failed_value} ya en cuarentena, "
                f"incrementando attempt_count"
            )
            existing.attempt_count += 1
            existing.last_failed_at = now
            existing.expiry_timestamp = expiry
            existing.error_reason = error_reason
            if resolution:
                existing.resolution = resolution
        else:
            # Crear nueva entrada
            existing = QuarantinedParameter(
                parameter=parameter,
                failed_value=failed_value,
                error_reason=error_reason,
                quarantine_timestamp=now,
                expiry_timestamp=expiry,
                attempt_count=1,
                last_failed_at=now,
                resolution=resolution
            )
            self.quarantine_cache.append(existing)
        
        # Persistir
        self._save_quarantine(existing)
        
        logger.info(
            f"🚫 CUARENTENA: {parameter}={failed_value} "
            f"({error_reason}) "
            f"hasta {datetime.fromtimestamp(expiry).isoformat()}"
        )
        
        return existing
    
    def is_quarantined(self, parameter: str, value: any = None) -> bool:
        """
        Verificar si parámetro está en cuarentena
        
        Argumentos:
            parameter: Nombre del parámetro
            value: Valor específico (opcional)
        
        Retorna:
            True si está en cuarentena y no ha expirado
        """
        
        # Limpiar expirados
        self._cleanup_expired()
        
        if value is None:
            # Cualquier valor en cuarentena
            for q in self.quarantine_cache:
                if q.parameter == parameter:
                    return True
            return False
        else:
            # Valor específico
            return self._find_quarantined(parameter, value) is not None
    
    def get_quarantine_info(self, parameter: str, value: any = None) -> Optional[Dict]:
        """
        Obtener información de cuarentena
        
        Retorna:
            Dict con metadata o None si no está en cuarentena
        """
        
        if value is None:
            # Obtener primer parámetro en cuarentena
            for q in self.quarantine_cache:
                if q.parameter == parameter:
                    return self._to_dict(q)
            return None
        else:
            q = self._find_quarantined(parameter, value)
            return self._to_dict(q) if q else None
    
    def get_all_quarantined(self) -> List[Dict]:
        """Obtener todos los parámetros en cuarentena (no expirados)"""
        
        self._cleanup_expired()
        return [self._to_dict(q) for q in self.quarantine_cache]
    
    def release_from_quarantine(self, parameter: str, value: any = None) -> bool:
        """
        Liberar parámetro de cuarentena manualmente
        
        Retorna:
            True si fue liberado, False si no estaba en cuarentena
        """
        
        original_count = len(self.quarantine_cache)
        
        if value is None:
            # Liberar todos los valores del parámetro
            self.quarantine_cache = [
                q for q in self.quarantine_cache
                if q.parameter != parameter
            ]
        else:
            # Liberar valor específico
            self.quarantine_cache = [
                q for q in self.quarantine_cache
                if not (q.parameter == parameter and q.failed_value == value)
            ]
        
        removed = original_count - len(self.quarantine_cache)
        
        if removed > 0:
            logger.info(
                f"✅ LIBERADO DE CUARENTENA: {parameter}={value} "
                f"({removed} entradas eliminadas)"
            )
            self._rebuild_quarantine_file()
            return True
        
        return False
    
    def _find_quarantined(
        self,
        parameter: str,
        value: any
    ) -> Optional[QuarantinedParameter]:
        """Buscar parámetro en cuarentena"""
        
        for q in self.quarantine_cache:
            if q.parameter == parameter and q.failed_value == value:
                if time.time() < q.expiry_timestamp:
                    return q
        return None
    
    def _cleanup_expired(self):
        """Eliminar entradas expiradas"""
        
        now = time.time()
        expired = [q for q in self.quarantine_cache if q.expiry_timestamp <= now]
        
        if expired:
            logger.info(f"🧹 Limpiando {len(expired)} entradas expiradas de cuarentena")
            
            for q in expired:
                logger.info(
                    f"  Liberado: {q.parameter}={q.failed_value} "
                    f"(expiró en {datetime.fromtimestamp(q.expiry_timestamp).isoformat()})"
                )
            
            self.quarantine_cache = [
                q for q in self.quarantine_cache
                if q.expiry_timestamp > now
            ]
            
            self._rebuild_quarantine_file()
    
    def _reload_cache(self):
        """Recargar quarantine desde archivo"""
        
        self.quarantine_cache = []
        
        try:
            with open(self.quarantine_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            q = QuarantinedParameter(**data)
                            self.quarantine_cache.append(q)
                        except Exception as e:
                            logger.error(f"Error parsing quarantine line: {e}")
        
        except FileNotFoundError:
            logger.warning(f"Quarantine file not found: {self.quarantine_file}")
    
    def _save_quarantine(self, q: QuarantinedParameter):
        """Guardar entrada en archivo"""
        
        with open(self.quarantine_file, 'a') as f:
            f.write(json.dumps(self._to_dict(q)) + '\n')
            f.flush()
    
    def _rebuild_quarantine_file(self):
        """Reconstruir archivo desde cache"""
        
        with open(self.quarantine_file, 'w') as f:
            for q in self.quarantine_cache:
                f.write(json.dumps(self._to_dict(q)) + '\n')
            f.flush()
    
    def _to_dict(self, q: QuarantinedParameter) -> Dict:
        """Convertir a dict para JSON"""
        
        return {
            'parameter': q.parameter,
            'failed_value': q.failed_value,
            'error_reason': q.error_reason,
            'quarantine_timestamp': q.quarantine_timestamp,
            'expiry_timestamp': q.expiry_timestamp,
            'attempt_count': q.attempt_count,
            'last_failed_at': q.last_failed_at,
            'resolution': q.resolution
        }
    
    def get_statistics(self) -> Dict:
        """Obtener estadísticas de cuarentena"""
        
        self._cleanup_expired()
        
        return {
            'total_quarantined': len(self.quarantine_cache),
            'by_parameter': self._group_by_parameter(),
            'average_attempts': self._average_attempts(),
            'oldest_entry': self._oldest_entry()
        }
    
    def _group_by_parameter(self) -> Dict[str, int]:
        """Agrupar por parámetro"""
        
        result = {}
        for q in self.quarantine_cache:
            result[q.parameter] = result.get(q.parameter, 0) + 1
        return result
    
    def _average_attempts(self) -> float:
        """Promedio de intentos fallidos"""
        
        if not self.quarantine_cache:
            return 0.0
        
        total = sum(q.attempt_count for q in self.quarantine_cache)
        return total / len(self.quarantine_cache)
    
    def _oldest_entry(self) -> Optional[float]:
        """Timestamp de entrada más antigua"""
        
        if not self.quarantine_cache:
            return None
        
        return min(q.quarantine_timestamp for q in self.quarantine_cache)
