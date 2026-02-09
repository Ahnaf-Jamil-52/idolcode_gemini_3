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
exports.CoachPresenter = void 0;
const vscode = __importStar(require("vscode"));
/**
 * CoachPresenter - Handles VS Code visual interventions
 *
 * This is the "Ghost" - the physical manifestation of the coach in the IDE.
 * It can show ghost text, toast notifications, and modal alerts.
 */
class CoachPresenter {
    /**
     * Handle an intervention based on severity level
     *
     * @param level Intervention level: NONE, MONITOR, GENTLE, ACTIVE, URGENT
     * @param message The message to display to the user
     */
    static handleIntervention(level, message) {
        if (!message) {
            return;
        }
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
    static triggerHardIntervention(message) {
        // A. Show Modal Alert (must dismiss to continue)
        vscode.window.showWarningMessage(`🛑 COACH INTERVENTION: ${message}`, { modal: true }, "I understand").then(selection => {
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
    static showGhostText(message) {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }
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
exports.CoachPresenter = CoachPresenter;
// Ghost text decoration (appears next to cursor)
CoachPresenter.ghostDecoration = vscode.window.createTextEditorDecorationType({
    after: {
        color: 'rgba(244, 63, 94, 0.8)', // Rose-red ghost
        fontStyle: 'italic',
        margin: '0 0 0 20px'
    },
    rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
});
//# sourceMappingURL=CoachPresenter.js.map