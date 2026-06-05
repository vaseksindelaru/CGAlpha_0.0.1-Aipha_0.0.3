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

    unique_entries = {}       # causal_key → line (FCFS: primera aparición gana)
    total_rows = 0
    duplicates_same_dir = 0   # mismo ts + precio + misma dirección
    duplicates_cross_pol = 0  # mismo ts + precio + distinta dirección (Cross-Polarity Clones)

    with open(DATASET_PATH, 'r') as f:
        for line in f:
            if not line.strip(): continue
            total_rows += 1
            try:
                data = json.loads(line)
                meta = data["_meta"]
                l2 = data.get("l2_snapshot_at_touch", {})
                zg = data.get("zone_geometry", {})

                # Causal Deduplication Key (B-008-v2):
                # Mismo momento temporal + mismo precio = Mismo evento físico
                # Sin dirección → detecta Cross-Polarity Clones
                ts = int(meta.get("capture_ts_unix_ms", 0))
                price = float(l2.get("retest_price", 0))
                direction = zg.get("direction", "unknown")

                causal_key = f"{ts}_{price:.2f}"

                if causal_key in unique_entries:
                    # Es un duplicado — clasificar tipo
                    existing_dir = unique_entries[causal_key]["direction"]
                    if existing_dir == direction:
                        duplicates_same_dir += 1
                    else:
                        duplicates_cross_pol += 1
                    # FCFS: primera aparición gana, descartamos esta
                    continue

                unique_entries[causal_key] = {
                    "direction": direction,
                    "line": line.strip(),
                }
            except Exception as e:
                print(f"Error parseando línea: {e}")

    with open(TMP_PATH, "w") as f:
        for entry in unique_entries.values():
            f.write(entry["line"] + "\n")
    TMP_PATH.replace(DATASET_PATH)

    total_dupes = duplicates_same_dir + duplicates_cross_pol
    print(f"--- LIMPIEZA COMPLETADA (B-008-v2) ---")
    print(f"Filas originales:              {total_rows}")
    print(f"Duplicados eliminados:         {total_dupes}")
    print(f"  ├─ Cross-Polarity Clones:    {duplicates_cross_pol}")
    print(f"  └─ Same-Direction Clones:    {duplicates_same_dir}")
    print(f"Filas únicas restantes:        {len(unique_entries)}")

if __name__ == "__main__":
    clean_duplicates()
