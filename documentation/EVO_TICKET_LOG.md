# EVO-TICKET LOG — cgAlpha_0.0.1

```
Origen: Apéndice — Constitutional Governance of Evolutionary Debt.
"AlphaLab does not manage tasks. AlphaLab manages precedents.
EVO-TICKETs are precedents."

AlphaLab como cámara completa (QUARANTINE_GATE, READY_FOR_CODEX,
resurrección automática de tickets dormidos) NO EXISTE como
componente — es arquitectura objetivo, igual que el Harness del
Acto VIII (ver B008_NEXUS_CAPSULE.md).

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
(LILA_ROUTING_PROMPT.md) + verificación contra §3 del Nexus.
```

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

MATURITY        : MATURITY_3
                  (dirección clara, bloqueado por P3/P4 sin CRB)

VITALITY        : DORMANT
                  (no puede avanzar hasta que P3/P4 tengan CRB)

ESTADO EN CICLO : INCUBATION

DEBT CLASS (estimado) : EXPANSION_DEBT

PROTOCOLO DE RESURRECCIÓN:
  Cuando P3 (L2 Ring Buffer) y P4 (DeferredOutcomeMonitor) tengan CRB:
    (a) retomar INCUBATION con nueva evidencia, o
    (b) terminar formalmente si suposiciones ya no aplican.
  "Permanent abandonment is forbidden."

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE
  [ ] ADR: walk-forward vs split estático
  [ ] ADR: diseño Ring Buffer feed hacia Oracle (interfaz con P3)
```

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
  [ ] RECONSTRUCTION_MAP_UPDATE — pendiente generación formal
  [ ] Actualizar §3 Nexus: añadir _heartbeat_timeout_ms como
      parámetro protegido (cambios requieren ADR)
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

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] RECONSTRUCTION_MAP_UPDATE
  [ ] ADR-EVO-TICKET-0005-1: cleanup por tiempo+distancia vs índice
      (alternativas: índice estable cross-restart vs timestamp+ATR
      — se eligió la segunda, requiere ADR por afectar componente P5)
  [ ] Iniciar CRB de TripleCoincidenceDetector (P5) — este ticket es
      la primera evidencia real de por qué P5 necesita CRB propio
  [ ] Cuando calibration_pending se resuelva: nuevo EVO-TICKET para
      el valor calibrado de zone_max_distance_atr (no reabrir este)
```

---

## EVO-TICKET-0004 — P6.5 File Reader (G4 building block)

```
ORIGIN          : Human Investigation (sesión 2026-06-14)
                  "una herramienta simple — un endpoint que dado un
                  path relativo devuelve el contenido del archivo"
                  Conexión directa con D-010: habilita LLM Readability
                  Check en tiempo real durante sesiones de chat.

MATURITY        : MATURITY_4
                  Diseño completo + implementación lista en
                  P65_FILE_READER_SPEC.md. Pendiente aplicación
                  en server.py y verificación con pytest.
                  MATURITY_5 = aplicado + tests pasando.

VITALITY        : ACTIVE
ESTADO EN CICLO : READY_FOR_CODEX
                  [Cat.2 — toca server.py, requiere aprobación
                  antes de aplicar. Ruta C.]

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

ENTREGABLES CONSTITUCIONALES REQUERIDOS AL CIERRE:
  [ ] Aplicar código de P65_FILE_READER_SPEC.md en server.py
  [ ] pytest pasa (sintaxis + test manual de los 4 casos del spec)
  [ ] RECONSTRUCTION_MAP_UPDATE (incluyendo LLM Readability Check D-010)
  [ ] Actualizar §5.11 del Nexus con Knowledge Card del File Reader
  [ ] Actualizar §8 del Nexus: P6.5 de "iniciado" a "G4 partial"
```

---

## Registro de cierre (se completa al terminar cada ticket)

```
Estado actual (snapshot). Historia completa en constitutional_events.jsonl.
```

| Ticket | Fecha cierre | RMU | ADRs | Debt final | Estado |
|---|---|---|---|---|---|
| EVO-TICKET-0001 | pendiente | pendiente | pendiente | CONSOLIDATION | READY_FOR_CODEX |
| EVO-TICKET-0002 | bloqueado P3/P4 | — | — | EXPANSION | DORMANT |
| EVO-TICKET-0003 | 2026-06-13 | pendiente formal | ADR-EVO-TICKET-0003-1 ✅ | EMERGENCY | IMPLEMENTED |
| EVO-TICKET-0004 | pendiente | pendiente | pendiente | EXPANSION | READY_FOR_CODEX |
| EVO-TICKET-0005 | pendiente (verif. en curso) | pendiente | pendiente | CONSOLIDATION + calibration_pending | EXECUTING |

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
{"event":"calibration_pending_flagged","ticket":"EVO-TICKET-0005","parameter":"zone_max_distance_atr","value":"5.0","status":"PROVISIONAL","reason":"intuition-based placeholder; requires percentile calibration from real detection cycles","timestamp":"2026-06-18T21:35:00Z"}
{"event":"debt_class_corrected","ticket":"EVO-TICKET-0005","from":"CALIBRATION_DEBT","to":"CONSOLIDATION_DEBT","reason":"CALIBRATION_DEBT is not a canonical debt class per Appendix; use orthogonal calibration_pending flag instead","timestamp":"2026-06-19T20:20:00Z"}
{"event":"state_preserved","ticket":"EVO-TICKET-0005","action":"detector_state.json and active_zones.json restored from .bak-pre-reset; restart deferred pending human approval","timestamp":"2026-06-18T21:35:00Z"}
{"event":"verification_completed","ticket":"EVO-TICKET-0005","method":"git checkout <commit>^ -- files + pytest","result":"2 failed 2 passed identical before/after — pre-existing failures, no regression","timestamp":"2026-06-19T20:25:00Z"}
{"event":"collection_verified","ticket":"EVO-TICKET-0005","method":"pytest --collect-only","result":"4 tests collected, no import errors silencing tests","timestamp":"2026-06-19T20:25:00Z"}
{"event":"post_restart_check","ticket":"EVO-TICKET-0005","active_zones":0,"dataset_total":236,"full_samples":94,"pending_count":0,"criterion_1":"PASSED (stale zones did not reappear)","criterion_2":"NOT_YET_VERIFIABLE (no new zone formed since restart)","timestamp":"2026-06-19T20:30:00Z"}
```
