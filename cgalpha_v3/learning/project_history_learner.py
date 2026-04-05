"""
CGAlpha v3 — Project History Learner (Deep Learning Ingestion)
=============================================================
Analiza artefactos de iteración y ADRs para inyectar sabiduría de alto nivel.
Implementa el requerimiento de "Aprender de lo construido".
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
from cgalpha_v3.domain.models.signal import MemoryLevel, MemoryEntry
from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine

class ProjectHistoryLearner:
    def __init__(self, memory_engine: MemoryPolicyEngine, base_dir: Path):
        self.memory_engine = memory_engine
        self.base_dir = base_dir
        # Ajustamos rutas para ser robustos
        self.iterations_dir = base_dir / "cgalpha_v3" / "memory" / "iterations"
        self.adr_dir = base_dir / "cgalpha_v3" / "docs" / "adr"

    def learn_from_history(self) -> dict[str, Any]:
        """Escanea, analiza e ingesta conocimiento de la construcción del sistema."""
        stats = {
            "status": "success",
            "iterations_found": 0,
            "adrs_found": 0,
            "entries_created": 0,
            "top_insights": []
        }
        
        # 1. Analizar Iteraciones (Aprendizaje de procesos)
        if self.iterations_dir.exists():
            # Ordenar por fecha si es posible
            iters = sorted(list(self.iterations_dir.iterdir()), key=lambda p: p.name, reverse=True)
            for iter_path in iters[:50]: # Limitar a las últimas 50 para no saturar memoria RAW
                if iter_path.is_dir():
                    summary_file = iter_path / "iteration_summary.md"
                    if summary_file.exists():
                        stats["iterations_found"] += 1
                        content = summary_file.read_text()
                        
                        # Ingesta como FACT (Nivel 2) o RELATION (Nivel 3)
                        # Usamos level FACT por defecto, pero si es 'summary' sube a RELATIONS
                        target_level = MemoryLevel.FACTS
                        if "Summary" in content or "Conclusion" in content:
                            target_level = MemoryLevel.RELATIONS
                            
                        entry = self.memory_engine.ingest_raw(
                            content=f"LEARNED-STEP: {content[:3000]}",
                            field="architect",
                            source_id=f"iter_{iter_path.name}",
                            source_type="primary",
                            tags=["v3-history", "iterative-learning", iter_path.name]
                        )
                        
                        # Promoción automática por Lila
                        self.memory_engine.promote(
                            entry_id=entry.entry_id, 
                            target_level=target_level, 
                            approved_by="Lila",
                            tags=["verified-history"]
                        )
                        stats["entries_created"] += 1
                        
                        if len(stats["top_insights"]) < 5:
                            title = content.split('\n')[0].strip('# ')
                            stats["top_insights"].append(title)

        # 2. Analizar ADRs (Sabiduría Arquitectónica)
        if self.adr_dir.exists():
            adrs = sorted(list(self.adr_dir.glob("*.md")), key=lambda p: p.name, reverse=True)
            for adr_file in adrs[:30]:
                stats["adrs_found"] += 1
                content = adr_file.read_text()
                
                # Las ADRs son sabiduría pura -> RELATIONS (Nivel 3)
                entry = self.memory_engine.ingest_raw(
                    content=f"ADR-WISDOM: {content[:3000]}",
                    field="architect",
                    source_id=f"adr_{adr_file.name}",
                    source_type="primary",
                    tags=["v3-history", "adr-wisdom", "architectural-design"]
                )
                
                self.memory_engine.promote(
                    entry_id=entry.entry_id, 
                    target_level=MemoryLevel.RELATIONS, 
                    approved_by="Lila"
                )
                stats["entries_created"] += 1

        return stats
