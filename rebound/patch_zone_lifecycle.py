"""
scripts/patch_zone_lifecycle.py
=================================
Shadow Harvesting — Patch 1/3
Objetivo: Añadir ZoneLifecycleState, TouchRecord, y extender ActiveZone
          para permitir múltiples retests (2do/3er toque) en triple_coincidence.py.

Método: Determinista — sin LLM, sin regex sobre lógica.
        Lee el archivo, localiza bloques exactos, reemplaza.
        Hace backup antes de escribir.

Ejecutar desde la raíz del proyecto:
    python3 scripts/patch_zone_lifecycle.py
"""

from pathlib import Path
import shutil
import sys

TARGET = Path("cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py")
BACKUP = TARGET.with_suffix(".py.bak_lifecycle")


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 1 — Nuevos imports y dataclasses al inicio del archivo (después de los
#            imports existentes y antes de la primera clase).
#            Se inserta justo después de la línea que contiene "from dataclasses"
# ─────────────────────────────────────────────────────────────────────────────

LIFECYCLE_ADDITIONS = '''

# ─── Shadow Harvesting v1: Zone Lifecycle ────────────────────────────────────

from enum import Enum

class ZoneLifecycleState(str, Enum):
    """Estado de vida de una zona para el harvesting multi-toque."""
    ACTIVE     = "active"      # Zona viva, esperando primer retest
    HARVESTING = "harvesting"  # Breakout confirmado, esperando 2do/3er toque
    EXHAUSTED  = "exhausted"   # Zona expirada (3 toques o TTL vencido)


from dataclasses import dataclass as _dc, field as _field

@_dc
class TouchRecord:
    """
    Registro inmutable de un toque a la zona.
    Se acumula en ActiveZone.touch_history.
    """
    touch_sequence: int           # 1 = primer retest, 2 = post-flip, 3 = terciario
    touch_ts_unix_ms: float
    touch_price: float
    obi_10_at_touch: float = 0.0
    cumulative_delta_at_touch: float = 0.0
    outcome: str = "PENDING"      # Relleno diferidamente por DeferredOutcomeMonitor
    polarity_flipped: bool = False # True si la zona había cambiado de polaridad

# ─────────────────────────────────────────────────────────────────────────────
'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 2 — Extensión de ActiveZone.
#            Buscamos el campo "retest_detected" y añadimos los nuevos campos
#            justo después. También añadimos los métodos de lifecycle.
# ─────────────────────────────────────────────────────────────────────────────

# Lo que existe en el dataclass ActiveZone (fragmento exacto a buscar):
ACTIVE_ZONE_OLD_FIELD = "    retest_detected: bool = False"

# Lo que ponemos en su lugar (preservamos el campo por compatibilidad pero
# añadimos toda la infraestructura nueva):
ACTIVE_ZONE_NEW_FIELDS = '''    retest_detected: bool = False  # Legado — usar lifecycle_state en su lugar

    # ── Shadow Harvesting: Zone Lifecycle ──────────────────────────────────
    lifecycle_state: ZoneLifecycleState = ZoneLifecycleState.ACTIVE
    touch_count: int = 0
    touch_history: list = None          # list[TouchRecord] — None → init en __post_init__
    polarity_flipped: bool = False
    flip_ts: float = None               # Unix timestamp del Breakout confirmado
    flip_price: float = None            # Precio donde se confirmó el Breakout
    harvest_expiry_ts: float = None     # TTL post-flip
    HARVEST_TTL_SECONDS: float = 172800 # 48 horas
    MAX_TOUCHES: int = 3

    def __post_init__(self):
        if self.touch_history is None:
            object.__setattr__(self, "touch_history", [])

    def register_breakout(self, breakout_price: float) -> None:
        """
        Transiciona la zona de ACTIVE → HARVESTING en lugar de eliminarla.
        La polaridad se invierte: soporte previo se convierte en resistencia
        y viceversa (Support/Resistance Flip).
        """
        import time as _time
        self.polarity_flipped = True
        self.flip_ts = _time.time()
        self.flip_price = breakout_price
        self.harvest_expiry_ts = self.flip_ts + self.HARVEST_TTL_SECONDS
        self.lifecycle_state = ZoneLifecycleState.HARVESTING

    def register_touch(self, price: float, obi: float = 0.0,
                       cum_delta: float = 0.0) -> int:
        """
        Registra un toque y retorna el touch_sequence asignado.
        Incrementa touch_count; si alcanza MAX_TOUCHES, marca EXHAUSTED.
        """
        import time as _time
        self.touch_count += 1
        seq = self.touch_count
        rec = TouchRecord(
            touch_sequence=seq,
            touch_ts_unix_ms=_time.time() * 1000,
            touch_price=price,
            obi_10_at_touch=obi,
            cumulative_delta_at_touch=cum_delta,
            polarity_flipped=self.polarity_flipped,
        )
        self.touch_history.append(rec)
        if self.touch_count >= self.MAX_TOUCHES:
            self.lifecycle_state = ZoneLifecycleState.EXHAUSTED
        return seq

    def is_exhausted(self) -> bool:
        """
        Una zona está agotada cuando:
          - Alcanzó MAX_TOUCHES, o
          - El TTL post-flip expiró (48h por defecto)
        """
        import time as _time
        if self.lifecycle_state == ZoneLifecycleState.EXHAUSTED:
            return True
        if (self.harvest_expiry_ts is not None
                and _time.time() > self.harvest_expiry_ts):
            self.lifecycle_state = ZoneLifecycleState.EXHAUSTED
            return True
        return False

    @property
    def effective_direction(self) -> str:
        """
        Dirección real post-flip para evaluar retests secundarios.
        Si la zona fue bullish y rompió → ahora actúa como resistencia bearish.
        """
        if not self.polarity_flipped:
            return self.direction
        return "bearish" if self.direction == "bullish" else "bullish"

    @property
    def prior_outcomes(self) -> list:
        """Lista de outcomes ya resueltos para contexto del 2do/3er toque."""
        return [r.outcome for r in self.touch_history
                if r.outcome not in ("PENDING", "")]'''


# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 3 — Cambio en el loop de retest (live path).
#            Buscamos el check que descarta zonas ya retestadas.
#            Existe en check_intra_candle_retest o process_live_tick.
# ─────────────────────────────────────────────────────────────────────────────

OLD_RETEST_SKIP = "if zone.retest_detected:"
NEW_RETEST_SKIP = "if zone.is_exhausted():"

# Debounce en el primer toque (el retest_detected = True original):
OLD_RETEST_SET = "zone.retest_detected = True"
NEW_RETEST_SET = (
    "zone.retest_detected = True  # Legado — touch registrado en Zone.register_touch()"
)

# ─────────────────────────────────────────────────────────────────────────────
# BLOQUE 4 — Garbage collector.
#            Actualmente limpia zonas con retest_detected=True.
#            Ahora las zonas se limpian solo cuando is_exhausted() es True.
# ─────────────────────────────────────────────────────────────────────────────

OLD_GC_CONDITION = "not z.retest_detected"
NEW_GC_CONDITION = "not z.is_exhausted()"

OLD_GC_CONDITION_2 = "z.retest_detected"
NEW_GC_CONDITION_2 = "z.is_exhausted()"


# ─────────────────────────────────────────────────────────────────────────────
# APLICAR PATCHES
# ─────────────────────────────────────────────────────────────────────────────

def apply():
    if not TARGET.exists():
        print(f"❌ No se encontró: {TARGET}")
        sys.exit(1)

    # Backup
    shutil.copy2(TARGET, BACKUP)
    print(f"✅ Backup creado: {BACKUP}")

    content = TARGET.read_text(encoding="utf-8")
    original_len = len(content)
    applied = []
    failed = []

    # ── Patch 1: Insertar nuevas clases después del primer "from dataclasses" ──
    # Buscamos el import de dataclasses para insertar después
    dc_import_candidates = [
        "from dataclasses import dataclass, field",
        "from dataclasses import dataclass",
        "import dataclasses",
    ]
    insertion_point = None
    for candidate in dc_import_candidates:
        idx = content.find(candidate)
        if idx != -1:
            # Encontrar el fin de esa línea
            end_of_line = content.find("\n", idx) + 1
            insertion_point = end_of_line
            break

    if insertion_point is None:
        failed.append("Bloque 1 (inserción de clases lifecycle): no se encontró import dataclasses")
    else:
        content = content[:insertion_point] + LIFECYCLE_ADDITIONS + content[insertion_point:]
        applied.append("Bloque 1: ZoneLifecycleState + TouchRecord insertados")

    # ── Patch 2: Extender ActiveZone ──────────────────────────────────────────
    if ACTIVE_ZONE_OLD_FIELD in content:
        content = content.replace(ACTIVE_ZONE_OLD_FIELD, ACTIVE_ZONE_NEW_FIELDS, 1)
        applied.append("Bloque 2: ActiveZone extendido con lifecycle + métodos")
    else:
        failed.append(f"Bloque 2: campo '{ACTIVE_ZONE_OLD_FIELD}' no encontrado en ActiveZone")

    # ── Patch 3: Cambiar check en loop de retest ──────────────────────────────
    count_old = content.count(OLD_RETEST_SKIP)
    if count_old > 0:
        content = content.replace(OLD_RETEST_SKIP, NEW_RETEST_SKIP)
        applied.append(f"Bloque 3a: '{OLD_RETEST_SKIP}' → '{NEW_RETEST_SKIP}' ({count_old} ocurrencias)")
    else:
        failed.append(f"Bloque 3a: '{OLD_RETEST_SKIP}' no encontrado")

    count_set = content.count(OLD_RETEST_SET)
    if count_set > 0:
        content = content.replace(OLD_RETEST_SET, NEW_RETEST_SET)
        applied.append(f"Bloque 3b: retest_detected=True comentado ({count_set} ocurrencias)")
    else:
        failed.append(f"Bloque 3b: '{OLD_RETEST_SET}' no encontrado (puede ser OK si no existe)")

    # ── Patch 4: Garbage collector ────────────────────────────────────────────
    gc_fixed = False
    if OLD_GC_CONDITION in content:
        content = content.replace(OLD_GC_CONDITION, NEW_GC_CONDITION)
        applied.append(f"Bloque 4a: GC usa is_exhausted() (positivo)")
        gc_fixed = True
    if OLD_GC_CONDITION_2 in content:
        content = content.replace(OLD_GC_CONDITION_2, NEW_GC_CONDITION_2)
        applied.append(f"Bloque 4b: GC usa is_exhausted() (negativo)")
        gc_fixed = True
    if not gc_fixed:
        failed.append(f"Bloque 4: condición GC '{OLD_GC_CONDITION}' no encontrada")

    # ── Escribir resultado ────────────────────────────────────────────────────
    if failed:
        print("\n⚠️  Bloques con advertencia:")
        for f in failed:
            print(f"   ✗ {f}")
        print()

    if applied:
        TARGET.write_text(content, encoding="utf-8")
        new_len = len(content)
        print(f"✅ Archivo actualizado: {TARGET}")
        print(f"   Tamaño: {original_len} → {new_len} bytes (+{new_len - original_len})")
        print("\n✅ Patches aplicados:")
        for a in applied:
            print(f"   ✓ {a}")
    else:
        print("❌ Ningún patch aplicado. Revirtiendo desde backup.")
        shutil.copy2(BACKUP, TARGET)
        sys.exit(1)

    print("\n⚡ Siguiente paso:")
    print("   python3 scripts/patch_deferred_monitor_multitouch.py")


if __name__ == "__main__":
    apply()
