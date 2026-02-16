"""
cgalpha.shared.exceptions — Domain exception hierarchy.

Design decisions:
- Every exception carries a machine-readable `error_code` for log aggregation.
- Optional `details` dict for structured context (no stringly-typed debugging).
- Leaf exceptions inherit from context-specific bases (e.g., SignalDetectionError
  inherits from TradingError, which inherits from CGAlphaError).
- This module has ZERO external dependencies — it is pure Python.

Relationship to legacy:
- core/exceptions.py remains for backward compatibility during migration.
- New code should import from cgalpha_v2.shared.exceptions.
- Once migration Phase 3 is complete, core/exceptions.py will be removed.

Usage:
    from cgalpha_v2.shared.exceptions import ConfigurationError

    raise ConfigurationError(
        "tp_factor must be positive",
        details={"parameter": "tp_factor", "value": -1.0},
    )
"""

from __future__ import annotations

from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# BASE
# ═══════════════════════════════════════════════════════════════════════════════


class CGAlphaError(Exception):
    """
    Root exception for the entire CGAlpha system.

    Every domain exception inherits from this, making it possible to catch
    all system errors with a single ``except CGAlphaError``.

    Attributes:
        message:    Human-readable description.
        error_code: Machine-readable code for log aggregation (e.g. "SIGNAL_001").
        details:    Optional structured context for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "CGALPHA_UNKNOWN",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details: dict[str, Any] = details or {}
        super().__init__(message)

    def __str__(self) -> str:
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            pairs = " | ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{base} ({pairs})"
        return base

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"message={self.message!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r})"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════════


class DataError(CGAlphaError):
    """Base for all data-related errors (loading, processing, validation)."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "DATA_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class DataLoadError(DataError):
    """Raised when market data cannot be loaded from its source."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="DATA_LOAD", details=details)


class DataValidationError(DataError):
    """Raised when loaded data fails integrity checks."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="DATA_VALIDATION", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════


class ConfigurationError(CGAlphaError):
    """Raised when configuration is missing, invalid, or out of range."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="CONFIG_ERROR", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# TRADING / SIGNAL DETECTION
# ═══════════════════════════════════════════════════════════════════════════════


class TradingError(CGAlphaError):
    """Base for errors in the Signal Detection bounded context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "TRADING_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class SignalDetectionError(TradingError):
    """Raised when signal detection fails (bad data, detector crash, etc.)."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="SIGNAL_DETECTION", details=details)


class BarrierCalculationError(TradingError):
    """Raised when ATR barrier calculation encounters invalid inputs."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="BARRIER_CALC", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# PREDICTION (ORACLE)
# ═══════════════════════════════════════════════════════════════════════════════


class PredictionError(CGAlphaError):
    """Base for errors in the Prediction bounded context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "PREDICTION_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class ModelLoadError(PredictionError):
    """Raised when a serialized ML model cannot be loaded."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="MODEL_LOAD", details=details)


class FeatureExtractionError(PredictionError):
    """Raised when feature extraction from candle data fails."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="FEATURE_EXTRACTION", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# CAUSAL ANALYSIS (GHOST ARCHITECT)
# ═══════════════════════════════════════════════════════════════════════════════


class AnalysisError(CGAlphaError):
    """Base for errors in the Causal Analysis bounded context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "ANALYSIS_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class PatternDetectionError(AnalysisError):
    """Raised when pattern detection produces inconsistent results."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="PATTERN_DETECTION", details=details)


class InferenceError(AnalysisError):
    """Raised when causal inference (LLM or heuristic) fails."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="INFERENCE", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# CODE EVOLUTION (CODE CRAFT SAGE)
# ═══════════════════════════════════════════════════════════════════════════════


class EvolutionError(CGAlphaError):
    """Base for errors in the Code Evolution bounded context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "EVOLUTION_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class ProposalParsingError(EvolutionError):
    """Raised when a natural-language proposal cannot be parsed."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="PROPOSAL_PARSE", details=details)


class CodeModificationError(EvolutionError):
    """Raised when AST-based code modification fails."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="CODE_MODIFY", details=details)


class RollbackError(EvolutionError):
    """Raised when a rollback from backup fails (critical)."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="ROLLBACK", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════


class OperationsError(CGAlphaError):
    """Base for errors in the System Operations bounded context."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "OPS_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class HealthCheckError(OperationsError):
    """Raised when a health check fails."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="HEALTH_CHECK", details=details)


class ResourceExhaustedError(OperationsError):
    """Raised when CPU/RAM exceeds safe thresholds."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="RESOURCE_EXHAUSTED", details=details)


class CycleInterruptedError(OperationsError):
    """Raised when a cycle is interrupted by signal or resource pressure."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="CYCLE_INTERRUPTED", details=details)


# ═══════════════════════════════════════════════════════════════════════════════
# LLM / EXTERNAL SERVICES
# ═══════════════════════════════════════════════════════════════════════════════


class LLMError(CGAlphaError):
    """Base for errors when calling external LLM providers."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "LLM_ERROR",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class LLMConnectionError(LLMError):
    """Raised when the LLM API is unreachable."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="LLM_CONNECTION", details=details)


class LLMRateLimitError(LLMError):
    """Raised when the LLM API rate limit is exceeded."""

    def __init__(self, message: str, *, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message, error_code="LLM_RATE_LIMIT", details=details)
