import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from core.context_sentinel import ContextSentinel, create_sentinel

class TestContextSentinel:
    @pytest.fixture
    def temp_storage(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_add_memory_basic(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.add_memory("test_key", {"value": 42})
        result = sentinel.query_memory("test_key")
        assert result is not None
        assert result["value"] == 42

    def test_memory_persists_between_instances(self, temp_storage):
        sentinel1 = ContextSentinel(temp_storage)
        sentinel1.add_memory("shared_key", {"data": "important"})
        
        sentinel2 = ContextSentinel(temp_storage)
        result = sentinel2.query_memory("shared_key")
        assert result is not None
        assert result["data"] == "important"

    def test_action_history_persists(self, temp_storage):
        sentinel1 = ContextSentinel(temp_storage)
        sentinel1.add_action("Agent1", "ACTION1")
        
        sentinel2 = ContextSentinel(temp_storage)
        history = sentinel2.get_action_history()
        assert len(history) == 1
        assert history[0]["action_type"] == "ACTION1"

    def test_two_executions_scenario(self, temp_storage):
        # Execution 1
        sentinel1 = ContextSentinel(temp_storage)
        sentinel1.add_memory("exec1", {"status": "ok"})
        sentinel1.add_action("Agent", "START")
        
        # Execution 2
        sentinel2 = ContextSentinel(temp_storage)
        assert sentinel2.query_memory("exec1")["status"] == "ok"
        sentinel2.add_action("Agent", "CONTINUE")
        
        # Verification
        sentinel3 = ContextSentinel(temp_storage)
        history = sentinel3.get_action_history()
        assert len(history) == 3 # MEMORY_ADD + START + CONTINUE
        assert history[1]["action_type"] == "START"
        assert history[2]["action_type"] == "CONTINUE"

    def test_corrupted_json_handling(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.add_memory("good", {"val": 1})
        
        state_file = temp_storage / "current_state.json"
        state_file.write_text("{ invalid json")
        
        sentinel2 = ContextSentinel(temp_storage)
        assert sentinel2.query_memory("good") is None
        sentinel2.add_memory("new", {"val": 2})
        assert sentinel2.query_memory("new")["val"] == 2

    def test_statistics(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.add_memory("k1", {})
        sentinel.add_action("A1", "T1")
        sentinel.add_action("A1", "T2")
        sentinel.add_action("A2", "T1")
        
        stats = sentinel.get_statistics()
        assert stats["total_actions"] == 4 # 1 MEMORY_ADD + 3 actions
        assert stats["actions_by_agent"]["A1"] == 2
        assert stats["actions_by_type"]["T1"] == 2
        assert stats["memory_keys_count"] == 1

    def test_get_memory_keys(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.add_memory("a", {})
        sentinel.add_memory("b", {})
        keys = sentinel.get_memory_keys()
        assert "a" in keys
        assert "b" in keys

    def test_create_sentinel_factory(self, temp_storage):
        sentinel = create_sentinel(str(temp_storage))
        assert sentinel.storage_root == temp_storage

    def test_corrupted_jsonl_line_skipping(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        with open(sentinel.action_history_file, "w") as f:
            f.write('{"valid": "json"}\n')
            f.write('invalid json\n')
            f.write('{"valid": "again"}\n')
        
        history = sentinel.get_action_history()
        assert len(history) == 2

    def test_load_state_empty_file(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.state_file.write_text("")
        assert sentinel._load_state() == {}

    def test_error_handling_add_memory(self, temp_storage, monkeypatch):
        sentinel = ContextSentinel(temp_storage)
        from pathlib import Path
        def mock_write_text(*args, **kwargs):
            raise Exception("Write error")
        monkeypatch.setattr(Path, "write_text", mock_write_text)
        with pytest.raises(Exception, match="Write error"):
            sentinel.add_memory("fail", {})

    def test_error_handling_query_memory(self, temp_storage, monkeypatch):
        sentinel = ContextSentinel(temp_storage)
        def mock_load_state(*args, **kwargs):
            raise Exception("Read error")
        monkeypatch.setattr(sentinel, "_load_state", mock_load_state)
        assert sentinel.query_memory("any") is None

    def test_error_handling_get_memory_keys(self, temp_storage, monkeypatch):
        sentinel = ContextSentinel(temp_storage)
        def mock_load_state(*args, **kwargs):
            raise Exception("Read error")
        monkeypatch.setattr(sentinel, "_load_state", mock_load_state)
        assert sentinel.get_memory_keys() == []

    def test_error_handling_add_action(self, temp_storage, monkeypatch):
        sentinel = ContextSentinel(temp_storage)
        import builtins
        real_open = builtins.open
        def mock_open(file, *args, **kwargs):
            if str(file) == str(sentinel.action_history_file):
                raise Exception("Open error")
            return real_open(file, *args, **kwargs)
        monkeypatch.setattr(builtins, "open", mock_open)
        with pytest.raises(Exception, match="Open error"):
            sentinel.add_action("Agent", "FAIL")

    def test_error_handling_get_action_history(self, temp_storage, monkeypatch):
        sentinel = ContextSentinel(temp_storage)
        import builtins
        real_open = builtins.open
        def mock_open(file, *args, **kwargs):
            if str(file) == str(sentinel.action_history_file):
                raise Exception("Open error")
            return real_open(file, *args, **kwargs)
        monkeypatch.setattr(builtins, "open", mock_open)
        assert sentinel.get_action_history() == []

    def test_load_state_corrupted_json(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.state_file.write_text("{ corrupted")
        assert sentinel._load_state() == {}

    def test_get_action_history_corrupted_json(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        sentinel.action_history_file.write_text('{"valid": "json"}\n{corrupted}\n{"valid": "again"}')
        history = sentinel.get_action_history()
        assert len(history) == 2

    def test_mkdir_error(self, temp_storage, monkeypatch):
        from pathlib import Path
        def mock_mkdir(*args, **kwargs):
            raise Exception("Mkdir error")
        monkeypatch.setattr(Path, "mkdir", mock_mkdir)
        with pytest.raises(Exception, match="Mkdir error"):
            ContextSentinel(temp_storage / "new_dir")

    def test_get_statistics_empty(self, temp_storage):
        sentinel = ContextSentinel(temp_storage)
        stats = sentinel.get_statistics()
        assert stats["total_actions"] == 0
        assert stats["memory_keys_count"] == 0
