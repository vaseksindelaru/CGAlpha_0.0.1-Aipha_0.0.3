"""
Task Buffer Manager: Persistence Layer for Redis Fallback.

Misión: Garantizar que ninguna tarea se pierda cuando Redis no está disponible.
Implementación: SQLite local en `aipha_memory/temporary/task_buffer.db`.
"""

import sqlite3
import json
import logging
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Callable

logger = logging.getLogger(__name__)

class TaskBufferManager:
    def __init__(self, db_path: str = "aipha_memory/temporary/task_buffer.db"):
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._ensure_db()

    def _ensure_db(self):
        """Inicializa la base de datos y la tabla si no existen."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS buffered_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        status TEXT DEFAULT 'pending'
                    )
                """)
                # Índice para búsquedas rápidas por estado
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON buffered_tasks(status)")
        except sqlite3.Error as e:
            logger.error(f"❌ Failed to initialize TaskBuffer DB: {e}")

    def save_task(self, task_type: str, payload: Dict[str, Any]) -> bool:
        """
        Guarda una tarea fallida en el buffer local (thread-safe).
        Returns: True si se guardó correctamente.
        """
        started_at = time.time()
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO buffered_tasks (task_type, payload, created_at, status) VALUES (?, ?, ?, ?)",
                        (task_type, json.dumps(payload), time.time(), 'pending')
                    )
                logger.warning(f"💾 Task buffered to disk: {task_type}")
                if time.time() - started_at > 1.0:
                    logger.warning("save_task held lock for >1s")
                return True
            except sqlite3.Error as e:
                logger.error(f"❌ CRITICAL failure saving task to buffer: {e}")
                return False

    def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera tareas pendientes para reintento."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        "SELECT * FROM buffered_tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?",
                        (limit,)
                    ).fetchall()
                    
                    tasks = []
                    for row in rows:
                        tasks.append({
                            "id": row["id"],
                            "task_type": row["task_type"],
                            "payload": json.loads(row["payload"]),
                            "created_at": row["created_at"]
                        })
                    return tasks
            except sqlite3.Error as e:
                logger.error(f"Error reading pending tasks: {e}")
                return []

    def mark_as_recovered(self, task_ids: List[int]):
        """Marca tareas como recuperadas (procesadas o enviadas a Redis)."""
        if not task_ids:
            return
            
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    placeholders = ','.join('?' * len(task_ids))
                    conn.execute(
                        f"UPDATE buffered_tasks SET status = 'recovered' WHERE id IN ({placeholders})",
                        task_ids
                    )
            except sqlite3.Error as e:
                logger.error(f"Error marking tasks as recovered: {e}")

    def _recover_tasks(
        self,
        push_callback: Callable[[str, Dict[str, Any]], bool],
        limit: int = 50
    ) -> int:
        """
        Recupera tareas pendientes usando callback externo (ej. Redis push).

        Nota: las I/O externas se hacen fuera de lock para no bloquear el sistema.
        """
        started_at = time.time()
        pending = self.get_pending_tasks(limit=limit)
        recovered_ids: List[int] = []

        for task in pending:
            try:
                if push_callback(task["task_type"], task["payload"]):
                    recovered_ids.append(task["id"])
            except Exception as exc:
                logger.warning(f"Recovery callback failed for task {task['id']}: {exc}")

        if recovered_ids:
            self.mark_as_recovered(recovered_ids)

        duration = time.time() - started_at
        if duration > 1.0:
            logger.warning("recover_tasks operation took %.2fs", duration)

        return len(recovered_ids)

    def recover_tasks(
        self,
        push_callback: Callable[[str, Dict[str, Any]], bool],
        limit: int = 50
    ) -> int:
        """Wrapper público para recuperación."""
        return self._recover_tasks(push_callback=push_callback, limit=limit)

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """Elimina tareas antiguas (ya recuperadas o expiradas)."""
        cutoff = time.time() - (max_age_hours * 3600)
        started_at = time.time()
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "DELETE FROM buffered_tasks WHERE status = 'recovered' OR created_at < ?",
                        (cutoff,)
                    )
                    deleted = cursor.rowcount
                if deleted > 0:
                    logger.info(f"🧹 Cleaned up {deleted} old tasks from buffer")
                return deleted
            except sqlite3.Error as e:
                logger.error(f"Error cleaning up task buffer: {e}")
                return 0
            finally:
                duration = time.time() - started_at
                if duration > 1.0:
                    logger.warning("cleanup_old_tasks held lock for %.2fs", duration)

    def get_stats(self) -> Dict[str, int]:
        """Retorna estadísticas del buffer."""
        stats = {"pending": 0, "recovered": 0, "total": 0}
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    rows = conn.execute("SELECT status, COUNT(*) as count FROM buffered_tasks GROUP BY status").fetchall()
                    for row in rows:
                        stats[row[0]] = row[1]
                    stats["total"] = sum(stats.values())
            except sqlite3.Error:
                pass
        return stats
