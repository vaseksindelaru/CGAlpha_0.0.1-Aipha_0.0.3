"""
CGAlpha v2 - Configuración Centralizada
Define parámetros de VWAP, OBI, Cumulative Delta
"""

# ===== VWAP REAL-TIME CONFIG =====
VWAP_CONFIG = {
    'window_ticks': 300,           # ~5min en 60 ticks/sec
    'std_multiplier': 2.0,         # Bandas: VWAP ± (STD * 2)
    'update_interval_ms': 100,     # Recalcular cada 100ms
    'min_volume_threshold': 1000,  # Ignorar ticks muy pequeños
}

# ===== OBI TRIGGER CONFIG =====
OBI_CONFIG = {
    'depth_levels': 10,            # Microestructura: top 10 niveles
    'obi_threshold': 0.25,         # OBI > ±0.25 es señal
    'history_size': 5,             # Últimas 5 actualizaciones
    'strength_threshold': 0.15,    # Fuerza mínima de señal
    'min_strengthening_ticks': 2,  # Debe fortalecerse N ticks
}

# ===== CUMULATIVE DELTA CONFIG =====
CUMULATIVE_DELTA_CONFIG = {
    'window_minutes': 1,           # Ventana de 1 minuto
    'reversal_percentile_weak': 25,  # Weak: percentil 25
    'reversal_percentile_strong': 10,  # Strong: percentil 10
    'history_depth': 100,          # Track últimas 100 ticks
    'exhaustion_window': 20,       # Calcular agotamiento en 20 ticks
}

# ===== CONTROL DE EJECUCIÓN =====
EXECUTION_CONFIG = {
    'min_entry_interval_ms': 500,  # Anti-bounce: 500ms entre entradas
    'latency_target_ms': 15,       # Target latencia total
    'max_spread_pips': 1.5,        # No entrar si spread > 1.5 pips
    'partial_exit_pct': 0.50,      # Salida parcial: 50%
    'full_exit_pct': 1.00,         # Salida completa: 100%
}

# ===== LOGGING CONFIG =====
LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_vwap_updates': False,     # Verbose: cada tick VWAP
    'log_obi_updates': False,      # Verbose: cada actualización OBI
    'log_delta_updates': False,    # Verbose: cada trade tick
    'log_entry_signals': True,     # Importante: cada entrada
    'log_exit_signals': True,      # Importante: cada salida
}

# ===== VALIDACIÓN =====
VALIDATION_CONFIG = {
    'require_all_signals': True,    # Todos deben confirmar (VWAP + OBI + CumDelta)
    'allow_partial_confirmation': False,  # Si es False, requiere 100% confirmación
    'confidence_threshold': 0.60,   # Mínima confianza para entrada
}
