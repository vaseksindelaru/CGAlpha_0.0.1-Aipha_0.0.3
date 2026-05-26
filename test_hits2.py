from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.application.live_adapter import LiveDataFeedAdapter
from cgalpha_v3.infrastructure.signal_detector.triple_coincidence import TripleCoincidenceDetector, ActiveZone

hit = {
    "zone": ActiveZone(candle_index=1, zone_top=80708.8, zone_bottom=80560.0,
                       vwap_at_detection=80600.0,
                       detection_timestamp=0, direction='bearish',
                       key_candle={}, accumulation_zone={}, mini_trend={},
                       atr_at_detection=300.0),
    "price": 80619.8,
    "clearance_atr": 0.0
}
import asyncio
class MockOracle:
    def predict(self, micro, signal_data):
        class Res:
            confidence = 0.5
            suggested_action = 'WAIT'
        return Res()

class MockManager:
    def get_current_obi(self, sym, levels): return 0.5
    def get_rolling_delta(self, sym, window_seconds): return 1.0

# Create detector
detector = TripleCoincidenceDetector()

adapter = LiveDataFeedAdapter(ComponentManifest(name="test", category="test", function="test", causal_score=1.0), MockManager(), detector)
adapter.inject_oracle(MockOracle())
adapter._on_retest_detected(hit, 80619.8, 123456)
import json
print("Success! pending labels:", len(adapter.deferred_monitor.pending))
with open('aipha_memory/operational/pending_labels.json', 'r') as f:
    print(f.read()[:500])
