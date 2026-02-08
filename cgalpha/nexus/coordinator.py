"""
CGA_Nexus: Coordinador Supremo de CGAlpha con Redis Buffer

🎯 MISIÓN: Orquestar el flujo de información usando Redis como bus de mensajes
           entre Labs distribuidos y el LLM Inventor.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

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
    timestamp: float
    findings: Dict[str, Any]
    priority: int  # 1-10
    confidence: float  # 0.0-1.0
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class CGANexus:
    """
    Coordinador Central con Integración Redis.
    
    Acts as CONSUMER of Lab Reports via Redis Queue.
    Acts as PUBLISHER of Market Regime.
    """
    
    def __init__(self, ops_manager):
        self.ops = ops_manager
        self.reports_buffer: List[LabReport] = []
        self.current_regime = MarketRegime.UNKNOWN
        self.max_buffer_size = 1000
        
        # Redis Key Constants
        self.QUEUE_REPORTS = "queue:reports"
        self.KEY_REGIME = "state:market_regime"

    def receive_report(self, lab_name: str, findings: Dict, priority: int = 5, confidence: float = 0.5):
        """
        Ingesta un reporte. 
        En modo distribuido, esto solo ENCOLA el reporte en Redis.
        """
        report = LabReport(
            lab_name=lab_name,
            timestamp=time.time(),
            findings=findings,
            priority=priority,
            confidence=confidence
        )
        
        if self.ops.redis:
            # Usar método genérico de cola FIFO (RPUSH)
            if self.ops.redis.push_item("reports", report.to_dict()):
                logger.info(f"📤 Report queued in Redis: {lab_name} (Pri: {priority})")
            else:
                logger.error("❌ Failed to queue report in Redis (Push returned False)")
                self._add_to_local_buffer(report)
        else:
            # Modo Local
            self._add_to_local_buffer(report)

    def fetch_pending_reports(self):
        """
        Consume reportes pendientes de la cola Redis y llena el buffer local.
        """
        if not self.ops.redis:
            return

        try:
            # Consumir hasta 50 reportes por ciclo
            for _ in range(50):
                # pop_item usa BLPOP (FIFO si usamos RPUSH en push_item)
                data = self.ops.redis.pop_item("reports", timeout=1)
                
                if not data:
                    break
                
                try:
                    report = LabReport.from_dict(data)
                    self._add_to_local_buffer(report)
                except Exception as e:
                    logger.error(f"Skipping corrupted report JSON: {e}")
                    
        except Exception as e:
            logger.error(f"Error fetching reports from Redis: {e}")

    def _add_to_local_buffer(self, report: LabReport):
        """Helper para gestión de memoria local"""
        if len(self.reports_buffer) >= self.max_buffer_size:
            # Drop lowest priority first, or oldest?
            # Simple FIFO drop for now
            self.reports_buffer.pop(0) 
            
        self.reports_buffer.append(report)
        # logger.debug(f"📥 Report buffered locally: {report.lab_name}")

    def set_market_regime(self, regime: MarketRegime):
        """
        Actualiza régimen y lo publica en Redis.
        """
        self.current_regime = regime
        logger.info(f"Market regime updated: {regime.value}")
        
        if self.ops.redis:
            self.ops.redis.publish_event("market_regime", {
                "regime": regime.value,
                "timestamp": time.time()
            })
            # También guardar en Key-Value para acceso rápido
            self.ops.redis.cache_system_state(self.KEY_REGIME, {"value": regime.value})

    def synthesize_for_llm(self, max_reports: int = 10) -> str:
        """
        Sintetiza reportes (incluyendo los nuevos de Redis).
        """
        # 1. Sincronizar con Redis
        self.fetch_pending_reports()
        
        # 2. Ordenar por Prioridad * Confianza
        sorted_reports = sorted(
            self.reports_buffer,
            key=lambda r: (r.priority, r.confidence),
            reverse=True
        )[:max_reports]
        
        synthesis = {
            "market_regime": self.current_regime.value,
            "total_buffered_reports": len(self.reports_buffer),
            "synthesis_timestamp": time.time(),
            "high_priority_findings": [r.to_dict() for r in sorted_reports]
        }
        
        return json.dumps(synthesis, indent=2)

    def clear_buffer(self):
        self.reports_buffer = []
        # Opcional: ¿Limpiar Redis también?
        # self.ops.redis.client.delete(self.QUEUE_REPORTS) 
        # No, Redis es la fuente de verdad persistente hasta ser consumida.

    def get_lab_priorities(self) -> Dict[str, int]:
        # Misma lógica que antes...
        base = {
            "signal_detection": 5, "zone_physics": 5,
            "execution_optimizer": 6, "risk_barrier": 10
        }
        if self.current_regime == MarketRegime.RANGING:
            base["zone_physics"] = 8
        elif self.current_regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            base["signal_detection"] = 7
        elif self.current_regime == MarketRegime.HIGH_VOLATILITY:
            base["execution_optimizer"] = 8
        return base
