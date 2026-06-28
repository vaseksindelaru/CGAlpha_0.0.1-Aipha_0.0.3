# ADR-EVO-TICKET-0008-1: Arquitectura Watchdog Externa vs Interna

## 1. Título y Estatus
- **Título**: División de Responsabilidades entre Emisor de Heartbeat y Daemon Externalizado (Watchdog).
- **Estatus**: ACEPTADO e IMPLEMENTADO retrospectivamente.
- **Contexto**: Para solucionar inestabilidades del pipeline (tiempo en el que la red está colgada, Websocket congelado), se decidió que el sistema necesitaba resiliencia activa.

## 2. El Problema (Cat. 3)
La inserción en `live_adapter.py` de lógica de monitoreo afecta la arquitectura principal del software. Es necesario documentar por qué el sistema no simplemente intenta auto-reiniciarse, sino que se delega esto a sistema operativo y scripts externos.

## 3. La Decisión Técnica
1. **Emisión Atómica en el Core (`live_adapter.py`)**: 
   Se inyecta el método `_export_heartbeat()` como emisor pasivo. Únicamente se limita a hacer dumps atómicos (`rename()`) a disco del estado actual. Emplea un estrangulador (`throttle`) de 10 segundos para no bloquear I/O ni afectar el "Speed 2" (frecuencia sub-segundo de streams).

2. **Watchdog Desacoplado (`harness_watchdog.py`)**:
   Implementado como un binario en un servicio Ubuntu real (`systemd`). Monitoriza la edad de archivo y datos. Con potestad otorgada para invocar ejecuciones forzosas (`SIGKILL` mediante `restart_pipeline.sh`).

## 4. Alternativas Descartadas
- **Monitor en `threading.Thread` o Corrutina `asyncio`**: Totalmente descartado. Si el Global Interpreter Lock (GIL) en el proceso de Python queda colgado o hay fugas de memoria y el OOM (Out Of Memory) interviene, tanto el script principal como su hilo monitor mueren simultáneamente.
- **Reloj del Sistema Local `cron`**: Un cron tiene ciclos de minuto exacto y no puede gestionar tiempos dinámicos como "gap de más de 30,000ms" de forma suave y sin chanchorreo de scripts sucios en memoria. Un Daemon puro asincrónico fue lo correcto.

## 5. Conclusión
El acoplamiento se mantiene bajo (el Live Adapter ni siquiera "sabe" que hay un watchdog vigilándolo, solo cumple escribiendo el `.json`), y nos otorga un 100% de aislamiento ante fallas catastróficas.
