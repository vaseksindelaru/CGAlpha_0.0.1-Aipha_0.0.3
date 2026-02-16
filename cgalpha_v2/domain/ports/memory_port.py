"""
cgalpha.domain.ports.memory_port — Ports for persistent memory (logging and state).

These ports abstract the ContextSentinel's two responsibilities:
1. ActionLogger — append-only event log (JSONL)
2. StateStore   — mutable key-value state (JSON files)

Implementations live in cgalpha.infrastructure.persistence.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ActionLogger(Protocol):
    """
    Port for append-only action logging.

    The action log is an immutable audit trail of everything the system
    does.  It never deletes or modifies entries.
    """

    def log_action(
        self,
        agent: str,
        action_type: str,
        *,
        details: Optional[dict[str, Any]] = None,
        proposal_id: Optional[str] = None,
    ) -> None:
        """
        Append an action entry to the log.

        Args:
            agent:       Component name that performed the action.
            action_type: Classification of the action (e.g. 'CYCLE_COMPLETED').
            details:     Optional structured context.
            proposal_id: Optional proposal this action relates to.
        """
        ...

    def get_history(
        self,
        limit: Optional[int] = None,
        action_type: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Read recent actions from the log.

        Args:
            limit:       Maximum number of entries to return.
            action_type: Filter by action type.

        Returns:
            List of action entries (dicts), most recent first.
        """
        ...


@runtime_checkable
class StateStore(Protocol):
    """
    Port for mutable key-value state persistence.

    Unlike ActionLogger (append-only), StateStore allows reading and
    overwriting state.  Used for current_state, pending_proposals, etc.
    """

    def get(self, key: str) -> Optional[dict[str, Any]]:
        """
        Read state for a given key.

        Args:
            key: State identifier (e.g. 'current_state', 'pending_proposals').

        Returns:
            The stored state dict, or None if not found.
        """
        ...

    def set(self, key: str, value: dict[str, Any]) -> None:
        """
        Write state for a given key (overwrites previous value).

        Args:
            key:   State identifier.
            value: State data to persist.
        """
        ...

    def delete(self, key: str) -> bool:
        """
        Delete state for a given key.

        Args:
            key: State identifier.

        Returns:
            True if the key existed and was deleted.
        """
        ...
