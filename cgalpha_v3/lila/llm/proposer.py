from typing import Optional, List, Dict
from dataclasses import dataclass
from cgalpha_v3.domain.base_component import BaseComponentV3, ComponentManifest

@dataclass
class TechnicalSpec:
    change_type: str        # "parameter" | "feature" | "optimization"
    target_file: str
    target_attribute: str
    old_value: float
    new_value: float
    reason: str             # Explicación lingüística para el operador
    causal_score_est: float # Promedio estimado ΔCausal
    confidence: float       # Confianza de la propuesta
    new_code: Optional[str] = None  # v4: Código Python como string para cambios estructurales
    old_code: Optional[str] = None  # v4: Fragmento original para verificación

class AutoProposer(BaseComponentV3):
    """
    ╔═══════════════════════════════════════════════════════╗
    ║  MOSAIC ADAPTER — Componente v3                      ║
    ║  Heritage: legacy_vault/v1/cgalpha/core/             ║
    ║            change_proposer.py                        ║
    ║  Heritage Contribution:                              ║
    ║    - Generación de objetos ChangeProposal            ║
    ║    - Identificación automática de drift              ║
    ║  v3 Adaptations:                                     ║
    │    - Generación de TechnicalSpec para CodeCraft      ║
    │    - Evaluación de Propuestas (Fase 6 CodeCraft)     ║
    ╚═══════════════════════════════════════════════════════╝
    """
    
    def __init__(self, manifest: ComponentManifest):
        super().__init__(manifest)
        self.min_proposal_score = 0.75 # Umbral canónico (Sección 2.4 v3.0)

    def analyze_drift(self, performance_metrics: Dict) -> List[TechnicalSpec]:
        """
        Analiza métricas de accuracy del Oracle y hit-rate de estrategia.
        Propone ajustes paramétricos si detecta degradación causal.
        """
        proposals: List[TechnicalSpec] = []

        accuracy = float(
            performance_metrics.get(
                "oracle_accuracy_oos",
                performance_metrics.get("oracle_accuracy_oos_avg", 0.85),
            )
        )
        max_dd = float(
            performance_metrics.get(
                "max_drawdown_pct",
                performance_metrics.get("max_drawdown_avg", 0.0),
            )
        )
        win_rate = float(
            performance_metrics.get(
                "win_rate_pct",
                performance_metrics.get("win_rate_avg", 55.0),
            )
        )
        sharpe = float(
            performance_metrics.get(
                "sharpe_neto",
                performance_metrics.get("sharpe_neto_avg", 1.0),
            )
        )
        importances = performance_metrics.get("feature_importances", {}) or {}
        errors = int(performance_metrics.get("errors", 0))

        if accuracy < 0.60:
            proposals.append(TechnicalSpec(
                change_type="parameter",
                target_file="cgalpha_v3/lila/llm/oracle.py",
                target_attribute="min_confidence",
                old_value=0.70,
                new_value=0.65,
                reason=(
                    f"Oracle accuracy OOS={accuracy:.2%} está por debajo del 60%. "
                    "Reducir umbral de confianza puede recuperar señales verdaderas."
                ),
                causal_score_est=0.45,
                confidence=0.70,
            ))

        if max_dd > 5.0:
            proposals.append(TechnicalSpec(
                change_type="parameter",
                target_file="cgalpha_v3/gui/server.py",
                target_attribute="max_position_size_pct",
                old_value=2.0,
                new_value=1.0,
                reason=(
                    f"Max drawdown={max_dd:.2f}% excede 5%. "
                    "Reducir el tamaño de posición limita la exposición."
                ),
                causal_score_est=0.55,
                confidence=0.80,
            ))

        if win_rate < 50.0:
            proposals.append(TechnicalSpec(
                change_type="parameter",
                target_file="cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py",
                target_attribute="min_coincidence_score",
                old_value=0.50,
                new_value=0.60,
                reason=(
                    f"Win rate={win_rate:.1f}% por debajo del 50%. "
                    "Subir el umbral de calidad reduce señales débiles."
                ),
                causal_score_est=0.50,
                confidence=0.65,
            ))

        if sharpe < 0.5:
            proposals.append(TechnicalSpec(
                change_type="parameter",
                target_file="cgalpha_v3/lila/llm/oracle.py",
                target_attribute="n_estimators",
                old_value=100.0,
                new_value=200.0,
                reason=(
                    f"Sharpe neto={sharpe:.4f} por debajo de 0.5. "
                    "Incrementar árboles puede capturar patrones más finos."
                ),
                causal_score_est=0.40,
                confidence=0.55,
            ))

        for feature_name, importance in importances.items():
            try:
                imp_value = float(importance)
            except (TypeError, ValueError):
                continue
            if imp_value < 0.05:
                proposals.append(TechnicalSpec(
                    change_type="feature",
                    target_file="cgalpha_v3/lila/llm/oracle.py",
                    target_attribute=f"feature:{feature_name}",
                    old_value=imp_value,
                    new_value=0.0,
                    reason=(
                        f"Feature '{feature_name}' tiene importancia={imp_value:.4f} (<5%). "
                        "Candidata a simplificación o eliminación."
                    ),
                    causal_score_est=0.30,
                    confidence=0.50,
                ))

        if errors > 3:
            # Propuesta estructural de prueba: Optimizar el latch de reconexión del WS
            proposals.append(TechnicalSpec(
                change_type="structural",
                target_file="cgalpha_v3/infrastructure/binance_websocket_manager.py",
                target_attribute="start",
                old_value=0.0,
                new_value=0.0,
                new_code='''async def start(self):
    """v4 AST-optimized connection latch."""
    self._active = True
    while self._active:
        try:
            await self._run_socket()
        except Exception as e:
            logger.warning(f"WS Exception in Sage-optimized loop: {e}")
            await asyncio.sleep(5) # backoff
''',
                reason=(
                    f"Se detectaron {errors} errores en el ciclo. "
                    "Optimizar el latch de reconexión del WS mediante AST patching para mejorar resiliencia."
                ),
                causal_score_est=0.65,
                confidence=0.85,
            ))

        return [proposal for proposal in proposals if proposal.causal_score_est >= 0.30]

    def evaluate_proposal(self, spec: TechnicalSpec) -> float:
        """
        Estima el impacto causal de un cambio propuesto antes de implementarlo.
        Usa heurísticas basadas en tipo de cambio, magnitud del delta y confianza.
        Retorna score en [0.0, 1.0].
        """
        score = 0.0

        # ── Base por tipo de cambio ──
        if spec.change_type == "parameter":
            # Cambios paramétricos son más seguros (reversibles, bajo riesgo)
            score += 0.30
        elif spec.change_type == "feature":
            # Cambios de features son moderados (pérdida de información posible)
            score += 0.20
        elif spec.change_type == "optimization":
            # Optimizaciones son más riesgosas
            score += 0.15

        # ── Magnitud del delta relativo ──
        if spec.old_value != 0:
            delta_ratio = abs(spec.new_value - spec.old_value) / abs(spec.old_value)
        else:
            delta_ratio = 0.0 if spec.new_value == 0 else 1.0

        # Delta pequeño (<10%) → más seguro
        if delta_ratio < 0.10:
            score += 0.25
        elif delta_ratio < 0.30:
            score += 0.20
        elif delta_ratio < 0.50:
            score += 0.15
        else:
            score += 0.05  # Delta grande → más riesgo

        # ── Feature elimination: ajustar por importancia actual ──
        if spec.change_type == "feature" and spec.new_value == 0.0:
            # Feature con importancia muy baja (<2%) → eliminar es más seguro
            if spec.old_value < 0.02:
                score += 0.20
            elif spec.old_value < 0.05:
                score += 0.15
            else:
                score += 0.05  # Feature importante → eliminar es riesgoso

        # ── Confidence del AutoProposer ──
        score += spec.confidence * 0.25  # Max 0.25 points from confidence

        # ── Causal score estimate ──
        score += spec.causal_score_est * 0.10  # Max 0.10 points from causal est.

        # Clamp to [0, 1]
        return round(min(max(score, 0.0), 1.0), 4)

    @classmethod
    def create_default(cls):
        manifest = ComponentManifest(
            name="AutoProposer",
            category="meta",
            function="Propuesta automática de mejoras arquitectónicas y paramétricas (Bucle de Evolución)",
            inputs=["PerformanceMetrics", "MarketDriftData"],
            outputs=["List[TechnicalSpec]"],
            heritage_source="legacy_vault/v1/cgalpha/core/change_proposer.py",
            heritage_contribution="Drift detection and proposal generation logic.",
            v3_adaptations="CodeCraft Phase 6 integration (TechnicalSpec/GitMetadata).",
            causal_score=0.75 # Umbral de propuesta
        )
        return cls(manifest)
