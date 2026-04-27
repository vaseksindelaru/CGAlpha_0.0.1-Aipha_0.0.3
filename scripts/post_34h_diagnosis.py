
import json
from pathlib import Path
from collections import Counter
import sys

def run_diagnosis():
    print('=== DIAGNÓSTICO POST-34H ===\n')

    # 1. Bridge: trades reales vs placeholder
    bridge = Path('aipha_memory/evolutionary/bridge.jsonl')
    if bridge.exists():
        try:
            trades = [json.loads(l) for l in bridge.read_text().splitlines() if l]
            real = [t for t in trades if not t.get('signal_data', {}).get('is_placeholder', True)]
            print(f'Trades totales:    {len(trades)}')
            print(f'Con Oracle real:   {len(real)} ({100*len(real)/max(len(trades),1):.1f}%)')
            if real:
                confs = [t.get('signal_data', {}).get('oracle_confidence', 0) for t in real]
                print(f'Confianza media:   {sum(confs)/len(confs):.3f}')
        except Exception as e:
            print(f'Error leyendo bridge.jsonl: {e}')
    else:
        print('bridge.jsonl no encontrado')

    print()

    # 2. Evolution log: diversidad de propuestas
    elog = Path('cgalpha_v3/memory/evolution_log.jsonl')
    if elog.exists():
        try:
            entries = [json.loads(l) for l in elog.read_text().splitlines() if l]
            attrs = Counter(e.get('spec', {}).get('target_attribute', '?') for e in entries)
            statuses = Counter(e.get('status', '?') for e in entries)
            print(f'Propuestas totales: {len(entries)}')
            print('Por atributo (top 5):')
            for attr, count in attrs.most_common(5):
                print(f'  {attr}: {count}')
            print('Por status:')
            for status, count in statuses.most_common():
                print(f'  {status}: {count}')
        except Exception as e:
            print(f'Error leyendo evolution_log.jsonl: {e}')
    else:
        print('evolution_log.jsonl no encontrado')

    print()

    # 3. Oracle actual
    try:
        sys.path.insert(0, '.')
        from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3
        o = OracleTrainer_v3.create_default()
        # Intentar cargar el modelo más reciente
        oracle_path = Path('aipha_memory/models/oracle_v3.joblib')
        if oracle_path.exists():
            o.load_from_disk(str(oracle_path))
            if o.model and o.model != 'placeholder_model_trained':
                m = o._training_metrics or {}
                print(f'Oracle: TRAINED')
                print(f'  Samples totales: {m.get("n_samples")}')
                print(f'  Train accuracy:  {m.get("train_accuracy")}')
                print(f'  Test accuracy:   {m.get("test_accuracy")} ← el número que importa')
                print(f'  Rebalance:       {m.get("rebalance_applied")}')
                dist = m.get('class_distribution', {})
                if dist:
                    total = sum(dist.values())
                    for cls, count in dist.items():
                        print(f'  {cls}: {count} ({100*count/total:.1f}%)')
            else:
                print('Oracle: PLACEHOLDER (no entrenó)')
        else:
            print('Archivo oracle_v3.joblib no encontrado')
    except Exception as e:
        print(f'Error cargando Oracle: {e}')

    print()
    print('=== FIN DIAGNÓSTICO ===')

if __name__ == "__main__":
    run_diagnosis()
