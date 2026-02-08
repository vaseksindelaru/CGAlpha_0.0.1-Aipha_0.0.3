# 🏗️ Integración de Redis en CGAlpha

## 1. Misión
Redis actúa como la capa de infraestructura **determinista** para el sistema distribuido CGAlpha. Su función es proporcionar almacenamiento volátil de alta velocidad, gestión de colas de mensajes y coordinación entre componentes.

**Principio Rector:** Redis NO gestiona lógica de negocio, solo persistencia efímera y transporte de datos.

## 2. Arquitectura

### Namespacing
Todas las claves deben seguir estrictamente el prefijo `cgalpha:` para evitar colisiones.

| Tipo | Prefijo Clave | Descripción | TTL Típico |
|---|---|---|---|
| **Cache** | `cgalpha:state:{key}` | Estado del sistema (semáforo, métricas) | 10s - 5m |
| **Cola** | `cgalpha:queue:{name}` | Colas FIFO para tareas (analysis, reports) | N/A |
| **Pub/Sub** | `cgalpha:channel:{name}` | Eventos en tiempo real (regime_change) | N/A |
| **Lock** | `cgalpha:lock:{resource}` | Lock distribuido para prevenir race conditions | 30s |

### Componentes Clave

1.  **CGA_Ops (Producer/Coordinator):**
    *   Publica el estado del semáforo (`state:global_resources`).
    *   Encola tareas de análisis (`queue:analysis`).
    *   Gestiona locks distribuidos.

2.  **Labs (Consumers):**
    *   Consumen tareas de `queue:analysis`.
    *   Publican reportes en `queue:reports`.

3.  **CGA_Nexus (Consumer/Synthesizer):**
    *   Consume reportes de `queue:reports`.
    *   Publica cambios de régimen (`channel:market_regime`).

## 3. Configuración y Deployment

### Variables de Entorno (.env)
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=secret
```

### Script de Control
Usa `scripts/start_redis.sh` para asegurar que el servicio esté activo antes de iniciar el sistema.

## 4. Patrones de Resiliencia

### Fallback a Memoria Local
Si Redis no está disponible, `CGA_Ops` detecta el fallo y:
1.  Loguea el error (`ERROR: Redis connection failed`).
2.  Desactiva las funciones distribuidas.
3.  Retorna `False` en adquisiciones de lock (o True si es single-instance, configurable).

### Buffer Persistente (SQLite)
Para garantizar que **NUNCA** se pierdan tareas críticas cuando Redis falla, se implementa un buffer persistente en disco.

*   **Ubicación:** `aipha_memory/temporary/task_buffer.db`
*   **Gestor:** `TaskBufferManager`
*   **Comportamiento:**
    1.  Si `push_analysis_task` falla, la tarea se guarda en SQLite.
    2.  `CGAOps` intenta recuperar tareas automáticamente cuando detecta que Redis vuelve a estar online.

### Script de Recuperación Manual
Si es necesario forzar la recuperación de tareas:
```bash
python scripts/recover_redis_buffer.py
```
Usa `--dry-run` para simular sin enviar:
```bash
python scripts/recover_redis_buffer.py --dry-run
```

### Reconexión Automática
El cliente `RedisClient` implementa lógica de `retry` con backoff exponencial transparente para el usuario.

## 5. Troubleshooting

**Verificar conexión:**
```bash
redis-cli ping
# PONG
```

**Monitorear colas en tiempo real:**
```bash
redis-cli monitor | grep "cgalpha"
```

**Limpiar estado (Danger):**
```bash
redis-cli --scan --pattern "cgalpha:*" | xargs redis-cli del
```
