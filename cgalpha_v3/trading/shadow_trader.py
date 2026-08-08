from dataclasses import dataclass, field
from typing import Optional, List, Dict
from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.domain.records import OutcomeOrdinal, MicrostructureRecord
from cgalpha_v3.risk.order_manager import DryRunOrderManager, LivePosition
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BRIDGE_JSONL_PATH = "aipha_memory/evolutionary/bridge.jsonl"


@dataclass
class ShadowPosition:
    trade_id: str
    entry_price: float
    entry_time: int
    direction: int
    status: str              # "OPEN" | "CLOSED"
    mfe: float              # Max Favorable Excursion (Precio)
    mae: float              # Max Adverse Excursion (Precio)
    entry_atr: float        # ATR en el momento de la entrada
    tp_targets: List[float] # Niveles de TP (unidades de ATR)
    sl_target: float        # Nivel de SL (unidades de ATR)
    config_snapshot: Optional[Dict] = None  # Snapshot de la config al momento de entrada
    signal_data: Optional[Dict] = None      # Features completas de la señal
    causal_tags: Optional[List[str]] = None  # Tags para análisis causal


class ShadowTrader(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  MOSAIC ADAPTER — Componente v3                      ║
    ║  Heritage: legacy_vault/v1/trading_manager/          ║
    ║            potential_capture_engine.py               ║
    ║  Heritage Contribution:                              ║
    ║    - Cálculo de Outcome Ordinal (en unidades ATR)     ║
    ║    - Invariante: Nunca cerrar al primer TP           ║
    ║  v3 Adaptations:                                     ║
    ║    - Gestión de Shadow Trades (Paper Trading v3)     ║
    │    - Captura de Trayectorias MFE/MAE para el Oracle  │
    │    - Delegación en DryRunOrderManager para ejecución │
    │    - Persistencia en bridge.jsonl                    ║
    ╚═══════════════════════════════════════════════════════╝
    """

    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        self.active_positions: List[ShadowPosition] = []
        # DryRunOrderManager handles real paper-trading logic (PnL, SL/TP, MFE/MAE)
        self.order_manager = DryRunOrderManager(initial_balance=10000.0)
        # Map trade_id → ShadowPosition for tracking
        self._shadow_map: Dict[str, ShadowPosition] = {}

    def open_shadow_trade(
        self,
        entry_price: float,
        direction: int,
        atr: float,
        config_snapshot: Optional[Dict] = None,
        signal_data: Optional[Dict] = None,
        causal_tags: Optional[List[str]] = None,
    ) -> str:
        """
        Abre una posición ficticia para estudio causal.
        Delega en DryRunOrderManager para la ejecución real con PnL, SL/TP.
        Registra el trade en bridge.jsonl para auditoría persistente.
        """
        # 1. Crear Signal dict compatible con DryRunOrderManager
        direction_str = "bullish" if direction > 0 else "bearish"
        signal = {
            "symbol": "BTCUSDT",
            "price": entry_price,
            "direction": direction_str,
            "atr": atr,
            "obi": (signal_data or {}).get("obi_10_at_retest", 0.0),
        }
        if signal_data and "symbol" in signal_data:
            signal["symbol"] = signal_data["symbol"]

        # 2. Ejecutar via DryRunOrderManager
        live_pos = self.order_manager.execute_signal(signal)
        if live_pos is None:
            logger.warning("⚠️ ShadowTrader: DryRunOrderManager rechazó la señal (risk limits).")
            return ""

        # 3. Crear ShadowPosition wrapper para tracking interno
        sl_target = 1.5 * atr
        tp_targets = [2.0 * atr, 3.0 * atr, 4.0 * atr]  # Triple Barrier

        shadow_pos = ShadowPosition(
            trade_id=live_pos.pos_id,
            entry_price=entry_price,
            entry_time=int(live_pos.entry_ts * 1000),
            direction=direction,
            status="OPEN",
            mfe=0.0,
            mae=0.0,
            entry_atr=atr,
            tp_targets=tp_targets,
            sl_target=sl_target,
            config_snapshot=config_snapshot,
            signal_data=signal_data,
            causal_tags=causal_tags or [],
        )
        self.active_positions.append(shadow_pos)
        self._shadow_map[live_pos.pos_id] = shadow_pos

        # 4. Registrar en bridge.jsonl
        self._write_bridge_entry(live_pos, shadow_pos, exit_reason="OPEN")

        logger.info(
            f"📈 Shadow Trade Abierto: {live_pos.pos_id} "
            f"(direction={direction_str}, price={entry_price:.2f}, ATR={atr:.4f})"
        )
        return live_pos.pos_id

    def update_shadow_traces(
        self, current_price: float, current_time: int
    ) -> List[OutcomeOrdinal]:
        """
        Actualiza MFE/MAE de todas las posiciones abiertas.
        Delega en DryRunOrderManager para monitoreo SL/TP.
        Retorna resultados ordinales de posiciones recién cerradas.
        """
        # 1. Actualizar posiciones en DryRunOrderManager
        self.order_manager.update_positions(current_price)

        # 2. Detectar posiciones cerradas y generar OutcomeOrdinal
        closed_outcomes: List[OutcomeOrdinal] = []

        for pos in list(self.active_positions):
            if pos.status == "CLOSED":
                continue

            # Check if the position was closed in DryRunOrderManager
            if pos.trade_id not in self.order_manager.active_positions:
                # Find it in history
                hist_pos = next(
                    (h for h in self.order_manager.history if h.pos_id == pos.trade_id),
                    None,
                )
                if hist_pos is None:
                    continue

                # Calculate outcome ordinal
                atr_scale = self._get_atr_scale(pos)
                mfe_atr = hist_pos.mfe / atr_scale if atr_scale > 0 else 0.0
                mae_atr = abs(hist_pos.mae) / atr_scale if atr_scale > 0 else 0.0
                outcome = self._compute_outcome_ordinal(hist_pos, pos)

                outcome_ordinal = OutcomeOrdinal(
                    trade_id=pos.trade_id,
                    mfe_atr=round(mfe_atr, 4),
                    mae_atr=round(mae_atr, 4),
                    outcome=outcome,
                    exit_reason=getattr(hist_pos, 'status', 'UNKNOWN'),
                )
                closed_outcomes.append(outcome_ordinal)

                # Update shadow position
                pos.status = "CLOSED"
                pos.mfe = hist_pos.mfe
                pos.mae = hist_pos.mae

                # Write final bridge entry with outcome
                self._write_bridge_entry(hist_pos, pos, exit_reason=getattr(hist_pos, 'status', 'CLOSED'))

        return closed_outcomes

    def _get_atr_scale(self, shadow_pos: ShadowPosition) -> float:
        """Returns the ATR scale for normalizing MFE/MAE."""
        return shadow_pos.entry_atr if shadow_pos.entry_atr > 0 else shadow_pos.entry_price * 0.01

    def _compute_outcome_ordinal(self, live_pos: LivePosition, shadow_pos: ShadowPosition) -> int:
        """
        Computes ordinal outcome based on Triple Barrier Method.
        0 = hit SL or loss, 1 = TP1 (2 ATR), 2 = TP2 (3 ATR), 3+ = TP3+ (4+ ATR)
        """
        atr_scale = self._get_atr_scale(shadow_pos)
        if atr_scale <= 0:
            return 0

        pnl_abs = abs(live_pos.exit_price - live_pos.entry_price) if live_pos.exit_price else 0
        pnl_atr = pnl_abs / atr_scale

        if live_pos.pnl_pct < 0:
            return 0  # SL hit or loss

        if pnl_atr >= 4.0:
            return 3
        elif pnl_atr >= 3.0:
            return 2
        elif pnl_atr >= 2.0:
            return 1
        else:
            return 0  # Closed before reaching TP1

    def _write_bridge_entry(
        self,
        live_pos: LivePosition,
        shadow_pos: ShadowPosition,
        exit_reason: str,
    ):
        """Persiste trade en bridge.jsonl para auditoría causal y feedback al Oracle."""
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "trade_id": live_pos.pos_id,
            "symbol": live_pos.symbol,
            "direction": live_pos.direction,
            "entry_price": live_pos.entry_price,
            "exit_price": live_pos.exit_price,
            "pnl_pct": round(live_pos.pnl_pct, 6),
            "mfe": round(live_pos.mfe, 6),
            "mae": round(live_pos.mae, 6),
            "mfe_atr": round(live_pos.mfe / self._get_atr_scale(shadow_pos), 4) if shadow_pos.entry_atr > 0 else 0.0,
            "mae_atr": round(abs(live_pos.mae) / self._get_atr_scale(shadow_pos), 4) if shadow_pos.entry_atr > 0 else 0.0,
            "exit_reason": exit_reason,
            "entry_atr": shadow_pos.entry_atr,
            "config_snapshot": shadow_pos.config_snapshot,
            "signal_data": shadow_pos.signal_data,
            "causal_tags": shadow_pos.causal_tags,
            "microstructure_mode": (shadow_pos.signal_data or {}).get("regime", "UNKNOWN"),
            "trinity_signal": {
                "vwap": (shadow_pos.signal_data or {}).get("vwap_at_retest"),
                "obi": (shadow_pos.signal_data or {}).get("obi_10_at_retest"),
                "cum_delta": (shadow_pos.signal_data or {}).get("cumulative_delta_at_retest"),
            },
            "oracle_confidence": (shadow_pos.signal_data or {}).get("oracle_confidence"),
            "status": live_pos.status,
        }

        Path(BRIDGE_JSONL_PATH).parent.mkdir(parents=True, exist_ok=True)
        with open(BRIDGE_JSONL_PATH, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def get_active_trade_count(self) -> int:
        """Returns count of currently open shadow trades."""
        return len(self.order_manager.active_positions)

    def get_total_pnl(self) -> float:
        """Returns total PnL percentage from all closed trades."""
        if not self.order_manager.history:
            return 0.0
        total_pnl = sum(p.pnl_pct for p in self.order_manager.history)
        return total_pnl / len(self.order_manager.history)

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="ShadowTrader",
            category="trading",
            function="Gestión de posiciones ficticias y captura de trayectorias MFE/MAE (Paper Trading v3)",
            inputs=["entry_price", "direction", "atr", "current_price"],
            outputs=["OutcomeOrdinal"],
            heritage_source="legacy_vault/v1/trading_manager/potential_capture_engine.py",
            heritage_contribution="Ordinal outcome calculation based on ATR multiple bars.",
            v3_adaptations="Shadow trade lifecycle management, DryRunOrderManager delegation, bridge.jsonl persistence.",
            causal_score=0.88
        )
        return cls(manifest)
