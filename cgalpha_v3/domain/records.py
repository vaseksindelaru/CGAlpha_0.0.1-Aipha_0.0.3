from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class MicrostructureRecord:
    timestamp: int           # Unix ms (ID temporal único)
    symbol: str              # Ej: "BTCUSDT"
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float              # VWAP acumulado del día
    vwap_std_1: float        # Desviación estándar 1
    vwap_std_2: float        # Desviación estándar 2
    obi_10: float            # OBI con 10 niveles de profundidad
    cumulative_delta: float  # Delta acumulado desde apertura de sesión
    delta_divergence: str    # "BULLISH_ABSORPTION"|"BEARISH_EXHAUSTION"|"NEUTRAL"
    atr_14: float            # ATR de contexto (volatilidad normalizada)
    regime: str               # "HIGH_VOL"|"TREND"|"LATERAL"

@dataclass
class ZoneState:
    candle_id: int          # Timestamp de la vela de absorción origen
    state: str              # "REBOTE_CONFIRMADO" | "FAKEOUT_DETECTADO" | "RUPTURA_LIMPIA" | "ABSORCION_EN_CURSO"
    absorption_score: float # 0-1 (Confianza de la absorción institucional)
    penetration_depth: float # % de penetración en la zona
    volume_ratio: float     # Volumen del re-test vs volumen de la vela origen

@dataclass
class OutcomeOrdinal:
    trade_id: str
    mfe_atr: float          # MFE normalizado en ATR
    mae_atr: float          # MAE normalizado en ATR
    outcome: int            # 0, 1, 2, 3+ (unidades de ATR alcanzadas)
    exit_reason: str        # "TP" | "SL" | "TS" | "SHADOW_TIMEOUT"
