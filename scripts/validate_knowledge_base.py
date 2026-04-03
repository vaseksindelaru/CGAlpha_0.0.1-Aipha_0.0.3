import pandas as pd
import json
from collections import Counter, defaultdict
from pathlib import Path

class KnowledgeBaseValidator:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)
        self.analysis = {}
    
    def validate_structure(self):
        """Valida que CSV tenga estructura mínima requerida"""
        required_cols = ['título', 'año', 'concepto_primario', 'tipo_señal', 
                        'abstract_resumen', 'doi', 'fecha_agregado']
        
        missing = set(required_cols) - set(self.df.columns)
        if missing:
            raise ValueError(f"Columnas faltantes: {missing}")
        
        print(f"✅ Estructura válida. Columnas: {list(self.df.columns)}")
        return True
    
    def count_papers(self):
        """Cuenta papers en CSV"""
        count = len(self.df)
        print(f"✅ Total papers: {count}")
        return count
    
    def analyze_concepts(self):
        """Analiza distribución de conceptos primarios"""
        concept_dist = self.df['concepto_primario'].value_counts()
        self.analysis['concept_distribution'] = concept_dist.to_dict()
        print(f"📊 Distribución de conceptos:\n{concept_dist}")
        return concept_dist
    
    def analyze_signal_types(self):
        """Analiza tipos de señal"""
        signal_dist = self.df['tipo_señal'].value_counts()
        self.analysis['signal_distribution'] = signal_dist.to_dict()
        print(f"📊 Distribución de tipos de señal:\n{signal_dist}")
        return signal_dist
    
    def analyze_year_range(self):
        """Analiza rango temporal de papers"""
        year_min, year_max = self.df['año'].min(), self.df['año'].max()
        year_dist = self.df['año'].value_counts().sort_index()
        self.analysis['year_range'] = {'min': int(year_min), 'max': int(year_max)}
        self.analysis['year_distribution'] = year_dist.to_dict()
        print(f"📊 Rango de años: {year_min}-{year_max}\nDistribución:\n{year_dist}")
        return year_min, year_max
    
    def identify_emerging_patterns(self):
        """Identifica patrones naturales que emergen de los datos"""
        patterns = {}
        
        # Patrón 1: Conceptos y sus tipos de señal asociados
        concept_signal_map = defaultdict(set)
        for _, row in self.df.iterrows():
            concept_signal_map[row['concepto_primario']].add(row['tipo_señal'])
        
        patterns['concept_signal_associations'] = {
            k: list(v) for k, v in concept_signal_map.items()
        }
        
        # Patrón 2: Qué información falta en abstracts
        abstract_lengths = self.df['abstract_resumen'].str.len()
        patterns['abstract_stats'] = {
            'min_length': int(abstract_lengths.min()),
            'max_length': int(abstract_lengths.max()),
            'avg_length': int(abstract_lengths.mean())
        }
        
        # Patrón 3: Cobertura temporal
        papers_per_decade = self.df['año'] // 10 * 10
        patterns['temporal_coverage'] = papers_per_decade.value_counts().sort_index().to_dict()
        
        self.analysis['emerging_patterns'] = patterns
        print(f"🔍 Patrones emergentes:\n{json.dumps(patterns, indent=2)}")
        return patterns
    
    def recommend_new_columns(self):
        """Recomienda columnas adicionales basadas en análisis"""
        recommendations = {
            'papers_relacionados': 'Conexiones entre papers (descubrir manualmente en Semana 2)',
            'subtemas': 'Sub-categorías de concepto_primario (ej: VWAP → scalping vs block trading)',
            'relevancia_scores': 'Scores de relevancia para cada concepto (para Capa 2 búsqueda)',
            'palabras_clave': 'Tags para full-text search (para Capa 2 búsqueda)',
            'nivel_dificultad': 'Intro/Intermedio/Avanzado (para Capa 4 LLM)',
        }
        
        print(f"\n💡 Columnas recomendadas para Semana 3:\n")
        for col, reason in recommendations.items():
            print(f"  - {col}: {reason}")
        
        self.analysis['recommended_columns'] = recommendations
        return recommendations
    
    def generate_report(self, output_path):
        """Genera reporte de análisis"""
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'total_papers': len(self.df),
            'analysis': self.analysis
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n📄 Reporte guardado en: {output_path}")
        return report
    
    def run_full_analysis(self, output_path='analysis_report.json'):
        """Ejecuta análisis completo"""
        print("=" * 60)
        print("VALIDADOR: Knowledge Base Semana 1")
        print("=" * 60)
        
        self.validate_structure()
        self.count_papers()
        self.analyze_concepts()
        self.analyze_signal_types()
        self.analyze_year_range()
        self.identify_emerging_patterns()
        self.recommend_new_columns()
        self.generate_report(output_path)
        
        print("\n" + "=" * 60)
        print("✅ FASE 1 VALIDADA. Listos para Semana 2: Análisis de Patrones")
        print("=" * 60)

if __name__ == "__main__":
    csv_path = Path(__file__).parent.parent / "knowledge_base_v1.csv"
    validator = KnowledgeBaseValidator(csv_path)
    validator.run_full_analysis(
        output_path=Path(__file__).parent.parent / "analysis_week1_patterns.json"
    )
