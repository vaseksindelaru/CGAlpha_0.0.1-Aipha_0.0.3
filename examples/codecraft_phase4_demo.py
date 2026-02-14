#!/usr/bin/env python3
"""
Code Craft Sage - Fase 4 Demo: Git Automator

Este script demuestra el ciclo completo de Code Craft Sage hasta la Fase 4:
1. Parsear propuesta (Fase 1)
2. Modificar código (Fase 2)
3. Generar y validar tests (Fase 3)
4. Crear rama Git y hacer commit (Fase 4)

SEGURIDAD:
- Este demo usa un repositorio Git temporal para no afectar el repo principal
- NUNCA hace push automático a remoto
- NUNCA modifica la rama principal (main/master)
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cgalpha.codecraft.proposal_parser import ProposalParser
from cgalpha.codecraft.ast_modifier import ASTModifier
from cgalpha.codecraft.test_generator import TestGenerator
from cgalpha.codecraft.git_automator import GitAutomator, GitAutomatorError
from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType


def setup_temp_repo():
    """
    Crea un repositorio Git temporal para el demo.
    
    Returns:
        Tuple (temp_dir, repo_path)
    """
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp(prefix="codecraft_demo_")
    print(f"📁 Directorio temporal creado: {temp_dir}")
    
    # Inicializar repositorio Git
    import git
    repo = git.Repo.init(temp_dir)
    
    # Crear un archivo de ejemplo
    example_file = Path(temp_dir) / "example_module.py"
    example_file.write_text("""
class ExampleClass:
    \"\"\"Example class for Code Craft Sage demo.\"\"\"
    
    def __init__(self):
        self.threshold = 0.3
        self.confidence = 0.5
    
    def process(self, data):
        \"\"\"Process data with current threshold.\"\"\"
        return data * self.threshold
""")
    
    # Hacer commit inicial
    repo.index.add(["example_module.py"])
    repo.index.commit("Initial commit: Add example module")
    
    print(f"✅ Repositorio Git inicializado en: {temp_dir}")
    
    return temp_dir, temp_dir


def cleanup_temp_repo(temp_dir):
    """
    Limpia el repositorio temporal.
    
    Args:
        temp_dir: Directorio temporal a limpiar
    """
    try:
        shutil.rmtree(temp_dir)
        print(f"🧹 Directorio temporal eliminado: {temp_dir}")
    except Exception as e:
        print(f"⚠️  Error limpiando directorio temporal: {e}")


def print_section(title):
    """Imprime una sección con formato."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_phase1_proposal_parser():
    """Demo de la Fase 1: Proposal Parser."""
    print_section("FASE 1: Proposal Parser")
    
    # Propuesta de ejemplo
    proposal = "Update the threshold parameter in ExampleClass from 0.3 to 0.65"
    print(f"📝 Propuesta: {proposal}")
    
    # Crear parser y parsear propuesta
    parser = ProposalParser()
    spec = parser.parse(proposal)
    
    print(f"\n✅ Especificación técnica generada:")
    print(f"   - Proposal ID: {spec.proposal_id}")
    print(f"   - Change Type: {spec.change_type.value}")
    print(f"   - File Path: {spec.file_path}")
    print(f"   - Class Name: {spec.class_name}")
    print(f"   - Attribute: {spec.attribute_name}")
    print(f"   - Old Value: {spec.old_value}")
    print(f"   - New Value: {spec.new_value}")
    print(f"   - Data Type: {spec.data_type}")
    
    return spec


def demo_phase2_ast_modifier(spec, temp_dir):
    """Demo de la Fase 2: AST Modifier."""
    print_section("FASE 2: AST Modifier")
    
    # Ruta al archivo de ejemplo
    file_path = Path(temp_dir) / "example_module.py"
    
    print(f"📄 Archivo a modificar: {file_path}")
    print(f"\nContenido original:")
    print("-" * 70)
    print(file_path.read_text())
    print("-" * 70)
    
    # Crear modifier y aplicar cambio
    modifier = ASTModifier()
    modified_file = modifier.apply_change(spec, str(file_path))
    
    print(f"\n✅ Código modificado exitosamente")
    print(f"\nContenido modificado:")
    print("-" * 70)
    print(file_path.read_text())
    print("-" * 70)
    
    return modified_file


def demo_phase3_test_generator(spec, modified_file):
    """Demo de la Fase 3: Test Generator."""
    print_section("FASE 3: Test Generator")
    
    # Crear generador de tests
    generator = TestGenerator()
    
    print(f"🧪 Generando y validando tests...")
    
    # Generar y validar tests
    result = generator.generate_and_validate(spec, modified_file)
    
    print(f"\n✅ Resultados de validación:")
    print(f"   - Test Path: {result['new_test_path']}")
    print(f"   - New Test Status: {result['new_test_status']}")
    print(f"   - Regression Status: {result['regression_status']}")
    print(f"   - Coverage: {result['coverage_percentage']}%")
    print(f"   - Overall Status: {result['overall_status']}")
    
    if result['details']['warnings']:
        print(f"\n⚠️  Advertencias:")
        for warning in result['details']['warnings']:
            print(f"   - {warning}")
    
    # Mostrar contenido del test generado
    if result['new_test_path'] and Path(result['new_test_path']).exists():
        print(f"\n📄 Contenido del test generado:")
        print("-" * 70)
        print(Path(result['new_test_path']).read_text())
        print("-" * 70)
    
    return result


def demo_phase4_git_automator(spec, modified_file, test_result, temp_dir):
    """Demo de la Fase 4: Git Automator."""
    print_section("FASE 4: Git Automator")
    
    # Verificar que la validación fue exitosa
    if test_result['overall_status'] != 'ready':
        print(f"❌ No se puede proceder con Git Automator")
        print(f"   El resultado de validación es: {test_result['overall_status']}")
        return None, None
    
    # Crear automator de Git
    automator = GitAutomator(temp_dir)
    
    # Mostrar estado actual del repo
    print(f"📊 Estado actual del repositorio:")
    status = automator.get_status()
    print(f"   - Rama actual: {status['current_branch']}")
    print(f"   - Repo limpio: {status['is_clean']}")
    print(f"   - Archivos modificados: {len(status['modified_files'])}")
    print(f"   - Archivos no rastreados: {len(status['untracked_files'])}")
    
    # Crear rama de feature
    print(f"\n🌿 Creando rama de feature...")
    try:
        branch_name = automator.create_feature_branch(spec.proposal_id)
        print(f"✅ Rama creada/cambiada: {branch_name}")
    except GitAutomatorError as e:
        print(f"❌ Error creando rama: {e}")
        return None, None
    
    # Preparar lista de archivos para commit
    files_changed = [modified_file]
    if test_result['new_test_path']:
        # Convertir ruta absoluta a relativa
        test_path_rel = Path(test_result['new_test_path']).relative_to(temp_dir)
        files_changed.append(str(test_path_rel))
    
    print(f"\n📝 Archivos para commit:")
    for file_path in files_changed:
        print(f"   - {file_path}")
    
    # Hacer commit
    print(f"\n💾 Haciendo commit...")
    try:
        commit_hash = automator.commit_changes(spec, files_changed)
        print(f"✅ Commit creado exitosamente")
        print(f"   - Hash: {commit_hash}")
    except GitAutomatorError as e:
        print(f"❌ Error haciendo commit: {e}")
        return None, None
    
    # Mostrar información del commit
    print(f"\n📋 Información del commit:")
    commit_info = automator.get_commit_info(commit_hash)
    print(f"   - Hash: {commit_info['hash']}")
    print(f"   - Autor: {commit_info['author']}")
    print(f"   - Fecha: {commit_info['date']}")
    print(f"   - Mensaje:")
    for line in commit_info['message'].split('\n'):
        print(f"     {line}")
    
    # Mostrar commits recientes
    print(f"\n📜 Commits recientes:")
    recent_commits = automator.get_recent_commits(limit=5)
    for i, commit in enumerate(recent_commits, 1):
        print(f"   {i}. {commit['hash'][:8]} - {commit['message']}")
    
    # Mostrar estado final del repo
    print(f"\n📊 Estado final del repositorio:")
    status = automator.get_status()
    print(f"   - Rama actual: {status['current_branch']}")
    print(f"   - Repo limpio: {status['is_clean']}")
    
    return branch_name, commit_hash


def main():
    """Función principal del demo."""
    print("\n" + "=" * 70)
    print("  Code Craft Sage - Fase 4 Demo: Git Automator")
    print("  Ciclo completo: Parse → Modify → Validate → Git")
    print("=" * 70)
    
    # Configurar repositorio temporal
    temp_dir, repo_path = setup_temp_repo()
    
    try:
        # Fase 1: Proposal Parser
        spec = demo_phase1_proposal_parser()
        
        # Fase 2: AST Modifier
        modified_file = demo_phase2_ast_modifier(spec, temp_dir)
        
        # Fase 3: Test Generator
        test_result = demo_phase3_test_generator(spec, modified_file)
        
        # Fase 4: Git Automator
        branch_name, commit_hash = demo_phase4_git_automator(
            spec, modified_file, test_result, temp_dir
        )
        
        # Resumen final
        print_section("RESUMEN FINAL")
        if branch_name and commit_hash:
            print(f"✅ Demo completado exitosamente")
            print(f"   - Rama creada: {branch_name}")
            print(f"   - Commit hash: {commit_hash}")
            print(f"   - Repositorio temporal: {temp_dir}")
            print(f"\n📌 NOTA: El repositorio temporal NO se ha eliminado")
            print(f"   Puedes inspeccionarlo manualmente si lo deseas:")
            print(f"   cd {temp_dir}")
            print(f"   git log --oneline")
            print(f"   git show {commit_hash}")
        else:
            print(f"❌ Demo completado con errores")
        
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Preguntar si limpiar el directorio temporal
        print(f"\n¿Deseas limpiar el directorio temporal? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                cleanup_temp_repo(temp_dir)
            else:
                print(f"📁 Directorio temporal conservado en: {temp_dir}")
        except (EOFError, KeyboardInterrupt):
            print(f"\n📁 Directorio temporal conservado en: {temp_dir}")
    
    print("\n" + "=" * 70)
    print("  Fin del Demo - Code Craft Sage Fase 4")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
