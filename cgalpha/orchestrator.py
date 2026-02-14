"""
CGAlpha Orchestrator - Phase 7 unification entrypoint.

Connects Ghost Architect (strategy) with Code Craft Sage (execution proposals).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from cgalpha.codecraft.proposal_generator import ProposalGenerator
from cgalpha.ghost_architect.simple_causal_analyzer import SimpleCausalAnalyzer


class CGAlphaOrchestrator:
    """Unified orchestrator for autonomous analysis cycle."""

    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir).resolve()
        memory_dir = self.working_dir / "aipha_memory"

        self.analyzer = SimpleCausalAnalyzer(working_dir=str(self.working_dir))
        self.proposal_generator = ProposalGenerator(data_dir=str(memory_dir), min_confidence=0.70)

    def auto_analyze(
        self,
        min_confidence: float = 0.70,
        log_file: Optional[str] = None,
        cleanup_processed: bool = False,
    ) -> Dict[str, Any]:
        self.proposal_generator.min_confidence = min_confidence

        analysis = self.analyzer.analyze_performance(log_file=log_file)
        insights = self.analyzer.get_actionable_insights(
            analysis.get("patterns", []),
            analysis.get("causal_hypotheses", []),
        )
        proposals = self.proposal_generator.analyze_performance()
        report_path = self.analyzer.save_analysis_report(analysis, insights)

        cleaned_log = None
        if cleanup_processed and analysis.get("source"):
            cleaned = self.analyzer.cleanup_processed_log(analysis["source"])
            cleaned_log = str(cleaned) if cleaned else None

        return {
            "analysis": analysis,
            "insights": insights,
            "proposals": proposals,
            "report_path": str(report_path),
            "cleaned_log": cleaned_log,
        }
