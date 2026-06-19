#!/usr/bin/env bash
# Reinicia la cosecha L2 del CGAlpha v3:
# 1. Detiene la GUI.
# 2. Limpia zonas activas persistidas (evita que zonas viejas reaparezcan).
# 3. Arranca la GUI de nuevo.
# 4. Espera y verifica que el endpoint forense responda.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

AUTH_TOKEN="${CGV3_AUTH_TOKEN:-cgalpha-v3-local-dev}"
API_URL="http://127.0.0.1:8080/api/l2-forensics/status"

echo "🛑 1. Deteniendo GUI..."
./stop_gui.sh

echo "🧹 2. Limpiando zonas persistidas..."
echo '[]' > aipha_memory/operational/detector_state.json
echo '[]' > aipha_memory/operational/active_zones.json

echo "🚀 3. Arrancando GUI..."
./start_gui.sh

echo "⏳ 4. Esperando 10 segundos a que el servidor responda..."
sleep 10

echo "🔍 5. Verificando estado forense..."
if response=$(curl -s -H "Authorization: Bearer $AUTH_TOKEN" "$API_URL" 2>/dev/null); then
  zones=$(echo "$response" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['active_zones']))" 2>/dev/null || echo "?")
  pending=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin)['pending_count'])" 2>/dev/null || echo "?")
  dataset=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['dataset_total']} total / {d['full_samples']} FULL\")" 2>/dev/null || echo "?")
  echo "   Zonas activas: $zones"
  echo "   Retests pendientes: $pending"
  echo "   Dataset: $dataset"
  echo "✅ Cosecha reiniciada correctamente."
else
  echo "❌ El servidor no responde en $API_URL"
  echo "   Revisa los logs con: tail -f logs/gui_*.log"
  exit 1
fi
