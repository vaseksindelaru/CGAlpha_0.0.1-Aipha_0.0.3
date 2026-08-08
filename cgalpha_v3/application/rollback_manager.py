"""
CGAlpha v3 — Rollback Manager (Sección P)
==========================================
Snapshot automático antes de cada propuesta.
Restauración desde GUI con verificación de hash.

SLAs:
  P0: <60s
  P1: <10min
  P2: <1h
  P3: próxima sesión
"""
from __future__ import annotations

import hashlib
import json
import logging
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

BASE_MEMORY = Path(__file__).parent.parent / "memory"
SNAPSHOTS_DIR = BASE_MEMORY / "snapshots"


# Snapshot structure (on disk):
#   memory/snapshots/YYYY-MM-DD_HH-MM_<proposal_id>/
#     ├── config.json          ← Configuración activa
#     ├── model_params.json    ← Parámetros de modelos
#     ├── git_sha.txt          ← Hash del código (git SHA o equivalente)
#     ├── memory_l3l4.json     ← Estado niveles 3 y 4
#     └── manifest.json        ← Hash global del snapshot


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_dict(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class RollbackManager:
    """
    Gestiona snapshots y restauraciones (Sección P).

    Uso:
        rm = RollbackManager()
        snap_path = rm.take_snapshot(proposal_id="prop-abc123", config={...})
        rm.restore(snap_path)
    """

    def __init__(self, snapshots_dir: Path | None = None) -> None:
        self._dir = snapshots_dir or SNAPSHOTS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    # ── SNAPSHOT ──────────────────────────────────
    def take_snapshot(
        self,
        proposal_id: str,
        config: dict[str, Any],
        model_params: dict[str, Any] | None = None,
        memory_l3l4: dict[str, Any] | None = None,
        git_sha: str = "unknown",
    ) -> Path:
        """
        Toma un snapshot antes de aplicar una propuesta.
        Retorna la ruta al directorio del snapshot.
        """
        ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M")
        snap_name = f"{ts_str}_{proposal_id}"
        snap_path = self._dir / snap_name
        snap_path.mkdir(parents=True, exist_ok=True)

        # Guardar artefactos
        self._write_json(snap_path / "config.json",       config)
        self._write_json(snap_path / "model_params.json", model_params or {})
        self._write_json(snap_path / "memory_l3l4.json",  memory_l3l4 or {})
        (snap_path / "git_sha.txt").write_text(git_sha)

        # Manifest con hash global
        hashes: dict[str, str] = {
            "config":       _sha256_dict(config),
            "model_params": _sha256_dict(model_params or {}),
            "memory_l3l4":  _sha256_dict(memory_l3l4 or {}),
        }
        manifest: dict[str, Any] = {
            "proposal_id": proposal_id,
            "created_at":  datetime.now(timezone.utc).isoformat(),
            "git_sha":     git_sha,
            "hashes": hashes,
        }
        manifest["global_hash"] = _sha256_dict(hashes)
        self._write_json(snap_path / "manifest.json", manifest)

        log.info(f"[Rollback] Snapshot creado: {snap_path} (hash: {manifest['global_hash'][:12]}…)")
        return snap_path

    # ── LIST ──────────────────────────────────────
    def list_snapshots(self) -> list[dict[str, Any]]:
        """Lista snapshots disponibles, ordenados por más reciente primero."""
        snaps = []
        for d in sorted(self._dir.iterdir(), reverse=True):
            if d.is_dir():
                manifest_path = d / "manifest.json"
                if manifest_path.exists():
                    try:
                        manifest = json.loads(manifest_path.read_text())
                        snaps.append({"name": d.name, "path": str(d), **manifest})
                    except Exception:
                        snaps.append({"name": d.name, "path": str(d)})
        return snaps

    # ── RESTORE ───────────────────────────────────
    def restore(
        self,
        snapshot_path: Path | str,
        verify_hash: bool = True,
    ) -> dict[str, Any]:
        """
        Restaura un snapshot. Verifica hash si `verify_hash=True` (Sección P).
        Retorna el contenido restaurado.

        SLA P0: esta operación debe completarse en <60s.
        El tiempo real depende del tamaño de los datos; en FASE 0 es <1s.
        """
        start = time.perf_counter()
        snap_path = Path(snapshot_path)

        if not snap_path.exists():
            raise FileNotFoundError(f"Snapshot no encontrado: {snap_path}")

        manifest_path = snap_path / "manifest.json"
        if not manifest_path.exists():
            raise ValueError(f"Snapshot inválido: sin manifest.json en {snap_path}")

        manifest = json.loads(manifest_path.read_text())
        config      = json.loads((snap_path / "config.json").read_text())
        model_params = json.loads((snap_path / "model_params.json").read_text())
        memory_l3l4  = json.loads((snap_path / "memory_l3l4.json").read_text())

        if verify_hash:
            current_hashes = {
                "config":       _sha256_dict(config),
                "model_params": _sha256_dict(model_params),
                "memory_l3l4":  _sha256_dict(memory_l3l4),
            }
            current_global = _sha256_dict(current_hashes)
            expected_global = manifest.get("global_hash", "")
            if current_global != expected_global:
                raise ValueError(
                    f"Hash mismatch en snapshot {snap_path.name}: "
                    f"actual={current_global[:12]}… esperado={expected_global[:12]}…"
                )

        elapsed = time.perf_counter() - start
        log.info(
            f"[Rollback] Restauración completada: {snap_path.name} "
            f"en {elapsed*1000:.0f}ms (SLA P0: <60000ms)"
        )

        return {
            "config":        config,
            "model_params":  model_params,
            "memory_l3l4":   memory_l3l4,
            "git_sha":       manifest.get("git_sha", "unknown"),
            "restored_from": str(snap_path),
            "elapsed_ms":    elapsed * 1000,
        }

    # ── UTILS ─────────────────────────────────────
    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        path.write_text(json.dumps(data, indent=2, default=str))
