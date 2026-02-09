import axios from 'axios';
import * as vscode from 'vscode';
import { CoachPresenter } from './CoachPresenter';

/**
 * CoachClient - Centralized API client for coach signals
 * 
 * Sends real-time telemetry to the Coach Backend (Phase 1 Brain)
 * and handles the feedback loop (Phase 3 Ghost Interface)
 */
export class CoachClient {
    private static getBackendUrl(): string {
        return vscode.workspace.getConfiguration('idolcode').get('backendUrl') || 'http://localhost:8000';
    }

    private static userHandle: string = 'anonymous';

    // Current problem context (Phase 4)
    private static currentProblemId: string | null = null;

    // Callback to send state updates to webview
    private static onStateUpdate: ((state: string, burnoutScore: number) => void) | null = null;

    /**
     * Set the current user handle (call after login)
     */
    static setUserHandle(handle: string) {
        this.userHandle = handle;
        console.log(`🧠 CoachClient: User set to ${handle}`);
    }

    /**
     * Set the current problem context (Phase 4: Context Aware AI)
     * Call this when user opens a problem
     */
    static setCurrentProblem(problemId: string | null) {
        this.currentProblemId = problemId;
        if (problemId) {
            console.log(`📚 CoachClient: Problem context set to ${problemId}`);
        }
    }

    /**
     * Set callback for state updates (called from SidebarProvider)
     */
    static setStateUpdateCallback(callback: (state: string, burnoutScore: number) => void) {
        this.onStateUpdate = callback;
    }


    /**
     * Send a behavioral signal to the Coach Backend
     * 
     * Maps to: POST /api/coach/signal
     * Handles the feedback loop: Signal → Brain → State → UI + Intervention
     */
    static async sendSignal(type: string, value: number, metadata: Record<string, any> = {}): Promise<void> {
        try {
            const response = await axios.post(`${this.getBackendUrl()}/api/coach/signal`, {
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
                CoachPresenter.handleIntervention(
                    data.intervention_level,
                    data.coach_response
                );
            }

        } catch (error) {
            console.error(`❌ Failed to send coach signal [${type}]:`, error);
        }
    }

    /**
     * Send a chat message to the Coach and get a response
     * 
     * Maps to: POST /api/coach/chat
     */
    static async sendChat(message: string): Promise<{ reply: string; detected_sentiment: string }> {
        try {
            const response = await axios.post(`${this.getBackendUrl()}/api/coach/chat`, {
                user_handle: this.userHandle,
                text: message,
                timestamp: new Date().toISOString(),
                current_problem_id: this.currentProblemId  // Phase 4: Problem context
            });


            const data = response.data;
            console.log(`💬 Coach Chat: Received response`);

            // Update state from chat response
            if (this.onStateUpdate && data.burnout_score !== undefined) {
                // Infer state from burnout score for chat responses
                let state = 'NORMAL';
                if (data.burnout_score > 0.7) { state = 'PROTECTIVE'; }
                else if (data.burnout_score > 0.4) { state = 'WATCHING'; }
                this.onStateUpdate(state, data.burnout_score);
            }

            return data;
        } catch (error) {
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
    static async getCoachState(): Promise<any> {
        try {
            const response = await axios.get(`${this.getBackendUrl()}/api/coach/state/${this.userHandle}`);
            return response.data;
        } catch (error) {
            console.error('❌ Failed to get coach state:', error);
            return null;
        }
    }

    /**
     * Send voice audio to the coach for multimodal Gemini processing
     *
     * Maps to: POST /api/coach/voice
     */
    static async sendVoice(audioBase64: string, codeContext: string = ''): Promise<{ reply: string; detected_intent: string }> {
        try {
            const response = await axios.post(`${this.getBackendUrl()}/api/coach/voice`, {
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
                if (data.burnout_score > 0.7) { state = 'PROTECTIVE'; }
                else if (data.burnout_score > 0.4) { state = 'WATCHING'; }
                this.onStateUpdate(state, data.burnout_score);
            }

            return data;
        } catch (error) {
            console.error('❌ Failed to send voice query:', error);
            return {
                reply: "I couldn't process your voice right now. Try again in a moment.",
                detected_intent: 'error'
            };
        }
    }
}
