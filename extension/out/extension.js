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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const SidebarProvider_1 = require("./SidebarProvider");
const storage_1 = require("./storage");
const CoachClient_1 = require("./utils/CoachClient");
// ==================== COACH TELEMETRY STATE ====================
let deletionCount = 0;
let lastKeystrokeTime = Date.now();
let idleTimer;
let telemetryInterval;
function activate(context) {
    console.log('Idolcode extension is now active!');
    // Initialize CoachClient with user handle if available
    const session = (0, storage_1.getSession)(context);
    if (session?.userHandle) {
        CoachClient_1.CoachClient.setUserHandle(session.userHandle);
    }
    // Create sidebar provider
    const sidebarProvider = new SidebarProvider_1.SidebarProvider(context.extensionUri, context);
    // Register the webview view provider
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('idolcode-panel', sidebarProvider));
    // Track active editor changes to auto-detect problem folders
    context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor((editor) => {
        if (editor) {
            sidebarProvider.handleActiveFileChange(editor.document.uri);
        }
    }));
    // ==================== COACH TELEMETRY: TOUCH SENSORS ====================
    // 1. Typing/Deletion Listener - detect frustration (rage deleting)
    context.subscriptions.push(vscode.workspace.onDidChangeTextDocument((event) => {
        // Reset idle timer on any keystroke
        lastKeystrokeTime = Date.now();
        resetIdleTimer();
        // Calculate deletions
        event.contentChanges.forEach(change => {
            if (change.text === '' && change.rangeLength > 0) {
                // This was a deletion
                deletionCount += change.rangeLength;
            }
        });
    }));
    // 2. Windowed Analysis - check every 60 seconds
    telemetryInterval = setInterval(() => {
        if (deletionCount > 50) {
            // 🚨 TRIGGER: High deletion rate = frustration
            CoachClient_1.CoachClient.sendSignal('frustration_detected', deletionCount, {
                context: 'high_deletion_rate',
                window_seconds: 60
            });
            console.log(`🔥 Frustration detected: ${deletionCount} chars deleted in last minute`);
        }
        // Reset counter for next window
        deletionCount = 0;
    }, 60000); // Every minute
    // 3. Start idle detection
    resetIdleTimer();
    // ==================== EXISTING COMMANDS ====================
    // Register logout command
    context.subscriptions.push(vscode.commands.registerCommand('idolcode.logout', () => {
        (0, storage_1.clearSession)(context);
        sidebarProvider.refresh();
        vscode.window.showInformationMessage('Logged out of Idolcode');
    }));
    // Register change idol command
    context.subscriptions.push(vscode.commands.registerCommand('idolcode.changeIdol', () => {
        sidebarProvider.showIdolSelection();
    }));
    // Cleanup on deactivation
    context.subscriptions.push({
        dispose: () => {
            if (idleTimer) {
                clearTimeout(idleTimer);
            }
            if (telemetryInterval) {
                clearInterval(telemetryInterval);
            }
        }
    });
}
/**
 * Reset the idle timer - called on every keystroke
 */
function resetIdleTimer() {
    if (idleTimer) {
        clearTimeout(idleTimer);
    }
    idleTimer = setTimeout(() => {
        // 🚨 TRIGGER: 2 minutes of no typing = idle/disengagement
        const idleMinutes = Math.floor((Date.now() - lastKeystrokeTime) / 60000);
        CoachClient_1.CoachClient.sendSignal('idle_detected', idleMinutes, {
            context: 'no_typing',
            threshold_minutes: 2
        });
        console.log(`😴 Idle detected: No typing for ${idleMinutes} minutes`);
    }, 120000); // 2 minutes
}
function deactivate() {
    console.log('Idolcode extension deactivated');
    if (idleTimer) {
        clearTimeout(idleTimer);
    }
    if (telemetryInterval) {
        clearInterval(telemetryInterval);
    }
}
//# sourceMappingURL=extension.js.map