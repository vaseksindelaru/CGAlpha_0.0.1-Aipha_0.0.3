#!/usr/bin/env bash
# Auto-restart script for CGAlpha pipeline
# Called by harness_watchdog.py when failure is detected
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/restart_$(date +%Y%m%d_%H%M%S).log"

echo "[$(date +%Y-%m-%d_%H:%M:%S)] Reiniciando pipeline..." >> "$LOG_FILE"

# 1. Matar instancias previas de launch_shadow_live.py
pkill -f "launch_shadow_live.py" 2>/dev/null || true
sleep 2
# Nota: pkill retorna exit 1 si no hay proceso, pero || true evita que set -e aborte

# 2. Limpiar heartbeat viejo para que el watchdog no confunda con uno valido
HEARTBEAT="$ROOT_DIR/aipha_memory/operational/heartbeat.json"
if [[ -f "$HEARTBEAT" ]]; then
    mv "$HEARTBEAT" "${HEARTBEAT}.bak.$(date +%s)" 2>/dev/null || true
fi

# 3. Lanzar pipeline en vivo
PYTHONPATH=. python3 cgalpha_v3/scripts/launch_shadow_live.py >> "$LOG_FILE" 2>&1 &
PID=$!

sleep 3

if kill -0 "$PID" 2>/dev/null; then
    echo "[$(date +%Y-%m-%d_%H:%M:%S)] Pipeline reiniciado exitosamente (PID=$PID)" >> "$LOG_FILE"
    echo "OK: Pipeline reiniciado (PID=$PID)"
else
    echo "[$(date +%Y-%m-%d_%H:%M:%S)] FALLO al reiniciar pipeline" >> "$LOG_FILE"
    echo "ERROR: Ver logs en $LOG_FILE"
    exit 1
fi
