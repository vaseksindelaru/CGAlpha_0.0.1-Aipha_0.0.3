"""
Clean proposal backlog — keep 1 per target_attribute (most recent), reject the rest.
Usage:
  python3 scripts/clean_proposal_backlog.py            # diagnostic only
  python3 scripts/clean_proposal_backlog.py --confirm   # apply cleanup
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, ".")
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine


def run_cleanup(confirm: bool = False):
    engine = MemoryPolicyEngine()
    engine.load_from_disk()
    pending = engine.get_pending_proposals()

    # Group by target_attribute
    by_attr: dict[str, list] = {}
    for entry in pending:
        try:
            data = json.loads(entry.content)
            attr = data.get("spec", {}).get("target_attribute", "unknown")
            if attr not in by_attr:
                by_attr[attr] = []
            by_attr[attr].append((entry, data))
        except Exception:
            pass

    print("=== BACKLOG DE PROPUESTAS ===\n")
    for attr, entries in sorted(by_attr.items(), key=lambda x: -len(x[1])):
        print(f"  {attr}: {len(entries)} propuestas")

    total = sum(len(v) for v in by_attr.values())
    print(f"\nTotal: {total} propuestas en {len(by_attr)} atributos")

    # Identify duplicates — keep most recent per attribute
    to_keep = []
    to_reject = []
    for attr, entries in by_attr.items():
        # Sort by timestamp descending — most recent first
        entries.sort(key=lambda x: x[1].get("timestamp", ""), reverse=True)
        to_keep.append(entries[0])  # most recent
        to_reject.extend(entries[1:])  # rest are duplicates

    print(f"\nPlan: mantener {len(to_keep)} (1 por atributo), rechazar {len(to_reject)} duplicadas")

    if not confirm:
        print("\nEjecutar con --confirm para aplicar la limpieza")
        return

    # Apply: reject duplicates
    rejected = 0
    for entry, data in to_reject:
        try:
            data["status"] = "REJECTED_DUPLICATE"
            data["rejection_reason"] = (
                f"Duplicate of {data.get('spec', {}).get('target_attribute', '?')} — "
                f"only most recent proposal kept per attribute"
            )
            entry.content = json.dumps(data, ensure_ascii=False)
            entry.tags.append("rejected_duplicate")
            engine._persist_memory_entry(entry)
            rejected += 1
        except Exception as e:
            print(f"  Error rechazando {entry.entry_id}: {e}")

    print(f"\n✓ {rejected} propuestas duplicadas rechazadas")
    print(f"  {len(to_keep)} propuestas únicas preservadas")


if __name__ == "__main__":
    confirm = "--confirm" in sys.argv
    run_cleanup(confirm=confirm)
