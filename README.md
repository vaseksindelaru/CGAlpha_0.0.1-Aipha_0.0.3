<p align="center">
  <img src="logo.png" alt="cgAlpha_0.0.1" width="200"/>
</p>

<h1 align="center">cgAlpha_0.0.1</h1>
<p align="center"><em>Causal Graph Alpha — Sistema de Trading Algorítmico con Evolución Autónoma Supervisada</em></p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.0.1-blue" alt="version"/>
  <img src="https://img.shields.io/badge/tests-144%20passing-brightgreen" alt="tests"/>
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="python"/>
  <img src="https://img.shields.io/badge/license-private-lightgrey" alt="license"/>
</p>

---

## ¿Qué es cgAlpha?

cgAlpha es un sistema de trading algorítmico para BTCUSDT que combina detección de zonas técnicas, microestructura de mercado y un oráculo de machine learning, todo supervisado por una IA constructora llamada **Lila**.

Lo que distingue a cgAlpha de otros sistemas de trading algorítmico es su **canal de evolución autónoma**: el sistema puede detectar sus propios problemas, proponer mejoras, implementarlas en código, testearlas, y persistirlas — con niveles graduales de supervisión humana.

## Arquitectura

```
┌──────────────────────────────────────────────────────────┐
│                    PIPELINE DE TRADING                    │
│  BinanceVision → TripleCoincidence → Oracle → ShadowTrader│
│                                                          │
│  Detecta zonas → Monitorea retests → Predice outcome →   │
│  Ejecuta en shadow → Persiste en bridge.jsonl            │
└──────────────────────────┬───────────────────────────────┘
                           │ métricas + drift
                           ▼
┌──────────────────────────────────────────────────────────┐
│                 CANAL DE EVOLUCIÓN (v4)                   │
│  AutoProposer → Orchestrator → CodeCraftSage             │
│                                                          │
│  Detecta drift → Clasifica propuesta (Cat.1/2/3) →       │
│  Implementa cambio → Tests → git commit                  │
└──────────────────────────┬───────────────────────────────┘
                           │ resultados + reflexiones
                           ▼
┌──────────────────────────────────────────────────────────┐
│                  MEMORIA INTELIGENTE                      │
│  7 niveles: RAW → NORMALIZED → FACTS → RELATIONS →       │
│  PLAYBOOKS → STRATEGY → IDENTITY                         │
│                                                          │
│  Persistencia a disco · Inmunidad IDENTITY a régimen ·    │
│  Reflexiones críticas con validación OOS                  │
└──────────────────────────────────────────────────────────┘
```

## Quickstart

```bash
# Instalar dependencias
pip install -e .

# Ejecutar tests
python -m pytest cgalpha_v3/tests/ -v

# Iniciar el Control Room (GUI)
python -m cgalpha_v3.gui.server
# → http://localhost:5000
```

## Estructura del proyecto

```
cgAlpha_0.0.1/
├── cgalpha_v3/              # Código fuente del pipeline y componentes
│   ├── application/         # Pipeline, ExperimentRunner, ChangeProposer
│   ├── domain/              # Modelos: Signal, Proposal, TechnicalSpec
│   ├── gui/                 # Control Room (Flask, dark premium theme)
│   ├── infrastructure/      # TripleCoincidenceDetector, BinanceVision
│   ├── learning/            # MemoryPolicyEngine (7 niveles)
│   ├── lila/                # CodeCraftSage, Oracle, LLM Switcher
│   │   └── llm/             # Providers: OpenAI, Ollama, Zhipu
│   ├── trading/             # ShadowTrader, DryRunOrderManager
│   └── tests/               # 144+ tests (pytest)
│
├── cgalpha_v4/              # Prompt Fundacional de Lila
│   ├── LILA_V4_PROMPT_FUNDACIONAL.md   # §0–§1
│   ├── S2_MISION_PRIMARIA.md           # §2
│   ├── S3_ORDEN_DE_CONSTRUCCION.md     # §3
│   ├── S4_ORCHESTRATOR_V4_SPEC.md      # §4
│   ├── S5_MEMORIA_INTELIGENTE_V4.md    # §5
│   ├── S6_INDEPENDENCIA_PROGRESIVA.md  # §6
│   ├── S7_ANTIPATRONES.md             # §7
│   ├── S8_ACTO_FUNDACIONAL.md         # §8
│   └── WHITEPAPER.md                  # White Paper (doc vivo)
│
├── legacy_vault/            # Documentación histórica (v1/v2)
├── logo.png                 # Logo cgAlpha_0.0.1
└── README.md                # Este fichero
```

## Documentación

| Documento | Propósito |
|---|---|
| [White Paper](cgalpha_v4/WHITEPAPER.md) | Descripción completa del sistema — mantenido por Lila |
| [Prompt Fundacional](cgalpha_v4/LILA_V4_PROMPT_FUNDACIONAL.md) | Instrucciones fundacionales de Lila |
| [NORTH STAR v3](LILA_v3_NORTH_STAR.md) | Arquitectura original de v3 |

## Nomenclatura

| Nombre | Significado |
|---|---|
| **cgAlpha_0.0.1** | El proyecto completo (Causal Graph Alpha, versión 0.0.1) |
| **Lila** | La IA constructora del sistema |
| Aipha | Nombre anterior del proyecto (pre-v1) |
| CGAlpha | Nombre legacy sin versión (v1-v3) |

## Historia del proyecto

```
Aipha_0.0.1 → Aipha_0.0.2 → aipha_0.1..0.3 → Aipha_1.1
                                                    ↓
                                            CGAlpha_0.0.1-Aipha_0.0.3 (v3)
                                                    ↓
                                            cgAlpha_0.0.1 (actual)
```

## Stack técnico

- **Lenguaje:** Python 3.10+
- **ML:** scikit-learn (RandomForest, meta-labeling)
- **Datos:** Binance Vision (BTCUSDT klines), pandas
- **GUI:** Flask + vanilla JS (dark premium theme)
- **LLM:** Multi-provider (Ollama local, OpenAI, Zhipu)
- **Tests:** pytest (144+ tests, walk-forward, no-leakage)
- **VCS:** git (feature branches, CodeCraftSage)

---

<p align="center">
  <em>Construido con Lila — La Constructora</em><br/>
  <em>cgAlpha_0.0.1 · Abril 2026</em>
</p>
