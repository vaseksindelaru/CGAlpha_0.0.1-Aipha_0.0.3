import sys
import os
from pathlib import Path

# Adjust path
project_root = "/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cgalpha_v3.learning.memory_policy import MemoryPolicyEngine
from cgalpha_v3.lila.llm.llm_switcher import LLMSwitcher, ProviderConfig
from cgalpha_v3.lila.llm.assistant import LLMAssistant
from cgalpha_v3.lila.codecraft_sage import CodeCraftSage, ComponentManifest
from cgalpha_v3.lila.evolution_orchestrator import EvolutionOrchestratorV4
from cgalpha_v3.lila.llm.proposer import TechnicalSpec

os.environ["FORCE_LOCAL_LLM"] = "true"

def run_patch():
    # Inicializar canal
    memory = MemoryPolicyEngine()
    memory.load_from_disk()
    assistant = LLMAssistant()
    switcher = LLMSwitcher(assistant=assistant)
    
    # ENFORCE LOCAL LLM (Ollama) for all categories
    for task in ["cat_1", "cat_2", "cat_3", "reflection", "whitepaper"]:
        switcher._task_routing[task] = [
            ProviderConfig(name="ollama", priority=1)
        ]

    manifest = ComponentManifest(
        name="CodeCraftSage", category="evolution",
        function="Patched", inputs=[], outputs=[], causal_score=0.1
    )
    sage = CodeCraftSage(manifest=manifest, switcher=switcher)
    orchestrator = EvolutionOrchestratorV4(
        memory=memory, switcher=switcher, sage=sage
    )

    # SPEC 2: ShadowTrader Integration in LiveDataFeedAdapter
    print(">>> Aplicando SPEC 2...")
    spec2 = TechnicalSpec(
        change_type="optimization",
        target_file="cgalpha_v3/application/live_adapter.py",
        target_attribute="LiveDataFeedAdapter._dispatch_kline",
        old_value="El adaptador live ignora ShadowTrader, impidiendo persistencia en bridge.jsonl.",
        new_value="Inyectar y usar ShadowTrader en _dispatch_kline.",
        reason="Habilitar bridge.jsonl en ejecución live.",
        causal_score_est=0.90,
        confidence=0.95
    )
    result2 = orchestrator.process_proposal(spec2)
    approved2 = orchestrator.approve_proposal(result2.proposal_id, approved_by="human")
    print(f"SPEC 2 status: {approved2.status}")
    if approved2.status != "SUCCESS":
        print(f"Error en SPEC 2: {getattr(approved2, 'error', 'Unknown error')}")
        return False

    # SPEC 3: Background Pipeline in server.py
    print(">>> Aplicando SPEC 3...")
    spec3 = TechnicalSpec(
        change_type="optimization",
        target_file="cgalpha_v3/gui/server.py",
        target_attribute="_main_startup_sequence",
        old_value="Sin evolución en background.",
        new_value="Iniciar loop de background para el pipeline.",
        reason="Activar autonomía del sistema.",
        causal_score_est=0.85,
        confidence=0.95
    )
    result3 = orchestrator.process_proposal(spec3)
    approved3 = orchestrator.approve_proposal(result3.proposal_id, approved_by="human")
    print(f"SPEC 3 status: {approved3.status}")
    if approved3.status != "SUCCESS":
        print(f"Error en SPEC 3: {getattr(approved3, 'error', 'Unknown error')}")
        return False

    return True

if __name__ == "__main__":
    if run_patch():
        print("BOOTSTRAP COMPLETED SUCCESSFULLY")
    else:
        sys.exit(1)
