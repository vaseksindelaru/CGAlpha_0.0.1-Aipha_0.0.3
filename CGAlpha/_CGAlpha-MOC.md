---
type: project-moc
project: CGAlpha
tags:
  - proyecto/cgalpha
  - moc
created: 2026-07-20
P26-08-01
---

# 🟢 CGAlpha v3 — Índice del Proyecto (MOC)

> [!info] Punto de entrada del proyecto. Todo lo de CGAlpha vive bajo `CGAlpha/`.
> Cada sesión de trabajo va en `CGAlpha/sessions/` con tag `#proyecto/cgalpha`.

## 📌 Qué es
Sistema de trading algorítmico. BTCUSDT 5min, estrategia de triple coincidencia.

## 🔑 Datos clave (fuente de verdad)
- **Features reales del oracle**: 23 (12 extra vs 11 esperado). NO usa `l2tp_*`.
- `test_oracle_encoding.py` está en `/tests/` (root), NO en `cgalpha_v3/tests/`.
- Los tests fallan porque se añadieron features DESPUÉS de escribir los tests.
- Hay `.venv` en el proyecto — usar para pytest.
- **Evaluación externa obsoleta** — 3 meses atrás decía "113 tests, 6 bugs" cuando la realidad es 401 tests (395/6) y 8 bugs originales ya resueltos.
- **Gobernanza constitucional** nueva — ciclo ANOMALY → LIBRARY, P0-P9 priority table en NEXUS_SUPERIOR.md.
- **QUARANTINE_GATE y READY_FOR_CODEX** verificados como cero código — solo checklist manual en §9 de NEXUS_SUPERIOR.md. Sin enforcement automático.
- **P6.5 Lila GUI** ya resuelto por el propio P0-P9: prerequisito es Orchestrator v5 estable, que se autodeclara baja urgencia mientras P1-P4 activos.

## 🗂️ Sesiones
- `CGAlpha/sessions/2026-08-01-restart-cgalpha-fix.md` — Restart Cgalpha Fix
- `CGAlpha/sessions/2026-07-29-cloud-infra.md` — Cloud Infra
- `CGAlpha/sessions/2026-07-27_vault-learning-development.md` — Vault Learning Development
- Ver todas: buscar `path:CGAlpha/sessions`

## 📚 Learning (Clases Magistrales)
Secciones teóricas que construyen comprensión profunda del sistema.
- **Índice**: `learning/00-índice.md`
- **01** — El Viaje de un Dato (json, Oracle→GUI, puente HTTP)
- **02** — Arquitectura y OOP (clases, dataclass, factory)
- **03** — Manipulación de Datos y ML (pandas, scikit-learn, pipeline)
- **04** — Testing — El Sistema Inmunológico (pytest, fixtures, Triple Barrier)
- **05** — Síntesis Final — Los Cinco Hilos
- **06** — Graphify como Tutor Activo (flujo de 5 pasos, aplicado sobre las comunidades del grafo)

> 📖 Lee en orden. Cada clase construye sobre la anterior.
> 🔧 Cada clase incluye sección de práctica con graphify.
> **Clase 6**: no se lee de principio a fin — se ejecuta (Paso 1 al 5, con acciones y preguntas).

## 🔧 Development (S2 — Próximos Pasos)
Área de desarrollo activo.
- **Índice**: `development/00-roadmap-s2.md`
- **01** — max_price_since_detection (fix del fixture listo para aplicar — diagnóstico completo)
- **02** — Gobernanza NEXUS_SUPERIOR (P0-P9, ciclo de vida, QUANTINE_GATE verificado como cero código)
- **03** — Auditoría LLM externo (evaluación verificada con distinción de confiabilidad: refutado vs verificado con alcance parcial)

## 🔗 Conocimiento aplicado
- [[Books/Philosophy-Software-Design/Applied-to-CGAlpha|Ousterhout aplicado a CGAlpha]]

## ⏭️ Pendientes verificados
- [ ] Aplicar fix del fixture de max_price_since_detection en repo real (el fix está propuesto en `development/01-max-price-since-detection.md`)
- [ ] Decidir si QUARANTINE_GATE sin enforcement automático es un riesgo aceitable para seguir trabajando en P1
- [ ] Reconciliar tests restantes con las 23 features reales (2 tests de feature count desactualizados)
- [ ] Completar Clase Magistral 6+ según avance de S2
- [ ] Profundizar NEXUS_SUPERIOR.md al 100% solo cuando una decisión concreta lo requiera

## 📊 Graphify Analysis
- **Analysis date**: 2026-07-27
- **Graph files**: `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json`
- **Stats**: 2798 nodes · 5671 edges · 151 communities

## 🔄 Auto-Update Workflow
1. Run `graphify update .` after every approved code change
2. Re-generate HTML and save to vault (`learning/` y `development/`)
3. Use `graphify query "..."` for deep exploration
4. Use `graphify explain "NodeName"` for node details
5. MCP server: `python -m graphify.serve graphify-out/graph.json` for multi-assistant access

## 🧪 Graphify para Learning
Graphify no es solo para análisis de código fuente — es una herramienta pedagógica cuando se usa sobre el vault mismo:
- `graphify .` sobre el vault revela las conexiones entre notas de learning
- `graphify cluster-only .` agrupa notas por tema
- `graphify explain "learning"` muestra la comunidad y complejidad del área de aprendizaje
- El grafo interactivo (HTML) visualiza cómo las 5 clases magistrales se interconectan