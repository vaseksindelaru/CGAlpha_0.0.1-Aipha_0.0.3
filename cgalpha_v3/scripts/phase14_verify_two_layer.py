"""
Script para verificar la Layer 1 y Layer 2 en aislamiento (Phase 14).
Crea un snapshot sintético y lo pasa por ambas capas.
"""

import sys
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from cgalpha_v3.lila.llm.oracle import OracleTrainer_v3, OracleRegressor_MAE

logging.basicConfig(level=logging.INFO)

def main():
    print("=" * 72)
    print("  Fase 14: Verificación Integral Oracle (Two-Layer Architecture)")
    print("=" * 72)

    try:
        # 1. Cargar modelos
        print("\n[1] Cargando Capa 1: Clasificador (BOUNCE_STRONG vs BREAKOUT)...")
        oracle = OracleTrainer_v3.create_default()
        oracle_path = PROJECT_ROOT / "aipha_memory/data/models/oracle_v5.joblib"
        oracle.load_from_disk(str(oracle_path))
        print("    ✅ Capa 1 cargada.")

        print("\n[2] Cargando Capa 2: Regresor MAE...")
        regressor = OracleRegressor_MAE.create_default()
        reg_path = PROJECT_ROOT / "aipha_memory/data/models/oracle_mae_v1.joblib"
        regressor.load_from_disk(str(reg_path))
        print("    ✅ Capa 2 cargada.")

        # 2. Señal sintética con alta probabilidad de éxito (Fake BOUNCE_STRONG)
        # OBI alto, sin divergencia
        print("\n[3] Generando señal sintética (Bullish, OBI alto)...")
        retest_price = 50000.0
        atr = 150.0  # ATR de la moneda
        zone_width = 100.0  # Zona estrecha (menos de 1 ATR)
        zone_bottom = retest_price
        zone_top = retest_price + zone_width

        signal_data = {
            "vwap_at_retest": retest_price,
            "obi_10_at_retest": 0.8,
            "cumulative_delta_at_retest": 20.0,
            "delta_divergence": "CONFIRMED",
            "atr_14": atr,
            "regime": "LATERAL",
            "direction": "bullish",
            "index": 12345,
            "zone_width_atr": zone_width / atr,
            "zone_top": zone_top,
            "zone_bottom": zone_bottom,
        }
        
        print("    Features: OBI=0.8, CumDelta=20.0, Div=CONFIRMED")
        
        # 3. Inferencia Capa 1
        res_l1 = oracle.predict(micro=None, signal_data=signal_data)
        print(f"\n[4] Inferencia Capa 1 (Clasificación):")
        print(f"    Sugerencia: {res_l1.suggested_action}")
        print(f"    Confianza:  {res_l1.confidence:.2%}")

        # 4. Inferencia Capa 2 (si autoriza L1)
        if res_l1.suggested_action == "EXECUTE" and res_l1.confidence > 0.70:
            res_l2 = regressor.predict_mae(micro=None, signal_data=signal_data)
            print(f"\n[5] Inferencia Capa 2 (Regresión MAE):")
            print(f"    MAE ATR Predicho: {res_l2.predicted_mae_atr:.4f} ATR")
            print(f"    Precio original:  {retest_price:.2f}")
            print(f"    Limit Price Opt:  {res_l2.limit_price:.2f}")
            print(f"    Safety Check:     {'Seguro' if res_l2.is_safe else 'Abortado'}")
            print(f"    Razón Lógica:     {res_l2.reason}")
        else:
            print(f"\n[5] Skipped Capa 2 (Capa 1 denegó la entrada).")

    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")

if __name__ == "__main__":
    main()
