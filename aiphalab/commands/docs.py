"""
aiphalab/commands/docs.py - Documentation navigation commands.

Provides direct CLI access to the new documentation hub.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List, Optional

import click

from .base import BaseCommand, get_console

console = get_console()


class DocsCommand(BaseCommand):
    """Command helper for documentation index and lookup."""

    def __init__(self, working_dir: str = "."):
        super().__init__()
        self.working_dir = Path(working_dir).resolve()
        self.doc_map: Dict[str, Dict[str, str]] = {
            "index": {
                "path": "docs/DOCS_INDEX.md",
                "description": "Master index with document map and reading order",
            },
            "master": {
                "path": "docs/CGALPHA_MASTER_DOCUMENTATION.md",
                "description": "Detailed canonical documentation for operations and architecture",
            },
            "constitution_companion": {
                "path": "docs/CONSTITUTION_RELEVANT_COMPANION.md",
                "description": "Actionable constitution digest and checklists",
            },
            "companion": {
                "path": "docs/CONSTITUTION_RELEVANT_COMPANION.md",
                "description": "Short alias for constitution companion",
            },
            "coverage": {
                "path": "docs/DOCS_COVERAGE_MATRIX.md",
                "description": "Coverage matrix of legacy docs into the new hub",
            },
            "retention": {
                "path": "docs/DOCS_RETENTION_TABLE.md",
                "description": "KEEP/MERGE/ARCHIVE classification for markdown cleanup",
            },
            "cleanup": {
                "path": "docs/DOCS_RETENTION_TABLE.md",
                "description": "Short alias for docs retention and cleanup table",
            },
            "guide": {
                "path": "docs/CGALPHA_SYSTEM_GUIDE.md",
                "description": "Complete high-level orientation guide for CGAlpha",
            },
            "codecraft_companion": {
                "path": "docs/CODECRAFT_PHASES_1_6_COMPANION.md",
                "description": "Merged operational guide for Code Craft Sage phases 1-6",
            },
            "codecraft": {
                "path": "docs/CODECRAFT_PHASES_1_6_COMPANION.md",
                "description": "Short alias for Code Craft phases 1-6 companion",
            },
            "llm": {
                "path": "docs/LLM_LOCAL_OPERATIONS.md",
                "description": "Local LLM operations, profiles, and prompt patterns",
            },
            "constitution": {
                "path": "UNIFIED_CONSTITUTION_v0.0.3.md",
                "description": "Unified constitution and non-negotiable rules",
            },
            "quickstart": {
                "path": "00_QUICKSTART.md",
                "description": "5-minute onboarding runbook",
            },
            "version": {
                "path": "VERSION.md",
                "description": "Single source of declared version status",
            },
            "constitution_core": {
                "path": "docs/reference/constitution_core.md",
                "description": "Operational constitution core (short form)",
            },
            "core_rules": {
                "path": "docs/reference/constitution_core.md",
                "description": "Short alias for operational constitution core",
            },
            "gates": {
                "path": "docs/reference/gates.md",
                "description": "Readiness gates and thresholds for Deep Causal",
            },
            "parameters": {
                "path": "docs/reference/parameters.md",
                "description": "Critical parameter reference for operation",
            },
            "reference": {
                "path": "docs/reference/README.md",
                "description": "Index for modular reference documentation",
            },
            "rutina_v03": {
                "path": "docs/guides/RUTINA_DIARIA_V03.md",
                "description": "Daily operating routine for Deep Causal v0.3 readiness",
            },
            "daily_v03": {
                "path": "docs/guides/RUTINA_DIARIA_V03.md",
                "description": "Short alias for daily V03 routine guide",
            },
            "phase7": {
                "path": "bible/codecraft_sage/phase7_ghost_architect.md",
                "description": "Ghost Architect phase baseline and goals",
            },
            "phase8": {
                "path": "bible/codecraft_sage/phase8_deep_causal_v03.md",
                "description": "Deep causal architecture guide",
            },
        }

    def list_docs(self) -> List[Dict[str, str]]:
        rows: List[Dict[str, str]] = []
        for key, item in self.doc_map.items():
            rel_path = item["path"]
            full_path = self.working_dir / rel_path
            rows.append(
                {
                    "key": key,
                    "path": rel_path,
                    "description": item["description"],
                    "exists": "yes" if full_path.exists() else "no",
                }
            )
        return rows

    def resolve_doc(self, key: str) -> Optional[Path]:
        item = self.doc_map.get(key)
        if not item:
            return None
        path = self.working_dir / item["path"]
        return path


@click.group(name="docs")
def docs_group():
    """Access project documentation directly from CLI."""
    pass


@docs_group.command(name="list")
@click.option("--working-dir", type=str, default=".", help="Project root")
def list_docs(working_dir: str):
    """List supported documentation entries."""
    cmd = DocsCommand(working_dir=working_dir)
    rows = cmd.list_docs()

    if console:
        from rich.table import Table

        table = Table(title="CGAlpha Docs", show_header=True, header_style="bold blue")
        table.add_column("Key", style="cyan")
        table.add_column("Exists", style="magenta")
        table.add_column("Path", style="green")
        table.add_column("Description", style="white")
        for row in rows:
            table.add_row(row["key"], row["exists"], row["path"], row["description"])
        console.print(table)
    else:
        for row in rows:
            click.echo(f"{row['key']}: {row['exists']} | {row['path']} | {row['description']}")


@docs_group.command(name="path")
@click.argument("key", type=str)
@click.option("--working-dir", type=str, default=".", help="Project root")
def doc_path(key: str, working_dir: str):
    """Show absolute path for one documentation key."""
    cmd = DocsCommand(working_dir=working_dir)
    path = cmd.resolve_doc(key)
    if path is None:
        cmd.print_error(f"Unknown doc key: {key}")
        raise click.Abort()
    if not path.exists():
        cmd.print_error(f"File not found: {path}")
        raise click.Abort()
    click.echo(str(path))


@docs_group.command(name="show")
@click.argument("key", type=str)
@click.option("--working-dir", type=str, default=".", help="Project root")
@click.option("--lines", type=int, default=160, show_default=True, help="How many lines to print")
@click.option("--full", "show_full", is_flag=True, default=False, help="Print full file")
def show_doc(key: str, working_dir: str, lines: int, show_full: bool):
    """Print one documentation file directly in terminal."""
    cmd = DocsCommand(working_dir=working_dir)
    path = cmd.resolve_doc(key)
    if path is None:
        cmd.print_error(f"Unknown doc key: {key}")
        raise click.Abort()
    if not path.exists():
        cmd.print_error(f"File not found: {path}")
        raise click.Abort()

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        cmd.print_error(f"Cannot read file: {exc}")
        raise click.Abort()

    if not show_full:
        content = "\n".join(content.splitlines()[:lines])
    click.echo(content)
