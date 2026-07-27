---
type: project-moc
project: CGAlpha
tags:
  - proyecto/cgalpha
  - moc
created: 2026-07-20
last_updated: 2026-07-27
---

# 🟢 CGAlpha v3 — Índice del Proyecto (MOC)

> [!info] Punto de entrada del proyecto. Todo lo de CGAlpha vive bajo `CGAlpha/`.
> Cada sesión de trabajo va en `CGAlpha/Sessions/` con tag `#proyecto/cgalpha`.

## 📌 Qué es
Sistema de trading algorítmico. BTCUSDT 5min, estrategia de triple coincidencia.

## 🔑 Datos clave (fuente de verdad)
- **Features reales del oracle**: 23 (12 extra vs 11 esperado). NO usa `l2tp_*`.
- `test_oracle_encoding.py` está en `/tests/` (root), NO en `cgalpha_v3/tests/`.
- Los tests fallan porque se añadieron features DESPUÉS de escribir los tests.
- Hay `.venv` en el proyecto — usar para pytest.

## 🗂️ Sesiones
- _(aún sin sesiones registradas aquí — las nuevas irán apareciendo abajo)_
- Ver todas: buscar `path:CGAlpha/Sessions`

## 📚 Learning (Clases Magistrales)
Secciones teóricas que construyen comprensión profunda del sistema.
- **Índice**: `learning/00-índice.md`
- **01** — El Viaje de un Dato (json, Oracle→GUI, puente HTTP)
- **02** — Arquitectura y OOP (clases, dataclass, factory methods)
- **03** — Manipulación de Datos y ML (pandas, scikit-learn, pipeline)
- **04** — Testing — El Sistema Inmunológico (pytest, fixtures, Triple Barrier)
- **05** — Síntesis Final — Los Cinco Hilos

> 📖 Lee en orden. Cada clase construye sobre la anterior.
> 🔧 Cada clase incluye sección de práctica con graphify.

## 🔧 Development (S2 — Próximos Pasos)
Área de desarrollo activo.
- **Índice**: `development/00-roadmap-s2.md`
- **Paso 1 (🔴 PENDIENTE)**: Investigar discrepancia de `max_price_since_detection` (100pts)

## 🔗 Conocimiento aplicado
- [[Books/Philosophy-Software-Design/Applied-to-CGAlpha|Ousterhout aplicado a CGAlpha]]

## ⏭️ Pendientes
- [ ] Procesar más capítulos de Ousterhout (2,3,5,9,10,20) aplicados a CGAlpha
- [ ] Reconciliar tests con las 23 features reales
- [ ] Completar Clase Magistral 6+ según avance de S2

## 📊 Graphify Analysis
- **Analysis date**: 2026-07-27
- **Graph files**: `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.json`
- **Stats** (después del último análisis): 2798 nodes · 5671 edges · 151 communities
- **Saved in vault**:
  - `learning/` — Clases Magistrales con graphify integrado como herramienta de aprendizaje
  - `development/` — Roadmap S2 con próximo paso concreto
  - `graph-analysis-latest.html` — visualización interactiva actualizada
  - `graph-report-latest.md` — resumen de comunidades actualizado

## 🔄 Auto-Update Workflow
1. Run `graphify update .` after every approved code change
2. Re-generate HTML and save to vault (`learning/` y `development/`)
3. Use `graphify query "..."` for deep exploration
4. Use `graphify explain "NodeName"` for node details
5. MCP server: `python -m graphify.serve graphify-out/graph.json` for multi-assistant access

## 🧪 Graphify para Learning
Graphify no es solo para análisis de código fuente — es una herramienta pedagógica cuando se usa sobre el vault mismo:
- `graphify .` sobre `~/Documents/Obsidian-Vault/CGAlpha/` revela las conexiones entre notas de learning
- `graphify cluster-only .` agrupa notas por tema (clases vs roadmap vs sesiones)
- `graphify explain "learning"` muestra la comunidad y complejidad del área de aprendizaje
- El grafo interactivo (HTML) visualiza cómo las 5 clases magistrales se interconectan