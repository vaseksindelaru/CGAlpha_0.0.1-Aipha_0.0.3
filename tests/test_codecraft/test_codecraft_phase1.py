"""
Tests para Code Craft Sage - Fase 1

Tests comprehensivos para TechnicalSpec y ProposalParser.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType
from cgalpha.codecraft.proposal_parser import ProposalParser


class TestTechnicalSpec:
    """Tests para TechnicalSpec dataclass"""
    
    def test_create_basic_spec(self):
        """Test creación básica de spec"""
        spec = TechnicalSpec(
            proposal_id="TEST_001",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="core/oracle.py",
            class_name="Oracle",
            attribute_name="confidence",
            old_value=0.7,
            new_value=0.65,
            data_type="float"
        )
        
        assert spec.proposal_id == "TEST_001"
        assert spec.change_type == ChangeType.PARAMETER_CHANGE
        assert spec.file_path == "core/oracle.py"
        assert spec.old_value == 0.7
        assert spec.new_value == 0.65
    
    def test_serialization_to_dict(self):
        """Test serialización a diccionario"""
        spec = TechnicalSpec(
            proposal_id="TEST_002",
            change_type=ChangeType.CONFIG_UPDATE,
            file_path="config/app.json"
        )
        
        data = spec.to_dict()
        
        assert isinstance(data, dict)
        assert data["proposal_id"] == "TEST_002"
        assert data["change_type"] == "config_update"  # Enum convertido a string
        assert data["file_path"] == "config/app.json"
    
    def test_deserialization_from_dict(self):
        """Test deserialización desde diccionario"""
        data = {
            "proposal_id": "TEST_003",
            "change_type": "parameter_change",
            "file_path": "core/test.py",
            "class_name": "TestClass",
            "attribute_name": "test_attr",
            "old_value": None,
            "new_value": 42,
            "validation_rules": None,
            "data_type": "int",
            "affected_tests": [],
            "documentation_files": [],
            "source_proposal": "",
            "confidence_score": 0.8
        }
        
        spec = TechnicalSpec.from_dict(data)
        
        assert spec.proposal_id == "TEST_003"
        assert spec.change_type == ChangeType.PARAMETER_CHANGE
        assert spec.new_value == 42
        assert spec.data_type == "int"
    
    def test_json_serialization(self):
        """Test serialización/deserialización JSON"""
        spec1 = TechnicalSpec(
            proposal_id="TEST_JSON",
            change_type=ChangeType.METHOD_ADDITION,
            file_path="core/utils.py",
            method_name="helper_function"
        )
        
        # Serializar
        json_str = spec1.to_json()
        assert isinstance(json_str, str)
        
        # Deserializar
        spec2 = TechnicalSpec.from_json(json_str)
        
        assert spec2.proposal_id == spec1.proposal_id
        assert spec2.change_type == spec1.change_type
        assert spec2.file_path == spec1.file_path
        assert spec2.method_name == spec1.method_name
    
    def test_cache_key_generation(self):
        """Test generación de cache key"""
        spec = TechnicalSpec(
            proposal_id="TEST_CACHE",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="test.py",
            source_proposal="Test proposal text"
        )
        
        key = spec.get_cache_key()
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5 hash length
    
    def test_validation_success(self):
        """Test validación exitosa"""
        spec = TechnicalSpec(
            proposal_id="VALID_SPEC",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="core/test.py",
            attribute_name="threshold",
            new_value=0.75,
            validation_rules={"min": 0.5, "max": 0.9},
            confidence_score=0.8
        )
        
        is_valid, error = spec.is_valid()
        
        assert is_valid is True
        assert error is None
    
    def test_validation_fail_missing_id(self):
        """Test validación falla sin proposal_id"""
        spec = TechnicalSpec(
            proposal_id="",  # Vacío
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="test.py"
        )
        
        is_valid, error = spec.is_valid()
        
        assert is_valid is False
        assert "proposal_id" in error
    
    def test_validation_fail_path_traversal(self):
        """Test validación detecta path traversal"""
        spec = TechnicalSpec(
            proposal_id="ATTACK",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="../../../etc/passwd"  # Path traversal attack
        )
        
        is_valid, error = spec.is_valid()
        
        assert is_valid is False
        assert "path traversal" in error.lower()
    
    def test_validation_fail_value_out_of_range(self):
        """Test validación detecta valor fuera de rango"""
        spec = TechnicalSpec(
            proposal_id="OUT_OF_RANGE",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="test.py",
            new_value=1.5,
            validation_rules={"min": 0.0, "max": 1.0},
            confidence_score=0.5
        )
        
        is_valid, error = spec.is_valid()
        
        assert is_valid is False
        assert "fuera de rango" in error.lower()


class TestProposalParser:
    """Tests para ProposalParser"""
    
    def test_parser_initialization_no_deps(self):
        """Test inicialización sin dependencias"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        assert parser is not None
        assert parser.metrics["total_parses"] == 0
    
    def test_parse_with_heuristics(self):
        """Test parsing con heurísticas (sin LLM)"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        proposal = "Cambiar confidence_threshold de 0.70 a 0.65"
        spec = parser.parse(proposal)
        
        assert spec is not None
        assert spec.attribute_name == "confidence_threshold"
        assert spec.old_value == 0.70
        assert spec.new_value == 0.65
        assert spec.data_type == "float"
    
    def test_parse_with_mocked_llm(self):
        """Test parsing con LLM mockeado"""
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.generate = Mock(return_value=json.dumps({
            "change_type": "parameter_change",
            "file_path": "oracle/oracle_v2.py",
            "class_name": "OracleV2",
            "attribute_name": "confidence_threshold",
            "old_value": 0.70,
            "new_value": 0.65,
            "data_type": "float",
            "validation_rules": {"min": 0.5, "max": 0.95}
        }))
        
        parser = ProposalParser(redis_client=None, llm_assistant=mock_llm)
        
        proposal = "Cambiar confidence_threshold de 0.70 a 0.65 en OracleV2"
        spec = parser.parse(proposal)
        
        assert spec.class_name == "OracleV2"
        assert spec.attribute_name == "confidence_threshold"
        assert spec.old_value == 0.70
        assert spec.new_value == 0.65
        assert mock_llm.generate.called
    
    def test_cache_behavior(self):
        """Test comportamiento del cache"""
        # Mock Redis
        mock_redis = Mock()
        mock_redis.is_connected = Mock(return_value=True)
        mock_redis.get_system_state = Mock(return_value=None)  # Cache miss
        mock_redis.cache_system_state = Mock()
        
        parser = ProposalParser(redis_client=mock_redis, llm_assistant=None)
        
        proposal = "Cambiar timeout de 30 a 60"
        spec = parser.parse(proposal)
        
        # Verificar que se intentó guardar en cache
        assert mock_redis.cache_system_state.called
        assert parser.metrics["cache_misses"] == 1
    
    def test_metrics_tracking(self):
        """Test tracking de métricas"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        # Parse varias propuestas
        proposals = [
            "Cambiar X de 1 a 2",
            "Modificar Y de 3 a 4",
            "Actualizar Z de 5 a 6"
        ]
        
        for proposal in proposals:
            parser.parse(proposal)
        
        metrics = parser.get_metrics()
        
        assert metrics["total_parses"] == 3
        assert metrics["heuristic_fallbacks"] >= 1
        assert "cache_hit_rate" in metrics
    
    def test_proposal_id_generation(self):
        """Test generación automática de proposal_id"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        spec = parser.parse("Cambiar valor de 1 a 2")
        
        assert spec.proposal_id.startswith("PROP_")
        assert len(spec.proposal_id) > 10  # PROP_YYYYMMDD_HHMMSS_hash
    
    def test_extract_json_from_markdown(self):
        """Test extracción de JSON de respuesta con markdown"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        # Respuesta con markdown code block
        response = """```json
        {
            "change_type": "parameter_change",
            "file_path": "test.py"
        }
        ```"""
        
        result = parser._extract_json_from_response(response)
        
        assert isinstance(result, dict)
        assert result["change_type"] == "parameter_change"
        assert result["file_path"] == "test.py"
    
    def test_fix_invalid_spec(self):
        """Test corrección automática de spec inválido"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        # Spec con path inválido
        spec = TechnicalSpec(
            proposal_id="INVALID",
            change_type=ChangeType.PARAMETER_CHANGE,
            file_path="../../../bad/path",
            confidence_score=1.5  # Fuera de rango
        )
        
        fixed_spec = parser._fix_spec(spec)
        
        assert ".." not in fixed_spec.file_path
        assert 0.0 <= fixed_spec.confidence_score <= 1.0


# Integration tests
class TestIntegration:
    """Tests de integración"""
    
    def test_end_to_end_parsing(self):
        """Test end-to-end de parsing completo"""
        parser = ProposalParser(redis_client=None, llm_assistant=None)
        
        proposal = "Cambiar max_drawdown de 0.20 a 0.15 en RiskManager"
        
        # Parse
        spec = parser.parse(proposal, proposal_id="E2E_TEST")
        
        # Verificaciones
        assert spec.proposal_id == "E2E_TEST"
        assert spec.source_proposal == proposal
        assert spec.attribute_name == "max_drawdown"
        assert spec.old_value == 0.20
        assert spec.new_value == 0.15
        
        # Validar
        is_valid, error = spec.is_valid()
        assert is_valid is True
        
        # Serializar
        json_str = spec.to_json()
        assert json_str is not None
        
        # Deserializar
        spec2 = TechnicalSpec.from_json(json_str)
        assert spec2.proposal_id == spec.proposal_id
