# EVO-TICKET LOG — cgAlpha_0.0.1

> Origen: Apéndice — Constitutional Governance of Evolutionary Debt.
> "AlphaLab does not manage tasks. AlphaLab manages precedents.
>  EVO-TICKETs are precedents."
>
> AlphaLab como cámara completa (QUARANTINE_GATE, READY_FOR_CODEX,
> resurrección automática de tickets dormidos) NO EXISTE como
> componente — es arquitectura objetivo, igual que el Harness del
> Acto VIII (ver B008_NEXUS_CAPSULE.md).
>
> Lo que SÍ existe desde hoy: este log, en formato de ticket.
> Cuando EvolutionOrchestrator (P6) y MemoryPolicyEngine (P7) estén
> reconstruidos, este archivo es la semilla — se ingiere tal cual,
> sin reinterpretación, porque ya sigue el schema constitucional.
>
> Ciclo de vida formal (referencia):
> ANOMALY → INCUBATION → MATURITY → QUARANTINE_GATE →
> READY_FOR_CODEX → EXECUTING → IMPLEMENTED →
> EVOLUTIONARY_DEBT → RECONSTRUCTION → LIBRARY
>
> Mientras QUARANTINE_GATE/READY_FOR_CODEX no existan como gates
> automáticos, su función la cumple: revisión humana + Ruta C
> (LILA_ROUTING_PROMPT.md) + verificación contra §3 del Nexus.

---

## EVO-TICKET-0001 — Oracle v6 Fase A (Encoding + Observabilidad)

```
ORIGIN          : Operational Anomaly + Epistemic Distillation
                  (cobertura 54.77%, LabelEncoder no-determinista,
                  FEATURE_COLS legacy)

MATURITY        : MATURITY_3  [corregido 2026-06-13 — era MATURITY_5]
                  MOTIVO: evidencia anterior citaba oracle_v6_skeleton.py
                  y test_oracle_v6_skeleton.py como existentes. Ambos
                  verificados en Git: NO EXISTEN. Sin artefactos de
                  implementación reales el ticket no puede superar
                  MATURITY_3 (diseño consolidado, sin código todavía).
                  MATURITY_4 requiere: skeleton creado + ≥1 test de
                  contrato pasando en pytest.

VITALITY        : ACTIVE
                  (desbloqueado tras resolución de EVO-TICKET-0003)

ESTADO EN CICLO : READY_FOR_CODEX
                  [simulado — revisión humana aprobada, pendiente
                  sesión de ejecución con LLM avanzado]

PHANTOM FILES RESUELTOS (Causal Closure violation — verificado 2026-06-13):
  ❌→⏳ RECONSTRUCTION_BRIEF.md v1.1 — NO EXISTE → pendiente creación
  ❌→⏳ oracle_v6_skeleton.py       — NO EXISTE → pendiente creación
  ❌→⏳ test_oracle_v6_skeleton.py  — NO EXISTE → pendiente creación
  Estos archivos no pueden citarse como base de maturity hasta existir.

PRÓXIMOS PASOS para MATURITY_4:
  [ ] Crear oracle_v6_skeleton.py (interfaz pública, sin implementación)
  [ ] Crear test_oracle_v6_skeleton.py (tests de contrato de interfaz)
  [ ] pytest pasa → MATURITY_4 confirmada → sesión LLM avanzado

DEBT CLASS (estimado pre-ejecución) : CONSOLIDATION_DEBT
  Razón: consolida base existente con deuda técnica documentada.
  Capacidad nueva real es Fase B (EVO-TICKET-0002).

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE
  [ ] ADR-EVO-TICKET-0001-1-encoding-determinista (mínimo esperado)
  [ ] Actualización §3 Nexus si se fija ENCODING_MAP
  [ ] Actualización §7/§8 Nexus
```

---

## EVO-TICKET-0002 — Oracle v6 Fase B (Features dinámicas + walk-forward)

```
ORIGIN          : Human Investigation + Operational Anomaly
                  ("el Oracle aprende con features estáticas" — §1 Nexus)

MATURITY        : MATURITY_4
                  (dirección clara + bloqueantes extirpados via deliberación Ruta B)

VITALITY        : ACTIVE
                  (reapertura formal 2026-06-23 — ver UPDATE LOG abajo)

ESTADO EN CICLO : READY_FOR_CODEX

DEBT CLASS (estimado) : EXPANSION_DEBT

PROTOCOLO DE RESURRECCIÓN:
  Cuando P3 (L2 Ring Buffer) y P4 (DeferredOutcomeMonitor) tengan CRB:
    (a) retomar INCUBATION con nueva evidencia, o
    (b) terminar formalmente si suposiciones ya no aplican.
  "Permanent abandonment is forbidden."

  ✅ RESURRECCIÓN EJECUTADA 2026-06-23:
     - CRB P3 creado (CRB_BinanceWebSocketManager_P3.md)
     - CRB P4 creado (CRB_DeferredOutcomeMonitor_P4.md)
     - ADR-RECONCILIATION-1 aplicado (Nexus reconciliado con código vivo)
     - ADR-FRICCION-ECONOMICA-1 aprobado (Opción C: EconomicGate en P9)
     - ADR-ACOPLAMIENTO-TEMPORAL-1 aprobado (D-014: ε=200ms)
     - Puerta de Cobertura Base añadida a plantilla RMU
     - Nexus §5.7 issue #3 y §5.4 issue #5 marcados ✅ RESUELTO via D-014

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE
  [ ] ADR: walk-forward vs split estático
  [ ] ADR: diseño Ring Buffer feed hacia Oracle (interfaz con P3)
      ✅ PARCIAL: D-014 establece el acoplamiento temporal (t_feature ≤ t_candle_close − 200ms).
         Falta ADR de interfaz schema (qué features exactas consume el Oracle).

PLAN DE ATAQUE (post-reapertura):
  Ver sección "PLAN DE ATAQUE — EVO-TICKET-0002" al final de este ticket.
```

### UPDATE LOG — EVO-TICKET-0002

**2026-06-23 — Reapertura formal:**
- **Vitality:** DORMANT → ACTIVE
- **Maturity:** MATURITY_3 → MATURITY_4
- **Lifecycle:** INCUBATION → READY_FOR_CODEX
- **Razón:** Deliberación arquitectónica Ruta B extirpó todos los bloqueantes.
  El forense de código vivo reveló que P3 y P4 estaban más implementados
  de lo que el Nexus reportaba (Document Drift). Los verdaderos bloqueos
  eran: (1) cobertura cero/incompleta, (2) time drift sin caracterizar,
  (3) fricción económica sin decidir. Los tres están ahora resueltos a
  nivel de diseño: Puerta de Cobertura Base (RMU template), D-014
  (acoplamiento temporal), y ADR-FRICCION-ECONOMICA-1 (Opción C).
- **Artefactos generados:** 2 CRBs, 3 ADRs, 1 D-ID (D-014), Nexus
  reconciliado, 11 eventos constitucionales registrados.

### PLAN DE ATAQUE — EVO-TICKET-0002

El plan sigue la lógica de dependencias: primero habilitar P3 y P4
(auditar + testear + caracterizar drift), luego ejecutar Fase B del Oracle.

**Fase 0 — Prerrequisitos (pueden ejecutarse en paralelo):**

  P3-A1. Escribir tests para L2RingBuffer (8 tests, ver CRB P3 §6 Fase A).
  P3-A2. Escribir tests para BinanceWebSocketManager (7 tests, ver CRB P3 §6 Fase A).
  P4-A1. Medir cobertura actual de P4 con pytest --cov sobre tests existentes.
  P4-A2. Escribir tests para _evaluate (10 tests, ver CRB P4 §6 Fase A).
  P4-A3. Escribir tests para tick (8 tests, ver CRB P4 §6 Fase A).
  P4-A4. Escribir tests para _flush_resolved (4 tests, ver CRB P4 §6 Fase A).

  Puerta de Cobertura Base: P3 ≥ 50%, P4 ≥ 70% antes de avanzar.

**Fase 1 — Caracterización forense (depende de Fase 0):**

  P3-B1. Estudio forense de Time Drift: medir local_offset_ms sobre ≥1000
         mensajes en producción. Reportar min/p50/p95/max.
         Si p95 > 200ms, aumentar ε o mejorar NTP.
         Si p95 ≤ 100ms, considerar bajar ε a 100ms (requiere nuevo ADR).
  P3-B2. Implementar D-014 en synthesize_at_retest(): filtrar snapshots
         con ts > t_candle_close_ms − 200ms. Añadir l2_data_quality="CAUSAL_REJECTED".
  P3-B3. Fix _empty_profile() schema (issue #5 del CRB P3).
  P3-B4. Cambiar last_trades a deque(maxlen=10000) (issue #4 del CRB P3).
  P4-B1. Migrar 4 usos de time.time() en P4 a binance_ts_ms (D-014).
  P4-B2. Fix docstring de adaptive_lookahead (issue #3 del CRB P4).
  P4-B3. Fix hours_since_flip para usar binance_ts_ms (issue #10 del CRB P4).

**Fase 2 — Fase B del Oracle (depende de Fase 1):**

  O-B1. Diseñar schema de features dinámicas del Oracle v6: qué features
         exactas consume del l2_temporal_profile (23 campos del Ring Buffer).
         ADR de interfaz schema (entregable constitucional pendiente).
  O-B2. Implementar walk-forward validation (ADR pendiente: walk-forward
         vs split estático — entregable constitucional pendiente).
  O-B3. Re-entrenar Oracle v6 con features dinámicas + walk-forward.
  O-B4. RECONSTRUCTION_MAP_UPDATE + ADRs de cierre.

**Fase 3 — Fricción económica (paralela, no bloquea Fase 2):**

  P9-A1. Redactar CRB de ShadowTrader (P9) con EconomicGate como Fase A.
  P9-A2. Implementar estimate_slippage(spread_bps, depth, order_size).
  P9-A3. Añadir economic_gate_decision y friction_atr_est a bridge.jsonl.
  P9-A4. Métrica de rejection rate en GUI.
  O-B5. (Feedback loop) Evaluar si economic_gate_decision histórica mejora
        la predicción como feature de régimen en Fase B del Oracle.

**Dependencias críticas:**
  - Fase 1 depende de Fase 0 (Puerta de Cobertura Base).
  - Fase 2 depende de Fase 1 (D-014 implementado + drift caracterizado).
  - Fase 3 es paralela a Fase 2 (no bloquea al Oracle).

**Entregables constitucionales al cierre:**
  [ ] RECONSTRUCTION_MAP_UPDATE (Fase 2)
  [ ] ADR: walk-forward vs split estático (Fase 2, O-B2)
  [ ] ADR: diseño Ring Buffer feed hacia Oracle (Fase 2, O-B1)
      ✅ PARCIAL: D-014 establece el acoplamiento temporal.

---

## EVO-TICKET-0003 — WebSocket Pipeline Freeze (RESUELTO)

```
ORIGIN          : Operational Anomaly (dos observaciones confirmadas)
                  Primera: ~2026-06-10 06:55 UTC
                  Segunda: 2026-06-13 (diagnóstico operador)
                  Pipeline inactivo: 3 días. PID 165833 vivo,
                  conexión ESTABLISHED, ficheros congelados.

CAUSA RAÍZ CONFIRMADA — H4 (verificada en código 2026-06-13):
  live_adapter.py línea ~110: on_ws_message() despachaba ÚNICAMENTE
  en event_type == 'aggTrade'. Cuando Binance Futures silencia ese
  stream (verificado experimentalmente), depthUpdate sigue fluyendo
  a 10 msg/s manteniendo el TCP ESTABLISHED — pero el reloj interno
  del pipeline nunca avanza. Resultado: proceso vivo, pipeline muerto.

  Corrección de registro previo:
  - Puntos Ciegos #3 y #4 marcados como "no implementados" en ticket
    original — ERROR. Ambos SÍ implementados en BWS:
    PC#3: get_rolling_delta() línea 241 (rolling window, no global)
    PC#4: _connection_epoch líneas 54/97/99 (tracking reconexiones)
  - H1/H2/H3 descartadas. H4 es la causa real y única.

MATURITY        : MATURITY_5 → IMPLEMENTED
VITALITY        : ACTIVE → RESOLVED
ESTADO EN CICLO : IMPLEMENTED (2026-06-13)

FIX IMPLEMENTADO — Heartbeat Watchdog (live_adapter.py):
  _last_aggtrade_ts_ms: int    — timestamp del último aggTrade
  _heartbeat_timeout_ms: 30000 — 30s sin aggTrade = stream muerto
  _last_heartbeat_price: float — último precio conocido

  on_ws_message() extendido:
    aggTrade → procesar normalmente (sin cambio)
    depthUpdate → calcular gap = depth_ts - last_aggtrade_ts
                  si gap > 30s → _heartbeat_candle_close(depth_ts)

  _heartbeat_candle_close():
    cierra vela usando timestamp de depth + último precio conocido
    o best bid del book si no hay precio de aggTrade disponible
    volumen = 0.0 (factualmente correcto: no hubo trades en ese periodo)

DEBT CLASS CONFIRMADO : EMERGENCY_DEBT
  (interrupción de 3 días en recolección de Set A)
  → pasa a EVOLUTIONARY_DEBT registrado: live_adapter.py tiene
  ahora dependencia de _last_heartbeat_price como fallback de precio,
  que puede ser stale si el silencio de aggTrade es muy prolongado.
  Riesgo documentado en ADR-EVO-TICKET-0003-1.

NOTA SOBRE ADR-008 (nomenclatura del editor):
  El editor lo llamó "ADR-008". La convención canónica de este log es
  ADR-EVO-TICKET-0003-1-heartbeat-watchdog. El contenido es correcto.
  Se almacena bajo ambos nombres para trazabilidad.

NOTA SOBRE "PUNTO CIEGO #7":
  ADR-008 referencia "Punto Ciego #7 (identificado tras el fallo)".
  No existía en architectural_analysis.md (que solo define PC#1-#6).
  Formalmente: este fallo constituye un nuevo Punto Ciego y debería
  añadirse al documento base como PC#7 — single clock source
  dependency. Pendiente de sesión que actualice ese documento.

ENTREGABLES CONSTITUCIONALES — ESTADO FINAL:
  [x] FIX implementado y verificado (live_adapter.py extendido)
  [x] ADR-EVO-TICKET-0003-1-heartbeat-watchdog generado
  [x] RECONSTRUCTION_MAP_UPDATE — governance_log/RMU-EVO-TICKET-0003-2026-06-13.md
  [ ] Actualizar §3 Nexus: _heartbeat_timeout_ms como parámetro protegido
  [ ] Añadir PC#7 a architectural_analysis.md

PID DE VERIFICACIÓN: 686383 (activo desde 2026-06-13 07:55)
  active_zones.json actualiza cada ~60s ✅
  market_price.json actualiza cada ~60s ✅
```

---

## EVO-TICKET-0005 — TripleCoincidenceDetector: zone cleanup + warm_start fix

```
ORIGIN          : Operational Anomaly (GUI mostraba zonas obsoletas
                  66.5k-66.0k con precio en 63.9k) + Human Investigation
                  Componente: P5 del Nexus (TripleCoincidenceDetector)
                  — SIN CRB todavía, zona de mayor riesgo del sistema.

CAUSA RAÍZ IDENTIFICADA:
  1. feed_kline_for_zone_detection recalculaba tendencias ZigZag por
     vela en lugar de precalcular sobre buffer — con 60 velas rara
     vez encontraba segmento válido.
  2. warm_start solo hidrataba buffer, no reproducía detección
     histórica — zonas persistidas nunca se renovaban tras reinicio.
  3. _cleanup_expired_zones usaba candle_index del buffer, no
     comparable entre reinicios (mismo patrón que Punto Ciego #4
     de architectural_analysis.md — estado no estable ante restart).

MATURITY        : MATURITY_3
                  Diagnóstico verificado, fix aplicado, tests
                  preexistentes confirmados (no rotos por el cambio).
                  No sube a MATURITY_4 porque zone_max_distance_atr
                  está marcado calibration_pending (ver abajo) — un
                  componente con un parámetro no calibrado no puede
                  considerarse diseño completo, solo funcional.

VITALITY        : ACTIVE
ESTADO EN CICLO : EXECUTING
                  (servidor detenido intencionalmente, pendiente
                  verificación final antes de reinicio — ver
                  Verificaciones Pendientes)

DEBT CLASS      : CONSOLIDATION_DEBT
  [CORREGIDO 2026-06-14 — editor reportó "CALIBRATION_DEBT", clase
  no válida. El Apéndice define únicamente 4 clases canónicas:
  EXPANSION/CONSOLIDATION/EMERGENCY/TOXIC. "Calibración pendiente"
  es ortogonal a la clase de deuda, no una clase en sí misma —
  ver flag calibration_pending abajo.]

CALIBRATION_PENDING (flag ortogonal, no clase de deuda):
  calibration_pending: true
  parameter: zone_max_distance_atr
  current_value: 5.0
  method_required: "percentile analysis de distancia real entre
                    zonas expiradas vs activas, sobre ≥200 ciclos
                    de detección — misma metodología aplicada al
                    ZigZag threshold (cronica_desarrollo_cgAlpha.md,
                    lección operativa #2)."
  marca_en_codigo: "EVO-TICKET-0005: zone_max_distance_atr is
                    PROVISIONAL" — comentario ya insertado en
                    triple_coincidence.py junto al valor.

VERIFICACIONES COMPLETADAS:
  [x] Backup de detector_state.json y active_zones.json antes del wipe
  [x] Estado restaurado desde backup, servidor detenido
  [x] git checkout <commit>^ -- archivos (NO stash — cambios ya
      commiteados, stash no aplicaba). Confirmado: 2 tests fallan
      idéntico antes/después → preexistentes, no regresión.
  [x] --collect-only confirmó 4 tests recolectados, sin errores
      de import silenciando tests
  [x] zone_max_distance_atr marcado PROVISIONAL en código + ticket
  [x] debt_class corregida a CONSOLIDATION_DEBT + calibration_pending
      (ya no CALIBRATION_DEBT, clase no canónica)

COMMITS:
  e984c61 — fix stale active zones after restart
  2155bdd — correct debt class and add calibration_pending flag
  (ambos en origin/main)

NOTA — MATURITY se mantiene en 3, no sube a pesar de verificación
completa. Razón: rigor de proceso y calibración del parámetro son
ejes ortogonales. zone_max_distance_atr sigue sin pasar por análisis
de percentiles — eso es lo único que puede subir la maturity de este
ticket, no la calidad de la verificación del fix en sí.

ESTADO POST-REINICIO (verificado 2026-06-14):
  active_zones: 0          → Criterio #1 CUMPLIDO (zonas viejas no
                              reaparecieron)
  dataset_total: 236        → pipeline no interrumpido durante el
  full_samples: 94            trabajo (85→92→94 FULL en esta sesión)
  pending_count: 0

  Criterio #2 (zona nueva detectada en ~50 velas) AÚN NO VERIFICABLE
  — active_zones=0 es consistente tanto con "fix funcionó, el
  mercado no ha formado zona válida todavía" como con "el bug
  persiste". Ticket permanece en EXECUTING, no pasa a IMPLEMENTED,
  hasta observar al menos una detección real post-fix.

CRITERIOS DE ÉXITO post-reinicio:
  1. Las 2 zonas viejas (66.5k-66.0k) no reaparecen
  2. Si el mercado forma zona válida, aparece en L2 Forensics
     dentro de ~50 velas
  3. El dataset sigue creciendo (training_dataset_v2.jsonl)

OBSERVACIÓN ~10H POST-RESTART (2026-06-20):
  Criterio #1: CUMPLIDO (zonas viejas no reaparecieron)
  Criterio #2: NO CUMPLIDO — active_zones.json vacío, sin ninguna
               detección nueva en logs en 10h
  Criterio #3: NO CUMPLIDO — training_dataset_v2.jsonl congelado
               desde 2026-06-19 09:27:02 (~21h), CERO muestras
               nuevas desde el restart con el fix aplicado.

  HALLAZGO INICIAL (parcialmente correcto, causa real distinta):
  El freeze del dataset (21h) era más largo que el silencio de
  aggTrade (2.4h) — confirmó que no eran la misma causa. La
  hipótesis de "ruta de escritura duplicada" resultó ser un falso
  positivo (logging en WARNING ocultaba los logs de INFO; el grep
  de market_price buscaba un string literal que se construye con
  f-string en runtime).

  CAUSA RAÍZ CONFIRMADA (2026-06-20, 3 rondas de Ruta A):
  El proceso PID 309946 arrancó a las 2026-06-19 20:12:51.
  El commit del fix (2155bdd) es de las 20:21:27 — 9 minutos
  DESPUÉS. Un proceso Python no puede ejecutar código que no
  existía cuando arrancó. El servidor en ejecución corre el
  código PRE-fix de EVO-TICKET-0005. El fix nunca se desplegó.

  Esto NO es una hipótesis — es una certeza dado el orden de
  eventos (timestamp de inicio de proceso vs timestamp de commit,
  comparación directa, sin ambigüedad).

  Verificaciones que sostienen esta conclusión:
  - detector_state.json y active_zones.json se modifican en el
    mismo segundo → _persist_active_zones() SÍ se ejecuta → el
    pipeline de cierre de velas está vivo, no muerto.
  - Logging efectivo = WARNING → explica por qué nunca se vieron
    los logs INFO de "Candle close procesada" / "Zonas GUI
    persistidas" durante 10+ horas de diagnóstico, generando
    falsa sospecha de pipeline congelado.
  - El freeze del dataset a las 09:27 del 19/06 es EL MISMO bug
    original que motivó la creación de este ticket — no es un
    evento nuevo. El reinicio de las 20:12 ocurrió ANTES del
    commit del fix, así que nunca tuvo oportunidad de corregirlo.

  ACCIÓN REQUERIDA (Ruta C — ejecutar, no más diagnóstico):
  1. Reiniciar servidor: kill 309946, levantar proceso nuevo
  2. Verificar inmediatamente: ps -o lstart= -p <nuevo_pid>
     DEBE ser POSTERIOR a 2026-06-19 20:21:27 (commit 2155bdd)
  3. NO declarar el fix desplegado solo por hacer `git push` —
     confirmar con el paso 2 cada vez, sin excepción
  4. Monitorear con el método ya validado (mtime sync de
     detector_state.json / active_zones.json), no depender de
     logs INFO mientras el nivel sea WARNING
  5. Reevaluar Criterio #2 y #3 después de ≥50 velas con el
     código real corriendo

  ✅ EJECUTADO (2026-06-20, 06:37:54):
  Proceso nuevo PID 460712 confirmado posterior al commit
  (10h después). Paso 7 de Ruta C (Verificar Despliegue) validado
  en su primer uso real — funcionó exactamente como se diseñó.

  RESULTADO TRAS 90 MIN + TEST AISLADO:
  - active_zones.json sigue vacío tras 90 min en vivo (1m)
  - Test aislado: 200 velas 1m → 0 zonas | 500 velas 5m → 9 zonas
  - Interpretación: el detector SÍ encuentra zonas cuando el
    timeframe lo permite (5m) → el código del fix funciona.
    En 1m, con el rango actual (~$600 en ~3h), no hay coincidencias
    bajo los thresholds vigentes → consistente con calibration_pending
    ya documentado, no con un bug nuevo.

  ⚠️ PENDIENTE ANTES DE CERRAR COMO "SOLO CALIBRACIÓN":
  Confirmar que el test aislado usó la MISMA instanciación de
  TripleCoincidenceDetector que live_adapter.py en producción
  (mismos parámetros), y que las velas de 1m comparadas no
  incluyen velas sintetizadas por heartbeat (volume=0.0) que no
  estarían en un test con datos REST limpios. Dado el historial
  de esta sesión (un "desplegado" que no lo estaba durante 10h),
  una confirmación más antes de archivar esto como calibración
  pura, no bug, es barata y reduce el riesgo de cerrar en falso.

  Si se confirma → este ticket converge a su forma esperada desde
  el inicio: fix verificado y correcto, deuda de calibración
  explícita pendiente (zone_max_distance_atr + thresholds 1m de
  KeyCandleDetector/ZoneDetector), NO bloqueante para Oracle v6
  Fase A (Set A ya tiene 94 FULL, suficiente).

  NOTA — zscore_calibration_log (0 líneas desde 17/jun) mencionado
  por el editor: posible infraestructura de calibración ya
  existente sin usar. Revisar antes de diseñar análisis de
  percentiles desde cero para resolver calibration_pending.

  ✅ CONFUSORES VERIFICADOS (2026-06-20, commit 6b64972):
  1. Config del detector idéntica entre test manual y producción
     (TripleCoincidenceDetector() sin args, confirmado por grep
     en server.py y launch_shadow_live.py).
  2. Barrido paramétrico de velas heartbeat (10%/50% volume=0
     inyectado) NO cambió el resultado — 0 zonas en 1m persiste
     en las 3 variantes. Confusor de heartbeat descartado.
  Comparación de control limpia: 200 velas 1m → 0 zonas |
  500 velas 5m → 9 zonas (misma config, mismo detector).

  ⚠️ HIPÓTESIS NUEVA — REFRAME de calibration_pending
  (2026-06-20, pendiente de verificación):
  Toda la calibración histórica documentada (zigzag_threshold=0.18%,
  cronica_desarrollo_cgAlpha.md Fase 4) se hizo contra "288 velas
  BTCUSDT 5m" — explícitamente 5 minutos, no 1 minuto. Pero
  live_adapter.py usa interval_s=60 (1 minuto) para la detección
  de zonas (Speed 1 del Two-Speed Architecture).

  Bajo random walk: rango típico de vela 1m ≈ 45% del rango de 5m
  (escala con raíz de tiempo); volumen típico ≈ 20% (escala
  linealmente). Thresholds calibrados para 5m aplicados sin ajuste
  a 1m serían sistemáticamente demasiado estrictos — explica el
  0 vs 9 de forma ESTRUCTURAL, no solo empírica, y es consistente
  con que el test de control SÍ detectó zonas en 5m usando los
  mismos thresholds.

  ✅ INVESTIGACIÓN CONVERGIDA (2026-06-20) — 4 rondas de Ruta A.

  Git archaeology confirmó: interval_s=60 introducido commit
  aa0190df (12 abr 2026), comentario original "Default 1m para
  el MVP live demo" — decisión de demo, NO calibrada. El comentario
  se perdió en el refactor "Two-Speed Architecture" (807b772,
  4 may 2026), que heredó 1m sin reconciliar con la calibración
  ZigZag de 5m hecha ~29 abr (entre ambos commits).

  Test decisivo: las MISMAS 200 y 1000 velas de 1m, agrupadas en
  velas sintéticas de 5m → 0 zonas en ambas granularidades sobre
  el mismo período. Esto refina (no descarta) la hipótesis de
  desajuste de timeframe: el desajuste es real y documentado, PERO
  el régimen de mercado de las últimas ~16h también es atípicamente
  quieto (rango ~$600 sostenido) — ambos factores contribuyen,
  ninguno por sí solo explica el resultado completo.

  Hallazgo adicional: fallbacks de timestamp en triple_coincidence.py
  (`candle["index"] * 300000`, L1292/L1356) asumen implícitamente
  5 minutos por vela — evidencia secundaria de que el detector se
  diseñó pensando en 5m, consistente con la calibración documentada.

  REFRAME FINAL de calibration_pending:
  No es "calibrar zone_max_distance_atr con percentiles de 1m" —
  es una decisión arquitectónica entre 3 opciones (ver abajo),
  ninguna requiere construir calibración nueva desde cero si se
  elige la opción A.

  DECISIÓN RECOMENDADA: Opción A — revertir interval_s a 300 (5m),
  ajustar lookback_candles/retest_timeout_bars proporcionalmente.
  Razón: reutiliza calibración YA validada (ZigZag 0.18%, P75 5m),
  sin trabajo nuevo de calibración. El costo (latencia de detección
  de zonas nuevas ~5min en vez de ~1min) es irrelevante mientras el
  sistema cosecha datos de entrenamiento, no ejecuta trades en vivo
  con sensibilidad a latencia. Retests (tick-level) y captura L2 (al
  toque de zona) no dependen de interval_s — siguen funcionando igual.
  Opciones B (recalibrar 1m desde cero) y C (timeframe configurable)
  son optimización prematura sobre una premisa (1m) que nunca tuvo
  evidencia de ser mejor que 5m — fue un default de demo sin validar.

  ESTADO: Cat.2 — requiere ADR antes de aplicar. NO aplicado todavía.
  Spin-off recomendado: EVO-TICKET-0006 (ver más abajo) para separar
  esta decisión arquitectónica del bugfix de cleanup/warm_start
  (que SÍ está completo y verificado en este ticket).

  LECCIÓN DE DISEÑO DE CRITERIOS DE ÉXITO:
  El Criterio #2 original ("zona nueva en ≤50 velas") asumía que el
  mercado cooperaría dentro de una ventana fija, sin controlar por
  régimen. Eso generó +10h de investigación que parecía apuntar a
  un bug cuando en realidad era una combinación de desajuste
  arquitectónico + régimen atípico. Criterios de éxito futuros que
  dependan de "observar X en N unidades de tiempo" deberían incluir
  una condición de control (ej: "O bien aparece X, O bien se
  confirma con un test aislado que la lógica es correcta
  independientemente del régimen") para no bloquear el cierre de
  un ticket indefinidamente por causas ajenas al cambio evaluado.

  LECCIÓN DE PROCESO (aplicable a todo Cat.1/2/3 futuro):
  "Commiteado" ≠ "Desplegado". Ruta C necesita un paso explícito
  de verificación post-aplicación: confirmar que el proceso que
  debe ejecutar el cambio realmente lo cargó (timestamp de inicio
  de proceso > timestamp de commit). Sin este paso, un fix puede
  considerarse "aplicado" durante horas o días sin estar activo.
  YA INCORPORADO a LILA_ROUTING_PROMPT.md (Ruta C, paso 7) y
  VALIDADO en su primer uso real el 2026-06-20.

ENTREGABLES CONSTITUCIONALES — ESTADO FINAL:
  [x] RECONSTRUCTION_MAP_UPDATE — governance_log/RMU-EVO-TICKET-0005-2026-06-20.md
  [x] ADR-EVO-TICKET-0005-1-cleanup-por-tiempo-distancia.md generado
  [x] Iniciar CRB de TripleCoincidenceDetector (P5) — creado
      cgalpha_v4/CRB_TripleCoincidenceDetector_P5.md (2026-06-21).
      Nexus §5.3 y §8 actualizados.
  [x] Verificación de despliegue: incorporada a LILA_ROUTING_PROMPT.md
      (Ruta C, paso 7), validada en uso real 2026-06-20
  [x] Hipótesis de timeframe mismatch: CONFIRMADA con git archaeology
      + test de control (200/1000 velas 1m agrupadas a 5m sintético)
  [x] calibration_pending separado a EVO-TICKET-0006 (cerrado con Opción A)
```

---

## EVO-TICKET-0006 — Decisión arquitectónica: reconciliar timeframe de detección (1m vs 5m)

```
ORIGIN          : Human Investigation + Operational Anomaly
                  Spin-off de EVO-TICKET-0005 — separado porque es
                  una decisión arquitectónica distinta del bugfix
                  de cleanup/warm_start (que ya está completo).

CONTEXTO CONFIRMADO (heredado de la investigación de EVO-0005):
  - interval_s=60 (1m) es un default de "MVP live demo" sin
    calibrar (commit aa0190df, 12 abr 2026)
  - Toda la calibración de thresholds documentada (ZigZag 0.18%,
    fallbacks de timestamp asumiendo 300000ms) se hizo contra 5m
  - Two-Speed Architecture (807b772, 4 may) heredó 1m sin reconciliar
  - Test de control: las mismas velas agrupadas a 5m sintético
    también dan 0 zonas en el período observado (régimen actual
    atípicamente quieto, ~$600 de rango sostenido)

MATURITY        : MATURITY_3
                  3 opciones caracterizadas con costo/beneficio,
                  evidencia de archaeology completa, sin ADR todavía
                  ni decisión humana formal.

VITALITY        : ACTIVE
ESTADO EN CICLO : INCUBATION
                  Esperando decisión humana antes de pasar a
                  QUARANTINE_GATE → READY_FOR_CODEX.

OPCIONES (documentadas, no aplicadas):

  OPCIÓN A (recomendada) — Revertir a 5m
    interval_s: 60 → 300
    Ajustar proporcionalmente: lookback_candles, retest_timeout_bars
    Costo: latencia de detección de zonas nuevas ~5min vs ~1min
           (irrelevante en modo cosecha, no ejecución en vivo)
    Beneficio: reutiliza calibración YA validada, cero trabajo
               nuevo de calibración
    Categoría: Cat.2 (toca live_adapter.py, requiere ADR)

  OPCIÓN B — Recalibrar todo para 1m
    Requiere estudio de percentiles reales en 1m (zscore_calibration_log
    existe pero está dormido, 0 líneas desde 17/jun — necesitaría
    alimentarse primero, lo cual es circular: para calibrar hacen
    falta muestras, para tener muestras hace falta calibración)
    Costo: alto, EXPANSION_DEBT significativa
    Categoría: Cat.3 (cambio estructural de múltiples thresholds)

  OPCIÓN C — Timeframe configurable + calibración dual
    Más robusto a largo plazo, mayor inversión
    Costo: más alto que B
    Categoría: Cat.3, candidato para CRB de P5 (TripleCoincidenceDetector)
               más que para un EVO-TICKET aislado

DEBT CLASS      : CONSOLIDATION_DEBT si se elige Opción A
                  EXPANSION_DEBT si se elige Opción B o C

NO BLOQUEA:
  Oracle v6 Fase A — Set A ya tiene 94 FULL, muy por encima del
  umbral (24). Esta decisión solo afecta velocidad de cosecha
  futura para Fase B, no la reconstrucción actual del Oracle.

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [x] Decisión humana explícita: Opción A confirmada
  [x] ADR-EVO-TICKET-0006-1-live-candle-interval-5m.md creado
  [x] Aplicado via Ruta C con paso 7 (verificación de despliegue):
      commit 24ea987 (16:01:33) → PID 627736 arrancó 16:02:00,
      27s después del commit. Confirmado correctamente SIN
      necesidad de recordatorio externo — primera señal de que
      el paso 7 se internalizó como parte del proceso por defecto.
  [x] Verificación post-cambio: 500 velas 5m reales → 11 zonas
      detectadas. warm_start ajustado a solicitar velas 5m (catch
      no anticipado explícitamente, correcto por consistencia).
  [x] D-011 añadida a §3 del Nexus: interval_s=300 protegido,
      requiere ADR + recalibración completa para cambiar
  [x] RECONSTRUCTION_MAP_UPDATE — governance_log/RMU-EVO-TICKET-0006-2026-06-20.md

ESTADO: IMPLEMENTED (código desplegado y verificado en producción)

✅ DEUDA DE RMU SALDADA (2026-06-21) — sesión en bloque completada:
  EVO-TICKET-0003 → governance_log/RMU-EVO-TICKET-0003-2026-06-13.md
  EVO-TICKET-0004 → governance_log/RMU-EVO-TICKET-0004-2026-06-14.md
  EVO-TICKET-0005 → governance_log/RMU-EVO-TICKET-0005-2026-06-20.md + ADR-0005
  EVO-TICKET-0006 → governance_log/RMU-EVO-TICKET-0006-2026-06-20.md
```

> Estado actual (snapshot). Historia completa en constitutional_events.jsonl.

| Ticket | Fecha cierre | RMU | ADRs | Debt final | Estado |
|---|---|---|---|---|---|
| EVO-TICKET-0001 | 2026-06-21 | governance_log/RMU-EVO-TICKET-0001-2026-06-21.md ✅ | ADR-EVO-TICKET-0001-1-encoding-determinista.md ✅ | CONSOLIDATION | IMPLEMENTED — MATURITY_5 (28/28 tests, 100% cov, D-007 verificado sin violación, alcance respetado: oracle.py v3 y live_adapter.py NO tocados) |
| EVO-TICKET-0002 | bloqueado P3/P4 | — | — | EXPANSION | DORMANT |
| EVO-TICKET-0003 | 2026-06-13 | governance_log/RMU-EVO-TICKET-0003-2026-06-13.md ✅ | ADR-EVO-TICKET-0003-1 ✅ | EMERGENCY | IMPLEMENTED |
| EVO-TICKET-0004 | 2026-06-14 | governance_log/RMU-EVO-TICKET-0004-2026-06-14.md ✅ | No requerido (Cat.2 sin alternativas arquitectónicas) | EXPANSION | IMPLEMENTED — endpoint /api/admin/read-file |
| EVO-TICKET-0005 | 2026-06-20 | governance_log/RMU-EVO-TICKET-0005-2026-06-20.md ✅ | ADR-EVO-TICKET-0005-1 ✅ | CONSOLIDATION | IMPLEMENTED (calibration_pending: zone_max_distance_atr=5.0 PROVISIONAL) |
| EVO-TICKET-0006 | 2026-06-20 | governance_log/RMU-EVO-TICKET-0006-2026-06-20.md ✅ | ADR-EVO-TICKET-0006-1 ✅ | CONSOLIDATION | IMPLEMENTED |

---

## EVO-TICKET-0004 — P6.5 File Reader (G4 building block)

```
ORIGIN          : Human Investigation (sesión 2026-06-14)
                  "una herramienta simple — un endpoint que dado un
                  path relativo devuelve el contenido del archivo"
                  Conexión directa con D-010: habilita LLM Readability
                  Check en tiempo real durante sesiones de chat.

MATURITY        : MATURITY_5  [actualizado 2026-06-14]
                  Implementado en server.py. Verificado con py_compile.
                  MATURITY_4 → MATURITY_5: endpoint activo y verificado.

VITALITY        : ACTIVE
ESTADO EN CICLO : IMPLEMENTED  [2026-06-14]

COMPONENTE      : Chat de Lila (P6.5 del Nexus)
GAP QUE AVANZA  : G4 (ContextBuilder dinámico) — building block
                  Los gaps G2/G3/G5 quedan pendientes para sesión
                  posterior (prerequisito: este ticket cerrado).

PROTECTED_MODULES TOCADOS:
  server.py — añade endpoint nuevo. No modifica endpoints existentes.
  deferred_outcome_monitor.py — NO TOCADO.
  oracle.py — NO TOCADO.

DEBT CLASS      : EXPANSION_DEBT
  Nueva capacidad (lectura dinámica de archivos en chat)
  sobre infraestructura existente (server.py Flask).

INVARIANTES DEL ENDPOINT (no negociables — ver P65_FILE_READER_SPEC.md):
  1. path siempre resuelto contra _PROJECT_ROOT_READER
  2. Solo GET — nunca modifica archivos
  3. @require_auth obligatorio
  4. Archivos >100KB sin rango → 413

DESVIÓN DE ESPECIFICACIÓN (registrado):
  Ruta implementada : /api/admin/read-file
  Ruta en spec      : /api/lila/read-file  (P65_FILE_READER_SPEC.md)
  Funcionalidad     : idéntica
  Razón             : no registrada en sesión de implementación.
  Acción requerida  : ninguna para el ticket actual — si la ruta
                      se expone en documentación pública o en el
                      Codex hay que reflejar la ruta real.

ENTREGABLES CONSTITUCIONALES — ESTADO FINAL:
  [x] Aplicar código de P65_FILE_READER_SPEC.md en server.py
  [x] Verificación con py_compile (sustituye pytest para Cat.2 simple)
  [ ] RECONSTRUCTION_MAP_UPDATE — NO GENERADO (deuda sistemática:
      mismo gap que EVO-TICKET-0003, 0005, 0006 — ver nota)
  [ ] Actualizar §5.11 del Nexus con Knowledge Card del File Reader
  [ ] Actualizar §8 del Nexus: P6.5 de "iniciado" a "G4 partial"

NOTA — PATRÓN DE DEUDA DE RMU (identificado 2026-06-21):
  EVO-TICKET-0003, 0004, 0005 y 0006 cerraron sin RMU.
  El ledger registró el cierre técnico pero el entregable de
  documentación quedó "pendiente" sistemáticamente en los cuatro.
  No es una anomalía aislada — es una brecha de proceso:
  el RMU nunca fue obligatorio en el momento del cierre.
  Acción correctiva: sesión de RMUs en bloque (4 documentos).
  Ver §0 Paso 0 del Nexus v0.5 para el guardrail permanente.
```
