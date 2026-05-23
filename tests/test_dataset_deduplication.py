import pytest
import json
from cgalpha_v3.domain.deferred_outcome_monitor import DeferredOutcomeMonitor
import cgalpha_v3.domain.deferred_outcome_monitor as dom


def test_deduplication_integrity(tmp_path):
    # Setup: aislar el test usando rutas temporales
    test_jsonl = tmp_path / "test_dataset.jsonl"
    test_pending = tmp_path / "test_pending.json"

    # Parchear las rutas en el módulo
    orig_jsonl = dom.COMPLETED_SAMPLES_PATH
    orig_pending = dom.PENDING_LABELS_PATH

    dom.COMPLETED_SAMPLES_PATH = str(test_jsonl)
    dom.PENDING_LABELS_PATH = str(test_pending)

    try:
        monitor = DeferredOutcomeMonitor()

        # Crear un snapshot fake
        dummy_id = "test_unique_id_123"
        snapshot = {
            "_meta": {"sample_id": dummy_id},
            "zone_geometry": {"direction": "bullish", "zone_top": 100, "zone_bottom": 90},
            "clearance": {"atr_at_detection": 1.0},
            "l2_snapshot_at_touch": {"retest_price": 95}
        }

        # 1. Registrar por primera vez
        monitor.register_retest(snapshot)
        assert len(monitor.pending) == 1

        # 2. Intentar registrar duplicado (debe ser ignorado por estar ya en pending)
        monitor.register_retest(snapshot)
        assert len(monitor.pending) == 1

        # 3. Simular que el ID ya existe en dataset persistido
        with open(test_jsonl, "w") as f:
            f.write(json.dumps({"_meta": {"sample_id": dummy_id}, "outcome": {"label": "BREAKOUT"}}) + "\n")
        monitor._sync_seen_ids()
        monitor.pending = []

        # 4. Intentar registrar otra vez (debe bloquearse por _seen_ids)
        monitor.register_retest(snapshot)
        assert len(monitor.pending) == 0
        assert dummy_id in monitor._seen_ids

    finally:
        # Restaurar rutas originales
        dom.COMPLETED_SAMPLES_PATH = orig_jsonl
        dom.PENDING_LABELS_PATH = orig_pending
