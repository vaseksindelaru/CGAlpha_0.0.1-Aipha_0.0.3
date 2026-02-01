import pandas as pd
import duckdb
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Core Imports
from core.config_manager import ConfigManager
from core.memory_manager import MemoryManager

# Trading Manager Imports (Building Blocks)
from trading_manager.building_blocks.detectors.key_candle_detector import SignalDetector
from trading_manager.building_blocks.detectors.accumulation_zone_detector import AccumulationZoneDetector
from trading_manager.building_blocks.detectors.trend_detector import TrendDetector
from trading_manager.building_blocks.signal_combiner import SignalCombiner
from trading_manager.building_blocks.labelers.potential_capture_engine import get_atr_labels

logger = logging.getLogger("TradingEngine")

class TradingEngine:
    """
    Motor de Trading Principal de Aipha (Capa 3).
    Orquesta la detección de señales (Triple Coincidencia) y la generación de evidencia (Sensor ATR).
    """

    def __init__(self):
        self.config = ConfigManager()
        self.memory = MemoryManager()
        self.bridge_path = Path("aipha_memory/evolutionary_bridge.jsonl")
        
        # Asegurar que el bridge existe
        self.bridge_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.bridge_path.exists():
            self.bridge_path.touch()

    def load_data(self, source: str = "duckdb") -> pd.DataFrame:
        """Carga datos de mercado (por ahora DuckDB Local)."""
        # TODO: Abstraer esto para soportar Live Feed
        db_path = "data_processor/data/aipha_data.duckdb"
        table_name = "btc_1h_data"
        
        if not os.path.exists(db_path):
            logger.error(f"Base de datos no encontrada: {db_path}")
            return pd.DataFrame()
            
        try:
            conn = duckdb.connect(db_path)
            # Limitamos carga por eficiencia en dev
            df = conn.execute(f"SELECT * FROM {table_name} ORDER BY Open_Time").df()
            conn.close()
            
            df['Open_Time'] = pd.to_datetime(df['Open_Time'])
            df = df.set_index('Open_Time')
            return df
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            return pd.DataFrame()

    def run_cycle(self) -> Dict[str, Any]:
        """
        Ejecuta un ciclo completo de trading:
        1. Cargar Datos
        2. Detectar (Triple Coincidencia)
        3. Etiquetar (Sensor Ordinal)
        4. Guardar Evidencia (Bridge)
        """
        logger.info("⚡ Iniciando ciclo de TradingEngine...")
        
        # 1. Cargar Datos
        df = self.load_data()
        if df.empty:
            return {"status": "error", "message": "No data"}
            
        # 2. Pipeline de Detección (Triple Coincidencia)
        logger.info("🔍 Ejecutando Pipeline de Detección...")
        
        # A. Detectar Zonas
        df = AccumulationZoneDetector.detect_zones(
            df, 
            atr_period=14,
            atr_multiplier=1.5
        )
        
        # B. Detectar Tendencia
        df = TrendDetector.analyze_trend(
            df,
            lookback_period=20
        )
        
        # C. Detectar Velas Clave
        df = SignalDetector.detect_key_candles(
            df,
            volume_lookback=20,
            volume_percentile_threshold=self.config.get("Trading.volume_percentile_threshold", 90),
            body_percentile_threshold=30
        )
        
        # D. Combinar Señales (Triple Coincidencia)
        df = SignalCombiner.combine_signals(
            df,
            tolerance_bars=8,
            min_r_squared=0.45
        )
        
        # 3. Filtrar Eventos
        signals = df[df['is_triple_coincidence']]
        if signals.empty:
            logger.info("ℹ️ No se detectaron señales de Triple Coincidencia.")
            return {"status": "neutral", "signals_found": 0}
            
        logger.info(f"✨ {len(signals)} Señales de Triple Coincidencia detectadas.")
        
        # 4. Sensor Ordinal (Captura de Trayectorias)
        logger.info("📡 Ejecutando Sensor Ordinal (PotentialCaptureEngine)...")
        
        # Configuración dinámica del sensor
        sensor_results = get_atr_labels(
            df,
            t_events=signals.index,
            sides=signals['signal_side'],
            atr_period=14,
            profit_factors=[1.0, 2.0, 3.0], # TPs escalonados para tracking
            drawdown_threshold=0.8,
            return_trajectories=True
        )
        
        # 5. Guardar en Puente Evolutivo
        trajectories_count = self._save_to_bridge(signals, sensor_results)
        
        return {
            "status": "success", 
            "signals_found": len(signals),
            "trajectories_saved": trajectories_count
        }

    def _save_to_bridge(self, signals: pd.DataFrame, sensor_results: Dict) -> int:
        """Serializa y guarda las trayectorias en el puente JSONL."""
        count = 0
        
        try:
            with open(self.bridge_path, "a") as f:
                for timestamp in signals.index:
                    if timestamp not in sensor_results['labels'].index:
                        continue
                        
                    # Construir objeto de evidencia
                    evidence = {
                        "event_id": f"evt_{int(timestamp.timestamp())}",
                        "timestamp": timestamp.isoformat(),
                        "signal_type": "triple_coincidence",
                        "side": int(signals.loc[timestamp, 'signal_side']),
                        "zone_id": int(signals.loc[timestamp, 'zone_id']),
                        "trend_r2": float(signals.loc[timestamp, 'trend_r_squared']),
                        "outcome": {
                            "label_ordinal": int(sensor_results['labels'][timestamp]),
                            "mfe_atr": float(sensor_results['mfe_atr'][timestamp]),
                            "mae_atr": float(sensor_results['mae_atr'][timestamp]),
                            "highest_tp": int(sensor_results['highest_tp_hit'][timestamp])
                        }
                    }
                    
                    f.write(json.dumps(evidence) + "\n")
                    count += 1
                    
            logger.info(f"🌉 {count} trayectorias guardadas en Evolutionary Bridge.")
        except Exception as e:
            logger.error(f"❌ Error guardando en bridge: {e}")
            
        return count
