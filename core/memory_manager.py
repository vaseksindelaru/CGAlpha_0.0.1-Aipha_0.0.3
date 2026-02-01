"""
core/memory_manager.py - Compatibility wrapper for ContextSentinel
FASE 1 - AIPHA 0.0.2
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from core.context_sentinel import ContextSentinel

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    Wrapper for ContextSentinel to provide record_metric functionality.
    """
    def __init__(self, storage_root: Optional[Path] = None):
        # Use the same default as ContextSentinel
        if storage_root is None:
            storage_root = Path.cwd() / "memory"
        self.sentinel = ContextSentinel(storage_root=storage_root)

    def record_metric(self, component: str, metric_name: str, value: Any, metadata: Optional[Dict] = None):
        """
        Records a metric in the system memory.
        """
        # Get current metrics or initialize
        metrics = self.sentinel.query_memory("trading_metrics") or {}
        
        # Update specific metric
        # Note: This is a simplified implementation for compatibility
        metrics[metric_name] = value
        if metadata:
            metrics[f"{metric_name}_metadata"] = metadata
            
        # Save back to sentinel
        self.sentinel.add_memory("trading_metrics", metrics)
        
        # Also log as an action for history
        self.sentinel.add_action(
            agent=component,
            action_type="METRIC_RECORDED",
            details={
                "metric": metric_name,
                "value": value,
                "metadata": metadata
            }
        )
        logger.info(f"📊 Metric recorded: {component}.{metric_name} = {value}")

    def query_memory(self, key: str) -> Optional[Dict[str, Any]]:
        return self.sentinel.query_memory(key)

    def add_memory(self, key: str, value: Dict[str, Any]):
        self.sentinel.add_memory(key, value)
