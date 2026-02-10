import * as vscode from 'vscode';
import * as api from './api';
import {
    StoredSession,
    saveSession, getSession, clearSession,
    updateIdol, saveViewState, getViewState,
    saveDashboardData, getDashboardData as getSavedDashboard
} from './storage';

export class SidebarProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'idolcode-sidebar';

    private _view?: vscode.WebviewView;
    private _serverReady = false;
    private _currentView = 'wakeup';
    private _busy = false;
    private _cancelled = false;

    // Dashboard data (mirrors frontend state)
    private _comparison: api.ComparisonData | null = null;
    private _recommendations: api.RecommendedProblem[] = [];
    private _recDescription = '';
    private _skillComparison: api.SkillComparisonData | null = null;
    private _history: api.HistoryItem[] = [];
    private _solvedProblems = new Set<string>();

    // Problem view data
    private _currentProblem: api.ProblemContent | null = null;
    private _testResults: api.TestResult[] = [];

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _context: vscode.ExtensionContext,
    ) {}

    /* ═══════════════════════════════════════════════════════════════
       Webview Lifecycle
       ═══════════════════════════════════════════════════════════════ */

    public resolveWebviewView(view: vscode.WebviewView) {
        this._view = view;
        view.webview.options = {
            enableScripts: true,
            localResourceRoots: [vscode.Uri.joinPath(this._extensionUri, 'webview')],
        };
        view.webview.html = this._getHtml(view.webview);

        view.webview.onDidReceiveMessage(async (msg) => {
            switch (msg.type) {
                case 'ready':           return this._init();
                case 'login':           return this._handleAuth(msg.handle, msg.password, false);
                case 'register':        return this._handleAuth(msg.handle, msg.password, true);
                case 'selectIdol':      return this._handleSelectIdol(msg.handle);
                case 'searchIdol':      return this._handleSearchIdol(msg.query);
                case 'refreshAll':      return this._loadDashboard(true);
                case 'refreshRecs':     return this._refreshRecs();
                case 'checkSubmissions':return this._checkSubmissions();
                case 'solveProblem':    return this._openProblem(msg.contestId, msg.index);
                case 'backToDashboard':
                    this._currentView = 'dashboard';
                    await saveViewState(this._context, { currentView: 'dashboard' });
                    this._updateWebview();
                    return;
                case 'runTests':        return this._runTests();
                case 'changeIdol':
                    this._currentView = 'idol-selection';
                    await saveViewState(this._context, { currentView: 'idol-selection' });
                    this._updateWebview();
                    return;
                case 'logout':
                    this._cancelled = true;
                    await clearSession(this._context);
                    this._resetData();
                    this._serverReady = false;
                    this._busy = false;
                    this._currentView = 'login';
                    this._updateWebview();
                    return;
                case 'customizeSkills':
                    return this._loadCustomSkills(msg.topics);
            }
        });
    }

    /* ═══════════════════════════════════════════════════════════════
       Init — show cached data instantly, fetch fresh in background
       ═══════════════════════════════════════════════════════════════ */

    private async _init() {
        console.log('[IdolCode] _init called, busy:', this._busy);
        if (this._busy) { this._updateWebview(); return; }
        this._busy = true;
        this._cancelled = false;

        try {
            const session = getSession(this._context);
            console.log('[IdolCode] session:', session ? `${session.userHandle}, idol: ${session.idolHandle}` : 'none');

            // ── Returning user with idol: show cached dashboard instantly ──
            if (session?.idolHandle) {
                const cached = getSavedDashboard(this._context);
                if (cached) {
                    this._comparison = cached.comparison;
                    this._recommendations = cached.recommendations;
                    this._recDescription = cached.recDescription;
                    this._skillComparison = cached.skillComparison;
                    this._history = cached.history;
                    this._solvedProblems = new Set(cached.solvedProblems);
                }
                const savedView = getViewState(this._context);
                if (savedView?.currentView === 'problem' && savedView.currentProblem) {
                    this._currentProblem = savedView.currentProblem;
                    this._currentView = 'problem';
                } else {
                    this._currentView = 'dashboard';
                }
                this._updateWebview();
                this._busy = false;

                // Background: wake server + refresh
                try {
                    if (!this._serverReady) {
                        const ready = await api.wakeUpServer();
                        if (this._cancelled) return;
                        if (ready) { this._serverReady = true; await this._loadDashboard(false); }
                    } else {
                        await this._loadDashboard(false);
                    }
                } catch (e) { console.error('[IdolCode] Background refresh error:', e); }
                return;
            }

            // ── No idol: need server for login/idol selection ──
            console.log('[IdolCode] No idol path, serverReady:', this._serverReady);
            if (!this._serverReady) {
                this._currentView = 'wakeup';
                this._updateWebview();
                try {
                    const ready = await api.wakeUpServer(s => {
                        console.log('[IdolCode] wakeup status:', s);
                        this._send({ type: 'wakeupStatus', message: s });
                    });
                    console.log('[IdolCode] wakeup result:', ready, 'cancelled:', this._cancelled);
                    if (this._cancelled) { this._busy = false; return; }
                    if (!ready) { this._send({ type: 'wakeupFailed' }); this._busy = false; return; }
                    this._serverReady = true;
                } catch (e) {
                    console.error('[IdolCode] Wakeup error:', e);
                    this._send({ type: 'wakeupFailed' });
                    this._busy = false;
                    return;
                }
            }

            const nextView = session ? 'idol-selection' : 'login';
            console.log('[IdolCode] Transitioning to:', nextView);
            this._currentView = nextView;
            this._updateWebview();
            this._busy = false;
        } catch (err) {
            console.error('[IdolCode] _init error:', err);
            try {
                const session = getSession(this._context);
                this._currentView = session?.idolHandle ? 'dashboard' : session ? 'idol-selection' : 'login';
                this._updateWebview();
            } catch (e2) { console.error('[IdolCode] _init recovery error:', e2); }
            this._busy = false;
        }
    }

    /* ═══════════════════════════════════════════════════════════════
       Auth
       ═══════════════════════════════════════════════════════════════ */

    private async _handleAuth(handle: string, password: string, isRegister: boolean) {
        this._busy = true;
        try {
            this._send({ type: 'loading', show: true });
            const result = isRegister
                ? await api.authRegister(handle, password)
                : await api.authLogin(handle, password);
            if (!result.success) throw new Error('Authentication failed');

            const session: StoredSession = {
                userHandle: result.handle,
                userInfo: { handle: result.handle, rating: result.rating, maxRating: result.maxRating, avatar: result.avatar },
            };
            await saveSession(this._context, session);

            if (result.idol) {
                await updateIdol(this._context, result.idol, {} as any);
                this._currentView = 'dashboard';
                await saveViewState(this._context, { currentView: 'dashboard' });
                this._send({ type: 'loading', show: false });
                this._updateWebview();
                this._busy = false;
                vscode.window.showInformationMessage(`Welcome${isRegister ? '' : ' back'}, ${result.handle}!`);
                await this._loadDashboard(false);
                return;
            }

            this._currentView = 'idol-selection';
            await saveViewState(this._context, { currentView: 'idol-selection' });
            this._send({ type: 'loading', show: false });
            this._updateWebview();
            this._busy = false;
            vscode.window.showInformationMessage(`Welcome, ${result.handle}! Choose your idol.`);
        } catch (err: any) {
            this._busy = false;
            this._send({ type: 'loading', show: false });
            this._send({ type: 'error', message: err.response?.data?.detail || (isRegister ? 'Registration failed' : 'Login failed') });
        }
    }

    /* ═══════════════════════════════════════════════════════════════
       Idol Selection
       ═══════════════════════════════════════════════════════════════ */

    private async _handleSelectIdol(idolHandle: string) {
        this._busy = true;
        try {
            this._send({ type: 'loading', show: true });
            const session = getSession(this._context);
            if (!session) throw new Error('No session');

            await updateIdol(this._context, idolHandle, {} as any);
            try { await api.saveIdol(session.userHandle, idolHandle); }
            catch (e) { console.error('Failed to save idol to backend:', e); }

            this._currentView = 'dashboard';
            await saveViewState(this._context, { currentView: 'dashboard' });
            this._send({ type: 'loading', show: false });
            this._updateWebview();
            this._busy = false;
            await this._loadDashboard(true);
        } catch (err: any) {
            this._busy = false;
            this._send({ type: 'loading', show: false });
            this._send({ type: 'error', message: 'Error selecting idol: ' + (err.message || 'Unknown') });
        }
    }

    private async _handleSearchIdol(query: string) {
        if (query.length < 2) { this._send({ type: 'searchResults', results: [] }); return; }
        try {
            const results = await api.searchCoders(query);
            this._send({ type: 'searchResults', results });
        } catch { this._send({ type: 'searchResults', results: [] }); }
    }

    /* ═══════════════════════════════════════════════════════════════
       Dashboard Data Loading
       ═══════════════════════════════════════════════════════════════ */

    private async _loadDashboard(refresh: boolean) {
        const session = getSession(this._context);
        if (!session?.idolHandle || !session.userHandle) return;
        if (this._cancelled) return;

        this._send({ type: 'dashLoading', loading: true });
        try {
            const data = await api.getDashboardData(session.userHandle, session.idolHandle, refresh);
            if (this._cancelled) return;

            if (data.comparison) {
                this._comparison = data.comparison;
                if (data.comparison.idol) await updateIdol(this._context, session.idolHandle, data.comparison.idol);
            }
            if (data.recommendations) {
                this._recommendations = data.recommendations.recommendations || [];
                this._recDescription = data.recommendations.description || '';
            }
            if (data.skillComparison) {
                this._skillComparison = data.skillComparison;
            }
            this._history = data.history || [];

            try {
                const solved = await api.getUserSolvedProblems(session.userHandle);
                if (!this._cancelled) this._solvedProblems = new Set(solved);
            } catch { /* ignore */ }

            if (!this._cancelled) {
                await saveDashboardData(this._context, {
                    comparison: this._comparison,
                    recommendations: this._recommendations,
                    recDescription: this._recDescription,
                    skillComparison: this._skillComparison,
                    history: this._history,
                    solvedProblems: Array.from(this._solvedProblems),
                });
            }
        } catch (err) {
            console.error('Error loading dashboard:', err);
        } finally {
            if (!this._cancelled) {
                this._send({ type: 'dashLoading', loading: false });
                this._updateWebview();
            }
        }
    }

    private async _refreshRecs() {
        const session = getSession(this._context);
        if (!session?.idolHandle || !session.userHandle) return;
        this._send({ type: 'dashLoading', loading: true });
        try {
            const recs = await api.getRecommendations(session.userHandle, session.idolHandle, true);
            this._recommendations = recs.recommendations || [];
            this._recDescription = recs.description || '';
        } catch (e) { console.error('Rec refresh error:', e); }
        finally { this._send({ type: 'dashLoading', loading: false }); this._updateWebview(); }
    }

    private async _loadCustomSkills(topics: string[]) {
        const session = getSession(this._context);
        if (!session?.idolHandle || !session.userHandle) return;
        this._send({ type: 'skillsLoading', loading: true });
        try {
            const skill = await api.getSkillComparison(session.userHandle, session.idolHandle, topics);
            this._skillComparison = skill;
            this._updateWebview();
        } catch (e) { console.error('Custom skills error:', e); }
        finally { this._send({ type: 'skillsLoading', loading: false }); }
    }

    /* ═══════════════════════════════════════════════════════════════
       Check CF Submissions
       ═══════════════════════════════════════════════════════════════ */

    private async _checkSubmissions() {
        const session = getSession(this._context);
        if (!session?.userHandle || this._recommendations.length === 0) return;

        this._send({ type: 'checkingSubmissions', checking: true });
        try {
            const ids = this._recommendations.map(r => r.problemId);
            const results = await api.checkSubmissions(session.userHandle, ids);
            const solvedList: api.RecommendedProblem[] = [];

            for (const [pid, info] of Object.entries(results)) {
                if (info.solved) {
                    this._solvedProblems.add(pid);
                    const rec = this._recommendations.find(r => r.problemId === pid);
                    if (rec) {
                        solvedList.push(rec);
                        api.recordProblemAttempt({
                            userHandle: session.userHandle,
                            idolHandle: session.idolHandle,
                            problemId: rec.problemId,
                            contestId: rec.contestId,
                            index: rec.index,
                            name: rec.name,
                            rating: rec.rating,
                            tags: rec.tags,
                            difficulty: rec.difficulty,
                            status: 'solved',
                        }).catch(() => {});
                    }
                }
            }

            if (solvedList.length > 0) {
                vscode.window.showInformationMessage(`Detected ${solvedList.length} solved problem(s)! Refreshing…`);
                await this._loadDashboard(true);
            } else {
                vscode.window.showInformationMessage('No new solutions detected.');
            }
        } catch {
            vscode.window.showErrorMessage('Failed to check submissions.');
        }
        this._send({ type: 'checkingSubmissions', checking: false });
    }

    /* ═══════════════════════════════════════════════════════════════
       Problem View
       ═══════════════════════════════════════════════════════════════ */

    private async _openProblem(contestId: number, index: string) {
        try {
            this._send({ type: 'loading', show: true });
            this._currentProblem = await api.getProblemContent(contestId, index);
            this._testResults = [];
            this._currentView = 'problem';
            await saveViewState(this._context, { currentView: 'problem', currentProblem: this._currentProblem });
            this._send({ type: 'loading', show: false });
            this._updateWebview();
        } catch {
            this._send({ type: 'loading', show: false });
            this._send({ type: 'error', message: 'Failed to load problem' });
        }
    }

    private async _runTests() {
        if (!this._currentProblem) return;
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            this._send({ type: 'error', message: 'Open a source file in the editor first' });
            return;
        }
        const code = editor.document.getText();
        const langMap: Record<string, string> = {
            python: 'python', javascript: 'javascript', typescript: 'javascript',
            cpp: 'cpp', c: 'cpp', java: 'java',
        };
        const lang = langMap[editor.document.languageId] || editor.document.languageId;

        this._send({ type: 'testsRunning', running: true });
        try {
            this._testResults = await api.testCode(code, lang, this._currentProblem.examples);
            this._send({ type: 'testResults', results: this._testResults });
        } catch (err: any) {
            this._send({ type: 'testResults', results: [], error: err.message || 'Test execution failed' });
        }
        this._send({ type: 'testsRunning', running: false });
    }

    /* ═══════════════════════════════════════════════════════════════
       Helpers
       ═══════════════════════════════════════════════════════════════ */

    private _resetData() {
        this._comparison = null;
        this._recommendations = [];
        this._recDescription = '';
        this._skillComparison = null;
        this._history = [];
        this._solvedProblems.clear();
        this._currentProblem = null;
        this._testResults = [];
    }

    private _send(msg: any) {
        this._view?.webview.postMessage(msg);
    }

    private _updateWebview() {
        if (!this._view) return;
        const session = getSession(this._context);
        this._send({
            type: 'updateState',
            view: this._currentView,
            session,
            comparison: this._comparison,
            recommendations: this._recommendations,
            recDescription: this._recDescription,
            skillComparison: this._skillComparison,
            history: this._history,
            solvedProblems: Array.from(this._solvedProblems),
            problem: this._currentProblem,
            testResults: this._testResults,
        });
    }

    private _getHtml(webview: vscode.Webview): string {
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'webview', 'styles.css'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'webview', 'main.js'));
        const nonce = getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'none';
                   style-src ${webview.cspSource} 'unsafe-inline' https://cdn.jsdelivr.net;
                   script-src 'nonce-${nonce}' https://cdn.jsdelivr.net;
                   font-src https://cdn.jsdelivr.net;
                   img-src ${webview.cspSource} https:;
                   connect-src http://localhost:* https://*;">
    <link href="${styleUri}" rel="stylesheet">
    <title>Idolcode</title>
</head>
<body>
    <div id="app">
        <div id="loading-overlay" class="hidden"><div class="spinner"></div></div>
        <div id="content">
            <div class="view-center">
                <div style="font-size:40px;margin-bottom:8px">🚀</div>
                <h2>Starting Idolcode</h2>
                <p id="wakeup-status" style="color:#9ca3af">Loading…</p>
                <div class="spinner" style="margin-top:16px"></div>
            </div>
        </div>
    </div>
    <script nonce="${nonce}">
        window.onerror = function(msg, src, line, col, err) {
            var el = document.getElementById('wakeup-status');
            if (el) el.textContent = 'Error: ' + msg;
            console.error('Webview error:', msg, src, line, col, err);
        };
    </script>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
    }
}

function getNonce() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let nonce = '';
    for (let i = 0; i < 32; i++) nonce += chars.charAt(Math.floor(Math.random() * chars.length));
    return nonce;
}

