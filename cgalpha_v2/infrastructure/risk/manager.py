"""
CGAlpha v3 — Risk Management Layer
Módulo central de gestión de riesgo operativo.

Implementa:
- Circuit breakers por drawdown de sesión
- Límite de señales por hora
- Kill-switch manual
- Estado serializable para GUI Risk Dashboard
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class CircuitBreakerTripped(Exception):
    """Lanzada cuando el circuit breaker suspende la operación."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Circuit breaker activado: {reason}")
        self.reason = reason


class KillSwitchActive(Exception):
    """Lanzada cuando el kill-switch está activo."""

    def __init__(self) -> None:
        super().__init__("Kill-switch activo. Sistema suspendido hasta reactivación manual.")


@dataclass
class SessionRiskMetrics:
    """Métricas de riesgo de la sesión actual."""

    session_id: str = ""
    started_at: str = ""
    signals_this_hour: int = 0
    drawdown_session_pct: float = 0.0
    peak_equity: float = 0.0
    current_equity: float = 0.0
    circuit_breaker_trips: int = 0
    last_trip_reason: str = ""
    kill_switch_active: bool = False
    kill_switch_activated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "signals_this_hour": self.signals_this_hour,
            "drawdown_session_pct": round(self.drawdown_session_pct, 4),
            "peak_equity": self.peak_equity,
            "current_equity": self.current_equity,
            "circuit_breaker_trips": self.circuit_breaker_trips,
            "last_trip_reason": self.last_trip_reason,
            "kill_switch_active": self.kill_switch_active,
            "kill_switch_activated_at": self.kill_switch_activated_at,
        }


class RiskManager:
    """
    Gestor de riesgo operativo para CGAlpha v3.

    Configuración (ajustable desde GUI):
        max_drawdown_session_pct:  5.0   — suspende operación si drawdown supera este %
        max_signals_per_hour:      10    — máximo señales por hora de sesión
        max_position_size_pct:     2.0   — % máximo del capital por señal
        latency_warn_ms:           500   — umbral de alerta de latencia

    Usage:
        rm = RiskManager(initial_equity=10000.0)
        rm.start_session("session-001")
        rm.check_signal_allowed()   # lanza si hay restricción
        rm.update_equity(9800.0)    # actualiza métricas de drawdown
        rm.activate_kill_switch()   # suspende todo
    """

    def __init__(
        self,
        initial_equity: float = 10_000.0,
        max_drawdown_session_pct: float = 5.0,
        max_signals_per_hour: int = 10,
        max_position_size_pct: float = 2.0,
        latency_warn_ms: float = 500.0,
    ) -> None:
        self.initial_equity = initial_equity
        self.max_drawdown_session_pct = max_drawdown_session_pct
        self.max_signals_per_hour = max_signals_per_hour
        self.max_position_size_pct = max_position_size_pct
        self.latency_warn_ms = latency_warn_ms

        self._metrics = SessionRiskMetrics()
        self._lock = threading.Lock()
        self._signal_timestamps: list[datetime] = []
        self._event_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------ #
    # Session lifecycle
    # ------------------------------------------------------------------ #

    def start_session(self, session_id: str, initial_equity: float | None = None) -> None:
        with self._lock:
            equity = initial_equity or self.initial_equity
            self._metrics = SessionRiskMetrics(
                session_id=session_id,
                started_at=self._now_iso(),
                peak_equity=equity,
                current_equity=equity,
                kill_switch_active=False,
            )
            self._signal_timestamps.clear()
            self._log_event("session_started", {"session_id": session_id, "equity": equity})
            logger.info("RiskManager: sesión %s iniciada con equity=%.2f", session_id, equity)

    def end_session(self) -> dict[str, Any]:
        with self._lock:
            self._log_event("session_ended", self._metrics.to_dict())
            return self._metrics.to_dict()

    # ------------------------------------------------------------------ #
    # Signal gate
    # ------------------------------------------------------------------ #

    def check_signal_allowed(self) -> None:
        """
        Verifica si se puede emitir una señal.

        Raises:
            KillSwitchActive:       si kill-switch está activo
            CircuitBreakerTripped:  si drawdown o señales superan límites
        """
        with self._lock:
            if self._metrics.kill_switch_active:
                raise KillSwitchActive()

            if self._metrics.drawdown_session_pct >= self.max_drawdown_session_pct:
                reason = (
                    f"drawdown_session={self._metrics.drawdown_session_pct:.2f}% "
                    f">= límite={self.max_drawdown_session_pct}%"
                )
                self._trip_circuit_breaker(reason)

            self._clean_old_signals()
            if len(self._signal_timestamps) >= self.max_signals_per_hour:
                reason = (
                    f"señales_hora={len(self._signal_timestamps)} "
                    f">= límite={self.max_signals_per_hour}"
                )
                self._trip_circuit_breaker(reason)

            # Señal permitida
            self._signal_timestamps.append(datetime.now(tz=timezone.utc))
            self._metrics.signals_this_hour = len(self._signal_timestamps)

    def update_equity(self, current_equity: float) -> None:
        """Actualiza equity y recalcula drawdown. Puede disparar circuit breaker."""
        with self._lock:
            self._metrics.current_equity = current_equity
            if current_equity > self._metrics.peak_equity:
                self._metrics.peak_equity = current_equity

            if self._metrics.peak_equity > 0:
                self._metrics.drawdown_session_pct = (
                    (self._metrics.peak_equity - current_equity)
                    / self._metrics.peak_equity
                    * 100.0
                )
            else:
                self._metrics.drawdown_session_pct = 0.0

            if self._metrics.drawdown_session_pct >= self.max_drawdown_session_pct:
                reason = (
                    f"drawdown_session={self._metrics.drawdown_session_pct:.2f}% "
                    f">= límite={self.max_drawdown_session_pct}%"
                )
                self._trip_circuit_breaker(reason)

    # ------------------------------------------------------------------ #
    # Kill-switch
    # ------------------------------------------------------------------ #

    def activate_kill_switch(self, confirmed: bool = False) -> dict[str, Any]:
        """
        Activa el kill-switch. Requiere confirmed=True (confirmación de 2 pasos desde GUI).

        Returns:
            Estado del risk manager tras activación
        """
        if not confirmed:
            raise ValueError("Kill-switch requiere confirmed=True (confirmación de 2 pasos)")

        with self._lock:
            self._metrics.kill_switch_active = True
            self._metrics.kill_switch_activated_at = self._now_iso()
            self._log_event("kill_switch_activated", {})
            logger.critical("KILL-SWITCH ACTIVADO — operación completamente suspendida")
            return self._metrics.to_dict()

    def deactivate_kill_switch(self, confirmed: bool = False) -> dict[str, Any]:
        """Desactiva el kill-switch. Requiere confirmed=True."""
        if not confirmed:
            raise ValueError("Reactivación requiere confirmed=True")

        with self._lock:
            self._metrics.kill_switch_active = False
            self._log_event("kill_switch_deactivated", {})
            logger.warning("Kill-switch desactivado — operación reanudada")
            return self._metrics.to_dict()

    # ------------------------------------------------------------------ #
    # GUI interface
    # ------------------------------------------------------------------ #

    def get_gui_status(self) -> dict[str, Any]:
        """Retorna estado completo para el panel Risk Dashboard de la GUI."""
        with self._lock:
            m = self._metrics
            drawdown_pct = m.drawdown_session_pct
            limit_pct = self.max_drawdown_session_pct
            drawdown_bar = min(100, int(drawdown_pct / limit_pct * 100)) if limit_pct else 0

            return {
                "session_id": m.session_id,
                "kill_switch": {
                    "active": m.kill_switch_active,
                    "activated_at": m.kill_switch_activated_at,
                    "label": "🔴 ACTIVO" if m.kill_switch_active else "✅ Armado",
                },
                "drawdown": {
                    "current_pct": round(drawdown_pct, 3),
                    "limit_pct": limit_pct,
                    "bar_pct": drawdown_bar,
                    "status": "danger" if drawdown_pct >= limit_pct * 0.8 else "ok",
                },
                "signals": {
                    "this_hour": m.signals_this_hour,
                    "limit": self.max_signals_per_hour,
                },
                "circuit_breaker": {
                    "trips": m.circuit_breaker_trips,
                    "last_reason": m.last_trip_reason,
                },
                "equity": {
                    "current": m.current_equity,
                    "peak": m.peak_equity,
                },
                "config": {
                    "max_drawdown_pct": self.max_drawdown_session_pct,
                    "max_signals_per_hour": self.max_signals_per_hour,
                    "max_position_size_pct": self.max_position_size_pct,
                },
                "event_log": self._event_log[-10:],  # últimos 10 eventos para GUI
            }

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _trip_circuit_breaker(self, reason: str) -> None:
        self._metrics.circuit_breaker_trips += 1
        self._metrics.last_trip_reason = reason
        self._log_event("circuit_breaker_tripped", {"reason": reason})
        logger.error("Circuit breaker ACTIVADO: %s", reason)
        raise CircuitBreakerTripped(reason)

    def _clean_old_signals(self) -> None:
        cutoff = datetime.now(tz=timezone.utc).replace(minute=0, second=0, microsecond=0)
        self._signal_timestamps = [
            ts for ts in self._signal_timestamps if ts >= cutoff
        ]

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        self._event_log.append({
            "ts": self._now_iso(),
            "event": event_type,
            "data": data,
        })
        # Mantener solo últimos 100 eventos
        if len(self._event_log) > 100:
            self._event_log = self._event_log[-100:]

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=timezone.utc).isoformat()
