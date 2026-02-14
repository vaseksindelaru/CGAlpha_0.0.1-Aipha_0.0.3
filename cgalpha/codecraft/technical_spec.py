"""
TechnicalSpec: Especificación técnica estructurada de cambios de código.

Este módulo define las estructuras de datos fundamentales para representar
cambios en código de forma que puedan ser procesados automáticamente.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import hashlib
import os


class ChangeType(Enum):
    """Tipos de cambios soportados por Code Craft Sage"""
    PARAMETER_CHANGE = "parameter_change"
    METHOD_ADDITION = "method_addition"
    CLASS_MODIFICATION = "class_modification"
    CONFIG_UPDATE = "config_update"
    IMPORT_ADDITION = "import_addition"
    DOCSTRING_UPDATE = "docstring_update"


@dataclass
class TechnicalSpec:
    """
    Especificación técnica estructurada de un cambio de código.
    
    Esta clase representa la conversión de una propuesta en lenguaje natural
    a una especificación técnica precisa que puede ser ejecutada automáticamente.
    
    Attributes:
        proposal_id: Identificador único de la propuesta
        change_type: Tipo de cambio a realizar
        file_path: Ruta relativa al archivo objetivo
        class_name: Nombre de la clase (si aplica)
        attribute_name: Nombre del atributo/parámetro (si aplica)
        method_name: Nombre del método (si aplica)
        old_value: Valor actual (antes del cambio)
        new_value: Valor nuevo (después del cambio)
        validation_rules: Reglas de validación {"min": 0, "max": 1, "type": "float"}
        data_type: Tipo de dato Python ("float", "int", "str", "bool", "dict", "list")
        affected_tests: Lista de archivos de tests afectados
        documentation_files: Lista de archivos de documentación a actualizar
        source_proposal: Texto original de la propuesta
        confidence_score: Confianza del parser (0.0-1.0)
    """
    
    # Identificación
    proposal_id: str
    change_type: ChangeType
    
    # Ubicación en código
    file_path: str
    class_name: Optional[str] = None
    attribute_name: Optional[str] = None
    method_name: Optional[str] = None
    
    # Valores
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Validación
    validation_rules: Optional[Dict[str, Any]] = None
    data_type: Optional[str] = None
    
    # Dependencias
    affected_tests: List[str] = field(default_factory=list)
    documentation_files: List[str] = field(default_factory=list)
    
    # Metadata
    source_proposal: str = ""
    confidence_score: float = 0.0
    
    def to_dict(self) -> dict:
        """
        Serializa TechnicalSpec a diccionario para JSON/Redis.
        
        Returns:
            Dict serializable a JSON
        """
        data = asdict(self)
        # Convertir enum a string
        data['change_type'] = self.change_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TechnicalSpec':
        """
        Deserializa diccionario a TechnicalSpec.
        
        Args:
            data: Diccionario con datos de spec
            
        Returns:
            Instancia de TechnicalSpec
        """
        # Convertir string a enum
        if 'change_type' in data and isinstance(data['change_type'], str):
            data['change_type'] = ChangeType(data['change_type'])
        
        return cls(**data)
    
    def to_json(self) -> str:
        """Serializa a JSON string"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TechnicalSpec':
        """Deserializa desde JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def get_cache_key(self) -> str:
        """
        Genera clave única para cache Redis basada en contenido.
        
        Returns:
            Hash MD5 del contenido relevante
        """
        # Usar source_proposal para cache key
        content = f"{self.source_proposal}:{self.change_type.value}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def is_valid(self) -> tuple[bool, Optional[str]]:
        """
        Valida la especificación técnica.
        
        Returns:
            Tupla (es_válido, mensaje_error)
        """
        # Validación básica de campos requeridos
        if not self.proposal_id:
            return False, "proposal_id es requerido"
        
        if not self.file_path:
            return False, "file_path es requerido"

        if "\x00" in self.file_path:
            return False, "file_path inválido (null byte detectado)"
        
        # Validar que file_path no tenga path traversal
        # Permitir absolute paths (necesario para testing)
        if ".." in self.file_path:
            return False, "file_path inválido (path traversal detectado)"

        normalized = os.path.abspath(self.file_path)
        normalized_parts = normalized.replace("\\", "/").split("/")
        if ".." in normalized_parts:
            return False, "file_path inválido (path traversal normalizado)"
        
        # Validar tipo de dato si se especifica
        if self.data_type:
            valid_types = ["float", "int", "str", "bool", "dict", "list", "tuple", "set", "None"]
            if self.data_type not in valid_types:
                return False, f"data_type '{self.data_type}' no soportado"
        
        # Validar rangos si existen
        if self.validation_rules:
            if "min" in self.validation_rules and "max" in self.validation_rules:
                min_val = self.validation_rules["min"]
                max_val = self.validation_rules["max"]
                if min_val > max_val:
                    return False, "validation_rules: min > max"
                
                # Validar que new_value esté en rango si es numérico
                if self.new_value is not None:
                    try:
                        new_val_num = float(self.new_value)
                        if not (min_val <= new_val_num <= max_val):
                            return False, f"new_value {new_val_num} fuera de rango [{min_val}, {max_val}]"
                    except (ValueError, TypeError):
                        pass  # No es numérico, skip validación de rango
        
        # Validar confidence_score
        if not (0.0 <= self.confidence_score <= 1.0):
            return False, "confidence_score debe estar entre 0.0 y 1.0"
        
        return True, None
    
    def __repr__(self) -> str:
        """Representación string legible"""
        return (
            f"TechnicalSpec(id={self.proposal_id}, "
            f"type={self.change_type.value}, "
            f"file={self.file_path}, "
            f"class={self.class_name}, "
            f"attr={self.attribute_name}, "
            f"change={self.old_value}→{self.new_value})"
        )
