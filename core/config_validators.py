"""
Configuration Validators - Validación de parámetros usando Pydantic.
Define rangos permitidos para todos los parámetros del sistema Aipha.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)


class TradingConfig(BaseModel):
    """Validador para parámetros de Trading."""
    model_config = ConfigDict(extra="allow")
    
    atr_period: int = Field(
        default=14,
        ge=5,
        le=50,
        description="Período del promedio verdadero (ATR)"
    )
    tp_factor: float = Field(
        default=2.0,
        ge=0.5,
        le=5.0,
        description="Factor de Take Profit (múltiple de ATR)"
    )
    sl_factor: float = Field(
        default=1.0,
        ge=0.1,
        le=3.0,
        description="Factor de Stop Loss (múltiple de ATR)"
    )
    time_limit: int = Field(
        default=24,
        ge=1,
        le=240,
        description="Límite de tiempo en horas"
    )
    volume_percentile_threshold: int = Field(
        default=90,
        ge=50,
        le=99,
        description="Percentil de volumen (50-99)"
    )
    body_percentile_threshold: int = Field(
        default=25,
        ge=5,
        le=50,
        description="Percentil de cuerpo de vela"
    )

    @field_validator('tp_factor', mode='after')
    @classmethod
    def tp_factor_greater_than_sl(cls, v, info):
        if 'sl_factor' in info.data and v <= info.data['sl_factor']:
            raise ValueError('tp_factor debe ser mayor que sl_factor')
        return v


class OracleConfig(BaseModel):
    """Validador para parámetros del Oracle."""
    model_config = ConfigDict(extra="allow")
    
    confidence_threshold: float = Field(
        default=0.70,
        ge=0.5,
        le=0.99,
        description="Umbral de confianza del oráculo"
    )
    n_estimators: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Número de estimadores en el modelo"
    )
    model_path: str = Field(
        default="oracle/models/proof_oracle.joblib",
        description="Ruta del modelo entrenado"
    )


class PostprocessorConfig(BaseModel):
    """Validador para parámetros del Postprocessor."""
    model_config = ConfigDict(extra="allow")
    
    adaptive_sensitivity: float = Field(
        default=0.1,
        ge=0.01,
        le=1.0,
        description="Sensibilidad adaptativa del postprocesador"
    )


class AiphaConfig(BaseModel):
    """Validador completo de la configuración de Aipha."""
    model_config = ConfigDict(extra="allow")
    
    Trading: TradingConfig = Field(default_factory=TradingConfig)
    Oracle: OracleConfig = Field(default_factory=OracleConfig)
    Postprocessor: PostprocessorConfig = Field(default_factory=PostprocessorConfig)


class ConfigValidator:
    """Servicio de validación de configuración."""

    RANGE_DEFINITIONS = {
        "Trading": {
            "atr_period": {"min": 5, "max": 50, "type": "int"},
            "tp_factor": {"min": 0.5, "max": 5.0, "type": "float"},
            "sl_factor": {"min": 0.1, "max": 3.0, "type": "float"},
            "time_limit": {"min": 1, "max": 240, "type": "int"},
            "volume_percentile_threshold": {"min": 50, "max": 99, "type": "int"},
            "body_percentile_threshold": {"min": 5, "max": 50, "type": "int"}
        },
        "Oracle": {
            "confidence_threshold": {"min": 0.5, "max": 0.99, "type": "float"},
            "n_estimators": {"min": 10, "max": 1000, "type": "int"},
            "model_path": {"type": "string"}
        },
        "Postprocessor": {
            "adaptive_sensitivity": {"min": 0.01, "max": 1.0, "type": "float"}
        }
    }

    @staticmethod
    def validate_full_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida la configuración completa.

        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []

        try:
            AiphaConfig(**config)
            return True, []
        except ValidationError as e:
            for error in e.errors():
                field_path = ".".join(str(x) for x in error["loc"])
                msg = error["msg"]
                errors.append(f"{field_path}: {msg}")
            return False, errors

    @staticmethod
    def validate_parameter(
        category: str,
        param_name: str,
        value: Any
    ) -> Tuple[bool, str]:
        """
        Valida un parámetro específico.

        Args:
            category: Categoría (Trading, Oracle, Postprocessor)
            param_name: Nombre del parámetro
            value: Valor a validar

        Returns:
            Tuple (is_valid, error_message)
        """
        if category not in ConfigValidator.RANGE_DEFINITIONS:
            return False, f"Categoría desconocida: {category}"

        if param_name not in ConfigValidator.RANGE_DEFINITIONS[category]:
            return False, f"Parámetro desconocido: {param_name}"

        param_def = ConfigValidator.RANGE_DEFINITIONS[category][param_name]
        param_type = param_def.get("type")

        # Validar tipo
        if param_type == "int" and not isinstance(value, int):
            return False, f"{param_name} debe ser un número entero"

        if param_type == "float" and not isinstance(value, (int, float)):
            return False, f"{param_name} debe ser un número decimal"

        if param_type == "string" and not isinstance(value, str):
            return False, f"{param_name} debe ser una cadena"

        # Validar rango para números
        if param_type in ("int", "float"):
            min_val = param_def.get("min")
            max_val = param_def.get("max")

            if min_val is not None and value < min_val:
                return False, f"{param_name} no puede ser menor que {min_val}"

            if max_val is not None and value > max_val:
                return False, f"{param_name} no puede ser mayor que {max_val}"

        return True, ""

    @staticmethod
    def get_validation_report(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un reporte detallado de validación.

        Returns:
            Reporte con status, errors y warnings
        """
        is_valid, errors = ConfigValidator.validate_full_config(config)

        warnings = []

        # Chequeos de coherencia
        if "Trading" in config:
            trading = config["Trading"]
            if trading.get("tp_factor", 2.0) <= trading.get("sl_factor", 1.0):
                warnings.append(
                    "⚠️  tp_factor debería ser mayor que sl_factor para máximas ganancias"
                )

            if trading.get("volume_percentile_threshold", 90) <= 60:
                warnings.append(
                    "⚠️  volume_percentile_threshold muy bajo podría permitir trades con bajo volumen"
                )

        if "Oracle" in config:
            oracle = config["Oracle"]
            if oracle.get("confidence_threshold", 0.7) < 0.6:
                warnings.append(
                    "⚠️  confidence_threshold muy bajo podría generar muchos falsos positivos"
                )

        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "status": "✅ VÁLIDA" if is_valid else "❌ INVÁLIDA",
        }

    @staticmethod
    def get_parameter_suggestions(category: str, param_name: str) -> Dict[str, Any]:
        """
        Retorna sugerencias para un parámetro específico.
        """
        if category not in ConfigValidator.RANGE_DEFINITIONS:
            return {}

        if param_name not in ConfigValidator.RANGE_DEFINITIONS[category]:
            return {}

        param_def = ConfigValidator.RANGE_DEFINITIONS[category][param_name]

        suggestions = {
            "name": param_name,
            "category": category,
            "description": f"{param_name} en {category}",
            "range": {
                "min": param_def.get("min"),
                "max": param_def.get("max"),
            },
            "type": param_def.get("type"),
        }

        # Agregar ejemplos según el parámetro
        if param_name == "tp_factor":
            suggestions["typical_values"] = [1.5, 2.0, 2.5, 3.0]
            suggestions["description"] = "Multiplicador de ATR para Take Profit"
        elif param_name == "sl_factor":
            suggestions["typical_values"] = [0.5, 1.0, 1.5]
            suggestions["description"] = "Multiplicador de ATR para Stop Loss"
        elif param_name == "atr_period":
            suggestions["typical_values"] = [7, 14, 21]
            suggestions["description"] = "Período del Promedio Verdadero"
        elif param_name == "confidence_threshold":
            suggestions["typical_values"] = [0.60, 0.70, 0.80, 0.90]
            suggestions["description"] = "Umbral mínimo de confianza del Oracle"

        return suggestions

