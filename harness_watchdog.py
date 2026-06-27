#!/usr/bin/env python3
"""
CGAlpha External Watchdog with Embedded Heartbeat Architecture
============================================================
Monitorea heartbeat.json generado por LiveDataFeedAdapter._export_heartbeat()
y detecta fallos silenciosos del pipeline de trading.

Reglas rigidas:
  1. heartbeat.json sin actualizar > 10 min  -> Adaptador muerto
  2. last_aggtrade_gap_ms > 30000           -> WebSocket desconectado
  3. Sin nuevas muestras en > 60 min         -> Silencio operativo

Uso:
  python harness_watchdog.py --project-root /path/to/CGAlpha_0.0.1-Aipha_0.0.3
  python harness_watchdog.py --daemon  # corre en loop cada 120s
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

HEARTBEAT_FILE = "aipha_memory/operational/heartbeat.json"
DATASET_FILE = "aipha_memory/operational/training_dataset_v2.jsonl"

MAX_HEARTBEAT_AGE_S = 600        # 10 minutos
MAX_AGGTRADE_GAP_MS = 30_000     # 30 segundos
MAX_DATASET_AGE_S = 3_600        # 60 minutos

POLL_INTERVAL_S = 120            # 2 minutos entre checks
RESTART_COOLDOWN_S = 300         # 5 minutos entre reintentos
MAX_RESTART_ATTEMPTS = 3

RESTART_SCRIPT = "restart_pipeline.sh"  # Script de reinicio del pipeline

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WATCHDOG] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("watchdog")

# ─── State ───────────────────────────────────────────────────────────────────

_consecutive_failures = 0
_last_restart_ts = 0.0
_restart_count = 0
_running = True


def _shutdown(signum, frame):
    global _running
    logger.info("Watchdog detenido (signal %d)", signum)
    _running = False


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


# ─── Core Checks ─────────────────────────────────────────────────────────────

def load_heartbeat(project_root: Path) -> dict | None:
    """Carga heartbeat.json. None si no existe o esta corrupto."""
    path = project_root / HEARTBEAT_FILE
    if not path.exists():
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("heartbeat.json invalido: %s", e)
        return None


def check_heartbeat_age(data: dict) -> tuple[bool, str]:
    """Regla 1: heartbeat sin actualizar > 10 min."""
    ts_unix_ms = data.get("ts_unix_ms", 0)
    if ts_unix_ms <= 0:
        return False, "ts_unix_ms invalido"
    age_s = (int(time.time() * 1000) - ts_unix_ms) / 1000
    if age_s > MAX_HEARTBEAT_AGE_S:
        return False, f"heartbeat age={age_s:.0f}s > {MAX_HEARTBEAT_AGE_S}s (adaptador muerto)"
    return True, f"age={age_s:.0f}s OK"


def check_aggtrade_gap(data: dict) -> tuple[bool, str]:
    """Regla 2: WebSocket desconectado."""
    gap = data.get("last_aggtrade_gap_ms", 0)
    if gap > MAX_AGGTRADE_GAP_MS:
        return False, f"aggtrade_gap={gap}ms > {MAX_AGGTRADE_GAP_MS}ms (WebSocket caido)"
    return True, f"aggtrade_gap={gap}ms OK"


def check_dataset_freshness(project_root: Path, data: dict) -> tuple[bool, str]:
    """Regla 3: Sin nuevas muestras en > 60 min."""
    dataset_path = project_root / DATASET_FILE
    if not dataset_path.exists():
        # Si el dataset no existe pero el pipeline esta vivo, esta bien
        # (se crea con el primer retest resuelto)
        ts_unix_ms = data.get("ts_unix_ms", 0)
        if ts_unix_ms > 0:
            return True, "dataset no existe aun (pipeline vivo, esperando primer retest)"
        return False, "dataset no existe y heartbeat invalido"

    try:
        dataset_mtime = dataset_path.stat().st_mtime
    except OSError:
        return False, "no se puede leer dataset mtime"

    # Usar dataset_mtime del heartbeat como referencia de ultima escritura
    heartbeat_dataset_mtime = data.get("dataset_mtime", 0)
    if heartbeat_dataset_mtime > 0:
        age_s = time.time() - heartbeat_dataset_mtime
    else:
        age_s = time.time() - dataset_mtime

    if age_s > MAX_DATASET_AGE_S:
        return False, f"dataset sin cambios hace {age_s/60:.1f}min > {MAX_DATASET_AGE_S/60:.0f}min (silencio operativo)"
    return True, f"dataset age={age_s/60:.1f}min OK"


# ─── Actions ─────────────────────────────────────────────────────────────────

def send_alert(subject: str, body: str):
    """Envia alerta por email via Gmail API."""
    try:
        hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
        gmail_script = (
            Path(hermes_home) / "skills" / "productivity" /
            "google-workspace" / "scripts" / "google_api.py"
        )
        if not gmail_script.exists():
            logger.warning("Script Gmail no encontrado, no se puede enviar alerta")
            return

        result = subprocess.run(
            [
                sys.executable, str(gmail_script), "gmail", "send",
                "--to", "arturcloe2084@gmail.com",
                "--subject", f"[CGAlpha WATCHDOG] {subject}",
                "--body", body,
            ],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            logger.info("Alerta enviada: %s", subject)
        else:
            logger.error("Fallo envio de alerta: %s", result.stderr[:200])
    except Exception as e:
        logger.error("Excepcion enviando alerta: %s", e)


def attempt_restart(project_root: Path) -> bool:
    """Intenta reiniciar el pipeline."""
    global _last_restart_ts, _restart_count

    now = time.time()
    if now - _last_restart_ts < RESTART_COOLDOWN_S:
        logger.info("Cooldown activo, reinicio pospuesto (%.0fs restantes)",
                     RESTART_COOLDOWN_S - (now - _last_restart_ts))
        return False

    if _restart_count >= MAX_RESTART_ATTEMPTS:
        logger.critical("Maximo de reintentos alcanzado (%d). Intervencion manual requerida.", MAX_RESTART_ATTEMPTS)
        send_alert(
            "CRITICO: Max reintentos alcanzado",
            f"El watchdog intento reiniciar {MAX_RESTART_ATTEMPTS} veces sin exito.\n"
            f"Intervencion manual requerida.\n"
            f"Timestamp: {datetime.now(timezone.utc).isoformat()}"
        )
        return False

    restart_script = project_root / RESTART_SCRIPT
    if not restart_script.exists():
        logger.warning("Script de reinicio no encontrado: %s", restart_script)
        return False

    logger.warning("Intentando reiniciar pipeline (intento %d/%d)...",
                    _restart_count + 1, MAX_RESTART_ATTEMPTS)

    try:
        subprocess.Popen(
            ["bash", str(restart_script)],
            cwd=str(project_root),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _last_restart_ts = now
        _restart_count += 1
        logger.info("Reinicio lanzado (PID en background)")
        return True
    except Exception as e:
        logger.error("Fallo al lanzar reinicio: %s", e)
        return False


# ─── Main Check Cycle ────────────────────────────────────────────────────────

def run_check(project_root: Path) -> dict:
    """Ejecuta un ciclo completo de verificacion."""
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "UNKNOWN",
        "checks": {},
        "action": "none",
    }

    data = load_heartbeat(project_root)

    if data is None:
        result["status"] = "ERROR"
        result["checks"]["heartbeat_file"] = (False, "heartbeat.json no existe o corrupto")
        result["action"] = "alert"
        send_alert(
            "ALERTA: Sin heartbeat",
            f"heartbeat.json no existe o esta corrupto.\n"
            f"El pipeline puede estar muerto.\n"
            f"Timestamp: {result['timestamp']}"
        )
        return result

    # Check 1: Heartbeat age
    ok1, msg1 = check_heartbeat_age(data)
    result["checks"]["heartbeat_age"] = (ok1, msg1)

    # Check 2: AggTrade gap
    ok2, msg2 = check_aggtrade_gap(data)
    result["checks"]["aggtrade_gap"] = (ok2, msg2)

    # Check 3: Dataset freshness
    ok3, msg3 = check_dataset_freshness(project_root, data)
    result["checks"]["dataset_freshness"] = (ok3, msg3)

    # Decision
    global _consecutive_failures, _restart_count
    all_ok = ok1 and ok2 and ok3

    if all_ok:
        result["status"] = "OK"
        if _consecutive_failures > 0:
            logger.info("Recuperacion detectada tras %d fallos consecutivos", _consecutive_failures)
            _consecutive_failures = 0
            _restart_count = 0  # Resetear contador de reintentos tras recuperacion
            send_alert(
                "RECUPERADO: Pipeline operativo",
                f"El pipeline se recupero exitosamente.\n"
                f"Checks: {msg1} | {msg2} | {msg3}\n"
                f"Timestamp: {result['timestamp']}"
            )
    else:
        _consecutive_failures += 1
        result["status"] = "ERROR"
        result["action"] = "restart"

        failed = [k for k, (ok, _) in result["checks"].items() if not ok]
        logger.warning("Fallo detectado (%d consecutivos): %s",
                        _consecutive_failures, ", ".join(failed))

        # Log detallado
        for check_name, (ok, msg) in result["checks"].items():
            if not ok:
                logger.warning("  FAIL: %s -> %s", check_name, msg)
            else:
                logger.info("  OK:   %s -> %s", check_name, msg)

        # Intentar reinicio
        restart_ok = attempt_restart(project_root)
        if not restart_ok and _restart_count >= MAX_RESTART_ATTEMPTS:
            result["action"] = "manual_intervention"

    return result


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CGAlpha External Watchdog")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Raiz del proyecto CGAlpha",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Correr en loop infinito",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecutar un solo check y salir",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    logger.info("Watchdog iniciado. Project root: %s", project_root)
    logger.info("Heartbeat file: %s", project_root / HEARTBEAT_FILE)
    logger.info("Check interval: %ds | Max age: %ds | Max gap: %dms | Max dataset age: %ds",
                POLL_INTERVAL_S, MAX_HEARTBEAT_AGE_S, MAX_AGGTRADE_GAP_MS, MAX_DATASET_AGE_S)

    if args.once:
        result = run_check(project_root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["status"] == "OK" else 1

    # Daemon mode — autonomous watchdog
    logger.info("Watchdog autonomo activo. Corriendo cada %ds...", POLL_INTERVAL_S)
    logger.info("Detectara paralisis, intentara reiniciar y notificara por email.")

    # Startup grace period: esperar a que el pipeline genere su primer heartbeat
    # Evita falsas alertas si el watchdog arranca antes que el pipeline
    GRACE_PERIOD_S = 180  # 3 minutos
    logger.info(f"Startup grace period: {GRACE_PERIOD_S}s (esperando primer heartbeat...)")
    grace_start = time.time()
    pipeline_alive_once = False

    while _running:
        try:
            heartbeat_path = project_root / HEARTBEAT_FILE
            elapsed = time.time() - grace_start

            # Durante grace period: solo verificar que el pipeline existe
            if elapsed < GRACE_PERIOD_S and not pipeline_alive_once:
                if heartbeat_path.exists():
                    logger.info(f"   Startup: heartbeat detectado tras {elapsed:.0f}s. Grace period superado.")
                    pipeline_alive_once = True
                else:
                    remaining = GRACE_PERIOD_S - elapsed
                    if int(elapsed) % 30 == 0:  # Log cada 30s
                        logger.info(f"   Startup: esperando pipeline... ({remaining:.0f}s restantes)")
                    time.sleep(min(10, remaining))
                    continue

            # Modo normal de monitoreo
            result = run_check(project_root)
            status_emoji = "OK" if result["status"] == "OK" else "ERROR"
            logger.info("Check result: %s | %s",
                        status_emoji,
                        " | ".join(f"{k}={'OK' if ok else 'FAIL'}" for k, (ok, _) in result["checks"].items()))

            if result["status"] != "OK":
                logger.warning("=== ALERTA: Cosecha detenida detectada ===")
                logger.warning("Accion tomada: %s", result.get("action", "none"))

        except Exception as e:
            logger.error("Excepcion en check cycle: %s", e, exc_info=True)

        # Sleep interruptible
        for _ in range(POLL_INTERVAL_S):
            if not _running:
                break
            time.sleep(1)

    logger.info("Watchdog finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
