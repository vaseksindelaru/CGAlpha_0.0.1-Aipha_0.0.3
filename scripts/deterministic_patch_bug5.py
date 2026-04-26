import sys
from pathlib import Path

TARGET_FILE = Path("cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py")

NEW_METHOD = """    def _determine_outcome(self, df: pd.DataFrame, retest_idx: int, zone=None) -> str:
        \"\"\"Determina outcome (BOUNCE vs BREAKOUT) usando los límites de la zona.\"\"\"
        if zone is None:
            return 'BOUNCE' # Fallback legacy
        
        lookahead = self.config['outcome_lookahead_bars']
        if retest_idx + lookahead >= len(df):
            return 'PENDING'

        zone_top = zone.zone_top
        zone_bottom = zone.zone_bottom

        for i in range(1, lookahead + 1):
            future_idx = retest_idx + i
            future_close = df.iloc[future_idx]['close']
            
            if zone.direction == 'bullish':
                if future_close < zone_bottom:
                    return 'BREAKOUT'  # rompió hacia abajo
                if future_close > zone_top:
                    return 'BOUNCE'    # rebotó hacia arriba
            else:
                if future_close > zone_top:
                    return 'BREAKOUT'  # rompió hacia arriba
                if future_close < zone_bottom:
                    return 'BOUNCE'    # rebotó hacia abajo
        
        return 'BOUNCE'  # se mantuvo en zona
"""

def apply_fix():
    print(f"Reading {TARGET_FILE}...")
    content = TARGET_FILE.read_text()
    lines = content.splitlines()
    new_lines = []
    
    in_old_method = False
    method_replaced = False
    call_replaced = False
    
    for i, line in enumerate(lines):
        # 1. Reemplazar la firma y el cuerpo del método
        if "def _determine_outcome(self, df: pd.DataFrame, retest_idx: int) -> str:" in line:
            print(f"Found method at line {i+1}. Replacing...")
            new_lines.append(NEW_METHOD.rstrip())
            in_old_method = True
            method_replaced = True
            continue
            
        if in_old_method:
            # Detectar fin del método (siguiente def o línea con menos indentación)
            if line.strip() and line.startswith("    def ") or (line.strip() and not line.startswith("    ")):
                in_old_method = False
            else:
                continue # Saltar líneas del método viejo
        
        # 2. Reemplazar la llamada
        if "outcome = self._determine_outcome(df, retest.retest_index)" in line:
            print(f"Found call site at line {i+1}. Updating call...")
            new_lines.append(line.replace("retest.retest_index)", "retest.retest_index, retest.zone)"))
            call_replaced = True
            continue
            
        new_lines.append(line)

    if method_replaced and call_replaced:
        TARGET_FILE.write_text("\n".join(new_lines) + "\n")
        print("✅ SUCCESS: BUG-5 deterministic fix applied.")
    else:
        print(f"❌ FAILED: Method replaced: {method_replaced}, Call replaced: {call_replaced}")

if __name__ == "__main__":
    apply_fix()
