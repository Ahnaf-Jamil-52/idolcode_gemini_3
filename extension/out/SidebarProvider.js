"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.SidebarProvider = void 0;
const vscode = __importStar(require("vscode"));
const api = __importStar(require("./api"));
const storage_1 = require("./storage");
class SidebarProvider {
    constructor(_extensionUri, _context) {
        this._extensionUri = _extensionUri;
        this._context = _context;
        this._currentView = 'wakeup';
        this._userSolvedProblems = new Set();
        this._serverReady = false;
    }
    resolveWebviewView(webviewView, context, _token) {
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
                    this._updateWebview();
                    break;
                case 'changeIdol':
                    this.showIdolSelection();
                    break;
                case 'logout':
                    (0, storage_1.clearSession)(this._context);
                    this._currentView = 'login';
                    this._updateWebview();
                    break;
                case 'ready':
                    await this._initializeServer();
                    break;
                case 'retryWakeup':
                    await this._initializeServer();
                    break;
            }
        });
    }
    async _initializeServer() {
        this._currentView = 'wakeup';
        this._updateWebview();
        const isReady = await api.wakeUpServer((status) => {
            this._sendMessage({ type: 'wakeupStatus', message: status });
        });
        if (isReady) {
            this._serverReady = true;
            // Check for existing session
            const session = (0, storage_1.getSession)(this._context);
            if (session) {
                if (session.idolHandle) {
                    this._currentView = 'workspace';
                    await this._loadWorkspaceData();
                }
                else {
                    this._currentView = 'idol-selection';
                }
            }
            else {
                this._currentView = 'login';
            }
            this._updateWebview();
        }
        else {
            this._sendMessage({ type: 'wakeupFailed' });
        }
    }
    refresh() {
        this._currentView = 'login';
        this._updateWebview();
    }
    showIdolSelection() {
        this._currentView = 'idol-selection';
        this._updateWebview();
    }
    async _handleLogin(handle) {
        try {
            this._sendMessage({ type: 'loading', loading: true });
            const userInfo = await api.validateUser(handle);
            const session = {
                userHandle: handle,
                userInfo: userInfo
            };
            (0, storage_1.saveSession)(this._context, session);
            this._currentView = 'idol-selection';
            this._sendMessage({ type: 'loading', loading: false });
            this._updateWebview();
            vscode.window.showInformationMessage(`Welcome, ${userInfo.handle}!`);
        }
        catch (error) {
            this._sendMessage({ type: 'loading', loading: false });
            this._sendMessage({
                type: 'error',
                message: error.response?.status === 404
                    ? 'Codeforces user not found'
                    : 'Error validating handle'
            });
        }
    }
    async _handleSelectIdol(idolHandle) {
        try {
            this._sendMessage({ type: 'loading', loading: true });
            const session = (0, storage_1.getSession)(this._context);
            if (!session) {
                throw new Error('No session found');
            }
            const comparison = await api.compareUsers(session.userHandle, idolHandle);
            (0, storage_1.updateIdol)(this._context, idolHandle, comparison.idol);
            this._comparison = comparison;
            this._currentView = 'workspace';
            this._sendMessage({ type: 'loading', loading: false });
            await this._loadWorkspaceData();
            this._updateWebview();
        }
        catch (error) {
            this._sendMessage({ type: 'loading', loading: false });
            this._sendMessage({
                type: 'error',
                message: 'Error selecting idol: ' + (error.message || 'Unknown error')
            });
        }
    }
    async _handleSearchIdol(query) {
        try {
            if (query.length < 2) {
                this._sendMessage({ type: 'searchResults', results: [] });
                return;
            }
            const results = await api.searchCoders(query);
            this._sendMessage({ type: 'searchResults', results });
        }
        catch (error) {
            this._sendMessage({ type: 'searchResults', results: [] });
        }
    }
    async _handleSolveProblem(contestId, index) {
        try {
            this._sendMessage({ type: 'loading', loading: true });
            const problem = await api.getProblemContent(contestId, index);
            this._currentProblem = problem;
            this._currentView = 'problem-solving';
            this._sendMessage({ type: 'loading', loading: false });
            this._updateWebview();
        }
        catch (error) {
            this._sendMessage({ type: 'loading', loading: false });
            this._sendMessage({
                type: 'error',
                message: 'Error loading problem: ' + (error.message || 'Unknown error')
            });
        }
    }
    async _loadWorkspaceData() {
        const session = (0, storage_1.getSession)(this._context);
        if (!session?.idolHandle)
            return;
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
        }
        catch (error) {
            console.error('Error loading workspace data:', error);
        }
    }
    _sendMessage(message) {
        if (this._view) {
            this._view.webview.postMessage(message);
        }
    }
    _updateWebview() {
        if (this._view) {
            const session = (0, storage_1.getSession)(this._context);
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
    _getHtmlForWebview(webview) {
        const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'webview', 'styles.css'));
        const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'webview', 'main.js'));
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
exports.SidebarProvider = SidebarProvider;
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
//# sourceMappingURL=SidebarProvider.js.map