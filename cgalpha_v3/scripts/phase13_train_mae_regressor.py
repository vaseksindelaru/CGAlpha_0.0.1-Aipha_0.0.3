"""
Fase 13: Entrenamiento del Oráculo Regresor MAE (Capa 2)
========================================================
Entrena un RandomForestRegressor sobre el dataset de alta fidelidad v2 
para predecir la Penetración Máxima Adversa (MAE_ATR) y usarla en
órdenes Limit optimizadas.
"""

import sys
import json
import logging
from pathlib import Path

# Ensure project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.lila.llm.oracle import OracleRegressor_MAE

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("phase13_mae_regressor")

def main():
    print("=" * 60)
    print("  Fase 13: Oracle Regressor MAE Training (Capa 2)")
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

    # 2. Inicializar y Entrenar Oracle Regressor MAE
    regressor = OracleRegressor_MAE.create_default()
    regressor.load_training_dataset(samples)
    
    success = regressor.train_model()
    
    if not success:
        logger.error("❌ El entrenamiento del Regresor MAE falló. Posible escasez de muestras válidas (BOUNCE_STRONG).")
        return

    # 3. Mostrar métricas y guardar
    metrics = regressor.get_training_metrics()
    if metrics:
        print("\n📊 Métricas OOS Reales (Fase 13 - MAE Regressor):")
        print(f"   Test MAE (ATR) : {metrics['test_mae_atr']:.4f} ATR")
        print(f"   Test R2 Score  : {metrics['test_r2']:.4f}")
        print(f"   Top Features   : {sorted(metrics['feature_importances'].items(), key=lambda x: x[1], reverse=True)[:3]}")

        model_dest = PROJECT_ROOT / "aipha_memory/data/models/oracle_mae_v1.joblib"
        model_dest.parent.mkdir(parents=True, exist_ok=True)
        regressor.save_to_disk(str(model_dest))
        logger.info(f"💾 Modelo Regresor MAE guardado exitosamente en: {model_dest.name}")

if __name__ == "__main__":
    main()
