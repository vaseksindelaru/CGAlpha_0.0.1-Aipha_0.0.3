"""
Fase 0a: Principios Meta-Cognitivos de Recomendación
Base teórica: CÓMO UN LLM DEBE HACER RECOMENDACIONES INTELIGENTES

No es "papers sobre trading".
Es "papers sobre CÓMO RECOMENDAR papers sobre trading".

Estructura de dos capas:
  Capa 0a (este módulo): LLM aprende TEORÍA de recomendación
  Capa 0b (next module): LLM aplica esa teoría para sugerir papers de trading
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MetaCognitiveCategory(Enum):
    """Categorías de principios meta-cognitivos"""
    RECOMMENDATION_SYSTEMS = "recommendation_systems"
    INFORMATION_RETRIEVAL = "information_retrieval"
    ACADEMIC_CURATION = "academic_curation"
    LLMS_FOR_RECOMMENDATION = "llms_for_recommendation"
    DOMAIN_TAXONOMY = "domain_taxonomy"
    QUALITY_BENCHMARKS = "quality_benchmarks"


@dataclass
class MetaCognitivePrinciple:
    """Principio fundamental de cómo hacer buenas recomendaciones"""
    
    id: str
    category: MetaCognitiveCategory
    title: str
    description: str
    
    # Por qué es importante
    importance: str  # "Critical" | "High" | "Medium"
    
    # Papers fundamentales que explican este principio
    foundational_papers: List[str]  # DOI o ArXiv IDs
    
    # Cómo aplicar a nuestro caso
    application_to_trading: str
    
    # Anti-patrón: qué NO hacer
    anti_pattern: str
    
    # Validación: cómo saber que lo hicimos bien
    validation_metric: str
    
    # Ejemplos concretos
    examples: List[str]


class MetaCognitiveFramework:
    """
    Framework de principios meta-cognitivos
    
    El LLM sugeridor DEBE entender estos principios PRIMERO
    Antes de sugerir papers sobre trading
    """
    
    def __init__(self):
        self.principles: Dict[str, MetaCognitivePrinciple] = {}
        self._load_principles()
    
    def _load_principles(self):
        """Carga principios fundamentales de recomendación"""
        
        # ===== RECOMMENDATION SYSTEMS =====
        
        self.principles['metacog_rs_001'] = MetaCognitivePrinciple(
            id='metacog_rs_001',
            category=MetaCognitiveCategory.RECOMMENDATION_SYSTEMS,
            title='Principio de Relevancia Contextual vs Popularidad',
            description=(
                'Una recomendación POPULAR no es lo mismo que RELEVANTE. '
                'Un paper muy citado (popular) puede NO ser relevante a tu contexto específico. '
                'El LLM debe priorizar RELEVANCIA sobre POPULARIDAD.'
            ),
            importance='Critical',
            foundational_papers=[
                'Ricci, Rokach, Shapira (2011) - Recommender Systems Handbook',
                'Jannach et al. (2016) - Evaluating Recommendations'
            ],
            application_to_trading=(
                'Paper sobre VWAP muy citado en academia puede NO ser relevante a '
                'scalping FX 1-minuto. Debes encontrar papers ESPECÍFICAMENTE sobre '
                'VWAP en microestructura, no solo VWAP teórico.'
            ),
            anti_pattern='Sugerir papers solo por citation count sin revisar relevancia.',
            validation_metric='Recall: ¿encuentra papers relevantes aunque sean poco citados?',
            examples=[
                'Paper clásico sobre ATR (popular) vs Paper específico sobre VWAP '
                'real-time en scalping (menos popular, más relevante)',
                'Paper general "machine learning" vs Paper específico "ML for order flow"'
            ]
        )
        
        self.principles['metacog_rs_002'] = MetaCognitivePrinciple(
            id='metacog_rs_002',
            category=MetaCognitiveCategory.RECOMMENDATION_SYSTEMS,
            title='Principio de Diversidad sin Redundancia',
            description=(
                'Recomendar 5 papers que dicen lo MISMO = desperdicio. '
                'Recomendar 5 papers sobre DIFERENTES ángulos del tema = excelente. '
                'El LLM debe detectar redundancia conceptual.'
            ),
            importance='High',
            foundational_papers=[
                'Ziegler et al. (2005) - Improving Recommendation Diversity',
                'Zhang, Hurley (2008) - Avoiding Monotony'
            ],
            application_to_trading=(
                'Al sugerir papers sobre VWAP, incluir: '
                '1) Fundación teórica (Almgren & Chriss) '
                '2) Implementación real-time '
                '3) Limitaciones (cuándo NO funciona) '
                '4) Microestructura '
                'NO: 5 papers que todos dicen "VWAP es la media ponderada del volumen"'
            ),
            anti_pattern='Recomendaciones que repiten el mismo concepto en diferentes palabras.',
            validation_metric='Unique concepts per paper: cada paper agrega concepto nuevo.',
            examples=[
                'Incluir paper sobre teoría + paper sobre implementación + paper sobre límites',
                'Papers sobre reversión: incluir momentum exhaustion + price action + order flow'
            ]
        )
        
        self.principles['metacog_rs_003'] = MetaCognitivePrinciple(
            id='metacog_rs_003',
            category=MetaCognitiveCategory.RECOMMENDATION_SYSTEMS,
            title='Principio de Confianza y Credibilidad de Fuente',
            description=(
                'No todas las fuentes son iguales. '
                'IEEE/ACM peer-reviewed > ArXiv preprint > Blog anónimo. '
                'El LLM debe ponderar por credibilidad de fuente.'
            ),
            importance='Critical',
            foundational_papers=[
                'Dellarocas, Zhang, Awad (2007) - Trust in Online Communities',
                'Wang, Strong (1996) - Data Quality'
            ],
            application_to_trading=(
                'Preferir papers sobre VWAP que: '
                '1) Son peer-reviewed '
                '2) Han sido citados en otros papers respetables '
                '3) Tienen validación empírica (backtest, live trading) '
                '4) Autores tienen track record en trading'
            ),
            anti_pattern='Tratar blog de trader anónimo igual que paper IEEE.',
            validation_metric='Authority score: ¿fuentes son verificables y respetables?',
            examples=[
                'Paper Almgren & Chriss (1200+ citas) vs blog "MyTradingSecrets" (desconocido)',
                'Prop firm research report vs Reddit user sugiriendo VWAP'
            ]
        )
        
        # ===== INFORMATION RETRIEVAL =====
        
        self.principles['metacog_ir_001'] = MetaCognitivePrinciple(
            id='metacog_ir_001',
            category=MetaCognitiveCategory.INFORMATION_RETRIEVAL,
            title='Principio de Búsqueda Semántica vs Lexical',
            description=(
                'Buscar por SIGNIFICADO, no solo por PALABRAS. '
                '"Money flow" y "volume momentum" son conceptos similares, '
                'aunque usen palabras diferentes. El LLM debe entender semántica.'
            ),
            importance='High',
            foundational_papers=[
                'Mikolov et al. (2013) - Word2Vec',
                'Devlin et al. (2019) - BERT'
            ],
            application_to_trading=(
                'Buscar "agotamiento de movimiento" DEBE encontrar papers sobre '
                'Cumulative Delta, Order Flow exhaustion, momentum reversal. '
                'No solo papers que usan palabra "exhaustion" literalmente.'
            ),
            anti_pattern='Búsqueda por keywords exactos. Ignorar sinónimos conceptuales.',
            validation_metric='Precision: ¿encuentra papers relevantes aunque usen palabras diferentes?',
            examples=[
                'Query: "reversión" → Encontrar papers sobre reversal, mean reversion, exhaustion',
                'Query: "volumen desequilibrio" → Encontrar papers sobre OBI, order imbalance, flow'
            ]
        )
        
        self.principles['metacog_ir_002'] = MetaCognitivePrinciple(
            id='metacog_ir_002',
            category=MetaCognitiveCategory.INFORMATION_RETRIEVAL,
            title='Principio de Ranking: Relevancia > Popularidad',
            description=(
                'En búsqueda, NO retornar por "más citado" sino por "más relevante". '
                'El ranking debe considerar: similitud semántica primero, '
                'luego credibilidad, luego popularidad.'
            ),
            importance='High',
            foundational_papers=[
                'Robertson (1977) - Probabilistic Ranking Principle',
                'Brin, Page (1998) - PageRank'
            ],
            application_to_trading=(
                'Si buscas "VWAP en scalping FX", paper muy antiguo (1995) pero ESPECÍFICO '
                'debe rankear más alto que paper reciente (2023) pero GENERAL sobre trading. '
                'Relevancia > Recency.'
            ),
            anti_pattern='Retornar papers en orden de citaciones descendentes.',
            validation_metric='NDCG@10: Ranked DCG normalizado en top 10 resultados.',
            examples=[
                'Query: "VWAP scalping" → Rankear específico sobre VWAP en scalping arriba, '
                'luego general sobre scalping, luego general sobre VWAP',
                'Paper antiguo pero muy específico > Paper reciente pero genérico'
            ]
        )
        
        # ===== ACADEMIC CURATION =====
        
        self.principles['metacog_cur_001'] = MetaCognitivePrinciple(
            id='metacog_cur_001',
            category=MetaCognitiveCategory.ACADEMIC_CURATION,
            title='Principio de Validación Empírica Obligatoria',
            description=(
                'Preferir papers que DEMUESTRAN con datos, no solo teoría. '
                'Backtest de 10 años > idea brillante sin validación. '
                'Si un paper hace claims sin datos, es sospechoso.'
            ),
            importance='Critical',
            foundational_papers=[
                'Popper (1934) - Logic of Scientific Discovery',
                'Merton (1973) - The Sociology of Science'
            ],
            application_to_trading=(
                'Paper que dice "VWAP tiene 82% winrate" DEBE incluir: '
                '1) Datos de backtest (símbolo, período, número de trades) '
                '2) Metodología (cómo calculó VWAP, timeframe, spread) '
                '3) Resultado verificable. '
                'Si NO incluye datos, es especulación. Descartar.'
            ),
            anti_pattern='Aceptar claims sin validación: "He ganado 200% con VWAP".',
            validation_metric='Empirical Rigor Score: ¿hay datos, metodología, reproducibilidad?',
            examples=[
                'Paper: "VWAP reduces slippage by 23%" + backtest de 5 años = BUENO',
                'Blog: "VWAP is the best" sin datos = MALO'
            ]
        )
        
        self.principles['metacog_cur_002'] = MetaCognitivePrinciple(
            id='metacog_cur_002',
            category=MetaCognitiveCategory.ACADEMIC_CURATION,
            title='Principio de Limitaciones Transparentes',
            description=(
                'Paper BUENO menciona: "No funciona cuando..." '
                'Paper SOSPECHOSO dice: "Siempre funciona". '
                'El LLM debe dar puntos a papers que discuten límites.'
            ),
            importance='High',
            foundational_papers=[
                'Kuhn (1962) - The Structure of Scientific Revolutions',
                'Taleb (2007) - The Black Swan'
            ],
            application_to_trading=(
                'Paper sobre VWAP BUENO: "Funciona bien en 75% de mercados, '
                'NO funciona en flash crashes, NO funciona con spread > 2 pips" '
                'Paper MALO: "VWAP es solución universal". '
                'Desconfiar de afirmaciones absolutas.'
            ),
            anti_pattern='Ignorar "fine print" o limitaciones. Creer en soluciones universales.',
            validation_metric='Honesty Index: ¿Paper menciona cuándo falla?',
            examples=[
                'Paper: "OBI effectiveness: 74% in normal conditions, 12% in flash crash"',
                'Paper: "This strategy always works" = Red flag'
            ]
        )
        
        # ===== LLMS FOR RECOMMENDATION =====
        
        self.principles['metacog_llm_001'] = MetaCognitivePrinciple(
            id='metacog_llm_001',
            category=MetaCognitiveCategory.LLMS_FOR_RECOMMENDATION,
            title='Principio de Prompt Engineering para Recomendaciones',
            description=(
                'Calidad de recomendaciones LLM depende del prompt. '
                'Prompt vago: "Dame papers sobre trading" → recomendaciones vagas. '
                'Prompt principiado: incluir restricciones, criterios, ejemplos → buenas recomendaciones.'
            ),
            importance='Critical',
            foundational_papers=[
                'Wei et al. (2022) - Emergent Abilities of LLMs',
                'Brown et al. (2020) - Language Models are Few-Shot Learners'
            ],
            application_to_trading=(
                'Prompt MALO: "Sugiere papers sobre VWAP". '
                'Prompt BUENO: '
                '"Basándote en principios de recomendación (relevancia, diversidad, '
                'credibilidad), sugiere 3 papers sobre VWAP en FX scalping que: '
                '1) Sean peer-reviewed, 2) Tengan validación empírica, 3) Mencionen límites. '
                'Usa búsqueda semántica, no solo palabras clave."'
            ),
            anti_pattern='Prompts genéricos. No especificar criterios.',
            validation_metric='Recommendation Quality Score: Prompts específicos > Prompts genéricos.',
            examples=[
                'Incluir ejemplos de BUENA recomendación en prompt',
                'Especificar: "diversidad de perspectivas", "validación empírica", "límites"'
            ]
        )
        
        self.principles['metacog_llm_002'] = MetaCognitivePrinciple(
            id='metacog_llm_002',
            category=MetaCognitiveCategory.LLMS_FOR_RECOMMENDATION,
            title='Principio de Validación de Outputs LLM (Anti-Alucinación)',
            description=(
                'LLMs pueden alucinar. Inventar papers que no existen. '
                'VALIDAR: ¿El paper que sugirió existe? ¿DOI es válido? ¿Autores reales? '
                'Si falla validación, descartar sugerencia.'
            ),
            importance='Critical',
            foundational_papers=[
                'Huang et al. (2023) - Hallucination in Neural Machine Translation',
                'Zhang et al. (2023) - Hallucination in Large Language Models'
            ],
            application_to_trading=(
                'LLM sugiere: "Paper: Almgren & Chriss (2005) - Advanced VWAP Techniques". '
                'VALIDAR: ¿Existe realmente? ¿Es 2005 o 2000? ¿Qué DOI? '
                'Si no puedes verificar, desconfía. No ingestar papers no verificables.'
            ),
            anti_pattern='Confiar ciegamente en sugerencias LLM sin verificación.',
            validation_metric='Hallucination Rate: <5% de sugerencias no verificables.',
            examples=[
                'Verificar DOI en CrossRef',
                'Verificar ArXiv ID',
                'Verificar que autores sean reales'
            ]
        )
        
        # ===== DOMAIN TAXONOMY =====
        
        self.principles['metacog_tax_001'] = MetaCognitivePrinciple(
            id='metacog_tax_001',
            category=MetaCognitiveCategory.DOMAIN_TAXONOMY,
            title='Principio de Jerarquía Conceptual Clara',
            description=(
                'Organizar conceptos de GENERAL → ESPECÍFICO. '
                'Trading > Scalping > EURUSD Scalping > VWAP en EURUSD Scalping. '
                'El LLM debe entender esta jerarquía.'
            ),
            importance='High',
            foundational_papers=[
                'Protege et al. (2000) - Ontology Design',
                'Guarino (1998) - Formal Ontology'
            ],
            application_to_trading=(
                'Estructura: '
                'Indicators → Dynamic Barriers → VWAP Real-time '
                'Indicators → Entry Confirmation → OBI '
                'Indicators → Exit Strategy → Cumulative Delta '
                'El LLM debe sugerir papers respetando esta jerarquía.'
            ),
            anti_pattern='Mezclar papers de niveles jerárquicos diferentes sin estructura.',
            validation_metric='Hierarchy Clarity Score: ¿papers están organizados lógicamente?',
            examples=[
                'Nivel 1: "Indicadores de trading" '
                'Nivel 2: "Barreras dinámicas" '
                'Nivel 3: "VWAP real-time" '
                'No: sugerir papers aleatorios sin estructura'
            ]
        )
        
        self.principles['metacog_tax_002'] = MetaCognitivePrinciple(
            id='metacog_tax_002',
            category=MetaCognitiveCategory.DOMAIN_TAXONOMY,
            title='Principio de Relaciones Cross-Cutting',
            description=(
                'Algunos conceptos se relacionan FUERA de jerarquía. '
                'VWAP (barrera) se RELACIONA con OBI (confirmación), '
                'aunque no es relación padre-hijo. '
                'El LLM debe detectar estas relaciones.'
            ),
            importance='Medium',
            foundational_papers=[
                'Sowa (1992) - Conceptual Graphs',
                'Hendler et al. (2001) - The Semantic Web'
            ],
            application_to_trading=(
                'VWAP ← está relacionado con → OBI (ambos validan entrada) '
                'OBI ← está relacionado con → Cumulative Delta (ambos usan flujo) '
                'El LLM debe vincular estos papers aunque estén en ramas distintas.'
            ),
            anti_pattern='Tratar papers aisladamente. No ver conexiones entre temas.',
            validation_metric='Cross-Link Coverage: ¿papers están interconectados semánticamente?',
            examples=[
                'Paper sobre VWAP debe referenciar papers sobre microestructura',
                'Paper sobre reversión debe referenciar papers sobre agotamiento'
            ]
        )
        
        # ===== QUALITY BENCHMARKS =====
        
        self.principles['metacog_bench_001'] = MetaCognitivePrinciple(
            id='metacog_bench_001',
            category=MetaCognitiveCategory.QUALITY_BENCHMARKS,
            title='Principio de Métricas Apropiadas al Dominio',
            description=(
                'No todas las métricas son válidas para todos los dominios. '
                'En trading: Sharpe ratio, winrate, drawdown. '
                'En papers: Citaciones, peer-review, reproducibilidad. '
                'Usar métricas apropiadas para validar.'
            ),
            importance='High',
            foundational_papers=[
                'Jøsang et al. (2007) - Subjective Logic',
                'Ricci et al. (2011) - Recommender Systems'
            ],
            application_to_trading=(
                'Medir calidad de recomendaciones por: '
                '- Relevancia (IR score) '
                '- Credibilidad (peer review level) '
                '- Novedad (año del paper) '
                'NO usar: "¿Es el paper más largo?" o "¿Tiene más figuras?"'
            ),
            anti_pattern='Usar métricas inapropiadas. Confundir largo con calidad.',
            validation_metric='Metric Alignment Score: ¿métricas son relevantes al dominio?',
            examples=[
                'Paper CORTO pero peer-reviewed > Paper LARGO pero blog personal',
                'Métrica: Citaciones en otros papers académicos (buena)',
                'Métrica: Número de descargas de ResearchGate (mala, puede ser spam)'
            ]
        )
        
        self.principles['metacog_bench_002'] = MetaCognitivePrinciple(
            id='metacog_bench_002',
            category=MetaCognitiveCategory.QUALITY_BENCHMARKS,
            title='Principio de Validación Cruzada Multi-Perspectiva',
            description=(
                'Una recomendación buena según métrica X podría ser mala según Y. '
                'VALIDAR con múltiples perspectivas. '
                'Consensus > Métrica única.'
            ),
            importance='High',
            foundational_papers=[
                'Kuncheva (2014) - Combining Pattern Classifiers',
                'Wolpert (1992) - Stacked Generalization'
            ],
            application_to_trading=(
                'Paper recomendado debe ser: '
                'BUENO según IR score AND credibilidad AND novedad AND honestidad. '
                'No confiar en métrica única. '
                'Si paper es: relevante (sí) + credible (sí) + nuevo (sí) + honesto (NO) → RECHAZAR'
            ),
            anti_pattern='Validar con una sola métrica. Ignorar perspectivas alternativas.',
            validation_metric='Cross-Validation Score: Consensus de múltiples métricas.',
            examples=[
                'Validar: IR relevance AND Citation Authority AND Empirical Validation AND Honesty',
                'Si falla cualquiera, dudar de la recomendación'
            ]
        )
    
    def get_principle(self, principle_id: str) -> Optional[MetaCognitivePrinciple]:
        """Retorna principio específico"""
        return self.principles.get(principle_id)
    
    def get_by_category(self, category: MetaCognitiveCategory) -> List[MetaCognitivePrinciple]:
        """Retorna principios por categoría"""
        return [p for p in self.principles.values() if p.category == category]
    
    def get_all_categories(self) -> List[MetaCognitiveCategory]:
        """Retorna todas las categorías"""
        return sorted(set(p.category for p in self.principles.values()))
    
    def synthesize_for_prompt(self) -> str:
        """
        Sintetiza TODOS los principios para pasar a Claude
        Este es el contexto que le hace entender CÓMO RECOMENDAR
        """
        
        synthesis = """
# PRINCIPIOS META-COGNITIVOS DE RECOMENDACIÓN
# Para usar antes de sugerir papers sobre trading

## ¿Por qué esto?
Antes de que me sugieraspapers sobre VWAP, OBI, Delta, 
PRIMERO debes entender CÓMO HACER BUENAS RECOMENDACIONES.

## Categorías de Principios

"""
        
        for category in self.get_all_categories():
            principles = self.get_by_category(category)
            synthesis += f"\n### {category.value.upper()}\n\n"
            
            for p in principles:
                synthesis += f"**{p.title}**\n"
                synthesis += f"{p.description}\n"
                synthesis += f"Importancia: {p.importance}\n"
                synthesis += f"Aplicación al trading: {p.application_to_trading}\n"
                synthesis += f"Anti-patrón: {p.anti_pattern}\n"
                synthesis += f"Validación: {p.validation_metric}\n\n"
        
        synthesis += """
## Cómo Usar Estos Principios

Cuando me pidas que sugiera papers sobre VWAP/OBI/Delta:

1. PRIMERO: Aplicar principios metacognitivos
2. LUEGO: Usar búsqueda semántica (relevancia)
3. LUEGO: Filtrar por credibilidad
4. LUEGO: Validar diversidad (no redundancia)
5. FINALMENTE: Retornar sugerencias con explicación

Ejemplo:
✓ "Sugerencia de paper X porque:
   - Relevancia: 0.94 (búsqueda semántica)
   - Credibilidad: IEEE peer-reviewed
   - Novedad: 2024 (reciente)
   - Honestidad: Menciona limitaciones
   - Diversidad: Enfoque diferente a paper Y"

✗ "Aquí hay papers sobre VWAP" (sin explicación)

## Recuerda
Una recomendación BUENA requiere entender principios,
no solo listar papers. Este contexto te ENTRENA para hacerlo bien.
"""
        
        return synthesis
    
    def create_improved_trading_prompt(self) -> str:
        """
        Crea prompt MEJORADO para Claude cuando pida papers sobre trading
        
        Este prompt incorpora los principios meta-cognitivos
        """
        
        metacognitive_context = self.synthesize_for_prompt()
        
        improved_prompt = f"""
{metacognitive_context}

---

## AHORA: Sugiere Papers Sobre Trading

Necesito papers sobre estos temas para un sistema de trading algorítmico (CGAlpha v2):

1. **VWAP Real-time:** Barrera dinámica para detección de ruptura en scalping FX 1-min
2. **Order Book Imbalance (OBI):** Confirmación de entrada basada en microestructura
3. **Cumulative Delta:** Stop dinámico basado en agotamiento de flujo

### Criterios de Sugerencia (APLICAR PRINCIPIOS ARRIBA)

Para CADA paper sugerido:

✓ Debe ser peer-reviewed O de fuente profesional confiable (credibilidad)
✓ Debe tener validación empírica (backtest, live trading) (empirical validation)
✓ Debe mencionar límites o cuándo NO funciona (transparency)
✓ Debe ser relevante específicamente a VWAP real-time / OBI / Delta (relevance)
✓ Debe ser diferente conceptualmente de otros papers sugeridos (diversity)

### Formato de Respuesta

Para cada paper:

```json
{{
  "title": "Paper Title",
  "authors": ["Author1", "Author2"],
  "year": 2024,
  "doi_or_arxiv": "10.xxxx/xxxx o arXiv:2401.xxxxx",
  "credibility": "IEEE | Peer-Reviewed | Professional | Blog",
  
  "why": "Explicación de por qué fue sugerido (1-2 párrafos referenciando principios)",
  "relevance": 0.95,  # 0-1
  "has_empirical_validation": true,
  "mentions_limitations": true,
  "application_area": "VWAP | OBI | Cumulative Delta",
  
  "key_concepts": ["concept1", "concept2"],
  "contradicts_other_suggestions": false,  # Es diferente a otros papers?
}}
```

### Restricción Anti-Alucinación

✓ SOLO sugiere papers que puedas verificar (DOI válido o ArXiv ID)
✗ NO inventes papers. Si no estás seguro, omite

Procede a sugerir papers ahora.
"""
        
        return improved_prompt
