import json
import logging
from pathlib import Path
from cgalpha_v3.learning.codex_kernel import CodexKernel

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_decisions")

# Ajuste automático de rutas
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODEX_DIR = PROJECT_ROOT / "cgalpha_v3" / "memory" / "codex"

DECISIONS = [
    {
        "codex_id": "D-003",
        "type": "DECISION",
        "status": "ACTIVE",
        "statement": "Determinismo sobre LLM en modificaciones de código extenso.",
        "rationale": "Archivos >300 líneas (como triple_coincidence.py) sufren truncamiento y pérdida de indentación si son editados directamente por LLMs pequeños. Se exige el uso de scripts Python de búsqueda y reemplazo para cambios estructurales.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["file_modification", "structural_change", "bug_fixing"],
        "evidence_ids": ["BUG-5_resolution_commit"]
    },
    {
        "codex_id": "D-005",
        "type": "DECISION",
        "status": "ACTIVE",
        "statement": "Safety Envelope: Umbral mínimo de validación OOS.",
        "rationale": "Ninguna propuesta de evolución (CEP) será promovida a MAIN si su precisión Out-of-Sample cae por debajo del 52% o su Brier Score empeora respecto al baseline. Previene el overfitting agresivo.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["evolution_proposal", "model_promotion", "backtest_validation"],
        "evidence_ids": ["V3_overfit_incident_report"]
    },
    {
        "codex_id": "D-009",
        "type": "DECISION",
        "status": "PARTIAL",
        "statement": "Rolling Window para Cumulative Delta.",
        "rationale": "El Delta acumulado globalmente sufre de drift de escala a lo largo del día, saturando los inputs del modelo. Se debe transicionar a una ventana deslizante de 30-300 segundos para normalizar la presión de compra/venta.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["feature_proposal", "data_normalization"],
        "evidence_ids": ["D-009_implementation_draft"]
    },
    {
        "codex_id": "D-010",
        "type": "DECISION",
        "status": "ACTIVE",
        "statement": "Timestamping Canónico (Exchange-driven).",
        "rationale": "Prohibido el uso de time.time() local para el alineamiento de Order Book y Ticks. Se exige el uso del campo 'T' (Event Time) de Binance para garantizar causalidad y sincronización multisímbolo.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["feature_proposal", "data_ingestion", "latency_audit"],
        "evidence_ids": ["B-001_clock_drift_fix"]
    }
]

def load_current_state():
    """Carga los IDs canónicos del disco para satisfacer al Kernel."""
    state = {}
    for sub in ["decisions", "bugs", "lessons"]:
        sub_dir = CODEX_DIR / sub
        if not sub_dir.exists(): continue
        for p in sub_dir.glob("*.json"):
            try:
                with open(p, 'r') as f:
                    entry = json.load(f)
                    if "codex_id" in entry:
                        state[entry["codex_id"]] = entry
            except:
                continue
    return state

def seed():
    # El Kernel EXIGE ver que los IDs canónicos están accesibles
    current_state = load_current_state()
    
    success_count = 0
    for entry in DECISIONS:
        # Validación vía Kernel Legal Layer
        if CodexKernel.validate_proposal(entry, current_state):
            # Guardar en el directorio correspondiente
            sub = "decisions"
            dst = CODEX_DIR / sub / f"{entry['codex_id']}.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dst, 'w') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Sembrada y validada: {entry['codex_id']}")
            success_count += 1
        else:
            logger.error(f"❌ Falló validación del Kernel para: {entry['codex_id']}")

    print(f"\n--- SESSION 1 COMPLETE: {success_count}/{len(DECISIONS)} Decisiones sembradas ---")

if __name__ == "__main__":
    seed()
