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
        title: '🚀 Quick Start — Arranque del Sistema',
        icon: '🚀',
        content: `
            <h4 style="color:var(--accent); margin-bottom:10px;">Requisitos</h4>
            <div style="background:var(--bg3); padding:12px; border-radius:8px; font-family:monospace; font-size:12px; margin-bottom:12px;">
# Dependencias mínimas
Python >= 3.11
flask >= 2.3.0

# Opcional para LLM Assistant
openai >= 1.0.0  # si OPENAI_API_KEY configurado
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:10px;">Arranque del servidor</h4>
            <div style="background:var(--bg3); padding:12px; border-radius:8px; font-family:monospace; font-size:12px; margin-bottom:12px;">
# Variables de entorno (opcional)
export CGV3_AUTH_TOKEN="tu-token-seguro-aqui"
export CGV3_HOST="127.0.0.1"
export CGV3_PORT="8080"

# Iniciar servidor
python cgalpha_v3/gui/server.py
            </div>
            
            <div style="background:rgba(0,212,170,0.08); padding:10px; border-radius:8px; border-left:3px solid var(--accent); font-size:12px;">
                <strong>Output esperado:</strong><br>
                <code style="color:var(--accent);">[CGAlpha v3 GUI] Iniciando en http://127.0.0.1:8080</code><br>
                <code style="color:var(--accent);">[CGAlpha v3 GUI] Auth token activo: tu-token...</code><br>
                <code style="color:var(--accent);">[CGAlpha v3 GUI] FASE 0 — Control Room en modo mock</code>
            </div>
        `
    },
    {
        cat: 'inicio',
        title: '🔍 Verificación con curl / httpie',
        icon: '🔍',
        content: `
            <h4 style="color:var(--accent); margin-bottom:10px;">Test de conectividad</h4>
            
            <div style="margin-bottom:16px;">
                <strong style="font-size:11px; color:var(--text-dim);">Con curl:</strong>
                <div style="background:var(--bg3); padding:12px; border-radius:8px; font-family:monospace; font-size:11px; margin-top:6px;">
curl -H "Authorization: Bearer cgalpha-v3-local-dev" \\<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;http://127.0.0.1:8080/api/status | jq .
                </div>
            </div>
            
            <div style="margin-bottom:16px;">
                <strong style="font-size:11px; color:var(--text-dim);">Con httpie:</strong>
                <div style="background:var(--bg3); padding:12px; border-radius:8px; font-family:monospace; font-size:11px; margin-top:6px;">
http :8080/api/status "Authorization: Bearer cgalpha-v3-local-dev"
                </div>
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:10px;">Acceso via navegador</h4>
            <div style="background:var(--bg3); padding:12px; border-radius:8px; font-size:12px;">
                <strong>URL:</strong> <code>http://localhost:8080</code><br>
                <strong>Token default:</strong> <code style="color:var(--accent);">cgalpha-v3-local-dev</code>
            </div>
            
            <div style="margin-top:12px; padding:10px; background:rgba(255,107,107,0.08); border-radius:8px; font-size:11px;">
                <strong style="color:var(--red);">⚠️ PRODUCCIÓN:</strong> Cambiar CGV3_AUTH_TOKEN por valor criptográficamente seguro (mínimo 32 caracteres).
            </div>
        `
    },
    {
        cat: 'inicio',
        title: '🏗️ Arquitectura del Sistema',
        icon: '🏗️',
        content: `
            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; overflow-x:auto; line-height:1.3;">
┌─────────────────────────────────────────┐
│           BROWSER (Frontend)             │
│  index.html │ style.css │ app.js         │
└─────────────────────────────────────────┘
                    │ HTTP/WS
                    ▼
┌─────────────────────────────────────────┐
│         SERVER.PY (Flask)                │
│  ┌──────────┐ ┌────────┐ ┌──────────┐   │
│  │Auth Layer│ │Routes  │ │Serialize │   │
│  └──────────┘ └────────┘ └──────────┘   │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           DOMAIN LAYER                   │
│  Signal │ Proposal │ MemoryEntry         │
│  ApproachType │ MemoryLevel             │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         APPLICATION LAYER                │
│  RollbackManager │ ExperimentRunner      │
│  ChangeProposer │ PromotionValidator     │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           SUBSYSTEMS                     │
│  Lila Library │ MemoryPolicyEngine       │
│  ProjectHistoryLearner                   │
└─────────────────────────────────────────┘
            </pre>
        `
    },
    {
        cat: 'inicio',
        title: '📊 Flujo de Datos Principal',
        icon: '📊',
        content: `
            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; overflow-x:auto; line-height:1.4;">
Usuario ──► GUI ──► API Endpoint ──► Manager/Service
                │
                ▼
          _record_control_cycle()
                │
                ├──► _log_event() ──► _events_log[]
                ├──► _persist_iteration_artifacts()
                │    └──► memory/iterations/
                ├──► _capture_memory_librarian_event()
                ├──► _register_incident()
                │    └──► docs/post_mortems/
                └──► _register_adr()
                     └──► docs/adr/
            </pre>
            
            <p style="margin-top:12px; font-size:12px; color:var(--text-dim);">
                Cada acción de control ejecutada via GUI dispara <code>_record_control_cycle()</code> 
                para garantizar trazabilidad automática.
            </p>
        `
    },
    {
        cat: 'riesgo',
        title: 'Gestión de Riesgos (Kill-Switch y Circuit Breakers)',
        icon: '🛡️',
        content: `
            <p>En esta fase de control, el sistema implementa protecciones mediante <strong>Kill-Switch</strong> (apagado controlado) y <strong>Circuit Breaker</strong> (pausa automática ante anomalías).</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                <div style="background:rgba(255,107,107,0.05); padding:8px; border-radius:8px; border:1px solid rgba(255,107,107,0.2);">
                    <strong style="color:var(--red); font-size:11px;">CIRCUIT BREAKERS</strong>
                    <p style="font-size:11px; margin-top:4px;">Se activan si el drawdown de sesión supera el límite configurado (por defecto 5%) o si la calidad de datos es inválida. Bloquea generación de nuevas señales.</p>
                </div>
                <div style="background:rgba(0,212,170,0.05); padding:8px; border-radius:8px; border:1px solid rgba(0,212,170,0.2);">
                    <strong style="color:var(--accent); font-size:11px;">KILL-SWITCH</strong>
                    <p style="font-size:11px; margin-top:4px;">Protocolo de dos pasos (armar + confirmar) que detiene operación inmediatamente. Se reactiva manualmente desde la GUI o vía API sin reiniciar el servidor.</p>
                </div>
            </div>
            <p style="margin-top:10px; font-size:12px;"><strong>SLO actual (mock):</strong> Se monitorea calidad de datos por polling REST (cada 5s). Si data_quality cae a "stale", el sistema marca el estado como degradado y registra incidente.</p>
        `
    },
    {
        cat: 'riesgo',
        title: 'Parámetros de Riesgo (Globales)',
        icon: '📉',
        content: `
            <p>En la fase actual, los parámetros de riesgo son <strong>globales</strong> (aplican a todas las operaciones). Se configuran desde el panel <em>Risk Management</em> o vía API <code>/api/risk/params</code>.</p>
            <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Parámetro</th>
                        <th style="padding:6px;">Default</th>
                        <th style="padding:6px;">Descripción</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">Max Drawdown Sesión</td>
                        <td style="padding:6px; color:var(--accent);">5.0%</td>
                        <td style="padding:6px;">Si supera este valor se activa Circuit Breaker</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">Max Position Size</td>
                        <td style="padding:6px;">2.0%</td>
                        <td style="padding:6px;">Límite de exposición por señal</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">Max Signals/Hora</td>
                        <td style="padding:6px;">10</td>
                        <td style="padding:6px;">Frecuencia máxima de señales</td>
                    </tr>
                    <tr>
                        <td style="padding:6px;">Min Signal Quality</td>
                        <td style="padding:6px;">0.65</td>
                        <td style="padding:6px;">Score mínimo para aceptar señal (0–1)</td>
                    </tr>
                </tbody>
            </table>
            <p style="margin-top:10px; font-size:11px; color:var(--text-dim);">Los cambios aplican inmediatamente vía API; no requieren reinicio.</p>
        `
    },
    {
        cat: 'riesgo',
        title: 'Drawdown y Exposición (FASE 0)',
        icon: '📊',
        content: `
            <p>En la fase actual se monitorean métricas básicas de riesgo (simuladas/mock):</p>
            <ul style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Drawdown de sesión:</strong> Caída desde el pico de capital inicial de la sesión. Dispara Circuit Breaker si supera el límite configurado.</li>
                <li><strong>Exposición por señal:</strong> Controlada por <em>Max Position Size</em> (% del capital por operación).</li>
                <li><strong>Frecuencia:</strong> Limitada por <em>Max Signals/Hora</em> para evitar sobre-trading.</li>
                <li><strong>Calidad mínima:</strong> Señales deben superar <em>Min Signal Quality Score</em> (0–1).</li>
            </ul>
            <div style="margin-top:12px; padding:10px; background:rgba(255,107,107,0.08); border-radius:8px; font-size:11px;">
                <strong style="color:var(--red);">⚠️ Alcance FASE 0:</strong> Las métricas de riesgo avanzadas (Greeks, correlación de cartera, drawdown histórico real) se habilitarán en fases posteriores con conexión a datos de mercado reales.
            </div>
        `
    },
    {
        cat: 'lila',
        title: 'Lila: Motor de Memoria y Validación',
        icon: '🤖',
        content: `
            <p>Lila es el componente de <strong>gobierno del conocimiento</strong> que gestiona la Library y el ciclo de vida de la memoria:</p>
            <ul style="margin-left:20px; margin-top:8px; font-size:13px; color:var(--text-dim);">
                <li><strong>Library Manager:</strong> Valida ingestion de fuentes, detecta duplicados, y gestiona contradicciones entre papers.</li>
                <li><strong>Validación de Claims:</strong> Verifica que hipótesis tengan soporte en fuentes primary (ev_level=1) antes de permitir experimentos.</li>
                <li><strong>Memory Policy:</strong> Gestiona TTL (time-to-live) de entradas de memoria y detecta regime shifts que requieren degradar conocimiento obsoleto.</li>
            </ul>
            <p style="margin-top:10px; font-size:12px; color:var(--text-dim);">En FASE 0, Lila opera como orquestador de validaciones, no como asistente conversacional automatizado. Las interacciones son vía API y formularios de la GUI.</p>
        `
    },
    {
        cat: 'lila',
        title: 'Comandos de Lila',
        icon: '⌨️',
        content: `
            <p>Lila acepta los siguientes comandos en el chat:</p>
            <div style="margin-top:10px; display:flex; flex-direction:column; gap:6px; font-size:12px;">
                <div style="background:var(--bg3); padding:8px; border-radius:6px;">
                    <code style="color:var(--accent);">/status</code> - Reporte completo de SLOs y estado del sistema
                </div>
                <div style="background:var(--bg3); padding:8px; border-radius:6px;">
                    <code style="color:var(--accent);">/risk</code> - Resumen de exposición y métricas de riesgo
                </div>
                <div style="background:var(--bg3); padding:8px; border-radius:6px;">
                    <code style="color:var(--accent);">/experiments</code> - Lista de experimentos activos y sus métricas
                </div>
                <div style="background:var(--bg3); padding:8px; border-radius:6px;">
                    <code style="color:var(--accent);">/memory</code> - Historial de decisiones y aprendizajes
                </div>
                <div style="background:var(--bg3); padding:8px; border-radius:6px;">
                    <code style="color:var(--accent);">/regime</code> - Análisis del régimen de mercado actual
                </div>
                <div style="background:var(--bg3); padding:8px; border-radius:6px;">
                    <code style="color:var(--accent);">/help</code> - Muestra esta guía de comandos
                </div>
            </div>
        `
    },
    {
        cat: 'lila',
        title: 'Change Proposer (Propuestas de Mejora)',
        icon: '🔄',
        content: `
            <p>El módulo <strong>Change Proposer</strong> analiza el estado del sistema y sugiere ajustes cuando detecta anomalías:</p>
            <ol style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Anomaly Detection:</strong> Detecta desviaciones en métricas (drawdown alto, calidad de datos baja, etc.).</li>
                <li><strong>Historical Pattern Matching:</strong> Compara situación actual con incidentes previos registrados en memoria.</li>
                <li><strong>Sugerencias:</strong> Propone ajustes de parámetros de riesgo o revisión de hipótesis.</li>
            </ol>
            <p style="margin-top:10px; font-size:11px;">Cada propuesta incluye: justificación, datos de soporte, y requiere aprobación humana explícita para aplicarse. No hay ejecución automática de cambios.</p>
        `
    },
    {
        cat: 'lila',
        title: 'Auditoría y Trazabilidad',
        icon: '📋',
        content: `
            <p>El sistema mantiene registro completo de decisiones para auditoría:</p>
            <ul style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Traceability:</strong> Cada acción de control genera entradas en <code>memory/iterations/</code> con timestamp y parámetros.</li>
                <li><strong>Event Log:</strong> Últimos 200 eventos en memoria (info/warning/critical) visibles en Dashboard y vía <code>/api/events</code>.</li>
                <li><strong>Incident Registry:</strong> Errores y anomalías se registran automáticamente con severity y contexto.</li>
                <li><strong>ADR Registry:</strong> Decisiones arquitectónicas importantes se documentan en <code>docs/adr/</code>.</li>
            </ul>
            <p style="margin-top:10px; font-size:11px; color:var(--text-dim);">Nota: En FASE 0 los logs se mantienen en memoria y se persisten en snapshots. La exportación a CSV/PDF y almacenamiento a largo plazo están planificados para fases posteriores.</p>
        `
    },
    {
        cat: 'doc',
        title: '📡 API Reference — Endpoints Críticos',
        icon: '📡',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">Sistema y Estado</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET /api/status          → Snapshot completo del sistema<br>
GET /api/events?limit=N  → Últimos N eventos
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Kill-Switch (2-pasos)</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
POST /api/kill-switch/arm     → Paso 1: Solicitar activación<br>
POST /api/kill-switch/confirm → Paso 2: Confirmar<br>
POST /api/kill-switch/reset   → Re-armar
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Rollback</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET  /api/rollback/list    → Snapshots disponibles<br>
POST /api/rollback/restore → Restaurar (body: {"path": "..."})
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Library (Lila)</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET  /api/library/status              → Estado biblioteca<br>
GET  /api/library/sources?query=...   → Búsqueda<br>
POST /api/library/ingest              → Ingestar fuente<br>
POST /api/library/claims/validate     → Validar claim
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Experiment Loop</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px;">
GET  /api/experiment/status   → Estado del loop<br>
POST /api/experiment/propose  → Crear propuesta<br>
POST /api/experiment/run      → Ejecutar (walk-forward ≥3 ventanas)
            </div>
        `
    },
    {
        cat: 'doc',
        title: '📡 API Reference — Memory & Learning',
        icon: '🧠',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">Learning & Memory</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET  /api/learning/memory/status         → Snapshot motor memoria<br>
GET  /api/learning/memory/entries        → Lista entradas<br>
POST /api/learning/memory/ingest         → Ingestar entrada<br>
POST /api/learning/memory/promote       → Promover nivel<br>
POST /api/learning/memory/retention/run → Ejecutar retención TTL<br>
POST /api/learning/memory/regime/check  → Detectar cambio régimen
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Risk Parameters</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET  /api/risk/params → Leer parámetros actuales<br>
POST /api/risk/params → Actualizar (body: {"max_drawdown_session_pct": 4.0})
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">LLM Assistant</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px;">
POST /api/assistant/chat       → Chat con Lila<br>
POST /api/learning/ingest/history → Ingesta iteraciones/ADRs
            </div>
        `
    },
    {
        cat: 'doc',
        title: '🏷️ Modelos de Dominio — ApproachType',
        icon: '🏷️',
        content: `
            <p style="margin-bottom:10px;">Taxonomía de acercamientos a zona de precio:</p>
            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Valor</th>
                        <th style="padding:6px;">Descripción</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">TOUCH</td>
                        <td style="padding:6px;">Precio alcanza zona sin cierre beyond</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">RETEST</td>
                        <td style="padding:6px;">Regresa tras haber cerrado fuera</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">REJECTION</td>
                        <td style="padding:6px;">Mecha opuesta >60% del rango</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">BREAKOUT</td>
                        <td style="padding:6px;">Cierre confirmado beyond zona</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">OVERSHOOT</td>
                        <td style="padding:6px;">Cierre beyond zona sin retorno en N velas</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">FAKE_BREAK</td>
                        <td style="padding:6px;">Cierre beyond zona con retorno en N velas</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'doc',
        title: '📊 Modelos de Dominio — MemoryLevel',
        icon: '📊',
        content: `
            <p style="margin-bottom:10px;">Jerarquía de memoria con TTL y aprobadores:</p>
            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Nivel</th>
                        <th style="padding:6px;">Código</th>
                        <th style="padding:6px;">TTL</th>
                        <th style="padding:6px;">Aprobador</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">RAW</td>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">0a</td>
                        <td style="padding:6px;">24h</td>
                        <td style="padding:6px;">Automático</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">NORMALIZED</td>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">0b</td>
                        <td style="padding:6px;">7d</td>
                        <td style="padding:6px;">Automático</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">FACTS</td>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">1</td>
                        <td style="padding:6px;">30d</td>
                        <td style="padding:6px;">Lila</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">RELATIONS</td>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">2</td>
                        <td style="padding:6px;">90d</td>
                        <td style="padding:6px;">Lila</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">PLAYBOOKS</td>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">3</td>
                        <td style="padding:6px;">∞</td>
                        <td style="padding:6px;">Humano</td>
                    </tr>
                    <tr>
                        <td style="padding:6px;">STRATEGY</td>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">4</td>
                        <td style="padding:6px;">∞</td>
                        <td style="padding:6px;">Humano</td>
                    </tr>
                </tbody>
            </table>
            <p style="margin-top:10px; font-size:11px; color:var(--text-dim);">
                Promoción a STRATEGY requiere experimento validado con <code>sharpe_like > 1.5</code>
            </p>
        `
    },
    {
        cat: 'doc',
        title: '📚 Modelos de Dominio — SourceType',
        icon: '📚',
        content: `
            <p style="margin-bottom:10px;">Clasificación de fuentes de conocimiento:</p>
            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Tipo</th>
                        <th style="padding:6px;">ev_level</th>
                        <th style="padding:6px;">Requisitos</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">primary</td>
                        <td style="padding:6px;">1</td>
                        <td style="padding:6px;">Peer-reviewed, venue reconocido</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">secondary</td>
                        <td style="padding:6px;">2</td>
                        <td style="padding:6px;">Blogs, docs técnicas, whitepapers</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">tertiary</td>
                        <td style="padding:6px;">3</td>
                        <td style="padding:6px;">Social media, foros, opiniones</td>
                    </tr>
                </tbody>
            </table>
            
            <h4 style="color:var(--accent); margin:12px 0 8px 0;">Venues primarios reconocidos</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-size:10px; font-family:monospace;">
acl, nips, neurips, icml, jof, journal_of_finance,<br>
journal_of_financial_economics, review_of_financial_studies,<br>
management_science, quantitative_finance
            </div>
        `
    },
    {
        cat: 'doc',
        title: 'Arquitectura de Ejecución (Futuro)',
        icon: '⚡',
        content: `
            <p>Esta sección describe la <strong>arquitectura objetivo</strong> para fases posteriores de CGAlpha (ejecución de alta frecuencia):</p>
            <div style="margin-top:10px; display:flex; flex-direction:column; gap:8px;">
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:4px solid var(--accent2);">
                    <strong>1. VWAP Engine:</strong> Calcula barreras dinámicas usando buffer de ticks. Detecta breakouts estadísticos.
                </div>
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:4px solid var(--accent);">
                    <strong>2. OBI (Order Book Imbalance):</strong> Analiza presión compra/venta en niveles superiores del libro.
                </div>
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:4px solid var(--red);">
                    <strong>3. Cumulative Delta:</strong> Monitorea volumen ejecutado para detectar reversiones tempranas.
                </div>
            </div>
            <p style="margin-top:12px; font-size:11px; color:var(--text-dim);">Nota: Esta arquitectura requiere conexión WebSocket a exchanges y está planificada para fases posteriores. FASE 0 opera en modo polling REST con datos mock.</p>
        `
    },
    {
        cat: 'doc',
        title: 'Gestión de Memoria y Teoría Live',
        icon: '🧠',
        content: `
            <p>El sistema "Theory Live" permite validar hipótesis contra la biblioteca de documentos científicos (Library).</p>
            <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:12px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:4px;">Nivel</th>
                        <th style="padding:4px;">Tipo de Dato</th>
                        <th style="padding:4px;">Uso</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="color:var(--accent); padding:4px;">L0</td>
                        <td style="padding:4px;">Logs brutos</td>
                        <td style="padding:4px;">Debug inmediato</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="color:var(--accent); padding:4px;">L1-L2</td>
                        <td style="padding:4px;">Evidencias</td>
                        <td style="padding:4px;">Auditoría de señales</td>
                    </tr>
                    <tr>
                        <td style="color:var(--accent); padding:4px;">L3-L4</td>
                        <td style="padding:4px;">Estrategia</td>
                        <td style="padding:4px;">Refinamiento de Lila</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'doc',
        title: 'Biblioteca de Estrategias',
        icon: '📚',
        content: `
            <p>La Library contiene estrategias categorizadas y versionadas:</p>
            <div style="margin-top:10px; display:flex; flex-direction:column; gap:8px; font-size:12px;">
                <div><strong style="color:var(--accent2);">📈 Trend Following:</strong> Media móvil, MACD, RSI-Stoch combo</div>
                <div><strong style="color:var(--accent);">🎯 Mean Reversion:</strong> Bollinger Bands, Z-Score, pairs trading</div>
                <div><strong style="color:var(--purple);">⚡ Arbitrage:</strong> Cross-exchange, triangular, funding rate</div>
                <div><strong style="color:var(--red);">🛡️ Market Making:</strong> Spread capture, inventory management</div>
            </div>
            <p style="margin-top:10px; font-size:11px; color:var(--text-dim);">Cada estrategia incluye: código fuente, backtest results, notes de uso, y compatibilidad con símbolos.</p>
        `
    },
    {
        cat: 'doc',
        title: 'Experiment Loop y Validación',
        icon: '🧪',
        content: `
            <p>El pipeline de experimentos valida hipótesis antes de promover a estrategia de producción:</p>
            <ol style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Proposal:</strong> Definir hipótesis, approach_types y justificación científica.</li>
                <li><strong>Backtest (Walk-Forward):</strong> Validación temporal con ≥3 ventanas (in-sample + out-of-sample). Bloquea automáticamente si detecta temporal leakage.</li>
                <li><strong>Evaluación:</strong> Métricas calculadas: Sharpe, Sortino, Max Drawdown, Win Rate.</li>
                <li><strong>Hardening (P3):</strong> Revisión final antes de permitir promoción a STRATEGY.</li>
                <li><strong>Promoción:</strong> Requiere sharpe_like > 1.5 + aprobación humana para alcanzar MemoryLevel.STRATEGY.</li>
            </ol>
            <div style="margin-top:10px; padding:8px; background:rgba(0,212,170,0.05); border-radius:6px; font-size:11px;">
                <strong>Nota:</strong> El Experiment Loop actual ejecuta en foreground (síncrono). La GUI muestra progreso y resultado final.
            </div>
        `
    },
    {
        cat: 'doc',
        title: 'Métricas de Performance',
        icon: '📊',
        content: `
            <p>El sistema calcula y muestra las siguientes métricas:</p>
            <table style="width:100%; border-collapse:collapse; margin-top:10px; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border);">
                        <th style="padding:4px; text-align:left;">Métrica</th>
                        <th style="padding:4px; text-align:left;">Descripción</th>
                        <th style="padding:4px; text-align:left;">Target</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Sharpe Ratio</td>
                        <td style="padding:4px;">Retorno ajustado por volatilidad</td>
                        <td style="padding:4px; color:var(--accent);">> 2.0</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Sortino Ratio</td>
                        <td style="padding:4px;">Sharpe considerando downside</td>
                        <td style="padding:4px; color:var(--accent);">> 2.5</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Max Drawdown</td>
                        <td style="padding:4px;">Pérdida máxima desde pico</td>
                        <td style="padding:4px; color:var(--red);">&lt; 10%</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Calmar Ratio</td>
                        <td style="padding:4px;">Return / Max DD anualizado</td>
                        <td style="padding:4px; color:var(--accent);">> 2.0</td>
                    </tr>
                    <tr>
                        <td style="padding:4px;">Win Rate</td>
                        <td style="padding:4px;">% trades rentables</td>
                        <td style="padding:4px; color:var(--accent);">> 55%</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'auditoria',
        title: 'Protocolo de Hardening P3',
        icon: '🔒',
        content: `
            <p>La Fase P3 representa el estado de "Producción Endurecida". Incluye:</p>
            <ul style="margin-left:20px; margin-top:8px; font-size:13px; color:var(--text-dim);">
                <li><strong>No-Leakage E2E:</strong> Pruebas que garantizan que el sistema no conoce el futuro durante el backtesting.</li>
                <li><strong>Rollback Atómico:</strong> Capacidad de volver a un estado estable (Snapshot) en &lt;2 segundos si se detecta deriva de métricas.</li>
                <li><strong>Change Proposer:</strong> Todas las modificaciones al código son propuestas por Lila y deben ser validadas por el pipeline de tests automáticos.</li>
            </ul>
        `
    },
    {
        cat: 'auditoria',
        title: 'Logs y Debugging',
        icon: '📝',
        content: `
            <p>Sistema de logging multinivel:</p>
            <ul style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong style="color:var(--red);">ERROR:</strong> Fallos críticos que requieren acción inmediata</li>
                <li><strong style="color:orange;">WARN:</strong> Anomalías que no bloquean pero deben investigarse</li>
                <li><strong style="color:var(--accent);">INFO:</strong> Eventos normales del sistema</li>
                <li><strong>DEBUG:</strong> Detalle técnico para troubleshooting</li>
            </ul>
            <p style="margin-top:10px; font-size:11px;">Filtre logs por: símbolo, nivel, timestamp, o módulo. Exporte a archivo para análisis offline.</p>
        `
    },
    {
        cat: 'auditoria',
        title: 'Rollback y Recovery',
        icon: '↩️',
        content: `
            <p>El sistema mantiene snapshots para recovery:</p>
            <ol style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Auto-snapshot:</strong> Cada 10 minutos o antes de cambios significativos</li>
                <li><strong>Manual snapshot:</strong> Antes de updates mayores</li>
                <li><strong>Restore:</strong> Seleccione snapshot y confirme - sistema reinicia en ~30s</li>
                <li><strong>Diff:</strong> Compare dos snapshots para ver qué cambió</li>
            </ol>
            <div style="margin-top:10px; padding:8px; background:rgba(255,107,107,0.08); border-radius:6px; font-size:11px;">
                <strong style="color:var(--red);">⚠️ Importante:</strong> El restore solo afecta la config/estrategias. Las posiciones reales deben cerrarse manualmente.
            </div>
        `
    },
    {
        cat: 'auditoria',
        title: '⚠️ Troubleshooting — Errores Comunes',
        icon: '⚠️',
        content: `
            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Error</th>
                        <th style="padding:6px;">Causa</th>
                        <th style="padding:6px;">Solución</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">Unauthorized</td>
                        <td style="padding:6px;">Token faltante o incorrecto</td>
                        <td style="padding:6px;">Agregar header <code>Authorization: Bearer &lt;token&gt;</code></td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">temporal_leakage</td>
                        <td style="padding:6px;">Feature timestamp > OOS start</td>
                        <td style="padding:6px;">Verificar timestamps en datos de entrada</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">production_gate_rejected</td>
                        <td style="padding:6px;">Promoción sin validación</td>
                        <td style="padding:6px;">Ejecutar experimento con sharpe > 1.5</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">primary_source_gap</td>
                        <td style="padding:6px;">Claim sin fuente primaria</td>
                        <td style="padding:6px;">Ingestar fuente con source_type=primary</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">invalid_approach_type</td>
                        <td style="padding:6px;">Valor no en taxonomía</td>
                        <td style="padding:6px;">Usar TOUCH|RETEST|REJECTION|BREAKOUT|OVERSHOOT|FAKE_BREAK</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">insufficient_windows</td>
                        <td style="padding:6px;">Walk-forward < 3 ventanas</td>
                        <td style="padding:6px;">Proporcionar más datos históricos</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; color:var(--red); font-family:monospace;">regime_shift_detected</td>
                        <td style="padding:6px;">Volatilidad > 2σ del baseline</td>
                        <td style="padding:6px;">Revisar parámetros o degradar memoria</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'auditoria',
        title: '🔒 Producción — Consideraciones de Seguridad',
        icon: '🔒',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">Token de autenticación</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
# Generar token seguro (32+ caracteres)
export CGV3_AUTH_TOKEN="$(openssl rand -hex 32)"
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Reverse Proxy (nginx)</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-size:11px; margin-bottom:12px;">
server {<br>
&nbsp;&nbsp;listen 443 ssl;<br>
&nbsp;&nbsp;server_name control.tudominio.com;<br>
&nbsp;&nbsp;ssl_certificate /path/to/cert.pem;<br>
&nbsp;&nbsp;ssl_certificate_key /path/to/key.pem;<br>
<br>
&nbsp;&nbsp;location / {<br>
&nbsp;&nbsp;&nbsp;&nbsp;proxy_pass http://127.0.0.1:8080;<br>
&nbsp;&nbsp;&nbsp;&nbsp;proxy_set_header Host $host;<br>
&nbsp;&nbsp;}<br>
}
            </div>
            
            <h4 style="color:var(--accent); margin-bottom:8px;">Health Checks</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-size:11px;">
GET /api/status → Monitorear system_status, data_quality<br>
GET /api/events → Alertar si hay eventos con severity=critical
            </div>
        `
    },
    {
        cat: 'faq',
        title: 'Preguntas Frecuentes (FAQ)',
        icon: '❓',
        isFaq: true,
        items: [
            { q: '¿Qué es el Temporal Leakage?', a: 'Es un error común donde el algoritmo usa datos del futuro (inconscientemente) para entrenarse. CGAlpha tiene gates matemáticos que bloquean cualquier experimento con leakage detectado (error: temporal_leakage).' },
            { q: '¿Por qué el Kill-Switch está armado por defecto?', a: 'Es un protocolo de seguridad operativa. Al arrancar, el sistema debe estar en estado “armed” para poder detenerse inmediatamente ante una anomalía detectada por Risk Dashboard.' },
            { q: '¿Cómo añado nuevos papers a la Library?', a: 'Ve a la pestaña Library, rellena el formulario de Ingesta (título, autores, venue, abstract, etc.) y haz clic en “Ingestar”. Si el venue está en la lista de primarios (ACL, NeurIPS, JOF, etc.), se clasificará automáticamente como primary.' },
            { q: '¿Qué significa "Regime Shift Detected"?', a: 'El MemoryPolicyEngine detectó que la volatilidad actual supera 2 desviaciones estándar del baseline. Esto puede degradar automáticamente entradas de memoria de nivel alto (PLAYBOOKS/STRATEGY) a nivel más bajo para evitar decisiones obsoletas.' },
            { q: '¿Puedo operar en modo live con dinero real?', a: 'No en FASE 0. La GUI actual es “Control Room” con datos mock (precios simulados). La fase actual sirve para validar lógica de riesgo, Library y Memory antes de conectar exchanges reales.' },
            { q: '¿Cómo funciona el Experiment Loop?', a: 'Crea una Proposal (hipótesis + approach_types), ejecútala con “Run Experiment”. El sistema hará walk-forward validation (≥3 ventanas) y calculará métricas (sharpe, sortino, max_dd). Solo con sharpe > 1.5 y aprobación humana se puede promover a STRATEGY.' },
            { q: '¿Qué pasa si el servidor pierde conexión?', a: 'La GUI dejará de recibir polling (cada 5s). El indicador de pulso se apagará (gris) y mostrará último estado conocido. Al recuperar conexión, se sincroniza automáticamente vía /api/status.' },
            { q: '¿Cómo hago rollback si algo sale mal?', a: 'En Mission Control se listan los snapshots disponibles. Selecciona uno y pulsa “Restaurar”. Esto recupera configuración, memoria y estado de experimentos al momento del snapshot (SLA <60s).' },
            { q: '¿Cómo contacto soporte?', a: 'Revisa la documentación en Help > Documentación y README.md. Para consultas técnicas, usa el chat de Lila con comandos como /status o /risk. No hay soporte telefónico ni email en esta versión.' },
            { q: '¿Cuántas ventanas mínimas necesita walk-forward?', a: 'Mínimo 3 ventanas para validación estadística. Cada ventana debe tener suficientes datos para entrenamiento (in-sample) y test out-of-sample (OOS).' },
            { q: '¿Cómo promuevo una entrada de memoria a STRATEGY?', a: 'Requisitos: (1) Experimento validado con sharpe_like > 1.5, (2) Aprobación humana (approver_by), (3) Ejecutar POST /api/learning/memory/promote con target_level=4. El Production Gate validará automáticamente.' },
            { q: '¿Qué significa "primary_source_gap"?', a: 'Aparece cuando intentas validar un claim (hipótesis) pero no hay fuentes primary (ev_level=1) en la Library que lo respalden. Solución: ingesta al menos una fuente primary relacionada con el claim.' }
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

let helpDebounceTimer = null;
function filterHelp() {
    clearTimeout(helpDebounceTimer);
    helpDebounceTimer = setTimeout(() => {
        const q = document.getElementById('help-search-input').value.toLowerCase();
        const matches = HELP_DATA.filter(d =>
            d.title.toLowerCase().includes(q) ||
            d.content?.toLowerCase()?.includes(q) ||
            (d.items && d.items.some(f => f.q.toLowerCase().includes(q)))
        );
        renderHelpArticles(matches, q);
    }, 150);
}

function highlightMatch(text, query) {
    if (!query || !text) return text;
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

function renderHelpArticles(data, searchQuery = '') {
    const container = document.getElementById('help-articles');
    if (!container) return;

    if (data.length === 0) {
        container.innerHTML = `
            <div class="help-empty">
                <span style="font-size:2rem;display:block;margin-bottom:10px;">🔍</span>
                No se encontraron artículos que coincidan con tu búsqueda.
            </div>`;
        return;
    }

    const fragment = document.createDocumentFragment();

    data.forEach(item => {
        const div = document.createElement('div');
        div.className = 'help-card';

        if (item.isFaq) {
            const titleHtml = searchQuery ? highlightMatch(item.title, searchQuery) : item.title;
            div.innerHTML = `<h4>${item.icon} ${titleHtml}</h4>`;
            item.items.forEach((faq, idx) => {
                const fdiv = document.createElement('div');
                fdiv.className = 'help-faq-item';
                fdiv.dataset.faqId = `faq-${item.cat}-${idx}`;
                const qHtml = searchQuery ? highlightMatch(faq.q, searchQuery) : faq.q;
                const aHtml = searchQuery ? highlightMatch(faq.a, searchQuery) : faq.a;
                fdiv.innerHTML = `
                    <div class="help-faq-q" onclick="toggleFaq('${item.cat}', ${idx})">${qHtml} <span class="faq-arrow">▼</span></div>
                    <div class="help-faq-a" id="faq-${item.cat}-${idx}">${aHtml}</div>
                `;
                div.appendChild(fdiv);
            });
        } else {
            const titleHtml = searchQuery ? highlightMatch(item.title, searchQuery) : item.title;
            const contentHtml = searchQuery ? highlightMatch(item.content, searchQuery) : item.content;
            div.innerHTML = `
                <h4>${item.icon} ${titleHtml}</h4>
                <p>${contentHtml}</p>
            `;
        }
        fragment.appendChild(div);
    });

    container.innerHTML = '';
    container.appendChild(fragment);
}

function toggleFaq(cat, idx) {
    const targetId = `faq-${cat}-${idx}`;
    const allFaqs = document.querySelectorAll('.help-faq-a');
    const target = document.getElementById(targetId);
    const wasOpen = target.classList.contains('open');

    allFaqs.forEach(f => {
        f.classList.remove('open');
        f.style.maxHeight = '0';
    });

    if (!wasOpen) {
        target.classList.add('open');
        target.style.maxHeight = target.scrollHeight + 'px';
    }
}
