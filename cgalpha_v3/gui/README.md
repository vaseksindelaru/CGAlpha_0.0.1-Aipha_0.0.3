# CGAlpha v3 — Control Room GUI

**Versión:** 3.1-audit  
**Namespace:** `v3`  
**Protocolo:** HTTP/1.1 + REST + Bearer Auth  
**Puerto default:** `8080`  
**Bind default:** `127.0.0.1` (loopback only)

---

## 1. Propósito y Filosofía

La GUI Control Room es el **interface operativo nativo** de CGAlpha v3. No es un addon ni una herramienta externa — es el punto de observación, intervención y decisión desde el minuto cero.

**Principios rectores:**

1. **Observable-first:** Todo estado del sistema es visible via API
2. **Intervención explícita:** Kill-switch, rollback, y ajustes de riesgo requieren confirmación
3. **Trazabilidad automática:** Cada acción genera artefactos en `memory/iterations/`
4. **Zero-trust:** Sin token de autenticación, ningún endpoint responde

---

## 2. Quick Start

### 2.1 Requisitos

```bash
# Dependencias mínimas
Python >= 3.11
flask >= 2.3.0

# Dependencias opcionales para LLM Assistant
openai >= 1.0.0  # si OPENAI_API_KEY está configurado
```

### 2.2 Arranque del servidor

```bash
# Desde la raíz del proyecto
cd /path/to/CGAlpha_0.0.1-Aipha_0.0.3

# Variables de entorno (opcional)
export CGV3_AUTH_TOKEN="tu-token-seguro-aqui"
export CGV3_HOST="127.0.0.1"
export CGV3_PORT="8080"

# Iniciar servidor
python cgalpha_v3/gui/server.py
```

**Output esperado:**
```
[CGAlpha v3 GUI] Iniciando en http://127.0.0.1:8080
[CGAlpha v3 GUI] Auth token activo: tu-token...
[CGAlpha v3 GUI] FASE 0 — Control Room en modo mock
```

### 2.3 Verificación rápida

```bash
# Test de conectividad con curl
curl -H "Authorization: Bearer cgalpha-v3-local-dev" \
     http://127.0.0.1:8080/api/status | jq .

# Test con httpie
http :8080/api/status "Authorization: Bearer cgalpha-v3-local-dev"
```

### 2.4 Acceso via navegador

```
URL:    http://localhost:8080
Token:  cgalpha-v3-local-dev (default de desarrollo)
```

⚠️ **PRODUCCIÓN:** Cambiar `CGV3_AUTH_TOKEN` por un valor criptográficamente seguro (mínimo 32 caracteres).

---

## 3. Arquitectura del Sistema

### 3.1 Stack Tecnológico

```
┌─────────────────────────────────────────────────────────────┐
│                    BROWSER (Frontend)                        │
│  index.html │ style.css │ app.js (Vanilla JS + Fetch API)   │
└─────────────────────────────────────────────────────────────┘
                              │ HTTP/WS
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 SERVER.PY (Flask Application)                │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────────────┐  │
│  │ Auth Layer  │ │ Route Layer  │ │ Serialization Layer  │  │
│  │ @require_   │ │ @app.route() │ │ _serialize_*()       │  │
│  │ auth        │ │              │ │                      │  │
│  └─────────────┘ └──────────────┘ └──────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN LAYER (Pure)                       │
│  ┌────────────────┐ ┌────────────────┐ ┌─────────────────┐  │
│  │ Signal         │ │ Proposal       │ │ MemoryEntry     │  │
│  │ ApproachType   │ │ RiskAssessment │ │ MemoryLevel     │  │
│  └────────────────┘ └────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER (Use Cases)               │
│  ┌──────────────────┐ ┌──────────────────┐ ┌─────────────┐  │
│  │ RollbackManager  │ │ ChangeProposer   │ │ Experiment  │  │
│  │ (snapshots)      │ │ (proposals)      │ │ Runner      │  │
│  └──────────────────┘ └──────────────────┘ └─────────────┘  │
│  ┌──────────────────┐ ┌──────────────────┐ ┌─────────────┐  │
│  │ PromotionValidator│ │ ProductionGate  │ │ HealthMonitor│ │
│  └──────────────────┘ └──────────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   SUBSYSTEMS (Cross-cutting)                 │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────────────┐   │
│  │ Lila         │ │ MemoryPolicy │ │ ProjectHistory      │   │
│  │ LibraryMgr   │ │ Engine       │ │ Learner             │   │
│  └──────────────┘ └──────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo de Datos Principal

```
Usuario ──► GUI ──► API Endpoint ──► Manager/Service ──► Domain Model
                │                                         │
                │         ┌───────────────────────────────┘
                ▼         ▼
          _record_control_cycle()
                │
                ├──► _log_event() ──► _events_log[]
                ├──► _persist_iteration_artifacts() ──► memory/iterations/
                ├──► _capture_memory_librarian_event() ──► Memory Engine
                ├──► _register_incident() ──► docs/post_mortems/
                └──► _register_adr() ──► docs/adr/
```

### 3.3 Estado Global del Sistema

El servidor mantiene un estado global `_system_state` con los siguientes campos:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `phase` | `str` | Fase actual: `FASE_0`, `FASE_1`, etc. |
| `status` | `str` | `idle` \| `running` \| `degraded` \| `error` \| `kill-switch-active` |
| `kill_switch` | `str` | `armed` \| `triggered` \| `disabled` |
| `circuit_breaker` | `str` | `inactive` \| `active` |
| `drawdown_session_pct` | `float` | Drawdown actual de la sesión |
| `max_drawdown_session_pct` | `float` | Límite máximo (default: 5.0) |
| `max_position_size_pct` | `float` | Tamaño máximo de posición (default: 2.0) |
| `max_signals_per_hour` | `int` | Límite de señales por hora (default: 10) |
| `min_signal_quality_score` | `float` | Score mínimo de calidad (default: 0.65) |
| `data_quality` | `str` | `valid` \| `stale` \| `corrupted` |
| `primary_source_gap` | `bool` | Gap de fuente primaria detectado |
| `regime_shift_active` | `bool` | Cambio de régimen de mercado activo |

---

## 4. Referencia API Completa

### 4.1 Autenticación

Todos los endpoints requieren header `Authorization: Bearer <token>`.

**Respuestas de error de auth:**
```json
// 401 Unauthorized
{"error": "Unauthorized"}
```

### 4.2 Sistema y Estado

#### `GET /api/status`

Retorna snapshot completo del estado del sistema (gui_status_snapshot).

**Response 200:**
```json
{
  "panels_active": ["mission_control", "market_live", "risk_dashboard"],
  "auth_enabled": true,
  "last_event": "Control Room iniciado — FASE 0",
  "kill_switch_status": "armed",
  "system_status": "idle",
  "phase": "FASE_0",
  "data_quality": "valid",
  "circuit_breaker": "inactive",
  "drawdown_session_pct": 0.0,
  "max_drawdown_session_pct": 5.0,
  "max_position_size_pct": 2.0,
  "max_signals_per_hour": 10,
  "min_signal_quality_score": 0.65,
  "health": {
    "status": "healthy",
    "metrics": {...},
    "total_samples": 0
  },
  "regime_shift_active": false,
  "primary_source_gap": false,
  "market": {
    "symbol": "BTCUSDT",
    "interval": "5m",
    "price": null,
    "ts": null
  },
  "library": {
    "total_docs": 0,
    "primary_ratio": 0.0,
    "pending_review": 0,
    "last_ingestion": null
  },
  "theory_live": {...},
  "experiment_loop": {...},
  "learning_memory": {...},
  "incident_open_count": 0,
  "adr_count": 0,
  "server_ts": "2026-04-05T14:44:00.000000+00:00"
}
```

#### `GET /api/events`

Stream de eventos recientes del sistema.

**Query params:**
- `limit` (int, default=50, max=200): Número de eventos a retornar

**Response 200:**
```json
[
  {
    "ts": "2026-04-05T14:44:00.000000+00:00",
    "event": "Control Room iniciado — FASE 0",
    "level": "info"
  }
]
```

### 4.3 Kill-Switch (Protocolo 2-Pasos)

El kill-switch requiere confirmación explícita para evitar activaciones accidentales.

#### `POST /api/kill-switch/arm`

Paso 1: Solicitar activación del kill-switch.

**Response 200:**
```json
{
  "status": "pending_confirmation",
  "message": "Confirme en /api/kill-switch/confirm"
}
```

#### `POST /api/kill-switch/confirm`

Paso 2: Confirmar activación. Solo funciona si previamente se ejecutó `/arm`.

**Response 200:**
```json
{
  "status": "triggered",
  "ts": "2026-04-05T14:44:00.000000+00:00"
}
```

**Response 400 (sin arm previo):**
```json
{
  "error": "No hay solicitud de activación pendiente"
}
```

#### `POST /api/kill-switch/reset`

Re-armar el kill-switch después de una activación.

**Response 200:**
```json
{
  "status": "armed"
}
```

### 4.4 Rollback Manager

#### `GET /api/rollback/list`

Lista snapshots disponibles para restauración.

**Response 200:**
```json
[
  {
    "name": "2026-04-05_14-30_prop-abc123",
    "path": "/path/to/memory/snapshots/2026-04-05_14-30_prop-abc123",
    "proposal_id": "prop-abc123",
    "created_at": "2026-04-05T14:30:00+00:00",
    "git_sha": "abc123def456",
    "global_hash": "a1b2c3d4..."
  }
]
```

#### `POST /api/rollback/restore`

Restaura un snapshot con verificación de hash.

**Request body:**
```json
{
  "path": "/path/to/memory/snapshots/2026-04-05_14-30_prop-abc123"
}
```

**Response 200:**
```json
{
  "status": "success",
  "restored": {
    "config": {...},
    "model_params": {...},
    "memory_l3l4": {...},
    "git_sha": "abc123def456",
    "restored_from": "/path/to/snapshot",
    "elapsed_ms": 42.5
  }
}
```

### 4.5 Library — Lila (Biblioteca de Conocimiento)

#### `GET /api/library/status`

Snapshot del estado de la biblioteca.

**Response 200:**
```json
{
  "total_docs": 15,
  "primary_ratio": 0.4,
  "pending_review": 3,
  "last_ingestion": "2026-04-05T14:00:00+00:00",
  "counts": {
    "primary": 6,
    "secondary": 5,
    "tertiary": 4
  }
}
```

#### `GET /api/library/sources`

Búsqueda y listado de fuentes.

**Query params:**
- `query` (str): Texto de búsqueda
- `source_type` (str): `primary` \| `secondary` \| `tertiary`
- `tags` (str): Tags separados por coma
- `limit` (int, default=50, max=200)

**Response 200:**
```json
{
  "query": "volatility",
  "source_type": "primary",
  "tags": [],
  "count": 2,
  "results": [
    {
      "source_id": "src-abc123",
      "title": "Volatility Trading Strategies",
      "authors": ["Smith, J.", "Doe, A."],
      "year": 2023,
      "source_type": "primary",
      "venue": "journal_of_finance",
      "url": "https://...",
      "abstract": "...",
      "relevant_finding": "...",
      "applicability": "...",
      "tags": ["volatility", "options"],
      "ev_level": 1,
      "ingested_at": "2026-04-05T14:00:00+00:00",
      "duplicate_of": null,
      "contradicts": [],
      "executive_summary": "...",
      "tech_summary": "..."
    }
  ]
}
```

#### `GET /api/library/sources/<source_id>`

Detalle de una fuente específica.

**Response 200:** Objeto `LibrarySource` serializado.

**Response 404:**
```json
{"error": "source_not_found"}
```

#### `POST /api/library/ingest`

Ingesta una nueva fuente en la biblioteca.

**Request body:**
```json
{
  "title": "Machine Learning for Trading",
  "authors": ["Zhang, W."],
  "year": 2024,
  "source_type": "primary",
  "venue": "neurips",
  "url": "https://arxiv.org/...",
  "abstract": "...",
  "relevant_finding": "LSTM models outperform ARIMA...",
  "applicability": "Time series prediction for BTCUSDT",
  "tags": ["ml", "lstm", "trading"],
  "executive_summary": "...",
  "tech_summary": "..."
}
```

**Response 200:**
```json
{
  "is_new": true,
  "source": {...},
  "snapshot": {...}
}
```

**Response 400 (duplicado):**
```json
{
  "is_new": false,
  "source": {..., "duplicate_of": "src-xyz789"},
  "snapshot": {...}
}
```

#### `POST /api/library/claims/validate`

Valida un claim contra fuentes existentes. Detecta `primary_source_gap`.

**Request body:**
```json
{
  "claim": "LSTM models achieve 60% accuracy on BTCUSDT prediction",
  "source_ids": ["src-abc123", "src-tertiary456"],
  "auto_backlog": true,
  "requested_by": "runtime"
}
```

**Response 200 (gap detectado):**
```json
{
  "primary_source_gap": true,
  "claim_ok": false,
  "validation_message": "claim '...' apoyado solo en fuentes ['secondary', 'tertiary'] — se requiere ≥1 primaria",
  "sources_total": 2,
  "primary_count": 0,
  "missing_source_ids": [],
  "backlog_item_id": "bl-xyz789"
}
```

### 4.6 Theory Live

#### `GET /api/theory/live`

Snapshot consolidado de Theory Live (biblioteca + backlog adaptativo).

**Response 200:**
```json
{
  "library": {
    "total_docs": 15,
    "primary_ratio": 0.4,
    "pending_review": 3,
    "last_ingestion": "2026-04-05T14:00:00+00:00"
  },
  "counts": {
    "primary": 6,
    "secondary": 5,
    "tertiary": 4
  },
  "primary_source_gap_open": false,
  "recent_sources": [...],
  "backlog": {
    "open": 3,
    "in_progress": 1,
    "resolved": 5,
    "primary_source_gap_open": 2,
    "top_priority_score": 87.5,
    "top_items": [...]
  }
}
```

### 4.7 Backlog Adaptativo

#### `GET /api/lila/backlog`

Lista items del backlog adaptativo.

**Query params:**
- `status` (str): `open` \| `in_progress` \| `resolved` \| `all`
- `limit` (int, default=20, max=200)

**Response 200:**
```json
{
  "status": "open",
  "count": 3,
  "items": [
    {
      "item_id": "bl-abc123",
      "title": "Primary source gap: LSTM accuracy claims",
      "rationale": "...",
      "item_type": "primary_source_gap",
      "impact": 5,
      "risk": 4,
      "evidence_gap": 5,
      "priority_score": 87.5,
      "requested_by": "runtime",
      "claim": "...",
      "related_source_ids": ["src-xyz"],
      "recommended_source_type": "primary",
      "status": "open",
      "created_at": "2026-04-05T14:00:00+00:00",
      "updated_at": "2026-04-05T14:00:00+00:00",
      "resolution_note": ""
    }
  ]
}
```

#### `POST /api/lila/backlog`

Crea un nuevo item en el backlog.

**Request body:**
```json
{
  "title": "Research gap: Volume profile analysis",
  "rationale": "No primary sources on volume profile effectiveness in crypto markets",
  "item_type": "research_gap",
  "impact": 4,
  "risk": 3,
  "evidence_gap": 5,
  "requested_by": "user",
  "claim": "Volume profile improves entry timing",
  "related_source_ids": [],
  "recommended_source_type": "primary"
}
```

**Response 200:** Item serializado.

#### `POST /api/lila/backlog/<item_id>/resolve`

Marca un item como resuelto.

**Request body:**
```json
{
  "resolution_note": "Primary source found: Journal of Trading 2024"
}
```

### 4.8 Experiment Loop

#### `GET /api/experiment/status`

Estado del Experiment Loop.

**Response 200:**
```json
{
  "status": "idle",
  "has_proposal": false,
  "has_experiment": false,
  "proposal": null,
  "latest_experiment": null,
  "history_count": 0
}
```

#### `POST /api/experiment/propose`

Genera una propuesta de experimento con fricciones por defecto.

**Request body:**
```json
{
  "hypothesis": "RSI < 30 + volume spike > 2σ predicts reversal with 65% probability",
  "approach_types": ["TOUCH", "RETEST"],
  "source_ids": ["src-abc123"],
  "max_drawdown_impact_pct": 1.5,
  "position_sizing_impact": "none",
  "kill_switch_threshold": "drawdown_session_pct > max_drawdown_session_pct",
  "circuit_breaker_interaction": "No bypass de circuit breaker"
}
```

**Response 200:** Propuesta serializada con `proposal_id`.

#### `POST /api/experiment/run`

Ejecuta el experimento con walk-forward (≥3 ventanas) y validación de no-leakage.

**Request body (opcional):**
```json
{
  "mock_rows": 180,
  "rows": null,
  "feature_timestamps": null
}
```

**Response 200:**
```json
{
  "experiment_id": "exp-xyz789",
  "proposal_id": "prop-abc123",
  "generated_at": "2026-04-05T14:44:00+00:00",
  "friction": {
    "fee_taker_pct": 0.075,
    "fee_maker_pct": 0.025,
    "slippage_bps": 2.0,
    "latency_ms": 50
  },
  "walk_forward_windows": [...],
  "metrics": {
    "gross_return_pct": 2.5,
    "friction_cost_pct": 0.35,
    "net_return_pct": 2.15,
    "sharpe_like": 1.23,
    "max_drawdown_pct": 1.8,
    "trades": 15.0,
    "walk_forward_windows": 3.0
  },
  "window_metrics": [...],
  "approach_type_histogram": {
    "TOUCH": 5,
    "RETEST": 3,
    "REJECTION": 2,
    "BREAKOUT": 1,
    "OVERSHOOT": 0,
    "FAKE_BREAK": 0
  },
  "no_leakage_checked": true,
  "symbol": "BTCUSDT"
}
```

**Response 400 (temporal leakage):**
```json
{
  "error": "temporal_leakage",
  "message": "Feature timestamp 1712345678.9 > OOS start 1712345000.0"
}
```

### 4.9 Promotion & Production Gate

#### `POST /api/promotion/validate`

Valida un experimento para promoción a producción.

**Request body:**
```json
{
  "experiment_id": "exp-xyz789"
}
```

**Response 200:**
```json
{
  "status": "approved",
  "overall_score": 0.85,
  "checks": {
    "min_sharpe": true,
    "max_drawdown_acceptable": true,
    "no_leakage_verified": true,
    "sufficient_trades": true,
    "walk_forward_stable": true
  },
  "reasons": []
}
```

### 4.10 Learning & Memory

#### `GET /api/learning/memory/status`

Snapshot del motor de memoria.

**Response 200:**
```json
{
  "total_entries": 25,
  "levels": {
    "0a": 5,
    "0b": 8,
    "1": 6,
    "2": 4,
    "3": 1,
    "4": 1
  },
  "fields": {
    "codigo": 3,
    "math": 5,
    "trading": 10,
    "architect": 4,
    "memory_librarian": 3
  },
  "stale_entries": 2,
  "expiring_within_24h": 3,
  "last_regime_shift": null,
  "regime_events_count": 0
}
```

#### `GET /api/learning/memory/entries`

Lista entradas de memoria.

**Query params:**
- `level` (str): `0a` \| `0b` \| `1` \| `2` \| `3` \| `4`
- `field` (str): `codigo` \| `math` \| `trading` \| `architect` \| `memory_librarian`
- `limit` (int, default=50, max=200)

#### `POST /api/learning/memory/ingest`

Ingesta una nueva entrada de memoria.

**Request body:**
```json
{
  "content": "RSI < 30 combined with volume spike > 2σ shows 65% reversal rate",
  "field": "trading",
  "source_id": "src-abc123",
  "source_type": "primary",
  "tags": ["rsi", "volume", "reversal"],
  "auto_normalize": true
}
```

#### `POST /api/learning/memory/promote`

Promueve una entrada a un nivel superior.

**Request body:**
```json
{
  "entry_id": "entry-xyz",
  "target_level": "2",
  "approved_by": "Lila",
  "tags": ["validated"],
  "experiment_id": "exp-abc"
}
```

**Response 403 (Production Gate rejection):**
```json
{
  "error": "production_gate_rejected",
  "message": "Promotion to STRATEGY level requires validated experiment with sharpe > 1.5"
}
```

#### `POST /api/learning/memory/retention/run`

Ejecuta retención TTL de memoria.

#### `POST /api/learning/memory/regime/check`

Detecta cambio de régimen y degrada memoria si aplica.

**Request body:**
```json
{
  "volatility_series": [0.5, 0.6, 0.4, 0.8, 1.2, 1.5, 1.8, 2.1, ...]
}
```

### 4.11 Incidents & ADRs

#### `GET /api/incidents`

Lista incidentes registrados.

**Query params:**
- `status` (str): `open` \| `resolved`
- `limit` (int, default=50, max=200)

#### `POST /api/incidents/<incident_id>/resolve`

Marca un incidente como resuelto.

#### `GET /api/adr/recent`

Lista ADRs (Architecture Decision Records) recientes.

### 4.12 Risk Parameters

#### `GET /api/risk/params`

Lee parámetros de riesgo actuales.

**Response 200:**
```json
{
  "max_drawdown_session_pct": 5.0,
  "max_position_size_pct": 2.0,
  "max_signals_per_hour": 10,
  "min_signal_quality_score": 0.65,
  "drawdown_session_pct": 0.0,
  "circuit_breaker": "inactive"
}
```

#### `POST /api/risk/params`

Actualiza parámetros de riesgo.

**Request body:**
```json
{
  "max_drawdown_session_pct": 4.0,
  "min_signal_quality_score": 0.70
}
```

**Response 200:**
```json
{
  "updated": ["max_drawdown_session_pct", "min_signal_quality_score"],
  "current": {...},
  "all": {...}
}
```

### 4.13 LLM Assistant

#### `POST /api/assistant/chat`

Chat interactivo con Lila (asistente v3).

**Request body:**
```json
{
  "message": "¿Cuál es el estado del sistema?"
}
```

**Comandos especiales:**
- `"aprende de la historia"` / `"learn from history"` — Dispara ingesta profunda de iteraciones y ADRs

#### `POST /api/learning/ingest/history`

Ingesta conocimiento de iteraciones y ADRs pasadas.

---

## 5. Modelos de Dominio

### 5.1 ApproachType (Taxonomía de Acercamientos)

```python
class ApproachType(str, Enum):
    TOUCH      = "TOUCH"       # Precio alcanza zona sin cierre beyond
    RETEST     = "RETEST"      # Regresa tras haber cerrado fuera
    REJECTION  = "REJECTION"   # Mecha opuesta >60% del rango
    BREAKOUT   = "BREAKOUT"    # Cierre confirmado beyond zona
    OVERSHOOT  = "OVERSHOOT"   # Cierre beyond zona sin retorno en N velas
    FAKE_BREAK = "FAKE_BREAK"  # Cierre beyond zona con retorno en N velas
```

### 5.2 MemoryLevel (Jerarquía de Memoria)

| Nivel | Código | TTL | Aprobador | Descripción |
|-------|--------|-----|-----------|-------------|
| RAW | `0a` | 24h | Automático | Ingesta cruda sin validar |
| NORMALIZED | `0b` | 7d | Automático | Normalizado, sin contradicciones |
| FACTS | `1` | 30d | Lila | Hechos verificados |
| RELATIONS | `2` | 90d | Lila | Relaciones entre hechos |
| PLAYBOOKS | `3` | ∞ | Humano | Playbooks operativos |
| STRATEGY | `4` | ∞ | Humano | Estrategia de alto nivel |

### 5.3 SourceType (Clasificación de Fuentes)

| Tipo | ev_level | Requisitos |
|------|----------|------------|
| `primary` | 1 | Peer-reviewed, venue reconocido |
| `secondary` | 2 | Blogs, documentación técnica, whitepapers |
| `tertiary` | 3 | Social media, foros, opiniones |

**Venues primarios reconocidos:**
```
acl, nips, neurips, icml, jof, journal_of_finance,
journal_of_financial_economics, review_of_financial_studies,
management_science, quantitative_finance
```

---

## 6. Trazabilidad Automática

Cada acción de control ejecutada via GUI dispara `_record_control_cycle()`:

1. **Event Log:** `_events_log` (últimos 200 eventos en memoria)
2. **Iteration Artifacts:**
   - `memory/iterations/YYYY-MM-DD_HH-MM/iteration_status.json`
   - `memory/iterations/YYYY-MM-DD_HH-MM/iteration_summary.md`
3. **Memory Capture:** Entrada en `memory_librarian` field
4. **Incident Registration:** Si `level` es `warning` o `critical`:
   - `docs/post_mortems/YYYY-MM-DD_Priority_Event_IncidentID.md`
5. **ADR Registration:**
   - `docs/adr/YYYY-MM-DD_HH-MM-SS_Trigger_AdrID.md`

---

## 7. Consideraciones de Producción

### 7.1 Seguridad

```bash
# Generar token seguro (32+ caracteres)
openssl rand -hex 32

# Configurar en producción
export CGV3_AUTH_TOKEN="$(openssl rand -hex 32)"
export CGV3_HOST="0.0.0.0"  # Solo si es necesario exponer
export CGV3_PORT="8080"
```

### 7.2 Reverse Proxy (Recomendado)

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name controlroom.tudominio.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 7.3 Health Checks

```bash
# Endpoint de health (sin auth requerido para monitoring)
curl http://localhost:8080/api/status | jq '.health'
```

### 7.4 Métricas Monitoreadas por HealthMonitor

- `leakage_rate`: 0.0 (sin leakage) | 1.0 (leakage detectado)
- `exp_latency`: Latencia de ejecución de experimentos (segundos)
- `rollback_sla`: Tiempo de rollback (segundos, SLA P0: <60s)

---

## 8. Troubleshooting

### 8.1 Error: "Unauthorized"

**Causa:** Token incorrecto o faltante.

**Solución:**
```bash
# Verificar token configurado
echo $CGV3_AUTH_TOKEN

# Usar token correcto en request
curl -H "Authorization: Bearer $CGV3_AUTH_TOKEN" http://localhost:8080/api/status
```

### 8.2 Error: "temporal_leakage"

**Causa:** Feature timestamps > OOS start timestamp.

**Solución:** Verificar que los timestamps de features no incluyan datos futuros.

### 8.3 Error: "production_gate_rejected"

**Causa:** Intento de promoción a nivel STRATEGY sin experimento validado.

**Solución:** Ejecutar experimento con `sharpe_like > 1.5` y validar via `/api/promotion/validate`.

### 8.4 Error: "invalid_approach_type"

**Causa:** ApproachType no reconocido.

**Valores válidos:** `TOUCH`, `RETEST`, `REJECTION`, `BREAKOUT`, `OVERSHOOT`, `FAKE_BREAK`

### 8.5 Error: "primary_source_gap"

**Causa:** Claim sin al menos 1 fuente primaria.

**Solución:** Ingestar fuente primaria via `/api/library/ingest` o resolver backlog item.

---

## 9. Estructura de Archivos

```
cgalpha_v3/gui/
├── README.md           ← Este documento
├── __init__.py
├── server.py           ← Servidor Flask (1558 líneas)
├── server.log          ← Log de servidor
└── static/
    ├── index.html      ← Frontend HTML (1742 líneas)
    ├── style.css       ← Estilos CSS
    └── app.js          ← Lógica frontend (69KB)
```

---

## 10. Referencias

- **Prompt Maestro:** `cgalpha_v3/PROMPT_MAESTRO_v3.1-audit.md`
- **Checklist Implementación:** `cgalpha_v3/CHECKLIST_IMPLEMENTACION.md`
- **Domain Models:** `cgalpha_v3/domain/models/signal.py`
- **Experiment Runner:** `cgalpha_v3/application/experiment_runner.py`
- **Library Manager:** `cgalpha_v3/lila/library_manager.py`
- **Memory Policy:** `cgalpha_v3/learning/memory_policy.py`
- **Rollback Manager:** `cgalpha_v3/application/rollback_manager.py`

---

*Construido mientras se ve, se entiende y se decide — nunca en oculto.*
