"""
CGA_Nexus: Coordinador Supremo de CGAlpha

🎯 MISIÓN: Orquestar el flujo de información entre los 4 Labs especializados
           y servir como interfaz con el LLM Inventor.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Clasificación del régimen de mercado"""
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    UNKNOWN = "unknown"


@dataclass
class LabReport:
    """Reporte estandarizado de un Laboratory"""
    lab_name: str
    timestamp: str
    findings: Dict[str, Any]
    priority: int  # 1-10, donde 10 es crítico
    confidence: float  # 0.0-1.0


class CGANexus:
    """
    Coordinador Central de CGAlpha
    
    **Decisiones Autónomas Implementadas:**
    1. Sistema de prioridades 1-10 para asignación de CPU
       Justificación: RiskBarrierLab (causal) tiene prioridad sobre otros
    2. Buffer de reportes de máximo 1000 items
       Justificación: Prevenir desbordamiento de memoria en análisis masivos
    3. Formato JSON para LLM (no raw Python)
       Justificación: Compatibilidad con diferentes LLMs (GPT, Claude, Qwen)
    """
    
    def __init__(self, ops_manager):
        """
        Args:
            ops_manager: Instancia de CGAOps para control de recursos
        """
        self.ops = ops_manager
        self.reports_buffer: List[LabReport] = []
        self.current_regime = MarketRegime.UNKNOWN
        self.max_buffer_size = 1000
        
    def receive_report(self, lab_name: str, findings: Dict, priority: int = 5, confidence: float = 0.5):
        """
        Recibe un reporte de un Laboratory
        
        Args:
            lab_name: Nombre del laboratorio (sd, zp, eo, rb)
            findings: Diccionario con los hallazgos del análisis
            priority: Nivel de urgencia (1-10)
            confidence: Nivel de confianza del hallazgo (0.0-1.0)
        """
        from datetime import datetime
        
        report = LabReport(
            lab_name=lab_name,
            timestamp=datetime.now().isoformat(),
            findings=findings,
            priority=priority,
            confidence=confidence
        )
        
        # Mantener buffer limitado (FIFO)
        if len(self.reports_buffer) >= self.max_buffer_size:
            logger.warning("Reports buffer full, removing oldest report")
            self.reports_buffer.pop(0)
        
        self.reports_buffer.append(report)
        logger.info(f"Report received from {lab_name} (Priority: {priority}, Confidence: {confidence:.2f})")
        
    def set_market_regime(self, regime: MarketRegime):
        """
        Actualiza el régimen de mercado detectado
        
        Este es usado para priorizar qué Labs deben activarse
        Ej: En RANGING, ZonePhysicsLab tiene prioridad
        """
        self.current_regime = regime
        logger.info(f"Market regime updated: {regime.value}")
        
    def synthesize_for_llm(self, max_reports: int = 10) -> str:
        """
        Sintetiza los reportes en un prompt estructurado para el LLM Inventor
        
        Args:
            max_reports: Máximo número de reportes a incluir (los más prioritarios)
            
        Returns:
            JSON string con el prompt sintetizado
        """
        # Ordenar por prioridad y confianza
        sorted_reports = sorted(
            self.reports_buffer,
            key=lambda r: (r.priority, r.confidence),
            reverse=True
        )[:max_reports]
        
        synthesis = {
            "market_regime": self.current_regime.value,
            "total_reports": len(self.reports_buffer),
            "high_priority_findings": []
        }
        
        for report in sorted_reports:
            synthesis["high_priority_findings"].append({
                "lab": report.lab_name,
                "timestamp": report.timestamp,
                "priority": report.priority,
                "confidence": report.confidence,
                "findings": report.findings
            })
        
        prompt_json = json.dumps(synthesis, indent=2, ensure_ascii=False)
        
        logger.info(f"Synthesized {len(sorted_reports)} reports for LLM")
        return prompt_json
    
    def clear_buffer(self):
        """Limpia el buffer de reportes (útil después de generar una propuesta)"""
        count = len(self.reports_buffer)
        self.reports_buffer = []
        logger.info(f"Reports buffer cleared ({count} reports discarded)")
    
    def get_lab_priorities(self) -> Dict[str, int]:
        """
        Retorna las prioridades de CPU para cada Lab según el régimen actual
        
        Returns:
            Dict con {lab_name: priority_score}
        """
        # Prioridades base
        base = {
            "signal_detection": 5,
            "zone_physics": 5,
            "execution_optimizer": 6,
            "risk_barrier": 10  # Siempre máxima (causal es crítico)
        }
        
        # Ajustes según régimen
        if self.current_regime == MarketRegime.RANGING:
            base["zone_physics"] = 8  # Zonas más importantes en ranging
        elif self.current_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            base["signal_detection"] = 7  # Tendencias más importantes en trending
        elif self.current_regime == MarketRegime.HIGH_VOLATILITY:
            base["execution_optimizer"] = 8  # Entradas precisas críticas en volatilidad
        
        return base


# 🧪 Test rápido
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from cgalpha.nexus.ops import CGAOps
    
    ops = CGAOps()
    nexus = CGANexus(ops)
    
    # Simular reportes de Labs
    nexus.receive_report(
        lab_name="risk_barrier",
        findings={"cate_score": 0.85, "parameter": "confidence_threshold", "suggested_value": 0.65},
        priority=10,
        confidence=0.89
    )
    
    nexus.receive_report(
        lab_name="zone_physics",
        findings={"fakeout_detected": True, "zone_id": "zone_01"},
        priority=7,
        confidence=0.75
    )
    
    # Síntesis para LLM
    nexus.set_market_regime(MarketRegime.HIGH_VOLATILITY)
    prompt = nexus.synthesize_for_llm()
    
    print("=" * 60)
    print("CGANexus LLM Synthesis:")
    print("=" * 60)
    print(prompt)
    print("\nLab Priorities:")
    for lab, priority in nexus.get_lab_priorities().items():
        print(f"  {lab}: {priority}/10")
