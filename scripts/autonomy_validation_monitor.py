"""
Monitor de validación pre-autonomía Cat.1
Ejecutar: python3 scripts/autonomy_validation_monitor.py
"""
import sys, json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Asegurarse de que el root del proyecto esté en el path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def check_validation_status():
    criteria_path = PROJECT_ROOT / 'scripts/autonomy_validation_criteria.json'
    if not criteria_path.exists():
        print("❌ Error: criteria.json no encontrado.")
        return False
        
    criteria = json.loads(criteria_path.read_text())
    sc = criteria['success_criteria']
    
    results = {}
    warnings = []
    failures = []
    
    # 1. Bridge: trades reales vs placeholder
    bridge_path = PROJECT_ROOT / 'aipha_memory/evolutionary/bridge.jsonl'
    if bridge_path.exists():
        try:
            lines = bridge_path.read_text().splitlines()
            trades = [json.loads(l) for l in lines if l]
            real = [t for t in trades if not t.get('is_placeholder', True)]
            placeholder_ratio = 1 - (len(real) / max(len(trades), 1))
            
            results['total_trades'] = len(trades)
            results['real_oracle_trades'] = len(real)
            results['placeholder_ratio'] = round(placeholder_ratio, 3)
            
            if len(real) < sc['min_real_oracle_trades']:
                warnings.append(
                    f"Solo {len(real)} trades con Oracle real "
                    f"(mínimo: {sc['min_real_oracle_trades']})"
                )
            if placeholder_ratio > sc['max_placeholder_ratio']:
                warnings.append(
                    f"Ratio placeholder: {placeholder_ratio:.1%} "
                    f"(máximo: {sc['max_placeholder_ratio']:.1%})"
                )
        except Exception as e:
            warnings.append(f"Error procesando bridge.jsonl: {e}")
    else:
        results['bridge'] = "No trades detected yet"
    
    # 2. Evolution log: salud del canal
    try:
        from cgalpha_v3.lila.evolution_orchestrator import EvolutionOrchestratorV4
        from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine
        
        memory = MemoryPolicyEngine()
        memory.load_from_disk()
        orchestrator = EvolutionOrchestratorV4(memory=memory)
        pending_list = orchestrator.get_pending_summary()
        pending = len(pending_list)
        
        # Para rejected_safety sí usamos el log histórico pero solo de las últimas 48h si es posible
        elog_path = PROJECT_ROOT / 'cgalpha_v3/memory/evolution_log.jsonl'
        rejected_safety = 0
        if elog_path.exists():
            lines = elog_path.read_text().splitlines()
            # De forma simplificada, contamos REJECTED_SAFETY en todo el log (o podrías filtrar por tiempo)
            for l in lines:
                if 'REJECTED_SAFETY' in l:
                    rejected_safety += 1
        
        results['pending_proposals'] = pending
        results['rejected_safety'] = rejected_safety
        
        if pending > sc['canal_health']['max_pending_proposals']:
            failures.append(
                f"Backlog Actual: {pending} propuestas pendientes "
                f"(máximo: {sc['canal_health']['max_pending_proposals']})"
            )
        
        if rejected_safety > sc['safety_envelope']['max_rejected_safety_violations']:
            warnings.append(
                f"Safety violations históricas: {rejected_safety} "
                f"(máximo sugerido: {sc['safety_envelope']['max_rejected_safety_violations']})"
            )
    except Exception as e:
        warnings.append(f"Error checking canal health: {e}")
    
    # 3. Oracle health
    try:
        from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3
        oracle = OracleTrainer_v3.create_default()
        model_path = PROJECT_ROOT / 'aipha_memory/models/oracle_v3.joblib'
        if model_path.exists():
            oracle.load_from_disk(str(model_path))
            if oracle.model and hasattr(oracle, '_training_metrics'):
                m = oracle._training_metrics
                oos = m.get('test_accuracy', 0)
                results['oracle_oos'] = oos
                results['oracle_samples'] = m.get('n_samples', 0)
                
                if oos < sc['oracle_oos_stability']['min_accuracy']:
                    failures.append(
                        f"Oracle OOS está en {oos:.3f} "
                        f"(mínimo deseado: {sc['oracle_oos_stability']['min_accuracy']})"
                    )
            else:
                 results['oracle'] = "Loaded but no metrics found (placeholder?)"
        else:
            results['oracle'] = "Model file not found"
    except Exception as e:
        warnings.append(f"No se pudo cargar Oracle: {e}")
    
    # Reporte
    print(f"\n=== VALIDACIÓN PRE-AUTONOMÍA [{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC] ===")
    print("\nMétricas:")
    for k, v in results.items():
        print(f"  {k}: {v}")
    
    if warnings:
        print(f"\n⚠️  Advertencias ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")
    
    if failures:
        print(f"\n❌ FALLOS ({len(failures)}) — NO ACTIVAR AUTONOMÍA:")
        for f in failures:
            print(f"  - {f}")
        return False
    
    print("\n✅ Todos los criterios cumplidos")
    return True

if __name__ == '__main__':
    passed = check_validation_status()
    sys.exit(0 if passed else 1)
EOF
