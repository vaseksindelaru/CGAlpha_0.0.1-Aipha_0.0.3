"""
Fase 0: Principios Fundamentales
Base teórica para que el LLM entienda CÓMO hacer recomendaciones inteligentes
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class Principle:
    """Principio fundamental de recomendación"""
    id: str
    category: str  # 'recommendation_systems', 'information_retrieval', etc.
    title: str
    description: str
    key_concepts: List[str]
    applications: List[str]
    related_papers: Optional[List[str]] = None
    validation_metrics: Optional[List[str]] = None


class PrinciplesLibrary:
    """
    Biblioteca de principios fundamentales
    Enseña al LLM la TEORÍA de recomendaciones
    """
    
    def __init__(self):
        self.principles: Dict[str, Principle] = {}
        self._load_principles()
    
    def _load_principles(self):
        """Carga principios fundamentales de recomendación"""
        
        # ===== CATEGORY: RECOMMENDATION SYSTEMS =====
        self.principles['rs_001'] = Principle(
            id='rs_001',
            category='recommendation_systems',
            title='Principio de Relevancia Contextual',
            description=(
                'Una recomendación es buena si es relevante al contexto actual. '
                'No solo debe ser buena EN GENERAL, sino buena PARA ESTE MOMENTO.'
            ),
            key_concepts=[
                'context-awareness',
                'temporal-relevance',
                'user-state',
                'situational-fit'
            ],
            applications=[
                'Trading: VWAP es relevante solo con suficientes datos intrabar',
                'Papers: Recomendar papers sobre reversión cuando hay señales de agotamiento',
                'Filtrado: Descartar papers que no aplican al estado actual del mercado'
            ],
            validation_metrics=[
                'P@K (Precision at K)',
                'MRR (Mean Reciprocal Rank)',
                'NDCG (Normalized Discounted Cumulative Gain)'
            ]
        )
        
        self.principles['rs_002'] = Principle(
            id='rs_002',
            category='recommendation_systems',
            title='Principio de Diversidad sin Redundancia',
            description=(
                'Recomendar variedad de perspectivas evitando duplicación. '
                'Si recomiendas 3 papers sobre VWAP, deben abordar ángulos distintos.'
            ),
            key_concepts=[
                'diversity',
                'novelty',
                'coverage',
                'anti-redundancy'
            ],
            applications=[
                'Trading: No sugerir 5 papers que dicen lo mismo sobre VWAP',
                'Papers: Papers deben cubrir: teoría, implementación, validación, límites',
                'Coverage: Asegurar que se cubren todos los aspectos del indicador'
            ],
            validation_metrics=[
                'Coverage metric',
                'Diversity score',
                'Redundancy ratio'
            ]
        )
        
        self.principles['rs_003'] = Principle(
            id='rs_003',
            category='recommendation_systems',
            title='Principio de Confianza y Credibilidad',
            description=(
                'No todas las fuentes tienen igual credibilidad. '
                'Papers de IEEE/ACM > arXiv preprint. Trader profesional > blog anónimo.'
            ),
            key_concepts=[
                'source-credibility',
                'peer-review',
                'author-authority',
                'citation-count',
                'validation-level'
            ],
            applications=[
                'Trading: Preferir papers peer-reviewed sobre especulaciones',
                'Sources: Filtrar por: publicación, citaciones, validación empírica',
                'Authority: Considerar experiencia del autor (10 años > 1 año)'
            ],
            validation_metrics=[
                'Authority score',
                'Citation impact',
                'H-index authors',
                'Peer review level'
            ]
        )
        
        # ===== CATEGORY: INFORMATION RETRIEVAL =====
        self.principles['ir_001'] = Principle(
            id='ir_001',
            category='information_retrieval',
            title='Principio de Búsqueda Semántica vs Lexical',
            description=(
                'Buscar por significado, no solo por palabras. '
                '"Money flow" y "volume momentum" son conceptos similares, '
                'aunque usen palabras diferentes.'
            ),
            key_concepts=[
                'semantic-search',
                'embeddings',
                'meaning-matching',
                'concept-similarity',
                'lexical-vs-semantic'
            ],
            applications=[
                'Trading: Buscar "agotamiento de movimiento" encuentra papers sobre Cumulative Delta',
                'Papers: Encontrar papers sobre reversal aunque usen términos distintos',
                'Indexing: Usar embeddings, no solo full-text search'
            ],
            validation_metrics=[
                'NDCG@10',
                'Recall',
                'Semantic similarity score'
            ]
        )
        
        self.principles['ir_002'] = Principle(
            id='ir_002',
            category='information_retrieval',
            title='Principio de Relevancia vs Popularidad',
            description=(
                'Relevancia NO es popularidad. Un paper muy citado '
                'puede no ser relevante a tu caso específico.'
            ),
            key_concepts=[
                'relevance-ranking',
                'popularity-bias',
                'query-match',
                'citation-bias',
                'long-tail'
            ],
            applications=[
                'Trading: Paper de VWAP muy antiguo podría ser obsoleto',
                'Papers: No usar solo "papers más descargados"',
                'Filtering: Combinar: relevancia (60%) + popularidad (40%)'
            ],
            validation_metrics=[
                'Precision',
                'Recall',
                'Popularity bias score'
            ]
        )
        
        # ===== CATEGORY: CURATION ACADEMICA =====
        self.principles['cur_001'] = Principle(
            id='cur_001',
            category='curacion_academica',
            title='Principio de Validación Empírica',
            description=(
                'Preferir papers que DEMUESTRAN con datos, no solo teoría. '
                'Backtest de 10 años > idea brillante sin validación.'
            ),
            key_concepts=[
                'empirical-validation',
                'backtesting',
                'live-trading-results',
                'statistical-significance',
                'methodology-rigor'
            ],
            applications=[
                'Trading: Paper que muestra +82% winrate en backtest > teoría pura',
                'Papers: Filtrar por: ha sido testeado en vivo, p-value < 0.05',
                'Weighting: Dar más peso a papers con validación empírica'
            ],
            validation_metrics=[
                'Sharpe ratio papers',
                'p-value of claims',
                'Backtest rigor score'
            ]
        )
        
        self.principles['cur_002'] = Principle(
            id='cur_002',
            category='curacion_academica',
            title='Principio de Limitaciones Transparentes',
            description=(
                'Paper bueno menciona qué NO funciona. '
                'Si dice "VWAP siempre funciona", es sospechoso. '
                'Si dice "VWAP funciona bien en 75% de condiciones", es honesto.'
            ),
            key_concepts=[
                'limitations-transparency',
                'failure-modes',
                'boundary-conditions',
                'honest-reporting',
                'negative-results'
            ],
            applications=[
                'Trading: Buscar papers que dicen: "VWAP NO funciona cuando..."',
                'Papers: Dar puntos a papers que discuten límites',
                'Filtering: Descartar papers que no mencionan limitaciones'
            ],
            validation_metrics=[
                'Limitation discussion score',
                'Honesty index',
                'Nuance level'
            ]
        )
        
        # ===== CATEGORY: LLMS PARA RECOMENDACION =====
        self.principles['llm_001'] = Principle(
            id='llm_001',
            category='llms_para_recomendacion',
            title='Principio de Prompt Engineering para Recomendación',
            description=(
                'La calidad de recomendaciones de LLM depende del prompt. '
                'Prompt vago → recomendaciones vagas. Prompt principiado → recomendaciones inteligentes.'
            ),
            key_concepts=[
                'prompt-engineering',
                'in-context-learning',
                'few-shot-examples',
                'task-specification',
                'constraint-definition'
            ],
            applications=[
                'Trading: Prompt debe especificar: validación empírica, limites, aplicabilidad',
                'Papers: Incluir en prompt los principios de curaduría',
                'Examples: Dar al LLM 2-3 ejemplos de BUENAS recomendaciones'
            ],
            validation_metrics=[
                'Prompt clarity score',
                'Recommendation quality post-prompt',
                'LLM adherence to constraints'
            ]
        )
        
        self.principles['llm_002'] = Principle(
            id='llm_002',
            category='llms_para_recomendacion',
            title='Principio de Validación de Outputs LLM',
            description=(
                'LLMs pueden alucinar. Validar que recomendaciones tienen '
                'coherencia interna y consistencia lógica.'
            ),
            key_concepts=[
                'hallucination-detection',
                'consistency-checking',
                'fact-verification',
                'logical-coherence',
                'confidence-scoring'
            ],
            applications=[
                'Trading: Si LLM sugiere paper, validar que existe y es relevante',
                'Papers: Cross-check recomendaciones contra base de datos conocida',
                'Scoring: Asignar confianza a cada recomendación'
            ],
            validation_metrics=[
                'Hallucination rate',
                'Logical consistency score',
                'Fact-check pass rate'
            ]
        )
        
        # ===== CATEGORY: TAXONOMIA DOMINIOS =====
        self.principles['tax_001'] = Principle(
            id='tax_001',
            category='taxonomia_dominios',
            title='Principio de Jerarquía Conceptual Clara',
            description=(
                'Organizar conceptos de GENERAL → ESPECÍFICO. '
                'Trading > Scalping > EURUSD Scalping > VWAP in Scalping'
            ),
            key_concepts=[
                'hierarchy-definition',
                'concept-granularity',
                'parent-child-relations',
                'sibling-relationships',
                'taxonomy-depth'
            ],
            applications=[
                'Trading: Estructura: Indicators > Dynamic Barriers > VWAP',
                'Papers: Catalogar por: Categoría > Subcategoría > Aplicación específica',
                'Navigation: Permitir búsqueda por nivel de especificidad'
            ],
            validation_metrics=[
                'Hierarchy clarity score',
                'Concept coverage',
                'Navigation efficiency'
            ]
        )
        
        self.principles['tax_002'] = Principle(
            id='tax_002',
            category='taxonomia_dominios',
            title='Principio de Relaciones Cross-Cutting',
            description=(
                'Algunos conceptos se relacionan fuera de jerarquía. '
                'VWAP (indicador de barrera) se RELACIONA con OBI (confirmación), '
                'pero no es "padre-hijo".'
            ),
            key_concepts=[
                'cross-cutting-relations',
                'concept-links',
                'non-hierarchical-connections',
                'semantic-networks',
                'knowledge-graphs'
            ],
            applications=[
                'Trading: Vincular VWAP ↔ OBI ↔ Cumulative Delta (correlacionados)',
                'Papers: Papers sobre reversión deben vincular a papers sobre agotamiento',
                'Discovery: Usuario explora tema descubre temas relacionados'
            ],
            validation_metrics=[
                'Link coherence',
                'Cross-reference quality',
                'Semantic relatedness'
            ]
        )
        
        # ===== CATEGORY: BENCHMARKS VALIDACION =====
        self.principles['bench_001'] = Principle(
            id='bench_001',
            category='benchmarks_validacion',
            title='Principio de Métricas Apropiadas al Dominio',
            description=(
                'No todas las métricas son válidas para todos los dominios. '
                'En trading: Sharpe ratio, winrate, drawdown. '
                'En papers: Citaciones, peer-review, reproducibilidad.'
            ),
            key_concepts=[
                'domain-specific-metrics',
                'metric-selection',
                'performance-indicators',
                'context-appropriateness',
                'metric-validation'
            ],
            applications=[
                'Trading: Medir recomendaciones por: winrate, PnL, Sharpe',
                'Papers: Medir por: relevancia (IR score), credibilidad, novedad',
                'Weighting: Diferentes métricas tienen diferentes pesos'
            ],
            validation_metrics=[
                'Metric appropriateness score',
                'Predictive validity',
                'Domain alignment'
            ]
        )
        
        self.principles['bench_002'] = Principle(
            id='bench_002',
            category='benchmarks_validacion',
            title='Principio de Validación Cruzada',
            description=(
                'Una recomendación buena según métrica X podría ser mala según Y. '
                'Validar con múltiples perspectivas.'
            ),
            key_concepts=[
                'cross-validation',
                'multi-metric-evaluation',
                'consensus-checking',
                'robustness-testing',
                'sensitivity-analysis'
            ],
            applications=[
                'Trading: Paper recomendado debe ser bueno según: IR score AND credibilidad AND novedad',
                'Papers: No confiar en métrica única',
                'Testing: Simular: si cambia métrica, cambia ranking?'
            ],
            validation_metrics=[
                'Cross-validation score',
                'Metric consensus',
                'Robustness index'
            ]
        )
    
    def get_principle(self, principle_id: str) -> Optional[Principle]:
        """Retorna un principio específico"""
        return self.principles.get(principle_id)
    
    def get_by_category(self, category: str) -> List[Principle]:
        """Retorna todos los principios de una categoría"""
        return [p for p in self.principles.values() if p.category == category]
    
    def get_all_categories(self) -> List[str]:
        """Retorna todas las categorías de principios"""
        return sorted(set(p.category for p in self.principles.values()))
    
    def synthesize_category(self, category: str) -> str:
        """
        Sintetiza principios de una categoría para usar en prompts
        """
        principles = self.get_by_category(category)
        
        synthesis = f"\n=== {category.upper()} ===\n"
        for p in principles:
            synthesis += f"\n{p.title}:\n"
            synthesis += f"  {p.description}\n"
            synthesis += f"  Key concepts: {', '.join(p.key_concepts)}\n"
            if p.applications:
                synthesis += f"  Applications: {'; '.join(p.applications[:2])}\n"
        
        return synthesis
    
    def get_all_principles_text(self) -> str:
        """Retorna TODOS los principios como texto para contexto del LLM"""
        text = "# PRINCIPIOS FUNDAMENTALES DE RECOMENDACIÓN INTELIGENTE\n\n"
        
        for category in self.get_all_categories():
            text += self.synthesize_category(category)
            text += "\n" + "="*80 + "\n\n"
        
        return text
    
    def get_applicable_principles(self, context: str) -> List[Principle]:
        """
        Retorna principios aplicables a un contexto específico
        
        context: ej. 'trading_entry_validation', 'paper_curation_vwap'
        """
        applicable = []
        
        # Mapeo de contextos a principios relevantes
        context_map = {
            'trading_entry': ['rs_001', 'rs_003', 'cur_001', 'llm_001'],
            'trading_exit': ['rs_001', 'cur_002', 'ir_002', 'bench_001'],
            'paper_recommendation': ['rs_002', 'rs_003', 'ir_001', 'cur_001', 'cur_002', 'tax_001', 'llm_002', 'bench_002'],
            'knowledge_organization': ['tax_001', 'tax_002', 'ir_001'],
            'quality_validation': ['bench_001', 'bench_002', 'cur_001', 'cur_002'],
        }
        
        principle_ids = context_map.get(context, [])
        
        for pid in principle_ids:
            p = self.get_principle(pid)
            if p:
                applicable.append(p)
        
        return applicable
    
    def export_as_json(self) -> str:
        """Exporta principios como JSON para persistencia"""
        data = {
            'principles': [
                {
                    'id': p.id,
                    'category': p.category,
                    'title': p.title,
                    'description': p.description,
                    'key_concepts': p.key_concepts,
                    'applications': p.applications,
                    'validation_metrics': p.validation_metrics
                }
                for p in self.principles.values()
            ]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
