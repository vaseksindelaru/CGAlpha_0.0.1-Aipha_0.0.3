from __future__ import annotations

from cgalpha_v3.domain.models.signal import ApproachType
from cgalpha_v3.trading.labelers import (
    classify_approach_type,
    label_approach_sample,
    label_approach_samples,
)


def test_schema_contains_approach_type():
    label = label_approach_sample(
        {
            "open_price": 100.0,
            "high_price": 101.0,
            "low_price": 99.5,
            "close_price": 100.1,
            "zone_low": 99.8,
            "zone_high": 100.3,
            "prev_close": 100.0,
            "future_closes": [100.2, 100.1],
        },
        sample_id="s-001",
    )
    body = label.as_dict()
    assert body["sample_id"] == "s-001"
    assert body["approach_type"] in {a.value for a in ApproachType}


def test_classifies_breakout_vs_fake_break_vs_overshoot():
    breakout = classify_approach_type(
        open_price=100.0,
        high_price=101.2,
        low_price=99.8,
        close_price=101.1,
        zone_low=99.9,
        zone_high=100.3,
        prev_close=100.0,
        future_closes=[],
    )
    assert breakout == ApproachType.BREAKOUT

    fake_break = classify_approach_type(
        open_price=100.0,
        high_price=101.2,
        low_price=99.8,
        close_price=101.1,
        zone_low=99.9,
        zone_high=100.3,
        prev_close=100.0,
        future_closes=[101.0, 100.2],
    )
    assert fake_break == ApproachType.FAKE_BREAK

    overshoot = classify_approach_type(
        open_price=100.0,
        high_price=101.2,
        low_price=99.8,
        close_price=101.1,
        zone_low=99.9,
        zone_high=100.3,
        prev_close=100.0,
        future_closes=[101.0, 101.3, 101.4],
    )
    assert overshoot == ApproachType.OVERSHOOT


def test_classifies_retest_rejection_touch():
    retest = classify_approach_type(
        open_price=100.5,
        high_price=100.8,
        low_price=99.9,
        close_price=100.0,
        zone_low=99.8,
        zone_high=100.2,
        prev_close=100.5,
    )
    assert retest == ApproachType.RETEST

    rejection = classify_approach_type(
        open_price=100.0,
        high_price=101.6,
        low_price=99.9,
        close_price=100.1,
        zone_low=99.8,
        zone_high=100.3,
        prev_close=100.0,
    )
    assert rejection == ApproachType.REJECTION

    touch = classify_approach_type(
        open_price=100.0,
        high_price=100.3,
        low_price=99.8,
        close_price=100.0,
        zone_low=99.8,
        zone_high=100.2,
        prev_close=100.0,
    )
    assert touch == ApproachType.TOUCH


def test_label_approach_samples_batch():
    samples = [
        {
            "open_price": 100.0,
            "high_price": 101.0,
            "low_price": 99.0,
            "close_price": 100.5,
            "zone_low": 99.5,
            "zone_high": 100.5,
        },
        {
            "open_price": 100.0,
            "high_price": 105.0,
            "low_price": 95.0,
            "close_price": 104.0,
            "zone_low": 99.5,
            "zone_high": 100.5,
            "sample_id": "custom-id-99",
        },
    ]
    labels = label_approach_samples(samples)
    assert len(labels) == 2
    assert labels[0].sample_id == "sample-00001"
    assert labels[1].sample_id == "custom-id-99"
    assert labels[1].approach_type == ApproachType.BREAKOUT
