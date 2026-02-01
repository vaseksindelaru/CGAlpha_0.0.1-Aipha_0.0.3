"""
tests/test_llm_providers.py - Tests de Proveedores LLM Modularizados

Valida que la arquitectura modular de LLM funciona correctamente.
Soluciona: P1 #6 - LLM Assistant modularizado

Ejecutar con: pytest tests/test_llm_providers.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.llm_providers.base import LLMProvider, LLMError, LLMConnectionError
from core.llm_providers.openai_provider import OpenAIProvider
from core.llm_providers.rate_limiter import RateLimiter, retry_with_rate_limit


class TestLLMProviderInterface:
    """Tests de la interfaz base LLMProvider"""
    
    def test_llm_provider_is_abstract(self):
        """✓ LLMProvider es abstracto y no se puede instanciar"""
        with pytest.raises(TypeError):
            LLMProvider()
    
    def test_llm_provider_requires_generate_method(self):
        """✓ Subclases deben implementar generate()"""
        class IncompleteProvider(LLMProvider):
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider()
    
    def test_parse_json_response(self):
        """✓ Método parse_json_response funciona"""
        # Crear provider dummy para probar método
        class DummyProvider(LLMProvider):
            def generate(self, *args, **kwargs): pass
            def validate_api_key(self): return True
            def get_model_info(self): return {}
            @property
            def name(self): return "dummy"
            @property
            def model_name(self): return "dummy-model"
        
        provider = DummyProvider()
        
        # Test JSON directo
        json_str = '{"key": "value", "number": 42}'
        result = provider.parse_json_response(json_str)
        assert result["key"] == "value"
        assert result["number"] == 42
        
        # Test JSON en markdown
        markdown_json = '```json\n{"test": true}\n```'
        result = provider.parse_json_response(markdown_json)
        assert result["test"] is True
        
        # Test inválido
        with pytest.raises(ValueError):
            provider.parse_json_response("not json at all")


class TestOpenAIProvider:
    """Tests del proveedor OpenAI"""
    
    def test_openai_provider_initialization(self):
        """✓ OpenAI provider se inicializa"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider()
            assert provider.name == "openai"
            assert provider.model_name == "gpt-3.5-turbo"
    
    def test_openai_provider_custom_model(self):
        """✓ OpenAI provider acepta modelo personalizado"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(model="gpt-4")
            assert provider.model_name == "gpt-4"
    
    def test_openai_provider_get_model_info(self):
        """✓ OpenAI provider retorna info del modelo"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider(model="gpt-4")
            info = provider.get_model_info()
            
            assert "name" in info
            assert "max_tokens" in info
            assert info["max_tokens"] > 0
    
    def test_openai_provider_validate_api_key_no_key(self):
        """✓ Validación falla sin API key"""
        provider = OpenAIProvider(api_key="")
        assert provider.validate_api_key() is False
    
    def test_openai_provider_generate_no_api_key(self):
        """✓ Generate falla sin API key"""
        provider = OpenAIProvider(api_key="")
        
        with pytest.raises(LLMError):
            provider.generate("test prompt")


class TestRateLimiter:
    """Tests del rate limiter"""
    
    def test_rate_limiter_initialization(self):
        """✓ RateLimiter se inicializa"""
        limiter = RateLimiter(max_requests_per_minute=10)
        assert limiter.max_requests_per_minute == 10
        assert limiter.is_available() is True
    
    def test_rate_limiter_tracks_requests(self):
        """✓ RateLimiter cuenta requests"""
        limiter = RateLimiter(max_requests_per_minute=3)
        
        assert limiter.is_available()
        limiter.record_request()
        
        assert limiter.is_available()
        limiter.record_request()
        
        assert limiter.is_available()
        limiter.record_request()
        
        assert not limiter.is_available()  # Limite alcanzado
    
    def test_rate_limiter_circuit_breaker(self):
        """✓ Circuit breaker se activa con errores"""
        limiter = RateLimiter(error_threshold=2)
        
        assert limiter.circuit_open is False
        
        limiter.record_error()
        assert limiter.circuit_open is False
        
        limiter.record_error()
        assert limiter.circuit_open is True
        assert not limiter.is_available()
    
    def test_rate_limiter_reset(self):
        """✓ Reset limpia el state"""
        limiter = RateLimiter(max_requests_per_minute=3)
        
        limiter.record_request()
        limiter.record_request()
        limiter.record_error()
        
        limiter.reset()
        
        assert len(limiter.request_times) == 0
        assert limiter.error_count == 0
        assert limiter.circuit_open is False
        assert limiter.is_available() is True
    
    def test_rate_limiter_error_recovery(self):
        """✓ RateLimiter se recupera después de éxitos"""
        limiter = RateLimiter(error_threshold=3)
        
        limiter.record_error()
        limiter.record_error()
        
        assert limiter.error_count == 2
        assert limiter.circuit_open is False
        
        limiter.record_success()
        assert limiter.error_count == 1
        
        limiter.record_success()
        assert limiter.error_count == 0


class TestRetryDecorator:
    """Tests del decorador retry_with_rate_limit"""
    
    def test_retry_decorator_success(self):
        """✓ Decorador pasa en éxito"""
        limiter = RateLimiter()
        
        @retry_with_rate_limit(limiter, max_retries=3)
        def successful_func():
            return "success"
        
        result = successful_func()
        assert result == "success"
    
    def test_retry_decorator_retries_on_failure(self):
        """✓ Decorador reintenta en fallo"""
        limiter = RateLimiter()
        call_count = 0
        
        @retry_with_rate_limit(limiter, max_retries=3)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Fail")
            return "success"
        
        result = failing_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_decorator_exhausts_retries(self):
        """✓ Decorador falla después de exhaustar intentos"""
        limiter = RateLimiter()
        
        @retry_with_rate_limit(limiter, max_retries=2)
        def always_fails():
            raise Exception("Always fails")
        
        with pytest.raises(Exception):
            always_fails()


class TestLLMProviderInterchangeability:
    """Tests que verifican que providers son intercambiables"""
    
    def test_multiple_providers_same_interface(self):
        """✓ Diferentes providers implementan la misma interfaz"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = OpenAIProvider()
            
            # Verificar que tiene todos los métodos requeridos
            assert hasattr(provider, 'generate')
            assert hasattr(provider, 'validate_api_key')
            assert hasattr(provider, 'get_model_info')
            assert hasattr(provider, 'name')
            assert hasattr(provider, 'model_name')
    
    def test_provider_interchangeability(self):
        """✓ Providers se pueden intercambiar en código"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            providers = [
                OpenAIProvider(model="gpt-3.5-turbo"),
                OpenAIProvider(model="gpt-4"),
            ]
            
            # Mismo código funciona con ambos
            for provider in providers:
                assert isinstance(provider, LLMProvider)
                assert provider.validate_api_key() is False  # No real API key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
