"""
aiphalab/commands/librarian.py - Local Librarian command.

Provides `cgalpha ask` to query a local Ollama model with project-aware context.
"""

from __future__ import annotations

import json
import socket
from http.client import RemoteDisconnected
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from urllib import error, request

import click

from .base import BaseCommand


DEFAULT_MODEL = "qwen2.5:1.5b"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


class LibrarianCommand(BaseCommand):
    """Simple local mentoring assistant backed by Ollama."""

    def __init__(self, working_dir: str = ".", host: str = DEFAULT_OLLAMA_HOST):
        super().__init__()
        self.working_dir = Path(working_dir).resolve()
        self.host = host.rstrip("/")
        self.history_path = self.working_dir / "aipha_memory" / "operational" / "librarian_history.jsonl"

    def build_context(self, question: str, max_files: int = 6, max_chars: int = 1200) -> str:
        """Collect high-level context snippets from key project files."""
        candidates: List[Path] = [
            self.working_dir / "README.md",
            self.working_dir / "UNIFIED_CONSTITUTION_v0.0.3.md",
            self.working_dir / "aiphalab" / "cli_v2.py",
            self.working_dir / "cgalpha" / "orchestrator.py",
            self.working_dir / "cgalpha" / "ghost_architect" / "simple_causal_analyzer.py",
            self.working_dir / "cgalpha" / "codecraft" / "orchestrator.py",
            self.working_dir / "bible" / "codecraft_sage" / "phase7_ghost_architect.md",
        ]

        lowered = question.lower()
        if "proposal" in lowered:
            candidates.insert(0, self.working_dir / "cgalpha" / "codecraft" / "proposal_generator.py")
        if "test" in lowered:
            candidates.insert(0, self.working_dir / "tests" / "test_proposal_generator.py")

        snippets: List[str] = []
        seen = set()
        for path in candidates:
            if len(snippets) >= max_files:
                break
            if path in seen or not path.exists() or not path.is_file():
                continue
            seen.add(path)
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            excerpt = content[:max_chars].strip()
            if not excerpt:
                continue
            rel = path.relative_to(self.working_dir)
            snippets.append(f"[{rel}]\n{excerpt}")

        architecture_hint = (
            "CGAlpha overview: CLI layer (aiphalab) -> orchestrator -> codecraft/ghost_architect/nexus. "
            "Use simple, robust guidance. Avoid proposing non-approved new layers."
        )
        return architecture_hint + "\n\n" + "\n\n".join(snippets)

    def save_history(self, question: str, answer: str, model: str):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "librarian_local",
            "model": model,
            "question": question,
            "answer": answer,
        }
        with self.history_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _ollama_alive(host: str, timeout_s: int = 4) -> bool:
    url = f"{host.rstrip('/')}/api/tags"
    req = request.Request(url=url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            return int(getattr(resp, "status", 200)) < 400
    except Exception:
        return False


def _list_ollama_models(host: str, timeout_s: int = 4) -> List[str]:
    url = f"{host.rstrip('/')}/api/tags"
    req = request.Request(url=url, method="GET")
    try:
        with request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        data = json.loads(raw)
    except Exception:
        return []
    models = data.get("models", [])
    names: List[str] = []
    for row in models:
        name = row.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names


def _query_ollama(
    prompt: str,
    model: str,
    host: str,
    timeout_s: int = 300,
    num_predict: int = 180,
    temperature: float = 0.2,
    num_ctx: int = 2048,
) -> Dict[str, Any]:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": temperature,
            "num_ctx": num_ctx,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url=f"{host.rstrip('/')}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="ignore")
    parsed = json.loads(raw)
    return {
        "response": str(parsed.get("response", "")).strip(),
        "eval_count": parsed.get("eval_count"),
        "eval_duration": parsed.get("eval_duration"),
        "model": parsed.get("model", model),
    }


def _build_mentor_prompt(question: str, context: str) -> str:
    return f"""
Eres "Librarian Local", mentor tecnico senior para CGAlpha.

Reglas:
1) Explica arquitectura y flujo de trabajo en alto nivel.
2) No propongas refactor total ni capas innecesarias.
3) Si surge "añadir función X", responde: "Eso no aprobado. Nos enfocamos en la simplicidad y robustez. El sistema es difícil de mantener. No añadamos capas innecesarias".
4) Prioriza claridad didáctica con pasos concretos.
5) Si falta contexto, dilo explícitamente y pide el archivo exacto.

Contexto del proyecto:
{context}

Pregunta del usuario:
{question}
""".strip()


@click.command(name="ask")
@click.argument("question", required=False)
@click.option("--working-dir", type=str, default=".", help="Raíz del proyecto")
@click.option("--model", type=str, default=DEFAULT_MODEL, help="Modelo local Ollama")
@click.option("--host", type=str, default=DEFAULT_OLLAMA_HOST, help="Host Ollama")
@click.option("--no-remote/--allow-remote", default=True, show_default=True, help="Mantener operación 100% local")
@click.option("--max-files", type=int, default=2, show_default=True, help="Cantidad de archivos de contexto")
@click.option("--max-chars", type=int, default=450, show_default=True, help="Máximo chars por archivo")
@click.option("--timeout", "timeout_s", type=int, default=300, show_default=True, help="Timeout en segundos")
@click.option("--num-predict", type=int, default=120, show_default=True, help="Tokens máximos a generar")
@click.option("--temperature", type=float, default=0.2, show_default=True, help="Creatividad del modelo")
@click.option("--num-ctx", type=int, default=1536, show_default=True, help="Ventana de contexto")
def ask_command(
    question: Optional[str],
    working_dir: str,
    model: str,
    host: str,
    no_remote: bool,
    max_files: int,
    max_chars: int,
    timeout_s: int,
    num_predict: int,
    temperature: float,
    num_ctx: int,
):
    """
    📚 Librarian Local: mentor técnico local para entender CGAlpha.

    Uso:
      cgalpha ask "¿Cómo fluye auto-analyze?"
      cgalpha ask
    """
    cmd = LibrarianCommand(working_dir=working_dir, host=host)

    if not no_remote:
        cmd.print_warning("Modo remoto no soportado en Librarian local; continuando en modo local.")

    if not _ollama_alive(host):
        cmd.print_error(
            "Ollama no responde en 127.0.0.1:11434. "
            "Inicia con: systemctl --user start ollama-local.service"
        )
        raise click.Abort()

    def run_once(q: str):
        q = (q or "").strip()
        if not q:
            return
        context = cmd.build_context(q, max_files=max_files, max_chars=max_chars)
        prompt = _build_mentor_prompt(q, context)
        try:
            result = _query_ollama(
                prompt=prompt,
                model=model,
                host=host,
                timeout_s=timeout_s,
                num_predict=num_predict,
                temperature=temperature,
                num_ctx=num_ctx,
            )
        except error.URLError as exc:
            cmd.print_error(f"No se pudo consultar Ollama: {exc}")
            raise click.Abort()
        except (TimeoutError, socket.timeout):
            cmd.print_error(
                "Timeout consultando el modelo local. "
                "Prueba: --max-files 2 --max-chars 400 --num-predict 120 --timeout 600"
            )
            raise click.Abort()
        except (RemoteDisconnected, ConnectionResetError):
            cmd.print_error(
                "Ollama cerró la conexión durante la respuesta. "
                "Reinicia servicio: systemctl --user restart ollama-local.service"
            )
            raise click.Abort()
        except json.JSONDecodeError:
            cmd.print_error("Respuesta inválida del modelo local.")
            raise click.Abort()

        answer = result.get("response") or "(Sin respuesta)"
        cmd.print(f"\n[bold cyan]Librarian ({result.get('model', model)}):[/bold cyan]\n{answer}\n")
        cmd.save_history(q, answer, str(result.get("model", model)))

    if question:
        run_once(question)
        return

    cmd.print("[bold]Modo interactivo Librarian[/bold] (escribe 'exit' para salir)")
    while True:
        try:
            q = input("ask> ").strip()
        except (EOFError, KeyboardInterrupt):
            cmd.print("\nSaliendo.")
            break
        if q.lower() in {"exit", "quit", "q"}:
            break
        run_once(q)


@click.command(name="ask-health")
@click.option("--working-dir", type=str, default=".", help="Raíz del proyecto")
@click.option("--model", type=str, default=DEFAULT_MODEL, help="Modelo esperado")
@click.option("--host", type=str, default=DEFAULT_OLLAMA_HOST, help="Host Ollama")
@click.option("--no-remote/--allow-remote", default=True, show_default=True, help="Mantener operación 100% local")
@click.option("--smoke", is_flag=True, default=False, help="Ejecuta una consulta corta de validación")
@click.option("--smoke-timeout", type=int, default=60, show_default=True, help="Timeout de smoke test (seg)")
def ask_health_command(
    working_dir: str,
    model: str,
    host: str,
    no_remote: bool,
    smoke: bool,
    smoke_timeout: int,
):
    """🩺 Verificación rápida de salud del Librarian local."""
    cmd = LibrarianCommand(working_dir=working_dir, host=host)
    failures: List[str] = []

    if not no_remote:
        cmd.print_warning("Modo remoto no soportado; health se ejecuta local-only.")

    alive = _ollama_alive(host)
    models = _list_ollama_models(host) if alive else []
    model_found = model in models

    history_lines = 0
    if cmd.history_path.exists():
        try:
            with cmd.history_path.open("r", encoding="utf-8") as handle:
                history_lines = sum(1 for _ in handle)
        except OSError:
            history_lines = 0

    cmd.print("[bold]Librarian Local Health[/bold]")
    cmd.print(f"- ollama_host: {host}")
    cmd.print(f"- ollama_status: {'up' if alive else 'down'}")
    cmd.print(f"- model_expected: {model}")
    cmd.print(f"- model_found: {'yes' if model_found else 'no'}")
    cmd.print(f"- models_available: {len(models)}")
    cmd.print(f"- history_file: {cmd.history_path}")
    cmd.print(f"- history_entries: {history_lines}")

    if not alive:
        failures.append("Ollama no responde.")
    if alive and not model_found:
        failures.append(f"Modelo no encontrado: {model}.")

    if smoke and alive and model_found:
        t0 = time.perf_counter()
        try:
            _query_ollama(
                prompt="Responde solo: OK",
                model=model,
                host=host,
                timeout_s=smoke_timeout,
                num_predict=8,
                temperature=0.0,
                num_ctx=512,
            )
            elapsed = time.perf_counter() - t0
            cmd.print(f"- smoke_test: ok ({elapsed:.2f}s)")
        except Exception as exc:  # pragma: no cover - exact exception varies by host load
            failures.append(f"Smoke test falló: {exc}")
            cmd.print(f"- smoke_test: fail ({exc})")

    if failures:
        for item in failures:
            cmd.print_error(item)
        raise click.Abort()

    cmd.print_success("Librarian local operativo.")
