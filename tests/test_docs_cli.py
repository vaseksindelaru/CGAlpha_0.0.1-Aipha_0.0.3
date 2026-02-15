from pathlib import Path

from click.testing import CliRunner

from aiphalab.cli_v2 import cli


def _seed_docs(root: Path):
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "DOCS_INDEX.md").write_text("# Index\n", encoding="utf-8")
    (root / "docs" / "CGALPHA_SYSTEM_GUIDE.md").write_text("# Guide\nline2\n", encoding="utf-8")
    (root / "docs" / "LLM_LOCAL_OPERATIONS.md").write_text("# LLM\n", encoding="utf-8")
    (root / "UNIFIED_CONSTITUTION_v0.0.3.md").write_text("# Constitution\n", encoding="utf-8")
    (root / "bible" / "codecraft_sage").mkdir(parents=True, exist_ok=True)
    (root / "bible" / "codecraft_sage" / "phase7_ghost_architect.md").write_text("# P7\n", encoding="utf-8")
    (root / "bible" / "codecraft_sage" / "phase8_deep_causal_v03.md").write_text("# P8\n", encoding="utf-8")


def test_docs_group_exists():
    runner = CliRunner()
    result = runner.invoke(cli, ["docs", "--help"])
    assert result.exit_code == 0, result.output
    assert "list" in result.output
    assert "show" in result.output
    assert "path" in result.output

    result_alias = runner.invoke(cli, ["d", "--help"])
    assert result_alias.exit_code == 0, result_alias.output
    assert "list" in result_alias.output


def test_docs_list_show_path(tmp_path: Path):
    _seed_docs(tmp_path)
    runner = CliRunner()

    result_list = runner.invoke(cli, ["docs", "list", "--working-dir", str(tmp_path)])
    assert result_list.exit_code == 0, result_list.output
    assert "CGAlpha Docs" in result_list.output

    result_show = runner.invoke(
        cli,
        ["docs", "show", "guide", "--working-dir", str(tmp_path), "--lines", "1"],
    )
    assert result_show.exit_code == 0, result_show.output
    assert "# Guide" in result_show.output
    assert "line2" not in result_show.output

    result_path = runner.invoke(cli, ["docs", "path", "index", "--working-dir", str(tmp_path)])
    assert result_path.exit_code == 0, result_path.output
    assert str(tmp_path / "docs" / "DOCS_INDEX.md") in result_path.output

    result_alias_show = runner.invoke(
        cli,
        ["d", "show", "guide", "--working-dir", str(tmp_path), "--lines", "1"],
    )
    assert result_alias_show.exit_code == 0, result_alias_show.output
    assert "# Guide" in result_alias_show.output
