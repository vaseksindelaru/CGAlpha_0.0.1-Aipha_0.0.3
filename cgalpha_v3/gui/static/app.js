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
const expandedProposals = new Set();
const knownProposalIds = new Set();
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
    fetchAutoProposals();
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
        fetchAutoProposals();
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

// ── AUTO-PROPOSALS (Triple Coincidence Strategy) ──────
async function fetchAutoProposals() {
    try {
        const props = await apiFetch("/api/experiment/proposals");
        updateProposalsWidget(props);
        checkNewProposalsForLila(props);
    } catch (e) {
        console.warn("Error fetching proposals:", e);
    }
}

function updateProposalsWidget(props) {
    const container = document.getElementById("prop-list");
    const countEl = document.getElementById("prop-count");
    const badge = document.getElementById("exp-badge");
    if (!container) return;

    const pending = props.filter(p => p.status === "pending");
    if (countEl) countEl.textContent = `${pending.length} pendientes`;
    if (badge) {
        if (pending.length > 0) {
            badge.textContent = pending.length;
            badge.style.display = "inline-block";
        } else {
            badge.style.display = "none";
        }
    }

    if (props.length === 0) {
        container.innerHTML = `
            <div class="placeholder">
                <span class="ph-icon">🤖</span>
                Analizando historial para detectar oportunidades de mejora...
            </div>`;
        return;
    }

    container.innerHTML = props.map(p => {
        const isExpanded = expandedProposals.has(p.id);
        return `
            <div class="prop-card" id="prop-${p.id}" tabindex="0"
                 onclick="handleProposalInteraction('${p.id}', event)"
                 onkeydown="if(event.key === 'Enter') handleProposalInteraction('${p.id}', event)"
                 style="${p.status !== 'pending' ? 'opacity:0.5; pointer-events:none;' : ''}">
                <div class="prop-header">
                    <span class="prop-label">${p.component}</span>
                    <span class="prop-delta">+${(p.estimated_delta * 100).toFixed(1)}% Δ</span>
                </div>
                <div class="prop-body">
                    <strong>Cambio:</strong> ${p.change}<br>
                    <em>${p.reason}</em>
                    <div id="prop-detail-${p.id}" class="prop-detail" style="display:${isExpanded ? 'block' : 'none'}; margin-top:10px; padding-top:10px; border-top:1px solid var(--border); font-size:11px; opacity:0.8;">
                        <strong>Justificación Técnica:</strong><br>
                        ${p.detailed_description || 'Sin descripción adicional.'}<br><br>
                        <strong>Confianza:</strong> ${Math.round(p.confidence * 100)}% | <strong>Estimación Alpha:</strong> +${p.estimated_delta}
                    </div>
                </div>
                <div class="prop-footer" onclick="event.stopPropagation()">
                    <button class="btn btn-sm" onclick="evaluateProposal('${p.id}')">Evaluar</button>
                    <button class="btn btn-sm btn-ghost" onclick="ignoreProposal('${p.id}')">Ignorar</button>
                </div>
            </div>
        `;
    }).join("");
}

function handleProposalInteraction(id, event) {
    if (expandedProposals.has(id)) {
        expandedProposals.delete(id);
    } else {
        expandedProposals.add(id);
    }
    const el = document.getElementById(`prop-detail-${id}`);
    if (el) el.style.display = expandedProposals.has(id) ? 'block' : 'none';
}

function checkNewProposalsForLila(props) {
    const pending = props.filter(p => p.status === "pending");
    pending.forEach(p => {
        if (!knownProposalIds.has(p.id)) {
            knownProposalIds.add(p.id);
            const ev = new CustomEvent("lila:insight", {
                detail: {
                    text: `He detectado una oportunidad de mejora en **${p.component}**. Estimación de impacto: **+${(p.estimated_delta * 100).toFixed(1)}%**. ¿Deseas evaluarla en el Experiment Loop?`,
                    source: "autoproposer",
                    proposalId: p.id
                }
            });
            window.dispatchEvent(ev);
        }
    });
}

function evaluateProposal(id) {
    const hypo = `Evaluación AutoProposer ${id}: Optimización de parámetros Triple Coincidence`;
    const hypEl = document.getElementById("exp-hypothesis");
    if (hypEl) hypEl.value = hypo;
    const appEl = document.getElementById("exp-approaches");
    if (appEl) appEl.value = "TRIPLE_COINCIDENCE, RETEST, BOUNCE";
    showSection('experiment');
    if (hypEl) {
        hypEl.style.outline = "2px solid var(--accent)";
        hypEl.scrollIntoView({ behavior: 'smooth' });
        setTimeout(() => { hypEl.style.outline = "none"; }, 2000);
    }
}

function ignoreProposal(id) {
    const card = document.getElementById(`prop-${id}`);
    if (card) {
        card.style.opacity = "0.3";
        card.style.transform = "scale(0.95)";
        card.style.pointerEvents = "none";
    }
}

// ── LILA LLM STATUS & PROVIDER ────────────────────────
async function fetchLilaLLMStatus() {
    try {
        const data = await apiFetch("/api/lila/llm/status");
        const provEl = document.getElementById("lila-provider-name");
        if (provEl) provEl.textContent = data.provider || "Unknown";
        const circEl = document.getElementById("lila-circuit-status");
        if (circEl) circEl.textContent = data.circuit_breaker_status || "OK";
        if (data.memory_levels) updateLilaMemoryStats(data.memory_levels);
    } catch (e) {
        console.warn("LLM status fetch error:", e);
    }
}

async function switchLilaProvider(provider) {
    try {
        const response = await fetch('/api/lila/llm/switch', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ provider })
        });
        const data = await response.json();
        if (data.error) {
            alert(`Error switching provider: ${data.error}`);
        } else {
            console.log(`Provider switched to ${provider}`);
            fetchLilaLLMStatus();
        }
    } catch (err) {
        console.error('Error switching provider:', err);
    }
}

function updateLilaMemoryStats(levels) {
    const keys = ["0a", "0b", "1", "2", "3", "4"];
    keys.forEach(k => {
        const el = document.getElementById(`mem-${k}`);
        if (el) el.innerText = levels[k] || 0;
    });
}

// ── VAULT & ACTIVE STRATEGY (Triple Coincidence) ──────
async function toggleLilaActiveStrategy() {
    const strat = document.getElementById("lila-strategy-overlay");
    if (!strat) return;
    strat.classList.toggle("hidden");
    if (!strat.classList.contains("hidden")) {
        document.getElementById("lila-history-overlay")?.classList.add("hidden");
        document.getElementById("lila-settings-overlay")?.classList.add("hidden");
        document.getElementById("lila-vault-overlay")?.classList.add("hidden");
        fetchStrategyStatus();
    }
}

async function fetchStrategyStatus() {
    const view = document.getElementById("strategy-pipeline-view");
    if (!view) return;
    try {
        const data = await apiFetch("/api/vault/status");
        view.innerHTML = `
            <div style="background:rgba(0,212,170,0.05); padding:12px; border-radius:10px; border:1px solid var(--accent); margin-bottom:15px;">
                <strong style="color:var(--accent); font-size:13px;">Triple Coincidence Strategy</strong>
                <div style="font-size:11px; margin:8px 0;">Hit Rate OOS: <strong style="color:#4f4;">${data.metrics.hit_rate_oos}</strong></div>
                <button class="btn" style="width:100%;" onclick="executePipelineCycle()">Execute Massive Cycle</button>
            </div>
            ${data.components.map(c => `<div style="background:#0f1b2d; padding:8px; border-radius:6px; margin-bottom:5px; border:1px solid rgba(255,255,255,0.05); display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:bold; font-size:11px; color:var(--accent);">${c.name}</span>
                <span style="font-size:9px; color:#4f4;">${c.status}</span>
            </div>`).join("")}
        `;
    } catch { view.innerHTML = "<p>Error syncing pipeline v3.</p>"; }
}

async function executePipelineCycle() {
    if (!confirm("¿Deseas iniciar un Ciclo Masivo de Cosecha y Entrenamiento?")) return;
    try {
        const resp = await apiFetch("/api/lila/execute-cycle", { method: 'POST', body: JSON.stringify({ symbol: "BTCUSDT" }) });
        alert(`Ciclo Completado: ${resp.nexus_decision}`);
        fetchStrategyStatus();
    } catch (err) { alert("Error: " + err.message); }
}

async function toggleLilaVault() {
    const vault = document.getElementById("lila-vault-overlay");
    if (!vault) return;
    vault.classList.toggle("hidden");
    if (!vault.classList.contains("hidden")) {
        document.getElementById("lila-history-overlay")?.classList.add("hidden");
        document.getElementById("lila-settings-overlay")?.classList.add("hidden");
        document.getElementById("lila-strategy-overlay")?.classList.add("hidden");
        fetchVaultStatus();
    }
}

async function fetchVaultStatus() {
    const listEl = document.getElementById("vault-layers-view");
    if (!listEl) return;
    try {
        const data = await apiFetch("/api/vault/status");
        listEl.innerHTML = `
            <h4 style="color:var(--accent); font-size:12px;">Layer 2: Permanent DNA</h4>
            <div style="background:rgba(0,212,170,0.1); padding:10px; border-radius:10px; border:1px solid var(--accent); margin-bottom:15px;">
                <span style="font-weight:bold;">Verified Components: ${data.layers.layer_2_permanent_dna.total} ACTIVE</span>
            </div>
            <h4 style="font-size:11px; opacity:0.7;">Layer 1: Provisional Vault</h4>
            ${Object.entries(data.layers.layer_1_provisional).map(([k, v]) => `
                <div style="background:#0f1b2d; padding:6px; margin-bottom:4px; font-size:10px; display:flex; justify-content:space-between;">
                    <span>${k}</span><strong>${v}</strong>
                </div>
            `).join("")}
        `;
    } catch { listEl.innerHTML = "<p>Error syncing vault.</p>"; }
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

function toggleLilaSettings() {
    document.getElementById("lila-history-overlay")?.classList.add("hidden");
    document.getElementById("lila-strategy-overlay")?.classList.add("hidden");
    document.getElementById("lila-vault-overlay")?.classList.add("hidden");
    const overlay = document.getElementById("lila-settings-overlay");
    if (!overlay) return;
    overlay.classList.toggle("hidden");
    if (!overlay.classList.contains("hidden")) {
        fetchLilaLLMStatus();
    }
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
    // ═══════════════════════════════════════════════════
    // CATEGORÍA: INICIO
    // ═══════════════════════════════════════════════════
    {
        cat: 'inicio',
        title: '🚀 Quick Start — Arranque del Sistema',
        icon: '🚀',
        content: `
            <h4 style="color:var(--accent); margin-bottom:10px;">Requisitos</h4>
            <div style="background:var(--bg3); padding:12px; border-radius:8px; font-family:monospace; font-size:12px; margin-bottom:12px;">
Python >= 3.11<br>
flask >= 2.3.0<br>
pandas >= 2.0.0<br>
numpy >= 1.24.0<br>
scikit-learn >= 1.3.0  # Para OracleTrainer (Meta-Labeling)<br><br>
# Opcional<br>
openai >= 1.0.0  # Lila LLM Assistant
            </div>

            <h4 style="color:var(--accent); margin-bottom:10px;">Arranque del servidor</h4>
            <div style="background:var(--bg3); padding:12px; border-radius:8px; font-family:monospace; font-size:12px; margin-bottom:12px;">
# Variables de entorno (opcional, defaults seguros para dev)<br>
export CGV3_AUTH_TOKEN="cgalpha-v3-local-dev"<br>
export CGV3_HOST="0.0.0.0"<br>
export CGV3_PORT="5000"<br><br>
# Iniciar Control Room<br>
python cgalpha_v3/gui/server.py
            </div>

            <div style="background:rgba(0,212,170,0.08); padding:10px; border-radius:8px; border-left:3px solid var(--accent); font-size:12px;">
                <strong>Output esperado:</strong><br>
                <code style="color:var(--accent);">[CGAlpha v3 / Control Room] Iniciando en http://0.0.0.0:5000</code><br>
                <code style="color:var(--accent);">[CGAlpha v3 / Control Room] Active Builder v3.0 iniciado</code>
            </div>
        `
    },
    {
        cat: 'inicio',
        title: '🎯 Triple Coincidence Strategy — Flujo Completo',
        icon: '🎯',
        content: `
            <h4 style="color:var(--accent); margin-bottom:10px;">Principio Fundamental</h4>
            <p style="margin-bottom:8px; font-size:12px;">La estrategia detecta zonas por <strong>triple coincidencia</strong> de tres señales independientes, luego <em>espera el retest del precio</em>, captura features de microestructura <strong>EN ESE MOMENTO</strong> y entrena al Oracle con el outcome real.</p>

            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin:12px 0;">
                <div style="background:rgba(0,212,170,0.08); padding:10px; border-radius:8px; border-top:3px solid var(--accent); font-size:11px;">
                    <strong>Pilar I: Vela Clave</strong><br>
                    Alto volumen + cuerpo comprimido → absorción institucional
                </div>
                <div style="background:rgba(0,174,240,0.08); padding:10px; border-radius:8px; border-top:3px solid var(--accent2); font-size:11px;">
                    <strong>Pilar II: Acumulación</strong><br>
                    Rango estrecho + volumen elevado → consolidación
                </div>
                <div style="background:rgba(148,100,255,0.08); padding:10px; border-radius:8px; border-top:3px solid var(--purple); font-size:11px;">
                    <strong>Pilar III: Mini-Tendencia</strong><br>
                    ZigZag + R² &gt; 0.45 → dirección confirmada
                </div>
            </div>

            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; overflow-x:auto; line-height:1.5; margin-top:12px;">[1] BinanceVisionFetcher_v3
     ↓ OHLCV + microestructura (VWAP, OBI, CumDelta)
[2] TripleCoincidenceDetector
     ↓ Detecta zona: Vela Clave + Acumulación + Mini-Tendencia
     ↓ Monitorea zona → Espera retest del precio
     ↓ Captura features EN el retest (VWAP, OBI, CumDelta)
     ↓ Determina outcome (BOUNCE vs BREAKOUT, N velas lookahead)
[3] ZonePhysicsMonitor_v3
     ↓ Confirma REBOTE_CONFIRMADO
[4] OracleTrainer_v3 (Meta-Labeling)
     ↓ Predice: ¿Este retest resultará en BOUNCE?
     ↓ confidence &gt; 0.70 → Ejecutar
[5] ShadowTrader
     ↓ Captura MFE/MAE → Estadísticas Walk-Forward
[6] NexusGate
     ↓ PROMOTE_TO_LAYER_2 | REJECT
[7] AutoProposer
     ↓ Detecta drift → Propone ajustes paramétricos</pre>

            <div style="margin-top:12px; padding:10px; background:rgba(0,212,170,0.08); border-radius:8px; font-size:11px; border-left:3px solid var(--accent);">
                <strong>Key insight:</strong> Las features se capturan EN el retest, no en la detección de la zona. El Oracle evalúa las <em>condiciones del mercado en el momento del retest</em>, que son significativamente más predictivas que las condiciones en el momento de la detección.
            </div>
        `
    },
    {
        cat: 'inicio',
        title: '🧬 Scoring de Triple Coincidencia',
        icon: '🧬',
        content: `
            <p style="margin-bottom:12px; font-size:12px;">El score final combina componentes básicos (70%) y factores avanzados (30%):</p>

            <h4 style="color:var(--accent); margin-bottom:8px;">Componentes Básicos (70%)</h4>
            <table style="width:100%; border-collapse:collapse; font-size:11px; margin-bottom:12px;">
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:6px; color:var(--accent); font-weight:bold;">Zona (35%)</td>
                    <td style="padding:6px;">(quality_score - 0.45) / 0.4</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:6px; color:var(--accent2); font-weight:bold;">Tendencia (35%)</td>
                    <td style="padding:6px;">R² × direction_alignment × slope_normalized</td>
                </tr>
                <tr>
                    <td style="padding:6px; color:var(--purple); font-weight:bold;">Vela Clave (30%)</td>
                    <td style="padding:6px;">0.6 × volume_score + 0.4 × morphology</td>
                </tr>
            </table>

            <h4 style="color:var(--accent); margin-bottom:8px;">Factores Avanzados (30%)</h4>
            <table style="width:100%; border-collapse:collapse; font-size:11px; margin-bottom:12px;">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:6px;">Convergencia (20%)</td>
                    <td style="padding:6px;">Proximidad espacial y temporal de los 3 pilares</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:6px;">Fiabilidad (15%)</td>
                    <td style="padding:6px;">Bonus si R² &gt; 0.75</td>
                </tr>
                <tr>
                    <td style="padding:6px;">Potencial (15%)</td>
                    <td style="padding:6px;">Estimated move / ATR</td>
                </tr>
            </table>

            <div style="display:grid; grid-template-columns:repeat(4,1fr); gap:6px; font-size:10px; text-align:center;">
                <div style="padding:6px; background:rgba(255,255,255,0.03); border-radius:4px;">⚪ &lt;0.5<br>Débil</div>
                <div style="padding:6px; background:rgba(245,158,11,0.1); border-radius:4px; color:#f59e0b;">🟡 0.5-0.6<br>Moderada</div>
                <div style="padding:6px; background:rgba(255,107,107,0.1); border-radius:4px; color:#ff6b6b;">🟠 0.6-0.7<br>Fuerte</div>
                <div style="padding:6px; background:rgba(0,212,170,0.1); border-radius:4px; color:var(--accent);">🟢 &gt;0.7<br>Premium</div>
            </div>
        `
    },
    {
        cat: 'inicio',
        title: '🏗️ Arquitectura del Sistema CGAlpha v3',
        icon: '🏗️',
        content: `
            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; overflow-x:auto; line-height:1.4;">
┌─────────────────────────────────────────────────┐
│              BROWSER (Frontend)                  │
│  index.html │ style.css │ app.js                 │
│  Dashboard │ Risk │ Library │ Theory │ Learning  │
└───────────────────────┬─────────────────────────┘
                        │ HTTP/REST (polling 5s)
                        ▼
┌─────────────────────────────────────────────────┐
│              server.py (Flask)                   │
│  ┌──────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │Auth Layer│ │ API Routes   │ │State Manager│  │
│  │(Bearer)  │ │ 30+ endpoints│ │(_system_st) │  │
│  └──────────┘ └──────────────┘ └─────────────┘  │
└───────────────────────┬─────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ DOMAIN LAYER │ │ APPLICATION  │ │ LILA ENGINE  │
│              │ │              │ │              │
│ Signal       │ │ Pipeline     │ │ Library      │
│ ApproachType │ │ Experiment   │ │ Memory(0a-4) │
│ MemoryLevel  │ │ Rollback     │ │ Oracle(ML)   │
│ MicroRecord  │ │ ChangeProposer│ │ Backlog     │
└──────────────┘ └──────────────┘ └──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────┐
│           INFRASTRUCTURE LAYER                   │
│  TripleCoincidenceDetector │ BinanceVisionFetcher│
│  ZonePhysicsMonitor │ ShadowTrader              │
│  OracleTrainer │ NexusGate │ AutoProposer       │
└─────────────────────────────────────────────────┘</pre>
        `
    },
    {
        cat: 'inicio',
        title: '📊 Pipeline de Datos: Del Tick al ADN Permanente',
        icon: '📊',
        content: `
            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; overflow-x:auto; line-height:1.5;">
DATOS BRUTOS                         PROCESAMIENTO                        RESULTADO
─────────────                        ──────────────                       ─────────
Binance Vision ──► OHLCV 5m/1h ──► TripleCoincidence ──► ActiveZone
                                         │
                   Microestructura       │ retest detected
                   (VWAP,OBI,Delta) ──► Features@Retest ──► RetestEvent
                                         │
                                         ▼
                                    Outcome Observation
                                    (N velas lookahead)
                                         │
                                    ┌─────┴─────┐
                                    │           │
                                  BOUNCE    BREAKOUT
                                    │           │
                                    ▼           ▼
                              TrainingSample{features, outcome}
                                    │
                                    ▼
                              OracleTrainer_v3
                              .load_training_dataset()
                              .train_model()
                                    │
                                    ▼
                              Oracle.predict(new_retest)
                              confidence &gt; 0.70 → OPERAR
                                    │
                                    ▼
                              ShadowTrader(virtual)
                              MFE/MAE → NexusGate
                                    │
                              ΔCausal &gt; 0 + human
                                    │
                                    ▼
                              ADN PERMANENTE (Capa 2)</pre>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: RIESGO
    // ═══════════════════════════════════════════════════
    {
        cat: 'riesgo',
        title: '🛡️ Kill-Switch y Circuit Breakers',
        icon: '🛡️',
        content: `
            <p>El sistema implementa protecciones multinivel siguiendo el principio <strong>"primero sobrevivir, después optimizar"</strong>.</p>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                <div style="background:rgba(255,107,107,0.05); padding:12px; border-radius:8px; border:1px solid rgba(255,107,107,0.2);">
                    <strong style="color:var(--red); font-size:11px;">🚨 CIRCUIT BREAKERS</strong>
                    <p style="font-size:11px; margin-top:4px;">Se activan automáticamente si:</p>
                    <ul style="font-size:10px; margin-left:15px; margin-top:4px; color:var(--text-dim);">
                        <li>Drawdown de sesión &gt; límite configurado (default: 5%)</li>
                        <li>Data quality gate = "corrupted"</li>
                        <li>3 señales rechazadas consecutivas por Oracle</li>
                        <li>Latencia API &gt; 1000ms p95 sostenida &gt;60s</li>
                    </ul>
                </div>
                <div style="background:rgba(0,212,170,0.05); padding:12px; border-radius:8px; border:1px solid rgba(0,212,170,0.2);">
                    <strong style="color:var(--accent); font-size:11px;">⚡ KILL-SWITCH (2-PASOS)</strong>
                    <p style="font-size:11px; margin-top:4px;">Protocolo de seguridad humana:</p>
                    <ol style="font-size:10px; margin-left:15px; margin-top:4px; color:var(--text-dim);">
                        <li><code>POST /api/kill-switch/arm</code> → solicitar</li>
                        <li><code>POST /api/kill-switch/confirm</code> → confirmar</li>
                        <li>Todas las señales suspendidas inmediatamente</li>
                        <li><code>POST /api/kill-switch/reset</code> → re-armar</li>
                    </ol>
                </div>
            </div>
        `
    },
    {
        cat: 'riesgo',
        title: '📉 Parámetros de Riesgo',
        icon: '📉',
        content: `
            <p>Parámetros <strong>globales</strong> configurables desde el panel Risk o vía API <code>/api/risk/params</code>:</p>
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
                        <td style="padding:6px;">Dispara Circuit Breaker si se supera</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">Max Position Size</td>
                        <td style="padding:6px;">2.0%</td>
                        <td style="padding:6px;">% del capital por singal (exposición máxima)</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px;">Max Signals/Hora</td>
                        <td style="padding:6px;">10</td>
                        <td style="padding:6px;">Limita sobre-trading en alta volatilidad</td>
                    </tr>
                    <tr>
                        <td style="padding:6px;">Min Signal Quality</td>
                        <td style="padding:6px;">0.65</td>
                        <td style="padding:6px;">Score mínimo Triple Coincidence + Oracle confidence</td>
                    </tr>
                </tbody>
            </table>
            <p style="margin-top:10px; font-size:11px; color:var(--text-dim);">Los cambios aplican inmediatamente vía API POST; no requieren reinicio del servidor.</p>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: LILA
    // ═══════════════════════════════════════════════════
    {
        cat: 'lila',
        title: '🧠 Lila: Motor de Conocimiento y Biblioteca Inteligente',
        icon: '🧠',
        content: `
            <p style="margin-bottom:10px;">Lila es el <strong>cerebro epistémico</strong> de CGAlpha v3. No es un chatbot; es un sistema de gobernanza del conocimiento con 4 subsistemas:</p>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:11px;">
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:3px solid var(--accent);">
                    <strong>Library Manager</strong><br>
                    Ingesta, clasificación (primary/secondary/tertiary) y deduplicación de fuentes científicas. Valida venues contra lista de journals reconocidos.
                </div>
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:3px solid var(--accent2);">
                    <strong>Claim Validator</strong><br>
                    Verifica que hipótesis tengan soporte en fuentes primary (ev_level=1). Detecta primary_source_gap y genera backlog adaptativo.
                </div>
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:3px solid var(--purple);">
                    <strong>Memory Policy Engine</strong><br>
                    Gestiona TTL de entradas de memoria (0a→4). Detecta regime shifts que requieren degradar conocimiento obsoleto. Retención selectiva.
                </div>
                <div style="background:var(--bg3); padding:10px; border-radius:8px; border-left:3px solid var(--red);">
                    <strong>AutoProposer</strong><br>
                    Analiza drift en métricas del sistema. Propone ajustes paramétricos con estimated_delta y justificación causal. Requiere aprobación humana.
                </div>
            </div>
        `
    },
    {
        cat: 'lila',
        title: '🗂️ Memoria Inteligente: 5 Niveles (0a → 4)',
        icon: '🗂️',
        content: `
            <p style="margin-bottom:10px;">El sistema de memoria implementa una jerarquía de confianza con TTL progresivo y aprobadores diferenciados:</p>
            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Nivel</th>
                        <th style="padding:6px;">Nombre</th>
                        <th style="padding:6px;">TTL</th>
                        <th style="padding:6px;">Aprobador</th>
                        <th style="padding:6px;">Contenido</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">0a</td>
                        <td style="padding:6px;">Meta-Cognitivo: Principios</td>
                        <td style="padding:6px;">24h</td>
                        <td style="padding:6px;">Auto</td>
                        <td style="padding:6px;">DML, Meta-Labeling, EconML — axiomas teóricos</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">0b</td>
                        <td style="padding:6px;">Meta-Cognitivo: Papers</td>
                        <td style="padding:6px;">7d</td>
                        <td style="padding:6px;">Auto</td>
                        <td style="padding:6px;">Papers de trading (VWAP, OBI, CumDelta)</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">1</td>
                        <td style="padding:6px;">Operacional: Almacenamiento</td>
                        <td style="padding:6px;">30d</td>
                        <td style="padding:6px;">Lila</td>
                        <td style="padding:6px;">DuckDB, bridge.jsonl — datos persistidos</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">2</td>
                        <td style="padding:6px;">Operacional: Recuperación</td>
                        <td style="padding:6px;">90d</td>
                        <td style="padding:6px;">Lila</td>
                        <td style="padding:6px;">Búsqueda semántica vectorial, relaciones</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">3</td>
                        <td style="padding:6px;">Operacional: Aplicación</td>
                        <td style="padding:6px;">∞</td>
                        <td style="padding:6px;">Humano</td>
                        <td style="padding:6px;">ΔCausal, propuestas validadas, playbooks</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">4</td>
                        <td style="padding:6px;">Estrategia (ADN)</td>
                        <td style="padding:6px;">∞</td>
                        <td style="padding:6px;">Humano</td>
                        <td style="padding:6px;">Estrategias validadas con Sharpe &gt; 1.5 + NexusGate</td>
                    </tr>
                </tbody>
            </table>
            <div style="margin-top:10px; padding:8px; background:rgba(0,212,170,0.08); border-radius:6px; font-size:11px;">
                <strong>Política de retención:</strong> Las entradas expiran según su TTL. Las de nivel 3-4 son permanentes pero pueden ser degradadas si el MemoryPolicyEngine detecta un regime shift (volatilidad &gt; 2σ del baseline).
            </div>
        `
    },
    {
        cat: 'lila',
        title: '🔬 Oracle Meta-Labeling: Entrenamiento y Predicción',
        icon: '🔬',
        content: `
            <p style="margin-bottom:10px;">El <strong>OracleTrainer_v3</strong> implementa Meta-Labeling: un modelo ML secundario que predice si una señal del detector primario será exitosa.</p>

            <h4 style="color:var(--accent); margin-bottom:8px;">Dataset de Entrenamiento</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-size:11px; margin-bottom:12px;">
                <strong>Origen:</strong> TripleCoincidenceDetector.get_training_dataset()<br>
                <strong>Formato:</strong> TrainingSample{features: Dict, outcome: "BOUNCE"|"BREAKOUT"}<br>
                <strong>Features:</strong> vwap_at_retest, obi_10_at_retest, cumulative_delta_at_retest,<br>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;delta_divergence, atr_14, regime, direction
            </div>

            <h4 style="color:var(--accent); margin-bottom:8px;">Features Capturadas EN el Retest</h4>
            <table style="width:100%; border-collapse:collapse; font-size:10px;">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">vwap_at_retest</td>
                    <td style="padding:4px;">VWAP en el momento exacto del retest</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">obi_10_at_retest</td>
                    <td style="padding:4px;">Order Book Imbalance (10 niveles del order book)</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">cumulative_delta</td>
                    <td style="padding:4px;">Delta acumulado de volumen (presión compradora/vendedora)</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">delta_divergence</td>
                    <td style="padding:4px;">BULLISH_ABSORPTION | BEARISH_EXHAUSTION | NEUTRAL</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">regime</td>
                    <td style="padding:4px;">Régimen de mercado: TREND | LATERAL | HIGH_VOL</td>
                </tr>
            </table>

            <div style="margin-top:10px; padding:8px; background:rgba(0,212,170,0.08); border-radius:6px; font-size:11px;">
                <strong>Umbral operativo:</strong> confidence &gt; 0.70 → operar. Señales con confidence 0.70-0.72 muestran win rate solo 3% sobre baseline aleatorio (candidatas a ajuste por AutoProposer).
            </div>
        `
    },
    {
        cat: 'lila',
        title: '🔄 Change Proposer y Ciclo Evolutivo',
        icon: '🔄',
        content: `
            <p style="margin-bottom:10px;">El <strong>AutoProposer</strong> detecta drift y propone mejoras basándose en datos reales:</p>
            <ol style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Drift Detection:</strong> Monitorea métricas (win rate, drawdown, latencia) vs. baseline. Alerta si caen 2σ.</li>
                <li><strong>Propuesta Paramétrica:</strong> Genera ajuste con estimated_delta (mejora causal estimada) y justificación técnica.</li>
                <li><strong>Búsqueda Teórica:</strong> Lila busca en la Library fuentes que respalden o contradigan la propuesta. Si no hay soporte primary, genera backlog_item.</li>
                <li><strong>Validación:</strong> Se re-ejecuta Walk-Forward con parámetros nuevos. Solo se aplica si ΔCausal &gt; 0.</li>
                <li><strong>Aprobación Humana:</strong> Ningún cambio se aplica sin aprobación explícita.</li>
            </ol>
            <div style="margin-top:10px; padding:8px; background:rgba(255,107,107,0.08); border-radius:6px; font-size:11px;">
                <strong>Filosofía:</strong> Las mejoras no son predefinidas. Emergen del <em>pensamiento de la IA sobre los datos reales obtenidos</em>, se corroboran con teoría, y cada paso genera el siguiente.
            </div>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: DOCUMENTACIÓN TÉCNICA
    // ═══════════════════════════════════════════════════
    {
        cat: 'doc',
        title: '📡 API Reference — Endpoints Principales',
        icon: '📡',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">Sistema y Estado</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET /api/status          → Snapshot completo del sistema<br>
GET /api/events?limit=N  → Últimos N eventos (info/warning/critical)
            </div>

            <h4 style="color:var(--accent); margin-bottom:8px;">Kill-Switch (2-pasos)</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
POST /api/kill-switch/arm     → Paso 1: Solicitar activación<br>
POST /api/kill-switch/confirm → Paso 2: Confirmar<br>
POST /api/kill-switch/reset   → Re-armar (desactivar)
            </div>

            <h4 style="color:var(--accent); margin-bottom:8px;">Signal Detector &amp; Oracle</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET  /api/signal-detector/config → Config del TripleCoincidenceDetector<br>
POST /api/signal-detector/config → Actualizar parámetros (JSON body)<br>
GET  /api/oracle/config          → Config del OracleTrainer_v3<br>
POST /api/oracle/config          → Actualizar (min_confidence, etc.)
            </div>

            <h4 style="color:var(--accent); margin-bottom:8px;">Library &amp; Theory</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
GET  /api/library/status              → Estado de la biblioteca<br>
GET  /api/library/sources?query=...   → Búsqueda de fuentes<br>
POST /api/library/ingest              → Ingestar nueva fuente<br>
POST /api/library/claims/validate     → Validar claim técnico<br>
GET  /api/theory/live                 → Snapshot teórico en vivo
            </div>

            <h4 style="color:var(--accent); margin-bottom:8px;">Experiment Loop &amp; Memory</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px;">
GET  /api/experiment/status     → Estado del loop<br>
POST /api/experiment/propose    → Crear propuesta<br>
POST /api/experiment/run        → Ejecutar (walk-forward ≥3 ventanas)<br>
GET  /api/learning/memory/status → Motor de memoria<br>
POST /api/learning/memory/ingest → Ingestar entrada de memoria<br>
POST /api/learning/memory/retention/run → Ejecutar retención TTL<br>
POST /api/vault/status          → Estado de Bóveda v3 (7 componentes)
            </div>
        `
    },
    {
        cat: 'doc',
        title: '🏷️ Modelos de Dominio — Taxonomía Completa',
        icon: '🏷️',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">ApproachType (Acercamiento a zona)</h4>
            <table style="width:100%; border-collapse:collapse; font-size:11px; margin-bottom:16px;">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">TOUCH</td>
                    <td style="padding:4px;">Precio alcanza zona sin cierre beyond</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">RETEST</td>
                    <td style="padding:4px;">Regresa tras haber cerrado fuera (el evento más importante para Oracle)</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">REJECTION</td>
                    <td style="padding:4px;">Mecha opuesta &gt;60% del rango → rechazo violento</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">BREAKOUT</td>
                    <td style="padding:4px;">Cierre confirmado beyond zona</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">OVERSHOOT</td>
                    <td style="padding:4px;">Cierre beyond sin retorno en N velas</td>
                </tr>
                <tr>
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">FAKE_BREAK</td>
                    <td style="padding:4px;">Cierre beyond con retorno — trampa institucional</td>
                </tr>
            </table>

            <h4 style="color:var(--accent); margin-bottom:8px;">SourceType (Clasificación de fuentes)</h4>
            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">primary (ev=1)</td>
                    <td style="padding:4px;">Peer-reviewed, venue reconocido (ACL, NeurIPS, JOF, etc.)</td>
                </tr>
                <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">secondary (ev=2)</td>
                    <td style="padding:4px;">Blogs técnicos, whitepapers, documentación interna</td>
                </tr>
                <tr>
                    <td style="padding:4px; color:var(--accent); font-family:monospace;">tertiary (ev=3)</td>
                    <td style="padding:4px;">Social media, foros, opiniones (mínimo peso)</td>
                </tr>
            </table>
        `
    },
    {
        cat: 'doc',
        title: '📊 Métricas de Performance y Walk-Forward',
        icon: '📊',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">Métricas Calculadas</h4>
            <table style="width:100%; border-collapse:collapse; font-size:11px; margin-bottom:12px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border);">
                        <th style="padding:4px; text-align:left;">Métrica</th>
                        <th style="padding:4px; text-align:left;">Target</th>
                        <th style="padding:4px; text-align:left;">Descripción</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Sharpe Ratio</td>
                        <td style="padding:4px; color:var(--accent);">&gt; 2.0</td>
                        <td style="padding:4px;">Retorno ajustado por volatilidad</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Max Drawdown</td>
                        <td style="padding:4px; color:var(--red);">&lt; 10%</td>
                        <td style="padding:4px;">Pérdida máxima desde pico</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Win Rate</td>
                        <td style="padding:4px; color:var(--accent);">&gt; 55%</td>
                        <td style="padding:4px;">% trades (retests) rentables</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:4px;">Oracle Accuracy</td>
                        <td style="padding:4px; color:var(--accent);">&gt; 65%</td>
                        <td style="padding:4px;">Precisión del Meta-Labeling model</td>
                    </tr>
                    <tr>
                        <td style="padding:4px;">Calmar Ratio</td>
                        <td style="padding:4px; color:var(--accent);">&gt; 2.0</td>
                        <td style="padding:4px;">Return / Max DD anualizado</td>
                    </tr>
                </tbody>
            </table>

            <h4 style="color:var(--accent); margin-bottom:8px;">Walk-Forward Validation</h4>
            <p style="font-size:11px; margin-bottom:8px;">Mínimo 3 ventanas temporales. Cada ventana: periodo in-sample (train) + out-of-sample (OOS). El No-Leakage Gate verifica que ningún feature use información futura. Si <code>train_end ≥ oos_start</code>, el experimento es rechazado automáticamente.</p>
            <div style="padding:8px; background:rgba(0,212,170,0.05); border-radius:6px; font-size:11px;">
                Promoción a nivel 4 (STRATEGY) requiere: <strong>sharpe_like &gt; 1.5</strong> + aprobación humana + NexusGate.
            </div>
        `
    },
    {
        cat: 'doc',
        title: '📚 Estructura del Proyecto CGAlpha v3',
        icon: '📚',
        content: `
            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; overflow-x:auto; line-height:1.4;">
CGAlpha_0.0.1-Aipha_0.0.3/
├── LILA_v3_NORTH_STAR.md          # Documento fundacional (1300+ líneas)
├── cgalpha_v3/                    # Código fuente v3
│   ├── application/               # Capa de aplicación
│   │   ├── pipeline.py            # TripleCoincidencePipeline
│   │   ├── experiment_runner.py   # Walk-Forward validation
│   │   ├── change_proposer.py     # AutoProposer
│   │   └── rollback_manager.py    # Snapshot/restore
│   ├── domain/                    # Modelos de dominio
│   │   ├── models/signal.py       # ApproachType, TRIPLE_COINCIDENCE
│   │   └── records.py             # MicrostructureRecord, ZoneState
│   ├── infrastructure/            # Infraestructura
│   │   ├── signal_detector/       # TripleCoincidenceDetector
│   │   └── binance_data.py        # BinanceVisionFetcher_v3
│   ├── indicators/                # Indicadores técnicos
│   │   ├── zone_monitors.py       # ZonePhysicsMonitor_v3
│   │   └── legacy_signals.py      # VWAP, OBI, CumDelta
│   ├── lila/                      # Motor de conocimiento
│   │   ├── llm/oracle.py          # OracleTrainer_v3 (ML)
│   │   ├── llm/proposer.py        # AutoProposer
│   │   ├── nexus/gate.py          # NexusGate
│   │   └── library_manager.py     # Gestión de fuentes
│   ├── trading/shadow_trader.py   # ShadowTrader (virtual)
│   ├── gui/                       # Frontend + Backend
│   │   ├── server.py              # Flask (1900+ líneas, 30+ endpoints)
│   │   └── static/                # HTML/CSS/JS
│   ├── docs/                      # Documentación técnica
│   ├── memory/                    # Persistencia de memoria
│   └── tests/                     # 118 tests automatizados
└── legacy_vault/                  # Bóveda Capa 1 (herencia)</pre>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: AUDITORÍA
    // ═══════════════════════════════════════════════════
    {
        cat: 'auditoria',
        title: '🔒 Protocolo de Hardening P3',
        icon: '🔒',
        content: `
            <p>La Fase P3 representa el estado de "Producción Endurecida". Incluye:</p>
            <ul style="margin-left:20px; margin-top:8px; font-size:13px; color:var(--text-dim);">
                <li><strong>No-Leakage E2E:</strong> Pruebas matemáticas que garantizan que el sistema no usa información del futuro durante backtesting. Gate automático en cada ExperimentRunner.run().</li>
                <li><strong>Rollback Atómico:</strong> Capacidad de volver a un estado estable (Snapshot) si se detecta deriva de métricas. Snapshots automáticos + manuales desde GUI.</li>
                <li><strong>Change Proposer:</strong> Todas las modificaciones son propuestas por Lila/AutoProposer y deben ser validadas por Walk-Forward + aprobación humana.</li>
                <li><strong>ADN Permanente:</strong> Solo componentes con ΔCausal &gt; 0 verificado en OOS alcanzan Capa 2. El resto permanece en Capa 1 (provisional) hasta validación.</li>
            </ul>
        `
    },
    {
        cat: 'auditoria',
        title: '↩️ Rollback y Recovery',
        icon: '↩️',
        content: `
            <p>El sistema mantiene snapshots para recovery:</p>
            <ol style="margin-left:20px; margin-top:8px; font-size:12px; color:var(--text-dim);">
                <li><strong>Auto-snapshot:</strong> Antes de cada cambio de parámetros o ejecución de experimento</li>
                <li><strong>Manual snapshot:</strong> Disponible desde Mission Control (botón Restaurar)</li>
                <li><strong>Restore:</strong> Seleccione snapshot → Restaurar → sistema reinicia con configuración del snapshot</li>
            </ol>
            <div style="margin-top:10px; padding:8px; background:rgba(255,107,107,0.08); border-radius:6px; font-size:11px;">
                <strong style="color:var(--red);">⚠️ Importante:</strong> El restore solo afecta config, memoria y estado de experimentos. Los datos de mercado son externos e inmutables.
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
                        <td style="padding:6px;">Header <code>Authorization: Bearer &lt;token&gt;</code></td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">temporal_leakage</td>
                        <td style="padding:6px;">Feature usa datos del futuro</td>
                        <td style="padding:6px;">Verificar train_end &lt; oos_start</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">primary_source_gap</td>
                        <td style="padding:6px;">Claim sin fuente primary</td>
                        <td style="padding:6px;">Ingestar fuente con source_type=primary</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">production_gate_rejected</td>
                        <td style="padding:6px;">Promoción sin validación</td>
                        <td style="padding:6px;">Ejecutar experimento con sharpe &gt; 1.5</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">insufficient_windows</td>
                        <td style="padding:6px;">Walk-forward &lt; 3 ventanas</td>
                        <td style="padding:6px;">Proporcionar más datos históricos</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">regime_shift_detected</td>
                        <td style="padding:6px;">Volatilidad &gt; 2σ del baseline</td>
                        <td style="padding:6px;">Revisar parámetros, degradar memoria si necesario</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; color:var(--red); font-family:monospace;">ImportError</td>
                        <td style="padding:6px;">Módulo no encontrado</td>
                        <td style="padding:6px;">Verificar PYTHONPATH e instalación de dependencias</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'auditoria',
        title: '🔒 Producción — Seguridad',
        icon: '🔒',
        content: `
            <h4 style="color:var(--accent); margin-bottom:8px;">Token de autenticación</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-family:monospace; font-size:11px; margin-bottom:12px;">
# Generar token seguro (32+ caracteres)<br>
export CGV3_AUTH_TOKEN="$(openssl rand -hex 32)"
            </div>

            <h4 style="color:var(--accent); margin-bottom:8px;">Health Checks</h4>
            <div style="background:var(--bg3); padding:10px; border-radius:6px; font-size:11px;">
GET /api/status → Monitorear system_status, data_quality<br>
GET /api/events → Alertar si hay eventos con severity=critical<br>
GET /api/vault/status → Verificar 7 componentes ACTIVE
            </div>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: MICROESTRUCTURA
    // ═══════════════════════════════════════════════════
    {
        cat: 'micro',
        title: '📡 La Trinidad de Microestructura: VWAP + OBI + CumDelta',
        icon: '📡',
        content: `
            <p style="margin-bottom:12px;">El motor sensorial de CGAlpha v3. Estas tres señales de microestructura son los <strong>ojos del sistema</strong> en el order book en tiempo real. Se capturan EN el momento del retest, no en la detección de la zona.</p>

            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin:12px 0;">
                <div style="background:rgba(0,212,170,0.08); padding:12px; border-radius:8px; border-top:3px solid var(--accent);">
                    <strong style="font-size:13px;">VWAP</strong><br>
                    <span style="font-size:10px; color:var(--text-dim);">Volume-Weighted Average Price</span>
                    <p style="font-size:11px; margin-top:6px;">Precio ponderado por volumen acumulado del día. Indica el "precio justo". Si el retest ocurre CERCA del VWAP, la zona tiene mayor probabilidad de BOUNCE (el mercado respeta el "consenso").</p>
                    <div style="background:var(--bg3); padding:6px; border-radius:4px; font-family:monospace; font-size:10px; margin-top:6px;">
                        VWAP = Σ(TP × Vol) / Σ(Vol)<br>
                        TP = (H + L + C) / 3
                    </div>
                </div>
                <div style="background:rgba(0,174,240,0.08); padding:12px; border-radius:8px; border-top:3px solid var(--accent2);">
                    <strong style="font-size:13px;">OBI</strong><br>
                    <span style="font-size:10px; color:var(--text-dim);">Order Book Imbalance (10 niveles)</span>
                    <p style="font-size:11px; margin-top:6px;">Mide el desequilibrio entre bids y asks en los 10 primeros niveles del order book. OBI > 0 = presión compradora dominante. OBI < 0 = presión vendedora. Rango: [-1, +1].</p>
                    <div style="background:var(--bg3); padding:6px; border-radius:4px; font-family:monospace; font-size:10px; margin-top:6px;">
                        OBI = (Σbids - Σasks) / (Σbids + Σasks)
                    </div>
                </div>
                <div style="background:rgba(148,100,255,0.08); padding:12px; border-radius:8px; border-top:3px solid var(--purple);">
                    <strong style="font-size:13px;">CumDelta</strong><br>
                    <span style="font-size:10px; color:var(--text-dim);">Cumulative Delta Volume</span>
                    <p style="font-size:11px; margin-top:6px;">Acumulación de volumen de compradores vs vendedores desde apertura de sesión. Si el precio baja pero el CumDelta sube = BULLISH_ABSORPTION (institucionales comprando la caída).</p>
                    <div style="background:var(--bg3); padding:6px; border-radius:4px; font-family:monospace; font-size:10px; margin-top:6px;">
                        Δ = Σ(buy_vol) - Σ(sell_vol)
                    </div>
                </div>
            </div>

            <div style="margin-top:12px; padding:10px; background:rgba(0,212,170,0.08); border-radius:8px; font-size:11px; border-left:3px solid var(--accent);">
                <strong>Origen:</strong> Sección 4 del NORTH_STAR — "Alpha Core: La Trinidad de Microestructura reemplaza ATR como motor primario de la estrategia de scalping 1-5min."
            </div>
        `
    },
    {
        cat: 'micro',
        title: '🔬 Delta Divergence — Señales de Absorción',
        icon: '🔬',
        content: `
            <p style="margin-bottom:10px;">La <strong>divergencia de delta</strong> es la señal más poderosa de la microestructura. Indica que la actividad del order book contradice el movimiento del precio visible.</p>

            <table style="width:100%; border-collapse:collapse; font-size:11px; margin:12px 0;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px;">Tipo</th>
                        <th style="padding:6px;">Precio</th>
                        <th style="padding:6px;">CumDelta</th>
                        <th style="padding:6px;">Interpretación</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">BULLISH_ABSORPTION</td>
                        <td style="padding:6px;">Bajando ↓</td>
                        <td style="padding:6px;">Subiendo ↑</td>
                        <td style="padding:6px;">Institucionales comprando la caída. Probable BOUNCE.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--red); font-family:monospace;">BEARISH_EXHAUSTION</td>
                        <td style="padding:6px;">Subiendo ↑</td>
                        <td style="padding:6px;">Bajando ↓</td>
                        <td style="padding:6px;">Compradores agotándose pese a subida. Probable reversión.</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; font-family:monospace;">NEUTRAL</td>
                        <td style="padding:6px;">—</td>
                        <td style="padding:6px;">—</td>
                        <td style="padding:6px;">Sin divergencia significativa. No accionable.</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'micro',
        title: '🌡️ Régimen de Mercado: TREND | LATERAL | HIGH_VOL',
        icon: '🌡️',
        content: `
            <p style="margin-bottom:10px;">El sistema clasifica automáticamente el régimen de mercado actual. Esto afecta cómo el Oracle interpreta los retests (un retest en LATERAL tiene diferente semántica que uno en HIGH_VOL).</p>

            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin:12px 0; font-size:11px;">
                <div style="background:rgba(0,212,170,0.05); padding:10px; border-radius:8px; border:1px solid rgba(0,212,170,0.2);">
                    <strong style="color:var(--accent);">TREND</strong>
                    <p style="margin-top:4px;">Movimiento direccional sostenido. ATR creciente. R² alto en regresión lineal. Las zonas de acumulación son <em>breakout candidates</em>.</p>
                </div>
                <div style="background:rgba(245,158,11,0.05); padding:10px; border-radius:8px; border:1px solid rgba(245,158,11,0.2);">
                    <strong style="color:#f59e0b;">LATERAL</strong>
                    <p style="margin-top:4px;">Precio consolidando. ATR bajo. Volumen promedio estable. Las zonas de acumulación son <em>bounce candidates</em> — mejor escenario para la estrategia TC.</p>
                </div>
                <div style="background:rgba(255,107,107,0.05); padding:10px; border-radius:8px; border:1px solid rgba(255,107,107,0.2);">
                    <strong style="color:var(--red);">HIGH_VOL</strong>
                    <p style="margin-top:4px;">Volatilidad extrema (&gt;2σ ATR). Circuit breakers pueden activarse. Señales menos confiables. AutoProposer reduce position size automáticamente.</p>
                </div>
            </div>

            <div style="padding:8px; background:rgba(148,100,255,0.08); border-radius:6px; font-size:11px; margin-top:8px;">
                <strong>Regime Shift Detection (NORTH_STAR §2.4):</strong> Si la volatilidad supera 2σ del baseline durante &gt;20 sesiones, el MemoryPolicyEngine degrada conocimiento del régimen anterior (TTL reducido 50%).
            </div>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: BÓVEDA Y ADN
    // ═══════════════════════════════════════════════════
    {
        cat: 'boveda',
        title: '🏛️ Bóveda de Dos Capas: Provisional → Permanente',
        icon: '🏛️',
        content: `
            <p style="margin-bottom:10px;">La Bóveda es el sistema de gestión de componentes de CGAlpha v3. Implementa una jerarquía estricta donde solo el código que demuestra <strong>ΔCausal &gt; 0</strong> en datos OOS sobrevive.</p>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin:12px 0;">
                <div style="background:rgba(245,158,11,0.05); padding:14px; border-radius:10px; border:1px solid rgba(245,158,11,0.2);">
                    <h4 style="color:#f59e0b; font-size:13px; margin-bottom:8px;">⏳ Capa 1 — Provisional</h4>
                    <p style="font-size:11px;"><strong>Ubicación:</strong> <code>legacy_vault/</code></p>
                    <p style="font-size:11px;"><strong>Contenido:</strong> Herencia bruta de v1/v2</p>
                    <p style="font-size:11px;"><strong>Destino:</strong> Eliminación progresiva</p>
                    <p style="font-size:11px; margin-top:6px; color:var(--text-dim);">Componentes que no han sido validados con ΔCausal. Permanecen aquí como materia prima para el Mosaic Bridge.</p>
                </div>
                <div style="background:rgba(0,212,170,0.05); padding:14px; border-radius:10px; border:1px solid rgba(0,212,170,0.2);">
                    <h4 style="color:var(--accent); font-size:13px; margin-bottom:8px;">🧬 Capa 2 — ADN Permanente</h4>
                    <p style="font-size:11px;"><strong>Ubicación:</strong> <code>cgalpha_v3/</code></p>
                    <p style="font-size:11px;"><strong>Contenido:</strong> 7 componentes validados</p>
                    <p style="font-size:11px;"><strong>Destino:</strong> Producción</p>
                    <p style="font-size:11px; margin-top:6px; color:var(--text-dim);">Solo código con ΔCausal &gt; 0, test_coverage ≥ 80%, y human_approval alcanza esta capa.</p>
                </div>
            </div>

            <div style="padding:10px; background:var(--bg3); border-radius:8px; font-size:11px;">
                <strong>Principio (NORTH_STAR §3):</strong> "La Bóveda Provisional tiene fecha de muerte. Tú [Lila] decides cuándo. El ADN Permanente solo acepta lo que lo merece."
            </div>
        `
    },
    {
        cat: 'boveda',
        title: '🌉 Mosaic Bridge: De Legacy a v3',
        icon: '🌉',
        content: `
            <p style="margin-bottom:10px;">El <strong>Mosaic Bridge</strong> (Sección 7 del NORTH_STAR) es el protocolo técnico para extraer, adaptar y validar componentes del legacy vault hacia v3.</p>

            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; line-height:1.6; overflow-x:auto;">
FASE 1: DISCOVERY
  legacy_vault/ → Identificar componente candidato
  Evaluar: ¿Tiene lógica reutilizable? ¿Tests existentes?

FASE 2: WRAP
  Crear Mosaic Adapter (Wrapper Pattern)
  Mantener lógica interna intacta
  Añadir inputs/outputs tipados (MicrostructureRecord, etc.)

FASE 3: AUDIT
  Ejecutar tests unitarios heredados
  Verificar no-regresión: pytest legacy_vault/tests/

FASE 4: REGISTER
  ComponentManifest(name, heritage_source, v3_adaptations)
  Registrar en TripleCoincidencePipeline

FASE 5: CANARY PUSH
  Ejecutar en shadow mode (ShadowTrader)
  Medir ΔCausal en datos OOS
  Si ΔCausal > 0 → PROMOTE_TO_LAYER_2
  Si ΔCausal ≤ 0 → REJECT_TO_LEARNING_VAULT</pre>

            <div style="margin-top:10px; padding:8px; background:rgba(0,212,170,0.08); border-radius:6px; font-size:11px;">
                <strong>7 componentes adaptados:</strong> BinanceVisionFetcher, TripleCoincidenceDetector, ZonePhysicsMonitor, ShadowTrader, OracleTrainer, NexusGate, AutoProposer — cada uno con su <code>ComponentManifest</code> y <code>heritage_contribution</code>.
            </div>
        `
    },
    {
        cat: 'boveda',
        title: '⚗️ Ciclo de Vida del Componente: Cosecha → Purga',
        icon: '⚗️',
        content: `
            <pre style="background:var(--bg3); padding:12px; border-radius:8px; font-size:10px; line-height:1.8; overflow-x:auto;">
┌─────────────────────────────────┐
│   BÓVEDA CAPA 1 (Provisional)  │
│   legacy_vault/ — Herencia Bruta│
└──────────────┬──────────────────┘
               │ Cosecha (Mosaic Bridge)
               ▼
┌─────────────────────────────────┐
│   SIMPLE FOUNDATION STRATEGY   │
│   Pipeline 7 componentes       │
│   Shadow Trading → MFE/MAE     │
└──────────────┬──────────────────┘
               │ Resultados reales OOS
               ▼
┌─────────────────────────────────┐
│   ORACLE TRAINER (Meta-Label)  │
│   Entrena → Valida → Auto-Prop │
└──────────────┬──────────────────┘
               │ ΔCausal > umbral
               ▼
┌─────────────────────────────────┐
│   NEXUS GATE (Aprobación)      │
│   delta_causal > 0             │
│   blind_test_ratio ≤ 0.25      │
│   test_coverage ≥ 0.80         │
│   human_approval == True       │
└──────────────┬──────────────────┘
               │ Aprobado
               ▼
┌─────────────────────────────────┐
│   BÓVEDA CAPA 2 (Permanente)   │
│   ADN de v3 — Solo lo validado │
└──────────────┬──────────────────┘
               │ Purga del origen
               ▼
┌─────────────────────────────────┐
│   CAPA 1: Componente PURGADO   │
│   Marcado → Archivado → Borrado│
└─────────────────────────────────┘</pre>
        `
    },

    // ═══════════════════════════════════════════════════
    // CATEGORÍA: GLOSARIO TÉCNICO
    // ═══════════════════════════════════════════════════
    {
        cat: 'glosario',
        title: '📖 Glosario Técnico Completo',
        icon: '📖',
        content: `
            <p style="margin-bottom:12px; font-size:12px;">Referencia rápida de todos los términos técnicos del sistema, compilados de <code>TripleCoincidenceStrategy_v3.md</code>, <code>LILA_v3_NORTH_STAR.md</code>, <code>SYSTEM_DEEP_DIVE.md</code> y <code>CHECKLIST_IMPLEMENTACION.md</code>.</p>

            <table style="width:100%; border-collapse:collapse; font-size:11px;">
                <thead>
                    <tr style="border-bottom:1px solid var(--border); text-align:left;">
                        <th style="padding:6px; width:30%;">Término</th>
                        <th style="padding:6px;">Definición</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Triple Coincidence</td>
                        <td style="padding:6px;">Convergencia de vela clave + zona de acumulación + mini-tendencia. Los 3 deben coincidir en ≤ proximity_tolerance velas.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Retest</td>
                        <td style="padding:6px;">Retorno del precio a una zona previamente detectada. El evento central de la estrategia: aquí se capturan features.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">ActiveZone</td>
                        <td style="padding:6px;">Zona en monitoreo activo esperando retest. Expira tras retest_timeout_bars velas sin contacto.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">RetestEvent</td>
                        <td style="padding:6px;">Evento de retest con features de microestructura capturadas (VWAP, OBI, CumDelta, ATR, regime).</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">TrainingSample</td>
                        <td style="padding:6px;">Par {features_retest, outcome} para entrenamiento del Oracle. Generado por TripleCoincidenceDetector.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Meta-Labeling</td>
                        <td style="padding:6px;">Técnica ML (López de Prado) donde un modelo secundario predice si la señal primaria será exitosa.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">ΔCausal</td>
                        <td style="padding:6px;">Mejora neta en performance atribuible causalmente al componente. Calculada en OOS. Requisito para Capa 2.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">BOUNCE</td>
                        <td style="padding:6px;">El precio respeta la zona y revierte → señal exitosa para el Oracle.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">BREAKOUT</td>
                        <td style="padding:6px;">El precio rompe la zona definitivamente → señal fallida.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">OOS</td>
                        <td style="padding:6px;">Out-of-Sample — datos no vistos durante entrenamiento. Obligatorio para validación.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Walk-Forward</td>
                        <td style="padding:6px;">Backtesting con ventanas deslizantes (Train/Val/OOS). Mínimo 3 ventanas en CGAlpha.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Temporal Leakage</td>
                        <td style="padding:6px;">Error de usar datos futuros en backtesting. CGAlpha lo detecta automáticamente con TemporalLeakageError.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">ADN Permanente</td>
                        <td style="padding:6px;">Capa 2 de la Bóveda: componentes validados con ΔCausal &gt; 0 en datos reales OOS.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Mosaic Bridge</td>
                        <td style="padding:6px;">Protocolo para extraer, adaptar y validar componentes del legacy vault hacia v3 (5 fases).</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">ComponentManifest</td>
                        <td style="padding:6px;">Metadatos de cada componente v3: name, heritage_source, v3_adaptations, causal_score.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">Regime Shift</td>
                        <td style="padding:6px;">Cambio brusco en mercado (vol &gt; 2σ baseline). Dispara degradación de memoria y ajuste de parámetros.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">NexusGate</td>
                        <td style="padding:6px;">Gate binario final: PROMOTE_TO_LAYER_2 | REJECT. 5 condiciones obligatorias incluyendo human_approval.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">ShadowTrader</td>
                        <td style="padding:6px;">Ejecuta posiciones virtuales (sin capital real). Captura MFE/MAE para validación Walk-Forward.</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">MFE / MAE</td>
                        <td style="padding:6px;">Max Favorable Excursion / Max Adverse Excursion — lo máximo que una posición ganó o perdió antes de cerrar.</td>
                    </tr>
                    <tr>
                        <td style="padding:6px; color:var(--accent); font-family:monospace;">CGA_Ops</td>
                        <td style="padding:6px;">Semáforo de recursos (psutil): 🟢 RAM &lt;60% (operar), 🟡 60-80% (pausar), 🔴 señal trading detectada (kill).</td>
                    </tr>
                </tbody>
            </table>
        `
    },
    {
        cat: 'faq',
        title: 'Preguntas Frecuentes (FAQ)',
        icon: '❓',
        isFaq: true,
        items: [
            { q: '¿Qué es la Triple Coincidence Strategy?', a: 'Es la estrategia fundacional de CGAlpha v3. Detecta zonas de alta probabilidad cuando tres señales independientes convergen: vela clave (absorción institucional), zona de acumulación (consolidación + volumen), y mini-tendencia (ZigZag con R² > 0.45). A diferencia de la v2, NO opera en la detección sino que espera el retest y captura features de microestructura en ESE momento.' },
            { q: '¿Por qué las features se capturan EN el retest y no en la detección?', a: 'Porque las condiciones del mercado en el momento del retest son más predictivas que las condiciones en la detección. La zona puede haberse detectado hace 30 velas, pero el estado del order book (OBI), el delta acumulado y el VWAP EN el retest reflejan la presión actual del mercado, que es lo que determina si el precio rebotará (BOUNCE) o romperá (BREAKOUT).' },
            { q: '¿Qué es el Oracle y cómo funciona?', a: 'El OracleTrainer_v3 implementa Meta-Labeling: un modelo ML secundario que predice si una señal del detector primario será exitosa. Se entrena con pares {features_retest → outcome}. Su predicción (confidence score) filtra señales: solo con confidence > 0.70 se opera. El modelo se re-entrena incrementalmente con cada nuevo retest observado.' },
            { q: '¿Qué es el Temporal Leakage?', a: 'Error donde el algoritmo usa datos del futuro. CGAlpha tiene gates matemáticos en cada ExperimentRunner que bloquean cualquier experimento con leakage. Si train_end >= oos_start, el experimento es rechazado automáticamente con error: temporal_leakage.' },
            { q: '¿Cómo funciona la memoria de 5 niveles?', a: 'Nivel 0a (Meta-Cognitivo/Principios, TTL 24h) → 0b (Papers, TTL 7d) → 1 (Almacenamiento operacional, TTL 30d) → 2 (Recuperación semántica, TTL 90d) → 3 (Playbooks, permanente, aprobación humana) → 4 (Estrategia/ADN, permanente, requiere NexusGate + Sharpe > 1.5).' },
            { q: '¿Cómo funciona el Experiment Loop?', a: 'Crea una Proposal (hipótesis + approach_types), ejecútala con "Run Experiment". El sistema hace Walk-Forward validation (≥3 ventanas temporal) calculando métricas netas post-fricción (fees + slippage). Solo con sharpe > 1.5, human_approval y ΔCausal > 0 se puede promover a nivel 4 (STRATEGY).' },
            { q: '¿Puedo operar en modo live?', a: 'No en Fase 0. La GUI actual es Control Room con datos mock (precios simulados). El pipeline está diseñado para generar dataset de entrenamiento del Oracle via backtesting intensivo. La conexión WebSocket a Binance para datos reales está planificada para fases posteriores.' },
            { q: '¿Qué es el NexusGate?', a: 'El NexusGate es el árbitro final del pipeline. Su gate es binario: PROMOTE_TO_LAYER_2 o REJECT. Condiciones: ΔCausal > 0 (mejora causal demostrada en OOS), blind_test_ratio ≤ 0.25, test_coverage ≥ 0.80, oos_hit_rate_improvement > 0, y human_approval == True.' },
            { q: '¿Cómo se evoluciona la estrategia sin predefinir los pasos?', a: 'El ciclo evolutivo es emergente: (1) ejecutar estrategia → (2) analizar datos reales → (3) AutoProposer detecta drift y propone mejora → (4) Lila busca soporte teórico en Library → (5) si hay gap, genera backlog para buscar fuentes → (6) se valida con Walk-Forward → (7) el resultado genera la siguiente propuesta. Cada paso nace del anterior, no de un plan predefinido.' },
            { q: '¿Qué es "primary_source_gap"?', a: 'Aparece cuando intentas validar un claim (hipótesis) pero no hay fuentes primary (peer-reviewed, ev_level=1) en la Library que lo respalden. Solución: ingestar al menos una fuente primary. Esto asegura que las decisiones del sistema tienen base científica verificable.' },
            { q: '¿Cómo hago rollback si algo sale mal?', a: 'En Mission Control se listan los snapshots disponibles. Selecciona uno y pulsa "Restaurar". Esto recupera configuración, memoria y estado de experimentos al momento del snapshot.' },
            { q: '¿Qué son los 7 componentes del ADN Permanente?', a: 'BinanceVisionFetcher_v3 (datos), TripleCoincidenceDetector (detección + retest), ZonePhysicsMonitor_v3 (física del retest), ShadowTrader (posiciones virtuales), OracleTrainer_v3 (Meta-Labeling), NexusGate (gate binario), AutoProposer (drift + mejoras). Cada componente tiene su origen en la Bóveda legacy y ha sido adaptado y validado para v3.' }
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
