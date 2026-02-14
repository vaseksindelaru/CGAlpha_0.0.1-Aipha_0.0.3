#!/usr/bin/env python3
"""
Code Craft Sage - Fase 2 Demostración: AST Modifier

Demuestra el flujo completo desde parsing hasta modificación segura de código.
"""

import sys
import logging
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from cgalpha.codecraft import ProposalParser, TechnicalSpec, ChangeType
from cgalpha.codecraft.ast_modifier import ASTModifier
from cgalpha.codecraft.safety_validator import SafetyValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger("Phase2Demo")


def demo_ast_modification():
    """Demuestra modificación AST completa"""
    print("\n" + "="*80)
    print("🔧 DEMO 1: Modificación AST")
    print("="*80)
    
    # Crear archivo temporal de prueba
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_code = """class OracleV2:
    \"\"\"Oracle para predicciones\"\"\"
    def __init__(self):
        self.confidence_threshold = 0.70  # Línea a modificar
        self.max_predictions = 100
    
    def predict(self):
        return self.confidence_threshold
"""
        f.write(test_code)
        test_file = f.name
    
    print(f"\n📄 Archivo de prueba creado: {test_file}")
    print(f"📝 Código original:")
    print(test_code)
    
    # Crear spec
    spec = TechnicalSpec(
        proposal_id="DEMO_AST_001",
        change_type=ChangeType.PARAMETER_CHANGE,
        file_path=test_file,
        class_name="OracleV2",
        attribute_name="confidence_threshold",
        old_value=0.70,
        new_value=0.65,
        data_type="float",
        validation_rules={"min": 0.5, "max": 0.9}
    )
    
    print(f"\n🎯 TechnicalSpec:")
    print(f"   Cambio: {spec.attribute_name} {spec.old_value} → {spec.new_value}")
    
    # Modificar
    modifier = ASTModifier()
    result = modifier.modify_file(spec)
    
    print(f"\n📊 Resultado:")
    print(f"   ✅" if result["success"] else "   ❌", f"Success: {result['success']}")
    print(f"   💾 Backup: {result['backup_path']}")
    print(f"   📝 Changes: {len(result['changes_made'])}")
    print(f"   🔒 Hash: {result['original_hash'][:8] if result['original_hash'] else 'N/A'} → {result['new_hash'][:8] if result['new_hash'] else 'N/A'}")
    
     # Leer código modificado
    if result["success"]:
        modified_code = Path(test_file).read_text()
        print(f"\n📝 Código modificado:")
        print(modified_code)
    
    # Cleanup
    Path(test_file).unlink()


def demo_safety_validation():
    """Demuestra validación de seguridad"""
    print("\n" + "="*80)
    print("🛡️ DEMO 2: Validación de Seguridad")
    print("="*80)
    
    validator = SafetyValidator()
    
    original_code = """import os
class Config:
    value = 0.70
"""
    
    modified_code = """import os
class Config:
    value = 0.65
"""
    
    spec = TechnicalSpec(
        proposal_id="SAFETY_DEMO",
        change_type=ChangeType.PARAMETER_CHANGE,
        file_path="config.py",
        class_name="Config",
        attribute_name="value",
        old_value=0.70,
        new_value=0.65,
        data_type="float"
    )
    
    validation = validator.validate_change(spec, original_code, modified_code)
    
    print(f"\n📊 Resultados de validación:")
    print(f"   ✅ Sintaxis válida: {validation['syntax_valid']}")
    print(f"   ✅ Imports intactos: {validation['imports_intact']}")
    print(f"   ✅ Tipos consistentes: {validation['type_consistency']}")
    print(f"   ⚠️  Risk Score: {validation['risk_score']:.2f}")
    
    if validation["warnings"]:
        print(f"\n   ⚠️  Warnings:")
        for warning in validation["warnings"]:
            print(f"      - {warning}")
    
    if validation["errors"]:
        print(f"\n   ❌ Errors:")
        for error in validation["errors"]:
            print(f"      - {error}")


def demo_full_workflow():
    """Demuestra workflow completo: parse → modify → validate"""
    print("\n" + "="*80)
    print("🚀 DEMO 3: Workflow Completo")
    print("="*80)
    
    # 1. Parsear propuesta
    print(f"\n📋 Paso 1: Parsear propuesta")
    parser = ProposalParser()
    proposal_text = "Cambiar confidence_threshold de 0.70 a 0.65 en OracleV2"
    spec = parser.parse(proposal_text)
    
    print(f"   📝 Propuesta: '{proposal_text}'")
    print(f"   ✅ Parseado: {spec.attribute_name} = {spec.new_value}")
    
    # 2. Pre-validar
    print(f"\n🔍 Paso 2: Pre-validación")
    validator = SafetyValidator()
    
    # Nota: archivo no existe, pero mostramos la validación
    print(f"   ⚠️  Archivo {spec.file_path} no existe (ejemplo)")
    print(f"   ✅ Spec es válido: {spec.is_valid()[0]}")
    
    # 3. Mostrar lo que haría el modifier
    print(f"\n🔧 Paso 3: Modificación (simulado)")
    print(f"   📄 Archivo objetivo: {spec.file_path}")
    print(f"   🏗️  Clase: {spec.class_name}")
    print(f"   🔧 Atributo: {spec.attribute_name}")
    print(f"   📊 Cambio: {spec.old_value} → {spec.new_value}")
    print(f"   💾 Backup se crearía automáticamente")
    print(f"   ✅ Validación post-modificación")
    
    print(f"\n📊 Métricas del parser:")
    metrics = parser.get_metrics()
    print(f"   Total parses: {metrics['total_parses']}")
    print(f"   Cache hit rate: {metrics['cache_hit_rate']*100:.0f}%")


def demo_backup_and_rollback():
    """Demuestra sistema de backup y rollback"""
    print("\n" + "="*80)
    print("💾 DEMO 4: Backup y Rollback")
    print("="*80)
    
    modifier = ASTModifier()
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("original_value = 123")
        test_file = f.name
    
    # Crear backup
    backup_path = modifier._create_backup(Path(test_file), "original_value = 123")
    
    print(f"\n📄 Archivo original: {test_file}")
    print(f"💾 Backup creado: {backup_path}")
    print(f"   ✅ Backup existe: {backup_path.exists()}")
    print(f"   📏 Tamaño: {backup_path.stat().st_size} bytes")
    
    # Mostrar historial de backups
    history = modifier.get_backup_history(test_file)
    print(f"\n📊 Historial de backups:")
    for i, backup in enumerate(history, 1):
        print(f"   {i}. {Path(backup['path']).name}")
        print(f"      Tamaño: {backup['size']} bytes")
        print(f"      Creado: {backup['created']}")
    
    # Cleanup
    Path(test_file).unlink()
    if backup_path.exists():
        backup_path.unlink()


def main():
    """Ejecuta todos los demos"""
    print("\n")
    print("🎨 " + "="*76 + " 🎨")
    print("🎨  CODE CRAFT SAGE - FASE 2: AST MODIFIER  🎨")
    print("🎨 " + "="*76 + " 🎨")
    
    try:
        demo_ast_modification()
        demo_safety_validation()
        demo_full_workflow()
        demo_backup_and_rollback()
        
        print("\n" + "="*80)
        print("✅ Todos los demos de Fase 2 completados")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Error en demo: {e}", exc_info=True)
        print(f"\n❌ Demo falló: {e}\n")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
