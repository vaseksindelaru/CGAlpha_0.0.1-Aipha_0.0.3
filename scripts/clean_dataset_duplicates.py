import json
import shutil
from pathlib import Path

DATASET_PATH = Path("aipha_memory/operational/training_dataset_v2.jsonl")
BACKUP_PATH = Path("aipha_memory/operational/training_dataset_v2.jsonl.bak")
TMP_PATH = Path("aipha_memory/operational/training_dataset_v2.jsonl.tmp")

def clean_duplicates():
    if not DATASET_PATH.exists():
        print("No existe el dataset.")
        return

    print(f"Copiando backup en {BACKUP_PATH}...")
    shutil.copy(DATASET_PATH, BACKUP_PATH)

    unique_entries = {}
    total_rows = 0
    
    with open(DATASET_PATH, 'r') as f:
        for line in f:
            if not line.strip(): continue
            total_rows += 1
            try:
                data = json.loads(line)
                meta = data["_meta"]
                l2 = data.get("l2_snapshot_at_touch", {})
                zg = data.get("zone_geometry", {})
                
                # Causal Deduplication Key: Mismo momento temporal + mismo precio de contacto + misma dirección de zona = Mismo evento físico
                ts = meta.get("capture_ts_unix_ms", 0)
                price = l2.get("retest_price", 0)
                direction = zg.get("direction", "unknown")
                
                causal_key = f"{ts}_{price}_{direction}"
                # Conservamos la última aparición de cada evento físico.
                unique_entries[causal_key] = line.strip()
            except Exception as e:
                print(f"Error parseando línea: {e}")

    with open(TMP_PATH, "w") as f:
        for line in unique_entries.values():
            f.write(line + "\n")
    TMP_PATH.replace(DATASET_PATH)

    diff = total_rows - len(unique_entries)
    print(f"--- LIMPIEZA COMPLETADA ---")
    print(f"Filas originales: {total_rows}")
    print(f"Filas únicas: {len(unique_entries)}")
    print(f"Duplicados eliminados: {diff}")

if __name__ == "__main__":
    clean_duplicates()
