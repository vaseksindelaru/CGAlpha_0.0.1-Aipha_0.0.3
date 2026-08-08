# CGAlpha v3 GUI — Quick Reference

**Token default:** `cgalpha-v3-local-dev`  
**Host:** `127.0.0.1:8080`

---

## 1. Arranque

```bash
# Variables de entorno
export CGV3_AUTH_TOKEN="cgalpha-v3-local-dev"
export CGV3_HOST="127.0.0.1"
export CGV3_PORT="8080"

# Iniciar servidor
python cgalpha_v3/gui/server.py
```

---

## 2. Verificación

```bash
# curl
curl -H "Authorization: Bearer cgalpha-v3-local-dev" \
     http://127.0.0.1:8080/api/status | jq .

# httpie
http :8080/api/status "Authorization: Bearer cgalpha-v3-local-dev"
```

---

## 3. Endpoints Críticos

### Estado del Sistema
```bash
GET /api/status
```

### Kill-Switch (2-pasos)
```bash
# Paso 1: Armar
POST /api/kill-switch/arm

# Paso 2: Confirmar
POST /api/kill-switch/confirm

# Re-armar
POST /api/kill-switch/reset
```

### Rollback
```bash
# Listar snapshots
GET /api/rollback/list

# Restaurar
POST /api/rollback/restore
# Body: {"path": "/path/to/snapshot"}
```

### Library (Lila)
```bash
# Estado
GET /api/library/status

# Buscar fuentes
GET /api/library/sources?query=volatility&source_type=primary

# Ingestar fuente
POST /api/library/ingest
# Body: {"title": "...", "source_type": "primary", "venue": "neurips", ...}

# Validar claim
POST /api/library/claims/validate
# Body: {"claim": "...", "source_ids": ["src-abc"], "auto_backlog": true}
```

### Experiment Loop
```bash
# Estado
GET /api/experiment/status

# Crear propuesta
POST /api/experiment/propose
# Body: {"hypothesis": "...", "approach_types": ["TOUCH"], ...}

# Ejecutar
POST /api/experiment/run
# Body: {"mock_rows": 180}  # opcional
```

### Memory
```bash
# Estado
GET /api/learning/memory/status

# Ingestar
POST /api/learning/memory/ingest
# Body: {"content": "...", "field": "trading", "source_id": "src-abc"}

# Promover
POST /api/learning/memory/promote
# Body: {"entry_id": "entry-xyz", "target_level": "2", "approved_by": "Lila"}
```

### Risk Parameters
```bash
# Leer
GET /api/risk/params

# Actualizar
POST /api/risk/params
# Body: {"max_drawdown_session_pct": 4.0}
```

---

## 4. Modelos Clave

### ApproachType
```
TOUCH | RETEST | REJECTION | BREAKOUT | OVERSHOOT | FAKE_BREAK
```

### MemoryLevel
```
0a (RAW, 24h) → 0b (NORMALIZED, 7d) → 1 (FACTS, 30d) →
2 (RELATIONS, 90d) → 3 (PLAYBOOKS, ∞) → 4 (STRATEGY, ∞)
```

### SourceType
```
primary (ev_level=1) | secondary (ev_level=2) | tertiary (ev_level=3)
```

---

## 5. Errores Comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `Unauthorized` | Token faltante/incorrecto | `Authorization: Bearer <token>` |
| `temporal_leakage` | Feature ts > OOS start | Verificar timestamps |
| `production_gate_rejected` | Promoción sin validación | Ejecutar experimento con sharpe > 1.5 |
| `primary_source_gap` | Claim sin fuente primaria | Ingestar fuente primary |
| `invalid_approach_type` | ApproachType no válido | Usar valores de la taxonomía |

---

## 6. Producción

```bash
# Token seguro (32+ chars)
export CGV3_AUTH_TOKEN="$(openssl rand -hex 32)"

# Exponer con reverse proxy (nginx + SSL)
# Ver README.md sección 7.2
```

---

## 7. Archivos Referencia

```
cgalpha_v3/gui/
├── README.md      ← Documentación completa
├── server.py      ← Servidor Flask
└── static/        ← Frontend
    ├── index.html
    ├── style.css
    └── app.js
```

---

*Ver documentación completa en `README.md`.*
