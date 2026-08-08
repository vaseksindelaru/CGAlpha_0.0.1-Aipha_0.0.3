"""
cgalpha_v3/application/resilience.py - Task Buffer Manager (Migrated from v1)
Garantiza que no se pierdan tareas ante fallos de Redis usando un buffer SQLite local.
"""

import sqlite3
import json
import logging
import time
import threading
from pathlib import Path
from typing import Dict, Any, List, Callable

log = logging.getLogger(__name__)

class TaskBuffer:
    """
    Buffer persistente local (SQLite) para tareas que fallaron en Redis.
    Inyectado desde legacy_vault/v1/cgalpha/nexus/task_buffer.py.
    """
    def __init__(self, db_path: str = "aipha_memory/temporary/task_buffer_v3.db"):
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._ensure_db()

    def _ensure_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON buffered_tasks(status)")
        except sqlite3.Error as e:
            log.error(f"Failed to initialize TaskBuffer v3: {e}")

    def save_task(self, task_type: str, payload: Dict[str, Any]) -> bool:
        """Guarda tarea en disco de forma segura."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT INTO buffered_tasks (task_type, payload, created_at, status) VALUES (?, ?, ?, ?)",
                        (task_type, json.dumps(payload), time.time(), 'pending')
                    )
                log.warning(f"💾 Task buffered locally: {task_type}")
                return True
            except sqlite3.Error as e:
                log.error(f"Critical buffer failure: {e}")
                return False

    def get_pending_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Recupera tareas para reintento."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    rows = conn.execute(
                        "SELECT * FROM buffered_tasks WHERE status = 'pending' ORDER BY created_at ASC LIMIT ?",
                        (limit,)
                    ).fetchall()
                    return [{
                        "id": r["id"],
                        "task_type": r["task_type"],
                        "payload": json.loads(r["payload"])
                    } for r in rows]
            except sqlite3.Error as e:
                log.error(f"Error reading buffer: {e}")
                return []
    
    def mark_as_recovered(self, task_ids: List[int]):
        """Marca como procesado."""
        if not task_ids: return
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    placeholders = ','.join('?' * len(task_ids))
                    conn.execute(f"UPDATE buffered_tasks SET status = 'recovered' WHERE id IN ({placeholders})", task_ids)
            except sqlite3.Error as e:
                log.error(f"Error marking recovered in buffer: {e}")
