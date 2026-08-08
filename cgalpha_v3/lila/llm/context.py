"""
cgalpha_v3/lila/llm/context.py - Technical Context Builder for Lila v3.

Gathers relevant project snippets and builds structured prompts for 
technical assistance and requirements architecture.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Construye el contexto técnico para las consultas de Lila.
    Recuperado de la infraestructura v1/v2 y optimizado para v3.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve()
        
        # Archivos clave para contexto general (Sección A/C/D)
        self.priority_files = [
            "LILA_v3_NORTH_STAR.md",
            "cgalpha_v3/domain/models/signal.py",
            "cgalpha_v3/application/change_proposer.py",
            "legacy_vault/v1/cgalpha/nexus/coordinator.py",
            "legacy_vault/v1/cgalpha/labs/risk_barrier_lab.py",
            "README.md"
        ]
        self.vault_dir = self.root_dir / "legacy_vault"

    def build_technical_context(self, 
                                 query: str, 
                                 max_files: int = 5, 
                                 max_chars_per_file: int = 1000) -> str:
        """
        Busca archivos relevantes basados en la consulta y extrae fragmentos.
        """
        candidates = list(self.priority_files)
        
        # Heurística simple de búsqueda de archivos por palabra clave
        query_lower = query.lower()
        if "llm" in query_lower or "lila" in query_lower:
            candidates.insert(0, "cgalpha_v3/lila/llm/assistant.py")
        if "gui" in query_lower or "server" in query_lower:
            candidates.insert(0, "cgalpha_v3/gui/server.py")
        if "risk" in query_lower or "circuit" in query_lower:
            candidates.insert(0, "cgalpha_v3/risk/health_monitor.py")
            
        snippets: List[str] = []
        seen = set()
        
        for rel_path in candidates:
            if len(snippets) >= max_files:
                break
                
            file_path = self.root_dir / rel_path
            if not file_path.exists() or file_path in seen:
                continue
                
            seen.add(file_path)
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                excerpt = content[:max_chars_per_file].strip()
                if excerpt:
                    snippets.append(f"--- FILE: {rel_path} ---\n{excerpt}")
            except Exception as e:
                logger.warning(f"Could not read {rel_path} for context: {e}")
                
        architecture_hint = (
            "Architecture V3: Domain-driven design. Namespaces: cgalpha_v3.lila (Intelligence), "
            "cgalpha_v3.risk (Safety), cgalpha_v3.application (Logic)."
        )
        
        return architecture_hint + "\n\n" + "\n\n".join(snippets)

    def get_mentor_prompt(self, query: str, context: str) -> str:
        """Prompt para el rol de Mentor Técnico (Librarian)."""
        return f"""
Eres "Lila: Mentor Técnico v3", el núcleo de inteligencia de CGAlpha.

TU MISIÓN:
1) Explicar la arquitectura y el flujo de trabajo de la v3 con máxima claridad.
2) Mantener la integridad de la v3: no propongas cambios que violen la Constitución o añadan capas innecesarias.
3) Si falta información, pide el archivo específico.

REGLA DE ORO: No apruebes refactors masivos sin justificación científica.

CONTEXTO DEL PROYECTO:
{context}

PREGUNTA TÉCNICA:
{query}
""".strip()

    def get_requirements_prompt(self, query: str, context: str) -> str:
        """Prompt para el rol de Arquitecto de Requisitos (Layer 3)."""
        return f"""
Eres "Lila: Arquitecto de Requisitos v3". Tu rol es traducir ideas en especificaciones técnicas.

TU TAREA:
- Analizar la viabilidad técnica en la v3.
- Definir: Problema, Alcance (In/Out), Riesgos y Criterios de Aceptación.
- NO generes código, solo la especificación funcional.

IMPORTANTE: Prioriza la seguridad (Risk Management) y la trazabilidad (Library).

CONTEXTO TÉCNICO:
{context}

IDEA/REQUERIMIENTO:
{query}

DEVUELVE TU RESPUESTA EN FORMATO MARKDOWN ESTRUCTURADO.
""".strip()
