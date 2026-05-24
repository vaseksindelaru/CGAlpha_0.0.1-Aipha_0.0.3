import json
import logging
from pathlib import Path
from cgalpha_v3.learning.codex_kernel import CodexKernel

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_bugs")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODEX_DIR = PROJECT_ROOT / "cgalpha_v3" / "memory" / "codex"

BUGS = [
    {
        "codex_id": "B-001",
        "type": "BUG",
        "status": "RESOLVED",
        "statement": "Clock Drift: Desincronización entre Tick y Order Book.",
        "rationale": "El uso de time.time() local causaba un desfase de hasta 1200ms respecto a los datos de Binance, resultando en features del pasado emparejadas con precios del futuro (lookahead accidental). Se resolvió forzando el uso exclusivo de 'T' (Event Time).",
        "schema_version": "4.0.0",
        "harness_inject_when": ["data_ingestion", "latency_audit", "feature_proposal"],
        "evidence_ids": ["B-001_fix_commit"]
    },
    {
        "codex_id": "B-003",
        "type": "BUG",
        "status": "PARTIAL",
        "statement": "Desbalance de Clases Extremo (94/6).",
        "rationale": "El entrenamiento inicial ignoraba la rareza estadística de los rebotes reales. El modelo aprendió que 'siempre es breakout'. Se mitigó con pesos de clase balanceados y oversampling de BOUNCE_STRONG, pero la causa raíz (distribución de mercado) sigue siendo un reto operativo.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["model_training", "dataset_audit", "optimizer"],
        "evidence_ids": ["B-003_distribution_report"]
    },
    {
        "codex_id": "B-006",
        "type": "BUG",
        "status": "RESOLVED",
        "statement": "Zero-Crossing Contamination en Cumulative Delta.",
        "rationale": "El cálculo del delta de volumen no reiniciaba tras periodos de inactividad, acumulando sesgos de tendencias muertas. Se resolvió implementando el 'Rolling Window' (D-009) y reinicio de buffers en cada nueva detección de zona.",
        "schema_version": "4.0.0",
        "harness_inject_when": ["feature_proposal", "data_normalization"],
        "evidence_ids": ["B-006_fix_commit"]
    }
]

def load_current_state():
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
            except: continue
    return state

def seed():
    current_state = load_current_state()
    success_count = 0
    for entry in BUGS:
        if CodexKernel.validate_proposal(entry, current_state):
            sub = "bugs"
            dst = CODEX_DIR / sub / f"{entry['codex_id']}.json"
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(dst, 'w') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Sembrado y validado: {entry['codex_id']}")
            success_count += 1
        else:
            logger.error(f"❌ Falló validación del Kernel para: {entry['codex_id']}")

    print(f"\n--- BUGS SEEDING COMPLETE: {success_count}/{len(BUGS)} Bugs sembrados ---")

if __name__ == "__main__":
    seed()
