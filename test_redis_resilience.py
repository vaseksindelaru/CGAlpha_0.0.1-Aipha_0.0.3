import sys
import logging
from cgalpha.nexus.ops import CGAOps
from cgalpha.nexus.task_buffer import TaskBufferManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("TestResilience")

def test_resilience():
    logger.info("🧪 Test 1: Resiliencia (Redis Down -> Buffer Local)")
    
    # Force RedisClient to fail connection (simulated if service not stopped, but we expect it stopped)
    ops = CGAOps()
    
    # Check status
    if ops.redis and ops.redis.is_connected():
        logger.warning("⚠️ Redis seems connected! The test expects Redis to be DOWN.")
        logger.warning("run 'sudo systemctl stop redis-server' first for real test.")
    else:
        logger.info("✅ Redis is disconnected as expected.")

    # Push tasks
    tasks_to_push = 5
    logger.info(f"Attempting to push {tasks_to_push} tasks...")
    
    for i in range(tasks_to_push):
        payload = {"data": f"critical_value_{i}"}
        # This returns True if buffered, False if dropped (should return True now)
        success = ops.push_lab_task("lab_test", payload)
        if success:
            logger.info(f"   Task {i} -> Accepted (Buffered)")
        else:
            logger.error(f"   ❌ Task {i} -> DROPPED (Failed)")

    # Verify buffer
    buffer = TaskBufferManager()
    stats = buffer.get_stats()
    logger.info(f"📊 Buffer Stats: {stats}")
    
    pending = buffer.get_pending_tasks(limit=100)
    # Check if our tasks are in there
    my_tasks = [t for t in pending if t['task_type'] == 'lab_analysis' and 'lab_test' in str(t['payload'])]
    
    if len(my_tasks) >= tasks_to_push:
        logger.info(f"✅ SUCCESS: Found {len(my_tasks)} tasks buffered in SQLite.")
    else:
        logger.error(f"❌ FAILURE: Only found {len(my_tasks)} tasks in buffer.")

if __name__ == "__main__":
    test_resilience()
