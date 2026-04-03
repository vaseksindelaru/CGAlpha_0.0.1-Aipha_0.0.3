"""
Intelligent Curator: Orquesta el sistema de conocimiento
Genera prompts mejorados para Claude basándose en Fase 0
"""

from typing import Dict, List, Optional
import json

from cgalpha_v2.knowledge_base.retrieval import KnowledgeRetriever


class IntelligentCurator:
    """
    Curador inteligente que:
    1. Entiende principios de recomendación
    2. Recupera papers inteligentemente
    3. Genera prompts mejorados para Claude
    4. Valida outputs de Claude
    """
    
    def __init__(self):
        self.retriever = KnowledgeRetriever()
    
    def generate_paper_recommendation_prompt(
        self,
        task: str,
        context: str,
        additional_constraints: Optional[List[str]] = None
    ) -> str:
        """
        Genera prompt mejorado para Claude para recomendar papers
        
        Incorpora principios de Fase 0 automáticamente
        """
        
        # Obtener contexto de conocimiento
        synthesis = self.retriever.synthesize_context(context)
        
        # Obtener principios de recomendación
        principles_text = self.retriever.principles_lib.get_all_principles_text()
        
        # Construir prompt
        prompt = f"""
# TAREA: {task}

## PRINCIPIOS DE RECOMENDACIÓN INTELIGENTE

Basándote en estos PRINCIPIOS FUNDAMENTALES, realiza la tarea indicada:

{principles_text}

## CONTEXTO ESPECÍFICO

{synthesis}

## RESTRICCIONES

Cuando recomiendes papers, ASEGÚRATE DE:

1. **Relevancia Contextual (rs_001):** Considera el CONTEXTO actual, no solo papers genéricamente buenos
2. **Diversidad (rs_002):** Recomienda perspectivas distintas, no solo variaciones del mismo tema
3. **Credibilidad (rs_003):** Prioriza papers peer-reviewed, validación empírica
4. **Búsqueda Semántica (ir_001):** Piensa en CONCEPTOS similares, no solo palabras iguales
5. **Relevancia > Popularidad (ir_002):** Busca relevancia al caso, no solo papers muy citados
6. **Validación Empírica (cur_001):** Preferir papers con backtest, live trading, datos reales
7. **Limitaciones Transparentes (cur_002):** Asigna MÁS puntos a papers que mencionan qué NO funciona
8. **Ejemplos en Prompt (llm_001):** Toma en cuenta los papers ejemplos para entender qué tipo de papers esperas
9. **Validación LLM (llm_002):** Si recomiendan papers, son REALES y correctamente descritos
10. **Jerarquía Conceptual (tax_001):** Organiza recomendaciones de GENERAL → ESPECÍFICO
11. **Relaciones Cross-cutting (tax_002):** Vincula papers que se relacionan aunque sean de temas distintos
12. **Métricas Apropiadas (bench_001):** Usa métricas relevantes para validar recomendación
13. **Validación Cruzada (bench_002):** Valida con múltiples perspectivas antes de recomendar

{self._format_additional_constraints(additional_constraints)}

## SALIDA ESPERADA

Para CADA paper que recomiendes, incluye:

```json
{{
  "title": "Título del paper",
  "authors": ["Author1", "Author2"],
  "year": 2024,
  "why": "Explicación de por qué es relevante (refiere a principios)",
  "credibility": "Nivel de credibilidad",
  "empirical": true/false,
  "live_tested": true/false,
  "applications": ["aplicación1", "aplicación2"],
  "limitations": ["limitación1", "limitación2"],
  "connection_to_other": ["Paper A", "Paper B"],
  "confidence": 0.95
}}
```

---

## EJEMPLO: Lo Que NO Queremos

❌ "Aquí hay 10 papers sobre VWAP que encontré en Google Scholar"

## EJEMPLO: Lo Que SÍ Queremos

✅ "Para {context}, recomiendo estos papers porque:
- Todos tienen validación empírica (Principio cur_001)
- Cubren perspectivas distintas: teoría, implementación, límites (Principio rs_002)
- Todos peer-reviewed o profesionales conocidos (Principio rs_003)
- Específicamente relevantes a tu contexto {context} (Principio rs_001)
- Cada uno menciona qué NO funciona (Principio cur_002)"

---

Procede a realizar la tarea.
"""
        
        return prompt
    
    def _format_additional_constraints(self, constraints: Optional[List[str]]) -> str:
        """Formatea restricciones adicionales"""
        
        if not constraints:
            return ""
        
        formatted = "\n## RESTRICCIONES ADICIONALES\n\n"
        for i, constraint in enumerate(constraints, 1):
            formatted += f"{i}. {constraint}\n"
        
        return formatted
    
    def generate_llm_context_for_trading_entry(self) -> str:
        """Genera contexto de Claude para decisión de entrada"""
        
        return self.retriever.synthesize_context('trading_entry_validation')
    
    def generate_llm_context_for_trading_exit(self) -> str:
        """Genera contexto de Claude para decisión de salida"""
        
        return self.retriever.synthesize_context('trading_exit_strategy')
    
    def validate_paper_recommendation(
        self,
        llm_output: Dict
    ) -> Dict:
        """
        Valida que recomendación de Claude es coherente
        Detecta alucinaciones
        """
        
        validation_result = {
            'valid': True,
            'issues': [],
            'confidence': 1.0
        }
        
        # Validar que paper existe
        paper_id = llm_output.get('paper_id')
        if paper_id:
            paper = self.retriever.trading_lib.get_paper(paper_id)
            if not paper:
                validation_result['valid'] = False
                validation_result['issues'].append(f"Paper {paper_id} no existe en biblioteca")
                validation_result['confidence'] = 0.0
                return validation_result
        
        # Validar que authors están correctos
        if 'authors' in llm_output:
            # TODO: verificar contra base de datos
            pass
        
        # Validar que año es razonable
        if 'year' in llm_output:
            year = llm_output['year']
            if not (1950 <= year <= 2025):
                validation_result['issues'].append(f"Año {year} fuera de rango")
        
        # Validar que tiene explicación
        if not llm_output.get('why'):
            validation_result['issues'].append("Falta explicación de relevancia")
        
        # Calcular confianza
        if validation_result['issues']:
            validation_result['confidence'] = max(0.5, 1.0 - len(validation_result['issues']) * 0.2)
        
        return validation_result
    
    def get_statistics(self) -> Dict:
        """Retorna estadísticas de la biblioteca"""
        
        all_papers = self.retriever.trading_lib.get_all_papers()
        empirically_validated = self.retriever.trading_lib.get_empirically_validated()
        live_tested = self.retriever.trading_lib.get_live_tested()
        
        return {
            'total_papers': len(all_papers),
            'empirically_validated': len(empirically_validated),
            'live_tested': len(live_tested),
            'avg_citations': sum(p.citation_count for p in all_papers) / len(all_papers) if all_papers else 0,
            'papers_with_limitations': sum(1 for p in all_papers if p.limitations),
            'principles_count': len(self.retriever.principles_lib.principles),
        }
    
    def export_library_metadata(self) -> str:
        """Exporta metadata de la biblioteca como JSON"""
        
        data = {
            'principles': json.loads(self.retriever.principles_lib.export_as_json()),
            'papers_count': len(self.retriever.trading_lib.get_all_papers()),
            'statistics': self.get_statistics(),
        }
        
        return json.dumps(data, indent=2, ensure_ascii=False)
