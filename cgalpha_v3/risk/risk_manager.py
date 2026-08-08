"""
CGAlpha v3 — Risk Management Layer (Sección M)
===============================================
Circuit breakers, kill-switch state, drawdown monitor.

Parámetros por defecto (todos configurables desde GUI):
  max_drawdown_session: 5%
  max_position_size:    2% del capital
  max_signals_per_hour: 10
  min_signal_quality:   0.65
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from cgalpha_v3.domain.models.signal import Signal

log = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# PARÁMETROS DE RIESGO
# ──────────────────────────────────────────────────────────────

@dataclass
class RiskParams:
    """Parámetros de riesgo configurables desde GUI (Sección M)."""
    max_drawdown_session_pct: float = 5.0
    max_position_size_pct:    float = 2.0
    max_signals_per_hour:     int   = 10
    min_signal_quality_score: float = 0.65
    circuit_breaker_latency_ms: float = 1000.0
    circuit_breaker_latency_window_s: float = 60.0


# ──────────────────────────────────────────────────────────────
# TIPO DE INCIDENTE
# ──────────────────────────────────────────────────────────────

@dataclass
class Incident:
    """Incidente registrado por el Risk Manager."""
    incident_id:   str
    priority:      str   # "P0" | "P1" | "P2" | "P3"
    description:   str
    occurred_at:   datetime
    resolved:      bool = False
    post_mortem:   str | None = None


# ──────────────────────────────────────────────────────────────
# KILL-SWITCH STATE
# ──────────────────────────────────────────────────────────────

class KillSwitchState:
    """Estado del kill-switch. Confirmación de 2 pasos (Sección M)."""

    def __init__(self) -> None:
        self._state: str = "armed"   # armed | arming | triggered | disabled

    @property
    def is_triggered(self) -> bool:
        return self._state == "triggered"

    @property
    def state(self) -> str:
        return self._state

    def arm_request(self) -> None:
        """Paso 1: solicitar activación."""
        if self._state == "armed":
            self._state = "arming"
            log.warning("[KillSwitch] Solicitud de activación (paso 1 de 2)")

    def confirm(self) -> None:
        """Paso 2: confirmar activación."""
        if self._state == "arming":
            self._state = "triggered"
            log.critical("[KillSwitch] ACTIVADO — todas las señales suspendidas")
        else:
            raise ValueError(f"No hay solicitud pendiente de confirmación (estado: {self._state})")

    def reset(self) -> None:
        """Re-armar desde GUI."""
        self._state = "armed"
        log.info("[KillSwitch] Re-armado")

    def disable(self) -> None:
        """Solo para mantenimiento planificado."""
        self._state = "disabled"


# ──────────────────────────────────────────────────────────────
# CIRCUIT BREAKER
# ──────────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    Circuit breaker según Sección M:
    - Drawdown sesión > max → suspender operación
    - Latencia API > 1000ms p95 sostenida >60s → stand-by
    - Data Quality Gate falla → suspender señales
    - 3 señales rechazadas consecutivas → revisar threshold
    """

    def __init__(self, params: RiskParams) -> None:
        self.params   = params
        self._active  = False
        self._reason: str | None = None
        self._consecutive_rejected = 0

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def reason(self) -> str | None:
        return self._reason

    def check_drawdown(self, drawdown_pct: float) -> bool:
        """Devuelve True si el CB se ha activado."""
        if drawdown_pct > self.params.max_drawdown_session_pct:
            self._activate(f"Drawdown sesión {drawdown_pct:.2f}% > límite {self.params.max_drawdown_session_pct}%")
            return True
        return False

    def check_data_quality(self, quality_ok: bool) -> bool:
        if not quality_ok:
            self._activate("Data Quality Gate fallido")
            return True
        return False

    def record_signal_rejection(self) -> bool:
        self._consecutive_rejected += 1
        if self._consecutive_rejected >= 3:
            self._activate("3 señales consecutivas rechazadas por filtro ML")
            return True
        return False

    def record_signal_acceptance(self) -> None:
        self._consecutive_rejected = 0

    def reset(self) -> None:
        self._active = False
        self._reason = None
        self._consecutive_rejected = 0
        log.info("[CircuitBreaker] Reseteado")

    def _activate(self, reason: str) -> None:
        self._active  = True
        self._reason  = reason
        log.critical(f"[CircuitBreaker] ACTIVADO: {reason}")


# ──────────────────────────────────────────────────────────────
# RISK MANAGER PRINCIPAL
# ──────────────────────────────────────────────────────────────

class RiskManager:
    """
    Orquesta el Risk Management Layer completo (Sección M).
    Expone métodos que la GUI y el Change Proposer consultan antes de cada acción.
    """

    def __init__(
        self,
        params: RiskParams | None = None,
        on_incident: Callable[[Incident], None] | None = None,
    ) -> None:
        self.params          = params or RiskParams()
        self.kill_switch     = KillSwitchState()
        self.circuit_breaker = CircuitBreaker(self.params)
        self._drawdown_pct   = 0.0
        self._incidents:     list[Incident] = []
        self._on_incident    = on_incident or (lambda i: None)
        self._signals_this_hour: list[float] = []

    # ── DRAWDOWN ────────────────────────────────
    @property
    def drawdown_session_pct(self) -> float:
        return self._drawdown_pct

    def update_drawdown(self, pct: float) -> None:
        self._drawdown_pct = pct
        triggered = self.circuit_breaker.check_drawdown(pct)
        if triggered:
            self._register_incident(
                "P0",
                f"Circuit breaker activado por drawdown: {pct:.2f}%",
            )

    # ── VALIDAR SEÑAL ────────────────────────────
    def validate_signal(self, signal: Signal, data_quality_ok: bool = True) -> tuple[bool, str]:
        """
        Valida una señal contra todos los gates de riesgo.
        Retorna (ok, motivo).
        """
        if self.kill_switch.is_triggered:
            return False, "Kill-switch activado"

        if self.circuit_breaker.is_active:
            return False, f"Circuit breaker activo: {self.circuit_breaker.reason}"

        if not data_quality_ok:
            self.circuit_breaker.check_data_quality(False)
            return False, "Data Quality Gate fallido"

        if signal.quality_score < self.params.min_signal_quality_score:
            rejected = self.circuit_breaker.record_signal_rejection()
            reason = f"Calidad insuficiente: {signal.quality_score:.2f} < {self.params.min_signal_quality_score}"
            if rejected:
                self._register_incident("P1", "3 señales rechazadas consecutivas por calidad")
            return False, reason

        # Rate limiting
        now = time.time()
        self._signals_this_hour = [t for t in self._signals_this_hour if now - t < 3600]
        if len(self._signals_this_hour) >= self.params.max_signals_per_hour:
            return False, f"Límite de señales/hora alcanzado ({self.params.max_signals_per_hour})"

        self._signals_this_hour.append(now)
        self.circuit_breaker.record_signal_acceptance()
        return True, "ok"

    # ── INCIDENTS ────────────────────────────────
    @property
    def incidents(self) -> list[Incident]:
        return list(self._incidents)

    def _register_incident(self, priority: str, description: str) -> None:
        import uuid
        inc = Incident(
            incident_id=str(uuid.uuid4()),
            priority=priority,
            description=description,
            occurred_at=datetime.now(timezone.utc),
        )
        self._incidents.append(inc)
        self._on_incident(inc)
        log.warning(f"[Incident {priority}] {description}")

    # ── STATUS PARA GUI ──────────────────────────
    def status_snapshot(self) -> dict:
        """Snapshot compatible con gui_status_snapshot (Sección J)."""
        return {
            "kill_switch_status":        self.kill_switch.state,
            "circuit_breaker_active":    self.circuit_breaker.is_active,
            "circuit_breaker_reason":    self.circuit_breaker.reason,
            "drawdown_session_pct":      self._drawdown_pct,
            "max_drawdown_session_pct":  self.params.max_drawdown_session_pct,
            "min_signal_quality_score":  self.params.min_signal_quality_score,
            "max_signals_per_hour":      self.params.max_signals_per_hour,
            "incidents_count":           len(self._incidents),
        }

    # ── RECICLAJE LEGACY: CAUSAL AUDITOR (v1/RiskBarrierLab) ──
    def run_causal_audit(self, bridge_path: str) -> list[dict]:
        """
        Lógica reciclada de legacy_vault/v1/cgalpha/labs/risk_barrier_lab.py.
        Analiza el bridge.jsonl para encontrar ineficiencias causales.
        """
        from pathlib import Path
        import pandas as pd
        import json
        
        p = Path(bridge_path)
        if not p.exists():
            return []
            
        data = []
        with open(p, 'r') as f:
            for line in f:
                try:
                    evt = json.loads(line)
                    if 'outcome' in evt:
                        data.append({
                            'label': evt['outcome'].get('label_ordinal', 0),
                            'mfe': evt['outcome'].get('mfe_atr', 0),
                            'mae': evt['outcome'].get('mae_atr', 0),
                            'regime': evt.get('causal_tags', ['UNKNOWN'])[0]
                        })
                except: continue
        
        if not data: return []
        df = pd.DataFrame(data)
        
        findings = []
        for regime, group in df.groupby('regime'):
            win_rate = len(group[group['label'] > 0]) / len(group)
            if win_rate < 0.40:
                findings.append({
                    "type": "risk_alert",
                    "regime": regime,
                    "insight": f"Win Rate crítico ({win_rate:.1%}) detectado por auditoría causal.",
                    "action": "Increase confidence_threshold"
                })
        return findings
