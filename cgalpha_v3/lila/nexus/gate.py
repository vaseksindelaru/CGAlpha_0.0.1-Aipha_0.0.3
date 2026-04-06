from typing import Optional, List, Dict
from dataclasses import dataclass
from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest
from cgalpha_v3.domain.records import OutcomeOrdinal

@dataclass
class GateReport:
    component_id: str
    delta_causal_oos: float
    blind_test_ratio: float
    test_coverage: float
    hit_rate_improvement: float
    human_approval: bool = False
    decision: str = "REJECTED" # "PROMOTED" | "REJECTED"

class NexusGate(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  MOSAIC ADAPTER — Componente v3                      ║
    ║  Heritage: legacy_vault/v1/cgalpha/nexus/            ║
    ║            coordinator.py (CGA_Nexus)                ║
    ║  Heritage Contribution:                              ║
    ║    - Orquestación de Labs y semáforo de estado       ║
    ║    - Gate final de promoción de señal                ║
    ║  v3 Adaptations:                                     ║
    │    - Gate Binario de ADN Permanente                  ║
    │    - Auditoría Causal de OOS (Sección 1.4)           ║
    ╚═══════════════════════════════════════════════════════╝
    """
    
    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        # Umbrales no negociables del canon 3.0.0
        self.min_delta = 0.0
        self.max_blind_ratio = 0.25
        self.min_test_coverage = 0.80

    def evaluate_performance(self, report: GateReport) -> str:
        """
        Determina de forma binaria si un componente es promovido al ADN Permanente.
        Implementa el NexusGate (Sección 1.4 North Star).
        """
        if (report.delta_causal_oos > self.min_delta and 
            report.blind_test_ratio <= self.max_blind_ratio and 
            report.test_coverage >= self.min_test_coverage and
            report.human_approval):
            
            report.decision = "PROMOTED_TO_LAYER_2"
        else:
            report.decision = "REJECTED_TO_VAULT"
            
        return report.decision

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="NexusGate",
            category="meta",
            function="Evaluación binaria para promoción al ADN Permanente (Juez del Gate)",
            inputs=["PerformanceReport", "HumanApproval"],
            outputs=["Decision (PROMOTED/REJECTED)"],
            heritage_source="legacy_vault/v1/cgalpha/nexus/coordinator.py",
            heritage_contribution="Orchestration logic and terminal signaling.",
            v3_adaptations="Binary DNA promotion gate logic and causal audit integration.",
            causal_score=1.0 # Máxima autoridad operativa
        )
        return cls(manifest)
