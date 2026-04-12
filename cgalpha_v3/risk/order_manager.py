import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger("order_manager")

@dataclass
class LivePosition:
    pos_id: str
    symbol: str
    direction: str  # "bullish" | "bearish"
    entry_price: float
    size_usdt: float
    sl_price: float
    tp_price: float
    entry_ts: float
    status: str = "open" # "open" | "closed"
    exit_price: Optional[float] = None
    exit_ts: Optional[float] = None
    pnl_pct: float = 0.0
    mfe: float = 0.0 # Max Favorable Excursion
    mae: float = 0.0 # Max Adverse Excursion

class DryRunOrderManager:
    """
    Order Manager en modo Dry Run (Fase 4.2).
    Soporta múltiples activos con control de exposición y margen.
    """
    def __init__(self, initial_balance: float = 10000.0):
        self.balance = initial_balance
        self.active_positions: Dict[str, LivePosition] = {}
        self.history: List[LivePosition] = []
        self.latency_ms = 150 
        self.comission_rate = 0.0004 
        
        # Parámetros de Riesgo Multi-Activo (Fase 4.2)
        self.max_exposure_per_symbol = 0.25 
        self.max_concurrent_positions = 5
        self.min_margin_available = 0.10 
        self.trade_log_path = "aipha_memory/operational/dry_run_history.jsonl"
        
        # Profit Target & Kill-Switch Psicológico (Fase 4.2+)
        self.daily_profit_target_pct = 0.02 # +2% de beneficio diario
        self.daily_stop_loss_pct = -0.015   # -1.5% de pérdida diaria
        self.session_pnl_pct = 0.0
        self.is_paused_by_target = False

    def execute_signal(self, signal: Dict) -> Optional[LivePosition]:
        """
        Convierte una señal en posición activa con validación multi-activo.
        """
        symbol = signal.get("symbol", "UNKNOWN")
        
        # 0. VALIDACIONES DE RIESGO MULTI-ACTIVO (Fase 4.2)
        if self.is_paused_by_target:
            logger.info(f"⏸️ [RISK] Trading paused: Daily Target Reached.")
            return None

        if len(self.active_positions) >= self.max_concurrent_positions:
            logger.warning(f"🚫 [RISK] Max concurrent positions ({self.max_concurrent_positions}) reached.")
            return None
            
        current_symbol_exposure = sum(p.size_usdt for p in self.active_positions.values() if p.symbol == symbol)
        if current_symbol_exposure > (self.balance * self.max_exposure_per_symbol):
            logger.warning(f"🚫 [RISK] Max exposure for {symbol} reached.")
            return None

        # 1. Simular Latencia (Slippage sintético)
        # Si el OBI es negativo en un Long, el slippage es mayor
        obi = signal.get("obi", 0.0)
        slippage_pct = 0.0001 # 0.01% base
        if signal["direction"] == "bullish" and obi < 0:
            slippage_pct += abs(obi) * 0.001
        
        entry_price = signal["price"] * (1 + slippage_pct if signal["direction"] == "bullish" else 1 - slippage_pct)
        
        # 2. Risk Sizing (Arriesgar 0.5% del balance)
        risk_per_trade = self.balance * 0.005
        # Cálculo simple de stop (1% del precio por defecto si no viene en la señal)
        sl_dist = entry_price * 0.01
        sl_price = entry_price - sl_dist if signal["direction"] == "bullish" else entry_price + sl_dist
        tp_price = entry_price + (sl_dist * 2) if signal["direction"] == "bullish" else entry_price - (sl_dist * 2)
        
        pos_id = f"DRY_{uuid.uuid4().hex[:8]}"
        pos = LivePosition(
            pos_id=pos_id,
            symbol=signal["symbol"],
            direction=signal["direction"],
            entry_price=entry_price,
            size_usdt=risk_per_trade * 10, # Apalancamiento 10x sim
            sl_price=sl_price,
            tp_price=tp_price,
            entry_ts=time.time()
        )
        
        self.active_positions[pos_id] = pos
        logger.info(f"🚀 [DRY RUN] Posición ABIERTA: {pos.pos_id} {pos.direction} @ {pos.entry_price:.2f}")
        return pos

    def update_positions(self, current_price: float):
        """
        Monitorea posiciones abiertas contra el precio actual para disparar SL/TP.
        """
        to_close = []
        for pid, pos in self.active_positions.items():
            # Actualizar MFE / MAE
            if pos.direction == "bullish":
                pos.mfe = max(pos.mfe, (current_price - pos.entry_price) / pos.entry_price)
                pos.mae = min(pos.mae, (current_price - pos.entry_price) / pos.entry_price)
                
                if current_price <= pos.sl_price:
                    self._close_position(pid, pos.sl_price, "STOP_LOSS")
                    to_close.append(pid)
                elif current_price >= pos.tp_price:
                    self._close_position(pid, pos.tp_price, "TAKE_PROFIT")
                    to_close.append(pid)
            else: # Bearish
                pos.mfe = max(pos.mfe, (pos.entry_price - current_price) / pos.entry_price)
                pos.mae = min(pos.mae, (pos.entry_price - current_price) / pos.entry_price)
                
                if current_price >= pos.sl_price:
                    self._close_position(pid, pos.sl_price, "STOP_LOSS")
                    to_close.append(pid)
                elif current_price <= pos.tp_price:
                    self._close_position(pid, pos.tp_price, "TAKE_PROFIT")
                    to_close.append(pid)
        
        for pid in to_close:
            del self.active_positions[pid]

    def close_all_positions(self, reason: str = "PANIC_CLOSE"):
        """Liquida todas las posiciones abiertas inmediatamente."""
        pids = list(self.active_positions.keys())
        for pid in pids:
            pos = self.active_positions[pid]
            # Usamos el precio de entrada como fallback si no tenemos uno real a mano, 
            # pero en un sistema real usaríamos el último mark price.
            self._close_position(pid, pos.entry_price, reason)
            del self.active_positions[pid]
        logger.warning(f"🛑 [DRY RUN] CIERRE DE EMERGENCIA: {len(pids)} posiciones liquidadas.")

    def _close_position(self, pid: str, exit_price: float, reason: str):
        pos = self.active_positions[pid]
        pos.status = "closed"
        pos.exit_price = exit_price
        pos.exit_ts = time.time()
        
        # Calcular PnL Real (con comisiones)
        gross_pnl = (exit_price - pos.entry_price) / pos.entry_price
        if pos.direction == "bearish": gross_pnl *= -1
        
        pos.pnl_pct = gross_pnl - (self.comission_rate * 2) # Entrada + Salida
        
        pnl_cash = pos.size_usdt * pos.pnl_pct
        self.balance += pnl_cash
        self.session_pnl_pct += (pnl_cash / self.balance) # Cálculo simplificado de equity
        
        # Verificar Profit Target
        if self.session_pnl_pct >= self.daily_profit_target_pct:
            self.is_paused_by_target = True
            logger.warning(f"🎯 TARGET REACHED: {self.session_pnl_pct:.2%}. Pausing for the day.")
        elif self.session_pnl_pct <= self.daily_stop_loss_pct:
            self.is_paused_by_target = True
            logger.warning(f"📉 STOP LOSS REACHED: {self.session_pnl_pct:.2%}. Pausing for safety.")
        
        # Persistencia Causal (Fase 4.2)
        self._log_trade_execution(pos, reason)
        
        self.history.append(pos)
        logger.info(f"🏁 [DRY RUN] Posición CERRADA: {pid} Reason={reason} PnL={pos.pnl_pct:.2%} (${pnl_cash:.2f})")

    def get_exposure_breakdown(self) -> Dict[str, float]:
        """Retorna el % de capital usado por cada símbolo."""
        breakdown = {}
        for pos in self.active_positions.values():
            breakdown[pos.symbol] = breakdown.get(pos.symbol, 0.0) + (pos.size_usdt / self.balance)
        return breakdown

    def _log_trade_execution(self, pos: LivePosition, reason: str):
        """Guarda trade en JSONL para auditoría del Oracle v3."""
        import json
        from pathlib import Path
        log_entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "pos_id": pos.pos_id,
            "symbol": pos.symbol,
            "direction": pos.direction,
            "pnl_pct": round(pos.pnl_pct, 6),
            "mfe": round(pos.mfe, 6),
            "mae": round(pos.mae, 6),
            "exit_reason": reason,
            "entry_price": pos.entry_price,
            "exit_price": pos.exit_price
        }
        Path("aipha_memory/operational").mkdir(parents=True, exist_ok=True)
        with open(self.trade_log_path, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
