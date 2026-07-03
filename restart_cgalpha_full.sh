#!/bin/bash
# Reinicio completo de CGAlpha v3 después de apagón
# Uso: ./restart_cgalpha_full.sh

set -e

echo "🔄 Reiniciando CGAlpha v3..."

# 1. Matar TODOS los procesos existentes
echo "🛑 Deteniendo procesos..."
pkill -9 -f "harness_watchdog.py" || true
pkill -9 -f "cgi.server" || true
pkill -9 -f "cgalpha_v3.gui.server" || true
sleep 2

# 2. Verificar limpieza
WATCHDOG_COUNT=$(ps aux | grep "harness_watchdog.py" | grep -v grep | wc -l)
GUI_COUNT=$(ps aux | grep "cgalpha_v3.gui.server" | grep -v grep | wc -l)

if [ "$WATCHDOG_COUNT" -gt 0 ] || [ "$GUI_COUNT" -gt 0 ]; then
    echo "⚠️  Aún hay procesos corriendo, forzando..."
    killall -9 python3 2>/dev/null || true
    sleep 2
fi

echo "✅ Procesos limpiados"

# 3. Iniciar GUI Server
echo "🚀 Iniciando GUI Server..."
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
nohup /home/vaclav/.pyenv/versions/3.11.9/bin/python3 -m cgalpha_v3.gui.server > logs/gui_restart.log 2>&1 &
GUI_PID=$!
echo "   GUI PID: $GUI_PID"

# 4. Esperar a que GUI responda
echo "⏳ Esperando GUI Server..."
for i in {1..30}; do
    if curl -s http://localhost:8080/ > /dev/null 2>&1; then
        echo "✅ GUI Server listo (puerto 8080)"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ GUI Server no respondió en 30s"
        exit 1
    fi
done

# 5. Iniciar Watchdog
echo "🚀 Iniciando Watchdog..."
pkill -f "harness_watchdog.py" || true
sleep 1
/home/vaclav/.pyenv/versions/3.11.9/bin/python3 /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/harness_watchdog.py --daemon > logs/watchdog_restart.log 2>&1 &
WATCHDOG_PID=$!
echo "   Watchdog PID: $WATCHDOG_PID"

# 6. Verificar estado
echo "🔍 Verificando estado..."
sleep 3

WATCHDOG_COUNT=$(ps aux | grep "harness_watchdog.py" | grep -v grep | wc -l)
GUI_RESPONDS=$(curl -s http://localhost:8080/ > /dev/null 2>&1 && echo "OK" || echo "FALLA")
HEARTBEAT_EXISTS=$(test -f aipha_memory/operational/heartbeat_BTCUSDT.json && echo "OK" || echo "FALLA")

echo ""
echo "📊 Estado final:"
echo "   Watchdog: $WATCHDOG_COUNT proceso(s)"
echo "   GUI Server: $GUI_RESPONDS"
echo "   Heartbeat: $HEARTBEAT_EXISTS"

if [ "$WATCHDOG_COUNT" -ge 1 ] && [ "$GUI_RESPONDS" = "OK" ] && [ "$HEARTBEAT_EXISTS" = "OK" ]; then
    echo ""
    echo "✅ Reinicio exitoso!"
    exit 0
else
    echo ""
    echo "❌ Reinicio incompleto - revisar logs"
    exit 1
fi
