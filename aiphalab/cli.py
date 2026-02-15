"""
Backward-compatible CLI entrypoint.

Legacy tests and scripts import `aiphalab.cli`. The active implementation
is `aiphalab.cli_v2`, so this module re-exports the current `cli` object.
"""

from .cli_v2 import cli

__all__ = ["cli"]
