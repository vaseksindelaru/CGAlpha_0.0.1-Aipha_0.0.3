"""
cgalpha.config.paths — ProjectPaths value object.

Centralizes ALL file system paths used by the system.  Every module
that needs a path should receive it via ProjectPaths instead of
constructing paths with hardcoded strings.

Design decisions (ADR-005):
- All paths are computed lazily from a single `root` directory.
- Directories are NOT created automatically — that's the caller's job.
- The class is a frozen dataclass so it can be safely shared across threads.
- For testing, pass a temp directory as root and all paths adjust automatically.

Usage:
    paths = ProjectPaths(root=Path("/home/user/cgalpha"))
    paths.bridge_file           # /home/user/cgalpha/data/memory/evolutionary/bridge.jsonl
    paths.config_file           # /home/user/cgalpha/aipha_config.json
    paths.ensure_directories()  # creates all directories
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """
    Centralized path registry for the CGAlpha project.

    All paths are computed relative to `root`.  No path is hardcoded
    anywhere else in the system.

    Attributes:
        root: Project root directory (absolute path).
    """

    root: Path

    def __post_init__(self) -> None:
        # Resolve to absolute path for consistency
        object.__setattr__(self, "root", self.root.resolve())

    # ── Memory: Operational ──────────────────────────────────────────────

    @property
    def memory_dir(self) -> Path:
        """Root of the memory hierarchy."""
        return self.root / "aipha_memory"

    @property
    def operational_dir(self) -> Path:
        """Runtime operational data (logs, state, health)."""
        return self.memory_dir / "operational"

    @property
    def action_log_file(self) -> Path:
        """Append-only action log (JSONL)."""
        return self.operational_dir / "action_log.jsonl"

    @property
    def current_state_file(self) -> Path:
        """Mutable current state file."""
        return self.operational_dir / "current_state.json"

    @property
    def health_log_file(self) -> Path:
        """Health event log (JSONL)."""
        return self.operational_dir / "health_events.jsonl"

    @property
    def performance_log_file(self) -> Path:
        """Performance metrics log (JSONL)."""
        return self.operational_dir / "performance.jsonl"

    @property
    def order_book_features_file(self) -> Path:
        """Order book feature data for Deep Causal v0.3."""
        return self.operational_dir / "order_book_features.jsonl"

    # ── Memory: Evolutionary ─────────────────────────────────────────────

    @property
    def evolutionary_dir(self) -> Path:
        """Evolutionary learning data (bridge, causal reports)."""
        return self.memory_dir / "evolutionary"

    @property
    def bridge_file(self) -> Path:
        """The evolutionary bridge (JSONL) — links trading to causal analysis."""
        return self.evolutionary_dir / "bridge.jsonl"

    @property
    def causal_reports_dir(self) -> Path:
        """Directory for causal analysis reports."""
        return self.evolutionary_dir / "causal_reports"

    @property
    def proposals_file(self) -> Path:
        """Pending proposals store."""
        return self.evolutionary_dir / "pending_proposals.json"

    # ── Memory: Temporary ────────────────────────────────────────────────

    @property
    def temporary_dir(self) -> Path:
        """Temporary files (buffers, backups) — safe to clean."""
        return self.memory_dir / "temporary"

    @property
    def task_buffer_db(self) -> Path:
        """SQLite task buffer (Redis fallback)."""
        return self.temporary_dir / "task_buffer.db"

    @property
    def ast_backups_dir(self) -> Path:
        """AST modifier backup directory."""
        return self.temporary_dir / "ast_backups"

    @property
    def quarantine_file(self) -> Path:
        """Quarantined parameters log (JSONL)."""
        return self.temporary_dir / "quarantine.jsonl"

    # ── Configuration ────────────────────────────────────────────────────

    @property
    def config_dir(self) -> Path:
        """Configuration directory (backups, snapshots)."""
        return self.memory_dir / "config"

    @property
    def config_file(self) -> Path:
        """Main system configuration file."""
        return self.root / "aipha_config.json"

    @property
    def config_backups_dir(self) -> Path:
        """Configuration backup directory."""
        return self.config_dir / "backups"

    # ── Oracle / Models ──────────────────────────────────────────────────

    @property
    def models_dir(self) -> Path:
        """Serialized ML model directory."""
        return self.root / "oracle" / "models"

    @property
    def default_model_file(self) -> Path:
        """Default Oracle model file."""
        return self.models_dir / "proof_oracle.joblib"

    # ── Testing ──────────────────────────────────────────────────────────

    @property
    def testing_dir(self) -> Path:
        """Test artifact directory."""
        return self.memory_dir / "testing"

    @property
    def generated_tests_dir(self) -> Path:
        """Directory for Code Craft Sage generated tests."""
        return self.testing_dir / "generated"

    # ── Lifecycle log ────────────────────────────────────────────────────

    @property
    def lifecycle_log_file(self) -> Path:
        """Main lifecycle log file."""
        return self.memory_dir / "aipha_lifecycle.log"

    # ── Convenience methods ──────────────────────────────────────────────

    def ensure_directories(self) -> None:
        """
        Create all expected directories if they don't exist.

        This is called once at system startup (in bootstrap.py).
        It is NOT called automatically — explicit over implicit.
        """
        directories = [
            self.operational_dir,
            self.evolutionary_dir,
            self.causal_reports_dir,
            self.temporary_dir,
            self.ast_backups_dir,
            self.config_dir,
            self.config_backups_dir,
            self.models_dir,
            self.testing_dir,
            self.generated_tests_dir,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def all_paths(self) -> dict[str, Path]:
        """
        Return a dictionary of all named paths for debugging/logging.

        Returns:
            Dict mapping path names to Path objects.
        """
        return {
            name: getattr(self, name)
            for name in dir(self)
            if not name.startswith("_")
            and isinstance(getattr(type(self), name, None), property)
            and isinstance(getattr(self, name), Path)
        }
