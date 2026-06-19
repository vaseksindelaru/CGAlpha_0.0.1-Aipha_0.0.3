# EVO-TICKET LOG — cgAlpha_0.0.1

```
Origen: Apéndice — Constitutional Governance of Evolutionary Debt.
"AlphaLab does not manage tasks. AlphaLab manages precedents.
EVO-TICKETs are precedents."

AlphaLab como cámara completa (QUARANTINE_GATE, READY_FOR_CODEX,
resurrección automática de tickets dormidos) NO EXISTE como
componente — es arquitectura objetivo, igual que el Harness del
Acto VIII (ver NEXUS_SUPERIOR.md §5.11, líneas 703/721).

Lo que SÍ existe desde hoy: este log, en formato de ticket.
Cuando EvolutionOrchestrator (P6) y MemoryPolicyEngine (P7) estén
reconstruidos, este archivo es la semilla — se ingiere tal cual,
sin reinterpretación, porque ya sigue el schema constitucional.

Ciclo de vida formal (referencia):
ANOMALY → INCUBATION → MATURITY → QUARANTINE_GATE →
READY_FOR_CODEX → EXECUTING → IMPLEMENTED →
EVOLUTIONARY_DEBT → RECONSTRUCTION → LIBRARY

Mientras QUARANTINE_GATE/READY_FOR_CODEX no existan como gates
automáticos, su función la cumple: revisión humana + Ruta C
(documentada en NEXUS_SUPERIOR.md §7 línea 699, archivo físico
LILA_ROUTING_PROMPT.md PENDIENTE DE CREACIÓN) + verificación
contra §3 del Nexus.
```

---

## EVO-TICKET-0001 — Oracle v6 Fase A (Encoding + Observabilidad)

```
ORIGIN          : Operational Anomaly + Epistemic Distillation
                  (cobertura 54.77%, LabelEncoder no-determinista,
                  FEATURE_COLS legacy — issues #1-#4 de §5.1 Nexus)

MATURITY        : MATURITY_3
                  (dirección clara en NEXUS_SUPERIOR.md §5.1,
                  issues #1-#4 identificados con especificación
                  suficiente para diseño. SIN artefactos de
                  implementación ejecutables — los archivos
                  oracle_v6_skeleton.py y test_oracle_v6_skeleton.py
                  referenciados en §5.1 L288-289 del Nexus NUNCA
                  FUERON CREADOS. Verificado: git log --all no
                  registra su existencia. cgalpha_v4/ solo contiene
                  documentos fundacionales S2-S8 + WHITEPAPER.)

VITALITY        : ACTIVE
                  (en progreso, P1 del Nexus, sesión activa)

ESTADO EN CICLO : INCUBATION
                  (no puede ser EXECUTING sin artefactos de código
                  verificables. Prerequisito para avanzar a MATURITY_4:
                  crear oracle_v6_skeleton.py + tests de contrato.)

DEBT CLASS (estimado pre-ejecución) : CONSOLIDATION_DEBT
  Razón: no añade capacidad nueva, consolida una base de código
  con deuda técnica conocida (issues #1-#4 de §5.1 Nexus) hacia
  un estado verificable. La capacidad nueva real es Fase B.

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE (plantilla PENDIENTE DE CREACIÓN —
      RECONSTRUCTION_MAP_UPDATE_TEMPLATE.md no existe, debe crearse
      como parte del scaffolding constitucional)
  [ ] ARCHITECTURAL_DECISION_RECORD por cada decisión con
      alternativas (mínimo esperado: 1, sobre el esquema de
      encoding — ver issue #2 de §5.1)
  [ ] Actualización de §3 (verdades inmutables) si se fija
      algún valor nuevo (ej: ENCODING_MAP)
  [ ] Actualización de §7/§8 del Nexus

REFERENCIA DE BRIEF:
  NEXUS_SUPERIOR.md §5.1 L287 referencia cgalpha_v4/RECONSTRUCTION_BRIEF.md
  como brief existente. VERIFICADO: NO EXISTE. cgalpha_v4/ contiene:
    LILA_V4_PROMPT_FUNDACIONAL.md, S2-S8, WHITEPAPER.md
  El brief debe CREARSE como prerequisito para MATURITY_4+.

CRITERIOS DE ÉXITO : ver §5.1 del Nexus, issues #1-#4
NO TOCAR           : PROTECTED_MODULES de §3 del Nexus
```

---

## EVO-TICKET-0002 — Oracle v6 Fase B (Features dinámicas + walk-forward)

```
ORIGIN          : Human Investigation + Operational Anomaly
                  (limitación central del sistema, §1 Nexus:
                  "el Oracle aprende con features estáticas")

MATURITY        : MATURITY_3
                  (dirección clara — Ring Buffer 30s + walk-forward —
                  pero depende de P3 L2 Ring Buffer y P4
                  DeferredOutcomeMonitor Fase Bridge, aún sin CRB)

VITALITY        : DORMANT
                  (no puede avanzar a INCUBATION plena hasta que
                  P3/P4 tengan CRB — bloqueado por dependencia,
                  no por falta de evidencia)

ESTADO EN CICLO : INCUBATION

DEBT CLASS (estimado) : EXPANSION_DEBT
  Razón: introduce capacidad genuinamente nueva (features
  temporales dinámicas) sobre una base que Fase A habrá
  consolidado.

BLOQUEO ADICIONAL (2026-06-13):
  EVO-TICKET-0003 (WebSocket Pipeline Freeze) bloquea
  indirectamente este ticket: cada día sin cosecha de datos
  retrasa la acumulación de Set A necesaria para Fase B.
  3+ días de pipeline muerto al momento de escribir esto.

PROTOCOLO DE RESURRECCIÓN (Apéndice — obligatorio, no opcional):
  Cuando P3 (L2 Ring Buffer) y P4 (DeferredOutcomeMonitor Fase
  Bridge) tengan CRB completo, este ticket DEBE ser revisado y
  decidido — no archivado sin acción:
    (a) vuelve a INCUBATION con la nueva evidencia de los CRBs, o
    (b) se termina formalmente si las suposiciones de
        §5.1 del Nexus ya no aplican.
  "Permanent abandonment is forbidden."

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE
  [ ] ARCHITECTURAL_DECISION_RECORD: walk-forward vs split estático
  [ ] ARCHITECTURAL_DECISION_RECORD: diseño del Ring Buffer feed
      hacia Oracle (interfaz con P3)

CRITERIOS DE ÉXITO : ver NEXUS_SUPERIOR.md §5.1, issues #5-#6
NO TOCAR           : igual que EVO-TICKET-0001
```

---

## EVO-TICKET-0003 — WebSocket Pipeline Freeze (Anomalía Recurrente)

```
ORIGIN          : Operational Anomaly (confirmada con evidencia de
                  código y tests de red — no solo observación OS-level)

                  Cronología verificada:
                    2026-06-10 06:55 UTC — última escritura en
                      training_dataset_v2.jsonl y pending_labels.json
                    2026-06-10 23:41 UTC — reinicio manual (PID 165833),
                      bootstrap exitoso (7 samples, 64 zonas activas),
                      reconexión WS OK (Epoch 1-4 en log)
                    2026-06-12 00:39 UTC — diagnóstico: proceso vivo,
                      ficheros congelados, aggTrade mudo en Futures
                      (confirmado con script de test: Spot OK, Futures
                      timeout), depth20@100ms fluyendo normalmente
                    2026-06-13 07:55 UTC — segundo reinicio (PID 565679)
                    2026-06-13 23:00 UTC — 15h+ después del reinicio,
                      training_dataset_v2.jsonl SIGUE sin cambios (211
                      líneas, mtime 2026-06-10 06:55). El reinicio NO
                      resolvió el problema.

                  Ficheros congelados confirmados (stat):
                    training_dataset_v2.jsonl — 351166 bytes, mtime 06-10
                    pending_labels.json — 2 bytes ("[]"), mtime 06-10
                    market_price.json — 81 bytes, mtime 06-10 23:32
                    active_zones.json — 13044 bytes, mtime 06-13 07:55
                      (actualizado solo por bootstrap, no por operación)

MATURITY        : MATURITY_4
                  Causa raíz CONFIRMADA con evidencia de código.
                  Fix propuesto y delimitado. Sin implementación todavía.

                  CAUSA RAÍZ CONFIRMADA (H4):
                    live_adapter.py línea 107-111:
                      async def on_ws_message(self, data):
                          event_type = data.get('e')
                          if event_type == 'aggTrade':
                              await self._process_trade(data)

                    on_ws_message() SOLO despacha en 'aggTrade'.
                    Los eventos 'depthUpdate' (depth20@100ms) llegan
                    abundantemente (~10/seg) pero se ignoran para el
                    avance del reloj interno de velas. Cuando el stream
                    aggTrade falla silenciosamente (verificado: la
                    conexión WS sigue ESTABLISHED, Binance sigue
                    distribuyendo depth, pero aggTrade no llega en
                    Futures), _on_candle_close() nunca se invoca →
                    no se evalúan retests → no se etiquetan outcomes
                    → pipeline completamente congelado.

                    Esto explica TODOS los síntomas simultáneamente:
                    - Proceso vivo con conexión ESTABLISHED ✓
                    - Reconexiones exitosas (Epoch 2/3/4) ✓
                    - depth20 fluyendo (OBI actualizándose) ✓
                    - training_dataset sin cambios desde 06-10 ✓
                    - market_price.json congelado ✓
                    - Reinicio no resuelve (bug estructural) ✓

                  HIPÓTESIS PREVIAS (reclasificadas):
                    H1 (aggTrade silenciado por Binance Futures):
                       PARCIALMENTE CONFIRMADA. El stream aggTrade
                       en Futures puede fallar silenciosamente mientras
                       depth20 sigue activo. Verificado con script de
                       test (Spot OK, Futures timeout). Pero H1 es el
                       trigger, no la causa raíz — un sistema resiliente
                       debe avanzar sin aggTrade.
                    H2 (silent disconnect / event loop bloqueado):
                       DESCARTADA. Las reconexiones Epoch 2/3/4
                       demuestran que el event loop siguió vivo.
                    H3 (tarea de escritura bloqueada):
                       DESCARTADA. No hay asyncio.create_task separado
                       para escritura. Todo corre síncrono dentro de
                       _on_candle_close() y _process_trade().

VITALITY        : ACTIVE — EMERGENCY
                  Afecta directamente la acumulación de Set A.
                  3+ días de pipeline muerto. Cada día bloquea
                  EVO-TICKET-0002 indirectamente.

ESTADO EN CICLO : INCUBATION (con fix propuesto, listo para
                  QUARANTINE_GATE → READY_FOR_CODEX)

DEBT CLASS      : EMERGENCY_DEBT
  Razón: causa raíz confirmada, pipeline completamente inerte,
  reinicios no resuelven, datos de entrenamiento no se acumulan.

FIX PROPUESTO (Cat.2 — live_adapter.py NO es PROTECTED_MODULE):
  Añadir heartbeat watchdog en on_ws_message() que use el
  timestamp de depthUpdate para avanzar el reloj de velas cuando
  aggTrade lleve >30s sin aparecer. El fix toca SOLO:
    - live_adapter.py: on_ws_message() + nuevo método _heartbeat()
  NO toca:
    - deferred_outcome_monitor.py (PROTECTED — Cat.3)
    - triple_coincidence.py (PROTECTED — Cat.3)
    - binance_websocket_manager.py (no necesario, BWS ya
      propaga timestamps correctamente)

COMPONENTES AFECTADOS:
  live_adapter.py (NO protegido — Cat.2)
  binance_websocket_manager.py (P3 del Nexus — indirecto, no
    requiere cambios para este fix)

RELACIONADO CON:
  Punto Ciego #3 — architectural_analysis.md (cumulative_delta)
    ESTADO: ✅ IMPLEMENTADO — get_rolling_delta() BWS línea 241,
    ventana 300 segundos. NO es causa de este bug.
  Punto Ciego #4 — architectural_analysis.md (connection_epoch)
    ESTADO: ✅ IMPLEMENTADO — _connection_epoch BWS líneas 54,97,99,
    propagado a L2RingBuffer via mark_reconnection(). NO es causa.
  NUEVO punto ciego identificado por este ticket:
    Single-clock dependency — live_adapter.on_ws_message() depende
    exclusivamente de aggTrade para el avance temporal. depthUpdate
    mantiene viva la conexión TCP pero no avanza el pipeline.

PROTOCOLO DE RESURRECCIÓN (si se STALL sin resolución):
  Este ticket no puede cerrarse como DORMANT sin:
    (a) haber implementado el fix del heartbeat, o
    (b) decidir formalmente que el reinicio manual periódico es
        suficiente y documentarlo como ADR.
  "Permanent abandonment is forbidden."

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE si se modifica código
  [ ] ARCHITECTURAL_DECISION_RECORD: heartbeat watchdog design
      (Cat.2 — live_adapter.py no es módulo protegido, pero
      el ADR es obligatorio por tratarse de cambio en el reloj
      del pipeline)
  [ ] Actualizar §5.7 del Nexus (BWS) añadiendo:
      "Issue #5: Single-clock dependency en live_adapter — RESUELTO"
```

---

## EVO-TICKET-0004 — File Reader (Observabilidad Admin)

```
ORIGIN          : Human Request (Gantry stabilization)
MATURITY        : MATURITY_4
VITALITY        : ACTIVE
ESTADO EN CICLO : EXECUTING
DEBT CLASS      : TECHNICAL_DEBT
CRITERIOS ÉXITO : Endpoint /api/admin/read-file funcional con auth.
```

---

## EVO-TICKET-0005 — Active Zones Stale After Restart (Cleanup + Warm-start)

```
ORIGIN          : Operational Anomaly (GUI showing 2 stale zones at 66.5k-66.0k
                  while BTCUSDT spot ~63.9k; zones persisted across restarts
                  without expiry)

MATURITY        : MATURITY_3
                  (root cause identified and fix implemented:
                   _cleanup_expired_zones used unstable buffer indices;
                   feed_kline_for_zone_detection recalculated ZigZag trends
                   per-candle instead of precomputing;
                   warm_start hydrated buffer but did not replay detection.)

VITALITY        : ACTIVE
                  (fix deployed, awaiting 2-4h observation after restart)

ESTADO EN CICLO : EXECUTING
                  (code changes in triple_coincidence.py, live_adapter.py,
                   gui/server.py; restart pending human approval)

DEBT CLASS      : CALIBRATION_DEBT
                  (new parameter zone_max_distance_atr=5.0 is PROVISIONAL
                   and intentionally uncalibrated — must be replaced with
                   percentile analysis of real expired-vs-active zone
                   distances once enough detection cycles are collected)

CRITERIOS ÉXITO :
  [ ] Tras reinicio, las 2 zonas viejas (66.5k-66.0k) no reaparecen.
  [ ] Si el mercado forma una zona válida, aparece en L2 Forensics
      dentro de ~50 velas (timeout actual).
  [ ] Dataset sigue creciendo (retests detectados y resueltos).

NO TOCAR        : PROTECTED_MODULES de §3 del Nexus
                  (no se modificaron módulos protegidos)

CALIBRATION DEBT:
  - zone_max_distance_atr=5.0 provisional. Método de calibración futuro:
    1. Medir distancia (en ATR) de zonas expiradas vs vigentes durante
       ~500-1000 velas de operación real.
    2. Calcular percentiles (P75/P90) de distancia en el momento de
       expiración por tiempo o por ruptura.
    3. Fijar zone_max_distance_atr = P90_distancia_expiradas + margen.
    4. Documentar en ADR y actualizar este ticket a MATURITY_4.
```

---

## Registro de cierre (se completa al terminar cada ticket)

```
Esta tabla es el resumen humano (snapshot). La secuencia completa
y cronológica de eventos vive en la sección JSONL al final de
este documento.

NOTA: constitutional_events.jsonl como archivo independiente y
CONSTITUTIONAL_EVENT_LEDGER_SPEC.md (citado como D-009 del Nexus)
NO EXISTEN. D-009 no está registrado en §3 del Nexus (último:
D-007). El ledger JSONL se mantiene inline aquí hasta que la
infraestructura constitucional se construya.
```

| Ticket | Fecha cierre | RMU generado | ADRs generados | Debt final | Próximo estado |
|---|---|---|---|---|---|
| EVO-TICKET-0001 | pendiente | pendiente | pendiente | pendiente | pendiente |
| EVO-TICKET-0002 | bloqueado por P3/P4 + EVO-0003 | — | — | — | DORMANT |
| EVO-TICKET-0003 | pendiente | pendiente | pendiente (≥1 ADR) | EMERGENCY_DEBT | pendiente |
| EVO-TICKET-0004 | pendiente | pendiente | pendiente | TECHNICAL_DEBT | pendiente |
| EVO-TICKET-0005 | pendiente | pendiente | pendiente (≥1 ADR) | CALIBRATION_DEBT | pendiente |

---

## Constitutional events · JSONL

```jsonl
{"event":"ticket_created","ticket":"EVO-TICKET-0001","component":"Oracle","maturity":"MATURITY_5","vitality":"ACTIVE","timestamp":"2026-06-12T00:00:00Z"}
{"event":"ticket_state_changed","ticket":"EVO-TICKET-0001","field":"lifecycle_state","from":"READY_FOR_CODEX","to":"EXECUTING","decided_by":"human","timestamp":"2026-06-12T00:00:00Z"}
{"event":"ticket_created","ticket":"EVO-TICKET-0002","component":"Oracle","maturity":"MATURITY_3","vitality":"DORMANT","timestamp":"2026-06-12T00:00:00Z"}
{"event":"ticket_state_changed","ticket":"EVO-TICKET-0002","field":"lifecycle_state","from":"-","to":"INCUBATION","decided_by":"human","timestamp":"2026-06-12T00:00:00Z"}
{"event":"ticket_created","ticket":"EVO-TICKET-0003","component":"binance_websocket_manager","maturity":"MATURITY_2","vitality":"ACTIVE","timestamp":"2026-06-13T00:00:00Z"}
{"event":"ticket_state_changed","ticket":"EVO-TICKET-0003","field":"lifecycle_state","from":"-","to":"INCUBATION","decided_by":"human","timestamp":"2026-06-13T00:00:00Z"}
{"event":"epistemic_distillation","ticket":"EVO-TICKET-0001","field":"maturity","from":"MATURITY_5","to":"MATURITY_3","decided_by":"human","reason":"skeleton + test files cited as evidence NEVER EXISTED (git --all verified). cgalpha_v4/ contains only foundational docs S2-S8.","timestamp":"2026-06-13T21:09:00Z"}
{"event":"ticket_state_changed","ticket":"EVO-TICKET-0001","field":"lifecycle_state","from":"EXECUTING","to":"INCUBATION","decided_by":"human","reason":"cannot be EXECUTING without verifiable code artifacts","timestamp":"2026-06-13T21:09:00Z"}
{"event":"epistemic_distillation","ticket":"EVO-TICKET-0003","field":"maturity","from":"MATURITY_2","to":"MATURITY_4","decided_by":"human","reason":"root cause H4 confirmed via code evidence: on_ws_message() single-clock dependency on aggTrade (live_adapter.py L110). Fix scoped and delimited.","timestamp":"2026-06-13T21:09:00Z"}
{"event":"epistemic_distillation","ticket":"EVO-TICKET-0003","field":"component","from":"binance_websocket_manager","to":"live_adapter","decided_by":"human","reason":"root cause is in live_adapter.on_ws_message() not BWS. BWS correctly delivers both depthUpdate and aggTrade.","timestamp":"2026-06-13T21:09:00Z"}
{"event":"epistemic_distillation","ticket":"EVO-TICKET-0003","field":"debt_class","from":"pending","to":"EMERGENCY_DEBT","decided_by":"human","reason":"3+ days pipeline dead, restart does not fix, blocks Set A accumulation","timestamp":"2026-06-13T21:09:00Z"}
{"event":"phantom_reference_flagged","document":"EVO_TICKET_LOG","references":["RECONSTRUCTION_BRIEF.md","oracle_v6_skeleton.py","test_oracle_v6_skeleton.py","RECONSTRUCTION_MAP_UPDATE_TEMPLATE.md","B008_NEXUS_CAPSULE.md (as standalone file)","LILA_ROUTING_PROMPT.md","constitutional_events.jsonl","CONSTITUTIONAL_EVENT_LEDGER_SPEC.md"],"verdict":"NEVER_EXISTED (git log --all confirms zero commits)","timestamp":"2026-06-13T21:09:00Z"}
{"event":"blind_spot_status_corrected","blind_spot":"#3 cumulative_delta","from":"NOT_IMPLEMENTED","to":"IMPLEMENTED","evidence":"get_rolling_delta() BWS L241, window=300s","timestamp":"2026-06-13T21:09:00Z"}
{"event":"blind_spot_status_corrected","blind_spot":"#4 connection_epoch","from":"NOT_IMPLEMENTED","to":"IMPLEMENTED","evidence":"_connection_epoch BWS L54/L97/L99, mark_reconnection() propagated","timestamp":"2026-06-13T21:09:00Z"}
{"event":"ticket_created","ticket":"EVO-TICKET-0004","component":"server","maturity":"MATURITY_4","vitality":"ACTIVE","timestamp":"2026-06-16T18:45:00Z"}
{"event":"ticket_created","ticket":"EVO-TICKET-0005","component":"triple_coincidence_detector","maturity":"MATURITY_3","vitality":"ACTIVE","timestamp":"2026-06-18T21:35:00Z"}
{"event":"fix_deployed","ticket":"EVO-TICKET-0005","files":["cgalpha_v3/infrastructure/signal_detector/triple_coincidence.py","cgalpha_v3/application/live_adapter.py","cgalpha_v3/gui/server.py"],"decided_by":"human","timestamp":"2026-06-18T21:35:00Z"}
{"event":"calibration_debt_flagged","ticket":"EVO-TICKET-0005","parameter":"zone_max_distance_atr","value":"5.0","status":"PROVISIONAL","reason":"intuition-based placeholder; requires percentile calibration from real detection cycles","timestamp":"2026-06-18T21:35:00Z"}
{"event":"state_preserved","ticket":"EVO-TICKET-0005","action":"detector_state.json and active_zones.json restored from .bak-pre-reset; restart deferred pending human approval","timestamp":"2026-06-18T21:35:00Z"}
```
