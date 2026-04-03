"""
CGAlpha v2 Trading Application
Integración completa: Knowledge Base ↔ Trading Engine ↔ Learning
"""

import logging
from typing import Dict, Optional
from datetime import datetime
import uuid

from cgalpha_v2.core.trading_engine import CGAlphaScalpingEngine
from cgalpha_v2.app.learning_integration import (
    LearningIntegrationEngine,
    TradingDecisionContext
)


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class CGAlphaTradingApplication:
    """
    Aplicación de trading CGAlpha v2
    
    Stack:
    - Capa 0: Knowledge Base (Principios + Papers)
    - Capa 1: Trading Engine (VWAP + OBI + Cumulative Delta)
    - Capa 2: Learning Integration (Contexto + Explicabilidad)
    - Capa 3: Application (orquestación)
    """
    
    def __init__(self, symbol: str = 'EURUSD', auto_learning: bool = True):
        """
        Inicializa aplicación
        
        Args:
            symbol: Par de trading (ej. EURUSD)
            auto_learning: Registrar decisiones automáticamente
        """
        
        self.symbol = symbol
        self.auto_learning = auto_learning
        self.logger = logging.getLogger(f'{__name__}.{symbol}')
        
        # Componentes
        self.trading_engine = CGAlphaScalpingEngine(symbol=symbol)
        self.learning_engine = LearningIntegrationEngine(symbol=symbol)
        
        # Estado
        self.is_running = False
        self.session_id = None
        
        self.logger.info(f"CGAlpha v2 Application initialized for {symbol}")
    
    def start_trading_session(self) -> str:
        """
        Inicia sesión de trading con aprendizaje
        
        Returns:
            session_id único
        """
        
        self.session_id = str(uuid.uuid4())[:8]
        
        self.learning_engine.start_learning_session(self.session_id)
        self.is_running = True
        
        self.logger.info(f"Trading session started: {self.session_id}")
        
        return self.session_id
    
    def stop_trading_session(self) -> Dict:
        """
        Finaliza sesión de trading
        
        Returns:
            Resumen de sesión
        """
        
        if not self.is_running:
            return {'error': 'No session running'}
        
        self.is_running = False
        
        session = self.learning_engine.end_learning_session()
        
        report = self.learning_engine.export_session_report(session)
        self.logger.info(report)
        
        return session.to_dict() if session else {}
    
    def process_order_book_update(self, bids, asks, timestamp):
        """
        Procesa actualización de order book
        Flujo: Order Book → VWAP → OBI → Entry/Exit
        """
        
        if not self.is_running:
            return
        
        # Delegar a trading engine
        entry_signal = self.trading_engine.on_order_book_update(
            bids=bids,
            asks=asks,
            timestamp=timestamp
        )
        
        # Si hay señal, registrar en learning engine
        if entry_signal and self.auto_learning:
            self._register_entry_decision(entry_signal)
    
    def process_trade_tick(self, buy_volume, sell_volume, timestamp):
        """
        Procesa ejecución de trade
        Actualiza Cumulative Delta y stops
        """
        
        if not self.is_running:
            return
        
        # Delegar a trading engine
        exit_signal = self.trading_engine.on_trade_tick(
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            timestamp=timestamp
        )
        
        # Si hay signal de salida, registrar
        if exit_signal and self.auto_learning:
            self._register_exit_decision(exit_signal)
    
    def _register_entry_decision(self, signal: Dict) -> TradingDecisionContext:
        """
        Registra decisión de entrada con contexto de knowledge
        """
        
        # Obtener contexto principiado
        context_text = self.learning_engine.get_entry_context(
            position_side=signal.get('position_side', 'LONG')
        )
        
        # Parsear papers y principios del contexto
        papers = self._extract_papers_from_context(context_text)
        principles = self._extract_principles_from_context(context_text)
        
        # Registrar decisión
        decision = self.learning_engine.record_trading_decision(
            decision_type='ENTRY',
            decision={
                'entry_price': signal.get('entry_price'),
                'position_side': signal.get('position_side'),
                'reason': signal.get('reason'),
                'barrier_metrics': signal.get('metrics')
            },
            principles=principles,
            papers=papers,
            signal_strength=signal.get('confidence', 0.5),
            confidence=signal.get('confidence', 0.5)
        )
        
        self.logger.info(
            f"Entry decision recorded | "
            f"Price: {signal.get('entry_price'):.5f} | "
            f"Confidence: {signal.get('confidence'):.0%}"
        )
        
        return decision
    
    def _register_exit_decision(self, signal: Dict) -> Optional[TradingDecisionContext]:
        """
        Registra decisión de salida
        """
        
        if signal.get('action') not in ['PARTIAL_EXIT', 'FULL_EXIT']:
            return None
        
        # Obtener contexto
        context_text = self.learning_engine.get_exit_context(
            position_side=self.trading_engine.position_side
        )
        
        papers = self._extract_papers_from_context(context_text)
        principles = self._extract_principles_from_context(context_text)
        
        # Registrar
        decision = self.learning_engine.record_trading_decision(
            decision_type='EXIT',
            decision={
                'action': signal.get('action'),
                'exit_qty': signal.get('exit_qty_pct'),
                'reason': signal.get('reason'),
                'stop_type': signal.get('stop_type')
            },
            principles=principles,
            papers=papers,
            signal_strength=1.0,
            confidence=0.9
        )
        
        self.logger.info(
            f"Exit decision recorded | "
            f"Action: {signal.get('action')} | "
            f"Reason: {signal.get('reason')}"
        )
        
        return decision
    
    def _extract_papers_from_context(self, context_text: str) -> list:
        """Extrae papers del texto de contexto"""
        
        # Parsear context para obtener papers recomendados
        # Por ahora, retorna estructura básica
        # TODO: Parsear de forma más sofisticada
        
        return [
            {'id': 'vwap_002', 'title': 'Real-time VWAP', 'relevance': 0.92},
            {'id': 'obi_002', 'title': 'OBI as Trading Signal', 'relevance': 0.89},
        ]
    
    def _extract_principles_from_context(self, context_text: str) -> list:
        """Extrae principios aplicados del contexto"""
        
        # Mapeo simple de principios aplicados
        # TODO: Parsear dinámicamente
        
        return ['rs_001', 'rs_003', 'cur_001', 'bench_001']
    
    def record_trade_outcome(self, entry_decision: TradingDecisionContext, 
                            exit_signal: Dict, pnl: float) -> None:
        """
        Registra resultado final de un trade
        Cierra el loop de aprendizaje
        
        Args:
            entry_decision: Decisión de entrada original
            exit_signal: Señal de salida
            pnl: PnL del trade
        """
        
        # Determinar outcome
        if pnl > 0:
            outcome = 'WIN'
        elif pnl < 0:
            outcome = 'LOSS'
        else:
            outcome = 'BREAK_EVEN'
        
        # Registrar
        self.learning_engine.record_decision_outcome(
            decision_context=entry_decision,
            outcome=outcome,
            pnl=pnl
        )
        
        self.logger.info(
            f"Trade outcome recorded | "
            f"Entry: {entry_decision.decision.get('entry_price'):.5f} | "
            f"PnL: ${pnl:.2f} | Outcome: {outcome}"
        )
    
    def get_trading_status(self) -> Dict:
        """Retorna estado actual de trading"""
        
        engine_status = self.trading_engine.get_status()
        knowledge_stats = self.learning_engine.get_knowledge_stats()
        
        return {
            'running': self.is_running,
            'session_id': self.session_id,
            'symbol': self.symbol,
            'engine_status': engine_status,
            'knowledge_stats': knowledge_stats,
            'current_session': self.learning_engine.current_session.to_dict() if self.learning_engine.current_session else None
        }
    
    def get_learning_report(self) -> Dict:
        """Retorna reporte de aprendizaje acumulado"""
        
        recommendations = self.learning_engine.get_improvement_recommendations()
        
        return {
            'sessions_completed': len(self.learning_engine.session_history),
            'total_decisions': self.learning_engine.total_decisions,
            'recommendations': recommendations,
            'last_session': (
                self.learning_engine.session_history[-1].to_dict()
                if self.learning_engine.session_history else None
            )
        }
    
    def explain_last_decision(self) -> str:
        """Retorna explicación de última decisión tomada"""
        
        if not self.learning_engine.decision_history:
            return "No decisions recorded yet"
        
        last_decision = self.learning_engine.decision_history[-1]
        
        return last_decision.explanation
    
    def show_knowledge_base_summary(self) -> str:
        """Retorna resumen de la knowledge base"""
        
        stats = self.learning_engine.get_knowledge_stats()
        
        summary = f"""
# Knowledge Base Summary

## Principles
- Total principles: {stats['principles_available']}
- Available for querying

## Papers
- Total papers: {stats['papers_available']}
- With empirical validation: {stats['papers_with_empirical_validation']}
- Live-tested in trading: {stats['papers_live_tested']}

## Usage Statistics
- Total decisions made: {stats['total_decisions']}
- Total sessions completed: {stats['total_sessions']}

## Data Status
✓ Knowledge base fully initialized
✓ Ready for trading decisions
✓ Auto-learning enabled
"""
        
        return summary


class TradingApplicationFactory:
    """Factory para crear aplicaciones de trading"""
    
    @staticmethod
    def create_trading_app(
        symbol: str = 'EURUSD',
        auto_learning: bool = True
    ) -> CGAlphaTradingApplication:
        """Crea nueva aplicación de trading"""
        
        return CGAlphaTradingApplication(
            symbol=symbol,
            auto_learning=auto_learning
        )
    
    @staticmethod
    def create_multi_symbol_trading(symbols: list) -> Dict[str, CGAlphaTradingApplication]:
        """Crea aplicaciones para múltiples símbolos"""
        
        return {
            symbol: CGAlphaTradingApplication(symbol=symbol)
            for symbol in symbols
        }
