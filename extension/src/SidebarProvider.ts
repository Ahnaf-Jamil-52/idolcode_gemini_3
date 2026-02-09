import * as vscode from 'vscode';
import * as api from './api';
import { getSession, saveSession, updateIdol, clearSession, StoredSession, ViewState, getViewState, updateCurrentProblem, updateCurrentView } from './storage';
import { setupProblemWorkspace, getProblemFolderPath } from './utils/workspaceManager';
import { testRunner } from './runner/testRunner';
import { ProblemPanel } from './webview/ProblemPanel';


export class SidebarProvider implements vscode.WebviewViewProvider {
    private _view?: vscode.WebviewView;
    private _currentView: ViewState = 'wakeup';
    private _currentProblem?: api.ProblemContent;
    private _journey?: api.IdolJourney;
    private _comparison?: api.ComparisonData;
    private _userSolvedProblems: Set<string> = new Set();
    private _serverReady: boolean = false;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        private readonly _context: vscode.ExtensionContext
    ) { }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        // Start with wakeup view
        this._currentView = 'wakeup';

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(async (data) => {
            switch (data.type) {
                case 'login':
                    await this._handleLogin(data.handle);
                    break;
                case 'selectIdol':
                    await this._handleSelectIdol(data.handle);
                    break;
                case 'searchIdol':
                    await this._handleSearchIdol(data.query);
                    break;
                case 'solveProblem':
                    await this._handleSolveProblem(data.contestId, data.index);
                    break;
                case 'backToWorkspace':
                    this._currentView = 'workspace';
                    updateCurrentView(this._context, 'workspace');
                    this._updateWebview();
                    break;
                case 'changeIdol':
                    this.showIdolSelection();
                    break;
                case 'logout':
                    clearSession(this._context);
                    this._currentView = 'login';
                    this._updateWebview();
                    break;
                case 'ready':
                    await this._initializeServer();
                    break;
                case 'retryWakeup':
                    await this._initializeServer();
                    break;
                case 'runTests':
                    await this._handleRunTests();
                    break;
                case 'openProblemPanel':
                    this._openProblemInWebview();
                    break;
            }
        });
    }

    private async _initializeServer() {
        this._currentView = 'wakeup';
        this._updateWebview();

        const isReady = await api.wakeUpServer((status) => {
            this._sendMessage({ type: 'wakeupStatus', message: status });
        });

        if (isReady) {
            this._serverReady = true;
            // Check for existing session
            const session = getSession(this._context);
            if (session) {
                if (session.idolHandle) {
                    // Check for saved view state (e.g., problem-solving)
                    const savedViewState = getViewState(this._context);
                    if (savedViewState?.currentView === 'problem-solving' && savedViewState?.currentProblem) {
                        // Restore to problem-solving view
                        this._currentProblem = savedViewState.currentProblem;
                        this._currentView = 'problem-solving';
                    } else {
                        this._currentView = 'workspace';
                    }
                    await this._loadWorkspaceData();
                } else {
                    this._currentView = 'idol-selection';
                }
            } else {
                this._currentView = 'login';
            }
            this._updateWebview();
        } else {
            this._sendMessage({ type: 'wakeupFailed' });
        }
    }

    public refresh() {
        this._currentView = 'login';
        this._updateWebview();
    }

    public showIdolSelection() {
        this._currentView = 'idol-selection';
        updateCurrentView(this._context, 'idol-selection');
        this._updateWebview();
    }

    /**
     * Handle active file change - detect problem folder and auto-switch view
     */
    public async handleActiveFileChange(fileUri: vscode.Uri) {
        if (!this._serverReady) return;

        const filePath = fileUri.fsPath;

        // Check if we're in a problem folder (format: {contestId}{index}_{ProblemName})
        const match = filePath.match(/[/\\](\d+)([A-Z]\d?)[_]([^/\\]+)[/\\]/i);
        if (!match) return;

        const contestId = parseInt(match[1]);
        const index = match[2].toUpperCase();
        const problemId = `${contestId}${index}`;

        // If we're already viewing this problem, no need to reload
        if (this._currentProblem &&
            this._currentProblem.contestId === contestId &&
            this._currentProblem.index === index) {
            return;
        }

        // Try to load this problem
        try {
            const problem = await api.getProblemContent(contestId, index);
            this._currentProblem = problem;
            updateCurrentProblem(this._context, problem);
            this._currentView = 'problem-solving';
            this._updateWebview();
        } catch (error) {
            // Silently fail - user may be in a folder that looks like a problem but isn't
            console.log(`Could not load problem ${problemId}:`, error);
        }
    }

    /**
     * Open the current problem in a webview panel for viewing and test extraction
     */
    private _openProblemInWebview() {
        if (!this._currentProblem) {
            vscode.window.showWarningMessage('No problem selected');
            return;
        }

        const problemId = `${this._currentProblem.contestId}${this._currentProblem.index}`;
        const folderPath = getProblemFolderPath(problemId, this._currentProblem.name);

        ProblemPanel.createOrShow(
            this._extensionUri,
            this._currentProblem.contestId,
            this._currentProblem.index,
            this._currentProblem.name,
            folderPath || undefined
        );
    }

    private async _handleLogin(handle: string) {
        try {
            this._sendMessage({ type: 'loading', loading: true });
            const userInfo = await api.validateUser(handle);

            const session: StoredSession = {
                userHandle: handle,
                userInfo: userInfo
            };
            saveSession(this._context, session);

            this._currentView = 'idol-selection';
            this._sendMessage({ type: 'loading', loading: false });
            this._updateWebview();
            vscode.window.showInformationMessage(`Welcome, ${userInfo.handle}!`);
        } catch (error: any) {
            this._sendMessage({ type: 'loading', loading: false });
            this._sendMessage({
                type: 'error',
                message: error.response?.status === 404
                    ? 'Codeforces user not found'
                    : 'Error validating handle'
            });
        }
    }

    private async _handleSelectIdol(idolHandle: string) {
        try {
            this._sendMessage({ type: 'loading', loading: true });
            const session = getSession(this._context);
            if (!session) {
                throw new Error('No session found');
            }

            const comparison = await api.compareUsers(session.userHandle, idolHandle);
            updateIdol(this._context, idolHandle, comparison.idol);

            this._comparison = comparison;
            this._currentView = 'workspace';
            this._sendMessage({ type: 'loading', loading: false });
            await this._loadWorkspaceData();
            this._updateWebview();
        } catch (error: any) {
            this._sendMessage({ type: 'loading', loading: false });
            this._sendMessage({
                type: 'error',
                message: 'Error selecting idol: ' + (error.message || 'Unknown error')
            });
        }
    }

    private async _handleSearchIdol(query: string) {
        try {
            if (query.length < 2) {
                this._sendMessage({ type: 'searchResults', results: [] });
                return;
            }
            const results = await api.searchCoders(query);
            this._sendMessage({ type: 'searchResults', results });
        } catch (error) {
            this._sendMessage({ type: 'searchResults', results: [] });
        }
    }

    private async _handleSolveProblem(contestId: number, index: string) {
        try {
            this._sendMessage({ type: 'loading', loading: true });
            const problem = await api.getProblemContent(contestId, index);
            this._currentProblem = problem;

            // Set up the workspace with folder and files
            const problemId = `${contestId}${index}`;
            await setupProblemWorkspace(
                problemId,
                problem.name,
                problem.examples
            );

            // Persist current problem state for restoration on restart
            updateCurrentProblem(this._context, problem);

            this._currentView = 'problem-solving';
            this._sendMessage({ type: 'loading', loading: false });
            this._updateWebview();

            // Automatically open the problem in a webview panel
            const folderPath = getProblemFolderPath(problemId, problem.name);
            ProblemPanel.createOrShow(
                this._extensionUri,
                contestId,
                index,
                problem.name,
                folderPath || undefined
            );
        } catch (error: any) {
            this._sendMessage({ type: 'loading', loading: false });
            this._sendMessage({
                type: 'error',
                message: 'Error loading problem: ' + (error.message || 'Unknown error')
            });
        }
    }

    private async _handleRunTests() {
        if (!this._currentProblem) {
            this._sendMessage({
                type: 'testResults',
                success: false,
                error: 'No problem selected'
            });
            return;
        }

        const problemId = `${this._currentProblem.contestId}${this._currentProblem.index}`;
        const folderPath = getProblemFolderPath(problemId, this._currentProblem.name);

        if (!folderPath) {
            this._sendMessage({
                type: 'testResults',
                success: false,
                error: 'Please open a folder to run tests'
            });
            return;
        }

        // Send running state
        this._sendMessage({ type: 'testRunning', running: true });

        try {
            // Fallback fetch function to get tests from Codeforces if tests.json is missing
            const fetchTestsFallback = async () => {
                if (!this._currentProblem) return null;
                try {
                    const problem = await api.getProblemContent(
                        this._currentProblem.contestId,
                        this._currentProblem.index
                    );
                    return problem.examples || null;
                } catch (e) {
                    return null;
                }
            };

            const result = await testRunner.runAllTests(folderPath, fetchTestsFallback);
            this._sendMessage({
                type: 'testResults',
                ...result
            });
        } catch (error: any) {
            this._sendMessage({
                type: 'testResults',
                success: false,
                error: error.message || 'Unknown error running tests'
            });
        } finally {
            // Always ensure we send testRunning: false to prevent stuck state
            this._sendMessage({ type: 'testRunning', running: false });
        }
    }

    private async _loadWorkspaceData() {
        const session = getSession(this._context);
        if (!session?.idolHandle) return;

        try {
            // Load comparison if not already loaded
            if (!this._comparison) {
                this._comparison = await api.compareUsers(session.userHandle, session.idolHandle);
            }

            // Load journey
            this._journey = await api.getIdolJourney(session.idolHandle, 0, 100);

            // Load user's solved problems
            const solved = await api.getUserSolvedProblems(session.userHandle);
            this._userSolvedProblems = new Set(solved);
        } catch (error) {
            console.error('Error loading workspace data:', error);
        }
    }

    private _sendMessage(message: any) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }

    private _updateWebview() {
        if (this._view) {
            const session = getSession(this._context);
            this._sendMessage({
                type: 'updateState',
                view: this._currentView,
                session: session,
                comparison: this._comparison,
                journey: this._journey,
                problem: this._currentProblem,
                solvedProblems: Array.from(this._userSolvedProblems)
            });
        }
    }

    private _getHtmlForWebview(webview: vscode.Webview): string {
        const styleUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'webview', 'styles.css')
        );
        const scriptUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'webview', 'main.js')
        );

        const nonce = getNonce();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}'; img-src ${webview.cspSource} https:;">
    <link href="${styleUri}" rel="stylesheet">
    <title>Idolcode</title>
</head>
<body>
    <div id="app">
        <div id="loading-overlay" class="hidden">
            <div class="spinner"></div>
        </div>
        <div id="content"></div>
    </div>
    <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
    }
}

function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

