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
exports.CodeforcesLoginPanel = void 0;
const vscode = __importStar(require("vscode"));
/**
 * CodeforcesLoginPanel - Opens Codeforces login page in a VS Code webview
 *
 * After user logs in, detects success and extracts session cookies
 * for use in authenticated API requests.
 */
class CodeforcesLoginPanel {
    constructor(panel, context) {
        this._disposables = [];
        this._panel = panel;
        this._context = context;
        // Listen for messages from the webview
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'loginSuccess':
                    // User successfully logged in
                    await this._handleLoginSuccess(message.cookies);
                    return;
                case 'loginCancelled':
                    this.dispose();
                    return;
                case 'cookiePasted':
                    await this._handleManualCookie(message.cookie);
                    return;
            }
        }, null, this._disposables);
        // Handle panel disposal
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Show the login page
        this._update();
    }
    /**
     * Open the login panel
     */
    static show(context) {
        return new Promise((resolve) => {
            const column = vscode.ViewColumn.Active;
            // If panel exists, reveal it
            if (CodeforcesLoginPanel.currentPanel) {
                CodeforcesLoginPanel.currentPanel._panel.reveal(column);
                CodeforcesLoginPanel.currentPanel._onLoginSuccess = (cookies) => resolve(cookies);
                return;
            }
            // Create new panel
            const panel = vscode.window.createWebviewPanel('codeforcesLogin', '🔐 Codeforces Login', column, {
                enableScripts: true,
                retainContextWhenHidden: true
            });
            const loginPanel = new CodeforcesLoginPanel(panel, context);
            loginPanel._onLoginSuccess = (cookies) => resolve(cookies);
            CodeforcesLoginPanel.currentPanel = loginPanel;
        });
    }
    /**
     * Handle successful login - store cookies
     */
    async _handleLoginSuccess(cookies) {
        // Store cookies in VS Code secrets (encrypted storage)
        await this._context.secrets.store('codeforces-cookies', cookies);
        vscode.window.showInformationMessage('✅ Successfully logged in to Codeforces!');
        if (this._onLoginSuccess) {
            this._onLoginSuccess(cookies);
        }
        this.dispose();
    }
    /**
     * Handle manually pasted cookie
     */
    async _handleManualCookie(cookie) {
        if (!cookie || cookie.trim().length === 0) {
            vscode.window.showErrorMessage('Cookie cannot be empty');
            return;
        }
        // Store the cookie
        await this._context.secrets.store('codeforces-cookies', cookie.trim());
        vscode.window.showInformationMessage('✅ Codeforces cookie saved!');
        if (this._onLoginSuccess) {
            this._onLoginSuccess(cookie.trim());
        }
        this.dispose();
    }
    /**
     * Get stored cookies
     */
    static async getCookies(context) {
        return await context.secrets.get('codeforces-cookies');
    }
    /**
     * Clear stored cookies (logout)
     */
    static async clearCookies(context) {
        await context.secrets.delete('codeforces-cookies');
        vscode.window.showInformationMessage('🚪 Logged out from Codeforces');
    }
    /**
     * Check if user is logged in
     */
    static async isLoggedIn(context) {
        const cookies = await context.secrets.get('codeforces-cookies');
        return cookies !== undefined && cookies.length > 0;
    }
    /**
     * Show the login UI
     */
    _update() {
        this._panel.webview.html = this._getHtmlContent();
    }
    _getHtmlContent() {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Codeforces Login</title>
                <style>
                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                    }
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                        min-height: 100vh;
                        color: #e4e4e7;
                        padding: 40px 20px;
                    }
                    .container {
                        max-width: 500px;
                        margin: 0 auto;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .header h1 {
                        font-size: 28px;
                        margin-bottom: 10px;
                        color: #06b6d4;
                    }
                    .header p {
                        color: #9ca3af;
                        font-size: 14px;
                    }
                    .card {
                        background: rgba(255,255,255,0.05);
                        border: 1px solid rgba(255,255,255,0.1);
                        border-radius: 16px;
                        padding: 30px;
                        margin-bottom: 20px;
                        backdrop-filter: blur(10px);
                    }
                    .card h2 {
                        font-size: 18px;
                        margin-bottom: 15px;
                        color: #f4f4f5;
                    }
                    .step {
                        display: flex;
                        align-items: flex-start;
                        gap: 15px;
                        margin-bottom: 15px;
                    }
                    .step-num {
                        background: #06b6d4;
                        color: #000;
                        width: 28px;
                        height: 28px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 14px;
                        flex-shrink: 0;
                    }
                    .step-text {
                        font-size: 14px;
                        line-height: 1.5;
                        color: #d4d4d8;
                    }
                    .step-text code {
                        background: rgba(6,182,212,0.2);
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-family: monospace;
                        color: #06b6d4;
                    }
                    .btn {
                        display: block;
                        width: 100%;
                        padding: 14px 20px;
                        border: none;
                        border-radius: 10px;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s;
                        text-decoration: none;
                        text-align: center;
                        margin-bottom: 12px;
                    }
                    .btn-primary {
                        background: linear-gradient(135deg, #06b6d4, #0891b2);
                        color: #000;
                    }
                    .btn-primary:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 20px rgba(6,182,212,0.4);
                    }
                    .btn-secondary {
                        background: rgba(255,255,255,0.1);
                        color: #e4e4e7;
                        border: 1px solid rgba(255,255,255,0.2);
                    }
                    .btn-secondary:hover {
                        background: rgba(255,255,255,0.15);
                    }
                    .divider {
                        display: flex;
                        align-items: center;
                        margin: 25px 0;
                        color: #6b7280;
                        font-size: 12px;
                    }
                    .divider::before, .divider::after {
                        content: '';
                        flex: 1;
                        height: 1px;
                        background: rgba(255,255,255,0.1);
                    }
                    .divider span {
                        padding: 0 15px;
                    }
                    textarea {
                        width: 100%;
                        height: 100px;
                        background: rgba(0,0,0,0.3);
                        border: 1px solid rgba(255,255,255,0.2);
                        border-radius: 8px;
                        padding: 12px;
                        color: #e4e4e7;
                        font-family: monospace;
                        font-size: 12px;
                        resize: vertical;
                        margin-bottom: 12px;
                    }
                    textarea:focus {
                        outline: none;
                        border-color: #06b6d4;
                    }
                    textarea::placeholder {
                        color: #6b7280;
                    }
                    .info-box {
                        background: rgba(6,182,212,0.1);
                        border: 1px solid rgba(6,182,212,0.3);
                        border-radius: 8px;
                        padding: 12px;
                        font-size: 12px;
                        color: #67e8f9;
                        margin-top: 15px;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 Codeforces Login</h1>
                        <p>Login to access problems without getting blocked</p>
                    </div>

                    <div class="card">
                        <h2>📋 Steps to Login</h2>
                        <div class="step">
                            <div class="step-num">1</div>
                            <div class="step-text">Click the button below to open Codeforces in your browser</div>
                        </div>
                        <div class="step">
                            <div class="step-num">2</div>
                            <div class="step-text">Login with your Codeforces account</div>
                        </div>
                        <div class="step">
                            <div class="step-num">3</div>
                            <div class="step-text">Open DevTools (F12) → Application → Cookies → <code>codeforces.com</code></div>
                        </div>
                        <div class="step">
                            <div class="step-num">4</div>
                            <div class="step-text">Copy the value of <code>JSESSIONID</code> and paste it below</div>
                        </div>

                        <a href="https://codeforces.com/enter" class="btn btn-primary" id="openBrowser">
                            🌐 Open Codeforces Login
                        </a>
                    </div>

                    <div class="card">
                        <h2>🍪 Paste Your Cookie</h2>
                        <textarea id="cookieInput" placeholder="Paste your JSESSIONID cookie value here...&#10;&#10;Example: 1234abcd5678efgh..."></textarea>
                        <button class="btn btn-primary" id="saveCookie">
                            💾 Save Cookie
                        </button>
                        
                        <div class="info-box">
                            💡 The cookie is stored securely and only used for Codeforces requests
                        </div>
                    </div>

                    <button class="btn btn-secondary" id="cancelBtn">
                        Cancel
                    </button>
                </div>

                <script>
                    const vscode = acquireVsCodeApi();

                    document.getElementById('openBrowser').addEventListener('click', (e) => {
                        e.preventDefault();
                        // Open in external browser
                        window.open('https://codeforces.com/enter', '_blank');
                    });

                    document.getElementById('saveCookie').addEventListener('click', () => {
                        const cookie = document.getElementById('cookieInput').value;
                        if (cookie.trim()) {
                            vscode.postMessage({
                                command: 'cookiePasted',
                                cookie: cookie.trim()
                            });
                        } else {
                            alert('Please paste your cookie first');
                        }
                    });

                    document.getElementById('cancelBtn').addEventListener('click', () => {
                        vscode.postMessage({ command: 'loginCancelled' });
                    });
                </script>
            </body>
            </html>
        `;
    }
    dispose() {
        CodeforcesLoginPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
}
exports.CodeforcesLoginPanel = CodeforcesLoginPanel;
//# sourceMappingURL=CodeforcesLoginPanel.js.map