#!/usr/bin/env python3
"""
Script para auto-generar type hints faltantes en archivos Python
Analiza mypy output y sugiere/aplica correcciones
"""
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

def extract_mypy_issues(file_path: str) -> List[Dict[str, Any]]:
    """Extraer issues de mypy para un archivo específico"""
    result = subprocess.run(
        ["python", "-m", "mypy", file_path, "--no-error-summary"],
        capture_output=True,
        text=True
    )
    
    issues = []
    for line in result.stdout.split('\n'):
        if not line.strip():
            continue
        # Parse format: file.py:LINE: error: MESSAGE
        match = re.match(r'([^:]+):(\d+): error: (.+)', line)
        if match:
            issues.append({
                'file': match.group(1),
                'line': int(match.group(2)),
                'message': match.group(3)
            })
    
    return issues

def suggest_fixes(issues: List[Dict[str, Any]], file_path: str) -> List[Tuple[int, str]]:
    """Sugerir correcciones basadas en issues de mypy"""
    with open(file_path) as f:
        lines = f.readlines()
    
    fixes = []
    
    for issue in issues:
        line_no = issue['line']
        msg = issue['message']
        
        # Agregar type hints para funciones
        if 'Need type annotation' in msg and 'hint' in msg:
            # Extract variable name and suggested type from hint
            hint_match = re.search(r'hint: "([^"]+)"', msg)
            if hint_match:
                suggested = hint_match.group(1)
                if line_no <= len(lines):
                    fixes.append((line_no - 1, suggested))
        
        # Fix "Function "builtins.any" is not valid as a type"
        if 'builtins.any' in msg:
            if line_no <= len(lines):
                fixes.append((line_no - 1, 'any -> Any'))
        
        # Fix implicit Optional
        if 'PEP 484 prohibits implicit Optional' in msg:
            if line_no <= len(lines):
                fixes.append((line_no - 1, 'Add Optional[...]'))
    
    return fixes

def main():
    """Main entry point"""
    print("🔧 AUTO-GENERATING TYPE HINTS...")
    print("=" * 70)
    
    # Files to process in order
    priority_files = [
        "core/orchestrator_hardened.py",
        "core/execution_queue.py",
        "core/atomic_update_system.py",
        "cgalpha/nexus/ops.py",
        "data_processor/data_system/main.py",
    ]
    
    for fpath in priority_files:
        if not Path(fpath).exists():
            print(f"⏭️  {fpath} NOT FOUND")
            continue
        
        print(f"\n📄 {fpath}")
        print("-" * 70)
        
        issues = extract_mypy_issues(fpath)
        if not issues:
            print("✅ No type hint issues found!")
            continue
        
        print(f"Found {len(issues)} type hint issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"  Line {issue['line']}: {issue['message']}")
        
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more issues")
        
        print("\nRecommendation:")
        print("  → Review mypy output manually")
        print("  → Add type hints using IDE or editor")
        print("  → Re-run mypy to validate")

if __name__ == "__main__":
    main()
