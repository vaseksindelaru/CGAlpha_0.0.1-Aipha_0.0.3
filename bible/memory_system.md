# 🧠 Sistema de Memoria CGAlpha

## Estructura de Directorios

```
aipha_memory/
├── operational/               # 📈 Datos para Aipha (Capa 1 - Fast Loop)
│   ├── current_state.json     # Estado actual
│   └── action_history.jsonl   # Historial de acciones
│
├── evolutionary/              # 🧠 Datos para CGAlpha (Capa 5 - Slow Loop)
│   ├── bridge.jsonl           # Puente evolutivo
│   ├── analysis_cache/        # Cache de análisis
│   └── proposals_history/     # Historial de propuestas
│
├── testing/                   # 🧪 Datos de prueba (NO producción)
│   ├── stress_test.jsonl      # Eventos simulados
│   └── synthetic_trades/      # Trades sintéticos
│
└── config/                    # ⚙️ Configuración
    ├── memory_config.yaml     # Políticas
    └── backup_schedule.json   # Calendario de backups
```

## Políticas de Retención

```yaml
# memory_config.yaml - Políticas de retención y gestión de memoria
retention_policies:
  operational:
    max_age_days: 7
    max_size_mb: 100
    purge_schedule: "daily"
    backup_enabled: true
  
  evolutionary:
    max_age_days: 90
    max_size_mb: 1000
    purge_schedule: "weekly"
    backup_enabled: true
    compression: true
  
  testing:
    max_age_days: 30
    max_size_mb: 5000
    purge_schedule: "monthly"
    backup_enabled: false

access_patterns:
  aipha_access: ["operational/"]
  cgalpha_access: ["evolutionary/", "operational/current_state.json"]
  test_access: ["testing/"]

backup_settings:
  operational_backup: "daily at 02:00"
  evolutionary_backup: "weekly on Sunday at 03:00"
  backup_location: "../aipha_memory_backups/"
```

## Ejemplos de Uso

```python
# Para Aipha (operacional):
from core.context_sentinel import ContextSentinel
sentinel = ContextSentinel()
sentinel.add_memory("trade_completed", {"symbol": "BTCUSDT", "profit": 1.2})

# Para CGAlpha (evolutivo):
from core.trading_engine import TradingEngine
engine = TradingEngine()
# Automatizado internamente al detectar señales
# engine._save_to_bridge(signals, sensor_results)
```
