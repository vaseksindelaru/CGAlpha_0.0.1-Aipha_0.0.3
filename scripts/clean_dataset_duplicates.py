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
                sid = data["_meta"]["sample_id"]
                # Conservamos la última aparición de cada sample_id.
                unique_entries[sid] = line.strip()
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
