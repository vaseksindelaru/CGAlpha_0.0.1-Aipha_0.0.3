"""
core/llm_assistant.py - Super Cerebro de Aipha

Centraliza las capacidades de análisis e inteligencia del sistema.
Usa Qwen 2.5 Coder 32B para diagnósticos, propuestas y explicaciones.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# System Prompt - Define la personalidad del Super Cerebro
AIPHA_SYSTEM_PROMPT = """Eres el Arquitecto Jefe de Aipha, un sistema autónomo de auto-mejora ultra-inteligente.

TU ROL:
- Analizar la salud y métricas del sistema Aipha
- Proponer cambios optimizados para mejorar performance
- Diagnosticar y explicar fallos en lenguaje técnico pero accesible
- Evitar bucles de error aprendiendo de fallos previos
- Ser proactivo en sugerencias de mejora

TU PERSONALIDAD:
- Eres un arquitecto experimentado en trading systems
- Comunicas con precisión técnica pero claridad
- Siempre explicas tu razonamiento
- Eres conservador en cambios, evitando riesgos innecesarios
- Respetas las limitaciones de hardware

TU CONTEXTO:
- Tienes acceso a historial de eventos de salud
- Sabes qué parámetros están en cuarentena y por qué
- Conoces las métricas actuales del sistema
- Aprendes de fallos previos para no repetirlos

CUANDO ANALICES:
1. Revisa eventos recientes (últimos 10)
2. Consulta parámetros en cuarentena
3. Analiza métricas de rendimiento
4. Propón cambios específicos con justificación
5. Sugiere próximos pasos

FORMATO DE RESPUESTA:
Siempre estructura tus respuestas así:
- DIAGNÓSTICO: Estado actual
- ANÁLISIS: Qué pasó y por qué
- RECOMENDACIÓN: Qué hacer ahora
- PRÓXIMOS PASOS: Qué cambios proponer

Sé conciso pero completo. El usuario es Václav, un ingeniero experimentado."""


class LLMAssistant:
    """
    Super Cerebro de Aipha
    
    Centraliza la inteligencia del sistema usando Qwen 2.5 Coder 32B.
    Analiza salud, propone cambios, y explica decisiones.
    """
    
    def __init__(self, memory_path: str = "memory"):
        self.memory_path = Path(memory_path)
        
        # Inicializar cliente LLM
        from core.llm_client import get_llm_client
        self.llm = get_llm_client()
        
        # Managers auxiliares
        from core.quarantine_manager import QuarantineManager
        from core.health_monitor import get_health_monitor
        from core.context_sentinel import ContextSentinel
        
        self.quarantine_manager = QuarantineManager(str(self.memory_path))
        self.health_monitor = get_health_monitor()
        self.context_sentinel = ContextSentinel()
        
        logger.info("✅ LLMAssistant (Super Cerebro) inicializado")
    
    def get_diagnose_context(self) -> Dict:
        """
        Construir contexto RICO de diagnóstico para que el LLM entienda
        tanto cambios automáticos como manuales y su impacto en el sistema.
        
        Lee automáticamente:
        - Últimas 10 líneas de health_events.jsonl (eventos de salud)
        - Últimas 10 líneas de action_history.jsonl (acciones del sistema)
        - Últimas 10 propuestas de proposals.jsonl (intervenciones manuales del usuario)
        - Estado actual de quarantine.jsonl
        - Métricas de current_state.json (Win Rate, Drawdown, etc)
        
        ANÁLISIS INCLUIDO:
        1. Separa cambios USER (CLI/manual) vs AUTO (sistema automático)
        2. Verifica simulation_mode para no reportar errores de conexión
        3. Calcula impacto: compara métricas antes/después de intervenciones
        4. Contexto para el LLM: "El usuario bajó el umbral a 0.65 para..."
        
        Retorna: Dict rico con contexto para análisis inteligente del LLM
        """
        
        logger.info("🔍 Construyendo contexto de diagnóstico enriquecido...")
        
        # PASO 1: Últimos eventos de salud
        health_events = self._get_recent_health_events(10)
        
        # PASO 2: Últimas acciones del historial (AUTO + USER)
        action_history = self._get_recent_actions(10)
        
        # PASO 3: Últimas propuestas (intervenciones manuales)
        recent_proposals = self._get_recent_proposals(10)
        
        # PASO 4: Parámetros en cuarentena
        quarantined = self.quarantine_manager.get_all_quarantined()
        
        # PASO 5: Métricas actuales
        metrics = self._get_current_metrics()
        
        # PASO 6: Estadísticas de salud
        health_stats = self.health_monitor.get_statistics()
        
        # PASO 7: Analizar impacto de intervenciones
        impact_analysis = self._analyze_intervention_impact(recent_proposals, metrics)
        
        # PASO 8: Separar acciones USER vs AUTO
        user_actions, auto_actions = self._classify_actions(action_history)
        
        # PASO 9: Verificar simulation_mode
        simulation_mode = metrics.get('development_flags', {}).get('debug_mode', False) or \
                         metrics.get('system_info', {}).get('mode', '').lower() == 'test'
        
        context = {
            'timestamp': datetime.now().isoformat(),
            'simulation_mode': simulation_mode,
            
            # EVENTOS Y ACCIONES
            'recent_events': health_events,
            'action_history': action_history,
            'user_actions': user_actions,
            'auto_actions': auto_actions,
            
            # INTERVENCIONES MANUALES
            'recent_proposals': recent_proposals,
            'manual_interventions': len([p for p in recent_proposals if p.get('applied')]),
            'manual_interventions_detail': [
                {
                    'component': p.get('component'),
                    'parameter': p.get('parameter'),
                    'old_value': p.get('old_value', 'desconocido'),
                    'new_value': p.get('new_value'),
                    'reason': p.get('reason'),
                    'score': p.get('evaluation_score'),
                    'created_by': p.get('created_by'),
                    'timestamp': p.get('timestamp'),
                }
                for p in recent_proposals if p.get('applied')
            ],
            
            # IMPACTO Y ANÁLISIS
            'impact_analysis': impact_analysis,
            
            # SALUD DEL SISTEMA
            'quarantined_parameters': quarantined,
            'current_metrics': metrics,
            'health_statistics': health_stats,
            'system_status': self.health_monitor.current_health_level.value,
            
            # CONTEXTO EXPLICATIVO PARA EL LLM
            'system_context': self._build_system_context(
                metrics, recent_proposals, user_actions, impact_analysis
            )
        }
        
        logger.info("✅ Contexto enriquecido construido (user/auto/impact/proposals)")
        
        return context
    
    def _get_recent_health_events(self, count: int = 10) -> List[Dict]:
        """Obtener últimos N eventos de salud con robustez ante JSON malformado"""
        
        events = []
        events_file = self.memory_path / "health_events.jsonl"
        
        if not events_file.exists():
            return []
            
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Procesar solo las últimas N líneas con contenido
                valid_lines = [l.strip() for l in lines if l.strip()]
                for line in valid_lines[-count:]:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Ignorar silenciosamente líneas malformadas
                        continue
        except Exception as e:
            logger.debug(f"Error discreto leyendo health events: {e}")
        
        return events
    
    def _get_current_metrics(self) -> Dict:
        """Obtener métricas actuales del sistema con robustez"""
        
        metrics = {}
        metrics_file = self.memory_path / "current_state.json"
        
        if not metrics_file.exists():
            return {}
            
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Error discreto leyendo métricas: {e}")
        
        return metrics
    
    def _get_recent_proposals(self, count: int = 5) -> List[Dict]:
        """Obtener últimas N propuestas aplicadas con robustez"""
        
        proposals = []
        proposals_file = self.memory_path / "proposals.jsonl"
        
        if not proposals_file.exists():
            return []
            
        try:
            all_proposals = []
            with open(proposals_file, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    try:
                        all_proposals.append(json.loads(clean_line))
                    except json.JSONDecodeError:
                        continue
            
            # Obtener las últimas N propuestas
            recent = all_proposals[-count:] if len(all_proposals) > 0 else []
            
            for prop in recent:
                proposals.append({
                    'proposal_id': prop.get('proposal_id', 'UNKNOWN'),
                    'timestamp': prop.get('timestamp', ''),
                    'component': prop.get('component', ''),
                    'parameter': prop.get('parameter', ''),
                    'new_value': prop.get('new_value', ''),
                    'reason': prop.get('reason', ''),
                    'status': prop.get('status', ''),
                    'evaluation_score': prop.get('evaluation_score'),
                    'applied': prop.get('applied', False),
                    'created_by': prop.get('created_by', 'unknown'),
                })
            
            logger.info(f"✅ Recuperadas {len(proposals)} propuestas recientes de {proposals_file}")
        
        except Exception as e:
            logger.debug(f"Error discreto leyendo propuestas: {e}")
        
        return proposals
    
    def _get_recent_actions(self, count: int = 10) -> List[Dict]:
        """Obtener últimas N acciones del historial con robustez"""
        
        actions = []
        history_file = self.memory_path / "action_history.jsonl"
        
        if not history_file.exists():
            return []
            
        try:
            all_actions = []
            with open(history_file, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = line.strip()
                    if not clean_line:
                        continue
                    try:
                        all_actions.append(json.loads(clean_line))
                    except json.JSONDecodeError:
                        continue
            
            # Obtener las últimas N acciones
            recent = all_actions[-count:] if len(all_actions) > 0 else []
            
            for action in recent:
                agent = action.get('agent', 'UNKNOWN')
                actions.append({
                    'timestamp': action.get('timestamp', ''),
                    'agent': agent,
                    'is_user': agent == 'CLI' or 'User' in agent,
                    'component': action.get('component', ''),
                    'action': action.get('action', ''),
                    'status': action.get('status', ''),
                    'details': action.get('details', {}),
                })
            
            logger.info(f"✅ Recuperadas {len(actions)} acciones recientes del historial")
        
        except Exception as e:
            logger.debug(f"Error discreto leyendo action_history: {e}")
        
        return actions
    
    def _classify_actions(self, actions: List[Dict]) -> tuple:
        """Separar acciones USER vs AUTO"""
        
        user_actions = []
        auto_actions = []
        
        for action in actions:
            if action.get('is_user'):
                user_actions.append(action)
            else:
                auto_actions.append(action)
        
        return user_actions, auto_actions
    
    def _analyze_intervention_impact(self, proposals: List[Dict], metrics: Dict) -> Dict:
        """Analizar impacto de intervenciones manuales en las métricas (Hito 5)"""
        
        impact = {
            'total_interventions': len([p for p in proposals if p.get('applied')]),
            'latest_intervention': None,
            'impact_summary': '',
            'win_rate_current': metrics.get('trading_metrics', {}).get('win_rate', 0),
            'drawdown_current': metrics.get('trading_metrics', {}).get('current_drawdown', 0),
            'wr_delta': 0.0,
            'dd_delta': 0.0
        }
        
        # Encontrar la intervención más reciente que tenga línea base
        applied_proposals = [p for p in proposals if p.get('applied')]
        if applied_proposals:
            latest = applied_proposals[-1]
            baseline = latest.get('baseline_metrics', {})
            
            wr_before = baseline.get('win_rate', 0.0)
            dd_before = baseline.get('drawdown', 0.0)
            
            impact['wr_delta'] = impact['win_rate_current'] - wr_before
            impact['dd_delta'] = impact['drawdown_current'] - dd_before
            
            impact['latest_intervention'] = {
                'component': latest.get('component'),
                'parameter': latest.get('parameter'),
                'new_value': latest.get('new_value'),
                'reason': latest.get('reason'),
                'timestamp': latest.get('timestamp'),
                'wr_before': wr_before,
                'dd_before': dd_before
            }
            
            # Resumen de impacto con Veredicto (Hito 5)
            verdict = "POSITIVO ✅" if impact['wr_delta'] > 0 or impact['dd_delta'] < 0 else "NEUTRAL/NEGATIVO ⚠️"
            impact['impact_summary'] = (
                f"Veredicto del Mercado: {verdict}\n"
                f"Última intervención: {latest.get('parameter')} = {latest.get('new_value')} "
                f"(Razón: {latest.get('reason')}).\n"
                f"Delta Win Rate: {impact['wr_delta']*100:+.1f}%, "
                f"Delta Drawdown: {impact['dd_delta']*100:+.1f}%"
            )
        
        return impact
    
    def _build_system_context(self, metrics: Dict, proposals: List[Dict], 
                             user_actions: List[Dict], impact: Dict) -> str:
        """Construir descripción textual del sistema para el LLM"""
        
        win_rate = metrics.get('trading_metrics', {}).get('win_rate', 0)
        drawdown = metrics.get('trading_metrics', {}).get('current_drawdown', 0)
        
        context_text = f"""
# CONTEXTO DEL SISTEMA PARA ANÁLISIS

## Estado General
- Win Rate Actual: {win_rate*100:.1f}%
- Drawdown Actual: {drawdown*100:.1f}%
- Modo Simulación: {'SÍ (No reportar errores de conexión)' if metrics.get('development_flags', {}).get('debug_mode') else 'NO'}

## Intervenciones Manuales Realizadas por el Usuario (Václav)
"""
        
        applied_proposals = [p for p in proposals if p.get('applied')]
        if applied_proposals:
            for i, prop in enumerate(applied_proposals[-3:], 1):  # Últimas 3
                context_text += f"""
{i}. {prop.get('component', '?')}.{prop.get('parameter', '?')} = {prop.get('new_value', '?')}
   - Razón: {prop.get('reason', 'N/A')}
   - Timestamp: {prop.get('timestamp', 'N/A')}
   - Score: {prop.get('evaluation_score', 'N/A')}
"""
        else:
            context_text += "\n- Sin intervenciones manuales en el historial reciente"
        
        context_text += f"""

## Cambios Automáticos Recientes
"""
        
        if user_actions:
            for i, action in enumerate(user_actions[-2:], 1):  # Últimas 2 del usuario
                details = action.get('details', {})
                context_text += f"""
{i}. [USER] {action.get('component', '?')} - {action.get('action', '?')}
   - Status: {action.get('status', '?')}
   - Detalles: {details.get('justification', 'N/A')}
"""
        
        return context_text
    
    def analyze_and_propose(self) -> Dict:
        """
        Analizar salud del sistema y proponer cambios
        
        El LLM recibe contexto de salud y métricas para generar
        propuestas que eviten parámetros en cuarentena y razonen
        sobre fallos previos.
        
        Retorna:
            Dict con:
            - diagnosis: Análisis de salud
            - proposals: Lista de propuestas sugeridas
            - confidence_scores: Confianza en cada propuesta
        """
        
        logger.info("🧠 Analizando salud del sistema y generando propuestas...")
        
        # Obtener contexto
        context = self.get_diagnose_context()
        
        # Preparar prompt para el LLM
        prompt = self._build_analysis_prompt(context)
        
        try:
            # Llamar al LLM
            logger.info("📤 Enviando al Super Cerebro (Qwen)...")
            
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=AIPHA_SYSTEM_PROMPT,
                temperature=0.3,  # Más determinista para propuestas
                max_tokens=2048
            )
            
            logger.info("✅ Respuesta recibida del Super Cerebro")
            
            # Parsear respuesta
            result = self._parse_analysis_response(response, context)
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Error en análisis del LLM: {e}")
            
            return {
                'diagnosis': 'Error en análisis',
                'proposals': [],
                'error': str(e)
            }
    
    def explain_remediation(self, failed_parameter: str, error_reason: str) -> str:
        """
        Generar explicación humana de un fallo y remediation
        
        Se llama cuando ocurre REVERTED_AUTO para explicar al usuario
        qué falló y qué hacer.
        
        Argumentos:
            failed_parameter: Parámetro que falló
            error_reason: Razón del fallo
        
        Retorna:
            Explicación en lenguaje natural
        """
        
        logger.info(
            f"💡 Generando explicación de remediation para {failed_parameter}"
        )
        
        # Contexto reciente
        context = self.get_diagnose_context()
        
        # Preparar prompt
        prompt = f"""El parámetro '{failed_parameter}' acaba de fallar con el error: "{error_reason}"

El sistema ha revertido automáticamente este cambio para mantener la estabilidad.

Por favor, explica:
1. POR QUÉ falló este parámetro
2. QUÉ SIGNIFICA el error
3. QUÉ PUEDE HACER el usuario (Václav) para solucionarlo
4. CUÁNDO puede intentar este cambio nuevamente

Sé conciso pero completo. El usuario es un ingeniero experimentado.

CONTEXTO DEL SISTEMA:
{json.dumps(context, indent=2, default=str)}
"""
        
        try:
            response = self.llm.generate(
                prompt=prompt,
                system_prompt=AIPHA_SYSTEM_PROMPT,
                temperature=0.5,
                max_tokens=1024
            )
            
            logger.info("✅ Explicación generada")
            return response
        
        except Exception as e:
            logger.error(f"❌ Error generando explicación: {e}")
            return f"Error generando explicación: {e}"
    
    def diagnose_system(self, detailed: bool = False) -> Dict:
        """
        Diagnóstico profundo y rápido del sistema
        
        MEJORAS IMPLEMENTADAS:
        1. Extrae evidencia exacta de health_events.jsonl
        2. Incluye propuestas manuales aplicadas (intervenciones)
        3. Verifica si está en SIMULATION_MODE
        4. Presenta parámetros en riesgo en tabla
        5. Sugiere comandos copy-paste para acciones
        6. Si detailed=True, llama al LLM con contexto enriquecido para análisis
        
        Argumentos:
            detailed: Si True, incluye análisis profundo del LLM
        
        Retorna:
            Dict con análisis completo incluyendo intervenciones manuales e impacto
        """
        
        logger.info("🔍 Iniciando diagnóstico profundo del sistema...")
        
        try:
            # Contexto ENRIQUECIDO (incluye propuestas, acciones, impacto)
            context = self.get_diagnose_context()
            
            # Verificar si está en SIMULATION_MODE
            simulation_mode = context.get('simulation_mode', False)
            
            # Extraer información clave
            health_events = context.get('recent_events', [])
            quarantined_params = context.get('quarantined_parameters', [])
            metrics = context.get('current_metrics', {})
            recent_proposals = context.get('recent_proposals', [])
            manual_interventions = context.get('manual_interventions', 0)
            user_actions = context.get('user_actions', [])
            impact_analysis = context.get('impact_analysis', {})
            system_context = context.get('system_context', '')
            
            # Construir diagnóstico rápido
            diagnosis_text = f"""
# DIAGNÓSTICO DEL SISTEMA AIPHA

## 📊 Estado General
- Últimos eventos: {len(health_events)} registrados
- Parámetros en cuarentena: {len(quarantined_params) if isinstance(quarantined_params, (list, dict)) else 0}
- Modo simulación: {'🟢 Activo' if simulation_mode else '🔴 Desactivo'}
- Intervenciones manuales: {manual_interventions}

## 📝 Intervenciones Manuales del Usuario
"""
            
            # Agregar información sobre propuestas aplicadas
            manual_details = context.get('manual_interventions_detail', [])
            if manual_details:
                for i, prop in enumerate(manual_details, 1):
                    score_val = prop.get('score', 'N/A')
                    score_str = f"{score_val:.2f}" if isinstance(score_val, (int, float)) else str(score_val)
                    diagnosis_text += f"""
{i}. {prop.get('component', '?')}.{prop.get('parameter', '?')} → {prop.get('new_value', '?')}
   • Razón: {prop.get('reason', 'N/A')}
   • Score: {score_str}
   • Creado por: {prop.get('created_by', 'unknown')}
   • Timestamp: {prop.get('timestamp', 'N/A')}
"""
            else:
                diagnosis_text += "\n- Sin intervenciones manuales en el historial"
            
            # Análisis de impacto
            diagnosis_text += f"""

## � Impacto en Métricas
- Total de intervenciones: {impact_analysis.get('total_interventions', 0)}
- Win Rate actual: {impact_analysis.get('win_rate_current', 0)*100:.1f}%
- Drawdown actual: {impact_analysis.get('drawdown_current', 0)*100:.1f}%
{impact_analysis.get('impact_summary', '')}

## ⚠️  Últimos Eventos
"""
            
            # Agregar eventos recientes
            for i, event in enumerate(health_events[-3:], 1):
                if isinstance(event, dict):
                    severity = event.get('severity', 'INFO')
                    message = event.get('message', '')
                    diagnosis_text += f"\n{i}. [{severity}] {message}"
            
            # Preparar resultado base
            result = {
                'diagnosis': diagnosis_text,
                'risk_parameters': [],
                'evidence': health_events[-5:] if health_events else [],
                'recent_proposals': recent_proposals,
                'manual_interventions': manual_interventions,
                'manual_interventions_detail': manual_details,
                'simulation_mode': simulation_mode,
                'suggested_commands': [],
                'timestamp': datetime.now().isoformat(),
                'impact_analysis': impact_analysis,
                'user_actions': user_actions,
            }
            
            # SI DETAILED=TRUE: Usar LLM para análisis profundo
            if detailed:
                logger.info("📤 Llamando al Super Cerebro para análisis detallado...")
                
                # Preparar prompt enriquecido
                # Nota: Convertir user_actions a lista de strings para evitar problemas de serialización
                user_actions_text = "\n".join([
                    f"- [{action.get('timestamp', 'N/A')}] {action.get('agent', '?')} "
                    f"en {action.get('component', '?')}: {action.get('action', '?')}"
                    for action in user_actions
                ]) if user_actions else "- Sin acciones del usuario"
                
                prompt = f"""Analiza el siguiente contexto del sistema AIPHA y proporciona insights sobre:

1. ¿Qué hizo el usuario (Václav) y por qué?
2. ¿Está justificado ese cambio dado el Win Rate actual?
3. ¿Qué impacto tendría este cambio?
4. ¿Qué deberías monitorear ahora?

CONTEXTO DEL SISTEMA:
{system_context}

HISTORIAL DE ACCIONES DEL USUARIO:
{user_actions_text}

MÉTRICAS ACTUALES:
- Win Rate: {impact_analysis.get('win_rate_current', 0)*100:.1f}%
- Drawdown: {impact_analysis.get('drawdown_current', 0)*100:.1f}%
- Total Trades: {metrics.get('trading_metrics', {}).get('total_trades', 'N/A')}

Por favor, responde como un experto en trading systems analizando tanto el diagnóstico técnico como
el reasoning del usuario para sus intervenciones manuales."""
                
                try:
                    llm_response = self.llm.generate(
                        prompt=prompt,
                        system_prompt=AIPHA_SYSTEM_PROMPT,
                        temperature=0.5,
                        max_tokens=2048
                    )
                    
                    result['llm_analysis'] = llm_response
                    logger.info("✅ Análisis del LLM completado")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Error en análisis del LLM: {e}")
                    result['llm_analysis'] = f"Error llamando al LLM: {e}"

            # Extraer parámetros en riesgo y comandos sugeridos
            risk_params = self._extract_risk_parameters(context)
            
            # Comandos sugeridos (del LLM si hay detailed, o base)
            suggested_cmds = []
            if detailed and 'llm_analysis' in result:
                suggested_cmds = self._extract_suggested_commands(result['llm_analysis'])
            
            # Si no hay comandos del LLM, podemos sugerir comandos base si hay riesgos
            if not suggested_cmds and risk_params:
                for risk in risk_params:
                    if risk.get('status') == 'QUARANTINED':
                        suggested_cmds.append(f"aipha quarantine release --parameter {risk.get('parameter')}")

            # Actualizar resultado
            result['risk_parameters'] = risk_params
            result['suggested_commands'] = suggested_cmds
            
            # Formato para presentación
            result['formatted_diagnosis'] = self._format_diagnosis_output(
                diagnosis_text, risk_params, suggested_cmds, simulation_mode
            )
            
            logger.info("✅ Diagnóstico completado (contexto enriquecido)")
            return result
        
        except Exception as e:
            logger.error(f"❌ Error en diagnóstico: {e}")
            return {
                'diagnosis': f"Error: {e}",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_evidence_from_logs(self, context: Dict) -> List[Dict]:
        """
        Extrae evidencia específica de los health_events
        Cita línea exacta y valor que causa el warning
        """
        evidence = []
        
        recent_events = context.get('recent_events', [])
        for i, event in enumerate(recent_events, 1):
            if event.get('severity') in ['WARNING', 'ERROR']:
                evidence.append({
                    'line_number': i,
                    'severity': event.get('severity'),
                    'message': event.get('message'),
                    'timestamp': event.get('timestamp'),
                    'cited_value': event.get('value')
                })
        
        return evidence
    
    def _extract_risk_parameters(self, context: Dict) -> List[Dict]:
        """
        Extrae parámetros en riesgo de current_state.json
        Incluye: valor actual, límite crítico, probabilidad de fallo
        """
        risk_params = []
        
        metrics = context.get('current_metrics', {})
        quarantined = context.get('quarantined_parameters', {})
        
        # Parámetros en cuarentena están en riesgo
        if isinstance(quarantined, dict):
            for param, info in quarantined.items():
                if isinstance(info, dict):
                    risk_params.append({
                        'parameter': param,
                        'current_value': info.get('value'),
                        'critical_limit': info.get('limit', 'N/A'),
                        'failure_probability': 'ALTO',
                        'status': 'QUARANTINED'
                    })
        elif isinstance(quarantined, list):
            for item in quarantined:
                if isinstance(item, dict):
                    risk_params.append({
                        'parameter': item.get('parameter', 'Unknown'),
                        'current_value': item.get('value'),
                        'critical_limit': item.get('limit', 'N/A'),
                        'failure_probability': 'ALTO',
                        'status': 'QUARANTINED'
                    })
        
        # Parámetros cercanos a límites
        if isinstance(metrics, dict):
            critical_metrics = ['latency_ms', 'drawdown', 'error_rate']
            for metric in critical_metrics:
                if metric in metrics:
                    value = metrics[metric]
                    # Heurística simple: si está > 80% del límite, está en riesgo
                    if isinstance(value, (int, float)) and value > 80:
                        risk_params.append({
                            'parameter': metric,
                            'current_value': value,
                            'critical_limit': 100,
                            'failure_probability': 'MEDIO',
                            'status': 'AT_RISK'
                        })
        
        return risk_params
    
    def _extract_suggested_commands(self, response: str) -> List[str]:
        """
        Extrae comandos sugeridos de la respuesta del LLM
        Busca patrones como "aipha proposal create..."
        """
        commands = []
        
        for line in response.split('\n'):
            if 'aipha proposal create' in line or 'aipha' in line and '--parameter' in line:
                # Limpia la línea
                cmd = line.strip()
                if cmd.startswith('aipha'):
                    commands.append(cmd)
        
        return commands
    
    def _format_diagnosis_output(self, diagnosis: str, risk_params: List[Dict], 
                                  suggested_commands: List[str], simulation_mode: bool) -> str:
        """
        Formatea el diagnóstico para presentación visual
        """
        output = f"""
╔════════════════════════════════════════════════════════════════╗
║       DIAGNÓSTICO PROFUNDO DEL SISTEMA AIPHA v2.0             ║
╚════════════════════════════════════════════════════════════════╝

🔍 ANÁLISIS DEL LLM:
{diagnosis}

"""
        
        # Tabla de parámetros en riesgo
        if risk_params:
            output += """
╔════════════════════════════════════════════════════════════════╗
║          PARÁMETROS EN RIESGO - TABLA DE ANÁLISIS             ║
╚════════════════════════════════════════════════════════════════╝

"""
            output += "Parámetro | Valor Actual | Límite Crítico | Probabilidad Fallo\n"
            output += "-----------|--------------|---------------|-----------------\n"
            for param in risk_params:
                output += f"{param.get('parameter', 'N/A')} | {param.get('current_value', 'N/A')} | {param.get('critical_limit', 'N/A')} | {param.get('failure_probability', 'N/A')}\n"
        
        # Información de simulación
        if simulation_mode:
            output += f"""
⚠️  MODO SIMULACIÓN ACTIVO
   → La latencia puede ser del flujo de datos sintéticos
   → Los timings pueden no reflejar el hardware real

"""
        
        # Comandos sugeridos
        if suggested_commands:
            output += """
╔════════════════════════════════════════════════════════════════╗
║               ACCIONES SUGERIDAS (COPY-PASTE)                 ║
╚════════════════════════════════════════════════════════════════╝

"""
            for cmd in suggested_commands:
                output += f"▶️  {cmd}\n"
        
        output += f"""
╔════════════════════════════════════════════════════════════════╗
║  Diagnóstico: Qwen 2.5 Coder 32B | Timestamp: {datetime.now().isoformat()}
╚════════════════════════════════════════════════════════════════╝
"""
        
        return output
    
    def _build_analysis_prompt(self, context: Dict) -> str:
        """Construir prompt para análisis y propuestas"""
        
        return f"""Analiza el estado actual del sistema Aipha y propón cambios de optimización.

CONTEXTO ACTUAL:
{json.dumps(context, indent=2, default=str)}

Por favor:
1. Resume el estado del sistema en 1-2 líneas
2. Identifica qué está funcionando bien
3. Identifica qué tiene problemas
4. Propón 2-3 cambios específicos que mejorarían la performance
5. Para CADA propuesta:
   - Especifica: parámetro, valor actual, valor nuevo
   - Justificación técnica
   - Riesgo potencial
   - Confianza (0-1)

IMPORTANTE: Evita proponer valores que estén en cuarentena.
Aprende de fallos previos documentados en los eventos."""
    
    def _parse_analysis_response(self, response: str, context: Dict) -> Dict:
        """
        Parsear respuesta del LLM para extraer propuestas
        
        Intenta extraer de la respuesta:
        - diagnosis: Análisis
        - proposals: Cambios propuestos
        - confidence: Confianzas
        """
        
        # Parseo simple (en producción, podría ser más sofisticado)
        result = {
            'diagnosis': response[:200] if response else "",
            'raw_response': response,
            'proposals': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Buscar patrones de propuestas en la respuesta
        lines = response.split('\n')
        for i, line in enumerate(lines):
            if 'parámetro' in line.lower() or 'cambio' in line.lower():
                result['proposals'].append({
                    'line': line,
                    'context': lines[max(0, i-1):min(len(lines), i+2)]
                })
        
        return result
