#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

DEFAULT_PORT="${CGV3_PORT:-8080}"
PORT_CANDIDATES=("$DEFAULT_PORT" "5000" "8081")
HOST="${CGV3_HOST:-127.0.0.1}"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/gui_$(date +%Y%m%d_%H%M%S).log"

is_port_free() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ! ss -ltn "( sport = :$port )" 2>/dev/null | grep -q ":$port"
  elif command -v netstat >/dev/null 2>&1; then
    ! netstat -ltn 2>/dev/null | grep -q ":$port"
  else
    # Sin herramienta de inspección: asumimos libre y dejamos que Python valide.
    return 0
  fi
}

SELECTED_PORT=""
for p in "${PORT_CANDIDATES[@]}"; do
  if is_port_free "$p"; then
    SELECTED_PORT="$p"
    break
  fi
done

if [[ -z "$SELECTED_PORT" ]]; then
  echo "❌ No hay puertos libres en la lista: ${PORT_CANDIDATES[*]}"
  exit 1
fi

echo "🌐 GUI host: $HOST"
echo "🌐 GUI port: $SELECTED_PORT"
echo "📝 Log file: $LOG_FILE"

PYTHONPATH=. CGV3_HOST="$HOST" CGV3_PORT="$SELECTED_PORT" \
  python3 cgalpha_v3/gui/server.py >"$LOG_FILE" 2>&1 &

GUI_PID=$!
sleep 1

if ! kill -0 "$GUI_PID" 2>/dev/null; then
  echo "❌ La GUI no arrancó correctamente. Revisa: $LOG_FILE"
  exit 1
fi

echo "✅ GUI iniciada (PID=$GUI_PID)"
echo "➡️  URL: http://$HOST:$SELECTED_PORT"
echo "📄 Para seguir logs: tail -f $LOG_FILE"
