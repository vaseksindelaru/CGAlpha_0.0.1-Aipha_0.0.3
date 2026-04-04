# CGAlpha v3

**Versión:** 3.1-audit  
**Estado:** 🚧 FASE 0 — Encendido visible + seguridad base  
**Namespace activo:** `v3` (v1/v2 son solo-lectura sin `--allow-legacy`)

---

## ¿Qué es CGAlpha v3?

CGAlpha v3 es un sistema operativo de mejora continua para trading algorítmico, construido
con **GUI-first**, **trazabilidad científica**, **memoria estructurada** y una **capa de riesgo formal**.

> **REGLA DE PARADA ACTIVA:** No se opera en mercado real hasta que P0, P1 y P2 del
> `CHECKLIST_IMPLEMENTACION.md` estén completamente verificados.

---

## Principios No Negociables (orden de arranque)

1. GUI universal de control → observable desde minuto 0  
2. Data Quality Gates activos  
3. Risk Management Layer activo  
4. Motor de propuestas y ejecución  
5. Capacidades avanzadas  

---

## Estructura Objetivo (Fase 0 puede tener subset)

```
cgalpha_v3/
├── README.md                        ← este archivo
├── CHECKLIST_IMPLEMENTACION.md      ← gates P0-P3
├── PROMPT_MAESTRO_v3.1-audit.md     ← contrato de trabajo completo
│
├── gui/                             ← Control Room (GUI nativa)
│   ├── README.md
│   ├── server.py                    ← servidor FastAPI/Flask con auth
│   ├── static/
│   │   ├── index.html
│   │   ├── style.css
│   │   └── app.js
│   └── panels/
│       ├── mission_control.py
│       ├── market_live.py
│       ├── theory_live.py
│       ├── experiment_loop.py
│       ├── risk_dashboard.py
│       └── user_participation.py
│
├── domain/                          ← dominio puro v3
│   ├── README.md
│   ├── models/
│   │   ├── signal.py
│   │   ├── proposal.py
│   │   └── memory_entry.py
│   └── ports/
│       ├── data_port.py
│       ├── risk_port.py
│       └── library_port.py
│
├── application/                     ← casos de uso / orquestación
│   ├── README.md
│   ├── change_proposer.py
│   ├── experiment_runner.py
│   └── rollback_manager.py
│
├── infrastructure/                  ← adaptadores externos
│   ├── README.md
│   ├── binance_adapter.py
│   ├── duckdb_adapter.py
│   └── llm_adapter.py
│
├── risk/                            ← Risk Management Layer
│   ├── README.md
│   ├── circuit_breaker.py
│   ├── kill_switch.py
│   ├── position_sizer.py
│   └── drawdown_monitor.py
│
├── data_quality/                    ← Data Quality Gates
│   ├── README.md
│   ├── gates.py
│   └── validators.py
│
├── lila/                            ← Bibliotecario central
│   ├── README.md
│   ├── library_manager.py
│   ├── source_classifier.py
│   └── ingestion_pipeline.py
│
├── learning/                        ← Memoria y aprendizaje
│   ├── README.md
│   ├── memory_policy.py
│   ├── learning_capsule.py
│   └── fields/
│       ├── codigo.py
│       ├── math.py
│       ├── trading.py
│       ├── architect.py
│       └── memory_librarian.py
│
├── trading/                         ← Detectores, labelers, taxonomía
│   ├── README.md
│   ├── detectors/
│   │   └── zone_detector.py
│   └── labelers/
│       └── triple_barrier.py
│
├── memory/                          ← Snapshots, iteraciones, rollback
│   ├── snapshots/
│   ├── iterations/
│   └── archive/
│
├── docs/                            ← Documentación viva
│   ├── adr/
│   ├── post_mortems/
│   └── promotions/
│
├── knowledge_base/
│   └── experiments/
│
└── tests/                           ← Tests por contexto
    ├── test_risk.py
    ├── test_data_quality.py
    ├── test_lila.py
    └── test_rollback.py
```

---

## Inicio Rápido (Fase 0)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Arrancar GUI (Control Room)
python cgalpha_v3/gui/server.py

# Abrir en navegador: http://localhost:8080
# Token Bearer por defecto: cgalpha-v3-local-dev
```

---

## Fases de Desarrollo

| Fase | Nombre | Estado |
|------|--------|--------|
| 0 | Encendido visible + seguridad base | 🚧 En progreso |
| 1 | Data Quality + Biblioteca viva | ⏳ Pendiente |
| 2 | Risk Management + Learning sincronizado | ⏳ Pendiente |
| 3 | Loop de mejora científica | ⏳ Pendiente |
| 4 | Hardening y Production Gate | ⏳ Pendiente |

---

## Reglas de Namespace

- `v3` → namespace activo de trabajo  
- `v1`/`v2` → solo lectura; cambios requieren `--allow-legacy`  
- Todo cambio en v3 queda registrado en `memory/iterations/`

---

*Construido mientras se ve, se entiende y se decide — nunca en oculto.*
