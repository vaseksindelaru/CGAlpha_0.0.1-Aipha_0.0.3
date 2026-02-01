"""
core/llm_assistant_v2.py - Assistant LLM Refactorizado (Modular)

Nueva arquitectura modular de LLM Assistant.
Usa core/llm_providers para intercambiabilidad.

Soluciona: P1 #6 - LLM Assistant acoplado (895 → ~200 líneas)
"""

import logging
from typing import Dict, Any, Optional
from core.llm_providers import OpenAIProvider, RateLimiter, retry_with_rate_limit
from core.exceptions import LLMError as AiphaLLMError

logger = logging.getLogger(__name__)


class LLMAssistantV2:
    """
    Asistente LLM refactorizado y modular.
    
    Cambios principales:
    - Usa LLMProvider (intercambiable)
    - Incluye RateLimiter para control automático
    - Separa prompt building de API calls
    - Testeable y mantenible
    """
    
    def __init__(self,
                 provider: Optional[Any] = None,
                 system_prompt: str = None):
        """
        Inicializar asistente LLM.
        
        Args:
            provider: LLMProvider (si None, usa OpenAI por defecto)
            system_prompt: Instrucciones del sistema
        """
        # Provider
        self.provider = provider or OpenAIProvider()
        
        # Rate limiter
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=60,
            error_threshold=5
        )
        
        # System prompt por defecto
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        logger.info(f"✓ LLMAssistantV2 inicializado (provider={self.provider.name})")
    
    def _get_default_system_prompt(self) -> str:
        """System prompt por defecto para Aipha"""
        return """Eres el arquitecto inteligente del sistema Aipha, un trading system autónomo.

Tu rol:
- Analizar métricas del sistema y proponer mejoras
- Diagnosticar problemas de manera clara y estructurada
- Sugerir parámetros óptimos basado en datos históricos

Personalidad:
- Precisión técnica pero accesible
- Conservador en cambios de riesgo
- Explicas siempre tu razonamiento

Formato: Siempre estructura así:
1. DIAGNÓSTICO: Estado actual
2. ANÁLISIS: Causa raíz
3. RECOMENDACIÓN: Qué hacer
4. PRÓXIMOS PASOS: Cambios sugeridos"""
    
    @retry_with_rate_limit
    def generate(self,
                 prompt: str,
                 temperature: float = 0.7,
                 max_tokens: int = 500) -> str:
        """
        Generar respuesta del LLM.
        
        Incluye retry automático y rate limiting.
        
        Args:
            prompt: Pregunta/prompt del usuario
            temperature: Creatividad (0-2)
            max_tokens: Máximo tokens en respuesta
        
        Returns:
            Respuesta generada
        
        Raises:
            AiphaLLMError: Si falla la generación
        """
        try:
            response = self.provider.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            self.rate_limiter.record_success()
            logger.debug(f"✓ LLM generation successful ({len(response)} chars)")
            
            return response
        
        except Exception as e:
            self.rate_limiter.record_error()
            logger.error(f"LLM generation failed: {e}")
            raise AiphaLLMError(f"LLM generation failed: {e}") from e
    
    def analyze_system(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analizar métricas del sistema.
        
        Args:
            metrics: Dict con métricas (win_rate, drawdown, etc)
        
        Returns:
            Análisis estructurado
        """
        prompt = f"""
Analiza estas métricas del sistema de trading:

{self._format_metrics(metrics)}

Proporciona:
1. Diagnóstico: ¿Cómo está la salud del sistema?
2. Análisis: ¿Qué patrones ves?
3. Recomendaciones: ¿Qué cambios sugiero?
4. Próximos pasos: ¿Qué medir?

Formato JSON con keys: diagnosis, analysis, recommendations, next_steps
        """
        
        response = self.generate(prompt, temperature=0.5, max_tokens=1000)
        
        try:
            result = self.provider.parse_json_response(response)
            return result
        except ValueError:
            # Si no es JSON, retornar como texto
            return {"analysis": response}
    
    def suggest_improvement(self, current_params: Dict[str, float]) -> Dict[str, Any]:
        """
        Sugerir mejora para parámetros.
        
        Args:
            current_params: Parámetros actuales
        
        Returns:
            Sugerencias de mejora
        """
        prompt = f"""
Dada la configuración actual:

{self._format_params(current_params)}

Sugiere ajustes específicos que podrían mejorar performance.

Retorna JSON con:
- suggested_params: dict de nuevos valores
- rationale: Explicación breve
- risk_level: "low", "medium", "high"
- expected_impact: Descripción del impacto esperado
        """
        
        response = self.generate(prompt, temperature=0.7, max_tokens=800)
        
        try:
            result = self.provider.parse_json_response(response)
            return result
        except ValueError:
            return {"suggestion": response}
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Formatear métricas para el prompt"""
        lines = []
        for key, value in metrics.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    def _format_params(self, params: Dict[str, float]) -> str:
        """Formatear parámetros para el prompt"""
        lines = []
        for key, value in params.items():
            lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    @property
    def is_available(self) -> bool:
        """Verificar si el asistente está disponible"""
        return (
            self.provider.validate_api_key() and
            self.rate_limiter.is_available()
        )


# Instancia global para uso en CLI
_assistant_instance: Optional[LLMAssistantV2] = None


def get_llm_assistant() -> LLMAssistantV2:
    """Obtener instancia global del asistente LLM"""
    global _assistant_instance
    if _assistant_instance is None:
        _assistant_instance = LLMAssistantV2()
    return _assistant_instance


def reset_llm_assistant():
    """Resetear la instancia global (útil para testing)"""
    global _assistant_instance
    _assistant_instance = None
