"""
ProposalParser: Conversión de lenguaje natural a especificaciones técnicas.

Este módulo implementa el parser inteligente que convierte propuestas en lenguaje
natural a especificaciones técnicas estructuradas (TechnicalSpec) usando LLM y cache Redis.
"""

import json
import logging
import hashlib
import re
from typing import Optional, Dict, Any
from pathlib import Path

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType

# Imports condicionales para no romper si no están disponibles
try:
    from core.llm_assistant_v2 import get_llm_assistant
except ImportError:
    get_llm_assistant = None

try:
    from cgalpha.nexus.redis_client import RedisClient
except ImportError:
    RedisClient = None

logger = logging.getLogger(__name__)


class ProposalParser:
    """
    Parser inteligente de propuestas con LLM y cache Redis.
    
    Convierte propuestas en lenguaje natural como:
    "Cambiar confidence_threshold de 0.70 a 0.65 en Oracle"
    
    A especificaciones técnicas estructuradas (TechnicalSpec).
    
    Features:
    - Cache en Redis para evitar llamadas redundantes al LLM
    - Fallback a reglas heurísticas si LLM no disponible
    - Validación de especificaciones generadas
    - Métricas de parsing (tiempo, cache hit rate)
    """
    
    CACHE_PREFIX = "codecraft:parse:"
    CACHE_TTL = 86400  # 24 horas
    
    def __init__(self, redis_client=None, llm_assistant=None):
        """
        Inicializa el parser.
        
        Args:
            redis_client: Cliente Redis (opcional, crea uno si None)
            llm_assistant: Asistente LLM (opcional, usa get_llm_assistant si None)
        """
        # Por defecto no se auto-inicializan dependencias externas para mantener
        # comportamiento determinista y testeable.
        self.redis = redis_client
        self.llm = llm_assistant
        
        # Métricas
        self.metrics = {
            "total_parses": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "llm_calls": 0,
            "heuristic_fallbacks": 0,
            "errors": 0
        }
    
    def parse(self, proposal_text: str, proposal_id: str = None) -> TechnicalSpec:
        """
        Convierte propuesta en lenguaje natural a TechnicalSpec.
        
        Flujo:
        1. Check Redis cache (hash del texto)
        2. Si en cache → deserializar y retornar
        3. Si no en cache → llamar a LLM
        4. Parsear respuesta del LLM a TechnicalSpec
        5. Validar spec (rangos, tipos, archivos existentes)
        6. Guardar en cache Redis (TTL: 24h)
        7. Retornar spec
        
        Args:
            proposal_text: Texto de la propuesta en lenguaje natural
            proposal_id: ID único de la propuesta (opcional, se genera si None)
            
        Returns:
            TechnicalSpec validado
            
        Raises:
            ValueError: Si el parsing falla completamente
        """
        self.metrics["total_parses"] += 1
        
        if not proposal_id:
            proposal_id = self._generate_proposal_id(proposal_text)
        
        logger.info(f"🔍 Parsing proposal: {proposal_id}")
        logger.debug(f"   Text: {proposal_text[:100]}...")
        
        # 1. Check cache
        cache_key = self._get_cache_key(proposal_text)
        cached_spec = self._get_from_cache(cache_key)
        
        if cached_spec:
            self.metrics["cache_hits"] += 1
            logger.info(f"   ✅ Cache HIT: {cache_key}")
            cached_spec.proposal_id = proposal_id  # Update ID
            return cached_spec
        
        # 2. Cache miss → parse proposal
        self.metrics["cache_misses"] += 1
        logger.info(f"   ⚠️ Cache MISS: {cache_key}")
        
        try:
            # Intentar LLM primero
            if self.llm:
                spec = self._parse_with_llm(proposal_text, proposal_id)
            else:
                # Fallback a heurísticas
                spec = self._parse_with_heuristics(proposal_text, proposal_id)
        
        except Exception as e:
            self.metrics["errors"] += 1
            logger.error(f"   ❌ Parsing error: {e}")
            # Último fallback: heurísticas
            spec = self._parse_with_heuristics(proposal_text, proposal_id)
        
        # 3. Validar spec
        is_valid, error_msg = spec.is_valid()
        if not is_valid:
            logger.warning(f"   ⚠️ Spec validation failed: {error_msg}")
            # Intentar corregir automáticamente
            spec = self._fix_spec(spec)
        
        # 4. Guardar en cache
        self._save_to_cache(cache_key, spec)
        
        logger.info(f"   ✅ Parsing complete: {spec}")
        return spec
    
    def _parse_with_llm(self, proposal_text: str, proposal_id: str) -> TechnicalSpec:
        """
        Parsea propuesta usando LLM.
        
        Args:
            proposal_text: Texto de la propuesta
            proposal_id: ID de la propuesta
            
        Returns:
            TechnicalSpec parseado por LLM
        """
        self.metrics["llm_calls"] += 1
        logger.info("   🤖 Calling LLM for parsing...")
        
        # Prompt estructurado
        prompt = self._build_llm_prompt(proposal_text)
        
        # Llamar al LLM con temperature baja para respuestas deterministas
        response = self.llm.generate(prompt, temperature=0.3, max_tokens=800)
        
        # Extraer JSON de la respuesta
        spec_data = self._extract_json_from_response(response)
        
        # Convertir a TechnicalSpec
        spec_data["proposal_id"] = proposal_id
        spec_data["source_proposal"] = proposal_text
        
        # Si change_type es string, convertir a enum
        if isinstance(spec_data.get("change_type"), str):
            spec_data["change_type"] = ChangeType(spec_data["change_type"])
        
        spec = TechnicalSpec.from_dict(spec_data)
        spec.confidence_score = 0.9  # Alta confianza en LLM
        
        logger.info(f"   ✅ LLM parsing successful. Confidence: {spec.confidence_score}")
        return spec
    
    def _parse_with_heuristics(self, proposal_text: str, proposal_id: str) -> TechnicalSpec:
        """
        Fallback: parsea usando reglas heurísticas simples.
        
        Detecta patrones como:
        - "cambiar X de A a B"
        - "modificar X en Clase"
        - "actualizar configuración X"
        
        Args:
            proposal_text: Texto de la propuesta
            proposal_id: ID de la propuesta
            
        Returns:
            TechnicalSpec parseado heurísticamente
        """
        self.metrics["heuristic_fallbacks"] += 1
        logger.info("   🔧 Using heuristic fallback...")
        
        text_lower = proposal_text.lower()
        
        # Detectar tipo de cambio
        if "config" in text_lower or "configuración" in text_lower:
            change_type = ChangeType.CONFIG_UPDATE
        elif "método" in text_lower or "method" in text_lower or "función" in text_lower:
            change_type = ChangeType.METHOD_ADDITION
        else:
            change_type = ChangeType.PARAMETER_CHANGE
        
        # Extraer atributo (buscar palabras clave en ES/EN)
        attribute_pattern = r'(?:cambiar|modificar|actualizar|update|change|modify|set|adjust)\s+(?:the\s+)?([A-Za-z_]\w*)'
        attribute_match = re.search(attribute_pattern, text_lower)
        attribute_name = attribute_match.group(1) if attribute_match else "unknown_attribute"
        
        # Extraer valores (buscar "de X a Y", "from X to Y" o "X -> Y")
        value_pattern = r'(?:de|from)\s+(-?\d+(?:\.\d+)?)\s+(?:a|to)\s+(-?\d+(?:\.\d+)?)|(-?\d+(?:\.\d+)?)\s*->\s*(-?\d+(?:\.\d+)?)'
        value_match = re.search(value_pattern, proposal_text)
        
        if value_match:
            groups = [g for g in value_match.groups() if g is not None]
            old_value = float(groups[0])
            new_value = float(groups[1])
            data_type = "float"
        else:
            to_only_match = re.search(r'(?:a|to)\s+(-?\d+(?:\.\d+)?)', proposal_text)
            if to_only_match:
                old_value = None
                new_value = float(to_only_match.group(1))
                data_type = "float"
            else:
                old_value = None
                new_value = None
                data_type = "str"
        
        # Detectar clase (buscar "en ClassName")
        class_pattern = r'(?:en|in)\s+([A-Z]\w+)'
        class_match = re.search(class_pattern, proposal_text)
        class_name = class_match.group(1) if class_match else None
        
        # Detectar file_path explícito en el texto
        file_path_match = re.search(r'([A-Za-z0-9_./-]+\.(?:py|json))', proposal_text)

        # Determinar file_path (heurística básica)
        if file_path_match:
            file_path = file_path_match.group(1)
        elif change_type == ChangeType.CONFIG_UPDATE:
            file_path = "config/default.json"
        elif class_name:
            snake_guess = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
            file_path = f"{snake_guess}.py"
        else:
            file_path = "core/unknown.py"
        
        spec = TechnicalSpec(
            proposal_id=proposal_id,
            change_type=change_type,
            file_path=file_path,
            class_name=class_name,
            attribute_name=attribute_name,
            old_value=old_value,
            new_value=new_value,
            data_type=data_type,
            source_proposal=proposal_text,
            confidence_score=0.6  # Confianza media en heurísticas
        )
        
        logger.info(f"   ⚠️ Heuristic parsing complete. Confidence: {spec.confidence_score}")
        return spec
    
    def _build_llm_prompt(self, proposal_text: str) -> str:
        """Construye prompt estructurado para el LLM"""
        return f"""Analiza esta propuesta de cambio de código y extrae información técnica estructurada.

PROPUESTA:
{proposal_text}

INSTRUCCIONES:
Responde SOLO con un JSON válido (sin markdown, sin explicaciones) con la siguiente estructura:

{{
  "change_type": "parameter_change|method_addition|class_modification|config_update|import_addition|docstring_update",
  "file_path": "ruta/relativa/al/archivo.py",
  "class_name": "NombreClase (null si no aplica)",
  "attribute_name": "nombre_atributo (null si no aplica)",
  "method_name": "nombre_metodo (null si no aplica)",
  "old_value": "valor_actual (null si desconocido)",
  "new_value": "valor_nuevo",
  "data_type": "float|int|str|bool|dict|list",
  "validation_rules": {{"min": 0.0, "max": 1.0}},
  "affected_tests": ["tests/test_archivo.py"],
  "documentation_files": ["README.md"]
}}

EJEMPLOS:

Propuesta: "Cambiar confidence_threshold de 0.70 a 0.65 en OracleV2"
Respuesta: {{"change_type": "parameter_change", "file_path": "oracle/oracle_v2.py", "class_name": "OracleV2", "attribute_name": "confidence_threshold", "old_value": 0.70, "new_value": 0.65, "data_type": "float", "validation_rules": {{"min": 0.5, "max": 0.95}}}}

Ahora analiza la propuesta arriba y responde SOLO con el JSON:"""
    
    def _extract_json_from_response(self, response: str) -> dict:
        """
        Extrae JSON de la respuesta del LLM.
        
        Maneja casos donde el LLM devuelve:
        - JSON puro
        - JSON envuelto en markdown ```json...```
        - JSON con texto adicional
        """
        # Remover markdown code blocks si existen
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response, re.DOTALL)
        
        if match:
            json_str = match.group(1)
        else:
            # Buscar JSON directamente
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in LLM response")
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from LLM: {json_str}")
            raise ValueError(f"Invalid JSON: {e}")
    
    def _get_cache_key(self, proposal_text: str) -> str:
        """Genera clave de cache basada en hash del texto"""
        text_hash = hashlib.md5(proposal_text.encode()).hexdigest()
        return f"{self.CACHE_PREFIX}{text_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[TechnicalSpec]:
        """Obtiene spec desde cache Redis"""
        if not self.redis or not self.redis.is_connected():
            return None
        
        try:
            cached_data = self.redis.get_system_state(cache_key)
            if cached_data:
                return TechnicalSpec.from_dict(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    def _save_to_cache(self, cache_key: str, spec: TechnicalSpec):
        """Guarda spec en cache Redis"""
        if not self.redis or not self.redis.is_connected():
            return
        
        try:
            self.redis.cache_system_state(cache_key, spec.to_dict(), ttl_seconds=self.CACHE_TTL)
            logger.debug(f"   💾 Saved to cache: {cache_key}")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _generate_proposal_id(self, proposal_text: str) -> str:
        """Genera ID único para propuesta"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        text_hash = hashlib.md5(proposal_text.encode()).hexdigest()[:6]
        return f"PROP_{timestamp}_{text_hash}"
    
    def _fix_spec(self, spec: TechnicalSpec) -> TechnicalSpec:
        """Intenta corregir especificación inválida"""
        # Corregir file_path si es inválido
        if not spec.file_path or spec.file_path.startswith("/") or ".." in spec.file_path:
            spec.file_path = "config/default.json"
        
        # Corregir confidence_score si está fuera de rango
        if spec.confidence_score < 0.0:
            spec.confidence_score = 0.0
        elif spec.confidence_score > 1.0:
            spec.confidence_score = 1.0
        
        return spec
    
    def get_metrics(self) -> dict:
        """
        Retorna métricas de parsing.
        
        Returns:
            Dict con estadísticas de uso
        """
        cache_hit_rate = (
            self.metrics["cache_hits"] / self.metrics["total_parses"] 
            if self.metrics["total_parses"] > 0 else 0.0
        )
        
        return {
            **self.metrics,
            "cache_hit_rate": round(cache_hit_rate, 2)
        }
