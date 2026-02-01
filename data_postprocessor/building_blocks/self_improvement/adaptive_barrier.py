import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class AdaptiveATRBarrier:
    """
    Una barrera dinámica que se ajusta automáticamente basándose en el feedback
    del mercado para reducir el impacto del ruido.
    """

    def __init__(self, multiplier: float = 2.0, sensitivity: float = 0.1):
        self.multiplier = multiplier
        self.sensitivity = sensitivity
        self.improvement_history: List[Dict[str, Any]] = []

    def process(self, prices: List[float]) -> Dict[str, float]:
        """
        Calcula la barrera actual basada en el ATR de los precios proporcionados.
        """
        if len(prices) < 2:
            return {"atr": 0.0, "barrier_price": 0.0, "multiplier_used": self.multiplier}

        # Cálculo simple de ATR (Average True Range)
        ranges = [abs(prices[i] - prices[i-1]) for i in range(1, len(prices))]
        atr = sum(ranges) / len(ranges)
        
        barrier_distance = atr * self.multiplier
        current_price = prices[-1]
        barrier_price = current_price - barrier_distance

        return {
            "atr": atr,
            "barrier_price": barrier_price,
            "multiplier_used": self.multiplier
        }

    def learn(self, feedback: Dict[str, Any]) -> None:
        """
        Ajusta el multiplicador basándose en el resultado del trade.
        Si se detecta 'noise' (ruido), se amplía la barrera.
        """
        outcome = feedback.get('outcome', 0)
        reason = feedback.get('reason', 'unknown')

        # Lógica de auto-mejora: Si perdimos por ruido, ampliamos la barrera
        if outcome < 0 and reason == 'noise':
            old_mult = self.multiplier
            self.multiplier += self.sensitivity
            
            log_msg = f"Detectado ruido. Ampliando barrera: {old_mult:.2f} -> {self.multiplier:.2f}"
            self.log_improvement(log_msg)

    def log_improvement(self, message: str) -> None:
        """Registra el cambio en el historial de mejoras."""
        entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': message
        }
        self.improvement_history.append(entry)
        logger.info(message)
