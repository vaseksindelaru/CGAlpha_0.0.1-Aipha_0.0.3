import json
from pathlib import Path

from click.testing import CliRunner

from cgalpha.ghost_architect.simple_causal_analyzer import SimpleCausalAnalyzer
from aiphalab.cli_v2 import cli


def _write_jsonl(path: Path, rows: list[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_simple_causal_analyzer_detects_actionable_patterns(tmp_path):
    log_path = tmp_path / "aipha_memory" / "cognitive_logs.jsonl"
    _write_jsonl(log_path, [
        {
            "timestamp": "2026-02-14T00:00:00Z",
            "agent": "Trader",
            "action": "enter_trade",
            "outcome": "failure",
            "context": {"drawdown": 0.22, "win_rate": 0.35},
        },
        {
            "timestamp": "2026-02-14T00:05:00Z",
            "agent": "Trader",
            "action": "enter_trade",
            "outcome": "failure",
            "context": {"drawdown": 0.18, "win_rate": 0.40},
        },
        {
            "timestamp": "2026-02-14T00:10:00Z",
            "agent": "Trader",
            "action": "enter_trade",
            "outcome": "failure",
            "context": {"drawdown": 0.16, "win_rate": 0.42},
        },
    ])

    analyzer = SimpleCausalAnalyzer(working_dir=str(tmp_path))
    analysis = analyzer.analyze_performance()

    assert analysis["records_analyzed"] == 3
    assert analysis["analysis_engine"] in {"llm", "heuristic_fallback"}
    assert "causal_metrics" in analysis
    assert "readiness_gates" in analysis
    assert analysis["readiness_gates"]["has_minimum_data"] is True
    pattern_types = {p["type"] for p in analysis["patterns"]}
    assert "high_drawdown" in pattern_types
    assert "low_win_rate" in pattern_types

    insights = analyzer.get_actionable_insights(
        analysis["patterns"],
        analysis["causal_hypotheses"],
    )
    assert len(insights) >= 1
    assert all(i["command"].startswith("cgalpha codecraft apply") for i in insights)


def test_cgalpha_auto_analyze_cli_end_to_end(tmp_path):
    _write_jsonl(
        tmp_path / "aipha_memory" / "cognitive_logs.jsonl",
        [
            {
                "timestamp": "2026-02-14T00:00:00Z",
                "agent": "RiskManager",
                "action": "rebalance",
                "outcome": "failure",
                "context": {"drawdown": 0.19, "win_rate": 0.41},
            }
        ],
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "auto-analyze",
            "--working-dir", str(tmp_path),
            "--min-confidence", "0.0",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "CGAlpha Performance Analysis" in result.output
    assert "Detected Issues" in result.output
    assert "Generated Proposals" in result.output
    assert "Report saved:" in result.output

    reports_dir = tmp_path / "aipha_memory" / "evolutionary" / "causal_reports"
    assert reports_dir.exists()
    assert any(p.suffix == ".json" for p in reports_dir.iterdir())


def test_analyze_performance_uses_llm_when_available(tmp_path):
    class _FakeLLM:
        def generate(self, prompt, temperature=0.2, max_tokens=1200):
            assert "Order Book / Microstructure" in prompt
            return json.dumps(
                {
                    "hypotheses": [
                        {
                            "cause": "Fakeout en order book durante news de alto impacto.",
                            "effect": "Stop prematuro antes de extension favorable.",
                            "confidence": 0.91,
                            "causal_signal": "fakeout",
                            "evidence_count": 4,
                            "recommended_action": "Reducir posicion y confirmar profundidad antes de mantener el corto.",
                            "command": 'cgalpha codecraft apply --text "Reducir size inicial y exigir confirmacion de order_book_depth"',
                        }
                    ]
                }
            )

    _write_jsonl(
        tmp_path / "aipha_memory" / "cognitive_logs.jsonl",
        [
            {
                "timestamp": "2026-02-14T00:00:00Z",
                "agent": "RiskManager",
                "action": "enter_short",
                "outcome": "failure",
                "context": {
                    "drawdown": 0.20,
                    "win_rate": 0.36,
                    "mfe": 0.7,
                    "mae": 1.3,
                    "fakeout": True,
                    "news_impact": "high",
                    "order_book_imbalance": -0.42,
                },
            },
            {
                "timestamp": "2026-02-14T00:10:00Z",
                "agent": "RiskManager",
                "action": "enter_short",
                "outcome": "failure",
                "context": {
                    "drawdown": 0.19,
                    "win_rate": 0.40,
                    "mfe": 0.8,
                    "mae": 1.4,
                    "fakeout": True,
                    "news_impact": "high",
                    "order_book_imbalance": -0.37,
                },
            },
            {
                "timestamp": "2026-02-14T00:20:00Z",
                "agent": "RiskManager",
                "action": "enter_short",
                "outcome": "success",
                "context": {
                    "drawdown": 0.08,
                    "win_rate": 0.55,
                    "mfe": 1.5,
                    "mae": 0.7,
                    "fakeout": False,
                    "news_impact": "low",
                    "order_book_imbalance": 0.12,
                },
            },
        ],
    )

    analyzer = SimpleCausalAnalyzer(working_dir=str(tmp_path), llm_assistant=_FakeLLM())
    analysis = analyzer.analyze_performance()
    assert analysis["analysis_engine"] == "llm"
    assert len(analysis["causal_hypotheses"]) >= 1
    assert 0.0 <= analysis["causal_metrics"]["accuracy_causal"] <= 1.0
    assert 0.0 <= analysis["causal_metrics"]["efficiency"] <= 1.0


def test_order_book_feature_enrichment_and_alignment(tmp_path):
    _write_jsonl(
        tmp_path / "aipha_memory" / "evolutionary" / "bridge.jsonl",
        [
            {
                "timestamp": "2026-02-14T00:00:00Z",
                "trade_id": "T1",
                "agent": "Trader",
                "action": "enter_short",
                "outcome": "failure",
                "context": {"drawdown": 0.18, "win_rate": 0.42, "mfe": 0.6, "mae": 1.4},
            },
            {
                "timestamp": "2026-02-14T00:00:02Z",
                "trade_id": "T2",
                "agent": "Trader",
                "action": "enter_short",
                "outcome": "failure",
                "context": {"drawdown": 0.17, "win_rate": 0.40, "mfe": 0.7, "mae": 1.3},
            },
            {
                "timestamp": "2026-02-14T00:00:04Z",
                "trade_id": "T3",
                "agent": "Trader",
                "action": "enter_short",
                "outcome": "failure",
                "context": {"drawdown": 0.16, "win_rate": 0.39, "mfe": 0.5, "mae": 1.2},
            },
        ],
    )
    _write_jsonl(
        tmp_path / "aipha_memory" / "operational" / "order_book_features.jsonl",
        [
            {
                "timestamp": "2026-02-14T00:00:00Z",
                "trade_id": "T1",
                "bid_size_1_5": 210.0,
                "ask_depth_1_5": 340.0,
                "spread_bps": 5.2,
                "cancel_ratio": 1.45,
                "replenishment_rate": 1.22,
                "sweep_events": 2,
                "micro_reversal_ticks": 2,
            },
            {
                "timestamp": "2026-02-14T00:00:02Z",
                "trade_id": "T2",
                "bid_size_1_5": 180.0,
                "ask_depth_1_5": 300.0,
                "spread_bps": 4.8,
                "cancel_ratio": 1.31,
                "replenishment_rate": 1.18,
                "sweep_events": 1,
                "micro_reversal_ticks": 3,
            },
            {
                "timestamp": "2026-02-14T00:00:04Z",
                "trade_id": "T3",
                "bid_size_1_5": 170.0,
                "ask_depth_1_5": 280.0,
                "spread_bps": 4.5,
                "cancel_ratio": 1.27,
                "replenishment_rate": 1.15,
                "sweep_events": 1,
                "micro_reversal_ticks": 2,
            },
        ],
    )

    analyzer = SimpleCausalAnalyzer(working_dir=str(tmp_path), enable_llm=False)
    analysis = analyzer.analyze_performance()
    pattern_types = {p["type"] for p in analysis["patterns"]}

    assert analysis["data_alignment"]["order_book_features_loaded"] is True
    assert analysis["data_alignment"]["order_book_coverage"] == 1.0
    assert analysis["data_alignment"]["contains_blind_tests"] is False
    assert analysis["readiness_gates"]["data_quality_pass"] is True
    assert "fakeout_cluster" in pattern_types


def test_order_book_nearest_window_and_blind_test_marker(tmp_path):
    _write_jsonl(
        tmp_path / "aipha_memory" / "evolutionary" / "bridge.jsonl",
        [
            {
                "timestamp": "2026-02-14T00:00:00Z",
                "trade_id": "A1",
                "agent": "Trader",
                "action": "enter_long",
                "outcome": "failure",
                "context": {"drawdown": 0.16, "win_rate": 0.41},
            },
            {
                "timestamp": "2026-02-14T00:00:02Z",
                "trade_id": "A2",
                "agent": "Trader",
                "action": "enter_long",
                "outcome": "failure",
                "context": {"drawdown": 0.17, "win_rate": 0.39},
            },
            {
                "timestamp": "2026-02-14T00:00:04Z",
                "trade_id": "A3",
                "agent": "Trader",
                "action": "enter_long",
                "outcome": "failure",
                "context": {"drawdown": 0.18, "win_rate": 0.38},
            },
        ],
    )
    # Solo A1 hace match exacto. A2/A3 quedan fuera de la ventana ±250ms y deben marcarse BLIND_TEST.
    _write_jsonl(
        tmp_path / "aipha_memory" / "operational" / "order_book_features.jsonl",
        [
            {
                "timestamp": "2026-02-14T00:00:00Z",
                "trade_id": "A1",
                "spread_bps": 4.1,
                "cancel_ratio": 1.2,
                "replenishment_rate": 1.1,
            },
            {
                "timestamp": "2026-02-14T00:00:05.100Z",
                "trade_id": "UNRELATED",
                "spread_bps": 4.5,
                "cancel_ratio": 1.3,
                "replenishment_rate": 1.15,
            },
        ],
    )

    analyzer = SimpleCausalAnalyzer(working_dir=str(tmp_path), enable_llm=False)
    analysis = analyzer.analyze_performance()

    assert analysis["data_alignment"]["order_book_features_loaded"] is True
    assert analysis["data_alignment"]["contains_blind_tests"] is True
    assert analysis["data_alignment"]["blind_test_count"] >= 1
    assert analysis["data_alignment"]["max_feature_join_lag_ms"] == 250
    assert analysis["readiness_gates"]["data_quality_pass"] is False
    assert analysis["readiness_gates"]["proceed_v03"] is False
