"""
Simple Causal Analyzer (Ghost Architect v0.2).

Adds LLM-driven causal inference while preserving heuristic fallback behavior.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

try:
    from core.llm_assistant_v2 import get_llm_assistant
except ImportError:  # pragma: no cover - optional dependency
    get_llm_assistant = None

try:
    from jinja2 import Environment, FileSystemLoader, TemplateNotFound
except ImportError:  # pragma: no cover - optional dependency
    Environment = None
    FileSystemLoader = None
    TemplateNotFound = Exception

logger = logging.getLogger(__name__)


@dataclass
class Insight:
    insight_type: str
    reason: str
    confidence: float
    command: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.insight_type,
            "reason": self.reason,
            "confidence": round(self.confidence, 2),
            "command": self.command,
        }


class SimpleCausalAnalyzer:
    """Ghost Architect causal analyzer with LLM + fallback heuristics."""

    SIGNAL_ALIASES = {
        "fakeout": {"fakeout", "orderbook_fakeout", "liquidity_trap"},
        "liquidity_fakeout": {"liquidity_fakeout", "book_fakeout", "micro_fakeout"},
        "structure_break": {"structure_break", "trend_structure_break"},
        "risk_logic_failure": {"risk_logic_failure", "risk_model_error"},
        "news_shock": {"news_shock", "news_impact", "macro_news"},
        "microstructure_imbalance": {"microstructure_imbalance", "order_book_imbalance", "obi"},
        "mfe_mae_asymmetry": {"mfe_mae_asymmetry", "mfe_mae"},
        "trend_break": {"trend_break", "regime_break", "structure_break"},
        "risk_regime": {"risk_regime", "risk_shift"},
        "regime_shift": {"regime_shift", "market_regime_shift"},
        "execution_stability": {"execution_stability", "execution_error"},
    }

    def __init__(self, working_dir: str = ".", llm_assistant=None, enable_llm: bool = True):
        self.working_dir = Path(working_dir).resolve()
        self.llm = llm_assistant
        self.enable_llm = enable_llm
        self.max_feature_join_lag_ms = int(os.environ.get("CGALPHA_FEATURE_JOIN_LAG_MS", "250"))
        self.max_blind_test_ratio = float(os.environ.get("CGALPHA_MAX_BLIND_TEST_RATIO", "0.25"))
        self.max_nearest_match_avg_lag_ms = float(os.environ.get("CGALPHA_MAX_NEAREST_LAG_MS", "150"))
        self.min_causal_accuracy = float(os.environ.get("CGALPHA_MIN_CAUSAL_ACCURACY", "0.55"))
        self.min_efficiency = float(os.environ.get("CGALPHA_MIN_CAUSAL_EFFICIENCY", "0.40"))
        self.order_book_features_path = self.working_dir / "aipha_memory" / "operational" / "order_book_features.jsonl"
        self.prompt_template_dir = Path(__file__).resolve().parent / "templates"
        self.prompt_template_name = "deep_causal_prompt.j2"
        self._last_hypotheses: List[Dict[str, Any]] = []
        self._llm_init_error: Optional[str] = None
        self._prompt_env = None
        if Environment is not None and FileSystemLoader is not None:
            self._prompt_env = Environment(loader=FileSystemLoader(str(self.prompt_template_dir)))
        self.metrics = {
            "llm_attempts": 0,
            "llm_successes": 0,
            "llm_failures": 0,
        }

    def analyze_performance(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        model_version = os.environ.get("CGALPHA_CAUSAL_MODEL", "DeepSeek-V3")

        bridge_truth = self.working_dir / "aipha_memory" / "evolutionary" / "bridge.jsonl"
        if log_file:
            log_path = self._resolve_log_path(log_file)
        elif bridge_truth.exists() and bridge_truth.is_file():
            log_path = bridge_truth.resolve()
        else:
            log_path = self._resolve_log_path(None)

        records = self._read_jsonl(log_path)
        order_book_index = self._load_order_book_feature_index()
        if not records:
            empty_data_alignment = {
                "order_book_features_path": str(self.order_book_features_path),
                "order_book_features_loaded": bool(order_book_index.get("rows")),
                "order_book_features_rows": order_book_index.get("rows", 0),
                "order_book_coverage": 0.0,
                "blind_test_count": 0,
                "blind_test_ratio": 0.0,
                "contains_blind_tests": False,
                "nearest_match_avg_lag_ms": None,
                "max_feature_join_lag_ms": self.max_feature_join_lag_ms,
            }
            empty_causal_metrics = self._empty_causal_metrics()
            return {
                "source": str(log_path) if log_path else None,
                "records_analyzed": 0,
                "patterns": [],
                "causal_hypotheses": [],
                "causal_metrics": empty_causal_metrics,
                "analysis_engine": "heuristic_fallback",
                "llm_status": self._llm_status(),
                "model_version": model_version,
                "data_alignment": empty_data_alignment,
                "readiness_gates": self._build_readiness_gates(
                    data_alignment=empty_data_alignment,
                    causal_metrics=empty_causal_metrics,
                    records_analyzed=0,
                ),
                "causal_inference": {
                    "hypothesis": "Sin datos historicos para inferencia causal.",
                    "recommended_action": "Safe Mode: mantener parametros actuales y recolectar mas contexto.",
                    "confidence": 0.0,
                    "model_version": model_version,
                    "reasoning": "No hay registros disponibles en bridge/cognitive logs.",
                },
            }

        snapshots = [self._extract_trade_snapshot(r, order_book_index=order_book_index) for r in records]
        patterns = self._detect_patterns(records, snapshots)
        data_alignment = self._build_data_alignment_summary(snapshots, order_book_index)

        llm_hypotheses = self._infer_with_llm(snapshots, patterns)
        engine = "llm" if llm_hypotheses else "heuristic_fallback"
        hypotheses = llm_hypotheses or self._build_hypotheses(patterns)
        causal_metrics = self._compute_causal_metrics(snapshots, hypotheses)
        readiness_gates = self._build_readiness_gates(
            data_alignment=data_alignment,
            causal_metrics=causal_metrics,
            records_analyzed=len(records),
        )
        self._last_hypotheses = hypotheses

        top = hypotheses[0] if hypotheses else {}
        hypothesis_text = top.get("cause") or "No causal hypothesis generated."
        recommended_action = top.get("recommended_action") or "Safe Mode: usar ajustes conservadores."
        confidence = self._clamp(float(top.get("confidence_score", 0.6)), 0.0, 1.0) if top else 0.0
        reasoning = top.get("effect") or "Sin evidencia suficiente para razonamiento adicional."

        return {
            "source": str(log_path) if log_path else None,
            "records_analyzed": len(records),
            "patterns": patterns,
            "causal_hypotheses": hypotheses,
            "causal_metrics": causal_metrics,
            "analysis_engine": engine,
            "llm_status": self._llm_status(),
            "model_version": model_version,
            "data_alignment": data_alignment,
            "readiness_gates": readiness_gates,
            "causal_inference": {
                "hypothesis": hypothesis_text,
                "recommended_action": recommended_action,
                "confidence": round(confidence, 3),
                "model_version": model_version,
                "reasoning": reasoning,
            },
        }

    def analyze_logs(self, log_file: Optional[str] = None) -> Dict[str, Any]:
        """Backward-compatible alias used by the current CLI/orchestrator."""
        return self.analyze_performance(log_file=log_file)

    def get_actionable_insights(
        self,
        patterns: List[Dict[str, Any]],
        hypotheses: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        insights: List[Insight] = []
        causal_hypotheses = hypotheses if hypotheses is not None else self._last_hypotheses

        for item in causal_hypotheses:
            command = self._safe_command(item.get("command"), item.get("recommended_action", ""))
            reason = item.get("cause") or item.get("effect") or "Causal hypothesis generated."
            confidence = self._clamp(float(item.get("confidence_score", 0.75)), 0.0, 1.0)
            insight_type = item.get("causal_signal", "causal_adjustment")
            insights.append(
                Insight(
                    insight_type=insight_type,
                    reason=reason,
                    confidence=confidence,
                    command=command,
                )
            )

        if insights:
            return [i.to_dict() for i in insights]

        for pattern in patterns:
            ptype = pattern.get("type")
            value = pattern.get("value")

            if ptype == "high_drawdown":
                insights.append(
                    Insight(
                        insight_type="risk_reduction",
                        reason=f"Drawdown {value:.1%} supera umbral seguro de 15%.",
                        confidence=0.86,
                        command='cgalpha codecraft apply --text "Reducir exposure_multiplier de 1.0 a 0.8"',
                    )
                )
            elif ptype == "low_win_rate":
                insights.append(
                    Insight(
                        insight_type="signal_quality",
                        reason=f"Win Rate reciente {value:.1%} por debajo del objetivo 50%.",
                        confidence=0.82,
                        command='cgalpha codecraft apply --text "Aumentar confidence_threshold de 0.70 a 0.75"',
                    )
                )
            elif ptype == "high_failure_rate":
                insights.append(
                    Insight(
                        insight_type="stability",
                        reason=f"Tasa de fallos {value:.1%}; hay inestabilidad operativa recurrente.",
                        confidence=0.76,
                        command='cgalpha codecraft apply --text "Reducir agresividad de entrada y añadir validacion defensiva"',
                    )
                )
            elif ptype == "repeated_action_failure":
                action_name = pattern.get("action", "unknown_action")
                insights.append(
                    Insight(
                        insight_type="process_fix",
                        reason=f"Accion '{action_name}' falla de forma repetida.",
                        confidence=0.72,
                        command=f'cgalpha codecraft apply --text "Fortalecer manejo de errores en {action_name}"',
                    )
                )

        return [i.to_dict() for i in insights]

    def save_analysis_report(self, analysis_result: Dict[str, Any], insights: List[Dict[str, Any]]) -> Path:
        out_dir = self.working_dir / "aipha_memory" / "evolutionary" / "causal_reports"
        out_dir.mkdir(parents=True, exist_ok=True)

        ts = str(analysis_result.get("source", "report")).replace("/", "_").replace(".", "_")
        filename = f"ghost_architect_v0_2_{Path(ts).stem}.json"
        out_path = out_dir / filename

        payload = {
            "analysis": analysis_result,
            "insights": insights,
            "metrics": self.metrics,
        }
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return out_path

    def cleanup_processed_log(self, log_file: str) -> Optional[Path]:
        path = Path(log_file)
        if not path.is_absolute():
            path = (self.working_dir / path).resolve()
        if not path.exists():
            return None

        archived = path.with_suffix(path.suffix + ".processed")
        path.rename(archived)
        return archived

    def _resolve_log_path(self, log_file: Optional[str]) -> Optional[Path]:
        candidates: List[Path] = []
        if log_file:
            p = Path(log_file)
            candidates.append(p if p.is_absolute() else (self.working_dir / p))

        candidates.extend(
            [
                self.working_dir / "aipha_memory" / "cognitive_logs.jsonl",
                self.working_dir / "aipha_memory" / "operational" / "action_history.jsonl",
                self.working_dir / "aipha_memory" / "evolutionary" / "bridge.jsonl",
                self.working_dir / "aipha" / "evolutionary" / "bridge.jsonl",
            ]
        )

        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate.resolve()
        return None

    def _read_jsonl(self, path: Optional[Path]) -> List[Dict[str, Any]]:
        if path is None:
            return []

        rows: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def _load_order_book_feature_index(self) -> Dict[str, Any]:
        path = self.order_book_features_path
        if not path.exists() or not path.is_file():
            return {"path": str(path), "rows": 0, "by_trade_id": {}, "by_ts": [], "ts_keys": []}

        rows = self._read_jsonl(path)
        by_trade_id: Dict[str, Dict[str, Any]] = {}
        by_ts: List[tuple] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            tid = self._extract_trade_id(row)
            if tid:
                by_trade_id[str(tid)] = row

            ts = self._to_epoch(row.get("timestamp"))
            if ts is not None:
                by_ts.append((ts, row))

        by_ts.sort(key=lambda item: item[0])
        ts_keys = [item[0] for item in by_ts]
        return {
            "path": str(path),
            "rows": len(rows),
            "by_trade_id": by_trade_id,
            "by_ts": by_ts,
            "ts_keys": ts_keys,
        }

    def _match_order_book_feature(self, row: Dict[str, Any], index: Dict[str, Any]) -> Dict[str, Any]:
        by_trade_id = index.get("by_trade_id") if isinstance(index, dict) else None
        by_ts = index.get("by_ts") if isinstance(index, dict) else None
        ts_keys = index.get("ts_keys") if isinstance(index, dict) else None
        if not isinstance(by_trade_id, dict) or not isinstance(by_ts, list) or not isinstance(ts_keys, list):
            return {}

        trade_id = self._extract_trade_id(row)
        if trade_id and str(trade_id) in by_trade_id:
            match = dict(by_trade_id[str(trade_id)])
            match["_matched_by"] = "trade_id"
            match["_lag_ms"] = 0
            return match

        source_ts = self._to_epoch(row.get("timestamp"))
        if source_ts is None or not by_ts:
            return {}

        pos = bisect_left(ts_keys, source_ts)
        candidates = []
        if pos < len(by_ts):
            candidates.append(by_ts[pos])
        if pos > 0:
            candidates.append(by_ts[pos - 1])
        if not candidates:
            return {}

        nearest = min(candidates, key=lambda item: abs(item[0] - source_ts))
        lag_ms = int(abs(nearest[0] - source_ts) * 1000.0)
        # Temporal join conservador: default ±250ms.
        if lag_ms <= self.max_feature_join_lag_ms:
            match = dict(nearest[1])
            match["_matched_by"] = "timestamp_nearest"
            match["_lag_ms"] = lag_ms
            return match
        return {}

    def _extract_trade_id(self, row: Dict[str, Any]) -> Optional[str]:
        if not isinstance(row, dict):
            return None
        context = row.get("context") if isinstance(row.get("context"), dict) else {}
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        for key in ("trade_id", "position_id", "order_id", "exec_id"):
            value = row.get(key)
            if value is None:
                value = context.get(key)
            if value is None:
                value = details.get(key)
            if value is not None:
                return str(value)
        return None

    def _extract_outcome(self, row: Dict[str, Any]) -> str:
        direct = str(row.get("outcome") or row.get("status") or "").lower()
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        verdict = str(details.get("verdict", "")).lower()

        if any(token in direct for token in ("fail", "error", "loss", "stop")):
            return "failure"
        if any(token in verdict for token in ("fail", "loss", "stop")):
            return "failure"
        if any(token in direct for token in ("success", "ok", "win", "tp")):
            return "success"
        if any(token in verdict for token in ("success", "win", "tp")):
            return "success"
        return "unknown"

    def _extract_drawdown(self, row: Dict[str, Any]) -> Optional[float]:
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        context = row.get("context") if isinstance(row.get("context"), dict) else {}

        for key in ("drawdown", "max_drawdown", "dd", "dd_abs"):
            value = context.get(key, details.get(key, row.get(key)))
            if isinstance(value, (int, float)):
                return abs(float(value))

        dd_delta = details.get("dd_delta", row.get("dd_delta"))
        if isinstance(dd_delta, (int, float)):
            return abs(float(dd_delta))
        return None

    def _extract_win_rate(self, row: Dict[str, Any]) -> Optional[float]:
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        context = row.get("context") if isinstance(row.get("context"), dict) else {}

        for key in ("win_rate", "wr", "success_rate"):
            value = context.get(key, details.get(key, row.get(key)))
            if isinstance(value, (int, float)):
                num = float(value)
                if num > 1:
                    num = num / 100.0
                return self._clamp(num, 0.0, 1.0)
        return None

    def _extract_trade_snapshot(
        self,
        row: Dict[str, Any],
        order_book_index: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        context = row.get("context") if isinstance(row.get("context"), dict) else {}
        details = row.get("details") if isinstance(row.get("details"), dict) else {}
        index = order_book_index or {}
        matched_feature = self._match_order_book_feature(row, index)
        trade_id = self._extract_trade_id(row)

        def pick(*keys):
            for key in keys:
                if key in context:
                    return context.get(key)
                if key in details:
                    return details.get(key)
                if key in row:
                    return row.get(key)
                if key in matched_feature:
                    return matched_feature.get(key)
            return None

        imbalance = self._coerce_float(
            pick("order_book_imbalance", "book_imbalance", "obi", "micro_imbalance")
        )
        bid_size_1_5 = self._coerce_float(pick("bid_size_1_5", "bid_depth_1_5", "bids_depth_1_5"))
        ask_depth_1_5 = self._coerce_float(pick("ask_depth_1_5", "ask_size_1_5", "asks_depth_1_5"))
        spread_bps = self._coerce_float(pick("spread_bps", "spread_bp", "spread_basis_points"))
        cancel_ratio = self._coerce_float(pick("cancel_ratio", "cancel_to_fill_ratio"))
        replenishment_rate = self._coerce_float(pick("replenishment_rate", "liquidity_replenishment_rate"))
        sweep_events = self._coerce_int(pick("sweep_events", "liquidity_sweep_events"))
        micro_reversal_ticks = self._coerce_int(pick("micro_reversal_ticks", "reversal_ticks"))
        aggressive_delta = self._coerce_float(
            pick("aggressive_buy_sell_delta", "aggressive_delta", "taker_delta")
        )

        outcome = self._extract_outcome(row)
        fakeout_flag = self._coerce_bool(
            pick("fakeout", "is_fakeout", "orderbook_fakeout", "fake_breakout", "liquidity_trap")
        )
        inferred_fakeout = self._infer_fakeout_from_microstructure(
            spread_bps=spread_bps,
            cancel_ratio=cancel_ratio,
            replenishment_rate=replenishment_rate,
            sweep_events=sweep_events,
            micro_reversal_ticks=micro_reversal_ticks,
            imbalance=imbalance,
            aggressive_delta=aggressive_delta,
        )
        fakeout = fakeout_flag or inferred_fakeout

        microstructure = self._normalize_microstructure(
            pick("microstructure", "order_book_state", "order_book_regime"), imbalance
        )
        micro_regime = self._infer_micro_regime(
            spread_bps=spread_bps,
            cancel_ratio=cancel_ratio,
            replenishment_rate=replenishment_rate,
            sweep_events=sweep_events,
            micro_reversal_ticks=micro_reversal_ticks,
            imbalance=imbalance,
        )
        news_impact = self._normalize_news_impact(
            pick("news_impact", "news_severity", "macro_news", "news_regime")
        )
        has_external_rows = bool(index.get("rows", 0))
        matched = bool(matched_feature)
        if matched:
            if matched_feature.get("_matched_by") == "trade_id":
                micro_data_mode = "ENRICHED_EXACT"
            else:
                micro_data_mode = "ENRICHED_NEAREST"
        elif has_external_rows:
            micro_data_mode = "BLIND_TEST"
        else:
            micro_data_mode = "LOCAL_ONLY"

        return {
            "timestamp": row.get("timestamp"),
            "trade_id": trade_id,
            "agent": row.get("agent"),
            "action": row.get("action") or row.get("action_type"),
            "outcome": outcome,
            "drawdown": self._extract_drawdown(row),
            "win_rate": self._extract_win_rate(row),
            "mfe": self._coerce_float(pick("mfe", "max_favorable_excursion", "mfe_abs")),
            "mae": self._coerce_float(pick("mae", "max_adverse_excursion", "mae_abs")),
            "fakeout": fakeout,
            "news_impact": news_impact,
            "microstructure": microstructure,
            "order_book_imbalance": imbalance,
            "bid_size_1_5": bid_size_1_5,
            "ask_depth_1_5": ask_depth_1_5,
            "spread_bps": spread_bps,
            "cancel_ratio": cancel_ratio,
            "replenishment_rate": replenishment_rate,
            "sweep_events": sweep_events,
            "micro_reversal_ticks": micro_reversal_ticks,
            "aggressive_buy_sell_delta": aggressive_delta,
            "micro_regime": micro_regime,
            "order_book_feature_match": matched,
            "order_book_match_type": matched_feature.get("_matched_by"),
            "order_book_lag_ms": matched_feature.get("_lag_ms"),
            "micro_data_mode": micro_data_mode,
            "candle_regime": pick("candle_regime", "candles", "regime", "market_regime"),
        }

    def _detect_patterns(
        self,
        records: List[Dict[str, Any]],
        snapshots: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        patterns: List[Dict[str, Any]] = []
        outcomes = [s["outcome"] for s in snapshots]
        failures = [o for o in outcomes if o == "failure"]
        failure_rate = len(failures) / len(snapshots)

        drawdowns = [d for d in (s.get("drawdown") for s in snapshots) if isinstance(d, (int, float))]
        if drawdowns:
            max_drawdown = max(drawdowns)
            if max_drawdown > 0.15:
                patterns.append(
                    {
                        "type": "high_drawdown",
                        "severity": "critical" if max_drawdown > 0.20 else "high",
                        "value": round(max_drawdown, 3),
                        "threshold": 0.15,
                        "evidence_count": len(drawdowns),
                        "causal_signal": "risk_regime",
                    }
                )

        if failure_rate >= 0.35:
            patterns.append(
                {
                    "type": "high_failure_rate",
                    "severity": "high" if failure_rate >= 0.50 else "medium",
                    "value": round(failure_rate, 3),
                    "threshold": 0.35,
                    "evidence_count": len(failures),
                    "causal_signal": "execution_stability",
                }
            )

        win_signal = self._compute_win_rate_signal(snapshots)
        if win_signal is not None:
            patterns.append(win_signal)

        repeated_fail_action = self._repeated_failure_action(records)
        if repeated_fail_action is not None:
            patterns.append(repeated_fail_action)

        fakeout_pattern = self._detect_fakeout_pattern(snapshots)
        if fakeout_pattern is not None:
            patterns.append(fakeout_pattern)

        news_pattern = self._detect_news_pattern(snapshots)
        if news_pattern is not None:
            patterns.append(news_pattern)

        micro_pattern = self._detect_microstructure_pattern(snapshots)
        if micro_pattern is not None:
            patterns.append(micro_pattern)

        mfe_mae_pattern = self._detect_mfe_mae_pattern(snapshots)
        if mfe_mae_pattern is not None:
            patterns.append(mfe_mae_pattern)

        return patterns

    def _compute_win_rate_signal(self, snapshots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        historical_wr = [s["win_rate"] for s in snapshots if isinstance(s.get("win_rate"), (int, float))]
        observed_wr = mean(historical_wr) if historical_wr else None

        if observed_wr is None:
            known = [s for s in snapshots if s["outcome"] in ("success", "failure")]
            if known:
                observed_wr = len([s for s in known if s["outcome"] == "success"]) / len(known)

        if observed_wr is None:
            return None

        recent_window = min(30, len(snapshots))
        recent = snapshots[-recent_window:]
        recent_known = [s for s in recent if s["outcome"] in ("success", "failure")]
        recent_wr = (
            len([s for s in recent_known if s["outcome"] == "success"]) / len(recent_known)
            if recent_known
            else observed_wr
        )

        degradation = observed_wr - recent_wr
        if recent_wr < 0.50 or degradation > 0.08:
            return {
                "type": "low_win_rate",
                "severity": "high" if recent_wr < 0.40 else "medium",
                "value": round(recent_wr, 3),
                "threshold": 0.50,
                "evidence_count": len(recent_known),
                "meta": {
                    "historical_win_rate": round(observed_wr, 3),
                    "degradation": round(degradation, 3),
                    "window": recent_window,
                },
                "causal_signal": "regime_shift",
            }
        return None

    def _detect_fakeout_pattern(self, snapshots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        fakeout_records = [s for s in snapshots if s.get("fakeout") is True]
        if len(fakeout_records) < 3:
            return None

        fakeout_failures = len([s for s in fakeout_records if s["outcome"] == "failure"])
        fakeout_failure_rate = fakeout_failures / len(fakeout_records)
        if fakeout_failure_rate < 0.60:
            return None

        return {
            "type": "fakeout_cluster",
            "severity": "high",
            "value": round(fakeout_failure_rate, 3),
            "threshold": 0.60,
            "evidence_count": len(fakeout_records),
            "causal_signal": "fakeout",
        }

    def _detect_news_pattern(self, snapshots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        high_news = [s for s in snapshots if s.get("news_impact") == "high"]
        if len(high_news) < 3:
            return None

        failures = len([s for s in high_news if s["outcome"] == "failure"])
        failure_rate = failures / len(high_news)
        if failure_rate < 0.60:
            return None

        return {
            "type": "news_shock_loss",
            "severity": "high",
            "value": round(failure_rate, 3),
            "threshold": 0.60,
            "evidence_count": len(high_news),
            "causal_signal": "news_shock",
        }

    def _detect_microstructure_pattern(self, snapshots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        stressed = [
            s
            for s in snapshots
            if s.get("microstructure") in {"ask_pressure", "imbalance"}
            or (isinstance(s.get("order_book_imbalance"), float) and abs(s["order_book_imbalance"]) >= 0.35)
        ]
        if len(stressed) < 3:
            return None

        failures = len([s for s in stressed if s["outcome"] == "failure"])
        failure_rate = failures / len(stressed)
        if failure_rate < 0.60:
            return None

        return {
            "type": "microstructure_imbalance_loss",
            "severity": "high",
            "value": round(failure_rate, 3),
            "threshold": 0.60,
            "evidence_count": len(stressed),
            "causal_signal": "microstructure_imbalance",
        }

    def _detect_mfe_mae_pattern(self, snapshots: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        ratios: List[float] = []
        for s in snapshots:
            mfe = s.get("mfe")
            mae = s.get("mae")
            if not isinstance(mfe, (int, float)) or not isinstance(mae, (int, float)):
                continue
            if abs(mae) < 1e-9:
                continue
            ratios.append(abs(float(mfe)) / abs(float(mae)))

        if len(ratios) < 3:
            return None

        ratio_mean = mean(ratios)
        if ratio_mean >= 0.90:
            return None

        return {
            "type": "mfe_mae_asymmetry",
            "severity": "medium",
            "value": round(ratio_mean, 3),
            "threshold": 0.90,
            "evidence_count": len(ratios),
            "causal_signal": "mfe_mae_asymmetry",
        }

    def _repeated_failure_action(self, records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        fail_count: Dict[str, int] = {}
        for row in records:
            if self._extract_outcome(row) != "failure":
                continue
            action = row.get("action") or row.get("action_type") or "unknown"
            action = str(action)
            fail_count[action] = fail_count.get(action, 0) + 1

        if not fail_count:
            return None

        action, count = max(fail_count.items(), key=lambda item: item[1])
        if count < 3:
            return None

        return {
            "type": "repeated_action_failure",
            "severity": "medium",
            "action": action,
            "value": count,
            "threshold": 3,
            "evidence_count": count,
            "causal_signal": "execution_stability",
        }

    def _build_hypotheses(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        hypotheses: List[Dict[str, Any]] = []
        for p in patterns:
            ptype = p.get("type")
            if ptype == "high_drawdown":
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": "Regimen de riesgo agresivo en entorno adverso.",
                            "effect": "Drawdown excede el limite operativo.",
                            "confidence": 0.84,
                            "recommended_action": "Reducir posicion y ajustar stop loss defensivo.",
                            "command": 'cgalpha codecraft apply --text "Reducir exposure_multiplier de 1.0 a 0.8 y subir stop_loss_buffer"',
                            "causal_signal": "risk_regime",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
            elif ptype == "low_win_rate":
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": "Cambio de micro-regimen: setup anterior ya no filtra fakeouts.",
                            "effect": "Win rate reciente cae por debajo del 50%.",
                            "confidence": 0.82,
                            "recommended_action": "Subir confidence threshold y reducir TP para capturar salidas mas rapidas.",
                            "command": 'cgalpha codecraft apply --text "Aumentar confidence_threshold de 0.70 a 0.75 y reducir tp_factor de 2.0 a 1.8"',
                            "causal_signal": "regime_shift",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
            elif ptype == "fakeout_cluster":
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": "Fakeouts en order book generan barridas tempranas.",
                            "effect": "Entradas se invalidan antes de alcanzar TP.",
                            "confidence": 0.81,
                            "recommended_action": "Mantener posicion corta solo con confirmacion de profundidad y reducir tamano inicial.",
                            "command": 'cgalpha codecraft apply --text "Reducir size inicial y exigir confirmacion de order_book_depth antes de cerrar corto"',
                            "causal_signal": "fakeout",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
            elif ptype == "news_shock_loss":
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": "Eventos de news de alto impacto invalidan microestructura previa.",
                            "effect": "Secuencia de stops en ventanas de volatilidad.",
                            "confidence": 0.78,
                            "recommended_action": "Reducir posicion o pausar entradas durante news high impact.",
                            "command": 'cgalpha codecraft apply --text "Activar filtro de noticias de alto impacto y reducir posicion durante eventos macro"',
                            "causal_signal": "news_shock",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
            elif ptype == "microstructure_imbalance_loss":
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": "Desbalance persistente en order book produce ejecucion contra flujo dominante.",
                            "effect": "Aumenta probabilidad de reversa inmediata.",
                            "confidence": 0.79,
                            "recommended_action": "Elevar stop loss tecnico y reducir TP en escenarios de imbalance.",
                            "command": 'cgalpha codecraft apply --text "Subir stop_loss_buffer y reducir tp_factor cuando order_book_imbalance sea alto"',
                            "causal_signal": "microstructure_imbalance",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
            elif ptype == "mfe_mae_asymmetry":
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": "Asimetria MFE/MAE indica trades que no extienden a favor antes de girar.",
                            "effect": "Take profit actual es demasiado ambicioso para el regimen.",
                            "confidence": 0.74,
                            "recommended_action": "Reducir TP y aplicar trailing stop mas cercano.",
                            "command": 'cgalpha codecraft apply --text "Reducir tp_factor de 2.0 a 1.8 y activar trailing stop adaptativo"',
                            "causal_signal": "mfe_mae_asymmetry",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
            elif ptype == "repeated_action_failure":
                action = p.get("action", "unknown_action")
                hypotheses.append(
                    self._normalize_hypothesis(
                        {
                            "cause": f"Inestabilidad recurrente en el flujo '{action}'.",
                            "effect": "Errores repetidos sobre la misma accion operativa.",
                            "confidence": 0.72,
                            "recommended_action": f"Fortalecer manejo de errores y guardas en {action}.",
                            "command": f'cgalpha codecraft apply --text "Fortalecer manejo de errores en {action}"',
                            "causal_signal": "execution_stability",
                            "evidence_count": p.get("evidence_count", 0),
                        }
                    )
                )
        return hypotheses

    def _infer_with_llm(
        self,
        snapshots: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        assistant = self._get_llm()
        if assistant is None or not snapshots:
            return []

        self.metrics["llm_attempts"] += 1
        prompt = self._build_causal_prompt(snapshots, patterns)

        started_at = time.time()
        try:
            try:
                response = assistant.generate(prompt, temperature=0.2, max_tokens=1200)
            except TypeError:
                # Compatibilidad con wrappers legacy que no aceptan kwargs.
                response = assistant.generate(prompt)
            elapsed = time.time() - started_at
            logger.info("Ghost Architect LLM causal inference completed in %.2fs", elapsed)
            self.metrics["llm_successes"] += 1
        except Exception as exc:  # pragma: no cover - external dependency
            self.metrics["llm_failures"] += 1
            logger.warning("Ghost Architect LLM unavailable, fallback to heuristics: %s", exc)
            return []

        data = self._extract_json_payload(response)
        raw_hypotheses = data.get("hypotheses") if isinstance(data, dict) else None
        if not isinstance(raw_hypotheses, list):
            return []

        hypotheses = [self._normalize_hypothesis(item) for item in raw_hypotheses if isinstance(item, dict)]
        return [h for h in hypotheses if h]

    def _build_causal_prompt(
        self,
        snapshots: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
    ) -> str:
        sample = snapshots[-30:]
        summary = {
            "records": len(snapshots),
            "failure_rate": round(
                len([s for s in snapshots if s["outcome"] == "failure"]) / max(1, len(snapshots)),
                3,
            ),
            "detected_patterns": patterns,
        }
        compact_records = [
            {
                "timestamp": s.get("timestamp"),
                "action": s.get("action"),
                "outcome": s.get("outcome"),
                "mfe": s.get("mfe"),
                "mae": s.get("mae"),
                "fakeout": s.get("fakeout"),
                "news_impact": s.get("news_impact"),
                "microstructure": s.get("microstructure"),
                "order_book_imbalance": s.get("order_book_imbalance"),
                "candle_regime": s.get("candle_regime"),
                "bid_size_1_5": s.get("bid_size_1_5"),
                "ask_depth_1_5": s.get("ask_depth_1_5"),
                "spread_bps": s.get("spread_bps"),
                "cancel_ratio": s.get("cancel_ratio"),
                "replenishment_rate": s.get("replenishment_rate"),
                "sweep_events": s.get("sweep_events"),
                "micro_reversal_ticks": s.get("micro_reversal_ticks"),
                "aggressive_buy_sell_delta": s.get("aggressive_buy_sell_delta"),
                "micro_regime": s.get("micro_regime"),
                "micro_data_mode": s.get("micro_data_mode"),
                "order_book_match_type": s.get("order_book_match_type"),
                "order_book_lag_ms": s.get("order_book_lag_ms"),
            }
            for s in sample
        ]

        model_hint = os.environ.get("CGALPHA_CAUSAL_MODEL", "deepseek-coder-v2-or-equivalent")
        micro_summary = self._build_microstructure_summary(sample)
        template_context = {
            "model_hint": model_hint,
            "summary_json": json.dumps(summary, ensure_ascii=False, indent=2),
            "micro_summary_json": json.dumps(micro_summary, ensure_ascii=False, indent=2),
            "recent_context_json": json.dumps(compact_records, ensure_ascii=False, indent=2),
            "max_feature_join_lag_ms": self.max_feature_join_lag_ms,
        }

        if self._prompt_env is not None:
            try:
                template = self._prompt_env.get_template(self.prompt_template_name)
                return template.render(**template_context)
            except TemplateNotFound:
                logger.warning("Prompt template %s not found, using inline fallback", self.prompt_template_name)

        return """
Role: Ghost Architect v0.3 - Deep Causal Inference Engine.
Model hint: %(model_hint)s

Task: infer root causes, not symptoms.
Analyze full trade context with focus on Order Book / Microstructure:
- bid_size_1_5 / ask_depth_1_5
- spread_bps
- cancel_ratio / replenishment_rate
- sweep_events / micro_reversal_ticks
- MFE/MAE, news impact and candle regime

DO NOT invent data. If evidence is missing, explicitly state insufficient_evidence.

Data summary:
%(summary_json)s

Microstructure summary:
%(micro_summary_json)s

Recent trade context:
%(recent_context_json)s

Return ONLY JSON:
{
  "hypotheses": [
    {
      "root_cause_label": "liquidity_fakeout|structure_break|risk_logic_failure|news_shock|microstructure_imbalance|trend_break",
      "cause": "Root cause statement",
      "effect": "Observed performance impact",
      "confidence": 0.0,
      "causal_signal": "liquidity_fakeout|structure_break|risk_logic_failure|news_shock|microstructure_imbalance|mfe_mae_asymmetry|trend_break",
      "evidence_count": 0,
      "evidence_fields": ["spread_bps", "cancel_ratio", "replenishment_rate"],
      "recommended_action": "Concrete action",
      "command": "cgalpha codecraft apply --text \"...\""
    }
  ]
}
""" % template_context

    def _build_microstructure_summary(self, sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not sample:
            return {
                "rows": 0,
                "avg_spread_bps": None,
                "avg_cancel_ratio": None,
                "avg_replenishment_rate": None,
                "fakeout_regime_ratio": 0.0,
                "structural_regime_ratio": 0.0,
            }

        def avg_numeric(key: str) -> Optional[float]:
            values = [float(s[key]) for s in sample if isinstance(s.get(key), (int, float))]
            if not values:
                return None
            return round(mean(values), 4)

        fakeout = len([s for s in sample if s.get("micro_regime") == "noise_fakeout"])
        structural = len([s for s in sample if s.get("micro_regime") == "structural_trend"])
        return {
            "rows": len(sample),
            "avg_spread_bps": avg_numeric("spread_bps"),
            "avg_cancel_ratio": avg_numeric("cancel_ratio"),
            "avg_replenishment_rate": avg_numeric("replenishment_rate"),
            "avg_bid_size_1_5": avg_numeric("bid_size_1_5"),
            "avg_ask_depth_1_5": avg_numeric("ask_depth_1_5"),
            "fakeout_regime_ratio": round(fakeout / max(1, len(sample)), 3),
            "structural_regime_ratio": round(structural / max(1, len(sample)), 3),
        }

    def _extract_json_payload(self, text: str) -> Dict[str, Any]:
        text = (text or "").strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

    def _normalize_hypothesis(self, item: Dict[str, Any]) -> Dict[str, Any]:
        cause = str(item.get("cause", "")).strip()
        effect = str(item.get("effect", "")).strip()
        if not cause and not effect:
            return {}

        confidence = self._coerce_float(item.get("confidence"))
        confidence = self._clamp(confidence if confidence is not None else 0.75, 0.0, 1.0)
        causal_signal = self._normalize_signal(item.get("causal_signal") or item.get("root_cause_label"))
        evidence_count = int(self._coerce_float(item.get("evidence_count")) or 0)
        recommended_action = str(item.get("recommended_action", "")).strip()
        command = self._safe_command(item.get("command"), recommended_action)
        evidence_fields = item.get("evidence_fields")
        if not isinstance(evidence_fields, list):
            evidence_fields = []

        return {
            "cause": cause or "Causa causal no especificada.",
            "effect": effect or "Efecto observado no especificado.",
            "confidence": "high" if confidence >= 0.8 else "medium" if confidence >= 0.6 else "low",
            "confidence_score": round(confidence, 3),
            "causal_signal": causal_signal,
            "root_cause_label": str(item.get("root_cause_label") or causal_signal),
            "evidence_count": evidence_count,
            "evidence_fields": [str(x) for x in evidence_fields],
            "recommended_action": recommended_action or "Aplicar ajuste conservador y reevaluar.",
            "command": command,
        }

    def _compute_causal_metrics(
        self,
        snapshots: List[Dict[str, Any]],
        hypotheses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not snapshots:
            return self._empty_causal_metrics()

        baseline_failure_rate = len([s for s in snapshots if s["outcome"] == "failure"]) / len(snapshots)
        actionable = len([h for h in hypotheses if str(h.get("command", "")).startswith("cgalpha codecraft apply")])
        actionable_ratio = actionable / max(1, len(hypotheses))

        matched_signals = 0
        scored_hypotheses = 0
        hypothesis_scores: List[float] = []

        for h in hypotheses:
            signal = self._normalize_signal(h.get("causal_signal"))
            subset = [s for s in snapshots if self._signal_present(s, signal)]
            if not subset:
                continue
            matched_signals += len(subset)
            failures = len([s for s in subset if s["outcome"] == "failure"])
            precision = failures / len(subset)
            hypothesis_scores.append(precision)
            scored_hypotheses += 1

        accuracy_causal = mean(hypothesis_scores) if hypothesis_scores else baseline_failure_rate
        signal_coverage = matched_signals / max(1, len(snapshots) * max(1, len(hypotheses)))
        efficiency = 0.6 * actionable_ratio + 0.4 * signal_coverage

        return {
            "accuracy_causal": round(self._clamp(accuracy_causal, 0.0, 1.0), 3),
            "efficiency": round(self._clamp(efficiency, 0.0, 1.0), 3),
            "baseline_failure_rate": round(baseline_failure_rate, 3),
            "signal_coverage": round(self._clamp(signal_coverage, 0.0, 1.0), 3),
            "actionable_hypothesis_ratio": round(self._clamp(actionable_ratio, 0.0, 1.0), 3),
            "scored_hypotheses": scored_hypotheses,
        }

    def _build_data_alignment_summary(
        self,
        snapshots: List[Dict[str, Any]],
        order_book_index: Dict[str, Any],
    ) -> Dict[str, Any]:
        total = len(snapshots)
        with_features = len([s for s in snapshots if s.get("order_book_feature_match")])
        blind_tests = len([s for s in snapshots if s.get("micro_data_mode") == "BLIND_TEST"])
        fakeout_like = len([s for s in snapshots if s.get("micro_regime") == "noise_fakeout"])
        structural_like = len([s for s in snapshots if s.get("micro_regime") == "structural_trend"])
        nearest_matches = [
            s.get("order_book_lag_ms")
            for s in snapshots
            if s.get("order_book_match_type") == "timestamp_nearest" and isinstance(s.get("order_book_lag_ms"), int)
        ]
        avg_lag_ms = round(mean(nearest_matches), 2) if nearest_matches else None

        return {
            "order_book_features_path": str(order_book_index.get("path", self.order_book_features_path)),
            "order_book_features_loaded": bool(order_book_index.get("rows", 0)),
            "order_book_features_rows": int(order_book_index.get("rows", 0)),
            "order_book_coverage": round(with_features / max(1, total), 3),
            "blind_test_count": blind_tests,
            "blind_test_ratio": round(blind_tests / max(1, total), 3),
            "contains_blind_tests": blind_tests > 0,
            "nearest_match_avg_lag_ms": avg_lag_ms,
            "max_feature_join_lag_ms": self.max_feature_join_lag_ms,
            "noise_regime_ratio": round(fakeout_like / max(1, total), 3),
            "structural_regime_ratio": round(structural_like / max(1, total), 3),
        }

    def _empty_causal_metrics(self) -> Dict[str, Any]:
        return {
            "accuracy_causal": 0.0,
            "efficiency": 0.0,
            "baseline_failure_rate": 0.0,
            "signal_coverage": 0.0,
            "actionable_hypothesis_ratio": 0.0,
            "scored_hypotheses": 0,
        }

    def _build_readiness_gates(
        self,
        data_alignment: Dict[str, Any],
        causal_metrics: Dict[str, Any],
        records_analyzed: int,
    ) -> Dict[str, Any]:
        blind_ratio = self._coerce_float(data_alignment.get("blind_test_ratio")) or 0.0
        avg_lag = self._coerce_float(data_alignment.get("nearest_match_avg_lag_ms"))
        accuracy = self._coerce_float(causal_metrics.get("accuracy_causal")) or 0.0
        efficiency = self._coerce_float(causal_metrics.get("efficiency")) or 0.0

        data_quality = blind_ratio <= self.max_blind_test_ratio and (
            avg_lag is None or avg_lag <= self.max_nearest_match_avg_lag_ms
        )
        causal_quality = accuracy >= self.min_causal_accuracy and efficiency >= self.min_efficiency
        has_data = records_analyzed > 0
        proceed = has_data and data_quality and causal_quality

        return {
            "proceed_v03": proceed,
            "has_minimum_data": has_data,
            "data_quality_pass": data_quality,
            "causal_quality_pass": causal_quality,
            "thresholds": {
                "max_blind_test_ratio": round(self.max_blind_test_ratio, 3),
                "max_nearest_match_avg_lag_ms": round(self.max_nearest_match_avg_lag_ms, 3),
                "min_causal_accuracy": round(self.min_causal_accuracy, 3),
                "min_efficiency": round(self.min_efficiency, 3),
            },
            "observed": {
                "blind_test_ratio": round(blind_ratio, 3),
                "nearest_match_avg_lag_ms": avg_lag,
                "accuracy_causal": round(accuracy, 3),
                "efficiency": round(efficiency, 3),
                "records_analyzed": records_analyzed,
            },
        }

    def _signal_present(self, snapshot: Dict[str, Any], signal: str) -> bool:
        if signal == "fakeout":
            return snapshot.get("fakeout") is True
        if signal == "liquidity_fakeout":
            return snapshot.get("micro_regime") == "noise_fakeout" or snapshot.get("fakeout") is True
        if signal == "structure_break":
            return snapshot.get("micro_regime") == "structural_break"
        if signal == "risk_logic_failure":
            return snapshot.get("micro_regime") == "risk_logic_failure"
        if signal == "news_shock":
            return snapshot.get("news_impact") == "high"
        if signal == "microstructure_imbalance":
            imbalance = snapshot.get("order_book_imbalance")
            return snapshot.get("microstructure") in {"ask_pressure", "imbalance"} or (
                isinstance(imbalance, float) and abs(imbalance) >= 0.35
            )
        if signal == "mfe_mae_asymmetry":
            mfe, mae = snapshot.get("mfe"), snapshot.get("mae")
            if not isinstance(mfe, (int, float)) or not isinstance(mae, (int, float)) or abs(mae) < 1e-9:
                return False
            return abs(float(mfe)) / abs(float(mae)) < 0.90
        if signal == "trend_break":
            regime = str(snapshot.get("candle_regime", "")).lower()
            return any(token in regime for token in ("break", "reversal", "regime_shift"))
        if signal == "risk_regime":
            drawdown = snapshot.get("drawdown")
            return isinstance(drawdown, (int, float)) and float(drawdown) > 0.15
        if signal == "regime_shift":
            wr = snapshot.get("win_rate")
            return isinstance(wr, (int, float)) and float(wr) < 0.50
        if signal == "execution_stability":
            action = str(snapshot.get("action", "")).lower()
            return snapshot.get("outcome") == "failure" and bool(action)
        return False

    def _infer_fakeout_from_microstructure(
        self,
        spread_bps: Optional[float],
        cancel_ratio: Optional[float],
        replenishment_rate: Optional[float],
        sweep_events: Optional[int],
        micro_reversal_ticks: Optional[int],
        imbalance: Optional[float],
        aggressive_delta: Optional[float],
    ) -> bool:
        reversal_fast = isinstance(micro_reversal_ticks, int) and micro_reversal_ticks <= 3
        sweep_present = isinstance(sweep_events, int) and sweep_events >= 1
        spread_stress = isinstance(spread_bps, (int, float)) and spread_bps >= 4.0
        cancel_stress = isinstance(cancel_ratio, (int, float)) and cancel_ratio >= 1.2
        replenishment_fast = isinstance(replenishment_rate, (int, float)) and replenishment_rate >= 1.1
        imbalance_stress = isinstance(imbalance, (int, float)) and abs(float(imbalance)) >= 0.35
        delta_flip = isinstance(aggressive_delta, (int, float)) and abs(float(aggressive_delta)) >= 0.30

        return (
            (reversal_fast and sweep_present and spread_stress)
            or (cancel_stress and replenishment_fast and imbalance_stress)
            or (reversal_fast and delta_flip and spread_stress)
        )

    def _infer_micro_regime(
        self,
        spread_bps: Optional[float],
        cancel_ratio: Optional[float],
        replenishment_rate: Optional[float],
        sweep_events: Optional[int],
        micro_reversal_ticks: Optional[int],
        imbalance: Optional[float],
    ) -> str:
        if self._infer_fakeout_from_microstructure(
            spread_bps=spread_bps,
            cancel_ratio=cancel_ratio,
            replenishment_rate=replenishment_rate,
            sweep_events=sweep_events,
            micro_reversal_ticks=micro_reversal_ticks,
            imbalance=imbalance,
            aggressive_delta=None,
        ):
            return "noise_fakeout"

        imbalance_strong = isinstance(imbalance, (int, float)) and abs(float(imbalance)) >= 0.45
        spread_tight = isinstance(spread_bps, (int, float)) and spread_bps <= 2.5
        refill_weak = isinstance(replenishment_rate, (int, float)) and replenishment_rate <= 0.9
        if imbalance_strong and spread_tight and refill_weak:
            return "structural_trend"

        if isinstance(cancel_ratio, (int, float)) and cancel_ratio >= 1.8 and not imbalance_strong:
            return "risk_logic_failure"
        if isinstance(micro_reversal_ticks, int) and micro_reversal_ticks <= 5 and imbalance_strong:
            return "structural_break"
        return "uncertain"

    def _get_llm(self):
        if not self.enable_llm:
            self._llm_init_error = "llm_disabled"
            return None
        if self.llm is not None:
            return self.llm
        if get_llm_assistant is None:
            self._llm_init_error = "llm_module_unavailable"
            return None
        if not os.environ.get("OPENAI_API_KEY") and os.environ.get("CGALPHA_FORCE_LLM", "0") != "1":
            self._llm_init_error = "missing_openai_api_key"
            return None
        try:
            self.llm = get_llm_assistant()
            return self.llm
        except Exception as exc:  # pragma: no cover - optional dependency
            self._llm_init_error = str(exc)
            return None

    def _llm_status(self) -> Dict[str, Any]:
        return {
            "enabled": self.enable_llm,
            "attempts": self.metrics["llm_attempts"],
            "successes": self.metrics["llm_successes"],
            "failures": self.metrics["llm_failures"],
            "init_error": self._llm_init_error,
        }

    def _safe_command(self, command: Any, action_text: str) -> str:
        if isinstance(command, str):
            cleaned = command.strip()
            if cleaned.startswith("cgalpha codecraft apply --text "):
                return cleaned

        fallback_text = action_text or "Ajustar parametros de riesgo segun analisis causal"
        fallback_text = fallback_text.replace('"', "'")
        return f'cgalpha codecraft apply --text "{fallback_text}"'

    def _normalize_signal(self, signal: Any) -> str:
        raw = str(signal or "").strip().lower()
        for canonical, aliases in self.SIGNAL_ALIASES.items():
            if raw == canonical or raw in aliases:
                return canonical
        if "news" in raw:
            return "news_shock"
        if "liquidity" in raw and "fake" in raw:
            return "liquidity_fakeout"
        if "risk" in raw and "failure" in raw:
            return "risk_logic_failure"
        if "structure" in raw and "break" in raw:
            return "structure_break"
        if "fake" in raw:
            return "fakeout"
        if "micro" in raw or "order" in raw or "imbalance" in raw:
            return "microstructure_imbalance"
        if "mfe" in raw or "mae" in raw:
            return "mfe_mae_asymmetry"
        if "trend" in raw or "break" in raw:
            return "trend_break"
        return raw if raw else "unknown"

    def _normalize_news_impact(self, raw: Any) -> Optional[str]:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            num = float(raw)
            if num >= 0.7:
                return "high"
            if num >= 0.4:
                return "medium"
            return "low"

        text = str(raw).lower()
        if any(token in text for token in ("high", "alto", "severe", "fomc", "cpi", "nfp")):
            return "high"
        if any(token in text for token in ("medium", "medio", "moderate")):
            return "medium"
        if text:
            return "low"
        return None

    def _normalize_microstructure(self, raw: Any, imbalance: Optional[float]) -> Optional[str]:
        if isinstance(raw, str):
            text = raw.lower()
            if "ask" in text or "sell" in text:
                return "ask_pressure"
            if "bid" in text or "buy" in text:
                return "bid_pressure"
            if "imbalance" in text:
                return "imbalance"
            if "balance" in text:
                return "balanced"

        if isinstance(imbalance, float):
            if imbalance <= -0.35:
                return "ask_pressure"
            if imbalance >= 0.35:
                return "bid_pressure"
            return "balanced"
        return None

    @staticmethod
    def _coerce_float(value: Any) -> Optional[float]:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip().replace(",", ".")
            try:
                return float(text)
            except ValueError:
                return None
        return None

    @staticmethod
    def _coerce_int(value: Any) -> Optional[int]:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            text = value.strip()
            try:
                return int(float(text))
            except ValueError:
                return None
        return None

    @staticmethod
    def _to_epoch(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                pass
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(text)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except ValueError:
                return None
        return None

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            text = value.strip().lower()
            return text in {"1", "true", "yes", "y", "si", "fakeout", "trap"}
        return False

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))
