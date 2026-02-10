// ═══════════════════════════════════════════════════════════════════
//  Idolcode VS Code Extension — Webview Main
//  Full replica of the React frontend
// ═══════════════════════════════════════════════════════════════════

const vscode = acquireVsCodeApi();

/* ── State ── */
let state = {
    view: 'wakeup',
    session: null,
    comparison: null,
    recommendations: [],
    recDescription: '',
    skillComparison: null,
    history: [],
    solvedProblems: [],
    problem: null,
    testResults: [],
};
let searchResults = [];
let searchTimeout = null;
let expandedTopics = {};
let customizeOpen = false;
let selectedCustomTopics = [];
let dashLoading = false;
let skillsLoading = false;
let testsRunning = false;
let checkingSubmissions = false;

/* ── Constants (mirroring frontend) ── */
const DIFFICULTY_CONFIG = {
    Easy:   { bg: 'diff-easy',   badge: 'badge-easy',   label: 'Easy' },
    Medium: { bg: 'diff-medium', badge: 'badge-medium', label: 'Medium' },
    Hard:   { bg: 'diff-hard',   badge: 'badge-hard',   label: 'Hard' },
};
const TAG_COLORS = [
    'tag-blue', 'tag-purple', 'tag-green', 'tag-amber',
    'tag-rose', 'tag-cyan', 'tag-indigo', 'tag-lime',
];
const RATING_COLORS = [
    { min: 0,    cls: 'rating-gray' },
    { min: 1200, cls: 'rating-green' },
    { min: 1400, cls: 'rating-cyan' },
    { min: 1600, cls: 'rating-blue' },
    { min: 1900, cls: 'rating-purple' },
    { min: 2100, cls: 'rating-amber' },
    { min: 2400, cls: 'rating-red' },
];

function ratingColor(r) {
    if (!r) return 'rating-gray';
    for (let i = RATING_COLORS.length - 1; i >= 0; i--) {
        if (r >= RATING_COLORS[i].min) return RATING_COLORS[i].cls;
    }
    return 'rating-gray';
}

/* ── Message Handling ── */
window.addEventListener('message', e => {
    const m = e.data;
    console.log('[IdolCode Webview] received:', m.type, m.view || '');
    switch (m.type) {
        case 'updateState':
            state = { ...state, ...m };
            try { render(); } catch(err) { console.error('[IdolCode Webview] render error:', err); }
            break;
        case 'wakeupStatus':
            const el = document.getElementById('wakeup-status');
            if (el) el.textContent = m.message;
            break;
        case 'wakeupFailed':
            const wc = document.getElementById('content');
            if (wc) wc.innerHTML = renderWakeupFailed();
            break;
        case 'loading':
            toggleOverlay(m.show);
            break;
        case 'dashLoading':
            dashLoading = m.loading;
            break;
        case 'skillsLoading':
            skillsLoading = m.loading;
            break;
        case 'searchResults':
            searchResults = m.results || [];
            renderSearchResults();
            break;
        case 'error':
            showError(m.message);
            break;
        case 'testResults':
            state.testResults = m.results || [];
            testsRunning = false;
            renderTestResults(m.error);
            break;
        case 'testsRunning':
            testsRunning = m.running;
            const tb = document.getElementById('run-tests-btn');
            if (tb) { tb.disabled = m.running; tb.textContent = m.running ? 'Running…' : '▶ Run Tests'; }
            break;
        case 'checkingSubmissions':
            checkingSubmissions = m.checking;
            const cb = document.getElementById('check-btn');
            if (cb) { cb.disabled = m.checking; cb.textContent = m.checking ? 'Checking…' : '🔍 Check Submissions'; }
            break;
    }
});

function toggleOverlay(show) {
    const o = document.getElementById('loading-overlay');
    if (o) o.classList.toggle('hidden', !show);
}

function showError(msg) {
    const el = document.getElementById('error-msg');
    if (el) { el.textContent = msg; el.classList.remove('hidden'); setTimeout(() => el.classList.add('hidden'), 5000); }
    else { /* fallback: inject in content */ }
}

/* ── Render Router ── */
function render() {
    const c = document.getElementById('content');
    if (!c) { console.error('[IdolCode Webview] #content not found'); return; }
    console.log('[IdolCode Webview] render view:', state.view);
    try {
        switch (state.view) {
            case 'wakeup':        c.innerHTML = renderWakeup(); break;
            case 'login':         c.innerHTML = renderLogin(); attachLoginHandlers(); break;
            case 'idol-selection': c.innerHTML = renderIdolSelection(); attachIdolHandlers(); break;
            case 'dashboard':     c.innerHTML = renderDashboard(); attachDashboardHandlers(); break;
            case 'problem':       c.innerHTML = renderProblem(); attachProblemHandlers(); loadKatexAndRender(); break;
            default:              c.innerHTML = renderWakeup();
        }
    } catch(err) {
        console.error('[IdolCode Webview] render error in view', state.view, err);
        c.innerHTML = '<div class="view-center"><p style="color:#ef4444">Render error: ' + err.message + '</p></div>';
    }
}

/* ═══════════════════════════════════════════════════════════════════
   VIEW: Wakeup
   ═══════════════════════════════════════════════════════════════════ */

function renderWakeup() {
    return `
    <div class="view-center">
        <div class="wakeup-icon">🚀</div>
        <h2>Starting Idolcode</h2>
        <p id="wakeup-status" class="text-muted">Connecting to server…</p>
        <div class="spinner mt-16"></div>
    </div>`;
}

function renderWakeupFailed() {
    return `
    <div class="view-center">
        <div class="wakeup-icon">⚠️</div>
        <h2>Connection Failed</h2>
        <p class="text-muted">Could not connect to the Idolcode server.</p>
        <button class="btn btn-primary mt-16" onclick="vscode.postMessage({type:'ready'})">Retry</button>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════════
   VIEW: Login
   ═══════════════════════════════════════════════════════════════════ */

function renderLogin() {
    return `
    <div class="view-center">
        <div class="login-card glass-card">
            <div class="brand-header">
                <span class="brand-icon">⚡</span>
                <h1 class="brand-title">Idolcode</h1>
                <p class="text-muted">Train like your idol. Code like a champion.</p>
            </div>
            <div id="error-msg" class="error-banner hidden"></div>
            <form id="login-form" class="form-group">
                <div class="input-group">
                    <label>Codeforces Handle</label>
                    <input type="text" id="inp-handle" placeholder="Enter your handle" required autocomplete="off" />
                </div>
                <div class="input-group">
                    <label>Password</label>
                    <input type="password" id="inp-password" placeholder="Enter password" required />
                </div>
                <button type="submit" id="submit-btn" class="btn btn-primary btn-full">Login</button>
            </form>
            <p class="toggle-text">
                <span id="toggle-label">Don't have an account?</span>
                <a href="#" id="toggle-auth">Register</a>
            </p>
        </div>
    </div>`;
}

function attachLoginHandlers() {
    let isRegister = false;
    const form = document.getElementById('login-form');
    const btn = document.getElementById('submit-btn');
    const toggle = document.getElementById('toggle-auth');
    const lbl = document.getElementById('toggle-label');

    toggle?.addEventListener('click', e => {
        e.preventDefault();
        isRegister = !isRegister;
        btn.textContent = isRegister ? 'Register' : 'Login';
        lbl.textContent = isRegister ? 'Already have an account?' : "Don't have an account?";
        toggle.textContent = isRegister ? 'Login' : 'Register';
    });

    form?.addEventListener('submit', e => {
        e.preventDefault();
        const h = document.getElementById('inp-handle').value.trim();
        const p = document.getElementById('inp-password').value;
        if (!h || !p) return;
        vscode.postMessage({ type: isRegister ? 'register' : 'login', handle: h, password: p });
    });
}

/* ═══════════════════════════════════════════════════════════════════
   VIEW: Idol Selection
   ═══════════════════════════════════════════════════════════════════ */

function renderIdolSelection() {
    return `
    <div class="view-center">
        <div class="idol-card glass-card">
            <div class="brand-header">
                <span class="brand-icon">🏆</span>
                <h2>Choose Your Idol</h2>
                <p class="text-muted">Find a Codeforces coder to follow and learn from.</p>
            </div>
            <div id="error-msg" class="error-banner hidden"></div>
            <div class="input-group">
                <label>Search Coders</label>
                <input type="text" id="idol-search" placeholder="Type a handle…" autocomplete="off" />
            </div>
            <div id="search-results" class="search-results"></div>
            <div class="input-group mt-16">
                <label>Or enter directly</label>
                <div class="row-between">
                    <input type="text" id="idol-direct" placeholder="Handle" autocomplete="off" />
                    <button class="btn btn-primary ml-8" id="idol-go-btn">Go</button>
                </div>
            </div>
        </div>
    </div>`;
}

function attachIdolHandlers() {
    const inp = document.getElementById('idol-search');
    inp?.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            vscode.postMessage({ type: 'searchIdol', query: inp.value.trim() });
        }, 300);
    });

    document.getElementById('idol-go-btn')?.addEventListener('click', () => {
        const v = document.getElementById('idol-direct').value.trim();
        if (v) vscode.postMessage({ type: 'selectIdol', handle: v });
    });
    document.getElementById('idol-direct')?.addEventListener('keydown', e => {
        if (e.key === 'Enter') {
            const v = e.target.value.trim();
            if (v) vscode.postMessage({ type: 'selectIdol', handle: v });
        }
    });
}

function renderSearchResults() {
    const c = document.getElementById('search-results');
    if (!c) return;
    if (!searchResults.length) { c.innerHTML = ''; return; }
    c.innerHTML = searchResults.map(r => `
        <div class="search-result-item" data-handle="${esc(r.handle)}">
            <img class="avatar-sm" src="${esc(r.avatar || '')}" onerror="this.style.display='none'" />
            <div class="search-result-info">
                <span class="search-handle">${esc(r.handle)}</span>
                <span class="search-rating ${ratingColor(r.rating)}">${r.rating || '?'}</span>
                ${r.rank ? `<span class="search-rank">${esc(r.rank)}</span>` : ''}
            </div>
        </div>
    `).join('');
    c.querySelectorAll('.search-result-item').forEach(el => {
        el.addEventListener('click', () => vscode.postMessage({ type: 'selectIdol', handle: el.dataset.handle }));
    });
}

/* ═══════════════════════════════════════════════════════════════════
   VIEW: Dashboard (replicas ProblemCards, SkillMap, History, etc.)
   ═══════════════════════════════════════════════════════════════════ */

function renderDashboard() {
    const s = state.session;
    const cmp = state.comparison;
    const user = cmp?.user || s?.userInfo || {};
    const idol = cmp?.idol || {};
    const handle = s?.userHandle || '?';
    const idolHandle = s?.idolHandle || '?';

    return `
    <div class="dashboard">
        <!-- Header -->
        <div class="dash-header">
            <div class="dash-user">
                ${user.avatar ? `<img class="avatar-md" src="${esc(user.avatar)}" onerror="this.style.display='none'" />` : ''}
                <div>
                    <h2 class="dash-handle">${esc(handle)}</h2>
                    <span class="text-muted text-sm">Following: <strong>${esc(idolHandle)}</strong></span>
                </div>
            </div>
            <div class="dash-actions">
                <button class="btn-icon" id="refresh-btn" title="Refresh">🔄</button>
                <button class="btn-icon" id="change-idol-btn" title="Change Idol">🔁</button>
                <button class="btn-icon" id="logout-btn" title="Logout">🚪</button>
            </div>
        </div>

        ${renderProgressSection(user, idol, idolHandle)}
        ${renderStatCards(user, idol)}
        ${renderProblemCards()}
        ${renderSkillMap()}
        ${renderHistorySection()}
    </div>`;
}

/* ── Progress Section ── */
function renderProgressSection(user, idol, idolHandle) {
    const ur = user.rating || 0;
    const ir = idol.rating || 1;
    const pct = Math.min(100, Math.round((ur / ir) * 100));
    const surpassed = ur >= ir && ir > 0;
    return `
    <div class="glass-card progress-card">
        <div class="row-between">
            <span class="text-sm text-muted">Following <strong class="text-cyan">${esc(idolHandle)}</strong></span>
            <span class="text-sm ${surpassed ? 'text-green' : 'text-amber'}">${surpassed ? '🎉 Surpassed!' : pct + '%'}</span>
        </div>
        <div class="progress-bar mt-8">
            <div class="progress-fill ${surpassed ? 'progress-green' : 'progress-cyan'}" style="width:${pct}%"></div>
        </div>
    </div>`;
}

/* ── Stat Cards (4 cards: Rating, Max Rating, Solved, Wins) ── */
function renderStatCards(user, idol) {
    const stats = [
        { label: 'Rating',    icon: '⭐', uv: user.rating || 0,    iv: idol.rating || 0 },
        { label: 'Max Rating',icon: '🏅', uv: user.maxRating || 0, iv: idol.maxRating || 0 },
        { label: 'Solved',    icon: '✅', uv: user.problemsSolved ?? user.solved ?? 0, iv: idol.problemsSolved ?? idol.solved ?? 0 },
        { label: 'Wins',      icon: '🏆', uv: user.contestsWon ?? user.wins ?? 0,    iv: idol.contestsWon ?? idol.wins ?? 0 },
    ];
    return `
    <div class="stat-grid">
        ${stats.map(s => {
            const diff = s.uv - s.iv;
            const diffCls = diff > 0 ? 'diff-positive' : diff < 0 ? 'diff-negative' : 'diff-neutral';
            const diffStr = diff > 0 ? `+${diff}` : `${diff}`;
            return `
            <div class="glass-card stat-card">
                <div class="stat-header">
                    <span class="stat-icon">${s.icon}</span>
                    <span class="stat-label">${s.label}</span>
                </div>
                <div class="stat-values">
                    <div class="stat-val">
                        <span class="text-xs text-muted">You</span>
                        <span class="stat-num text-cyan">${s.uv}</span>
                    </div>
                    <div class="stat-val">
                        <span class="text-xs text-muted">Idol</span>
                        <span class="stat-num text-purple">${s.iv}</span>
                    </div>
                </div>
                <div class="stat-diff ${diffCls}">${diffStr}</div>
            </div>`;
        }).join('')}
    </div>`;
}

/* ── Problem Cards (roadmap) ── */
function renderProblemCards() {
    const recs = state.recommendations || [];
    const desc = state.recDescription || '';
    const solved = new Set(state.solvedProblems || []);

    if (!recs.length && !dashLoading) return '';

    const cards = recs.filter(r => !solved.has(r.problemId));
    const groupMap = { Easy: [], Medium: [], Hard: [] };
    cards.forEach(c => {
        const d = c.difficulty || 'Medium';
        (groupMap[d] || groupMap.Medium).push(c);
    });

    return `
    <div class="section">
        <div class="section-header">
            <h3>📋 Your Roadmap</h3>
            <div class="row-gap-8">
                <span class="ai-badge">AI Personalized</span>
                <button class="btn btn-sm btn-outline" id="refresh-recs-btn">🔄 Refresh</button>
            </div>
        </div>
        ${desc ? `<p class="text-muted text-sm mb-12">${esc(desc)}</p>` : ''}

        <div class="difficulty-groups">
            ${['Easy', 'Medium', 'Hard'].map(diff => {
                const dCards = groupMap[diff];
                if (!dCards.length) return '';
                const cfg = DIFFICULTY_CONFIG[diff];
                return `
                <div class="diff-group">
                    <div class="diff-group-header">
                        <span class="diff-label ${cfg.badge}">${cfg.label}</span>
                        <span class="text-muted text-xs">${dCards.length} problems</span>
                    </div>
                    <div class="problem-grid">
                        ${dCards.map(c => renderProblemCard(c, cfg)).join('')}
                    </div>
                </div>`;
            }).join('')}
        </div>

        <button class="btn btn-outline btn-full mt-12" id="check-btn">${checkingSubmissions ? 'Checking…' : '🔍 Check Submissions'}</button>
    </div>`;
}

function renderProblemCard(c, cfg) {
    const tagHtml = (c.tags || []).slice(0, 3).map((t, i) =>
        `<span class="tag ${TAG_COLORS[i % TAG_COLORS.length]}">${esc(t)}</span>`
    ).join('');
    return `
    <div class="glass-card problem-card ${cfg.bg}">
        <div class="problem-card-top">
            <span class="problem-id">${esc(c.contestId + '' + c.index)}</span>
            <span class="badge ${ratingColor(c.rating)}">${c.rating || '?'}</span>
        </div>
        <h4 class="problem-name" title="${esc(c.name)}">${esc(c.name)}</h4>
        <div class="tag-list">${tagHtml}</div>
        <div class="problem-card-actions">
            <button class="btn btn-sm btn-primary solve-btn" data-cid="${c.contestId}" data-idx="${esc(c.index)}">Solve</button>
            <a class="btn btn-sm btn-outline" href="https://codeforces.com/problemset/problem/${c.contestId}/${c.index}" target="_blank">CF ↗</a>
        </div>
    </div>`;
}

/* ── Skill Map ── */
function renderSkillMap() {
    const sk = state.skillComparison;
    if (!sk) return '';

    const topics = sk.topicStats || sk.topics || [];
    const weak = sk.weakestTopics || [];
    const allTopics = sk.allTopics || [];
    const maxVal = Math.max(...topics.map(t => Math.max(t.userCount || 0, t.idolCount || 0)), 1);

    return `
    <div class="section">
        <div class="section-header">
            <h3>📊 Skill Map</h3>
            <button class="btn btn-sm btn-outline" id="customize-btn">⚙ Customize</button>
        </div>

        ${customizeOpen ? renderCustomizeOverlay(allTopics) : ''}

        <!-- Bar Chart -->
        <div class="bar-chart">
            ${topics.map(t => {
                const uw = Math.round((t.userCount || 0) / maxVal * 100);
                const iw = Math.round((t.idolCount || 0) / maxVal * 100);
                const ahead = (t.userCount || 0) >= (t.idolCount || 0);
                const gap = (t.idolCount || 0) - (t.userCount || 0);
                return `
                <div class="bar-row">
                    <div class="bar-label" title="${esc(t.topic)}">${esc(truncate(t.topic, 18))}</div>
                    <div class="bar-tracks">
                        <div class="bar-track">
                            <div class="bar-fill ${ahead ? 'bar-green' : 'bar-cyan'}" style="width:${uw}%"></div>
                            <span class="bar-val">${t.userCount || 0}</span>
                        </div>
                        <div class="bar-track">
                            <div class="bar-fill bar-purple" style="width:${iw}%"></div>
                            <span class="bar-val">${t.idolCount || 0}</span>
                        </div>
                    </div>
                    ${gap > 0 ? `<span class="gap-badge">-${gap}</span>` : gap < 0 ? `<span class="gap-badge gap-positive">+${Math.abs(gap)}</span>` : ''}
                </div>`;
            }).join('')}
        </div>
        <div class="chart-legend">
            <span class="legend-item"><i class="legend-dot dot-cyan"></i> You</span>
            <span class="legend-item"><i class="legend-dot dot-purple"></i> Idol</span>
            <span class="legend-item"><i class="legend-dot dot-green"></i> Ahead</span>
        </div>

        <!-- Focus Areas -->
        ${weak.length ? `
        <div class="focus-areas mt-16">
            <h4>🎯 Focus Areas</h4>
            ${weak.map((w, wi) => `
                <div class="focus-topic glass-card">
                    <div class="focus-topic-header" data-topic-idx="${wi}">
                        <span class="focus-name">${esc(w.topic)}</span>
                        <span class="focus-gap">Gap: ${w.gap || '?'}</span>
                        <span class="focus-toggle">${expandedTopics[wi] ? '▼' : '▶'}</span>
                    </div>
                    ${expandedTopics[wi] && w.problems?.length ? `
                    <div class="focus-problems">
                        ${w.problems.map(p => `
                            <div class="focus-problem-row">
                                <span class="text-sm">${esc(p.name)}</span>
                                <span class="badge ${ratingColor(p.rating)} text-xs">${p.rating || '?'}</span>
                                ${p.contestId && p.index ? `<button class="btn btn-xs btn-primary solve-focus-btn" data-cid="${p.contestId}" data-idx="${esc(p.index)}">Solve</button>` : ''}
                                ${p.url ? `<a class="btn btn-xs btn-outline" href="${esc(p.url)}" target="_blank">↗</a>` : ''}
                            </div>
                        `).join('')}
                    </div>` : ''}
                </div>
            `).join('')}
        </div>` : ''}
    </div>`;
}

function renderCustomizeOverlay(allTopics) {
    return `
    <div class="customize-overlay glass-card">
        <div class="row-between mb-12">
            <h4>Select 3 Topics</h4>
            <button class="btn-icon" id="close-customize">✕</button>
        </div>
        <div class="topic-grid">
            ${allTopics.map(t => `
                <label class="topic-chip ${selectedCustomTopics.includes(t) ? 'topic-selected' : ''}" data-topic="${esc(t)}">
                    <input type="checkbox" class="topic-cb" value="${esc(t)}" ${selectedCustomTopics.includes(t) ? 'checked' : ''} />
                    ${esc(t)}
                </label>
            `).join('')}
        </div>
        <button class="btn btn-primary btn-full mt-12" id="apply-custom-btn" ${selectedCustomTopics.length !== 3 ? 'disabled' : ''}>
            Apply (${selectedCustomTopics.length}/3)
        </button>
    </div>`;
}

/* ── Problem History ── */
function renderHistorySection() {
    const hist = state.history || [];
    if (!hist.length) return '';

    const STATUS = {
        solved:    { icon: '✅', cls: 'status-solved',    label: 'Solved' },
        failed:    { icon: '❌', cls: 'status-failed',    label: 'Failed' },
        attempted: { icon: '⏳', cls: 'status-attempted', label: 'Attempted' },
    };

    return `
    <div class="section">
        <div class="section-header">
            <h3>📜 Problem History</h3>
            <span class="text-muted text-xs">${hist.length} entries</span>
        </div>
        <div class="history-list">
            ${hist.map(h => {
                const st = STATUS[h.status] || STATUS.attempted;
                const diff = DIFFICULTY_CONFIG[h.difficulty] || DIFFICULTY_CONFIG.Medium;
                const tagHtml = (h.tags || []).slice(0, 2).map((t, i) =>
                    `<span class="tag tag-sm ${TAG_COLORS[i % TAG_COLORS.length]}">${esc(t)}</span>`
                ).join('');
                return `
                <div class="glass-card history-row">
                    <div class="history-left">
                        <span class="history-status-icon" title="${st.label}">${st.icon}</span>
                        <div class="history-info">
                            <div class="history-name">${esc(h.name || 'Problem')}</div>
                            <div class="history-meta">
                                <span class="text-xs text-muted">${esc(h.problemId || '')}</span>
                                <span class="badge ${ratingColor(h.rating)} text-xs">${h.rating || '?'}</span>
                                <span class="badge ${diff.badge} text-xs">${diff.label}</span>
                            </div>
                            <div class="tag-list mt-4">${tagHtml}</div>
                        </div>
                    </div>
                    <div class="history-right">
                        <span class="badge ${st.cls} text-xs">${st.label}</span>
                        <span class="text-xs text-muted">${timeAgo(h.attemptedAt)}</span>
                        <div class="history-actions">
                            ${h.contestId && h.index ? `<button class="btn btn-xs btn-primary solve-hist-btn" data-cid="${h.contestId}" data-idx="${esc(h.index)}">${h.status === 'solved' ? 'Retry' : 'Continue'}</button>` : ''}
                            ${h.contestId && h.index ? `<a class="btn btn-xs btn-outline" href="https://codeforces.com/problemset/problem/${h.contestId}/${h.index}" target="_blank">↗</a>` : ''}
                        </div>
                    </div>
                </div>`;
            }).join('')}
        </div>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════════
   VIEW: Problem
   ═══════════════════════════════════════════════════════════════════ */

function renderProblem() {
    const p = state.problem;
    if (!p) return '<div class="view-center"><p class="text-muted">No problem loaded</p></div>';

    const examplesHtml = (p.examples || []).map((ex, i) => `
        <div class="example-block glass-card">
            <h4>Example ${i + 1}</h4>
            <div class="example-io">
                <div class="io-col">
                    <div class="io-label">Input</div>
                    <pre class="io-pre">${esc(ex.input)}</pre>
                </div>
                <div class="io-col">
                    <div class="io-label">Output</div>
                    <pre class="io-pre">${esc(ex.output)}</pre>
                </div>
            </div>
        </div>
    `).join('');

    const tagsHtml = (p.tags || []).map((t, i) =>
        `<span class="tag ${TAG_COLORS[i % TAG_COLORS.length]}">${esc(t)}</span>`
    ).join('');

    return `
    <div class="problem-view">
        <button class="btn btn-sm btn-outline mb-12" id="back-btn">← Dashboard</button>

        <div class="glass-card problem-header-card">
            <h2 class="problem-title">${esc(p.name || 'Problem')}</h2>
            <div class="problem-meta">
                ${p.rating ? `<span class="badge ${ratingColor(p.rating)}">${p.rating}</span>` : ''}
                ${p.timeLimit ? `<span class="badge badge-outline">⏱ ${esc(p.timeLimit)}</span>` : ''}
                ${p.memoryLimit ? `<span class="badge badge-outline">💾 ${esc(p.memoryLimit)}</span>` : ''}
            </div>
            <div class="tag-list mt-8">${tagsHtml}</div>
        </div>

        <div class="glass-card problem-statement latex-content">
            ${p.statement || ''}
        </div>

        ${p.inputSpec ? `<div class="glass-card"><h4>Input</h4><div class="latex-content">${p.inputSpec}</div></div>` : ''}
        ${p.outputSpec ? `<div class="glass-card"><h4>Output</h4><div class="latex-content">${p.outputSpec}</div></div>` : ''}

        ${examplesHtml}

        ${p.note ? `<div class="glass-card"><h4>Note</h4><div class="latex-content">${p.note}</div></div>` : ''}

        <button class="btn btn-primary btn-full mt-12" id="run-tests-btn">${testsRunning ? 'Running…' : '▶ Run Tests'}</button>
        <div id="test-results-area"></div>
    </div>`;
}

function renderTestResults(errorMsg) {
    const area = document.getElementById('test-results-area');
    if (!area) return;
    if (errorMsg) {
        area.innerHTML = `<div class="glass-card test-error mt-12"><p class="text-red">❌ ${esc(errorMsg)}</p></div>`;
        return;
    }
    const results = state.testResults || [];
    if (!results.length) { area.innerHTML = ''; return; }
    area.innerHTML = `
    <div class="test-results mt-12">
        ${results.map((r, i) => `
            <div class="glass-card test-case ${r.passed ? 'test-pass' : 'test-fail'}">
                <div class="test-case-header">
                    <span>${r.passed ? '✅' : '❌'} Test ${i + 1}</span>
                    ${r.time != null ? `<span class="text-xs text-muted">${r.time}ms</span>` : ''}
                </div>
                ${!r.passed ? `
                <div class="test-detail">
                    <div><strong>Expected:</strong> <pre class="io-pre-sm">${esc(r.expected || '')}</pre></div>
                    <div><strong>Got:</strong> <pre class="io-pre-sm">${esc(r.actual || '')}</pre></div>
                </div>` : ''}
            </div>
        `).join('')}
    </div>`;
}

/* ── Lazy KaTeX loader ── */
let katexLoaded = false;
let katexLoading = false;
function loadKatexAndRender() {
    if (katexLoaded) { renderLatex(); return; }
    if (katexLoading) return;
    katexLoading = true;
    // Load CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css';
    document.head.appendChild(link);
    // Load JS
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js';
    script.onload = () => { katexLoaded = true; renderLatex(); };
    script.onerror = () => { katexLoading = false; console.warn('KaTeX CDN failed to load'); };
    document.head.appendChild(script);
}

function renderLatex() {
    if (typeof katex === 'undefined') return;
    document.querySelectorAll('.latex-content').forEach(el => {
        let html = el.innerHTML;
        // $$...$$ (display)
        html = html.replace(/\$\$([\s\S]*?)\$\$/g, (_, tex) => {
            try { return katex.renderToString(tex.trim(), { displayMode: true, throwOnError: false }); }
            catch { return tex; }
        });
        // $...$ (inline)
        html = html.replace(/\$([^\$]+?)\$/g, (_, tex) => {
            try { return katex.renderToString(tex.trim(), { displayMode: false, throwOnError: false }); }
            catch { return tex; }
        });
        el.innerHTML = html;
    });
}

/* ═══════════════════════════════════════════════════════════════════
   Dashboard Event Handlers
   ═══════════════════════════════════════════════════════════════════ */

function attachDashboardHandlers() {
    document.getElementById('refresh-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'refreshAll' }));
    document.getElementById('change-idol-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'changeIdol' }));
    document.getElementById('logout-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'logout' }));
    document.getElementById('refresh-recs-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'refreshRecs' }));
    document.getElementById('check-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'checkSubmissions' }));

    // Solve buttons (problem cards)
    document.querySelectorAll('.solve-btn').forEach(b => {
        b.addEventListener('click', () => {
            vscode.postMessage({ type: 'solveProblem', contestId: parseInt(b.dataset.cid), index: b.dataset.idx });
        });
    });

    // Solve buttons (focus areas)
    document.querySelectorAll('.solve-focus-btn').forEach(b => {
        b.addEventListener('click', () => {
            vscode.postMessage({ type: 'solveProblem', contestId: parseInt(b.dataset.cid), index: b.dataset.idx });
        });
    });

    // Solve buttons (history)
    document.querySelectorAll('.solve-hist-btn').forEach(b => {
        b.addEventListener('click', () => {
            vscode.postMessage({ type: 'solveProblem', contestId: parseInt(b.dataset.cid), index: b.dataset.idx });
        });
    });

    // Focus area expand/collapse
    document.querySelectorAll('.focus-topic-header').forEach(el => {
        el.addEventListener('click', () => {
            const idx = el.dataset.topicIdx;
            expandedTopics[idx] = !expandedTopics[idx];
            render();
        });
    });

    // Customize skills
    document.getElementById('customize-btn')?.addEventListener('click', () => {
        customizeOpen = !customizeOpen;
        if (customizeOpen) selectedCustomTopics = [];
        render();
    });
    document.getElementById('close-customize')?.addEventListener('click', () => {
        customizeOpen = false;
        render();
    });

    // Topic checkboxes
    document.querySelectorAll('.topic-cb').forEach(cb => {
        cb.addEventListener('change', () => {
            const val = cb.value;
            if (cb.checked) {
                if (selectedCustomTopics.length < 3) selectedCustomTopics.push(val);
                else { cb.checked = false; return; }
            } else {
                selectedCustomTopics = selectedCustomTopics.filter(t => t !== val);
            }
            render();
        });
    });

    // Apply custom topics
    document.getElementById('apply-custom-btn')?.addEventListener('click', () => {
        if (selectedCustomTopics.length === 3) {
            customizeOpen = false;
            vscode.postMessage({ type: 'customizeSkills', topics: selectedCustomTopics });
        }
    });
}

function attachProblemHandlers() {
    document.getElementById('back-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'backToDashboard' }));
    document.getElementById('run-tests-btn')?.addEventListener('click', () => vscode.postMessage({ type: 'runTests' }));
}

/* ═══════════════════════════════════════════════════════════════════
   Utilities
   ═══════════════════════════════════════════════════════════════════ */

function esc(s) {
    if (s == null) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function truncate(s, n) {
    return s && s.length > n ? s.slice(0, n) + '…' : (s || '');
}

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return mins + 'm ago';
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return hrs + 'h ago';
    const days = Math.floor(hrs / 24);
    if (days < 30) return days + 'd ago';
    return Math.floor(days / 30) + 'mo ago';
}

/* ── Boot ── */
console.log('[IdolCode Webview] booting, sending ready');
vscode.postMessage({ type: 'ready' });
