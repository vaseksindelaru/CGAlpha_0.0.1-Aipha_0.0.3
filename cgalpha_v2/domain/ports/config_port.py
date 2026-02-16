"""
cgalpha.domain.ports.config_port — Ports for configuration access.

Separates reading and writing configuration into two interfaces
(Interface Segregation Principle).  Most consumers only need ConfigReader.

Implementations live in cgalpha.infrastructure.persistence.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ConfigReader(Protocol):
    """
    Port for reading system configuration.

    Provides dot-path access to configuration values
    (e.g. 'Trading.tp_factor' → 2.0).
    """

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Read a configuration value by dot-path.

        Args:
            key_path: Dot-separated path (e.g. 'Trading.tp_factor').
            default:  Value to return if the key is not found.

        Returns:
            The configuration value, or `default` if not found.
        """
        ...

    def get_all(self) -> dict[str, Any]:
        """
        Return the complete configuration as a nested dictionary.

        Returns:
            Full configuration dict.
        """
        ...


@runtime_checkable
class ConfigWriter(Protocol):
    """
    Port for writing system configuration.

    Only the orchestrator and the ActionApplicator should use this port.
    All other components should use ConfigReader (read-only).
    """

    def set(self, key_path: str, value: Any) -> None:
        """
        Write a configuration value by dot-path.

        Persists the change to disk and creates a backup of the
        previous configuration.

        Args:
            key_path: Dot-separated path (e.g. 'Trading.tp_factor').
            value:    New value to set.

        Raises:
            ConfigurationError: If the key path is invalid.
        """
        ...

    def rollback(self) -> bool:
        """
        Revert to the previous configuration backup.

        Returns:
            True if rollback succeeded, False if no backup available.
        """
        ...
