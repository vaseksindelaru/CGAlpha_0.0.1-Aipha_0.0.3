import json
from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3
from cgalpha_v3.domain.base_component import ComponentManifest

def test_retraining():
    dataset_path = "aipha_memory/operational/training_dataset_v2.jsonl"
    samples = []
    with open(dataset_path, "r") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line))
                
    manifest = ComponentManifest(name="Oracle_v5_Test", category="filtering", function="test", inputs=[], outputs=[], heritage_source="", heritage_contribution="")
    oracle = OracleTrainer_v3(manifest)
    
    # Cargar samples
    oracle.load_training_dataset(samples)
    
    # Entrenar
    oracle.train_model()
    
    # Validar
    metrics = oracle._training_metrics
    
    print("\n✅ RETRAINING SUCCESSFUL!")
    print(f"Total Samples Original: {len(samples)}")
    print(f"Valid Samples (Filtered BOUNCE_WEAK/INCONCLUSIVE): {metrics['n_samples']}")
    print(f"Train Accuracy: {metrics['train_accuracy'] * 100:.2f}%")
    print(f"Test Accuracy: {metrics['test_accuracy'] * 100:.2f}%")
    print(f"CV Mean Accuracy: {metrics['cv_mean'] * 100:.2f}%")
    print(f"Brier Score: {metrics['brier_score']}")
    print(f"Class Distribution: {oracle.get_training_metrics().get('class_balance', 'N/A')}")
    print("\nFeature Importances:")
    for f, imp in sorted(metrics["feature_importances"].items(), key=lambda x: x[1], reverse=True):
        print(f" - {f}: {imp}")

    # Persist model
    from pathlib import Path
    model_path = Path("aipha_memory/data/models/oracle_v5.joblib")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    oracle.save_to_disk(str(model_path))
    print(f"\n✅ Model saved successfully to {model_path}")

if __name__ == "__main__":
    test_retraining()
