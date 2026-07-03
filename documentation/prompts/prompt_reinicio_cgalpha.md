# PROMPT DE REINICIO CGALPHA v3 — Despues de apagon de PC

## Archivos clave del sistema
```
Proyecto:     /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
Python:       /home/vaclav/.pyenv/versions/3.11.9/bin/python3
GUI Server:   cgalpha_v3/gui/server.py (puerto 8080)
Watchdog:     harness_watchdog.py
Heartbeat:    aipha_memory/operational/heartbeat_BTCUSDT.json
Dataset:      aipha_memory/operational/training_dataset_v2.jsonl
```

---

## PROMPT PARA COPIAR Y PEGAR A HERMES

```
Se apago la PC y necesito recuperar el sistema CGAlpha v3.
Ejecuta los siguientes pasos EN ORDEN. No te saltes ningun paso.

PASO 1 — DIAGNOSTICO
Ejecuta este comando y reporta el resultado:
  cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3 && ps aux | grep -E "python.*cgalpha" | grep -v grep | wc -l && netstat -tlnp 2>/dev/null | grep 8080 | wc -l

PASO 2 — DETENER TODO
Si el resultado del PASO 1 muestra procesos o puerto ocupado, ejecuta:
  pkill -9 -f harness_watchdog.py 2>/dev/null; pkill -9 -f cgalpha_v3.gui.server 2>/dev/null; sleep 3
Verifica que el puerto quedo libre:
  netstat -tlnp 2>/dev/null | grep 8080
Si el puerto sigue ocupado, fuerza liberacion:
  fuser -k 8080/tcp 2>/dev/null; sleep 2

PASO 3 — INICIAR GUI SERVER
  cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3 && nohup /home/vaclav/.pyenv/versions/3.11.9/bin/python3 -m cgalpha_v3.gui.server > logs/gui_restart.log 2>&1 &
Espera 12 segundos:
  sleep 12

PASO 4 — VERIFICAR GUI
  curl -s -o /dev/null -w "HTTP %{http_code}" http://127.0.0.1:8080/
Si el resultado no es "HTTP 200", revisa el log:
  tail -30 /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/logs/gui_restart.log
Y reporta el error. No continues al PASO 5 si GUI no responde.

PASO 5 — INICIAR WATCHDOG
  cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3 && nohup /home/vaclav/.pyenv/versions/3.11.9/bin/python3 harness_watchdog.py --daemon > logs/watchdog_restart.log 2>&1 &
Espera 5 segundos:
  sleep 5

PASO 6 — VERIFICACION FINAL
Ejecuta este comando y verifica TODOS los criterios:
  cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3 && echo "PROCESOS:" && ps aux | grep -E "python.*cgalpha" | grep -v grep | wc -l && echo "PUERTO:" && netstat -tlnp 2>/dev/null | grep 8080 | wc -l && echo "HEARTBEAT:" && cat aipha_memory/operational/heartbeat_BTCUSDT.json && echo "WATCHDOG:" && tail -3 logs/watchdog-systemd.log

CRITERIOS DE EXITO (todos deben cumplirse):
  1. Procesos: exactamente 2 (GUI + Watchdog)
  2. Puerto: 1 (8080 LISTEN)
  3. Heartbeat last_price > 10000 (es BTC, no ETH)
  4. Heartbeat last_aggtrade_gap_ms < 30000
  5. Watchdog log dice "Check result: OK"

Si algun criterio falla, reporta cual y por que.
No digas "sistema recuperado" sin verificar los 5 criterios.
```
