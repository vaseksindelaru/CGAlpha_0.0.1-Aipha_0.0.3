"""
Redis Client Determinista para CGAlpha.

Este módulo provee una interfaz robusta para interactuar con Redis,
enfocada en cache, colas y pub/sub para la arquitectura de CGAlpha.

Características:
- Conexión resiliente con reintentos.
- Serialización automática JSON.
- Namespacing estricto.
- Fallback a memoria local (opcional, simulado si Redis falla críticamente).
"""

import os
import json
import logging
import redis
from typing import Optional, Dict, Any, Tuple, Callable
from redis.exceptions import ConnectionError, TimeoutError, RedisError

logger = logging.getLogger(__name__)

class RedisClient:
    """
    Cliente Redis wrapper para operaciones deterministas de infraestructura.
    """
    
    NAMESPACE = "cgalpha"

    def __init__(self):
        """Inicializa la conexión con variables de entorno."""
        # Configuración
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.password = os.getenv("REDIS_PASSWORD", None)
        self.socket_connect_timeout = 5.0
        self.socket_timeout = 10.0
        
        self.pool = None
        self.client = None
        self._is_connected = False
        
        # Intento inicial
        self._connect()

    def _connect(self):
        """Intenta establecer la conexión."""
        try:
            self.pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_connect_timeout=self.socket_connect_timeout,
                socket_timeout=self.socket_timeout,
                decode_responses=True
            )
            self.client = redis.Redis(connection_pool=self.pool)
            self.client.ping()
            logger.info(f"✅ Redis conectado en {self.host}:{self.port}/{self.db}")
            self._is_connected = True
        except (ConnectionError, TimeoutError, RedisError) as e:
            logger.error(f"❌ Fallo conectando a Redis: {e}")
            self._is_connected = False

    def get_namespaced_key(self, key: str) -> str:
        """Aplica el namespace a la clave."""
        return f"{self.NAMESPACE}:{key}"

    def is_connected(self) -> bool:
        """Verifica si la conexión está activa."""
        if not self._is_connected:
            # Si no cliente, reintentar conexión completa
            if self.client is None:
                self._connect()
                return self._is_connected
                
            # Si hay cliente, probar ping
            try:
                self.client.ping()
                self._is_connected = True
                logger.info("♻️ Redis reconectado exitosamente")
            except RedisError:
                self._is_connected = False
                # Reintentar conexión completa si ping falla
                self._connect()
                
        return self._is_connected

    def health_check(self) -> bool:
        """Chequeo explícito de salud (ping)."""
        if not self.client:
            return False
        try:
            return self.client.ping()
        except RedisError:
            return False
    
    # --- Generic Queue Methods ---
    
    def push_item(self, queue_name: str, item: Dict[str, Any]) -> bool:
        """
        Encola un item genérico en una lista (RPUSH).
        """
        if not self.is_connected():
            return False
            
        full_key = self.get_namespaced_key(f"queue:{queue_name}")
        try:
            self.client.rpush(full_key, json.dumps(item))
            return True
        except (TypeError, RedisError) as e:
            logger.error(f"Error pushing item to {queue_name}: {e}")
            return False

    def pop_item(self, queue_name: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        """
        Desencola un item genérico (BLPOP - Head).
        """
        if not self.is_connected():
            return None
            
        full_key = self.get_namespaced_key(f"queue:{queue_name}")
        try:
            result = self.client.blpop(full_key, timeout=timeout)
            if result:
                _, data_str = result
                return json.loads(data_str)
            return None
        except (json.JSONDecodeError, RedisError) as e:
            logger.error(f"Error popping item from {queue_name}: {e}")
            return None

    # --- Cache de Estado ---

    def cache_system_state(self, key: str, state_dict: Dict[str, Any], ttl_seconds: int = 300) -> bool:
        """
        Guarda el estado del sistema (ej. semáforo) en cache.
        """
        if not self.is_connected():
            return False
            
        full_key = self.get_namespaced_key(f"state:{key}")
        try:
            json_data = json.dumps(state_dict)
            self.client.setex(full_key, ttl_seconds, json_data)
            return True
        except (TypeError, RedisError) as e:
            logger.error(f"Error caching system state {key}: {e}")
            return False

    def get_system_state(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Recupera el estado del sistema desde cache.
        """
        if not self.is_connected():
            return None
            
        full_key = self.get_namespaced_key(f"state:{key}")
        try:
            data = self.client.get(full_key)
            if data:
                return json.loads(data)
            return None
        except (json.JSONDecodeError, RedisError) as e:
            logger.error(f"Error retrieving system state {key}: {e}")
            return None

    # --- Colas de Tareas (FIFO) ---

    def push_analysis_task(self, task_type: str, task_data: Dict[str, Any]) -> bool:
        """
        Encola una tarea de análisis para los Labs (LPUSH).
        """
        if not self.is_connected():
            return False
            
        full_key = self.get_namespaced_key("queue:analysis")
        payload = {
            "type": task_type,
            "data": task_data,
            "timestamp": os.getenv("TIMESTAMP_MOCK", None) # Útil para testing/determinismo
        }
        
        try:
            json_payload = json.dumps(payload)
            self.client.lpush(full_key, json_payload)
            return True
        except (TypeError, RedisError) as e:
            logger.error(f"Error pushing analysis task: {e}")
            return False

    def pop_analysis_task(self, timeout: int = 0) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Desencola una tarea pendiente (BRPOP).
        Si timeout=0, bloquea indefinidamente hasta que llegue algo (cuidado).
        """
        if not self.is_connected():
            return None
            
        full_key = self.get_namespaced_key("queue:analysis")
        try:
            # brpop retorna una tupla (key, value) o None
            result = self.client.brpop(full_key, timeout=timeout)
            if result:
                _, data_str = result
                payload = json.loads(data_str)
                return payload.get("type"), payload.get("data")
            return None
        except (json.JSONDecodeError, RedisError) as e:
            logger.error(f"Error popping analysis task: {e}")
            return None

    # --- Pub/Sub ---

    def publish_event(self, channel: str, event_data: Dict[str, Any]) -> bool:
        """
        Publica un evento a un canal específico.
        """
        if not self.is_connected():
            return False
            
        full_channel = self.get_namespaced_key(f"channel:{channel}")
        try:
            json_data = json.dumps(event_data)
            self.client.publish(full_channel, json_data)
            return True
        except (TypeError, RedisError) as e:
            logger.error(f"Error publishing event to {channel}: {e}")
            return False

    def subscribe_to_events(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Suscribe un callback a un canal.
        NOTA: Esto bloquea el hilo si se usa en un loop simple. 
        Se recomienda usar en un thread o proceso separado.
        """
        if not self.is_connected():
            logger.warning("Cannot subscribe: Redis disconnected")
            return
            
        full_channel = self.get_namespaced_key(f"channel:{channel}")
        pubsub = self.client.pubsub()
        pubsub.subscribe(full_channel)
        
        logger.info(f"🎧 Suscrito a {full_channel}")
        
        try:
            for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        callback(data)
                    except json.JSONDecodeError:
                        logger.error(f"Received invalid JSON on {channel}")
        except RedisError as e:
            logger.error(f"Error in pubsub loop {channel}: {e}")
            self._is_connected = False

    # --- Distributed Lock ---

    def acquire_lock(self, resource: str, timeout: int = 30) -> bool:
        """
        Intenta adquirir un lock distribuido simple.
        """
        if not self.is_connected():
            # Si no hay Redis, asumimos éxito local (ops degradado) o fallo seguro?
            # Para recursos críticos distribuidos, mejor fallar seguro (False).
            # Pero si es un sistema único, podríamos devolver True.
            # Siguiendo principio de resiliencia: Fallar seguro para evitar race conditions reales.
            return False
            
        key = self.get_namespaced_key(f"lock:{resource}")
        try:
            # set nx=True (set if not exists), ex=timeout (expire)
            return bool(self.client.set(key, "LOCKED", nx=True, ex=timeout))
        except RedisError as e:
            logger.error(f"Error acquiring lock for {resource}: {e}")
            return False

    def release_lock(self, resource: str) -> bool:
        """
        Libera un lock.
        """
        if not self.is_connected():
            return False
            
        key = self.get_namespaced_key(f"lock:{resource}")
        try:
            self.client.delete(key)
            return True
        except RedisError as e:
            logger.error(f"Error releasing lock for {resource}: {e}")
            return False
