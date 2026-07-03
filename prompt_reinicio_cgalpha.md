# PROMPT DE REINICIO CGALPHA (Después de apagón)

Si el sistema CGAlpha v3 no está funcionando después de un apagón de PC, ejecuta este prompt exacto para recuperar el sistema en menos de 2 minutos:

---

```
Recupera el sistema CGAlpha v3 después de apagón siguiendo estos pasos:

1. MATA WATCHDOGS Y GUI EXISTENTES:
```bash
pkill -9 -f harness_watchdog
pkill -9 -f "server.py:main"
pkill -9 -f cgalpha_v3.gui.server
sleep 2
```

2. VERIFICA QUE NO HAY PROCESOS DUPLICADOS:
```bash
ps aux | grep -E "watchdog|cgalpha" | grep -v grep | wc -l
# Debe retornar 0
```

3. INICIA WATCHDOG (MODO FOREGROUND PARA DEBUG):
```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
source /home/vaclav/hermes-python-venv/bin/activate
python3 watchdog.py --log-level DEBUG
```

4. EN OTRA TERMINAL, INICIA GUI SERVER:
```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3
source /home/vaclav/hermes-python-venv/bin/activate
python3 -m cgalpha_v3.gui.server
```

5. VERIFICA QUE TODO ESTÁ CORRIENDO:
```bash
# Debe haber 2 procesos (watchdog + gui)
ps aux | grep -E "watchdog|cgalpha" | grep -v grep

# GUI debe responder
curl -s http://localhost:8080 | head -1
```

6. VERIFICA RECOLECCIÓN DE DATOS:
```bash
# Heartbeat debe tener datos recientes
tail -5 aipha_memory/operational/heartbeat.jsonl

# Dataset debe crecer
tail -5 aipha_memory/operational/training_dataset_v2.jsonl
```

7. SI HAY ERRORES, REPORTA:
- Mensajes de error exactos
- Estado de los procesos (ps aux)
- Últimas 10 líneas de logs/watchdog.log
```

---

## Notas técnicas:

- **Puertos**: Watchdog usa 8080, GUI usa 5000
- **Virtualenv**: Siempre activar `/home/vaclav/hermes-python-venv/bin/activate`
- **Timeout**: Si watchdog no inicia en 30s, revisar logs/watchdog.log
- **Datos**: Heartbeat se actualiza cada 5s si recolección está funcionando
