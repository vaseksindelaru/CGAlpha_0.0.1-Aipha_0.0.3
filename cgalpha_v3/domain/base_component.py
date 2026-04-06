from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

@dataclass
class ParameterSpec:
    value: Any
    range: tuple
    critical: bool = False

@dataclass
class CorrelationEdge:
    component_id: str
    correlation: float
    type: str  # e.g., "complementary", "prerequisite"

@dataclass
class ComponentManifest:
    # --- IDENTIDAD ---
    component_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    category: str = "general"  # signal | entry | exit | filtering | microstructure | labeling | meta
    layer: str = "layer_2_permanent"
    
    # --- FUNCIÓN ---
    function: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    
    # --- PARÁMETROS VALIDADOS ---
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # --- GENEALOGÍA ---
    heritage_source: str = ""
    heritage_contribution: str = ""
    v3_adaptations: str = ""
    vault_origin_purged: bool = False
    
    # --- VALIDACIÓN CAUSAL ---
    causal_score: float = 0.0
    oos_period: str = ""
    hit_rate_improvement: float = 0.0
    validated_regimes: List[str] = field(default_factory=list)
    invalid_regimes: List[str] = field(default_factory=list)
    cate_by_regime: Dict[str, float] = field(default_factory=dict)
    
    # --- CALIDAD TÉCNICA ---
    test_coverage: float = 0.0
    complexity_cyclomatic: int = 0
    last_codecraft_improvement: str = field(default_factory=lambda: datetime.now().isoformat())
    rollback_available: bool = True
    
    # --- ORGANIZACIÓN VECTORIAL ---
    embedding_vector: List[float] = field(default_factory=list)
    correlated_with: List[CorrelationEdge] = field(default_factory=list)
    
    # --- ESTADO ---
    status: str = "ACTIVE"  # ACTIVE | DEPRECATED | EVOLVED | ROLLBACK

class BaseComponentV3:
    """
    Contrato base inmutable para todos los componentes del ADN Permanente.
    Implementa el Wrapper Pattern y asegura la trazabilidad causal.
    """
    def __init__(self, manifest: ComponentManifest):
        self.manifest = manifest

    def evaluate(self, *args, **kwargs) -> Any:
        """Metodo principal de ejecucion del componente."""
        raise NotImplementedError("Cada componente del ADN debe implementar 'evaluate'")

    @property
    def identity(self) -> str:
        return f"{self.manifest.name} v{self.manifest.version} [{self.manifest.component_id}]"
