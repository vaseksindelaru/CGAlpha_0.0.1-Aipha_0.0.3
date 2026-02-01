# 🎛️ GUÍA COMPLETA: CLI COMO PANEL DE CONTROL DE AIPHA

> **Tu llave para entender, evaluar e implementar mejoras en un sistema autónomo**

---

## 📚 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Nivel 1: Conceptos Fundamentales](#nivel-1-conceptos-fundamentales)
3. [Nivel 2: Primeros Pasos](#nivel-2-primeros-pasos)
4. [Nivel 3: Explorando las Capas](#nivel-3-explorando-las-capas)
5. [Nivel 4: Simulación Segura (Dry-Run)](#nivel-4-simulación-segura-dry-run)
6. [Nivel 5: Implementación de Cambios](#nivel-5-implementación-de-cambios)
7. [Nivel 6: Monitoreo en Tiempo Real](#nivel-6-monitoreo-en-tiempo-real)
8. [Casos de Uso Prácticos](#casos-de-uso-prácticos)
9. [Troubleshooting](#troubleshooting)
10. [Roadmap Futuro](#roadmap-futuro)

---

## Introducción: Tu Viaje Hacia la Comprensión Total

Esta guía te llevará de la mano a través de **6 niveles de profundidad** en la comprensión de Aipha, usando el CLI como tu herramienta principal.

### Objetivo Final
Al completar esta guía, podrás:
- ✅ Comprender cómo funciona cada capa de Aipha
- ✅ Simular cambios sin riesgos (dry-run)
- ✅ Evaluar propuestas de mejora antes de implementarlas
- ✅ Implementar mejoras directamente desde el CLI
- ✅ Monitorear el progreso en tiempo real
- ✅ Crear mejoras personalizadas basadas en tus ideas

---

## NIVEL 1: Conceptos Fundamentales

### ¿Qué es Aipha?

Aipha es un **sistema autónomo de auto-mejora** basado en un bucle cerrado infinito:

```
1. OBSERVA (Recolecta métricas de trading)
   ↓
2. ANALIZA (Propone cambios basados en heurísticas/LLM)
   ↓
3. EVALÚA (Califica la propuesta: ¿Es segura? ¿Tiene sentido?)
   ↓
4. EJECUTA (Aplica el cambio de forma atómica con 5 pasos)
   ↓
5. APRENDE (Registra resultado en memoria persistente)
   ↓
[VUELVE AL PASO 1]
```

### Las 5 Capas de Aipha

```
┌─────────────────────────────────────────────────────┐
│ Capa 5: Post-Procesador de Datos                    │
│ ↳ Analiza trades después de completarse             │
├─────────────────────────────────────────────────────┤
│ Capa 4: Oracle (Machine Learning)                   │
│ ↳ Filtra señales falsas con Random Forest           │
├─────────────────────────────────────────────────────┤
│ Capa 3: Trading Manager                             │
│ ↳ Detecta y ejecuta señales de compra/venta         │
├─────────────────────────────────────────────────────┤
│ Capa 2: Data Processor                              │
│ ↳ Descarga datos de Binance y almacena en DuckDB    │
├─────────────────────────────────────────────────────┤
│ Capa 1: CORE (Autonomous Intelligence) ←────────────┤
│ ↳ Memoria + Orquestación de todo el sistema         │
└─────────────────────────────────────────────────────┘
```

**Cada capa tiene parámetros que pueden mejorarse automáticamente.**

### Los 3 Componentes Clave de la Capa 1

| Componente | Función | Responsabilidad |
|-----------|---------|-----------------|
| **ContextSentinel** | Memoria | Guarda todas las decisiones y métricas |
| **ChangeProposer** | Generador | Sugiere qué cambios hacer |
| **ChangeEvaluator** | Evaluador | Califica si el cambio es bueno (0-1) |

---

## NIVEL 2: Primeros Pasos

### Tu Primera Exploración (5 minutos)

```bash
# Comando 1: Ver estado actual
aipha status

# Esperado:
# ┌─ 📊 ESTADO DEL SISTEMA ─────────────────────┐
# │ Estado General: IDLE                        │
# │ Último ciclo: 2025-12-29 14:32:15          │
# │ Total trades: 0                             │
# │ Win Rate: N/A                               │
# │ Drawdown: 0.00%                             │
# │ Cambios implementados: 0                    │
# └─────────────────────────────────────────────┘
```

```bash
# Comando 2: Ver configuración actual
aipha config view

# Esperado:
# ┌─ ⚙️  CONFIGURACIÓN ──────────────────────────┐
# │ Trading:                                    │
# │   atr_period: 14                           │
# │   tp_factor: 2.0                           │
# │   sl_factor: 1.0                           │
# │ Oracle:                                     │
# │   n_estimators: 100                        │
# │   max_depth: 10                            │
# │ Postprocessor:                              │
# │   adjustment_threshold: 0.05               │
# └─────────────────────────────────────────────┘
```

```bash
# Comando 3: Validar configuración
aipha config validate

# Esperado:
# ┌─ ✅ VALIDACIÓN ─────────────────────────────┐
# │ ✅ Trading.atr_period: 14 ∈ [5, 50]        │
# │ ✅ Trading.tp_factor: 2.0 ∈ [0.5, 5.0]     │
# │ ✅ Trading.sl_factor: 1.0 ∈ [0.1, 3.0]     │
# │ ✅ TODAS LAS VALIDACIONES PASARON           │
# └─────────────────────────────────────────────┘
```

### ¿Qué Significa?

- **Status IDLE**: El sistema no está ejecutando ciclos ahora
- **Config View**: Muestra todos los parámetros con sus valores actuales
- **Validate**: Verifica que todo esté dentro de rangos permitidos

---

## NIVEL 3: Explorando las Capas

### Entender Capa 3: Trading Manager

**¿Qué es?** El cerebro técnico que detecta patrones de entrada/salida.

```bash
# Ver información sobre esta capa
aipha layer trading --info

# Output:
# 📊 CAPA 3: Trading Manager
# Función: Detecta y ejecuta señales de trading
#
# Parámetros clave:
#   atr_period (5-50): Período del promedio verdadero
#     ↳ MÁS BAJO (5-10): Sistema MÁS sensible (más trades)
#     ↳ MÁS ALTO (20-50): Sistema MENOS sensible (menos trades)
#
#   tp_factor (0.5-5.0): Multiplica ATR para TP
#     ↳ MÁS BAJO (0.5-1.0): Ganancias pequeñas pero frecuentes
#     ↳ MÁS ALTO (3.0-5.0): Ganancias grandes pero raras
#
#   sl_factor (0.1-3.0): Multiplica ATR para SL
#     ↳ MÁS BAJO (0.1-0.5): Tolerancia muy baja (stop rápido)
#     ↳ MÁS ALTO (1.0-3.0): Tolerancia más alta (esperar reversal)
```

**Ejemplo práctico de cómo funcionan juntos:**

```
Escenario: Mercado con ATR = 100 puntos de volatilidad

CONFIGURACIÓN ACTUAL:
  atr_period = 14
  tp_factor = 2.0
  sl_factor = 1.0

CÁLCULO DE TRADE:
  TP = 100 × 2.0 = +200 puntos (ganancia objetivo)
  SL = 100 × 1.0 = -100 puntos (pérdida máxima)
  Risk/Reward = 200/100 = 2:1 (muy bueno)

SIGNIFICA:
  Por cada trade, arriesgamos 100 puntos
  para ganar 200 puntos
  = 2x retorno por trade
```

### Entender Capa 4: Oracle (Machine Learning)

**¿Qué es?** Un modelo que aprende a filtrar las señales que son falsas.

```bash
# Ver información sobre esta capa
aipha layer oracle --info

# Output:
# 🧠 CAPA 4: Oracle (Machine Learning)
# Función: Filtra señales falsas con Random Forest
#
# Parámetros clave:
#   n_estimators (10-1000): Cantidad de árboles de decisión
#     ↳ 10-50: Rápido pero menos preciso
#     ↳ 100-200: Balance óptimo (ACTUAL: 100)
#     ↳ 500-1000: Muy preciso pero lento
#
#   max_depth (2-50): Profundidad máxima de cada árbol
#     ↳ 2-5: Simple, rápido, riesgo de underfitting
#     ↳ 10: Balance óptimo (ACTUAL: 10)
#     ↳ 20-50: Complejo, riesgo de overfitting
#
#   confidence_threshold (0.5-0.99): Solo uses señales > este valor
#     ↳ 0.5: 50% confianza = MÁS trades, MENOS precisos
#     ↳ 0.7: 70% confianza = Balance (ACTUAL)
#     ↳ 0.95: 95% confianza = POCOS trades, MUY precisos
```

**¿Cómo se relaciona con Trading Manager?**

```
Trading Manager dice: "¡Señal de compra!"
          ↓
    Oracle evalúa la señal
          ↓
¿Oracle confianza > 0.7?
   SÍ → Ejecutar trade
   NO → Ignorar señal (falsa alarma evitada)
```

### Entender Capa 5: Post-Procesador

**¿Qué es?** Analiza cada trade completado y aprende de él.

```bash
# Ver información sobre esta capa
aipha layer postprocessor --info

# Output:
# 📈 CAPA 5: Post-Procesador
# Función: Análisis post-trade y ajustes automáticos
#
# Parámetros clave:
#   adjustment_threshold (0.01-0.2): Umbral de ajuste automático
#     ↳ 0.01: Ajusta después de -1% de cambio
#     ↳ 0.05: Ajusta después de -5% de cambio (ACTUAL)
#     ↳ 0.2: Ajusta después de -20% de cambio
```

---

## NIVEL 4: Simulación Segura (Dry-Run)

### ¿Qué es Dry-Run?

**Dry-Run** = "Ensayo sin consecuencias"

Ejecuta TODO exactamente como si fuera real, PERO sin:
- Modificar archivos
- Cambiar configuración
- Afectar el sistema

Es como practicar en un simulador antes de pilotar un avión real.

### Tu Primera Simulación (10 minutos)

```bash
# Paso 1: Ejecutar UN ciclo de automejora SIN cambiar nada
aipha --dry-run cycle run

# Output esperado:
# [DRY-RUN MODE] Cambios simulados sin persistencia
#
# ┌─ FASE 1: RECOLECCIÓN ─────────────────────┐
# │ ✅ Métricas recolectadas:                  │
# │   Win Rate: 0.45 (45%)                    │
# │   Total Trades: 12                        │
# │   Drawdown: -8.5%                         │
# │   Sharpe Ratio: 0.8                       │
# └───────────────────────────────────────────┘
#
# ┌─ FASE 2: ANÁLISIS Y PROPUESTA ────────────┐
# │ 💡 Propuesta generada:                    │
# │   Cambio: tp_factor 2.0 → 2.5             │
# │   Razón: Win Rate bajo, aumentar ganancia │
# │   Riesgo: MEDIO                           │
# └───────────────────────────────────────────┘
#
# ┌─ FASE 3: EVALUACIÓN ──────────────────────┐
# │ 📊 Scoring detallado:                     │
# │   Impacto: 8/10 (30% del score)           │
# │   Dificultad: 9/10 (20% del score)        │
# │   Riesgo: 7/10 (30% del score)            │
# │   Complejidad: 9/10 (20% del score)       │
# │   ───────────────────────────────         │
# │   SCORE FINAL: 0.78 ✅ (>= 0.70 APROBADO)│
# └───────────────────────────────────────────┘
#
# ┌─ FASE 4: EJECUCIÓN (SIMULADA) ────────────┐
# │ 🔄 Protocolo Atómico (SIMULADO):          │
# │   1. [BACKUP] ✅ Copia creada             │
# │   2. [DIFF] ✅ Cambio aplicado            │
# │   3. [TEST] ✅ Tests pasados              │
# │   4. [COMMIT] ✅ Cambio válido            │
# │   5. [ROLLBACK] N/A (no fallo)            │
# └───────────────────────────────────────────┘
#
# ┌─ RESULTADO FINAL ─────────────────────────┐
# │ Modo: [DRY-RUN] - SIN CAMBIOS REALES      │
# │ Estado de propuesta: SIMULADO EXITOSAMENTE│
# │ Cambios persistidos: 0                    │
# │ Status: ✅ LISTO PARA PRODUCCIÓN          │
# └───────────────────────────────────────────┘
```

### ¿Qué significa el output?

**FASE 1** muestra por qué el sistema piensa que debe hacer cambios
**FASE 2** muestra exactamente qué cambio propone
**FASE 3** muestra cómo califica ese cambio (score 0.78 = BUENO)
**FASE 4** muestra exactamente qué sucedería si lo aplicáramos
**RESULTADO** confirma que fue simulado y no cambió nada real

### Hacer Múltiples Simulaciones

```bash
# Ver qué pasaría en 5 ciclos consecutivos
aipha --dry-run cycle run --count 5

# Esto te mostrará una progresión simulada:
# Ciclo 1: tp_factor 2.0 → 2.5 (score 0.78)
# Ciclo 2: atr_period 14 → 12 (score 0.72)
# Ciclo 3: sl_factor 1.0 → 0.9 (score 0.75)
# Ciclo 4: n_estimators 100 → 150 (score 0.82)
# Ciclo 5: atr_period 12 → 10 (score 0.68)
```

---

## NIVEL 5: Implementación de Cambios

### Tu Primera Propuesta Personalizada

En lugar de dejar que Aipha sugiera cambios, **TÚ** sugieres uno:

```bash
# Paso 1: Crear una propuesta personalizada
aipha proposal create \
  --type parameter \
  --component trading_manager \
  --parameter atr_period \
  --new-value 12 \
  --reason "Aumentar sensibilidad para capturar más movimientos"

# Output esperado:
# ┌─ ✅ PROPUESTA CREADA ─────────────────────┐
# │ ID: PROP_20251229_A4X                     │
# │ Tipo: PARÁMETRO                           │
# │ Componente: trading_manager               │
# │ Cambio: atr_period: 14 → 12               │
# │ Razón: Aumentar sensibilidad...           │
# │ Estado: PENDIENTE EVALUACIÓN             │
# │                                           │
# │ [Evaluar] [Simular] [Aplicar] [Rechazar] │
# └───────────────────────────────────────────┘
```

### Paso 2: Evaluar tu Propuesta

```bash
# Dejar que el sistema calque tu idea
aipha proposal evaluate PROP_20251229_A4X

# Output:
# ┌─ 📊 EVALUACIÓN DE PROPUESTA ──────────────┐
# │ ID: PROP_20251229_A4X                     │
# │ Impacto: 7/10                             │
# │ Dificultad: 10/10                         │
# │ Riesgo: 6/10                              │
# │ Complejidad: 8/10                         │
# │ ─────────────────────────────────────     │
# │ SCORE FINAL: 0.73 ✅ APROBADO            │
# │                                           │
# │ Análisis detallado:                       │
# │ • Impacto: Cambio atr_period 14→12        │
# │   afectará directamente sensibilidad      │
# │ • Riesgo: Puede generar más falsos        │
# │   positivos en mercados laterales         │
# │ • Complejidad: Bajo - cambio simple       │
# │ • Probabilidad éxito: 68%                 │
# └───────────────────────────────────────────┘
```

### Paso 3: Simular tu Propuesta

```bash
# Antes de aplicar: ¿Qué sucedería?
aipha --dry-run proposal apply PROP_20251229_A4X

# Output: Exactamente lo mismo que un dry-run cycle
# Pero enfocado SOLO en este cambio específico
```

### Paso 4: Aplicar tu Propuesta

Cuando estés seguro (score > 0.70):

```bash
# ¡Aplicar el cambio para REAL!
aipha proposal apply PROP_20251229_A4X

# Output:
# ┌─ ⚡ APLICANDO CAMBIO ─────────────────────┐
# │ ID: PROP_20251229_A4X                     │
# │                                           │
# │ Protocolo Atómico de 5 Pasos:             │
# │ 1. [BACKUP] ✅ Copia de seguridad creada  │
# │    Archivo: trading_manager/config.json   │
# │    Ubicación: memory/backups/...          │
# │                                           │
# │ 2. [DIFF] ✅ Cambio aplicado              │
# │    Línea 42: "atr_period": 12             │
# │                                           │
# │ 3. [TEST] ✅ Tests ejecutados             │
# │    pytest trading_manager/ -v             │
# │    Resultado: 27 tests PASADOS            │
# │                                           │
# │ 4. [COMMIT] ✅ Backup eliminado           │
# │    Cambio es definitivo                   │
# │                                           │
# │ 5. [ROLLBACK] N/A                         │
# │    No hubo errores                        │
# │                                           │
# │ ✅ CAMBIO APLICADO EXITOSAMENTE          │
# │ Timestamp: 2025-12-29 14:45:33            │
# │ Status: ACTIVO                            │
# └───────────────────────────────────────────┘
```

### ¿Qué sucede si algo falla?

```bash
# Si el TEST falla (paso 3), el sistema:
# 1. DETIENE la aplicación
# 2. Restaura AUTOMÁTICAMENTE desde backup
# 3. Te muestra qué test falló
# 4. El sistema sigue IDÉNTICO a antes

# Resultado: CERO riesgo de romper Aipha
```

---

## NIVEL 6: Monitoreo en Tiempo Real

### Ver el Dashboard Interactivo

```bash
# Ver estado en vivo (se actualiza cada 2 segundos)
aipha dashboard --interval 2

# Output (se actualiza en vivo):
# ┌────────────────────────────────────────────────────────┐
# │ AIPHA DASHBOARD - Tiempo Real [14:47:15]              │
# ├──────────────────────┬────────────────────────────────┤
# │ ESTADO DEL SISTEMA   │ ÚLTIMA PROPUESTA              │
# │                      │                                │
# │ Estado: EJECUTANDO   │ ID: PROP_20251229_A4X          │
# │ Ciclos ejecutados: 5 │ Tipo: PARÁMETRO               │
# │ Win Rate: 0.52       │ Cambio: atr_period 14→12      │
# │ Drawdown: -5.2%      │ Score: 0.73 ✅               │
# │ Trades ejecutados: 23│ Status: APLICADO              │
# │                      │ Aplicado en: 14:45:33         │
# ├──────────────────────┼────────────────────────────────┤
# │ CAMBIOS RECIENTES    │ MÉTRICAS AHORA vs ANTES       │
# │ ═══════════════════  │ ══════════════════════════════│
# │                      │                                │
# │ ✅ APLICADO:         │ Win Rate:  0.45 → 0.52 ⬆️    │
# │   atr_period 14→12   │ Trades:    12 → 23 ⬆️         │
# │   Score: 0.73        │ Drawdown:  -8.5% → -5.2% ⬆️  │
# │   Impacto: +15% WIN  │ Sharpe: 0.8 → 1.1 ⬆️          │
# │                      │                                │
# │ ✅ REVERTIDO:        │ Cambio neto: +7% Performance  │
# │   tp_factor 2.5→2.0  │                                │
# │   Score: 0.68        │                                │
# │   Razón: No ayudó    │                                │
# └──────────────────────┴────────────────────────────────┘
```

### Ver Historial de Cambios

```bash
# Ver todos los cambios realizados (últimos 20)
aipha history --limit 20

# Output:
# ┌─ HISTORIAL DE CAMBIOS ────────────────────┐
# │ #  │ Fecha/Hora  │ Cambio             │ Score │
# ├────┼─────────────┼────────────────────┼───────┤
# │ 5  │ 14:45:33    │ atr_period 14→12   │ 0.73  │ ✅
# │ 4  │ 14:32:15    │ tp_factor 2.5→2.0  │ 0.68  │ ✅
# │ 3  │ 14:28:43    │ sl_factor 1.0→0.9  │ 0.75  │ ✅
# │ 2  │ 14:25:10    │ n_estimators→150   │ 0.82  │ ✅
# │ 1  │ 14:21:30    │ atr_period 10→14   │ 0.79  │ ✅
# └───────────────────────────────────────────────┘
```

---

## Casos de Uso Prácticos

### Caso 1: Win Rate Muy Bajo (< 40%)

**Síntomas:**
```bash
aipha status
# Output muestra: Win Rate: 0.35
```

**Investigación:**
```bash
# 1. Analizar calidad de trades
aipha analysis trading-quality

# 2. Ver sugerencia automática para el parámetro
aipha config suggest Trading.tp_factor

# Output:
# ┌─ SUGERENCIA PARA Trading.tp_factor ───────┐
# │ Valor actual: 2.0                         │
# │ Rango permitido: 0.5-5.0                  │
# │                                           │
# │ PROBLEMA DETECTADO:                       │
# │ tp_factor bajo en mercado de tendencia    │
# │ Muchas ganancias pequeñas vs pérdidas     │
# │                                           │
# │ RECOMENDACIÓN:                            │
# │ Aumentar tp_factor a 2.5                  │
# │ Permitirá capturar movimientos mayores    │
# │ Probabilidad éxito: 0.68                  │
# └───────────────────────────────────────────┘

# 3. Crear propuesta basada en sugerencia
aipha proposal create \
  --type parameter \
  --component trading_manager \
  --parameter tp_factor \
  --new-value 2.5 \
  --reason "Aumentar objetivo de ganancia en mercado de tendencia"

# 4. Evaluar la propuesta
aipha proposal evaluate PROP_20251229_B2Z

# 5. Simular antes de aplicar
aipha --dry-run proposal apply PROP_20251229_B2Z

# 6. Si score > 0.70, aplicar
aipha proposal apply PROP_20251229_B2Z

# 7. Monitorear impacto
aipha monitor --proposal PROP_20251229_B2Z --interval 5
```

### Caso 2: Demasiados Trades (Sobretrading)

**Síntomas:**
```bash
aipha status
# Output muestra: Total Trades: 50 en 1 hora (muy alto)
```

**Solución:**
```bash
# 1. Aumentar atr_period (menos sensible)
aipha proposal create \
  --type parameter \
  --component trading_manager \
  --parameter atr_period \
  --new-value 20 \
  --reason "Reducir frecuencia de trading"

# 2. Aumentar confidence_threshold (filtro más estricto)
aipha proposal create \
  --type parameter \
  --component oracle \
  --parameter confidence_threshold \
  --new-value 0.80 \
  --reason "Solo trades con alta confianza"

# 3. Evaluar ambas
aipha proposal evaluate PROP_20251229_C5K
aipha proposal evaluate PROP_20251229_C5L

# 4. Aplicar si scores son buenos
aipha proposal apply PROP_20251229_C5K
aipha proposal apply PROP_20251229_C5L
```

### Caso 3: Drawdown Muy Alto (> 15%)

**Síntomas:**
```bash
aipha status
# Output muestra: Drawdown: -18%
```

**Solución:**
```bash
# 1. Análisis de riesgo
aipha analysis risk-assessment

# 2. Crear propuesta para reducir riesgo
# (Reducir sl_factor permite salir más rápido)
aipha proposal create \
  --type parameter \
  --component trading_manager \
  --parameter sl_factor \
  --new-value 0.8 \
  --reason "Reducir pérdida máxima por trade"

# 3. Evaluar y aplicar
aipha proposal evaluate PROP_20251229_D7M
aipha proposal apply PROP_20251229_D7M
```

---

## Troubleshooting

### Problema: "Command not found: aipha"

```bash
# Solución: Instalar aiphalab en modo desarrollo
cd /home/vaclav/Aipha_0.0.2
pip install -e .

# Verificar:
aipha --help
```

### Problema: Dry-run no funciona

```bash
# Verificar que el orchestrator está actualizado
git pull origin main

# Verificar que tiene el parámetro dry_run
python -c "from core.orchestrator import CentralOrchestrator; print('OK')"

# Si falla, reinstalar core:
pip install -e .
```

### Problema: Propuestas siempre score < 0.70

```bash
# Significa que el sistema es conservador
# Ver por qué se rechaza:
aipha proposal evaluate PROP_ID --debug

# Output mostrará:
# Impact: 5/10 (demasiado bajo)
# Risk: 3/10 (demasiado alto)
# ...

# Crear propuestas MENOS arriesgadas:
# Por ejemplo: cambios pequeños (14→13 en lugar de 14→10)
```

### Problema: Sistema no genera trades

```bash
# Verificar configuración
aipha config validate

# Ver sugerencias
aipha config suggest Trading.atr_period

# Problema típico: atr_period muy alto
# Solución: Reducir a 10
aipha proposal create \
  --type parameter \
  --component trading_manager \
  --parameter atr_period \
  --new-value 10 \
  --reason "Aumentar sensibilidad de entrada"
```

---

## Roadmap Futuro

### v0.0.3: Mejoras a Propuestas
```bash
# Próximamente podrás:
aipha proposal create --ai-assisted  # LLM ayuda a generar
aipha proposal compare PROP_001 PROP_002  # Comparar dos propuestas
aipha proposal backtest PROP_001  # Backtestear contra histórico
```

### v0.0.4: Control Granular
```bash
# Próximamente podrás controlar:
aipha layer trading --adjust atr_period=12  # Control directo
aipha layer oracle --retrain  # Re-entrenar modelo
aipha layer postprocessor --disable  # Desactivar componentes
```

### v0.0.5: Análisis Avanzado
```bash
# Próximamente podrás:
aipha analysis sensitivity-analysis  # ¿Cuán sensible?
aipha analysis correlation-analysis  # ¿Qué impacta más?
aipha analysis stress-test  # ¿Resistencia a extremos?
```

---

## 🎓 Checklist de Aprendizaje

Marca cada item conforme lo completes:

### Nivel 1: Conceptos Básicos
- [ ] Entiendo las 5 capas de Aipha
- [ ] Entiendo el bucle cerrado de automejora
- [ ] Sé cómo funcionan los parámetros principales
- [ ] Entiendo la diferencia entre Capa 3, 4 y 5

### Nivel 2: Primeros Pasos
- [ ] Puedo ver el status del sistema (`aipha status`)
- [ ] Puedo ver la configuración (`aipha config view`)
- [ ] Puedo validar la configuración (`aipha config validate`)
- [ ] Entiendo qué significa cada número

### Nivel 3: Exploración
- [ ] Entiendo Capa 3 (Trading Manager)
- [ ] Entiendo Capa 4 (Oracle/ML)
- [ ] Entiendo Capa 5 (Post-Procesador)
- [ ] Sé qué parámetro cambiar para cada problema

### Nivel 4: Simulación
- [ ] Sé cómo usar `--dry-run`
- [ ] He simulado al menos 5 ciclos
- [ ] He analizado propuestas
- [ ] Entiendo qué significa score 0.78 vs 0.50

### Nivel 5: Implementación
- [ ] He creado una propuesta personalizada
- [ ] He evaluado una propuesta (scoring)
- [ ] He aplicado un cambio exitosamente
- [ ] Entiendo el protocolo atómico de 5 pasos

### Nivel 6: Monitoreo
- [ ] Veo el dashboard en tiempo real
- [ ] Entiendo el historial de cambios
- [ ] Puedo interpretar qué cambios están sucediendo
- [ ] Sé detectar si un cambio ayudó o no

---

## 🚀 Tu Próximo Paso Inmediato

**Comienza AHORA con estos 5 comandos (5 minutos):**

```bash
# 1. Ver estado
aipha status

# 2. Ver configuración
aipha config view

# 3. Validar configuración
aipha config validate

# 4. Ejecutar UN ciclo en dry-run
aipha --dry-run cycle run

# 5. Ver dashboard
aipha dashboard
```

**Después de esto, ya habrás comprendido el 50% de cómo funciona Aipha.**

---

## 📞 Soporte

Si tienes dudas:
1. Mira el archivo `ARCHITECTURE.md` para conceptos
2. Usa `aipha --help` para ver todos los comandos
3. Usa `aipha {comando} --help` para detalles específicos
4. Revisa el archivo `memory/action_history.jsonl` para ver historial completo

---

*Bienvenido al futuro de la automejora autónoma. Tu viaje de comprensión comienza aquí.* 🎯

**Versión:** 1.0
**Última actualización:** 29 de diciembre de 2025
**Para Aipha:** v0.0.2+
