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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CoachClient = void 0;
const axios_1 = __importDefault(require("axios"));
const vscode = __importStar(require("vscode"));
const CoachPresenter_1 = require("./CoachPresenter");
/**
 * CoachClient - Centralized API client for coach signals
 *
 * Sends real-time telemetry to the Coach Backend (Phase 1 Brain)
 * and handles the feedback loop (Phase 3 Ghost Interface)
 */
class CoachClient {
    static getBackendUrl() {
        return vscode.workspace.getConfiguration('idolcode').get('backendUrl') || 'http://localhost:8000';
    }
    /**
     * Set the current user handle (call after login)
     */
    static setUserHandle(handle) {
        this.userHandle = handle;
        console.log(`🧠 CoachClient: User set to ${handle}`);
    }
    /**
     * Set the current problem context (Phase 4: Context Aware AI)
     * Call this when user opens a problem
     */
    static setCurrentProblem(problemId) {
        this.currentProblemId = problemId;
        if (problemId) {
            console.log(`📚 CoachClient: Problem context set to ${problemId}`);
        }
    }
    /**
     * Set callback for state updates (called from SidebarProvider)
     */
    static setStateUpdateCallback(callback) {
        this.onStateUpdate = callback;
    }
    /**
     * Send a behavioral signal to the Coach Backend
     *
     * Maps to: POST /api/coach/signal
     * Handles the feedback loop: Signal → Brain → State → UI + Intervention
     */
    static async sendSignal(type, value, metadata = {}) {
        try {
            const response = await axios_1.default.post(`${this.getBackendUrl()}/api/coach/signal`, {
                user_handle: this.userHandle,
                signal_type: type,
                value: value,
                metadata: {
                    ...metadata,
                    timestamp: new Date().toISOString()
                }
            });
            const data = response.data;
            console.log(`📡 Coach Signal Sent: ${type} → State: ${data.current_state}, Burnout: ${data.new_burnout_score.toFixed(2)}`);
            // ===== PHASE 3: THE FEEDBACK LOOP =====
            // 1. Update The Face (Sidebar)
            if (this.onStateUpdate) {
                this.onStateUpdate(data.current_state, data.new_burnout_score);
            }
            // 2. Update The Ghost (Intervention)
            if (data.needs_attention || data.intervention_level === 'active' || data.intervention_level === 'urgent') {
                CoachPresenter_1.CoachPresenter.handleIntervention(data.intervention_level, data.coach_response);
            }
        }
        catch (error) {
            console.error(`❌ Failed to send coach signal [${type}]:`, error);
        }
    }
    /**
     * Send a chat message to the Coach and get a response
     *
     * Maps to: POST /api/coach/chat
     */
    static async sendChat(message) {
        try {
            const response = await axios_1.default.post(`${this.getBackendUrl()}/api/coach/chat`, {
                user_handle: this.userHandle,
                text: message,
                timestamp: new Date().toISOString(),
                current_problem_id: this.currentProblemId // Phase 4: Problem context
            });
            const data = response.data;
            console.log(`💬 Coach Chat: Received response`);
            // Update state from chat response
            if (this.onStateUpdate && data.burnout_score !== undefined) {
                // Infer state from burnout score for chat responses
                let state = 'NORMAL';
                if (data.burnout_score > 0.7) {
                    state = 'PROTECTIVE';
                }
                else if (data.burnout_score > 0.4) {
                    state = 'WATCHING';
                }
                this.onStateUpdate(state, data.burnout_score);
            }
            return data;
        }
        catch (error) {
            console.error('❌ Failed to send chat message:', error);
            return {
                reply: "I'm having trouble connecting. Try again in a moment.",
                detected_sentiment: 'unknown'
            };
        }
    }
    /**
     * Get current coach state for a user (for debugging/UI)
     */
    static async getCoachState() {
        try {
            const response = await axios_1.default.get(`${this.getBackendUrl()}/api/coach/state/${this.userHandle}`);
            return response.data;
        }
        catch (error) {
            console.error('❌ Failed to get coach state:', error);
            return null;
        }
    }
    /**
     * Send voice audio to the coach for multimodal Gemini processing
     *
     * Maps to: POST /api/coach/voice
     */
    static async sendVoice(audioBase64, codeContext = '') {
        try {
            const response = await axios_1.default.post(`${this.getBackendUrl()}/api/coach/voice`, {
                audio_data: audioBase64,
                code_context: codeContext,
                problem_id: this.currentProblemId,
                user_handle: this.userHandle,
                audio_format: 'wav'
            });
            const data = response.data;
            console.log('🎙️ Voice response received');
            // Update burnout state if available
            if (this.onStateUpdate && data.burnout_score !== undefined) {
                let state = 'NORMAL';
                if (data.burnout_score > 0.7) {
                    state = 'PROTECTIVE';
                }
                else if (data.burnout_score > 0.4) {
                    state = 'WATCHING';
                }
                this.onStateUpdate(state, data.burnout_score);
            }
            return data;
        }
        catch (error) {
            console.error('❌ Failed to send voice query:', error);
            return {
                reply: "I couldn't process your voice right now. Try again in a moment.",
                detected_intent: 'error'
            };
        }
    }
}
exports.CoachClient = CoachClient;
CoachClient.userHandle = 'anonymous';
// Current problem context (Phase 4)
CoachClient.currentProblemId = null;
// Callback to send state updates to webview
CoachClient.onStateUpdate = null;
//# sourceMappingURL=CoachClient.js.map