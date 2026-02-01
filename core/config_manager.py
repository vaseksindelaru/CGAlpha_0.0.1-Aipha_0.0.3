"""
Config Manager - Gestión centralizada de parámetros del sistema Aipha.
Permite que la Capa 1 modifique parámetros y las Capas 2-5 los consuman.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    """Gestiona la configuración persistente del sistema."""
    def __init__(self, config_path: Path = Path("memory/aipha_config.json")):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load_initial_config()

    def _load_initial_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo o crea una por defecto."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error cargando config: {e}")
        
        # Valores por defecto (Baseline)
        default_config = {
            "Trading": {
                "atr_period": 14,
                "tp_factor": 2.0,
                "sl_factor": 1.0,
                "time_limit": 24,
                "volume_percentile_threshold": 90,
                "body_percentile_threshold": 25
            },
            "Oracle": {
                "confidence_threshold": 0.70,
                "n_estimators": 100,
                "model_path": "oracle/models/proof_oracle.joblib"
            },
            "Postprocessor": {
                "adaptive_sensitivity": 0.1
            }
        }
        self.save_config(default_config)
        return default_config

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtiene un valor usando una ruta (ej: 'Trading.tp_factor').
        """
        parts = key_path.split(".")
        val = self._config
        try:
            for part in parts:
                val = val[part]
            return val
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """
        Establece un valor usando una ruta y guarda en disco.
        """
        parts = key_path.split(".")
        val = self._config
        for part in parts[:-1]:
            if part not in val:
                val[part] = {}
            val = val[part]
        val[parts[-1]] = value
        self.save_config(self._config)

    def save_config(self, config: Dict[str, Any], create_backup: bool = True) -> None:
        """Guarda la configuración en disco y opcionalmente crea un backup."""
        try:
            if create_backup and self.config_path.exists():
                self._create_backup()
                
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            self._config = config
            logger.info(f"Configuración guardada en {self.config_path}")
        except Exception as e:
            logger.error(f"Error guardando config: {e}")

    def _create_backup(self) -> None:
        """Crea una copia de seguridad de la configuración actual."""
        import shutil
        from datetime import datetime
        
        backup_dir = self.config_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"config_backup_{timestamp}.json"
        
        shutil.copy2(self.config_path, backup_path)
        
        # Mantener solo los últimos 10 backups
        backups = sorted(list(backup_dir.glob("config_backup_*.json")), reverse=True)
        for old_backup in backups[10:]:
            old_backup.unlink()

    def rollback(self) -> bool:
        """Revierte a la última configuración de backup disponible."""
        backup_dir = self.config_path.parent / "backups"
        if not backup_dir.exists():
            logger.warning("No hay backups disponibles para rollback")
            return False
            
        backups = sorted(list(backup_dir.glob("config_backup_*.json")), reverse=True)
        if not backups:
            logger.warning("No hay archivos de backup en el directorio")
            return False
            
        last_backup = backups[0]
        try:
            with open(last_backup, "r", encoding="utf-8") as f:
                restored_config = json.load(f)
            
            self.save_config(restored_config, create_backup=False)
            logger.info(f"Rollback exitoso usando {last_backup.name}")
            return True
        except Exception as e:
            logger.error(f"Error durante rollback: {e}")
            return False

    def get_all(self) -> Dict[str, Any]:
        """Devuelve toda la configuración."""
        return self._config
