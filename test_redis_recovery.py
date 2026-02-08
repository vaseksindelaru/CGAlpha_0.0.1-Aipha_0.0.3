import sys
import logging
import time
from cgalpha.nexus.ops import CGAOps
from cgalpha.nexus.redis_client import RedisClient
from cgalpha.nexus.task_buffer import TaskBufferManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TestRecovery")

def test_recovery():
    logger.info("🧪 Test 2: Recuperación (Redis Up -> Drain Buffer)")
    
    # Check buffer first
    buffer = TaskBufferManager()
    stats_before = buffer.get_stats()
    logger.info(f"📊 Stats BEFORE recovery: {stats_before}")
    
    # Trigger auto-recovery via Ops
    ops = CGAOps()
    
    if not ops.redis or not ops.redis.is_connected():
        logger.error("❌ Redis is DOWN! Start it before running this.")
        sys.exit(1)
        
    logger.info("✅ Redis connected. Waiting for auto-recovery...")
    
    # Ops tries recover on init and on get_resource_state
    start_time = time.time()
    while time.time() - start_time < 5:
        ops.get_resource_state() # Triggers recovery check
        stats = buffer.get_stats()
        if stats.get('recovered', 0) > stats_before.get('recovered', 0):
            break
        time.sleep(0.5)
        
    stats_after = buffer.get_stats()
    recovered = stats_after['recovered'] - stats_before['recovered']
    
    logger.info(f"📊 Stats AFTER recovery attempt: {stats_after}")
    logger.info(f"🔄 Recovered Count: {recovered}")
    
    # Verify Redis Queue manually
    r = RedisClient()
    queue_len = r.client.llen("cgalpha:queue:analysis")
    logger.info(f"📬 Redis Queue Length: {queue_len} (Should be > 0)")
    
    item = r.pop_analysis_task(timeout=1)
    if item:
        logger.info(f"✅ Successfully popped item from Redis: {item[0]}")
    else:
        logger.warning("⚠️ Could not pop item from Redis (queue empty?)")

if __name__ == "__main__":
    test_recovery()
