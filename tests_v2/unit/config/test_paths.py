"""Unit tests for cgalpha_v2.config.paths."""

from __future__ import annotations

from pathlib import Path

from cgalpha_v2.config import ProjectPaths


def test_project_paths_root_is_resolved(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path / ".." / tmp_path.name)
    assert paths.root == tmp_path.resolve()


def test_project_paths_ensure_directories_creates_structure(tmp_path: Path) -> None:
    root = tmp_path / "project_root"
    paths = ProjectPaths(root=root)
    paths.ensure_directories()

    assert paths.operational_dir.exists()
    assert paths.evolutionary_dir.exists()
    assert paths.causal_reports_dir.exists()
    assert paths.temporary_dir.exists()
    assert paths.ast_backups_dir.exists()
    assert paths.config_dir.exists()
    assert paths.config_backups_dir.exists()
    assert paths.models_dir.exists()
    assert paths.testing_dir.exists()
    assert paths.generated_tests_dir.exists()


def test_project_paths_all_paths_returns_path_values(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    all_paths = paths.all_paths()

    assert "config_file" in all_paths
    assert "bridge_file" in all_paths
    assert all(isinstance(value, Path) for value in all_paths.values())


def test_project_paths_key_files_are_under_root(tmp_path: Path) -> None:
    paths = ProjectPaths(root=tmp_path)
    assert str(paths.config_file).startswith(str(paths.root))
    assert str(paths.bridge_file).startswith(str(paths.root))
    assert str(paths.task_buffer_db).startswith(str(paths.root))
