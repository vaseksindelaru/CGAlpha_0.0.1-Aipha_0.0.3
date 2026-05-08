"""
Fase 10: Retraining Oracle v5 with High-Fidelity L2 Metrics
===========================================================
"""

import sys
import json
import logging
from pathlib import Path

# Ensure project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("phase10")

def main():
    print("=" * 60)
    print("  Fase 10: Oracle v5 Retraining (High-Fidelity L2)")
    print("=" * 60)

    dataset_path = PROJECT_ROOT / "aipha_memory/operational/training_dataset_v2.jsonl"
    if not dataset_path.exists():
        logger.error(f"Dataset no encontrado: {dataset_path}")
        return

    # 1. Leer JSONL
    samples = []
    with open(dataset_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logger.warning(f"Error parseando linea: {e}")

    logger.info(f"✅ Cargados {len(samples)} samples desde dataset L2")

    # 2. Inicializar y Entrenar Oracle v5
    oracle = OracleTrainer_v3.create_default()
    oracle.load_training_dataset(samples)
    
    oracle.train_model()
    
    metrics = oracle.get_training_metrics()
    if not metrics or metrics.get("quality_gate") == "FAILED":
        logger.error("❌ El entrenamiento falló. Revisa Data Quality Gate.")
        return

    # 3. Mostrar métricas y guardar
    if metrics:
        print("\n📊 Métricas OOS Reales (Fase 10 - Oracle v5):")
        print(f"   Accuracy Test : {metrics['test_accuracy']:.2%}")
        print(f"   Accuracy Train: {metrics['train_accuracy']:.2%}")
        print(f"   Brier Score   : {metrics['brier_score']:.4f}")
        print(f"   Muestras      : {metrics['n_samples']} validas de {len(samples)} totales")
        print(f"   Top Features  : {sorted(metrics['feature_importances'].items(), key=lambda x: x[1], reverse=True)[:3]}")

        model_dest = PROJECT_ROOT / "aipha_memory/data/models/oracle_v5.joblib"
        model_dest.parent.mkdir(parents=True, exist_ok=True)
        oracle.save_to_disk(str(model_dest))
        logger.info(f"💾 Modelo guardado exitosamente en: {model_dest.name}")

if __name__ == "__main__":
    main()
