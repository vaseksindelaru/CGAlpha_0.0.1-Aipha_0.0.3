import pytest
import json
import time
from unittest.mock import MagicMock, patch
from cgalpha.nexus.redis_client import RedisClient
from cgalpha.nexus.ops import CGAOps

@pytest.fixture
def mock_redis():
    with patch('redis.Redis') as mock:
        client = mock.return_value
        client.ping.return_value = True
        yield client

def test_connection_success(mock_redis):
    client = RedisClient()
    assert client.is_connected() is True
    mock_redis.ping.assert_called()

from redis.exceptions import ConnectionError

def test_connection_failure():
    with patch('redis.ConnectionPool', side_effect=ConnectionError("Connection refused")):
        client = RedisClient()
        assert client.is_connected() is False

def test_cache_system_state(mock_redis):
    client = RedisClient()
    data = {"status": "ok", "value": 123}
    
    # Test Set
    client.cache_system_state("test_key", data)
    mock_redis.setex.assert_called_with(
        "cgalpha:state:test_key", 
        300, 
        json.dumps(data)
    )
    
    # Test Get
    mock_redis.get.return_value = json.dumps(data)
    result = client.get_system_state("test_key")
    assert result == data

def test_queue_operations(mock_redis):
    client = RedisClient()
    item = {"task": "analyze", "id": 1}
    
    # Test Push (RPUSH)
    client.push_item("test_queue", item)
    mock_redis.rpush.assert_called_with(
        "cgalpha:queue:test_queue", 
        json.dumps(item)
    )
    
    # Test Pop (BLPOP)
    mock_redis.blpop.return_value = (b"key", json.dumps(item).encode())
    result = client.pop_item("test_queue")
    assert result == item

def test_distributed_lock(mock_redis):
    client = RedisClient()
    resource = "critical_resource"
    
    # Test Acquire
    mock_redis.set.return_value = True
    assert client.acquire_lock(resource) is True
    mock_redis.set.assert_called_with(
        "cgalpha:lock:critical_resource", 
        "LOCKED", 
        nx=True, 
        ex=30
    )
    
    # Test Release
    client.release_lock(resource)
    mock_redis.delete.assert_called_with("cgalpha:lock:critical_resource")

def test_fallback_behavior():
    # Simulate Redis unavailable
    with patch('redis.ConnectionPool', side_effect=ConnectionError("Down")):
        ops = CGAOps()
        assert ops.redis is not None
        assert ops.redis.is_connected() is False
        
        # Test Persistent Buffer Fallback
        # Should return True because it's buffered to SQLite
        assert ops.push_lab_task("lab1", {"test": "data"}) is True
        
        # Verify it's in the buffer
        pending = ops.task_buffer.get_pending_tasks()
        assert len(pending) > 0
        assert pending[-1]['payload']['payload'] == {"test": "data"}
        
        # Get tasks from Redis should be empty (since Redis is down)
        assert ops.get_pending_tasks() == []
        
        # Lock -> False (Fail safe when Redis client exists but is down)
        assert ops.acquire_resource_lock("res1") is False
