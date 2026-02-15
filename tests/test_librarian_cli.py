import json
from pathlib import Path

from click.testing import CliRunner

from aiphalab.cli_v2 import cli
import aiphalab.commands.librarian as librarian


def test_ask_command_exists_in_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ask" in result.output
    assert "ask-health" in result.output
    assert "ask-requirements" in result.output
    assert "ask-setup" in result.output


def test_ask_command_success_with_mocked_ollama(tmp_path, monkeypatch):
    monkeypatch.setattr(librarian, "_ollama_alive", lambda host, timeout_s=4: True)
    monkeypatch.setattr(
        librarian,
        "_query_ollama",
        lambda prompt, model, host, timeout_s=120, **kwargs: {
            "response": "Respuesta local de prueba",
            "model": model,
            "eval_count": 12,
            "eval_duration": 12345,
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ask",
            "¿Qué hace el orchestrator?",
            "--working-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Respuesta local de prueba" in result.output

    history_path = tmp_path / "aipha_memory" / "operational" / "librarian_history.jsonl"
    assert history_path.exists()
    rows = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["question"] == "¿Qué hace el orchestrator?"
    assert rows[0]["profile"] == "mentor"
    assert rows[0]["response_format"] == "markdown"


def test_ask_requirements_success_with_mocked_ollama(tmp_path, monkeypatch):
    monkeypatch.setattr(librarian, "_ollama_alive", lambda host, timeout_s=4: True)
    monkeypatch.setattr(
        librarian,
        "_query_ollama",
        lambda prompt, model, host, timeout_s=120, **kwargs: {
            "response": '{"problem_statement":"x","scope_in":[],"scope_out":[]}',
            "model": model,
            "eval_count": 40,
            "eval_duration": 12345,
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ask-requirements",
            "Necesito un plan de requisitos",
            "--working-dir",
            str(tmp_path),
            "--response-format",
            "json",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "problem_statement" in result.output

    history_path = tmp_path / "aipha_memory" / "operational" / "librarian_history.jsonl"
    assert history_path.exists()
    rows = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 1
    assert rows[0]["question"] == "Necesito un plan de requisitos"
    assert rows[0]["profile"] == "requirements"
    assert rows[0]["response_format"] == "json"


def test_ask_command_when_ollama_down(monkeypatch):
    monkeypatch.setattr(librarian, "_ollama_alive", lambda host, timeout_s=4: False)
    runner = CliRunner()
    result = runner.invoke(cli, ["ask", "test"])
    assert result.exit_code != 0
    assert "Ollama no responde" in result.output


def test_ask_health_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(librarian, "_ollama_alive", lambda host, timeout_s=4: True)
    monkeypatch.setattr(librarian, "_list_ollama_models", lambda host, timeout_s=4: ["qwen2.5:1.5b"])

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "ask-health",
            "--working-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Librarian local operativo" in result.output


def test_ask_health_fails_when_ollama_down(monkeypatch):
    monkeypatch.setattr(librarian, "_ollama_alive", lambda host, timeout_s=4: False)
    runner = CliRunner()
    result = runner.invoke(cli, ["ask-health"])
    assert result.exit_code != 0
    assert "Ollama no responde" in result.output


def test_ask_setup_saves_defaults(monkeypatch):
    monkeypatch.setattr(librarian, "_ollama_alive", lambda host, timeout_s=4: True)
    monkeypatch.setattr(
        librarian,
        "_list_ollama_models",
        lambda host, timeout_s=4: ["qwen2.5:1.5b", "deepseek-coder:1.3b"],
    )

    runner = CliRunner()
    with runner.isolated_filesystem():
        user_input = "\n".join(
            [
                "deepseek-coder:1.3b",
                "requirements",
                "json",
                "2",
                "500",
                "900",
                "260",
                "0.1",
                "1536",
            ]
        ) + "\n"
        result = runner.invoke(cli, ["ask-setup", "--working-dir", "."], input=user_input)
        assert result.exit_code == 0, result.output
        assert "Configuración guardada" in result.output

        cfg_file = Path("memory/aipha_config.json")
        assert cfg_file.exists()
        cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert cfg["Librarian"]["model"] == "deepseek-coder:1.3b"
        assert cfg["Librarian"]["profile"] == "requirements"
