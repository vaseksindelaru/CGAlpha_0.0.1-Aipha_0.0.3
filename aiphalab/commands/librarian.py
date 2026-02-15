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
PROFILE_MENTOR = "mentor"
PROFILE_REQUIREMENTS = "requirements"
DEFAULT_RESPONSE_FORMAT = "markdown"

DEFAULT_RUNTIME_OPTIONS = {
    "model": DEFAULT_MODEL,
    "profile": PROFILE_MENTOR,
    "response_format": DEFAULT_RESPONSE_FORMAT,
    "max_files": 2,
    "max_chars": 450,
    "timeout_s": 300,
    "num_predict": 120,
    "temperature": 0.2,
    "num_ctx": 1536,
}


class LibrarianCommand(BaseCommand):
    """Simple local mentoring assistant backed by Ollama."""

    def __init__(self, working_dir: str = ".", host: str = DEFAULT_OLLAMA_HOST):
        super().__init__()
        self.working_dir = Path(working_dir).resolve()
        self.host = host.rstrip("/")
        self.history_path = self.working_dir / "aipha_memory" / "operational" / "librarian_history.jsonl"

    def _read_librarian_config(self) -> Dict[str, Any]:
        raw = self.config.get("Librarian", {})
        return raw if isinstance(raw, dict) else {}

    def _normalize_profile(self, value: Any, fallback: str = PROFILE_MENTOR) -> str:
        if isinstance(value, str) and value in {PROFILE_MENTOR, PROFILE_REQUIREMENTS}:
            return value
        return fallback

    def _normalize_response_format(self, value: Any, fallback: str = DEFAULT_RESPONSE_FORMAT) -> str:
        if isinstance(value, str) and value in {"markdown", "json"}:
            return value
        return fallback

    def get_runtime_options(self, overrides: Dict[str, Any], force_profile: Optional[str] = None) -> Dict[str, Any]:
        cfg = self._read_librarian_config()
        merged: Dict[str, Any] = dict(DEFAULT_RUNTIME_OPTIONS)
        merged.update(cfg)

        if force_profile:
            merged["profile"] = force_profile
            if force_profile == PROFILE_REQUIREMENTS:
                merged["response_format"] = "json"
                merged["timeout_s"] = 900
                merged["num_predict"] = 260
                merged["temperature"] = 0.1
                merged["max_chars"] = max(int(merged.get("max_chars", 450) or 450), 500)

        for key, value in overrides.items():
            if value is not None:
                merged[key] = value

        merged["profile"] = self._normalize_profile(merged.get("profile"), fallback=PROFILE_MENTOR)
        merged["response_format"] = self._normalize_response_format(
            merged.get("response_format"),
            fallback="json" if merged["profile"] == PROFILE_REQUIREMENTS else DEFAULT_RESPONSE_FORMAT,
        )
        merged["model"] = str(merged.get("model") or DEFAULT_MODEL)

        int_keys = ("max_files", "max_chars", "timeout_s", "num_predict", "num_ctx")
        for key in int_keys:
            try:
                merged[key] = int(merged.get(key, DEFAULT_RUNTIME_OPTIONS[key]))
            except Exception:
                merged[key] = DEFAULT_RUNTIME_OPTIONS[key]

        try:
            merged["temperature"] = float(merged.get("temperature", DEFAULT_RUNTIME_OPTIONS["temperature"]))
        except Exception:
            merged["temperature"] = DEFAULT_RUNTIME_OPTIONS["temperature"]

        return merged

    def save_runtime_defaults(self, runtime: Dict[str, Any]):
        keys = (
            "model",
            "profile",
            "response_format",
            "max_files",
            "max_chars",
            "timeout_s",
            "num_predict",
            "temperature",
            "num_ctx",
        )
        for key in keys:
            self.config.set(f"Librarian.{key}", runtime.get(key))

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

    def save_history(
        self,
        question: str,
        answer: str,
        model: str,
        profile: str = PROFILE_MENTOR,
        response_format: str = "markdown",
    ):
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": "librarian_local",
            "model": model,
            "profile": profile,
            "response_format": response_format,
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


def _build_requirements_prompt(question: str, context: str, response_format: str) -> str:
    output_rule = (
        "Devuelve JSON valido exclusivamente."
        if response_format == "json"
        else "Devuelve Markdown estructurado y concreto."
    )
    return f"""
Eres "Requirements Architect Local", Ingeniero de Requisitos Senior.

Mision:
- Traducir ideas vagas a especificaciones tecnicas accionables.
- Actuar como Critico/Traductor en un workflow Actor-Critic.
- NO escribir codigo.

Reglas estrictas:
1) No propongas refactor total del sistema.
2) No inventes archivos ni datos inexistentes.
3) Prioriza seguridad, mantenibilidad y alcance incremental.
4) Si la idea es ambigua, explicita supuestos y riesgos.
5) Incluye criterios de aceptacion verificables.
6) {output_rule}

Entrega minima:
- problem_statement
- scope_in / scope_out
- assumptions
- functional_requirements
- non_functional_requirements
- acceptance_criteria
- risks_and_mitigations
- execution_plan
- prompt_for_coding_llm

Contexto del proyecto:
{context}

Solicitud del usuario:
{question}
""".strip()


def _build_prompt(profile: str, question: str, context: str, response_format: str) -> str:
    if profile == PROFILE_REQUIREMENTS:
        return _build_requirements_prompt(question, context, response_format=response_format)
    return _build_mentor_prompt(question, context)


def _run_once_query(
    cmd: LibrarianCommand,
    q: str,
    profile: str,
    response_format: str,
    model: str,
    host: str,
    max_files: int,
    max_chars: int,
    timeout_s: int,
    num_predict: int,
    temperature: float,
    num_ctx: int,
):
    q = (q or "").strip()
    if not q:
        return

    context = cmd.build_context(q, max_files=max_files, max_chars=max_chars)
    prompt = _build_prompt(profile=profile, question=q, context=context, response_format=response_format)
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
    cmd.save_history(
        q,
        answer,
        str(result.get("model", model)),
        profile=profile,
        response_format=response_format,
    )


@click.command(name="ask")
@click.argument("question", required=False)
@click.option("--working-dir", type=str, default=".", help="Raíz del proyecto")
@click.option("--model", type=str, default=None, help="Modelo local Ollama")
@click.option("--host", type=str, default=DEFAULT_OLLAMA_HOST, help="Host Ollama")
@click.option(
    "--profile",
    type=click.Choice([PROFILE_MENTOR, PROFILE_REQUIREMENTS]),
    default=None,
    help="Perfil de rol para la respuesta",
)
@click.option(
    "--response-format",
    type=click.Choice(["markdown", "json"]),
    default=None,
    help="Formato deseado de la respuesta",
)
@click.option("--no-remote/--allow-remote", default=True, show_default=True, help="Mantener operación 100% local")
@click.option("--max-files", type=int, default=None, help="Cantidad de archivos de contexto")
@click.option("--max-chars", type=int, default=None, help="Máximo chars por archivo")
@click.option("--timeout", "timeout_s", type=int, default=None, help="Timeout en segundos")
@click.option("--num-predict", type=int, default=None, help="Tokens máximos a generar")
@click.option("--temperature", type=float, default=None, help="Creatividad del modelo")
@click.option("--num-ctx", type=int, default=None, help="Ventana de contexto")
@click.option("--select", is_flag=True, default=False, help="Abrir selector guiado (modelo/rol/formato)")
@click.option("--save-defaults", is_flag=True, default=False, help="Guardar selección como predeterminada")
def ask_command(
    question: Optional[str],
    working_dir: str,
    model: str,
    host: str,
    profile: str,
    response_format: str,
    no_remote: bool,
    max_files: int,
    max_chars: int,
    timeout_s: int,
    num_predict: int,
    temperature: float,
    num_ctx: int,
    select: bool,
    save_defaults: bool,
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

    runtime = cmd.get_runtime_options(
        overrides={
            "model": model,
            "profile": profile,
            "response_format": response_format,
            "max_files": max_files,
            "max_chars": max_chars,
            "timeout_s": timeout_s,
            "num_predict": num_predict,
            "temperature": temperature,
            "num_ctx": num_ctx,
        }
    )

    if select:
        models = _list_ollama_models(host)
        if models:
            default_model = runtime["model"] if runtime["model"] in models else models[0]
            runtime["model"] = click.prompt(
                "Modelo",
                type=click.Choice(models, case_sensitive=False),
                default=default_model,
                show_default=True,
            )
        runtime["profile"] = click.prompt(
            "Rol",
            type=click.Choice([PROFILE_MENTOR, PROFILE_REQUIREMENTS], case_sensitive=False),
            default=runtime["profile"],
            show_default=True,
        )
        runtime["response_format"] = click.prompt(
            "Formato",
            type=click.Choice(["markdown", "json"], case_sensitive=False),
            default=runtime["response_format"],
            show_default=True,
        )
        if save_defaults:
            cmd.save_runtime_defaults(runtime)
            cmd.print_success("Preferencias Librarian guardadas en config.")
    elif save_defaults:
        cmd.save_runtime_defaults(runtime)
        cmd.print_success("Preferencias Librarian guardadas en config.")

    def run_once(q: str):
        _run_once_query(
            cmd=cmd,
            q=q,
            profile=runtime["profile"],
            response_format=runtime["response_format"],
            model=runtime["model"],
            host=host,
            max_files=runtime["max_files"],
            max_chars=runtime["max_chars"],
            timeout_s=runtime["timeout_s"],
            num_predict=runtime["num_predict"],
            temperature=runtime["temperature"],
            num_ctx=runtime["num_ctx"],
        )

    if question:
        run_once(question)
        return

    cmd.print_info(
        f"Modelo={runtime['model']} | Rol={runtime['profile']} | Formato={runtime['response_format']}"
    )
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


@click.command(name="ask-requirements")
@click.argument("request_text", required=False)
@click.option("--working-dir", type=str, default=".", help="Raíz del proyecto")
@click.option("--model", type=str, default=None, help="Modelo local Ollama")
@click.option("--host", type=str, default=DEFAULT_OLLAMA_HOST, help="Host Ollama")
@click.option(
    "--response-format",
    type=click.Choice(["json", "markdown"]),
    default=None,
    help="Formato de salida para especificaciones",
)
@click.option("--no-remote/--allow-remote", default=True, show_default=True, help="Mantener operación 100% local")
@click.option("--max-files", type=int, default=None, help="Cantidad de archivos de contexto")
@click.option("--max-chars", type=int, default=None, help="Máximo chars por archivo")
@click.option("--timeout", "timeout_s", type=int, default=None, help="Timeout en segundos")
@click.option("--num-predict", type=int, default=None, help="Tokens máximos a generar")
@click.option("--temperature", type=float, default=None, help="Creatividad del modelo")
@click.option("--num-ctx", type=int, default=None, help="Ventana de contexto")
@click.option("--select", is_flag=True, default=False, help="Abrir selector guiado (modelo/formato)")
@click.option("--save-defaults", is_flag=True, default=False, help="Guardar selección como predeterminada")
def ask_requirements_command(
    request_text: Optional[str],
    working_dir: str,
    model: str,
    host: str,
    response_format: str,
    no_remote: bool,
    max_files: int,
    max_chars: int,
    timeout_s: int,
    num_predict: int,
    temperature: float,
    num_ctx: int,
    select: bool,
    save_defaults: bool,
):
    """
    📐 Requirements Architect: traduce ideas vagas a especificaciones accionables.

    Uso:
      cgalpha ask-requirements "Quiero un flujo actor-critic para PR review"
      cgalpha ask-requirements
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

    runtime = cmd.get_runtime_options(
        overrides={
            "model": model,
            "response_format": response_format,
            "max_files": max_files,
            "max_chars": max_chars,
            "timeout_s": timeout_s,
            "num_predict": num_predict,
            "temperature": temperature,
            "num_ctx": num_ctx,
        },
        force_profile=PROFILE_REQUIREMENTS,
    )

    if select:
        models = _list_ollama_models(host)
        if models:
            default_model = runtime["model"] if runtime["model"] in models else models[0]
            runtime["model"] = click.prompt(
                "Modelo",
                type=click.Choice(models, case_sensitive=False),
                default=default_model,
                show_default=True,
            )
        runtime["response_format"] = click.prompt(
            "Formato",
            type=click.Choice(["json", "markdown"], case_sensitive=False),
            default=runtime["response_format"],
            show_default=True,
        )

    if save_defaults:
        cmd.save_runtime_defaults(runtime)
        cmd.print_success("Preferencias Librarian guardadas en config.")

    def run_once(q: str):
        _run_once_query(
            cmd=cmd,
            q=q,
            profile=PROFILE_REQUIREMENTS,
            response_format=runtime["response_format"],
            model=runtime["model"],
            host=host,
            max_files=runtime["max_files"],
            max_chars=runtime["max_chars"],
            timeout_s=runtime["timeout_s"],
            num_predict=runtime["num_predict"],
            temperature=runtime["temperature"],
            num_ctx=runtime["num_ctx"],
        )

    if request_text:
        run_once(request_text)
        return

    cmd.print_info(
        f"Modelo={runtime['model']} | Rol={PROFILE_REQUIREMENTS} | Formato={runtime['response_format']}"
    )
    cmd.print("[bold]Modo interactivo Requirements Architect[/bold] (escribe 'exit' para salir)")
    while True:
        try:
            q = input("req> ").strip()
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


@click.command(name="ask-setup")
@click.option("--working-dir", type=str, default=".", help="Raíz del proyecto")
@click.option("--host", type=str, default=DEFAULT_OLLAMA_HOST, help="Host Ollama")
def ask_setup_command(working_dir: str, host: str):
    """
    ⚙️ Asistente de configuración del Librarian Local.

    Permite elegir modelo, rol y formato por defecto sin usar flags largos.
    """
    cmd = LibrarianCommand(working_dir=working_dir, host=host)

    if not _ollama_alive(host):
        cmd.print_error(
            "Ollama no responde en 127.0.0.1:11434. "
            "Inicia con: systemctl --user start ollama-local.service"
        )
        raise click.Abort()

    runtime = cmd.get_runtime_options(overrides={})
    models = _list_ollama_models(host)

    cmd.print("[bold]Configuración guiada: Librarian Local[/bold]")
    if models:
        default_model = runtime["model"] if runtime["model"] in models else models[0]
        runtime["model"] = click.prompt(
            "Modelo por defecto",
            type=click.Choice(models, case_sensitive=False),
            default=default_model,
            show_default=True,
        )
    else:
        runtime["model"] = click.prompt("Modelo por defecto", default=runtime["model"], show_default=True)

    runtime["profile"] = click.prompt(
        "Rol por defecto",
        type=click.Choice([PROFILE_MENTOR, PROFILE_REQUIREMENTS], case_sensitive=False),
        default=runtime["profile"],
        show_default=True,
    )
    runtime["response_format"] = click.prompt(
        "Formato por defecto",
        type=click.Choice(["markdown", "json"], case_sensitive=False),
        default=runtime["response_format"],
        show_default=True,
    )
    runtime["max_files"] = click.prompt("max_files", type=int, default=runtime["max_files"], show_default=True)
    runtime["max_chars"] = click.prompt("max_chars", type=int, default=runtime["max_chars"], show_default=True)
    runtime["timeout_s"] = click.prompt("timeout", type=int, default=runtime["timeout_s"], show_default=True)
    runtime["num_predict"] = click.prompt("num_predict", type=int, default=runtime["num_predict"], show_default=True)
    runtime["temperature"] = click.prompt(
        "temperature",
        type=float,
        default=runtime["temperature"],
        show_default=True,
    )
    runtime["num_ctx"] = click.prompt("num_ctx", type=int, default=runtime["num_ctx"], show_default=True)

    cmd.save_runtime_defaults(runtime)
    cmd.print_success("Configuración guardada.")
    cmd.print_info(
        f"Modelo={runtime['model']} | Rol={runtime['profile']} | Formato={runtime['response_format']}"
    )
