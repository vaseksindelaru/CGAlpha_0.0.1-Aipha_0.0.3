#!/bin/bash

# ==============================================================================
# CGAlpha v3 — RECOVERY SCRIPT (Auto-Start)
# Uso: ./scripts/recovery.sh
# ==============================================================================

PROJECT_ROOT="/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3"
cd "$PROJECT_ROOT" || exit 1

echo "🌌 Iniciando Restauración de Sistemas CGAlpha..."

# 1. Limpieza de procesos zombies (opcional)
pkill -f "cgalpha_v3/gui/server.py"
pkill -f "cgalpha_v3/scripts/launch_shadow_live.py"
sleep 2

# 2. Iniciar Dashboard (GUI)
echo "🖥️ Levantando Control Room (GUI)..."
nohup python3 -u cgalpha_v3/gui/server.py >> gui_server.log 2>&1 &
echo "   [OK] Lobby disponible en http://127.0.0.1:8080"

# 3. Iniciar Pipeline de Cosecha L2 (Shadow Trader)
echo "📡 Levantando Cosecha de Microestructura L2..."
export PYTHONPATH="."
export CGALPHA_BINANCE_MARKET="spot"
export ORACLE_MODE="observe"
export CGALPHA_DISABLE_NEXUS_GATE="1"
export CGALPHA_BYPASS_DISABLE_AT_FULL="${CGALPHA_BYPASS_DISABLE_AT_FULL:-50}"
export CGALPHA_BYPASS_DISABLE_MODE="${CGALPHA_BYPASS_DISABLE_MODE:-set_a_ready}"
export CGALPHA_SET_A_MIN_BOUNCE="${CGALPHA_SET_A_MIN_BOUNCE:-8}"
export CGALPHA_SET_A_MIN_BREAKOUT="${CGALPHA_SET_A_MIN_BREAKOUT:-16}"
export CGALPHA_SET_A_MIN_FULL="${CGALPHA_SET_A_MIN_FULL:-24}"
export CGALPHA_PROXIMITY_PENALTY="${CGALPHA_PROXIMITY_PENALTY:-0.85}"

nohup python3 -u cgalpha_v3/scripts/launch_shadow_live.py >> shadow_trader.log 2>&1 &
echo "   [OK] Cosechadora activa (Modo Observe/Spot)"
echo "   [OK] NexusGate bypass habilitado (mode=${CGALPHA_BYPASS_DISABLE_MODE})"
echo "   [OK] Auto-disable Set A: BOUNCE_STRONG>=${CGALPHA_SET_A_MIN_BOUNCE}, BREAKOUT>=${CGALPHA_SET_A_MIN_BREAKOUT}, FULL>=${CGALPHA_SET_A_MIN_FULL}"

echo "------------------------------------------------------------------------------"
echo "✅ Sistema Restablecido."
echo "   - Para ver logs de la GUI: tail -f gui_server.log"
echo "   - Para ver logs de Cosecha: tail -f shadow_trader.log"
echo "------------------------------------------------------------------------------"
