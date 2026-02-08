import threading
import logging
import random
import time
from cgalpha.nexus.task_buffer import TaskBufferManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TestConcurrency")

def worker(worker_id, buffer, num_tasks=50):
    for i in range(num_tasks):
        buffer.save_task("concurrent_test", {
            "worker": worker_id, 
            "seq": i,
            "ts": time.time()
        })
        time.sleep(random.random() * 0.001) # Tiny sleep to interleave

def test_concurrency():
    logger.info("🧪 Test 3: Concurrencia SQLite (Multi-threading)")
    buffer = TaskBufferManager()
    
    stats_before = buffer.get_stats()
    logger.info(f"📊 Stats START: {stats_before}")
    
    num_threads = 20
    tasks_per_thread = 50
    total_expected = num_threads * tasks_per_thread
    
    threads = []
    
    logger.info(f"🚀 Starting {num_threads} threads, {tasks_per_thread} tasks each...")
    
    start_time = time.time()
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i, buffer, tasks_per_thread))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    end_time = time.time()
    duration = end_time - start_time
    
    stats_after = buffer.get_stats()
    new_pending = stats_after['total'] - stats_before['total'] # Assuming recovered is stable
    
    logger.info(f"📊 Stats END: {stats_after}")
    logger.info(f"⏱️ Duration: {duration:.2f}s (Avg {total_expected/duration:.1f} ops/s)")
    
    if new_pending == total_expected:
        logger.info(f"✅ SUCCESS: All {total_expected} tasks buffered correctly.")
    else:
        logger.error(f"❌ FAILURE: Expected {total_expected}, got {new_pending} new tasks.")

if __name__ == "__main__":
    test_concurrency()
