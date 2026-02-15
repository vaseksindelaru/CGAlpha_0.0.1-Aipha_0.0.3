# Code Craft Sage - Fase 6: Automatic Proposal Generator

## Resumen Ejecutivo

La Fase 6 de Code Craft Sage implementa el **Proposal Generator**, un componente que analiza datos de rendimiento para sugerir mejoras de configuración automáticamente.

**Objetivo:** Cerrar el ciclo de "Auto-Mejora" analizando métricas y generando propuestas accionables.

**Principio Fundamental:** Este componente solo **genera propuestas**, NO las aplica automáticamente. Requiere aprobación humana para ejecutar cambios.

---

## Arquitectura del Proposal Generator

### Fuentes de Datos

| Fuente | Descripción | Ubicación |
|--------|-------------|-----------|
| **bridge.jsonl** | Historial de trades y resultados (MFE/MAE) | `aipha_memory/evolutionary/bridge.jsonl` |
| **current_state.json** | Estado actual de métricas | `aipha_memory/operational/current_state.json` |
| **Métricas Redis** | Cache hit rates, latencias | Redis (opcional) |

### Clase Principal

Ubicación: [`cgalpha/codecraft/proposal_generator.py`](../../cgalpha/codecraft/proposal_generator.py)

```python
class ProposalGenerator:
    def __init__(self, data_dir: str = "aipha_memory", min_confidence: float = 0.70):
        """
        Args:
            data_dir: Directorio de datos
            min_confidence: Confianza mínima para propuestas
        """
        
    def analyze_performance(self) -> List[Dict]:
        """
        Analiza rendimiento y genera propuestas.
        
        Returns:
            Lista de propuestas filtradas por confianza
        """
        
    def generate_proposal_id(self) -> str:
        """
        Genera ID único: AUTO_PROP_YYYYMMDD_HHMMSS
        """
```

---

## Lógica de Análisis

### Reglas Heurísticas

El sistema usa reglas if/else simples para detectar problemas:

| Problema Detectado | Umbral | Acción Propuesta |
|-------------------|--------|------------------|
| **Win Rate Bajo** | < 40% | "Aumentar confidence_threshold de 0.70 a 0.75" |
| **Drawdown Excesivo** | > 15% | "Reducir exposure_multiplier de 1.0 a 0.8" |
| **Racha de Pérdidas** | > 5 trades seguidos | "Reducir position_size de 1.0 a 0.8" |
| **Pérdidas Acumuladas** | Total < 0 | "Reducir take_profit_factor de 2.0 a 1.8" |
| **Cobertura Baja** | < 80% | "Añadir tests para módulo X" |

### Formato de Propuesta

```python
{
    "proposal_id": "AUTO_PROP_20260209_120000_abc123",
    "proposal_text": "Aumentar confidence_threshold de 0.70 a 0.75",
    "reason": "Win Rate bajo (38%) en estado actual",
    "confidence": 0.85,
    "source": "current_state",
    "severity": "high",
    "metric_value": 0.38,
    "threshold": 0.40
}
```

---

## Umbrales de Configuración

### THRESHOLDS

```python
THRESHOLDS = {
    "win_rate": {
        "target": 0.50,      # 50% objetivo
        "critical": 0.40,    # Por debajo = crítico
        "action": "Aumentar confidence_threshold de {current} a {proposed}"
    },
    "drawdown": {
        "max_acceptable": 0.15,  # 15% máximo
        "critical": 0.20,         # Por encima = crítico
        "action": "Reducir exposure_multiplier de {current} a {proposed}"
    },
    "loss_streak": {
        "max_streak": 5,
        "action": "Reducir position_size de {current} a {proposed}"
    },
    "test_coverage": {
        "minimum": 0.80,  # 80% mínimo
        "action": "Añadir tests para el módulo {module}"
    }
}
```

---

## Uso del CLI

### Comando Principal

```bash
# Analizar y mostrar propuestas
aipha codecraft auto-analyze

# Con confianza mínima específica
aipha codecraft auto-analyze --min-confidence 0.80

# En directorio específico
aipha codecraft auto-analyze --working-dir /path/to/project
```

### Salida de Ejemplo

```
🔍 CGAlpha Performance Analysis

📊 Detected Issues:
- Win Rate: 38% (Target: >50%)
- Avg Loss per Trade: -$120

💡 Generated Proposals:

1. [Confidence: 88%]
   "Aumentar confidence_threshold de 0.70 a 0.75"
   Reason: Filtrar señales de baja calidad para mejorar Win Rate.

2. [Confidence: 72%]
   "Reducir tp_factor de 2.0 a 1.8"
   Reason: Salir más rápido antes de reversión del mercado.

Run 'aipha codecraft apply --id AUTO_PROP_001' to execute.
```

---

## Integración con Code Craft Sage

### Flujo de Trabajo

```
┌─────────────────────────────────────────────────────────────┐
│                    ProposalGenerator                         │
│  1. Lee bridge.jsonl y current_state.json                  │
│  2. Analiza métricas con reglas heurísticas                  │
│  3. Genera propuestas con confianza                        │
│  4. Filtra por confianza mínima (>70%)                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
              ┌──────────────────────┐
              │   Aprobación Humana   │
              └──────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                   CodeCraftOrchestrator                      │
│  1. execute_pipeline(proposal_text, proposal_id)           │
│  2. Si éxito: Loggear "Mejora Automática Aplicada"        │
│  3. Si fallo: Loggear "Mejora Rechazada por Tests"       │
└─────────────────────────────────────────────────────────────┘
```

### Modo Dry-Run

Por defecto, el sistema solo **genera propuestas** sin aplicarlas:

```python
#伪 El ProposalGenerator NUNCA llama a execute_pipeline

# El usuario decide:
# 1. Revisar propuesta
# 2. Ejecutar manualmente:
aipha codecraft apply --text "Aumentar confidence_threshold..." --id AUTO_PROP_XXX
```

---

## Políticas de Seguridad

### Frecuencia de Análisis

| Intervalo | Límite | Razón |
|-----------|--------|-------|
| **Automático** | Cada 24 horas | Evitar cambios frecuentes |
| **Manual** | Sin límite | Usuario controla |
| **Por Trade** | Máximo 1/100 trades | Evitar spam |

### Límites

```python
# Configuración de seguridad
SECURITY_CONFIG = {
    "max_proposals_per_day": 1,      # Máximo 1 propuesta automática por día
    "min_confidence_threshold": 0.70, # Confianza mínima
    "require_approval": True,          # Siempre requiere aprobación humana
    "tag_auto_proposals": True         # Marcar con tag [AUTO]
}
```

### Tag [AUTO] en Commits

Las propuestas automáticas se marcan en los mensajes de commit:

```
[AUTO] feat: Update confidence_threshold to 0.75 (CodeCraft Sage)

Proposal ID: AUTO_PROP_20260209_120000
Confidence: 85%
Reason: Win Rate bajo (38%) en último periodo
```

---

## API del ProposalGenerator

### Métodos Principales

```python
class ProposalGenerator:
    def analyze_performance(self) -> List[Dict]:
        """
        Analiza rendimiento y genera propuestas.
        
        Returns:
            Lista de propuestas ordenadas por confianza
        """
        
    def generate_proposal_id(self) -> str:
        """
        Genera ID único para propuesta.
        
        Returns:
            ID en formato: AUTO_PROP_YYYYMMDD_HHMMSS
        """
        
    def _analyze_current_state(self, state: Dict) -> List[Dict]:
        """Analiza métricas del estado actual."""
        
    def _analyze_trade_history(self, trades: List[Dict]) -> List[Dict]:
        """Analiza historial de trades."""
```

### Función de Conveniencia

```python
from cgalpha.codecraft.proposal_generator import analyze_and_report

proposals = analyze_and_report(data_dir="aipha_memory")

for prop in proposals:
    print(f"{prop['confidence']:.0%}: {prop['proposal_text']}")
```

---

## Ejemplo de Uso Programático

```python
from cgalpha.codecraft.proposal_generator import ProposalGenerator

# Crear generator
generator = ProposalGenerator(
    data_dir="aipha_memory",
    min_confidence=0.70
)

# Analizar
proposals = generator.analyze_performance()

# Mostrar propuestas
for prop in proposals:
    print(f"\n[{prop['confidence']:.0%}] {prop['severity'].upper()}")
    print(f"  {prop['proposal_text']}")
    print(f"  Reason: {prop['reason']}")
    print(f"  ID: {prop['proposal_id']}")
```

---

## Métricas Analizadas

### current_state.json

```json
{
    "win_rate": 0.38,
    "max_drawdown": 0.12,
    "total_trades": 156,
    "test_coverage": 0.75,
    "timestamp": "2026-02-09T12:00:00Z"
}
```

### bridge.jsonl (Trade History)

```json
{"trade_id": "TRADE_0001", "profit": 100, "result": "WIN"}
{"trade_id": "TRADE_0002", "profit": -80, "result": "LOSS"}
{"trade_id": "TRADE_0003", "profit": 120, "result": "WIN"}
...
```

---

## Configuración

### Parámetros de Inicialización

```python
generator = ProposalGenerator(
    data_dir="aipha_memory",      # Directorio de datos
    min_confidence=0.70           # Confianza mínima (0.0 - 1.0)
)
```

### Umbrales Personalizables

Los umbrales pueden modificarse editando `THRESHOLDS` en el código:

```python
THRESHOLDS["win_rate"]["critical"] = 0.35  # Más estricto
THRESHOLDS["drawdown"]["max_acceptable"] = 0.10  # Más conservador
```

---

## Solución de Problemas

### Error: "No data files found"

```bash
# Verificar que existen los archivos
ls -la aipha_memory/evolutionary/bridge.jsonl
ls -la aipha_memory/operational/current_state.json

# Si no existen, el sistema usará datos dummy para testing
```

### Error: "No proposals generated"

```bash
# Verificar que las métricas están por debajo de los umbrales
# Si todas las métricas están bien, no se generarán propuestas

# Forzar generación de propuestas con confianza baja
aipha codecraft auto-analyze --min-confidence 0.50
```

---

## Fases Futuras

### Fully Autonomous Mode (Fase 7)

Esta fase (pendiente) permitirá aplicación automática:

```
Pendiente de implementar:
- Aprobación automática si confidence > 95%
- Learning de qué propuestas funcionan
- Ajuste automático de umbrales
```

---

## Referencias

- **ProposalGenerator:** [`cgalpha/codecraft/proposal_generator.py`](../../cgalpha/codecraft/proposal_generator.py)
- **CLI Command:** [`aiphalab/commands/codecraft.py`](../../aiphalab/commands/codecraft.py)
- **Fase 1-5:** Ver documentación en [`bible/codecraft_sage/`](.)

---

## Changelog

### v0.0.1 (2026-02-09)
- Implementación inicial del ProposalGenerator
- Reglas heurísticas para detectar problemas
- Integración con CLI
- Datos dummy para testing
- Políticas de seguridad
- Solo genera propuestas, NO aplica automáticamente
