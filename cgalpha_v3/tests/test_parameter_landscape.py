from __future__ import annotations

import json
from pathlib import Path

from cgalpha_v3.lila.parameter_landscape import build_parameter_landscape_map, load_parameter_landscape_map


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_min_project(root: Path) -> None:
    _write(
        root / "core_config.py",
        """
SYSTEM = {
    "volume_threshold": 1.2,
    "quality_threshold": 0.45,
    "min_confidence": 0.70,
    "max_drawdown_session_pct": 5.0,
    "max_position_size_pct": 2.0,
    "max_signals_per_hour": 10,
    "min_signal_quality_score": 0.65,
    "lookback_candles": 30,
    "atr_period": 14,
    "atr_multiplier": 1.5,
    "retest_timeout_bars": 40,
    "slippage_bps": 2.0,
    "fee_taker_pct": 0.04,
    "cooldown_seconds": 300,
    "retrain_interval_hours": 24,
    "max_tokens": 1000
}
""",
    )

    _write(
        root / "lila/llm/proposer.py",
        """
volume_threshold = 1.2
max_drawdown_session_pct = 5.0
min_confidence = 0.7
""",
    )
    _write(root / "application/change_proposer.py", "min_confidence = 0.7\n")
    _write(root / "application/pipeline.py", "volume_threshold = 1.2\n")
    _write(
        root / "data/phase1_results/auto_proposer_output.json",
        json.dumps({"volume_threshold": 1.2, "max_drawdown_session_pct": 5.0}),
    )


def test_build_parameter_landscape_map_detects_minimum_parameters(tmp_path: Path):
    project_root = tmp_path / "cgalpha_v3"
    _build_min_project(project_root)
    artifact_path = tmp_path / "parameter_landscape_map.json"

    artifact = build_parameter_landscape_map(
        project_root=project_root,
        artifact_path=artifact_path,
        switcher=None,
        use_llm=False,
    )

    assert artifact_path.exists()
    assert artifact["parameter_count"] >= 15
    assert artifact["qualitative_source"] == "heuristic_fallback"

    first = artifact["parameters"][0]
    assert "name" in first
    assert "file" in first
    assert "line" in first
    assert "current_value" in first
    assert "type" in first
    assert "sensitivity" in first
    assert "causal_impact_est" in first
    assert "auto_proposer_refs" in first

    assert any(p["auto_proposer_refs"] > 0 for p in artifact["parameters"])


def test_load_parameter_landscape_map_invalid_json(tmp_path: Path):
    artifact_path = tmp_path / "broken.json"
    artifact_path.write_text("{not-valid-json", encoding="utf-8")

    assert load_parameter_landscape_map(artifact_path) is None
