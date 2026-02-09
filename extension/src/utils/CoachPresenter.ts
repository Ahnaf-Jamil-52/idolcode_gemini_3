import * as vscode from 'vscode';

/**
 * CoachPresenter - Handles VS Code visual interventions
 * 
 * This is the "Ghost" - the physical manifestation of the coach in the IDE.
 * It can show ghost text, toast notifications, and modal alerts.
 */
export class CoachPresenter {
    // Ghost text decoration (appears next to cursor)
    private static ghostDecoration = vscode.window.createTextEditorDecorationType({
        after: {
            color: 'rgba(244, 63, 94, 0.8)', // Rose-red ghost
            fontStyle: 'italic',
            margin: '0 0 0 20px'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    });

    private static clearTimer: NodeJS.Timeout | undefined;

    /**
     * Handle an intervention based on severity level
     * 
     * @param level Intervention level: NONE, MONITOR, GENTLE, ACTIVE, URGENT
     * @param message The message to display to the user
     */
    static handleIntervention(level: string, message: string | null) {
        if (!message) { return; }

        // Clear any existing ghost text
        this.clearGhostText();

        switch (level.toUpperCase()) {
            case 'NONE':
            case 'MONITOR':
                // Silent - just update sidebar state
                break;

            case 'GENTLE':
                // Non-intrusive toast notification
                vscode.window.showInformationMessage(`🦆 Coach: ${message}`);
                break;

            case 'ACTIVE':
                // More prominent warning
                vscode.window.showWarningMessage(`⚠️ Coach: ${message}`);
                this.showGhostText(message);
                break;

            case 'URGENT':
                // 🚨 FULL INTERVENTION - Modal + Ghost Text
                this.triggerHardIntervention(message);
                break;
        }
    }

    /**
     * Trigger a hard intervention - modal alert + ghost text
     */
    private static triggerHardIntervention(message: string) {
        // A. Show Modal Alert (must dismiss to continue)
        vscode.window.showWarningMessage(
            `🛑 COACH INTERVENTION: ${message}`,
            { modal: true },
            "I understand"
        ).then(selection => {
            if (selection === "I understand") {
                console.log('🦆 User acknowledged intervention');
            }
        });

        // B. Inject Ghost Text at current cursor position
        this.showGhostText(message);
    }

    /**
     * Show ghost text next to the user's cursor
     */
    private static showGhostText(message: string) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) { return; }

        const position = editor.selection.active;
        const range = new vscode.Range(position, position);

        // "Ghost" text appears next to cursor
        editor.setDecorations(this.ghostDecoration, [{
            range,
            renderOptions: {
                after: {
                    contentText: `  ← ${message}`
                }
            }
        }]);

        // Auto-clear after 10 seconds
        if (this.clearTimer) {
            clearTimeout(this.clearTimer);
        }
        this.clearTimer = setTimeout(() => this.clearGhostText(), 10000);
    }

    /**
     * Clear ghost text from the editor
     */
    static clearGhostText() {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            editor.setDecorations(this.ghostDecoration, []);
        }
        if (this.clearTimer) {
            clearTimeout(this.clearTimer);
            this.clearTimer = undefined;
        }
    }
}
