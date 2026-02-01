"""
Action Applicator (La Mano del Inventor).
Ejecuta los cambios propuestos en el sistema de archivos (Config / Code).
"""
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ActionApplicator:
    """
    Componente ejecutor de propuestas de política.
    En v0.0.3, se especializa en modificar `aipha_config.json`.
    """
    
    def __init__(self, config_path: str = "aipha_config.json"):
        self.config_path = Path(config_path)
        
    def apply_proposal(self, proposal_data: Dict[str, Any]) -> bool:
        """
        Aplica una propuesta de cambio.
        
        Args:
            proposal_data: Dict con {parameter, action, value}
            
        Returns:
            True si se aplicó con éxito.
        """
        logger.info(f"🛠️ ActionApplicator: Aplicando propuesta -> {proposal_data}")
        
        # 1. Validar existencia de config
        if not self.config_path.exists():
            logger.error(f"❌ Config file not found: {self.config_path}")
            return False
            
        try:
            # 2. Backup de seguridad
            backup_path = self.config_path.with_suffix('.json.bak')
            shutil.copy(self.config_path, backup_path)
            logger.info(f"   💾 Backup creado en {backup_path}")
            
            # 3. Leer Configuración
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # 4. Modificar Valor (Lógica "The Inventor" Simplificada)
            param = proposal_data.get('parameter')
            new_value = proposal_data.get('value')
            
            # Navegar estructura anidada si es necesario (ej. "Trading.confidence_threshold")
            # En v0.0.3 asumimos estructura plana o 'Trading.' prefix
            
            applied = False
            
            if param.startswith("Trading."):
                key = param.split(".")[1]
                if key in config.get("Trading", {}):
                    old_value = config["Trading"][key]
                    config["Trading"][key] = new_value
                    applied = True
                    logger.info(f"   🔄 Cambio: Trading.{key} {old_value} -> {new_value}")
                else:
                    # Si no existe en sección Trading, quizás está en root o debemos crearlo
                     # Para este demo, asumimos que debe existir
                     if "Trading" not in config:
                         config["Trading"] = {}
                     
                     config["Trading"][key] = new_value
                     applied = True
                     logger.info(f"   ➕ Nuevo Parámetro: Trading.{key} = {new_value}")
                     
            else:
                # Root level
                if param in config:
                    old_value = config[param]
                    config[param] = new_value
                    applied = True
                    logger.info(f"   🔄 Cambio: {param} {old_value} -> {new_value}")
                else:
                     config[param] = new_value
                     applied = True
                     logger.info(f"   ➕ Nuevo Parámetro: {param} = {new_value}")
            
            if applied:
                # 5. Guardar Cambios
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                logger.info("   ✅ Cambios guardados en disco.")
                return True
            else:
                logger.warning("   ⚠️ No se pudo determinar ruta del parámetro.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error aplicando cambio: {e}")
            # Restore backup logic could go here
            return False

