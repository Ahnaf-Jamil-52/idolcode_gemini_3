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
exports.ProblemPanel = void 0;
const vscode = __importStar(require("vscode"));
const https = __importStar(require("https"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
/**
 * ProblemPanel - Opens Codeforces problem page in a webview and extracts test cases
 */
class ProblemPanel {
    constructor(panel, extensionUri, problemUrl, problemFolderPath, problemId) {
        this._disposables = [];
        this._panel = panel;
        this._problemFolderPath = problemFolderPath;
        this._problemId = problemId;
        // Listen for messages from the injected script
        this._panel.webview.onDidReceiveMessage(async (message) => {
            switch (message.command) {
                case 'saveTests':
                    await this._saveTestsToWorkspace(message.data);
                    return;
                case 'extractionError':
                    vscode.window.showWarningMessage(`Test extraction failed: ${message.error}`);
                    return;
            }
        }, null, this._disposables);
        // Handle panel disposal
        this._panel.onDidDispose(() => this.dispose(), null, this._disposables);
        // Load the problem page
        this._update(problemUrl);
    }
    /**
     * Create or show the problem panel
     */
    static createOrShow(extensionUri, contestId, index, problemName, problemFolderPath) {
        const problemUrl = `https://codeforces.com/contest/${contestId}/problem/${index}`;
        const problemId = `${contestId}${index}`;
        const column = vscode.ViewColumn.Two; // Open in side column
        // If panel exists, reveal and update
        if (ProblemPanel.currentPanel) {
            ProblemPanel.currentPanel._panel.reveal(column);
            ProblemPanel.currentPanel._problemFolderPath = problemFolderPath;
            ProblemPanel.currentPanel._problemId = problemId;
            ProblemPanel.currentPanel._update(problemUrl);
            return;
        }
        // Create new panel
        const panel = vscode.window.createWebviewPanel('idolcodeProblem', `Problem ${problemId}: ${problemName}`, column, {
            enableScripts: true, // Essential for extraction script
            retainContextWhenHidden: true
        });
        ProblemPanel.currentPanel = new ProblemPanel(panel, extensionUri, problemUrl, problemFolderPath, problemId);
    }
    /**
     * Fetch HTML and inject extraction script
     */
    async _update(url) {
        this._panel.webview.html = this._getLoadingHtml();
        try {
            const rawHtml = await this._fetchHtml(url);
            this._panel.webview.html = this._getWebviewContent(rawHtml, url);
        }
        catch (e) {
            this._panel.webview.html = this._getErrorHtml(e.message || 'Unknown error');
        }
    }
    /**
     * Fetch HTML using Node.js https module
     */
    _fetchHtml(url) {
        return new Promise((resolve, reject) => {
            const options = {
                headers: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
            };
            https.get(url, options, (response) => {
                // Handle redirects
                if (response.statusCode === 301 || response.statusCode === 302) {
                    const redirectUrl = response.headers.location;
                    if (redirectUrl) {
                        this._fetchHtml(redirectUrl).then(resolve).catch(reject);
                        return;
                    }
                }
                if (response.statusCode !== 200) {
                    reject(new Error(`HTTP ${response.statusCode}`));
                    return;
                }
                let data = '';
                response.on('data', (chunk) => { data += chunk; });
                response.on('end', () => { resolve(data); });
                response.on('error', reject);
            }).on('error', reject);
        });
    }
    /**
     * Inject base tag and extraction script into HTML
     */
    _getWebviewContent(html, baseUrl) {
        // Extract base URL for assets
        const urlObj = new URL(baseUrl);
        const baseHref = `${urlObj.protocol}//${urlObj.host}`;
        // Inject base tag for relative links (CSS, images, etc.)
        let modifiedHtml = html.replace('<head>', `<head><base href="${baseHref}/">`);
        // The extraction script that runs after page loads
        const extractorScript = `
            <script>
                (function() {
                    const vscode = acquireVsCodeApi();
                    
                    function extractTests() {
                        try {
                            const sampleDiv = document.querySelector('.sample-test');
                            if (!sampleDiv) {
                                console.log('No sample-test div found');
                                return;
                            }
                            
                            const inputs = [...sampleDiv.querySelectorAll('.input pre')];
                            const outputs = [...sampleDiv.querySelectorAll('.output pre')];
                            
                            const tests = inputs.map((inp, i) => {
                                // Handle <br> tags by replacing with newlines
                                const inputText = inp.innerText || inp.textContent || '';
                                const outputText = outputs[i] ? (outputs[i].innerText || outputs[i].textContent || '') : '';
                                
                                return {
                                    input: inputText.trim(),
                                    output: outputText.trim()
                                };
                            });
                            
                            if (tests.length > 0) {
                                vscode.postMessage({
                                    command: 'saveTests',
                                    data: tests
                                });
                            }
                        } catch(e) {
                            vscode.postMessage({
                                command: 'extractionError',
                                error: e.message
                            });
                        }
                    }
                    
                    // Run when DOM is ready
                    if (document.readyState === 'complete') {
                        extractTests();
                    } else {
                        window.addEventListener('load', extractTests);
                    }
                })();
            </script>
        `;
        // Inject script before closing body tag
        if (modifiedHtml.includes('</body>')) {
            modifiedHtml = modifiedHtml.replace('</body>', extractorScript + '</body>');
        }
        else {
            modifiedHtml += extractorScript;
        }
        return modifiedHtml;
    }
    /**
     * Save extracted tests to the problem folder
     */
    async _saveTestsToWorkspace(tests) {
        if (!tests || tests.length === 0) {
            return;
        }
        // Try to save to specific problem folder if provided
        if (this._problemFolderPath) {
            try {
                const testsPath = path.join(this._problemFolderPath, 'tests.json');
                fs.writeFileSync(testsPath, JSON.stringify(tests, null, 2));
                vscode.window.showInformationMessage(`✅ Extracted ${tests.length} test case(s) for problem ${this._problemId}`);
                return;
            }
            catch (e) {
                console.error('Failed to write to problem folder:', e);
            }
        }
        // Fallback: save to workspace root
        if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
            try {
                const workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
                const testsPath = path.join(workspaceFolder, `tests_${this._problemId}.json`);
                fs.writeFileSync(testsPath, JSON.stringify(tests, null, 2));
                vscode.window.showInformationMessage(`✅ Extracted ${tests.length} test case(s) - saved to ${path.basename(testsPath)}`);
            }
            catch (e) {
                vscode.window.showErrorMessage(`Failed to save tests: ${e.message}`);
            }
        }
        else {
            vscode.window.showWarningMessage(`Extracted ${tests.length} test case(s) but no workspace folder is open to save them.`);
        }
    }
    _getLoadingHtml() {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: #1e1e1e;
                        color: #fff;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    }
                    .loader {
                        text-align: center;
                    }
                    .spinner {
                        width: 50px;
                        height: 50px;
                        border: 4px solid #333;
                        border-top-color: #06b6d4;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                        margin: 0 auto 20px;
                    }
                    @keyframes spin {
                        to { transform: rotate(360deg); }
                    }
                </style>
            </head>
            <body>
                <div class="loader">
                    <div class="spinner"></div>
                    <p>Loading problem from Codeforces...</p>
                </div>
            </body>
            </html>
        `;
    }
    _getErrorHtml(error) {
        return `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background: #1e1e1e;
                        color: #fff;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    }
                    .error {
                        text-align: center;
                        max-width: 500px;
                        padding: 20px;
                    }
                    .error-icon {
                        font-size: 48px;
                        margin-bottom: 20px;
                    }
                    h2 { color: #f87171; }
                    p { color: #9ca3af; }
                </style>
            </head>
            <body>
                <div class="error">
                    <div class="error-icon">⚠️</div>
                    <h2>Failed to Load Problem</h2>
                    <p>${error}</p>
                    <p>Codeforces may be blocking requests. Try opening the problem directly in your browser.</p>
                </div>
            </body>
            </html>
        `;
    }
    dispose() {
        ProblemPanel.currentPanel = undefined;
        this._panel.dispose();
        while (this._disposables.length) {
            const x = this._disposables.pop();
            if (x) {
                x.dispose();
            }
        }
    }
}
exports.ProblemPanel = ProblemPanel;
//# sourceMappingURL=ProblemPanel.js.map