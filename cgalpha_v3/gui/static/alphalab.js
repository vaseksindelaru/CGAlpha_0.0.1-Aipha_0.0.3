/* ══════════════════════════════════════════════════════════
   AlphaLab v1.0 — Module Logic
   ══════════════════════════════════════════════════════════ */

// ── State ─────────────────────────────────────────────────
const AL = {
    ideas: [],
    stats: {},
    activity: { human: [], lila: [] },
    perspective: 'human',  // 'human' | 'lila'
    view: 'list',          // 'list' | 'board'
    currentSubview: 'home', // 'home' | 'inventory' | 'distill' | 'gate' | 'stub'
    detailOpen: null,       // vt_id of currently open detail
    filters: { text: '', type: 'all', status: 'all', vitality: 'all', pMin: 1, sMin: 1, dMax: 5, sort: 'p_desc' },
    distillStatus: null,
    gateArtifacts: [],
};

const STATUS_ORDER = ['IDEA_POOL', 'IN_RESEARCH', 'EVO_DRAFT', 'EVO_SUBMITTED', 'CODIFIED', 'ARCHIVED'];
const STATUS_LABELS = { IDEA_POOL: 'Pool', IN_RESEARCH: 'Research', EVO_DRAFT: 'Draft', EVO_SUBMITTED: 'Submitted', CODIFIED: 'Codified', ARCHIVED: 'Archived' };
const TYPE_LABELS = { F_CANDIDATE: 'Feature', A_MOTIVATION: 'Arquitectura', P_THEORY: 'Patrón', LC_DECISION: 'Config Lila' };
const TYPE_SHORT = { F_CANDIDATE: 'F', A_MOTIVATION: 'A', P_THEORY: 'P', LC_DECISION: 'LC' };

// ── Entry Point ───────────────────────────────────────────
function refreshAlphaLab() {
    Promise.all([
        fetch('/alphalab/stats').then(r => r.json()),
        fetch('/alphalab/ideas').then(r => r.json()),
        fetch('/alphalab/activity').then(r => r.json()),
    ]).then(([stats, ideas, activity]) => {
        AL.stats = stats;
        AL.ideas = ideas.ideas || [];
        AL.activity = activity;
        renderAlphaLabHome();
    }).catch(err => {
        console.error('AlphaLab fetch error:', err);
    });
}

// ── Home View ─────────────────────────────────────────────
function renderAlphaLabHome() {
    alShowSubview('home');
    // Stats
    _id('al-stat-active').textContent = AL.stats.active || 0;
    _id('al-stat-research').textContent = AL.stats.in_research || 0;
    _id('al-stat-drafts').textContent = AL.stats.evo_drafts || 0;
    _id('al-stat-codified').textContent = AL.stats.codified || 0;
    _id('al-stat-orphaned').textContent = AL.stats.orphaned || 0;

    // Vitality counters
    _id('al-vital-active-n').textContent = AL.stats.vitality_active || 0;
    _id('al-vital-dormant-n').textContent = AL.stats.vitality_dormant || 0;
    _id('al-vital-stalled-n').textContent = AL.stats.vitality_stalled || 0;
    _id('al-vital-orphaned-n').textContent = AL.stats.vitality_orphaned || 0;

    // Activity feed
    _renderActivityFeed();

    // Lila badge
    const lilaBadge = _id('al-lila-event-badge');
    if (lilaBadge) {
        const lilaCount = (AL.activity.lila || []).length;
        if (lilaCount > 0) { lilaBadge.textContent = lilaCount; lilaBadge.classList.add('visible'); }
        else { lilaBadge.classList.remove('visible'); }
    }
}

function _renderActivityFeed() {
    const humanList = _id('al-activity-human-list');
    const lilaList = _id('al-activity-lila-list');
    if (!humanList || !lilaList) return;

    humanList.innerHTML = (AL.activity.human || []).slice(0, 5).map(e =>
        `<div class="al-activity-event">
            <span class="al-event-dot human"></span>
            <span>${_esc(e.text)}</span>
            <span class="al-event-time">${_timeAgo(e.timestamp)}</span>
        </div>`
    ).join('') || '<div class="al-activity-event" style="color:var(--text-dim)">Sin actividad reciente</div>';

    lilaList.innerHTML = (AL.activity.lila || []).slice(0, 5).map(e =>
        `<div class="al-activity-event">
            <span class="al-event-dot lila"></span>
            <span>${_esc(e.text)}</span>
            <span class="al-event-time">${_timeAgo(e.timestamp)}</span>
        </div>`
    ).join('') || '<div class="al-activity-event" style="color:var(--text-dim)">Sin actividad reciente</div>';
}

// ── Perspective Toggle ────────────────────────────────────
function alSetPerspective(p) {
    AL.perspective = p;
    document.querySelectorAll('.al-perspective-btn').forEach(b => {
        b.classList.toggle('active', b.dataset.perspective === p);
    });
}

// ── Subview Navigation ────────────────────────────────────
function alShowSubview(name) {
    AL.currentSubview = name;
    document.querySelectorAll('#section-alphalab .al-subview').forEach(s => s.classList.remove('active'));
    const el = _id('al-subview-' + name);
    if (el) el.classList.add('active');

    if (name === 'inventory') alLoadInventory();
    if (name === 'distill') alLoadDistillAula();
    if (name === 'gate') alLoadGate();
}

function alBack() {
    renderAlphaLabHome();
}

// ── Inventory ─────────────────────────────────────────────
function alLoadInventory() {
    fetch('/alphalab/ideas').then(r => r.json()).then(data => {
        AL.ideas = data.ideas || [];
        AL.view === 'board' ? _renderBoard() : _renderList();
    });
}

function alSetView(v) {
    AL.view = v;
    document.querySelectorAll('.al-view-btn').forEach(b => b.classList.toggle('active', b.dataset.view === v));
    AL.view === 'board' ? _renderBoard() : _renderList();
}

function _getFiltered() {
    let items = [...AL.ideas];
    const f = AL.filters;

    if (f.text) {
        const q = f.text.toLowerCase();
        items = items.filter(i =>
            (i.title || '').toLowerCase().includes(q) ||
            (i.theory || '').toLowerCase().includes(q) ||
            (i.tags || []).some(t => t.toLowerCase().includes(q)) ||
            (i.vt_id || '').toLowerCase().includes(q)
        );
    }
    if (f.type !== 'all') items = items.filter(i => i.type === f.type);
    if (f.status !== 'all') items = items.filter(i => i.status === f.status);
    if (f.vitality !== 'all') items = items.filter(i => _calcVitality(i).state === f.vitality);
    items = items.filter(i => (i.score?.P || 0) >= f.pMin);
    items = items.filter(i => (i.score?.S || 0) >= f.sMin);
    items = items.filter(i => (i.score?.D || 5) <= f.dMax);

    // Sort
    switch (f.sort) {
        case 'p_desc': items.sort((a, b) => (b.score?.P || 0) - (a.score?.P || 0)); break;
        case 's_desc': items.sort((a, b) => (b.score?.S || 0) - (a.score?.S || 0)); break;
        case 'date_asc': items.sort((a, b) => (a.extraction_date || '').localeCompare(b.extraction_date || '')); break;
        case 'idle_desc': items.sort((a, b) => _calcVitality(b).days - _calcVitality(a).days); break;
    }
    return items;
}

function alApplyFilters() {
    AL.filters.text = (_id('al-filter-text') || {}).value || '';
    AL.filters.type = (_id('al-filter-type') || {}).value || 'all';
    AL.filters.status = (_id('al-filter-status') || {}).value || 'all';
    AL.filters.vitality = (_id('al-filter-vitality') || {}).value || 'all';
    AL.filters.pMin = parseInt((_id('al-filter-pmin') || {}).value || '1');
    AL.filters.sMin = parseInt((_id('al-filter-smin') || {}).value || '1');
    AL.filters.dMax = parseInt((_id('al-filter-dmax') || {}).value || '5');
    AL.filters.sort = (_id('al-filter-sort') || {}).value || 'p_desc';
    AL.view === 'board' ? _renderBoard() : _renderList();
}

function _renderList() {
    const items = _getFiltered();
    const tbody = _id('al-inventory-tbody');
    if (!tbody) return;

    tbody.innerHTML = items.map(idea => {
        const vit = _calcVitality(idea);
        const ts = TYPE_SHORT[idea.type] || '?';
        const maturityIdx = STATUS_ORDER.indexOf(idea.status);
        const maturityDots = STATUS_ORDER.slice(0, 5).map((_, i) => {
            if (i < maturityIdx) return '<span class="al-maturity-dot completed"></span>';
            if (i === maturityIdx) return '<span class="al-maturity-dot current"></span>';
            return '<span class="al-maturity-dot"></span>';
        }).join('');

        let stalledHtml = '';
        if (vit.state === 'STALLED') {
            stalledHtml = `<div class="al-stalled-alert">
                <span class="al-alert-text">⚠ ${vit.days} días sin actividad</span>
                <button class="al-btn al-btn-sm al-btn-ghost" onclick="event.stopPropagation();alUpdateStatus('${idea.vt_id}','IN_RESEARCH')">Investigar</button>
                <button class="al-btn al-btn-sm al-btn-danger" onclick="event.stopPropagation();alArchiveIdea('${idea.vt_id}')">Archivar</button>
                ${(idea.postpone_count || 0) < 2 ? `<button class="al-btn al-btn-sm al-btn-ghost" onclick="event.stopPropagation();alPostpone('${idea.vt_id}')">Posponer</button>` : ''}
            </div>`;
        }

        return `<tr onclick="alOpenDetail('${idea.vt_id}')">
            <td><span class="al-type-badge ${ts.toLowerCase()}">${ts}</span></td>
            <td><code style="color:var(--al-accent);font-size:11px">${_esc(idea.vt_id)}</code></td>
            <td>${_esc(idea.title || '')}</td>
            <td><span class="al-status-badge ${(idea.status || '').toLowerCase()}">${STATUS_LABELS[idea.status] || idea.status}</span></td>
            <td><div class="al-maturity">${maturityDots}</div></td>
            <td><span class="al-vital-badge ${vit.state.toLowerCase()}">${vit.state}</span></td>
            <td><span class="al-psd-badge">P${idea.score?.P || 0}/S${idea.score?.S || 0}/D${idea.score?.D || 0}</span></td>
            <td style="color:var(--text-dim);font-size:12px">${vit.days}d</td>
        </tr>${stalledHtml ? `<tr><td colspan="8" style="padding:0 12px 8px">${stalledHtml}</td></tr>` : ''}`;
    }).join('');
}

function _renderBoard() {
    const items = _getFiltered();
    const types = ['F_CANDIDATE', 'A_MOTIVATION', 'P_THEORY', 'LC_DECISION'];
    const labels = ['F-CANDIDATES', 'A-MOTIVATIONS', 'P-THEORIES', 'LC-DECISIONS'];
    const container = _id('al-board-container');
    if (!container) return;

    container.innerHTML = types.map((t, idx) => {
        const typeItems = items.filter(i => i.type === t).sort((a, b) => (b.score?.P || 0) - (a.score?.P || 0));
        return `<div class="al-board-column">
            <div class="al-board-column-title">${labels[idx]} (${typeItems.length})</div>
            ${typeItems.map(idea => {
                const vit = _calcVitality(idea);
                const maturityIdx = STATUS_ORDER.indexOf(idea.status);
                const dots = STATUS_ORDER.slice(0, 5).map((_, i) => {
                    if (i < maturityIdx) return '<span class="al-maturity-dot completed"></span>';
                    if (i === maturityIdx) return '<span class="al-maturity-dot current"></span>';
                    return '<span class="al-maturity-dot"></span>';
                }).join('');
                return `<div class="al-board-card" onclick="alOpenDetail('${idea.vt_id}')">
                    <div class="al-board-card-id">${_esc(idea.vt_id)}</div>
                    <div class="al-board-card-title">${_esc(idea.title || '')}</div>
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
                        <span class="al-psd-badge">P${idea.score?.P || 0}/S${idea.score?.S || 0}/D${idea.score?.D || 0}</span>
                        <span class="al-vital-badge ${vit.state.toLowerCase()}">${vit.state}</span>
                    </div>
                    <div class="al-maturity">${dots}
                        <span class="al-maturity-label">${STATUS_LABELS[idea.status] || ''} · ${vit.days}d</span>
                    </div>
                </div>`;
            }).join('')}
        </div>`;
    }).join('');
}

// ── Detail Panel ──────────────────────────────────────────
function alOpenDetail(vtId) {
    const idea = AL.ideas.find(i => i.vt_id === vtId);
    if (!idea) return;
    AL.detailOpen = vtId;

    const vit = _calcVitality(idea);
    const maturityIdx = STATUS_ORDER.indexOf(idea.status);
    const dots = STATUS_ORDER.slice(0, 5).map((_, i) => {
        if (i < maturityIdx) return '<span class="al-maturity-dot completed"></span>';
        if (i === maturityIdx) return '<span class="al-maturity-dot current"></span>';
        return '<span class="al-maturity-dot"></span>';
    }).join('');
    const ts = TYPE_SHORT[idea.type] || '?';

    const panel = _id('al-detail-panel');
    const backdrop = _id('al-detail-backdrop');
    if (!panel) return;

    panel.innerHTML = `
        <div class="al-detail-header">
            <div>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
                    <code style="font-size:15px;font-weight:700;color:var(--al-accent)">${_esc(idea.vt_id)}</code>
                    <span class="al-type-badge ${ts.toLowerCase()}">${TYPE_LABELS[idea.type] || idea.type}</span>
                </div>
                <div style="font-size:17px;font-weight:700;color:var(--text)">${_esc(idea.title || '')}</div>
            </div>
            <button class="al-detail-close" onclick="alCloseDetail()">✕</button>
        </div>

        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap">
            <div class="al-maturity">${dots}
                <span class="al-maturity-label">${STATUS_LABELS[idea.status] || ''} · ${vit.days}d</span>
            </div>
            <span class="al-psd-badge">P:${idea.score?.P || 0} / S:${idea.score?.S || 0} / D:${idea.score?.D || 0}</span>
            <span class="al-vital-badge ${vit.state.toLowerCase()}">${vit.state}</span>
        </div>

        <div class="al-detail-section">
            <h4>Origen</h4>
            <p>${_esc(idea.origin_doc || 'Sin documento')} · Párrafos: ${(idea.origin_paragraphs || []).join(', ') || '—'}</p>
            <p style="font-size:11px;color:var(--text-dim)">Extraído: ${idea.extraction_date || '—'} · Última actividad: ${_timeAgo(idea.last_activity)}</p>
        </div>

        <div class="al-detail-section">
            <h4>Teoría Rescatada</h4>
            <textarea id="al-detail-theory" rows="4">${_esc(idea.theory || '')}</textarea>
        </div>

        <div class="al-detail-section">
            <h4>Inyección en Código</h4>
            <input type="text" class="al-filter-input" style="width:100%" id="al-detail-target" value="${_esc(idea.code_target || '')}">
        </div>

        <div class="al-detail-section">
            <h4>Investigación Pendiente</h4>
            <textarea id="al-detail-research" rows="3">${_esc(idea.research_needed || '')}</textarea>
        </div>

        <div class="al-detail-section">
            <h4>Tags</h4>
            <div id="al-detail-tags" style="margin-bottom:6px">
                ${(idea.tags || []).map(t => `<span class="al-tag">${_esc(t)}</span>`).join('')}
            </div>
            <input type="text" class="al-filter-input" id="al-detail-tags-input" placeholder="Nuevo tag (Enter para añadir)" style="width:200px"
                onkeydown="if(event.key==='Enter'){alAddTag('${idea.vt_id}',this.value);this.value=''}">
        </div>

        <div class="al-detail-section">
            <h4>Relaciones Confirmadas</h4>
            <div id="al-detail-relations">
                ${(idea.related_ideas || []).length > 0 ?
                    idea.related_ideas.map(r => `<div style="font-size:12px;margin-bottom:4px">🔗 ${_esc(r)}</div>`).join('') :
                    '<div style="font-size:12px;color:var(--text-dim)">Sin relaciones vinculadas</div>'}
            </div>
            <input type="text" class="al-filter-input" id="al-detail-link-input" placeholder="VT-ID a vincular (Enter)" style="width:200px;margin-top:6px"
                onkeydown="if(event.key==='Enter'){alLinkIdea('${idea.vt_id}',this.value);this.value=''}">
        </div>

        ${idea.linked_codex ? `
        <div class="al-detail-section">
            <h4>Entrada Codex Vinculada</h4>
            <div class="al-codex-card">
                <div class="al-codex-header">
                    <span class="al-codex-id">${_esc(idea.linked_codex)}</span>
                    <span class="al-harness-badge">⚡ HARNESS ACTIVO</span>
                </div>
            </div>
        </div>` : ''}

        <div class="al-detail-actions">
            <button class="al-btn al-btn-primary" onclick="alSaveDetail('${idea.vt_id}')">💾 Guardar Cambios</button>
            ${idea.status === 'IDEA_POOL' ? `<button class="al-btn al-btn-ghost" onclick="alUpdateStatus('${idea.vt_id}','IN_RESEARCH')">🔍 Marcar para Investigación</button>` : ''}
            ${['IDEA_POOL','IN_RESEARCH'].includes(idea.status) ? `<button class="al-btn al-btn-ghost" onclick="alPromoteToEvo('${idea.vt_id}')">🚀 Promover a EVO Draft</button>` : ''}
            ${idea.status !== 'ARCHIVED' ? `<button class="al-btn al-btn-danger" onclick="alArchiveIdea('${idea.vt_id}')">📦 Archivar</button>` : ''}
        </div>
    `;

    panel.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
}

function alCloseDetail() {
    AL.detailOpen = null;
    const panel = _id('al-detail-panel');
    const backdrop = _id('al-detail-backdrop');
    if (panel) panel.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
}

function alSaveDetail(vtId) {
    const updates = {
        theory: (_id('al-detail-theory') || {}).value,
        code_target: (_id('al-detail-target') || {}).value,
        research_needed: (_id('al-detail-research') || {}).value,
    };
    fetch(`/alphalab/ideas/${vtId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    }).then(() => { alLoadInventory(); alOpenDetail(vtId); });
}

function alAddTag(vtId, tag) {
    if (!tag.trim()) return;
    const idea = AL.ideas.find(i => i.vt_id === vtId);
    if (!idea) return;
    const tags = [...(idea.tags || []), tag.trim()];
    fetch(`/alphalab/ideas/${vtId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tags })
    }).then(() => { alLoadInventory(); alOpenDetail(vtId); });
}

function alLinkIdea(vtId, linkId) {
    if (!linkId.trim()) return;
    const idea = AL.ideas.find(i => i.vt_id === vtId);
    if (!idea) return;
    const related = [...(idea.related_ideas || []), linkId.trim()];
    fetch(`/alphalab/ideas/${vtId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ related_ideas: related })
    }).then(() => { alLoadInventory(); alOpenDetail(vtId); });
}

// ── Status & Actions ──────────────────────────────────────
function alUpdateStatus(vtId, newStatus) {
    fetch(`/alphalab/ideas/${vtId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
    }).then(() => { alLoadInventory(); });
}

function alArchiveIdea(vtId) {
    const epitaph = prompt('Epitafio (razón de archivo):');
    if (!epitaph || epitaph.length < 20) { alert('El epitafio debe tener al menos 20 caracteres.'); return; }
    fetch(`/alphalab/ideas/${vtId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'ARCHIVED', archive_epitaph: epitaph })
    }).then(() => { alLoadInventory(); alCloseDetail(); });
}

function alPostpone(vtId) {
    const date = prompt('Nueva fecha de revisión (YYYY-MM-DD):');
    if (!date) return;
    fetch(`/alphalab/ideas/${vtId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ next_review_date: date, _postpone: true })
    }).then(() => alLoadInventory());
}

function alPromoteToEvo(vtId) {
    alUpdateStatus(vtId, 'EVO_DRAFT');
}

// ── Orphan Resolution ─────────────────────────────────────
function alShowOrphanRitual(vtId) {
    const idea = AL.ideas.find(i => i.vt_id === vtId);
    if (!idea) return;
    const vit = _calcVitality(idea);

    const overlay = _id('al-orphan-overlay');
    if (!overlay) return;

    overlay.innerHTML = `
        <div class="al-orphan-modal">
            <h3>RESOLUCIÓN REQUERIDA</h3>
            <div class="al-idea-ref">${_esc(idea.vt_id)} · ${_esc(idea.title)} · ${vit.days} días sin actividad</div>

            <div class="al-orphan-option">
                <label><input type="radio" name="orphan-action" value="reactivate"> REACTIVAR</label>
                <textarea id="al-orphan-justification" placeholder="¿Qué cambió que hace esta idea relevante ahora? (mín. 40 caracteres)" rows="2"></textarea>
            </div>

            <div class="al-orphan-option">
                <label><input type="radio" name="orphan-action" value="archive"> ARCHIVAR</label>
                <textarea id="al-orphan-epitaph" placeholder="Epitafio: razón para el archivo (mín. 20 caracteres)" rows="2"></textarea>
            </div>

            ${(idea.postpone_count || 0) < 2 ? `
            <div class="al-orphan-option">
                <label><input type="radio" name="orphan-action" value="keep"> MANTENER ABIERTA</label>
                <textarea id="al-orphan-keep-reason" placeholder="Justificación (obligatorio)" rows="2"></textarea>
                <input type="date" id="al-orphan-review-date" style="margin-top:6px">
            </div>` : ''}

            <div style="display:flex;gap:8px;margin-top:16px">
                <button class="al-btn al-btn-primary" onclick="alSubmitOrphanResolution('${idea.vt_id}')">Confirmar</button>
                <button class="al-btn al-btn-ghost" onclick="_id('al-orphan-overlay').style.display='none'">Cancelar</button>
            </div>
        </div>
    `;
    overlay.style.display = 'flex';
}

function alSubmitOrphanResolution(vtId) {
    const action = document.querySelector('input[name="orphan-action"]:checked')?.value;
    if (!action) { alert('Selecciona una acción.'); return; }

    if (action === 'reactivate') {
        const j = (_id('al-orphan-justification') || {}).value || '';
        if (j.length < 40) { alert('La justificación debe tener al menos 40 caracteres.'); return; }
        fetch(`/alphalab/ideas/${vtId}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'IN_RESEARCH', _reactivate_reason: j })
        }).then(() => { _id('al-orphan-overlay').style.display = 'none'; alLoadInventory(); });
    } else if (action === 'archive') {
        const e = (_id('al-orphan-epitaph') || {}).value || '';
        if (e.length < 20) { alert('El epitafio debe tener al menos 20 caracteres.'); return; }
        fetch(`/alphalab/ideas/${vtId}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'ARCHIVED', archive_epitaph: e })
        }).then(() => { _id('al-orphan-overlay').style.display = 'none'; alLoadInventory(); });
    } else if (action === 'keep') {
        const r = (_id('al-orphan-keep-reason') || {}).value || '';
        const d = (_id('al-orphan-review-date') || {}).value || '';
        if (!r || !d) { alert('Justificación y fecha son obligatorios.'); return; }
        fetch(`/alphalab/ideas/${vtId}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ next_review_date: d, _postpone: true })
        }).then(() => { _id('al-orphan-overlay').style.display = 'none'; alLoadInventory(); });
    }
}

// ── Distillation Aula ─────────────────────────────────────
function alLoadDistillAula() {
    fetch('/alphalab/distill/status').then(r => r.json()).then(data => {
        AL.distillStatus = data;
        _renderDistillStatus();
    });
}

function alStartDistillation() {
    const fileInput = _id('al-distill-file');
    const filter = document.querySelector('input[name="al-filter-type"]:checked')?.value || 'old_testament';
    if (!fileInput || !fileInput.files.length) { alert('Selecciona un documento.'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('filter', filter);

    fetch('/alphalab/distill', { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            AL.distillStatus = data;
            _renderDistillStatus();
            if (data.status === 'completed') {
                AL.gateArtifacts = data.artifacts || [];
                alShowSubview('gate');
            }
        });
}

function _renderDistillStatus() {
    const el = _id('al-distill-status');
    if (!el || !AL.distillStatus) { if (el) el.innerHTML = ''; return; }
    const s = AL.distillStatus;

    if (s.status === 'idle') {
        el.innerHTML = '';
    } else if (s.status === 'processing') {
        el.innerHTML = `
            <div style="padding:16px;background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.15);border-radius:8px">
                <div style="font-weight:700;color:var(--al-yellow);margin-bottom:8px">🟡 Destilando: ${_esc(s.document || '')}</div>
                <div class="al-progress-bar"><div class="al-progress-fill" style="width:${s.progress || 0}%"></div></div>
                <div style="font-size:11px;color:var(--text-dim);margin-top:6px">${s.progress || 0}% · ${s.artifacts_found || 0} artefactos detectados</div>
            </div>`;
    } else if (s.status === 'completed') {
        el.innerHTML = `
            <div style="padding:16px;background:rgba(52,211,153,0.06);border:1px solid rgba(52,211,153,0.15);border-radius:8px">
                <div style="font-weight:700;color:var(--al-green);margin-bottom:4px">🟢 Destilación completada: ${_esc(s.document || '')}</div>
                <div style="font-size:12px;color:var(--text-dim)">${s.artifacts?.length || 0} artefactos extraídos</div>
                <button class="al-btn al-btn-primary al-btn-sm" style="margin-top:8px" onclick="AL.gateArtifacts=AL.distillStatus.artifacts||[];alShowSubview('gate')">Revisar en Puerta de Ingreso →</button>
            </div>`;
    }
}

// ── Quarantine Gate ───────────────────────────────────────
function alLoadGate() {
    const arts = AL.gateArtifacts || [];
    const container = _id('al-gate-container');
    if (!container) return;

    const trayA = arts.filter(a => (a.score?.P || 0) >= 4 && (a.score?.S || 0) >= 4);
    const trayC = arts.filter(a => (a.score?.P || 0) < 3 && (a.score?.S || 0) < 3);
    const trayB = arts.filter(a => !trayA.includes(a) && !trayC.includes(a));

    container.innerHTML = `
        ${_renderGateTray('A', 'Señal alta (P≥4 y S≥4)', trayA, true)}
        ${_renderGateTray('B', 'Señal media', trayB, false)}
        ${_renderGateTray('C', 'Señal baja', trayC, false)}
    `;
}

function _renderGateTray(band, label, items, allowBatch) {
    if (!items.length) return '';
    return `<div class="al-gate-tray">
        <div class="al-gate-tray-header">
            <span class="al-gate-tray-title">BANDEJA ${band} — ${label} · ${items.length} artefactos</span>
            ${allowBatch ? `<button class="al-btn al-btn-approve al-btn-sm" onclick="alApproveBatch('${band}')">✓ Aprobar toda la Bandeja ${band}</button>` : ''}
            ${band === 'C' ? `<button class="al-btn al-btn-danger al-btn-sm" onclick="alDiscardBatch('C')">✗ Descartar toda la Bandeja C</button>` : ''}
        </div>
        ${items.map(a => `<div class="al-gate-item">
            <code style="font-size:11px;color:var(--al-accent)">${_esc(a.vt_id)}</code>
            <span class="al-psd-badge">P${a.score?.P}/S${a.score?.S}/D${a.score?.D}</span>
            <span style="flex:1;font-size:13px">${_esc(a.title || '')}</span>
            <div class="al-gate-actions">
                <button class="al-btn al-btn-sm al-btn-ghost" onclick="alGateEdit('${a.vt_id}')">✏️</button>
                <button class="al-btn al-btn-sm al-btn-approve" onclick="alGateApprove('${a.vt_id}')">✓</button>
                <button class="al-btn al-btn-sm al-btn-danger" onclick="alGateDiscard('${a.vt_id}')">✗</button>
            </div>
        </div>`).join('')}
    </div>`;
}

function alGateApprove(vtId) {
    fetch('/alphalab/distill/approve', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vt_ids: [vtId] })
    }).then(() => {
        AL.gateArtifacts = AL.gateArtifacts.filter(a => a.vt_id !== vtId);
        alLoadGate();
    });
}

function alGateDiscard(vtId) {
    fetch('/alphalab/distill/discard', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vt_ids: [vtId] })
    }).then(() => {
        AL.gateArtifacts = AL.gateArtifacts.filter(a => a.vt_id !== vtId);
        alLoadGate();
    });
}

function alApproveBatch(band) {
    const arts = AL.gateArtifacts.filter(a => (a.score?.P || 0) >= 4 && (a.score?.S || 0) >= 4);
    const ids = arts.map(a => a.vt_id);
    fetch('/alphalab/distill/approve', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vt_ids: ids })
    }).then(() => {
        AL.gateArtifacts = AL.gateArtifacts.filter(a => !ids.includes(a.vt_id));
        alLoadGate();
    });
}

function alDiscardBatch(band) {
    const arts = AL.gateArtifacts.filter(a => (a.score?.P || 0) < 3 && (a.score?.S || 0) < 3);
    const ids = arts.map(a => a.vt_id);
    fetch('/alphalab/distill/discard', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vt_ids: ids })
    }).then(() => {
        AL.gateArtifacts = AL.gateArtifacts.filter(a => !ids.includes(a.vt_id));
        alLoadGate();
    });
}

function alGateEdit(vtId) {
    const a = AL.gateArtifacts.find(x => x.vt_id === vtId);
    if (!a) return;
    const newP = prompt(`P (Prioridad) actual: ${a.score?.P}`, a.score?.P);
    const newS = prompt(`S (Señal) actual: ${a.score?.S}`, a.score?.S);
    const newD = prompt(`D (Distancia) actual: ${a.score?.D}`, a.score?.D);
    if (newP !== null) a.score.P = parseInt(newP);
    if (newS !== null) a.score.S = parseInt(newS);
    if (newD !== null) a.score.D = parseInt(newD);
    alLoadGate();
}

// ── Dropzone ──────────────────────────────────────────────
function alInitDropzone() {
    const dz = _id('al-dropzone');
    if (!dz) return;
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
    dz.addEventListener('drop', e => {
        e.preventDefault(); dz.classList.remove('dragover');
        const fi = _id('al-distill-file');
        if (fi && e.dataTransfer.files.length) { fi.files = e.dataTransfer.files; }
    });
    dz.addEventListener('click', () => { const fi = _id('al-distill-file'); if (fi) fi.click(); });
}

// ── Vitality Calc ─────────────────────────────────────────
function _calcVitality(idea) {
    const now = new Date();
    const last = idea.last_activity ? new Date(idea.last_activity) : new Date(idea.extraction_date || now);
    const days = Math.max(0, Math.floor((now - last) / 86400000));
    let state = 'ACTIVE';
    if (days > 90) state = 'ORPHANED';
    else if (days > 45) state = 'STALLED';
    else if (days > 14) state = 'DORMANT';
    return { state, days };
}

// ── Utilities ─────────────────────────────────────────────
function _id(id) { return document.getElementById(id); }
function _esc(s) { const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }
function _timeAgo(ts) {
    if (!ts) return '—';
    const d = new Date(ts);
    const now = new Date();
    const mins = Math.floor((now - d) / 60000);
    if (mins < 60) return `hace ${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `hace ${hrs}h`;
    const days = Math.floor(hrs / 24);
    return `hace ${days}d`;
}
