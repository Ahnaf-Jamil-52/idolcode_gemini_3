import * as vscode from 'vscode';
import { SidebarProvider } from './SidebarProvider';
import { clearSession, getSession } from './storage';
import { CoachClient } from './utils/CoachClient';

// ==================== COACH TELEMETRY STATE ====================
let deletionCount = 0;
let lastKeystrokeTime = Date.now();
let idleTimer: NodeJS.Timeout | undefined;
let telemetryInterval: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
    console.log('Idolcode extension is now active!');

    // Initialize CoachClient with user handle if available
    const session = getSession(context);
    if (session?.userHandle) {
        CoachClient.setUserHandle(session.userHandle);
    }

    // Create sidebar provider
    const sidebarProvider = new SidebarProvider(context.extensionUri, context);

    // Register the webview view provider
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            'idolcode-panel',
            sidebarProvider
        )
    );

    // Track active editor changes to auto-detect problem folders
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor) {
                sidebarProvider.handleActiveFileChange(editor.document.uri);
            }
        })
    );

    // ==================== COACH TELEMETRY: TOUCH SENSORS ====================

    // 1. Typing/Deletion Listener - detect frustration (rage deleting)
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
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
        })
    );

    // 2. Windowed Analysis - check every 60 seconds
    telemetryInterval = setInterval(() => {
        if (deletionCount > 50) {
            // 🚨 TRIGGER: High deletion rate = frustration
            CoachClient.sendSignal('frustration_detected', deletionCount, {
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
    context.subscriptions.push(
        vscode.commands.registerCommand('idolcode.logout', () => {
            clearSession(context);
            sidebarProvider.refresh();
            vscode.window.showInformationMessage('Logged out of Idolcode');
        })
    );

    // Register change idol command
    context.subscriptions.push(
        vscode.commands.registerCommand('idolcode.changeIdol', () => {
            sidebarProvider.showIdolSelection();
        })
    );

    // Cleanup on deactivation
    context.subscriptions.push({
        dispose: () => {
            if (idleTimer) { clearTimeout(idleTimer); }
            if (telemetryInterval) { clearInterval(telemetryInterval); }
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
        CoachClient.sendSignal('idle_detected', idleMinutes, {
            context: 'no_typing',
            threshold_minutes: 2
        });
        console.log(`😴 Idle detected: No typing for ${idleMinutes} minutes`);
    }, 120000); // 2 minutes
}

export function deactivate() {
    console.log('Idolcode extension deactivated');
    if (idleTimer) { clearTimeout(idleTimer); }
    if (telemetryInterval) { clearInterval(telemetryInterval); }
}
