import sys
from cgalpha_v3.domain.deferred_outcome_monitor import DeferredOutcomeMonitor, PendingLabel
import time

m = DeferredOutcomeMonitor()
m.register_retest(
    snapshot={"_meta": {"sample_id": "test"}},
    raw_buffer=[],
    touch_sequence=1,
    polarity_flipped=False,
    prior_touch_outcomes=[1, 2, 3],
    zone_original_direction='bullish',
    flip_ts=None
)
import json
with open('aipha_memory/operational/pending_labels.json', 'r') as f:
    print(f.read()[:500])
