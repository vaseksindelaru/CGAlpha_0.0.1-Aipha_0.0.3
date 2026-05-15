#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PATTERN="python3 cgalpha_v3/gui/server.py"

pids="$(pgrep -f "$PATTERN" || true)"

if [[ -z "$pids" ]]; then
  echo "ℹ️ No hay proceso GUI activo."
  exit 0
fi

echo "🛑 Deteniendo GUI. PID(s): $pids"
pkill -TERM -f "$PATTERN" || true
sleep 1

remaining="$(pgrep -f "$PATTERN" || true)"
if [[ -n "$remaining" ]]; then
  echo "⚠️ Aún quedan procesos. Forzando cierre: $remaining"
  pkill -KILL -f "$PATTERN" || true
  sleep 1
fi

final="$(pgrep -f "$PATTERN" || true)"
if [[ -n "$final" ]]; then
  echo "❌ No se pudo detener completamente la GUI. PID(s): $final"
  exit 1
fi

echo "✅ GUI detenida."
