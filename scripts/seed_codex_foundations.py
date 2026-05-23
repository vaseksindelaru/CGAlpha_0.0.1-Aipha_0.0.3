import json
from datetime import datetime, timezone
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine, MemoryLevel
from cgalpha_v3.domain.models.signal import MemoryEntry

def seed_foundations():
    engine = MemoryPolicyEngine()
    
    # 1. L-003: La lección de los Thresholds Artificiales
    l003_content = {
        "codex_id": "L-003",
        "type": "LESSON",
        "status": "APPROVED",
        "title": "Thresholds Artificiales vs Percentiles Reales",
        "statement": "Los thresholds arbitrarios (ej. 0.1%) pueden producir distribuciones de datos balanceadas artificialmente (55/45). Se debe calibrar usando percentiles reales (P75=0.18%) para mantener la integridad del mercado.",
        "rationale": "La observación de 288 velas BTCUSDT mostró que la mediana de volatilidad es mayor a 0.1%, haciendo que el threshold original fuera demasiado ruidoso.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["optimizer", "backtest_config"]
    }
    
    # 2. B-002: El Bug de Persistencia del Oracle
    b002_content = {
        "codex_id": "B-002",
        "type": "BUG",
        "status": "RESOLVED",
        "title": "Pérdida de Entrenamiento por Falta de Serialización",
        "statement": "El Oracle v3 perdía su progreso tras reinicios porque save_to_disk() no se llamaba en el ciclo principal del servidor.",
        "rationale": "Error de integración entre la capa de aplicación (server.py) y el dominio (oracle.py). Requiere llamada explícita en startup y shutdown.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["server_setup", "model_training"],
        "affects_files": ["cgalpha_v3/gui/server.py", "cgalpha_v3/lila/llm/oracle.py"]
    }
    
    # 3. D-008: Proximity Buffer para acelerar cosecha
    d008_content = {
        "codex_id": "D-008",
        "type": "DECISION",
        "status": "APPROVED",
        "title": "Ampliación de Perímetro de Retest (Proximity Buffer)",
        "statement": "Añadir un buffer de 0.1% (retest_proximity_pct) para capturar toques cercanos fuera de los límites estrictos de la zona.",
        "rationale": "La dispersión institucional hace que muchos retests ocurran a pocos dólares de la zona exacta. Sin buffer, el tiempo de cosecha se duplicaba innecesariamente.",
        "schema_version": "1.0.0",
        "harness_inject_when": ["signal_detector", "live_pipeline"],
        "affects_files": ["cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py"]
    }

    foundations = [l003_content, b002_content, d008_content]
    
    for content in foundations:
        entry = MemoryEntry.new(
            content=json.dumps(content),
            level=MemoryLevel.STRATEGY,
            field="architect",
            source_id="foundation_seed_v1",
            source_type="primary",
            tags=["codex", "foundation", content["type"].lower()],
            expires_at=None # Nivel STRATEGY no expira
        )
        # Sobreescribimos el entry_id con el codex_id para consistencia canónica
        # Nota: entry es un objeto inmutable en v3 (dataclass frozen=False por defecto aquí)
        entry.entry_id = content["codex_id"]
        entry.approved_by = "human"
        
        # Persistimos usando las herramientas del motor
        engine._persist_codex_entry(entry)
        print(f"✅ Codex Seeded: {content['codex_id']} - {content['title']}")

if __name__ == "__main__":
    seed_foundations()
