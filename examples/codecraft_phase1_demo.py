#!/usr/bin/env python3
"""
Code Craft Sage - Fase 1 Demostración

Este script demuestra las capacidades de parsing de propuestas
de Code Craft Sage Fase 1.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cgalpha.codecraft import ProposalParser, TechnicalSpec, ChangeType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("CodeCraftDemo")


def demo_basic_parsing():
    """Demuestra parsing básico de propuestas"""
    print("\n" + "="*70)
    print("📋 DEMO 1: Parsing Básico")
    print("="*70)
    
    parser = ProposalParser()
    
    # Propuesta de ejemplo
    proposal_text = "Cambiar confidence_threshold de 0.70 a 0.65 en OracleV2"
    
    print(f"\n📝 Propuesta:")
    print(f"   '{proposal_text}'")
    
    # Parsear
    print(f"\n🔍 Parseando...")
    spec = parser.parse(proposal_text)
    
    # Mostrar resultados
    print(f"\n✅ Resultado:")
    print(f"   📄 Archivo: {spec.file_path}")
    print(f"   🏗️ Clase: {spec.class_name}")
    print(f"   🔧 Atributo: {spec.attribute_name}")
    print(f"   📊 Tipo: {spec.data_type}")
    print(f"   📈 Valor antiguo: {spec.old_value}")
    print(f"   🎯 Valor nuevo: {spec.new_value}")
    print(f"   ✅ Validación: {spec.validation_rules}")
    print(f"   🎓 Confianza: {spec.confidence_score}")
    print(f"   🔑 Cache key: {spec.get_cache_key()[:16]}...")
    
    # Validar
    is_valid, error = spec.is_valid()
    if is_valid:
        print(f"\n   ✅ Especificación VÁLIDA")
    else:
        print(f"\n   ❌ Especificación INVÁLIDA: {error}")


def demo_cache_behavior():
    """Demuestra comportamiento del cache Redis"""
    print("\n" + "="*70)
    print("💾 DEMO 2: Cache Redis")
    print("="*70)
    
    parser = ProposalParser()
    
    proposal_text = "Actualizar max_drawdown de 0.20 a 0.15 en RiskManager"
    
    # Primera llamada (CACHE MISS esperado)
    print(f"\n🔍 Primera llamada (esperando CACHE MISS)...")
    spec1 = parser.parse(proposal_text)
    print(f"   ✅ Parseado: {spec1.attribute_name} = {spec1.new_value}")
    
    # Segunda llamada (CACHE HIT esperado)
    print(f"\n🔍 Segunda llamada (esperando CACHE HIT)...")
    spec2 = parser.parse(proposal_text)
    print(f"   ✅ Parseado: {spec2.attribute_name} = {spec2.new_value}")
    
    # Mostrar métricas
    metrics = parser.get_metrics()
    print(f"\n📊 Métricas del Parser:")
    print(f"   Total parses: {metrics['total_parses']}")
    print(f"   Cache hits: {metrics['cache_hits']}")
    print(f"   Cache misses: {metrics['cache_misses']}")
    print(f"   Cache hit rate: {metrics['cache_hit_rate']*100:.1f}%")
    print(f"   LLM calls: {metrics['llm_calls']}")
    print(f"   Heuristic fallbacks: {metrics['heuristic_fallbacks']}")


def demo_multiple_proposals():
    """Demuestra parsing de múltiples tipos de propuestas"""
    print("\n" + "="*70)
    print("🔄 DEMO 3: Múltiples Tipos de Propuestas")
    print("="*70)
    
    parser = ProposalParser()
    
    proposals = [
        "Cambiar stop_loss de 0.02 a 0.015 en TradingStrategy",
        "Modificar timeout de 30 a 60 en ConnectionManager",
       "Actualizar configuración log_level a DEBUG",
        "Añadir método calculate_sharpe_ratio en PerformanceAnalyzer"
    ]
    
    for i, proposal in enumerate(proposals, 1):
        print(f"\n📝 Propuesta {i}: '{proposal}'")
        spec = parser.parse(proposal)
        print(f"   → Tipo: {spec.change_type.value}")
        print(f"   → Archivo: {spec.file_path}")
        print(f"   → Cambio: {spec.attribute_name or spec.method_name}")
        print(f"   → Confianza: {spec.confidence_score}")


def demo_serialization():
    """Demuestra serialización/deserialización"""
    print("\n" + "="*70)
    print("💿 DEMO 4: Serialización")
    print("="*70)
    
    # Crear spec manualmente
    spec = TechnicalSpec(
        proposal_id="DEMO_001",
        change_type=ChangeType.PARAMETER_CHANGE,
        file_path="oracle/oracle_v2.py",
        class_name="OracleV2",
        attribute_name="confidence_threshold",
        old_value=0.70,
        new_value=0.65,
        data_type="float",
        validation_rules={"min": 0.5, "max": 0.9},
        source_proposal="Demo proposal",
        confidence_score=0.95
    )
    
    print(f"\n📦 TechnicalSpec original:")
    print(f"   {spec}")
    
    # Serializar a JSON
    json_str = spec.to_json()
    print(f"\n📄 JSON serializado:")
    print(f"   {json_str[:200]}...")
    
    # Deserializar
    spec_restored = TechnicalSpec.from_json(json_str)
    print(f"\n📦 TechnicalSpec restaurado:")
    print(f"   {spec_restored}")
    
    # Verificar igualdad
    match = (spec.to_dict() == spec_restored.to_dict())
    print(f"\n   {'✅' if match else '❌'} Serialización {'exitosa' if match else 'fallida'}")


def main():
    """Ejecuta todos los demos"""
    print("\n")
    print("🎨 " + "="*66 + " 🎨")
    print("🎨  CODE CRAFT SAGE - FASE 1 DEMOSTRACIÓN  🎨")
    print("🎨 " + "="*66 + " 🎨")
    
    try:
        demo_basic_parsing()
        demo_cache_behavior()
        demo_multiple_proposals()
        demo_serialization()
        
        print("\n" + "="*70)
        print("✅ Todos los demos completados exitosamente")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Error en demo: {e}", exc_info=True)
        print(f"\n❌ Demo falló: {e}\n")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
