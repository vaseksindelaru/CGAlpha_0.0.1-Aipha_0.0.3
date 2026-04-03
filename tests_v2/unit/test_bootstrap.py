"""Unit tests for cgalpha_v2.bootstrap."""

from __future__ import annotations

from pathlib import Path

from cgalpha_v2.bootstrap import bootstrap
from cgalpha_v2.config import Settings


def test_bootstrap_returns_container_with_expected_objects(tmp_path: Path) -> None:
    settings = Settings(project_root=tmp_path, log_level="DEBUG")
    container = bootstrap(settings=settings)

    assert container.settings is settings
    assert container.paths.root == tmp_path.resolve()


def test_bootstrap_creates_directories(tmp_path: Path) -> None:
    root = tmp_path / "project_a"
    settings = Settings(project_root=root)
    container = bootstrap(settings=settings)

    assert container.paths.memory_dir.exists()
    assert container.paths.evolutionary_dir.exists()
    assert container.paths.temporary_dir.exists()


def test_bootstrap_project_root_argument_overrides_settings(tmp_path: Path) -> None:
    root_a = tmp_path / "root_a"
    root_b = tmp_path / "root_b"
    settings = Settings(project_root=root_a)

    container = bootstrap(settings=settings, project_root=root_b)
    assert container.paths.root == root_b.resolve()
