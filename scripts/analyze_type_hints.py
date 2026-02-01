#!/usr/bin/env python3
"""
Script para analizar y reportar necesidades de type hints
"""
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

def run_mypy(target: str = "core/") -> Dict[str, Any]:
    """Ejecutar mypy y retornar resultados"""
    result = subprocess.run(
        ["python", "-m", "mypy", target, "--json", "--no-error-summary"],
        capture_output=True,
        text=True
    )
    
    try:
        return json.loads(result.stdout) if result.stdout else {}
    except:
        return {}

def run_pyright(target: str = "core/") -> Dict[str, Any]:
    """Ejecutar pyright y retornar resultados"""
    result = subprocess.run(
        ["pyright", target, "--outputjson"],
        capture_output=True,
        text=True
    )
    
    try:
        data = json.loads(result.stdout) if result.stdout else {}
        return data
    except:
        return {}

def analyze_files_needing_hints() -> List[str]:
    """Analizar qué archivos necesitan type hints"""
    print("📊 ANALYZING TYPE HINTS COVERAGE...")
    print("=" * 70)
    
    # Archivos priorizados según el roadmap
    priority_files = {
        "Tier 1 - CRÍTICA": [
            "core/orchestrator_hardened.py",
            "core/health_monitor.py",
            "core/memory_manager.py",
            "data_processor/data_system/main.py",
            "data_processor/data_system/fetcher.py",
            "core/config_manager.py",
        ],
        "Tier 2 - IMPORTANTE": [
            "core/execution_queue.py",
            "core/quarantine_manager.py",
            "core/change_evaluator.py",
            "core/atomic_update_system.py",
            "oracle/strategies/self_improvement_loop.py",
            "cgalpha/nexus/ops.py",
            "cgalpha/labs/risk_barrier_lab.py",
        ]
    }
    
    for tier, files in priority_files.items():
        print(f"\n{tier}")
        print("-" * 70)
        for fpath in files:
            if Path(fpath).exists():
                # Count def statements (functions/methods)
                with open(fpath) as f:
                    content = f.read()
                    defs = content.count("def ")
                    # Rough estimate: lines with type hints
                    type_hints = len([l for l in content.split('\n') if '->' in l or ': ' in l and 'def' in l])
                    coverage = int((type_hints / max(defs, 1)) * 100)
                    
                lines = len(content.split('\n'))
                status = "✅" if coverage >= 85 else "⚠️" if coverage >= 50 else "❌"
                print(f"{status} {fpath:<45} ({lines:>3}L, {coverage:>3}% coverage)")
            else:
                print(f"❌ {fpath:<45} NOT FOUND")

if __name__ == "__main__":
    analyze_files_needing_hints()
    print("\n" + "=" * 70)
    print("Run the following to fix type hints issues:")
    print("  python -m mypy core/ --no-error-summary")
    print("  pyright core/")
