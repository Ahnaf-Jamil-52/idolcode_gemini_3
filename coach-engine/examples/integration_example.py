"""
Web Editor Integration Example

Shows how to integrate the Real-Time Coach with a web-based code editor.
This example uses WebSocket for backend communication but adapts to any setup.
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import coach_engine
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================================
# BACKEND (Python - FastAPI or similar)
# ============================================================================

from fastapi import FastAPI, WebSocket
from coach_engine.realtime_coach import RealtimeCoach
import asyncio
import json

app = FastAPI()

# Store coaches per user session
active_coaches = {}


@app.websocket("/ws/coach/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket endpoint for real-time coaching."""
    await websocket.accept()
    
    # Create coach for this user
    coach = RealtimeCoach(
        user_id=user_id,
        enable_tts=True,  # Server-side TTS (send audio to client)
        enable_interventions=True
    )
    active_coaches[user_id] = coach
    
    # Background task for periodic updates
    async def periodic_update():
        while True:
            try:
                update = coach.update()
                
                # Send update to client
                await websocket.send_json({
                    "type": "coaching_update",
                    "data": update.to_dict()
                })
                
                await asyncio.sleep(15)  # Update every 15 seconds
            except Exception as e:
                print(f"Update error: {e}")
                break
    
    # Start background task
    update_task = asyncio.create_task(periodic_update())
    
    try:
        while True:
            # Receive events from client
            message = await websocket.receive_json()
            
            event_type = message.get("type")
            
            if event_type == "start_problem":
                coach.start_problem(
                    problem_id=message["problem_id"],
                    tags=message["tags"],
                    difficulty=message.get("difficulty")
                )
                await websocket.send_json({
                    "type": "ack",
                    "message": "Problem started"
                })
            
            elif event_type == "typing":
                coach.on_typing(
                    line_number=message["line"],
                    chars_added=message.get("chars_added", 0),
                    chars_deleted=message.get("chars_deleted", 0),
                    is_paste=message.get("is_paste", False)
                )
            
            elif event_type == "code_change":
                coach.on_code_change(
                    code=message["code"],
                    line_count=message["line_count"]
                )
            
            elif event_type == "submit":
                coach.on_problem_submit(success=message["success"])
            
            elif event_type == "ghost_result":
                coach.on_ghost_race_result(won=message["won"])
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        update_task.cancel()
        del active_coaches[user_id]


# ============================================================================
# FRONTEND (JavaScript - React/Monaco Editor)
# ============================================================================

"""
// CoachIntegration.jsx

import React, { useEffect, useRef, useState } from 'react';
import * as monaco from 'monaco-editor';

export function CoachIntegration({ userId, problemId, problemTags }) {
    const [coachState, setCoachState] = useState('silent');
    const [lastIntervention, setLastIntervention] = useState(null);
    const editorRef = useRef(null);
    const wsRef = useRef(null);
    
    useEffect(() => {
        // Connect to coaching WebSocket
        const ws = new WebSocket(`ws://localhost:8000/ws/coach/${userId}`);
        wsRef.current = ws;
        
        ws.onopen = () => {
            console.log('Coach connected');
            
            // Start problem
            ws.send(JSON.stringify({
                type: 'start_problem',
                problem_id: problemId,
                tags: problemTags,
                difficulty: 1500
            }));
        };
        
        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === 'coaching_update') {
                const update = message.data;
                
                // Update UI
                setCoachState(update.coach_state);
                
                // Show intervention if present
                if (update.intervention && update.intervention_delivered) {
                    setLastIntervention(update.intervention);
                    showCoachMessage(update.intervention);
                }
                
                // Update visual indicators based on state
                updateEditorIndicators(update);
            }
        };
        
        return () => ws.close();
    }, [userId, problemId]);
    
    useEffect(() => {
        // Setup Monaco editor
        const editor = monaco.editor.create(
            document.getElementById('editor-container'),
            {
                value: '// Start coding here...',
                language: 'python',
                theme: 'vs-dark'
            }
        );
        
        editorRef.current = editor;
        
        // Track typing events
        let lastContent = editor.getValue();
        let lastLine = 0;
        
        editor.onDidChangeModelContent((e) => {
            const changes = e.changes[0];
            if (!changes) return;
            
            const newContent = editor.getValue();
            const charsAdded = Math.max(0, newContent.length - lastContent.length);
            const charsDeleted = Math.max(0, lastContent.length - newContent.length);
            
            // Send typing event
            wsRef.current?.send(JSON.stringify({
                type: 'typing',
                line: changes.range.startLineNumber,
                chars_added: charsAdded,
                chars_deleted: charsDeleted,
                is_paste: charsAdded > 20
            }));
            
            lastContent = newContent;
        });
        
        // Periodic code snapshot
        const snapshotInterval = setInterval(() => {
            const code = editor.getValue();
            const lineCount = editor.getModel().getLineCount();
            
            wsRef.current?.send(JSON.stringify({
                type: 'code_change',
                code: code,
                line_count: lineCount
            }));
        }, 5000);
        
        return () => {
            clearInterval(snapshotInterval);
            editor.dispose();
        };
    }, []);
    
    const showCoachMessage = (intervention) => {
        // Show as notification
        const notification = document.createElement('div');
        notification.className = `coach-notification mood-${intervention.mood}`;
        notification.innerHTML = `
            <div class="duck-avatar">🦆</div>
            <div class="message">${intervention.text}</div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            notification.remove();
        }, 10000);
        
        // Optionally speak it (Web Speech API)
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(intervention.text);
            utterance.rate = getMoodRate(intervention.mood);
            window.speechSynthesis.speak(utterance);
        }
    };
    
    const getMoodRate = (mood) => {
        const rates = {
            'gentle': 0.9,
            'calm': 0.85,
            'warning': 0.8,
            'protective': 0.75,
            'encouraging': 1.0,
            'neutral': 0.9
        };
        return rates[mood] || 0.9;
    };
    
    const updateEditorIndicators = (update) => {
        // Change editor border color based on state
        const container = document.getElementById('editor-container');
        const stateColors = {
            'silent': '#2d2d2d',
            'normal': '#2d2d2d',
            'watching': '#3a3a00',
            'hinting': '#004d00',
            'warning': '#4d3300',
            'protective': '#4d0000',
            'recovery': '#003d4d'
        };
        
        container.style.borderLeft = `4px solid ${stateColors[update.coach_state]}`;
        
        // Show active signals
        const signalsDiv = document.getElementById('active-signals');
        if (update.active_signals && update.active_signals.length > 0) {
            signalsDiv.innerHTML = `
                <div class="signals-label">Active Signals:</div>
                ${update.active_signals.map(s => 
                    `<span class="signal-badge">${s}</span>`
                ).join('')}
            `;
        } else {
            signalsDiv.innerHTML = '';
        }
    };
    
    return (
        <div className="coach-integrated-editor">
            <div className="coach-status-bar">
                <span className="coach-state">Coach: {coachState}</span>
                {lastIntervention && (
                    <span className="last-message">
                        🦆 "{lastIntervention.text}"
                    </span>
                )}
            </div>
            <div id="active-signals"></div>
            <div id="editor-container" style={{height: '600px'}}></div>
        </div>
    );
}

// CSS Styles
const styles = `
.coach-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #1e1e1e;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    gap: 12px;
    align-items: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    animation: slideIn 0.3s ease;
    max-width: 400px;
    z-index: 1000;
}

.mood-gentle { border-left: 4px solid #4CAF50; }
.mood-warning { border-left: 4px solid #FF9800; }
.mood-protective { border-left: 4px solid #F44336; }
.mood-encouraging { border-left: 4px solid #2196F3; }

.duck-avatar {
    font-size: 24px;
}

.message {
    color: #e0e0e0;
    font-size: 14px;
}

@keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.coach-status-bar {
    background: #1e1e1e;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #333;
}

.coach-state {
    font-weight: bold;
    color: #4CAF50;
}

.last-message {
    color: #888;
    font-style: italic;
    font-size: 12px;
}

#active-signals {
    padding: 8px 12px;
    background: #252525;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
}

.signals-label {
    font-size: 11px;
    color: #888;
    text-transform: uppercase;
}

.signal-badge {
    background: #333;
    color: #f39c12;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
}
`;
"""


# ============================================================================
# ALTERNATIVE: REST API Integration (Simpler, No WebSockets)
# ============================================================================

"""
If WebSockets are too complex, use REST API with polling:

# Backend
@app.post("/api/coach/typing")
async def record_typing(data: dict):
    coach = get_or_create_coach(data['user_id'])
    coach.on_typing(
        line_number=data['line'],
        chars_added=data.get('chars_added', 0),
        chars_deleted=data.get('chars_deleted', 0)
    )
    return {"status": "recorded"}

@app.post("/api/coach/code")
async def record_code(data: dict):
    coach = get_or_create_coach(data['user_id'])
    coach.on_code_change(
        code=data['code'],
        line_count=data['line_count']
    )
    return {"status": "recorded"}

@app.get("/api/coach/update/{user_id}")
async def get_update(user_id: str):
    coach = get_or_create_coach(user_id)
    update = coach.update()
    return update.to_dict()

# Frontend (polling every 15 seconds)
setInterval(async () => {
    const response = await fetch(`/api/coach/update/${userId}`);
    const update = await response.json();
    
    if (update.intervention) {
        showCoachMessage(update.intervention);
    }
}, 15000);

// Send typing events
editor.onDidChangeModelContent(() => {
    fetch('/api/coach/typing', {
        method: 'POST',
        body: JSON.stringify({
            user_id: userId,
            line: currentLine,
            chars_added: added,
            chars_deleted: deleted
        })
    });
});
"""


# ============================================================================
# SIMPLE PYTHON SCRIPT INTEGRATION (For Testing)
# ============================================================================

def simple_file_watcher_example():
    """
    Watch a file being edited and provide coaching.
    Useful for testing without full editor integration.
    """
    import time
    from pathlib import Path
    from coach_engine.realtime_coach import RealtimeCoach
    
    coach = RealtimeCoach(user_id="file_watcher", enable_tts=True)
    coach.start_problem(1001, ["implementation"])
    
    file_path = Path("solution.py")
    last_content = ""
    last_mtime = 0
    
    print("Watching solution.py for changes...")
    print("The coach will provide feedback as you edit.")
    print("Press Ctrl+C to stop.\n")
    
    try:
        while True:
            if file_path.exists():
                mtime = file_path.stat().st_mtime
                
                if mtime != last_mtime:
                    content = file_path.read_text()
                    line_count = len(content.split('\n'))
                    
                    # Detect changes
                    if last_content:
                        chars_added = max(0, len(content) - len(last_content))
                        chars_deleted = max(0, len(last_content) - len(content))
                        
                        if chars_added > 0 or chars_deleted > 0:
                            coach.on_typing(
                                line_number=line_count,
                                chars_added=chars_added,
                                chars_deleted=chars_deleted
                            )
                    
                    coach.on_code_change(content, line_count)
                    
                    last_content = content
                    last_mtime = mtime
            
            # Update coach periodically
            update = coach.update()
            
            if update.intervention:
                print(f"\n🦆 Coach: {update.intervention.text}")
                print(f"   State: {update.coach_state.value}")
                print(f"   Signals: {[s.value for s in update.active_signals]}\n")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\nStopped watching.")


if __name__ == "__main__":
    print(__doc__)
    print("\nTo run file watcher demo:")
    print("  python integration_example.py")
    print("\nCreate 'solution.py' and start editing to see coaching in action!")
    
    # Uncomment to run:
    # simple_file_watcher_example()
