/* CGAlpha v3 — Control Room JS
   Usa la misma paleta que la GUI anterior: #1a1a2e / #00d4aa
*/
"use strict";

const API_BASE = window.location.origin;
const POLL_MS = 5000;
const EVENTS_N = 30;
const RISK_INPUT_IDS = [
    "risk-max-dd",
    "risk-max-position",
    "risk-max-signals",
    "risk-min-quality",
];

let authToken = "";
let pollTimer = null;
let libraryItems = [];
let selectedLibrarySourceId = null;
let theorySnapshot = null;
let experimentSnapshot = null;

// ── LOGIN ─────────────────────────────────────────────
function doLogin() {
    const raw = document.getElementById("auth-token").value.trim();
    authToken = raw || "cgalpha-v3-local-dev";

    fetchStatus()
        .then(() => {
            document.getElementById("login-overlay").classList.add("hidden");
            const app = document.getElementById("app");
            app.classList.remove("hidden");
            app.style.display = "flex";
            startPolling();
            renderFooterTs();
        })
        .catch(() => {
            const err = document.getElementById("login-error");
            err.textContent = "Token inválido o servidor no disponible.";
            err.classList.remove("hidden");
        });
}

document.addEventListener("DOMContentLoaded", () => {
    // Modo Acceso Directo v3: no solicita token en local
    authToken = "cgalpha-v3-local-dev";
    startPolling();
    renderFooterTs();
});

// ── API ───────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
    const res = await fetch(API_BASE + path, {
        ...opts,
        headers: {
            "Authorization": `Bearer ${authToken}`,
            "Content-Type": "application/json",
            ...(opts.headers || {}),
        },
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

// ── POLLING ───────────────────────────────────────────
function startPolling() {
    fetchStatus();
    fetchEvents();
    fetchRollbacks();
    fetchLibraryStatus();
    fetchLibrarySources();
    fetchTheoryLive();
    fetchAdaptiveBacklog();
    fetchExperimentStatus();
    fetchLearningMemoryStatus();
    pollTimer = setInterval(() => {
        fetchStatus();
        fetchEvents();
        fetchRollbacks();
        fetchLibraryStatus();
        fetchLibrarySources();
        fetchTheoryLive();
        fetchAdaptiveBacklog();
        fetchExperimentStatus();
        fetchLearningMemoryStatus();
        renderFooterTs();
    }, POLL_MS);
}

async function fetchStatus() {
    const d = await apiFetch("/api/status");
    updateMissionControl(d);
    updateMarketLive(d);
    updateRiskPanel(d);
    updateTopbar(d);
    if (d.library) updateLibraryStatus(d.library);
    if (d.theory_live) updateTheoryLive(d.theory_live);
    if (d.experiment_loop) updateExperimentLoop(d.experiment_loop);
    if (d.learning_memory) updateLearningMemoryStatus(d.learning_memory);
    if (d.regime_shift_active !== undefined) {
        setText("learn-regime-active", d.regime_shift_active ? "SI" : "NO");
    }
    return d;
}

async function fetchEvents() {
    try {
        const events = await apiFetch(`/api/events?limit=${EVENTS_N}`);
        renderEvents(events);
    } catch { /* silencioso */ }
}

// ── MISSION CONTROL ────────────────────────────────────
function updateMissionControl(d) {
    setText("mc-phase", d.phase || "—");
    setText("mc-ks", d.kill_switch_status || "—");
    setText("mc-last-event", d.last_event || "—");
    setText("mc-ts", formatTs(d.server_ts));

    const pill = document.getElementById("mc-status-pill");
    const status = d.system_status || "idle";
    pill.textContent = status;
    pill.className = "pill " + pillClass(status);
}

function pillClass(s) {
    return {
        idle: "pill-idle",
        running: "pill-running",
        degraded: "pill-degraded",
        error: "pill-error",
        "kill-switch-active": "pill-killswitch",
    }[s] || "pill-idle";
}

// ── MARKET LIVE ────────────────────────────────────────
function updateMarketLive(d) {
    const mkt = d.market || {};
    setText("mkt-symbol", mkt.symbol || "—");
    setText("mkt-interval", mkt.interval || "—");
    setText("mkt-price", mkt.price != null ? `$${mkt.price}` : "— (mock)");
    setText("mkt-ts", mkt.ts ? formatTs(mkt.ts) : "—");

    const dq = d.data_quality || "stale";
    const badge = document.getElementById("dq-badge");
    const text = document.getElementById("dq-text");

    const dqCfg = {
        valid: { cls: "pill-idle", label: "✅ valid", txt: "✅ Datos válidos" },
        stale: { cls: "pill-degraded", label: "⚠️ stale", txt: "⚠️ Datos obsoletos" },
        corrupted: { cls: "pill-error", label: "❌ corrupted", txt: "❌ Datos corruptos" },
    };
    const cfg = dqCfg[dq] || dqCfg.stale;
    badge.textContent = cfg.label;
    badge.className = "pill " + cfg.cls;
    setText("dq-text", cfg.txt);
}

// ── RISK PANEL ─────────────────────────────────────────
function updateRiskPanel(d) {
    const dd = d.drawdown_session_pct ?? 0;
    const limit = d.max_drawdown_session_pct ?? 5;
    const pct = Math.min((dd / limit) * 100, 100);
    const cb = d.circuit_breaker || "inactive";

    setText("dd-value", `${dd.toFixed(2)}%`);
    setText("dd-limit", `${limit.toFixed(1)}%`);

    const bar = document.getElementById("dd-bar");
    bar.style.width = `${pct}%`;
    bar.className = "progress-fill" + (pct > 70 ? " danger" : "");

    const cbPill = document.getElementById("cb-pill");
    cbPill.textContent = `CB: ${cb}`;
    cbPill.className = "pill " + (cb === "active" ? "pill-error" : "pill-idle");
    setText("cb-text", cb);

    // Risk section KS
    const ksBig = document.getElementById("ks-status-big");
    if (ksBig) ksBig.textContent = d.kill_switch_status || "—";

    syncRiskInputsFromStatus(d);
}

function syncRiskInputsFromStatus(d) {
    const active = document.activeElement;
    if (active && RISK_INPUT_IDS.includes(active.id)) {
        return;
    }

    setInputValue("risk-max-dd", d.max_drawdown_session_pct);
    setInputValue("risk-max-position", d.max_position_size_pct);
    setInputValue("risk-max-signals", d.max_signals_per_hour);
    setInputValue("risk-min-quality", d.min_signal_quality_score);
}

// ── TOPBAR ─────────────────────────────────────────────
function updateTopbar(d) {
    const dot = document.getElementById("status-dot");
    const txt = document.getElementById("status-text");
    const st = d.system_status || "idle";
    const ks = d.kill_switch_status || "armed";

    const colors = {
        idle: "#00d4aa",
        running: "#00aef0",
        degraded: "#f59e0b",
        error: "#ff6b6b",
        "kill-switch-active": "#ff6b6b",
    };
    dot.style.background = colors[st] || "#777";
    txt.textContent = `${st} · KS: ${ks}`;
}

// ── EVENTS ─────────────────────────────────────────────
function renderEvents(events) {
    const el = document.getElementById("events-list");
    if (!events || !events.length) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Sin eventos aún.</span>';
        return;
    }
    const icons = { info: "ℹ️", warning: "⚠️", critical: "🚨" };
    el.innerHTML = events.map(e => {
        const level = e.level || "info";
        return `<div class="ev-entry ev-${level}">
      <span>${icons[level] || "📋"}</span>
      <span class="ev-text">${escHtml(e.event)}</span>
      <span class="ev-ts">${formatTsShort(e.ts)}</span>
    </div>`;
    }).join("");
}

// ── KILL-SWITCH ────────────────────────────────────────
function killSwitchStep1() {
    apiFetch("/api/kill-switch/arm", { method: "POST" })
        .then(() => document.getElementById("ks-modal").classList.remove("hidden"))
        .catch(err => alert("Error: " + err.message));
}
function closeKsModal() {
    document.getElementById("ks-modal").classList.add("hidden");
}
function killSwitchConfirm() {
    apiFetch("/api/kill-switch/confirm", { method: "POST" })
        .then(() => { closeKsModal(); fetchStatus(); })
        .catch(err => alert("Error: " + err.message));
}
function resetKillSwitch() {
    apiFetch("/api/kill-switch/reset", { method: "POST" })
        .then(() => fetchStatus())
        .catch(err => alert("Error: " + err.message));
}
// ── ROLLBACK ───────────────────────────────────────────
async function fetchRollbacks() {
    try {
        const snaps = await apiFetch("/api/rollback/list");
        renderRollbacks(snaps);
    } catch { /* silencioso */ }
}

function renderRollbacks(snaps) {
    const el = document.getElementById("rollback-list");
    if (!snaps || !snaps.length) {
        el.innerHTML = '<span style="font-size:10px;color:var(--text-muted)">Sin snapshots.</span>';
        return;
    }
    el.innerHTML = snaps.slice(0, 5).map(s => `
    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.02); padding:4px 6px; border-radius:4px; border:1px solid rgba(255,255,255,0.05);">
      <span style="font-size:9px; font-family:monospace; color:var(--text-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:110px;">${s.name}</span>
      <button class="btn btn-ghost" style="padding:2px 6px; font-size:9px; border-color:rgba(0,174,240,0.3); color:var(--accent2)" onclick="doRollback('${s.path.replace(/\\/g, '/')}')">Restaurar</button>
    </div>
  `).join("");
}

async function doRollback(path) {
    if (!confirm("¿Confirmar restauración de snapshot? Se perderán configuraciones actuales.")) return;
    try {
        await apiFetch("/api/rollback/restore", {
            method: "POST",
            body: JSON.stringify({ path })
        });
        fetchStatus();
        alert("Rollback ejecutado con éxito.");
    } catch (e) {
        alert("Error en rollback: " + e.message);
    }
}

// ── LIBRARY ────────────────────────────────────────────
async function fetchLibraryStatus() {
    try {
        const status = await apiFetch("/api/library/status");
        updateLibraryStatus(status);
    } catch { /* silencioso */ }
}

function updateLibraryStatus(status) {
    if (!status) return;
    setText("lib-total", status.total_docs ?? 0);
    const ratio = Number(status.primary_ratio ?? 0);
    setText("lib-primary-ratio", ratio.toFixed(3));
    setText("lib-pending", status.pending_review ?? 0);
    setText("lib-last-ingestion", status.last_ingestion ? formatTs(status.last_ingestion) : "—");

    const counts = status.counts || {};
    setText("lib-count-primary", counts.primary ?? 0);
    setText("lib-count-secondary", counts.secondary ?? 0);
    setText("lib-count-tertiary", counts.tertiary ?? 0);
}

async function fetchLibrarySources() {
    const query = (document.getElementById("lib-query")?.value || "").trim();
    const sourceType = (document.getElementById("lib-type")?.value || "").trim();
    const tags = (document.getElementById("lib-tags")?.value || "").trim();
    const params = new URLSearchParams();
    if (query) params.set("query", query);
    if (sourceType) params.set("source_type", sourceType);
    if (tags) params.set("tags", tags);
    params.set("limit", "100");
    const path = `/api/library/sources?${params.toString()}`;
    try {
        const payload = await apiFetch(path);
        libraryItems = payload.results || [];
        renderLibraryResults(libraryItems);

        if (selectedLibrarySourceId) {
            const found = libraryItems.find(s => s.source_id === selectedLibrarySourceId);
            if (found) renderLibraryDetail(found);
        }
    } catch {
        const el = document.getElementById("lib-results");
        if (el) el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Error cargando biblioteca.</span>';
    }
}

function renderLibraryResults(items) {
    const el = document.getElementById("lib-results");
    if (!el) return;
    if (!items || !items.length) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Sin resultados.</span>';
        return;
    }
    el.innerHTML = items.map((s) => `
      <div class="lib-row" onclick="selectLibrarySource('${escHtml(s.source_id)}')">
        <div class="lib-row-title">${escHtml(s.title)}</div>
        <div class="lib-row-meta">
          <span>${escHtml(s.source_type)}</span>
          <span>${escHtml(String(s.year))}</span>
          <span>${escHtml(s.venue || "unknown")}</span>
          <span>${escHtml(s.source_id)}</span>
        </div>
      </div>
    `).join("");
}

async function selectLibrarySource(sourceId) {
    selectedLibrarySourceId = sourceId;
    const local = libraryItems.find(s => s.source_id === sourceId);
    if (local) {
        renderLibraryDetail(local);
        return;
    }
    try {
        const source = await apiFetch(`/api/library/sources/${encodeURIComponent(sourceId)}`);
        renderLibraryDetail(source);
    } catch {
        renderLibraryDetail(null);
    }
}

function renderLibraryDetail(source) {
    const el = document.getElementById("lib-detail");
    if (!el) return;
    if (!source) {
        el.textContent = "No se pudo cargar detalle de la fuente.";
        return;
    }
    const lines = [
        `ID: ${source.source_id}`,
        `Tipo: ${source.source_type} (EV ${source.ev_level})`,
        `Titulo: ${source.title}`,
        `Autores: ${(source.authors || []).join(", ") || "—"}`,
        `Year/Venue: ${source.year} · ${source.venue || "unknown"}`,
        `Tags: ${(source.tags || []).join(", ") || "—"}`,
        `Duplicate of: ${source.duplicate_of || "—"}`,
        `Ingested at: ${source.ingested_at ? formatTs(source.ingested_at) : "—"}`,
        "",
        `Finding: ${source.relevant_finding || "—"}`,
        `Applicability: ${source.applicability || "—"}`,
        "",
        `Abstract: ${source.abstract || "—"}`,
    ];
    el.textContent = lines.join("\n");
}

function searchLibrary() {
    fetchLibrarySources();
}

function clearLibraryFilters() {
    const q = document.getElementById("lib-query");
    const t = document.getElementById("lib-type");
    const g = document.getElementById("lib-tags");
    if (q) q.value = "";
    if (t) t.value = "";
    if (g) g.value = "";
    fetchLibrarySources();
}

function refreshLibrary() {
    fetchLibraryStatus();
    fetchLibrarySources();
}

// ── THEORY LIVE ─────────────────────────────────────────
async function fetchTheoryLive() {
    try {
        const snapshot = await apiFetch("/api/theory/live");
        updateTheoryLive(snapshot);
    } catch { /* silencioso */ }
}

function updateTheoryLive(snapshot) {
    if (!snapshot) return;
    theorySnapshot = snapshot;
    const lib = snapshot.library || {};
    const backlog = snapshot.backlog || {};
    setText("th-total-docs", lib.total_docs ?? 0);
    setText("th-primary-ratio", Number(lib.primary_ratio ?? 0).toFixed(3));
    setText("th-primary-gap", snapshot.primary_source_gap_open ? "SI" : "NO");
    setText("th-backlog-open", backlog.open ?? 0);
    setText("th-backlog-inprogress", backlog.in_progress ?? 0);
    setText("th-backlog-resolved", backlog.resolved ?? 0);
    renderTheoryRecentSources(snapshot.recent_sources || []);
}

function renderTheoryRecentSources(items) {
    const el = document.getElementById("th-recent-sources");
    if (!el) return;
    if (!items.length) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Sin fuentes recientes.</span>';
        return;
    }
    el.innerHTML = items.map((s) => `
      <div class="lib-row" onclick="selectLibrarySource('${escHtml(s.source_id)}')">
        <div class="lib-row-title">${escHtml(s.title)}</div>
        <div class="lib-row-meta">
          <span>${escHtml(s.source_type)}</span>
          <span>${escHtml(String(s.year))}</span>
          <span>${escHtml(s.source_id)}</span>
        </div>
      </div>
    `).join("");
}

async function validateTheoryClaim() {
    const claim = (document.getElementById("th-claim")?.value || "").trim();
    const sourceIdsRaw = (document.getElementById("th-source-ids")?.value || "").trim();
    const sourceIds = sourceIdsRaw.split(",").map(x => x.trim()).filter(Boolean);
    if (!sourceIds.length) {
        alert("Debes indicar al menos 1 source_id.");
        return;
    }

    try {
        const result = await apiFetch("/api/library/claims/validate", {
            method: "POST",
            body: JSON.stringify({
                claim,
                source_ids: sourceIds,
                auto_backlog: true,
                requested_by: "gui_theory_live",
            }),
        });
        const box = document.getElementById("th-claim-result");
        if (box) {
            box.textContent = [
                `claim_ok: ${result.claim_ok}`,
                `primary_source_gap: ${result.primary_source_gap}`,
                `primary_count: ${result.primary_count}`,
                `sources_total: ${result.sources_total}`,
                `backlog_item_id: ${result.backlog_item_id || "—"}`,
                "",
                result.validation_message || "",
            ].join("\n");
        }
        refreshTheoryLive();
    } catch (e) {
        alert("Error validando claim: " + e.message);
    }
}

async function fetchAdaptiveBacklog() {
    try {
        const payload = await apiFetch("/api/lila/backlog?status=open&limit=20");
        renderAdaptiveBacklog(payload.items || []);
    } catch {
        const el = document.getElementById("th-backlog-list");
        if (el) el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Error cargando backlog.</span>';
    }
}

function renderAdaptiveBacklog(items) {
    const el = document.getElementById("th-backlog-list");
    if (!el) return;
    if (!items.length) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Sin items abiertos.</span>';
        return;
    }
    el.innerHTML = items.map((i) => `
      <div class="lib-row">
        <div class="lib-row-title">${escHtml(i.title)}</div>
        <div class="lib-row-meta">
          <span>${escHtml(i.item_type)}</span>
          <span>prio ${escHtml(String(i.priority_score))}</span>
          <span>I${escHtml(String(i.impact))}/R${escHtml(String(i.risk))}/E${escHtml(String(i.evidence_gap))}</span>
        </div>
        <div style="margin-top:6px; font-size:11px; color:var(--text-dim); line-height:1.4">${escHtml(i.rationale)}</div>
        <div style="margin-top:6px">
          <button class="btn btn-ghost btn-sm" onclick="resolveBacklogItem('${escHtml(i.item_id)}')">Resolver</button>
        </div>
      </div>
    `).join("");
}

async function resolveBacklogItem(itemId) {
    if (!itemId) return;
    try {
        await apiFetch(`/api/lila/backlog/${encodeURIComponent(itemId)}/resolve`, {
            method: "POST",
            body: JSON.stringify({ resolution_note: "Resuelto desde GUI Theory Live" }),
        });
        refreshTheoryLive();
    } catch (e) {
        alert("Error resolviendo backlog: " + e.message);
    }
}

function refreshTheoryLive() {
    fetchTheoryLive();
    fetchAdaptiveBacklog();
}

// ── EXPERIMENT LOOP ───────────────────────────────────
async function fetchExperimentStatus() {
    try {
        const payload = await apiFetch("/api/experiment/status");
        updateExperimentLoop(payload);
    } catch { /* silencioso */ }
}

function updateExperimentLoop(payload) {
    if (!payload) return;
    experimentSnapshot = payload;
    setText("exp-status", payload.status || "idle");
    const proposal = payload.proposal || null;
    const exp = payload.latest_experiment || null;
    setText("exp-proposal-id", proposal ? proposal.proposal_id : "—");
    setText("exp-experiment-id", exp ? exp.experiment_id : "—");
    setText("exp-no-leakage", exp ? String(!!exp.no_leakage_checked) : "—");
    setText("exp-wf-windows", exp ? (exp.walk_forward_windows || []).length : 0);

    const metrics = exp ? (exp.metrics || {}) : {};
    setText("exp-gross", formatNum(metrics.gross_return_pct, 4));
    setText("exp-cost", formatNum(metrics.friction_cost_pct, 4));
    setText("exp-net", formatNum(metrics.net_return_pct, 4));
    setText("exp-sharpe", formatNum(metrics.sharpe_like, 4));
    setText("exp-mdd", formatNum(metrics.max_drawdown_pct, 4));
    setText("exp-trades", formatNum(metrics.trades, 0));
    renderExperimentWindows(exp ? (exp.window_metrics || []) : []);
    renderApproachHistogram(exp ? (exp.approach_type_histogram || {}) : {});
}

function renderExperimentWindows(items) {
    const el = document.getElementById("exp-window-metrics");
    if (!el) return;
    if (!items.length) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Sin resultados aún.</span>';
        return;
    }
    el.innerHTML = items.map((w) => `
      <div class="lib-row">
        <div class="lib-row-title">Window ${escHtml(String(w.window_id))}</div>
        <div class="lib-row-meta">
          <span>gross ${escHtml(formatNum(w.gross_return_pct, 4))}%</span>
          <span>cost ${escHtml(formatNum(w.friction_cost_pct, 4))}%</span>
          <span>net ${escHtml(formatNum(w.net_return_pct, 4))}%</span>
        </div>
        <div class="lib-row-meta">
          <span>sharpe ${escHtml(formatNum(w.sharpe_like, 4))}</span>
          <span>mdd ${escHtml(formatNum(w.max_drawdown_pct, 4))}%</span>
          <span>trades ${escHtml(String(w.trades || 0))}</span>
        </div>
      </div>
    `).join("");
}

function renderApproachHistogram(hist) {
    const el = document.getElementById("exp-approach-hist");
    if (!el) return;
    const entries = Object.entries(hist || {});
    const total = entries.reduce((acc, [, v]) => acc + Number(v || 0), 0);
    setText("exp-approach-total", total);
    if (!entries.length || total === 0) {
        el.innerHTML = '<span style="color:var(--text-muted);font-size:12px">Sin histograma aún.</span>';
        return;
    }
    const maxVal = Math.max(...entries.map(([, v]) => Number(v || 0)), 1);
    el.innerHTML = entries.map(([k, v]) => {
        const n = Number(v || 0);
        const width = Math.max((n / maxVal) * 100, 4);
        return `
      <div style="display:flex; align-items:center; gap:8px; margin-top:4px;">
        <span style="width:90px; font-size:11px; color:var(--text-dim);">${escHtml(k)}</span>
        <div style="flex:1; height:10px; border:1px solid rgba(0,212,170,0.2); border-radius:4px; overflow:hidden;">
          <div style="height:100%; width:${width}%; background:linear-gradient(90deg,var(--accent),var(--accent2));"></div>
        </div>
        <span style="width:30px; text-align:right; font-size:11px;">${escHtml(String(n))}</span>
      </div>
    `;
    }).join("");
}

async function proposeExperiment() {
    const hypothesis = (document.getElementById("exp-hypothesis")?.value || "").trim();
    const approaches = (document.getElementById("exp-approaches")?.value || "").trim();
    if (!hypothesis) {
        alert("La hipótesis es obligatoria.");
        return;
    }
    try {
        await apiFetch("/api/experiment/propose", {
            method: "POST",
            body: JSON.stringify({
                hypothesis,
                approach_types: approaches,
            }),
        });
        const msg = document.getElementById("exp-propose-msg");
        if (msg) {
            msg.classList.remove("hidden");
            setTimeout(() => msg.classList.add("hidden"), 2500);
        }
        fetchExperimentStatus();
    } catch (e) {
        alert("Error generando propuesta: " + e.message);
    }
}

async function runExperiment() {
    try {
        await apiFetch("/api/experiment/run", {
            method: "POST",
            body: JSON.stringify({}),
        });
        fetchExperimentStatus();
    } catch (e) {
        alert("Error ejecutando experimento: " + e.message);
        fetchExperimentStatus();
    }
}

// ── LEARNING MEMORY ───────────────────────────────────
async function fetchLearningMemoryStatus() {
    try {
        const payload = await apiFetch("/api/learning/memory/status");
        updateLearningMemoryStatus(payload);
    } catch { /* silencioso */ }
}

function updateLearningMemoryStatus(payload) {
    if (!payload) return;
    const fields = payload.fields || {};
    setText("learn-field-codigo", fields.codigo ?? 0);
    setText("learn-field-math", fields.math ?? 0);
    setText("learn-field-trading", fields.trading ?? 0);
    setText("learn-field-architect", fields.architect ?? 0);
    setText("learn-field-memory-librarian", fields.memory_librarian ?? 0);

    const levels = payload.levels || {};
    setText("learn-level-0a", levels["0a"] ?? 0);
    setText("learn-level-0b", levels["0b"] ?? 0);
    setText("learn-level-1", levels["1"] ?? 0);
    setText("learn-level-2", levels["2"] ?? 0);
    setText("learn-level-3", levels["3"] ?? 0);
    setText("learn-level-4", levels["4"] ?? 0);
    setText("learn-expiring", payload.expiring_within_24h ?? 0);
    setText("learn-stale", payload.stale_entries ?? 0);
}

async function ingestLearningMemory() {
    const content = (document.getElementById("learn-content")?.value || "").trim();
    const field = (document.getElementById("learn-field")?.value || "memory_librarian").trim();
    if (!content) {
        alert("Debes escribir contenido para memoria.");
        return;
    }
    try {
        await apiFetch("/api/learning/memory/ingest", {
            method: "POST",
            body: JSON.stringify({ content, field, auto_normalize: true }),
        });
        const msg = document.getElementById("learn-msg");
        if (msg) {
            msg.textContent = "✓ Ingesta de memoria OK";
            msg.classList.remove("hidden");
            setTimeout(() => msg.classList.add("hidden"), 2500);
        }
        const input = document.getElementById("learn-content");
        if (input) input.value = "";
        fetchLearningMemoryStatus();
    } catch (e) {
        alert("Error en ingesta learning: " + e.message);
    }
}

async function runLearningRetention() {
    try {
        await apiFetch("/api/learning/memory/retention/run", {
            method: "POST",
            body: JSON.stringify({}),
        });
        const msg = document.getElementById("learn-msg");
        if (msg) {
            msg.textContent = "✓ Retención TTL ejecutada";
            msg.classList.remove("hidden");
            setTimeout(() => msg.classList.add("hidden"), 2500);
        }
        fetchLearningMemoryStatus();
    } catch (e) {
        alert("Error en retención learning: " + e.message);
    }
}

async function runLearningRegimeCheck() {
    const series = [];
    for (let i = 0; i < 22; i += 1) series.push(0.8 + (i * 0.02));
    for (let i = 0; i < 20; i += 1) series.push(3.6 + (i * 0.05));
    try {
        const res = await apiFetch("/api/learning/memory/regime/check", {
            method: "POST",
            body: JSON.stringify({ volatility_series: series }),
        });
        const shift = !!(res.result && res.result.regime_shift);
        const msg = document.getElementById("learn-msg");
        if (msg) {
            msg.textContent = shift ? "✓ Regime shift detectado" : "✓ Sin cambio de régimen";
            msg.classList.remove("hidden");
            setTimeout(() => msg.classList.add("hidden"), 2500);
        }
        setText("learn-regime-active", shift ? "SI" : "NO");
        fetchLearningMemoryStatus();
    } catch (e) {
        alert("Error en regime check: " + e.message);
    }
}

function _libRead(id) {
    return (document.getElementById(id)?.value || "").trim();
}

async function ingestLibrarySource() {
    const payload = {
        title: _libRead("lib-ingest-title"),
        year: parseInt(_libRead("lib-ingest-year"), 10),
        source_type: _libRead("lib-ingest-type") || "primary",
        venue: _libRead("lib-ingest-venue"),
        authors: _libRead("lib-ingest-authors"),
        tags: _libRead("lib-ingest-tags"),
        abstract: _libRead("lib-ingest-abstract"),
        relevant_finding: _libRead("lib-ingest-finding"),
        applicability: _libRead("lib-ingest-applicability"),
    };

    if (!payload.title || !payload.abstract || !Number.isFinite(payload.year)) {
        alert("Title, year y abstract son obligatorios.");
        return;
    }

    try {
        const res = await apiFetch("/api/library/ingest", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        const msg = document.getElementById("lib-ingest-msg");
        if (msg) {
            msg.textContent = res.is_new ? "✓ Fuente ingestada" : "✓ Fuente duplicada detectada";
            msg.classList.remove("hidden");
            setTimeout(() => msg.classList.add("hidden"), 2500);
        }
        selectedLibrarySourceId = res.source?.source_id || null;
        refreshLibrary();
    } catch (e) {
        alert("Error en ingesta: " + e.message);
    }
}

// ── RISK PARAMS ────────────────────────────────────────
function saveRiskParams() {
    const maxDd = parseFloat(document.getElementById("risk-max-dd").value);
    const maxPosition = parseFloat(document.getElementById("risk-max-position").value);
    const maxSignals = parseInt(document.getElementById("risk-max-signals").value, 10);
    const minQuality = parseFloat(document.getElementById("risk-min-quality").value);
    apiFetch("/api/risk/params", {
        method: "POST",
        body: JSON.stringify({
            max_drawdown_session_pct: maxDd,
            max_position_size_pct: maxPosition,
            max_signals_per_hour: maxSignals,
            min_signal_quality_score: minQuality,
        }),
    }).then(() => {
        const msg = document.getElementById("risk-save-msg");
        msg.classList.remove("hidden");
        setTimeout(() => msg.classList.add("hidden"), 2500);
        fetchStatus();
    }).catch(err => alert("Error: " + err.message));
}

// ── NAV ────────────────────────────────────────────────
function showSection(name) {
    document.querySelectorAll(".section").forEach(s => {
        s.classList.remove("active");
    });
    const t = document.getElementById("section-" + name);
    if (t) t.classList.add("active");

    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    const btn = document.querySelector(`.nav-btn[onclick*="'${name}'"]`);
    if (btn) btn.classList.add("active");

    if (name === "library") {
        refreshLibrary();
    }
    if (name === "theory") {
        refreshTheoryLive();
    }
    if (name === "experiment") {
        fetchExperimentStatus();
    }
    if (name === "learning") {
        fetchLearningMemoryStatus();
    }
    if (name === "help") {
        helpSearch('inicio');
    }
}

// ── FOOTER ─────────────────────────────────────────────
function renderFooterTs() {
    const el = document.getElementById("footer-ts");
    if (el) el.textContent = new Date().toLocaleTimeString();
}

// ── UTILS ──────────────────────────────────────────────
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
}
function setInputValue(id, val) {
    const el = document.getElementById(id);
    if (!el || val === undefined || val === null || Number.isNaN(val)) return;
    el.value = String(val);
}
function formatTs(iso) {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleString(); } catch { return iso; }
}
function formatTsShort(iso) {
    if (!iso) return "—";
    try { return new Date(iso).toLocaleTimeString(); } catch { return iso; }
}
function escHtml(s) {
    return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
function formatNum(v, digits = 2) {
    const n = Number(v);
    if (!Number.isFinite(n)) return "0";
    return n.toFixed(digits);
}

// ── LILA ASSISTANT (Advanced) ─────────────────────────
let lilaHistory = JSON.parse(localStorage.getItem("lila_history") || "[]");

function toggleLilaChat() {
    const chat = document.getElementById("lila-chat");
    if (chat.classList.contains("lila-fullscreen")) return; // Prevent collapse if FS
    chat.classList.toggle("lila-collapsed");

    const icon = document.getElementById("lila-toggle-icon");
    icon.textContent = chat.classList.contains("lila-collapsed") ? "▲" : "▼";
}

function toggleLilaFullScreen() {
    const chat = document.getElementById("lila-chat");
    const btn = document.getElementById("lila-fs-btn");
    chat.classList.toggle("lila-fullscreen");
    chat.classList.remove("lila-collapsed");

    // Update SVG icon to exit/enter
    if (chat.classList.contains("lila-fullscreen")) {
        btn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z"/></svg>`;
    } else {
        btn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14"><path fill="currentColor" d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z"/></svg>`;
    }
}

function startNewLilaChat() {
    if (!confirm("Start a new conversation with Lila? Current messages will be saved to history.")) return;

    // Save current to history
    const msgs = document.getElementById("lila-messages");
    if (msgs.children.length > 1) {
        const summary = msgs.children[1].textContent.substring(0, 40) + "...";
        lilaHistory.unshift({
            id: Date.now(),
            date: new Date().toLocaleString(),
            summary: summary,
            html: msgs.innerHTML
        });
        localStorage.setItem("lila_history", JSON.stringify(lilaHistory.slice(0, 10)));
    }

    // Reset UI
    msgs.innerHTML = `<div class="msg lila-msg">Hi. I'm Lila, your v3 audit assistant. New session started. How can I help?</div>`;
}

function toggleLilaHistory() {
    const overlay = document.getElementById("lila-history-overlay");
    overlay.classList.toggle("hidden");
    if (!overlay.classList.contains("hidden")) {
        renderLilaHistory();
    }
}

function renderLilaHistory() {
    const list = document.getElementById("lila-history-list");
    list.innerHTML = lilaHistory.length ? "" : '<div style="color:var(--text-muted); font-size:12px; margin-top:20px; text-align:center;">No history found.</div>';

    lilaHistory.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item";
        div.innerHTML = `<strong>${item.date}</strong><br>${item.summary}`;
        div.onclick = () => {
            document.getElementById("lila-messages").innerHTML = item.html;
            toggleLilaHistory();
        };
        list.appendChild(div);
    });
}

async function sendLilaMessage() {
    const input = document.getElementById("lila-input");
    const text = input.value.trim();
    if (!text) return;

    input.value = "";
    appendChatMessage("user", text);

    // Typing indicator
    const indicator = appendChatMessage("lila typing", "Lila is thinking...");

    try {
        const res = await apiFetch("/api/assistant/chat", {
            method: "POST",
            body: JSON.stringify({ message: text })
        });
        indicator.remove();
        appendChatMessage("lila", res.response);
    } catch (err) {
        indicator.remove();
        appendChatMessage("lila", "Internal Error: Connection to Lila Core V3 failed.");
    }
}

function appendChatMessage(type, text) {
    const container = document.getElementById("lila-messages");
    if (!container) return;
    const div = document.createElement("div");
    div.className = `msg ${type}-msg`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

// ── HELP CENTER DATA ──────────────────────────────────
const HELP_DATA = [
    {
        cat: 'inicio',
        title: 'Inicio Rápido / Mission Control',
        icon: '🚀',
        content: 'El Mission Control es el corazón del sistema. (1) Verifica que la base de datos de mercado esté VÁLIDA. (2) Usa el botón "Re-armar sistema" si hubo un incidente. (3) Monitorea los eventos en tiempo real para detectar anomalías.'
    },
    {
        cat: 'riesgo',
        title: 'Gestión de Riesgos y SLOs',
        icon: '🛡️',
        content: 'El Dashboard de Riesgos monitorea SLOs críticos. Si el Drawdown supera el 5% o hay inconsistencias en los datos, el sistema activará los Circuit Breakers e incluso el Kill-Switch si es necesario.'
    },
    {
        cat: 'lila',
        title: 'Lila Assistant v3.1',
        icon: '🤖',
        content: 'Lila es tu compañera de IA. (1) Puede aprender de la historia del proyecto. (2) Puede auditar experimentos. (3) Usa los botones del encabezado para gestionar el historial de chat o la vista de pantalla completa.'
    },
    {
        cat: 'auditoria',
        title: 'Hardening Progresivo (P3)',
        icon: '📋',
        content: 'CGAlpha v3 ha pasado por auditorías P0 (Risk), P1 (Rollback), P2 (Memory) y P3 (Hardening). Esto garantiza integridad temporal, gates de producción y soporte multi-symbol (BTC/ETH/SOL).'
    },
    {
        cat: 'faq',
        title: 'Preguntas Frecuentes (FAQ)',
        icon: '❓',
        isFaq: true,
        items: [
            { q: '¿Cómo accedo a los experimentos pasados?', a: 'En la pestaña "Experiment Loop" encontrarás el resumen del último experimento. El historial completo reside en la memoria de Lila.' },
            { q: '¿Qué significa el punto verde arriba?', a: 'Significa que la conexión con el servidor Flask está activa y el HealthMonitor está reportando estado HEALTHY.' },
            { q: '¿Cómo restauro el sistema tras un Kill-Switch?', a: 'Haz clic en "Re-armar sistema" en el panel de Mission Control.' },
            { q: '¿El asistente guarda mis conversaciones?', a: 'Sí, todas las sesiones se guardan localmente y puedes consultarlas en la carpeta de historial de Lila.' }
        ]
    }
];

function helpSearch(cat) {
    const btns = document.querySelectorAll('.help-nav-btn');
    btns.forEach(b => {
        b.classList.remove('active');
        if (b.getAttribute('data-cat') === cat) b.classList.add('active');
    });

    renderHelpArticles(HELP_DATA.filter(d => d.cat === cat));
}

function filterHelp() {
    const q = document.getElementById('help-search-input').value.toLowerCase();
    const matches = HELP_DATA.filter(d =>
        d.title.toLowerCase().includes(q) ||
        d.content?.toLowerCase()?.includes(q) ||
        (d.items && d.items.some(f => f.q.toLowerCase().includes(q)))
    );
    renderHelpArticles(matches);
}

function renderHelpArticles(data) {
    const container = document.getElementById('help-articles');
    if (!container) return;
    container.innerHTML = '';

    if (data.length === 0) {
        container.innerHTML = '<div style="color:var(--text-muted)">No se encontraron artículos que coincidan con tu búsqueda.</div>';
        return;
    }

    data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'help-card';

        if (item.isFaq) {
            div.innerHTML = `<h4>${item.icon} ${item.title}</h4>`;
            item.items.forEach(faq => {
                const fdiv = document.createElement('div');
                fdiv.className = 'help-faq-item';
                fdiv.innerHTML = `
                    <div class="help-faq-q" onclick="this.parentElement.classList.toggle('open')">${faq.q} <span>▼</span></div>
                    <div class="help-faq-a">${faq.a}</div>
                `;
                div.appendChild(fdiv);
            });
        } else {
            div.innerHTML = `
                <h4>${item.icon} ${item.title}</h4>
                <p>${item.content}</p>
            `;
        }
        container.appendChild(div);
    });
}
