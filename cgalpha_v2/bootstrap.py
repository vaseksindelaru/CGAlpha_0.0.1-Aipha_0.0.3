"""
cgalpha.bootstrap — Composition root for dependency injection.

This is the ONLY place in the system where concrete implementations
are instantiated and wired together.  All other modules depend on
abstractions (ports), never on concrete classes.

Design decisions (ADR-004):
- No global singletons — every instance is created here and passed explicitly.
- The bootstrap function returns a Container dataclass with all wired dependencies.
- For testing, callers can override specific dependencies.
- This module is intentionally thin in Phase 2.1 — it grows as we migrate contexts.

Usage:
    from cgalpha_v2.bootstrap import bootstrap

    container = bootstrap()                           # production defaults
    container = bootstrap(project_root=Path("/tmp"))  # for testing
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cgalpha_v2.config.paths import ProjectPaths
from cgalpha_v2.config.settings import Settings


@dataclass
class Container:
    """
    Dependency container — holds all wired instances.

    This is NOT frozen because it's mutable during bootstrap (we build
    it incrementally).  However, once bootstrap() returns, callers should
    treat it as read-only.

    Attributes:
        settings:      Application-level settings.
        paths:         Centralized project paths.

    Future attributes (Phase 2.2+):
        market_data_reader:  MarketDataReader implementation.
        bridge_writer:       BridgeWriter implementation.
        predictor:           Predictor implementation.
        action_logger:       ActionLogger implementation.
        state_store:         StateStore implementation.
        llm_provider:        LLMProvider implementation.
        config_reader:       ConfigReader implementation.
        config_writer:       ConfigWriter implementation.
    """

    settings: Settings
    paths: ProjectPaths


def bootstrap(
    *,
    project_root: Optional[Path] = None,
    settings: Optional[Settings] = None,
) -> Container:
    """
    Wire all dependencies and return a Container.

    This is the single entry point for constructing the dependency graph.
    In production, call with no arguments.  For testing, override
    project_root or provide a custom Settings instance.

    Args:
        project_root: Override the project root (defaults to Settings.project_root).
        settings:     Override the entire Settings object.

    Returns:
        Fully wired Container ready for use.
    """
    # 1. Load settings
    if settings is None:
        settings = Settings()

    # 2. Determine project root
    root = project_root or settings.project_root
    root = Path(root).resolve()

    # 3. Create paths
    paths = ProjectPaths(root=root)

    # 4. Ensure directory structure exists
    paths.ensure_directories()

    # 5. Wire container (minimal for Phase 2.1)
    container = Container(
        settings=settings,
        paths=paths,
    )

    return container
