"""
cgAlpha_0.0.1 — Parameter Landscape Map (S3 Step 4)
====================================================
Deterministic extraction of configurable parameters plus
qualitative impact estimation (heuristic-first, optional LLM enrichment).
"""
from __future__ import annotations

import ast
import json
import logging
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("parameter_landscape")


PARAMETER_NAME_HINTS = (
    "threshold",
    "min_",
    "max_",
    "timeout",
    "window",
    "lookback",
    "period",
    "ratio",
    "multiplier",
    "size",
    "pct",
    "score",
    "confidence",
    "cooldown",
    "retry",
    "retrain",
    "slippage",
    "fee",
    "risk",
    "drawdown",
    "limit",
    "token",
    "bars",
)

HIGH_SENSITIVITY_HINTS = (
    "risk",
    "drawdown",
    "kill_switch",
    "max_position",
    "max_signals",
    "min_signal_quality",
    "confidence",
    "threshold",
    "slippage",
    "fee",
)

MEDIUM_SENSITIVITY_HINTS = (
    "window",
    "period",
    "lookback",
    "timeout",
    "multiplier",
    "cooldown",
    "bars",
    "retrain",
    "token",
)

DEFAULT_EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    ".pytest_cache",
    ".venv",
    "docs",
    "memory",
    "tests",
}

AUTO_PROPOSER_REFERENCE_FILES = (
    "lila/llm/proposer.py",
    "application/change_proposer.py",
    "application/pipeline.py",
    "data/phase1_results/auto_proposer_output.json",
)


@dataclass(frozen=True)
class ParameterRecord:
    name: str
    file: str
    line: int
    current_value: Any
    type: str
    sensitivity: str
    causal_impact_est: float
    auto_proposer_refs: int


def build_parameter_landscape_map(
    *,
    project_root: Path,
    artifact_path: Path,
    switcher: Any = None,
    use_llm: bool = False,
) -> dict[str, Any]:
    """
    Build and persist a deterministic-first parameter landscape artifact.
    """
    project_root = project_root.resolve()
    python_files = _discover_python_files(project_root)

    candidates = _extract_parameter_candidates(project_root, python_files)
    refs_map = _count_auto_proposer_refs(project_root, [c.name for c in candidates])

    records = []
    for candidate in candidates:
        refs = refs_map.get(candidate.name, 0)
        sensitivity = _estimate_sensitivity(candidate.name, candidate.file, refs)
        causal = _estimate_causal_impact(candidate.file, sensitivity, refs)
        records.append(
            ParameterRecord(
                name=candidate.name,
                file=candidate.file,
                line=candidate.line,
                current_value=candidate.current_value,
                type=candidate.type,
                sensitivity=sensitivity,
                causal_impact_est=causal,
                auto_proposer_refs=refs,
            )
        )

    qualitative_source = "heuristic_fallback"
    if use_llm and switcher is not None and records:
        llm_enriched, source = _try_llm_enrichment(records, switcher)
        if llm_enriched:
            records = llm_enriched
            qualitative_source = source

    sensitivity_breakdown = {"high": 0, "medium": 0, "low": 0}
    for rec in records:
        if rec.sensitivity in sensitivity_breakdown:
            sensitivity_breakdown[rec.sensitivity] += 1

    artifact = {
        "artifact": "parameter_landscape_map",
        "version": "v4_s3_step4",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "qualitative_source": qualitative_source,
        "parameter_count": len(records),
        "sensitivity_breakdown": sensitivity_breakdown,
        "parameters": [asdict(r) for r in records],
    }

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(artifact, indent=2, ensure_ascii=False), encoding="utf-8")
    return artifact


def load_parameter_landscape_map(artifact_path: Path) -> dict[str, Any] | None:
    if not artifact_path.exists():
        return None
    try:
        return json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Parameter landscape artifact is not valid JSON: %s", artifact_path)
        return None


@dataclass(frozen=True)
class _ParameterCandidate:
    name: str
    file: str
    line: int
    current_value: Any
    type: str


def _discover_python_files(project_root: Path) -> list[Path]:
    files = []
    for py_file in project_root.rglob("*.py"):
        if any(part in DEFAULT_EXCLUDED_DIRS for part in py_file.parts):
            continue
        files.append(py_file)
    return sorted(files)


def _extract_parameter_candidates(project_root: Path, python_files: list[Path]) -> list[_ParameterCandidate]:
    found: dict[tuple[str, int, str], _ParameterCandidate] = {}

    for py_file in python_files:
        try:
            src = py_file.read_text(encoding="utf-8")
        except OSError:
            continue

        try:
            tree = ast.parse(src, filename=str(py_file))
        except SyntaxError:
            continue

        rel_file = str(py_file.relative_to(project_root))
        for name, line, value in _iter_parameter_assignments(tree):
            if not _looks_like_parameter_name(name):
                continue
            if not _is_supported_parameter_value(value):
                continue
            key = (rel_file, line, name)
            if key in found:
                continue
            found[key] = _ParameterCandidate(
                name=name,
                file=rel_file,
                line=line,
                current_value=value,
                type=type(value).__name__,
            )

    # Prefer stable ordering and deterministic output.
    return [found[key] for key in sorted(found.keys(), key=lambda x: (x[0], x[1], x[2]))]


def _iter_parameter_assignments(tree: ast.AST) -> list[tuple[str, int, Any]]:
    rows: list[tuple[str, int, Any]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = _literal_eval(node.value)
            if value is None:
                continue
            for target in node.targets:
                target_name = _extract_target_name(target)
                if target_name:
                    rows.append((target_name, getattr(target, "lineno", getattr(node, "lineno", 0)), value))
        elif isinstance(node, ast.AnnAssign):
            value = _literal_eval(node.value)
            if value is None:
                continue
            target_name = _extract_target_name(node.target)
            if target_name:
                rows.append((target_name, getattr(node.target, "lineno", getattr(node, "lineno", 0)), value))
        elif isinstance(node, ast.Dict):
            for key_node, value_node in zip(node.keys, node.values):
                key_name = _extract_dict_key_name(key_node)
                value = _literal_eval(value_node)
                if key_name is None or value is None:
                    continue
                line = getattr(key_node, "lineno", getattr(value_node, "lineno", getattr(node, "lineno", 0)))
                rows.append((key_name, line, value))

    return rows


def _literal_eval(node: ast.AST | None) -> Any | None:
    if node is None:
        return None

    if isinstance(node, ast.Constant):
        value = node.value
        if isinstance(value, (bool, int, float, str)):
            return value
        return None

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _literal_eval(node.operand)
        if isinstance(inner, (int, float)):
            return -inner
        return None

    return None


def _extract_target_name(target: ast.AST) -> str | None:
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Subscript):
        key_name = _extract_dict_key_name(target.slice)
        if key_name:
            return key_name
    return None


def _extract_dict_key_name(node: ast.AST | None) -> str | None:
    if node is None:
        return None

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value

    # Python <3.9 compatibility on typed trees is not needed here, but keep tolerant.
    if hasattr(ast, "Index") and isinstance(node, ast.Index):  # pragma: no cover
        return _extract_dict_key_name(node.value)

    return None


def _looks_like_parameter_name(name: str) -> bool:
    normalized = name.strip().lower()
    if not normalized:
        return False
    return any(hint in normalized for hint in PARAMETER_NAME_HINTS)


def _is_supported_parameter_value(value: Any) -> bool:
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        return len(value) <= 48
    return False


def _count_auto_proposer_refs(project_root: Path, parameter_names: list[str]) -> dict[str, int]:
    refs: dict[str, int] = {name: 0 for name in parameter_names}

    texts: list[str] = []
    for rel in AUTO_PROPOSER_REFERENCE_FILES:
        path = project_root / rel
        if not path.exists():
            continue
        try:
            texts.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue

    if not texts:
        return refs

    corpus = "\n".join(texts)
    for name in refs:
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        refs[name] = len(pattern.findall(corpus))
    return refs


def _estimate_sensitivity(name: str, file_path: str, refs: int) -> str:
    context = f"{name} {file_path}".lower()
    score = 0

    if any(hint in context for hint in HIGH_SENSITIVITY_HINTS):
        score += 2
    if any(hint in context for hint in MEDIUM_SENSITIVITY_HINTS):
        score += 1

    if refs >= 6:
        score += 2
    elif refs >= 2:
        score += 1

    if "risk/" in file_path or "oracle.py" in file_path or "pipeline.py" in file_path:
        score += 1

    if score >= 4:
        return "high"
    if score >= 2:
        return "medium"
    return "low"


def _estimate_causal_impact(file_path: str, sensitivity: str, refs: int) -> float:
    base = {"high": 0.72, "medium": 0.54, "low": 0.34}[sensitivity]
    base += min(0.20, refs * 0.03)

    if "risk/" in file_path:
        base += 0.08
    elif "oracle.py" in file_path:
        base += 0.06
    elif "pipeline.py" in file_path:
        base += 0.05

    return round(max(0.0, min(base, 0.99)), 2)


def _try_llm_enrichment(
    records: list[ParameterRecord], switcher: Any
) -> tuple[list[ParameterRecord] | None, str]:
    """
    Optional qualitative enrichment from LLM. Deterministic fields stay unchanged.
    """
    sample = records[:60]
    payload = [
        {
            "name": rec.name,
            "file": rec.file,
            "line": rec.line,
            "current_value": rec.current_value,
            "type": rec.type,
            "auto_proposer_refs": rec.auto_proposer_refs,
            "sensitivity": rec.sensitivity,
            "causal_impact_est": rec.causal_impact_est,
        }
        for rec in sample
    ]

    prompt = (
        "Refina SOLO campos cualitativos para este mapa de parametros.\n"
        "No cambies name/file/line/current_value/type/auto_proposer_refs.\n"
        "Devuelve JSON con formato: {\"parameters\":[{\"name\":\"...\",\"sensitivity\":\"high|medium|low\","
        "\"causal_impact_est\":0.0}]}\n"
        f"INPUT={json.dumps(payload, ensure_ascii=False)}"
    )

    try:
        raw = switcher.generate("cat_2", prompt, temperature=0.1, max_tokens=1200)
        parsed = json.loads(raw)
    except Exception as exc:
        logger.info("LLM enrichment unavailable, using heuristic fallback: %s", exc)
        return None, "heuristic_fallback"

    mapping = {}
    for item in parsed.get("parameters", []):
        name = str(item.get("name", "")).strip()
        sensitivity = str(item.get("sensitivity", "")).strip().lower()
        causal = item.get("causal_impact_est")
        if not name or sensitivity not in {"high", "medium", "low"}:
            continue
        try:
            causal_value = float(causal)
        except (TypeError, ValueError):
            continue
        mapping[name] = (sensitivity, round(max(0.0, min(causal_value, 1.0)), 2))

    if not mapping:
        return None, "heuristic_fallback"

    enriched = []
    for rec in records:
        sensitivity, causal = mapping.get(rec.name, (rec.sensitivity, rec.causal_impact_est))
        enriched.append(
            ParameterRecord(
                name=rec.name,
                file=rec.file,
                line=rec.line,
                current_value=rec.current_value,
                type=rec.type,
                sensitivity=sensitivity,
                causal_impact_est=causal,
                auto_proposer_refs=rec.auto_proposer_refs,
            )
        )

    return enriched, "llm_switcher_cat_2"
