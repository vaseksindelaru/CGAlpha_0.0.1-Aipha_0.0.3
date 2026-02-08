"""
Test de concurrencia mejorado para TaskBufferManager.
Verifica 0% pérdida de tareas en escenarios de alta concurrencia.
"""
import threading
import logging
import time
from cgalpha.nexus.task_buffer import TaskBufferManager

logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(message)s')
logger = logging.getLogger("ConcurrencyTest")
logger.setLevel(logging.INFO)

def aggressive_writer(worker_id, buffer, num_tasks=100, results=None):
    """Worker que escribe agresivamente con delays mínimas."""
    success_count = 0
    for i in range(num_tasks):
        result = buffer.save_task("stress_test", {
            "worker_id": worker_id,
            "task_seq": i,
            "timestamp": time.time()
        })
        if result:
            success_count += 1
        # No sleep - máxima presión
    
    if results is not None:
        results[worker_id] = success_count

def test_zero_loss():
    """Test principal: Verificar 0% pérdida con 50 threads x 100 tareas."""
    logger.info("🧪 Test de Concurrencia Extrema - Verificando 0% pérdida")
    
    buffer = TaskBufferManager()
    stats_before = buffer.get_stats()
    
    num_threads = 50
    tasks_per_thread = 100
    total_expected = num_threads * tasks_per_thread
    
    # Track results
    results = {}
    threads = []
    
    logger.info(f"🚀 Lanzando {num_threads} threads con {tasks_per_thread} tareas cada uno...")
    logger.info(f"📊 Total esperado: {total_expected} tareas")
    
    start = time.time()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=aggressive_writer, 
            args=(i, buffer, tasks_per_thread, results)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    duration = time.time() - start
    
    # Verify results
    stats_after = buffer.get_stats()
    total_written = sum(results.values())
    total_in_db = stats_after['total'] - stats_before['total']
    
    logger.info(f"⏱️  Duración: {duration:.2f}s ({total_expected/duration:.0f} ops/s)")
    logger.info(f"📝 Escrituras reportadas: {total_written}/{total_expected}")
    logger.info(f"💾 Registros en DB: {total_in_db}")
    logger.info(f"📊 Stats finales: {stats_after}")
    
    # Loss calculation
    loss_count = total_expected - total_in_db
    loss_percent = (loss_count / total_expected) * 100 if total_expected > 0 else 0
    
    if loss_count == 0:
        logger.info(f"✅ SUCCESS: 0% pérdida ({total_in_db}/{total_expected} tareas guardadas)")
        return True
    else:
        logger.error(f"❌ FAILURE: {loss_percent:.2f}% pérdida ({loss_count}/{total_expected} tareas perdidas)")
        return False

if __name__ == "__main__":
    success = test_zero_loss()
    exit(0 if success else 1)
