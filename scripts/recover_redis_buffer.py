#!/usr/bin/env python3
"""
Recover Redis Buffer.

Script de mantenimiento para recuperar tareas fallidas guardadas en SQLite local
y reintentar su envío a Redis cuando el servicio esté disponible.

Uso:
    python recover_redis_buffer.py [--dry-run]
"""

import sys
import logging
import argparse
import time
from pathlib import Path

# Añadir root al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from cgalpha.nexus.redis_client import RedisClient
from cgalpha.nexus.task_buffer import TaskBufferManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RecoverBuffer")

def recover_tasks(dry_run: bool = False):
    logger.info("🔧 Iniciando recuperación de buffer local...")
    
    redis_client = RedisClient()
    if not redis_client.is_connected():
        logger.error("❌ Redis no está disponible. Abortando recuperación.")
        sys.exit(1)
        
    buffer_manager = TaskBufferManager()
    stats = buffer_manager.get_stats()
    logger.info(f"📊 Estadísticas del buffer: {stats}")
    
    tasks = buffer_manager.get_pending_tasks(limit=100)
    if not tasks:
        logger.info("✅ No hay tareas pendientes para recuperar.")
        return

    logger.info(f"🔄 Intentando recuperar {len(tasks)} tareas...")
    
    recovered_count = 0
    failed_count = 0
    recovered_ids = []
    
    for task in tasks:
        task_id = task['id']
        task_type = task['task_type']
        payload = task['payload']
        
        logger.info(f"   Task #{task_id} ({task_type}) - Created: {time.ctime(task['created_at'])}")
        
        if dry_run:
            logger.info("   [DRY-RUN] Task skipped")
            continue
            
        if redis_client.push_analysis_task(task_type, payload):
            logger.info(f"   ✅ Task #{task_id} re-enqueued to Redis")
            recovered_ids.append(task_id)
            recovered_count += 1
        else:
            logger.error(f"   ❌ Task #{task_id} failed to push to Redis")
            failed_count += 1
            
    if not dry_run and recovered_ids:
        buffer_manager.mark_as_recovered(recovered_ids)
        logger.info(f"💾 Marked {len(recovered_ids)} tasks as recovered in DB")
        
    # Cleanup old stuff
    if not dry_run:
        cleaned = buffer_manager.cleanup_old_tasks(max_age_hours=24)
        logger.info(f"🧹 Cleaned {cleaned} old recovered entries")
        
    logger.info(f"🏁 Recuperación completada: {recovered_count} exitosos, {failed_count} fallidos")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recover failed tasks from local SQLite buffer to Redis")
    parser.add_argument("--dry-run", action="store_true", help="Simulate recovery without sending to Redis")
    args = parser.parse_args()
    
    recover_tasks(dry_run=args.dry_run)
