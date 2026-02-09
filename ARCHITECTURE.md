# Idolcode — Full Architecture Documentation

> **Generated:** February 2026  
> A competitive-programming coach that lives inside VS Code.  
> You pick a Codeforces "idol", follow their problem-solving journey, and an AI coach monitors your mental state in real time.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Backend (FastAPI + Python)](#2-backend-fastapi--python)
3. [VS Code Extension (TypeScript)](#3-vs-code-extension-typescript)
4. [Data Flow Diagrams](#4-data-flow-diagrams)
5. [How Backend ↔ Extension Connect](#5-how-backend--extension-connect)
6. [Coach Engine Deep Dive](#6-coach-engine-deep-dive)
7. [Voice Interface Flow](#7-voice-interface-flow)
8. [Database Schema (MongoDB Atlas)](#8-database-schema-mongodb-atlas)
9. [Known Errors & Missing Pieces](#9-known-errors--missing-pieces)
10. [File Reference Map](#10-file-reference-map)

---

## 1. High-Level Overview

```
┌────────────────────────────────────────────────────────────────┐
│                        VS Code Editor                          │
│                                                                │
│  ┌──────────────┐     ┌─────────────────────────────────────┐  │
│  │  Extension    │     │           Webview (HTML/JS/CSS)     │  │
│  │  Host (TS)    │◄───►│  Sidebar UI  ·  Duck Coach         │  │
│  │              │      │  Problem View · Test Results        │  │
│  │  Telemetry   │      │  Burnout Bar  · Mic Button         │  │
│  │  Sensors     │      └─────────────────────────────────────┘  │
│  └──────┬───────┘                                              │
│         │  HTTP (axios)                                        │
└─────────┼──────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────┐
│        FastAPI Backend  (port 8000)          │
│                                             │
│  Codeforces API  ◄──  /api/user/*           │
│  Codeforces Web  ◄──  /api/problem/*        │
│  Coach Engine    ◄──  /api/coach/*          │
│  Gemini AI       ◄──  /api/coach/chat|voice │
│  MongoDB Atlas   ◄──  Sessions + State      │
└─────────────────────────────────────────────┘
```

**Three runtime layers:**

| Layer | Tech | Role |
|-------|------|------|
| **Webview** | HTML / JS / CSS | User-facing UI rendered inside VS Code sidebar |
| **Extension Host** | TypeScript (Node.js) | Message relay, telemetry sensors, test runner, voice recorder |
| **Backend** | Python FastAPI + Uvicorn | API gateway, Codeforces data, Coach AI engine, MongoDB persistence |

---

## 2. Backend (FastAPI + Python)

### 2.1 Entry Point & Config

| File | Purpose |
|------|---------|
| `backend/server.py` | FastAPI app, all API routes, MongoDB client init |
| `backend/config.py` | Loads env vars (`GOOGLE_API_KEY`, `MONGODB_URI`, `DATABASE_NAME`) |
| `backend/.env.local` | Local secrets (Gemini key, Atlas connection string) |
| `backend/requirements.txt` | Python dependencies |

**Startup sequence:**
1. `server.py` loads `.env.local` (override) or `.env` (fallback) via `python-dotenv`
2. Creates `AsyncIOMotorClient` to MongoDB Atlas with `certifi` TLS
3. Creates `FastAPI()` app + `APIRouter(prefix="/api")`
4. Instantiates `FusionEngine()` and `GeminiCoachAnalyzer()` singletons
5. Runs via: `uvicorn server:app --host 0.0.0.0 --port 8000 --reload`

### 2.2 API Endpoints (all prefixed `/api`)

#### Codeforces Proxy Endpoints

| Method | Path | Purpose | External Call |
|--------|------|---------|---------------|
| `GET` | `/` | Health check | — |
| `GET` | `/coders/search?query=` | Search users by handle | `codeforces.com/api/user.info` |
| `GET` | `/user/{handle}/info` | Get user profile | `codeforces.com/api/user.info` |
| `GET` | `/user/{handle}/stats` | Problems solved, contests, wins | `user.info` + `user.status` + `user.rating` |
| `GET` | `/idol/{handle}/journey` | Chronological problem history | `user.status` + `user.rating` |
| `GET` | `/user/{handle}/solved-problems` | Set of solved problem IDs | `user.status` |
| `GET` | `/compare/{user}/{idol}` | Side-by-side stats | Calls `get_user_stats()` × 2 |
| `GET` | `/problem/{cid}/{idx}` | Full problem with statement, examples | `problemset.problems` API + HTML scrape |

#### Session Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/session` | Create/get user session |
| `GET` | `/session/{user}/{idol}` | Get session data |
| `PUT` | `/session/{user}/{idol}/mark-solved` | Mark problem solved |

#### Coach Engine Endpoints

| Method | Path | Request Model | Response Model | Purpose |
|--------|------|---------------|----------------|---------|
| `POST` | `/coach/signal` | `SignalRequest` | `SignalResponse` | Process behavioral signal |
| `GET` | `/coach/state/{handle}` | — | JSON | Get current coach state |
| `DELETE` | `/coach/state/{handle}` | — | JSON | Reset coach state |
| `POST` | `/coach/chat` | `ChatRequest` | `ChatResponse` | AI chat with problem context |
| `POST` | `/coach/voice` | `VoiceRequest` | `VoiceResponse` | Voice → Gemini multimodal |

#### Status Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/status` | Create status check |
| `GET` | `/status` | List status checks (paginated, newest first) |

### 2.3 Pydantic Models (`backend/models/coach_state.py`)

```
CoachStateModel     — MongoDB document for coach session state
SignalRequest       — { user_handle, signal_type, value, metadata, message? }
SignalResponse      — { burnout_score, state, intervention_level, ghost_speed, ... }
ChatRequest         — { user_handle, text, timestamp?, current_problem_id? }
ChatResponse        — { reply, detected_sentiment, burnout_score, intervention_level }
VoiceRequest        — { audio_data (Base64), code_context, problem_id?, audio_format }
VoiceResponse       — { reply, detected_intent, burnout_score }
```

---

## 3. VS Code Extension (TypeScript)

### 3.1 File Map

| File | Purpose |
|------|---------|
| `extension.ts` | Activation, telemetry sensors, commands |
| `SidebarProvider.ts` | Webview provider, message relay, state management |
| `api.ts` | HTTP client functions for all backend endpoints |
| `storage.ts` | VS Code `globalState` persistence (session, view state) |
| `utils/CoachClient.ts` | Coach-specific HTTP client (signal, chat, voice) |
| `utils/CoachPresenter.ts` | VS Code visual interventions (toast, ghost text, modal) |
| `utils/VoiceRecorder.ts` | Windows MCI audio recording via PowerShell |
| `utils/workspaceManager.ts` | Problem folder creation (solution.cpp + tests.json) |
| `runner/testRunner.ts` | C++ compilation (g++) and test execution |
| `webview/main.js` | Webview UI (5 views, duck coach, burnout bar, mic) |
| `webview/styles.css` | All webview styling |

### 3.2 Extension Activation (`extension.ts`)

On activate:
1. Reads saved session from `globalState` → sets `CoachClient.userHandle`
2. Registers `SidebarProvider` as webview view provider for `idolcode-panel`
3. Starts **Telemetry Sensors:**
   - **Typing/Deletion Listener** — counts deletions per 60s window, fires `frustration_detected` signal if > 50 chars deleted
   - **Idle Timer** — fires `idle_detected` signal after 2 minutes of no typing
4. Registers commands: `idolcode.logout`, `idolcode.changeIdol`

### 3.3 SidebarProvider Message Flow

The webview communicates with the extension host via `postMessage`. Here is every message type:

| Webview → Extension | Handler | What Happens |
|---------------------|---------|--------------|
| `ready` | `_initializeServer()` | Health-checks backend, restores session/view |
| `retryWakeup` | `_initializeServer()` | Retry if server was down |
| `login` | `_handleLogin()` | Validates CF handle, saves session |
| `selectIdol` | `_handleSelectIdol()` | Loads idol journey + comparison |
| `searchIdol` | `_handleSearchIdol()` | Searches CF users, returns suggestions |
| `solveProblem` | `_handleSolveProblem()` | Scrapes problem, creates workspace folder |
| `backToWorkspace` | inline | Switches view, updates storage |
| `changeIdol` | `showIdolSelection()` | Clears idol, shows selection view |
| `logout` | inline | Clears session, shows login |
| `runTests` | `_handleRunTests()` | Compiles C++, runs against tests.json |
| `openProblemPanel` | `_openProblemInWebview()` | Opens problem in separate panel |
| `onChatSubmit` | `_handleChatMessage()` | Sends text to `/coach/chat`, shows reply |
| `startRecording` | `_handleStartRecording()` | Starts VoiceRecorder (Windows MCI) |
| `stopRecording` | `_handleStopRecording()` | Stops recording, sends to `/coach/voice` |

| Extension → Webview | Purpose |
|---------------------|---------|
| `updateState` | Full state push (view, session, problem, journey) |
| `loading` | Show/hide loading overlay |
| `error` | Show error message |
| `searchResults` | Idol search results |
| `wakeupStatus` | Server connection status text |
| `wakeupFailed` | Server unreachable |
| `testResults` | Test case results from C++ runner |
| `testRunning` | Test execution started/stopped |
| `updateCoachState` | Burnout score + coach state update |
| `addChatMessage` | Coach reply (chat or voice) |
| `voiceStatus` | Voice recording status (recording/processing/error/idle) |

### 3.4 Webview Views (`main.js`)

The webview is a single-page app with 5 views:

| View | Content |
|------|---------|
| `wakeup` | Server connection progress + retry button |
| `login` | CF handle input + validation |
| `idol-selection` | Search idol by handle, suggestion cards |
| `workspace` | User vs Idol comparison, journey problem list |
| `problem-solving` | Problem statement, duck coach, burnout bar, test runner, mic button |

### 3.5 CoachClient (Signal Pipeline)

```
Extension Host (sensors)
    │
    ├─ Deletion counter > 50/min ──► CoachClient.sendSignal("frustration_detected", count)
    ├─ Idle > 2 min ───────────────► CoachClient.sendSignal("idle_detected", minutes)
    ├─ Test pass ──────────────────► CoachClient.sendSignal("run_success", 1)
    ├─ Test fail (single) ─────────► CoachClient.sendSignal("run_failure", 1)
    ├─ Test fail (3+ consecutive) ─► CoachClient.sendSignal("repeated_failure", count)
    │
    ▼
POST /api/coach/signal  →  FusionEngine  →  SignalResponse
    │
    ├─ Updates sidebar burnout bar + coach state badge
    └─ Triggers CoachPresenter intervention if needed
```

### 3.6 CoachPresenter (Intervention Levels)

| Level | UI Action |
|-------|-----------|
| `NONE` / `MONITOR` | Silent — sidebar only |
| `GENTLE` | Info toast: "🦆 Coach: ..." |
| `ACTIVE` | Warning toast + ghost text next to cursor (10s auto-clear) |
| `URGENT` | Modal alert (must acknowledge) + ghost text |

---

## 4. Data Flow Diagrams

### 4.1 User Login & Idol Selection

```
User types CF handle
    → Webview sends { type: 'login', value: handle }
        → SidebarProvider._handleLogin()
            → api.validateUser(handle)         # GET /api/user/{handle}/info
            → api.getUserStats(handle)          # GET /api/user/{handle}/stats
            → storage.saveSession()             # globalState persistence
            → CoachClient.setUserHandle(handle)
            → view → 'idol-selection'

User searches for idol
    → Webview sends { type: 'searchIdol', value: query }
        → SidebarProvider._handleSearchIdol()
            → api.searchCoders(query)           # GET /api/coders/search
            → Webview receives { type: 'searchResults' }

User selects idol
    → Webview sends { type: 'selectIdol', value: handle }
        → SidebarProvider._handleSelectIdol()
            → api.getUserStats(handle)          # GET /api/user/{handle}/stats
            → api.getIdolJourney(handle)        # GET /api/idol/{handle}/journey
            → api.compareUsers(user, idol)      # GET /api/compare/{user}/{idol}
            → api.getUserSolvedProblems(user)   # GET /api/user/{handle}/solved-problems
            → storage.updateIdol()
            → view → 'workspace'
```

### 4.2 Problem Solving & Test Running

```
User clicks "Solve" on a problem
    → Webview sends { type: 'solveProblem', value: { contestId, index, name } }
        → SidebarProvider._handleSolveProblem()
            → api.getProblemContent(cid, idx)   # GET /api/problem/{cid}/{idx}
            → workspaceManager.setupProblemWorkspace()
                → Creates folder: {problemId}_{title}/
                → Creates solution.cpp (C++ template)
                → Creates tests.json (sample test cases)
                → Opens solution.cpp in editor
            → CoachClient.setCurrentProblem(problemId)
            → view → 'problem-solving'

User clicks "Run All Tests"
    → Webview sends { type: 'runTests' }
        → SidebarProvider._handleRunTests()
            → testRunner.runAllTests(folderPath)
                → g++ -std=c++17 -O2 solution.cpp → solution.exe
                → For each test case in tests.json:
                    → Execute binary with input via stdin
                    → Compare stdout vs expected output
                → Delete executable
                → CoachClient.sendSignal('run_success' or 'run_failure')
            → Webview receives { type: 'testResults' }
```

### 4.3 Coach Signal Processing (Full Pipeline)

```
Signal arrives at POST /api/coach/signal
    │
    ▼
┌─────────────────────────────────────────┐
│  1. Load State from MongoDB             │
│     db.coach_sessions.find_one(handle)  │
│     ↓                                   │
│  2. Hydrate FusionEngine                │
│     coach_engine.load_context(state)    │
│     ↓                                   │
│  3. Process Signal                      │
│     coach_engine.process_signal()       │
│     ├─ SignalCollector.record_event()   │
│     │   → detects patterns (WA burst,  │
│     │     skip streak, ghost losses)    │
│     ├─ SentimentAnalyzer.analyze()      │
│     │   → if message provided           │
│     ├─ BurnoutScorer.calculate()        │
│     │   → EMA-smoothed burnout score    │
│     ├─ FusionEngine.analyze()           │
│     │   → alignment detection           │
│     │   → composite score               │
│     │   → intervention level            │
│     │   → ghost speed modifier          │
│     ├─ CoachStateMachine.update()       │
│     │   → NORMAL↔WATCHING↔WARNING       │
│     │     ↔PROTECTIVE↔RECOVERY          │
│     └─ ResponseSelector.generate()      │
│         → templated or Gemini response  │
│     ↓                                   │
│  4. Persist to MongoDB                  │
│     db.coach_sessions.update_one()      │
│     ↓                                   │
│  5. Return SignalResponse               │
│     { burnout_score, state,             │
│       intervention_level,               │
│       ghost_speed_modifier,             │
│       coach_response, actions }         │
└─────────────────────────────────────────┘
    │
    ▼
Extension receives response
    ├─ CoachClient updates sidebar (burnout bar, state badge)
    └─ CoachPresenter triggers intervention if needed
```

### 4.4 AI Chat Flow

```
User types in chat
    → Webview sends { type: 'onChatSubmit', value: text }
        → SidebarProvider._handleChatMessage(text)
            → CoachClient.sendChat(text)
                → POST /api/coach/chat
                    │
                    ├─ Load state from MongoDB
                    ├─ Process as "chat" signal in FusionEngine
                    ├─ Fetch problem context from db.problems (if problem_id set)
                    ├─ gemini_analyzer.generate_chat_response()
                    │   → Gemini 1.5 Flash with system prompt:
                    │     "You are a CP Coach. State: {state}. Burnout: {score}."
                    │   → Includes problem statement, rating, tags if available
                    ├─ Save updated state to MongoDB
                    └─ Return { reply, sentiment, burnout_score }
                │
            → Webview receives { type: 'addChatMessage', value: { text, sender } }
            → Duck speech bubble shows reply
```

---

## 5. How Backend ↔ Extension Connect

### Connection Configuration

| Setting | Default | Where Set |
|---------|---------|-----------|
| `idolcode.backendUrl` | `http://0.0.0.0:8000` (⚠️ see errors) | VS Code settings / `package.json` |
| Backend listen address | `0.0.0.0:8000` | `uvicorn` CLI args |
| CORS | `*` (all origins) | `server.py` CORS middleware |

### Connection Protocol

```
Extension (TypeScript)          Backend (Python)
─────────────────────          ─────────────────
api.ts                         server.py
    ├── axios.get/post  ──HTTP──►  FastAPI routes
    │   Headers: JSON               │
    │   Timeout: 10-30s              │
    │                                ▼
    │                          Codeforces API
    │                          MongoDB Atlas
    │                          Gemini AI API
    │                                │
    ◄──── JSON response ────────────┘

CoachClient.ts                 server.py
    ├── sendSignal()  ──POST──► /api/coach/signal
    ├── sendChat()    ──POST──► /api/coach/chat
    ├── sendVoice()   ──POST──► /api/coach/voice
    └── getState()    ──GET───► /api/coach/state/{handle}
```

### Server Health Check (Startup)

```
Extension activates
    → SidebarProvider.resolveWebviewView()
        → Webview sends { type: 'ready' }
            → _initializeServer()
                → api.wakeUpServer()
                    → GET /api/  (3 retries, 5s delay)
                    → If OK → restore session
                    → If fail → show retry button
```

---

## 6. Coach Engine Deep Dive

### Module Architecture

```
FusionEngine (orchestrator)
    ├── SignalCollector      — behavioral event detection
    ├── SentimentAnalyzer    — text analysis (keyword + optional LLM)
    ├── BurnoutScorer        — EMA-weighted burnout score
    ├── CoachStateMachine    — 5-state managed transitions
    ├── TrendDetector        — linear regression on burnout history
    └── ResponseSelector     — response generation (template + Gemini)

Stand-alone modules (not yet integrated into main flow):
    ├── CognitiveMirror      — metacognition engine
    ├── FailureArchetypeDetector — 7 failure archetypes
    ├── ProblemIntentEngine   — pedagogical problem selection
    └── GeminiCoachAnalyzer   — direct Gemini API client
```

### Burnout Scoring Formula

$$\text{raw} = \sum_{i} w_i \cdot e^{-\lambda \cdot t_i}$$

Where $w_i$ = signal weight, $t_i$ = seconds since signal, $\lambda$ = decay factor.

Then EMA smoothing: $\text{score}_n = \alpha \cdot \text{raw} + (1 - \alpha) \cdot \text{score}_{n-1}$

### State Machine Transitions

```
         burnout < 0.25
    ┌────────────────────────┐
    ▼                        │
 NORMAL ──burnout > 0.30──► WATCHING ──burnout > 0.50──► WARNING
    ▲                                                       │
    │                                                  burnout > 0.65
    │                                                       ▼
 RECOVERY ◄────── burnout < 0.40 (sustained) ────── PROTECTIVE
```

### Signal Types & Weights

| Signal | Weight | Trigger |
|--------|--------|---------|
| `RAPID_WA_BURST` | 0.8 | 3+ wrong answers in 2 minutes |
| `GHOST_LOSS_STREAK` | 0.7 | 3+ consecutive ghost race losses |
| `SKIP_STREAK` | 0.5 | 3+ problems skipped in a row |
| `LONG_IDLE` | 0.4 | 15+ minutes of silence |
| `HINT_ABUSE` | 0.6 | 3+ hints on same problem |
| `SILENCE_AFTER_FAILURE` | 0.6 | 15+ min silence after wrong answer |
| `EXCESSIVE_TAB_SWITCHES` | 0.3 | 5+ tab switches in 30 seconds |
| `NEGATIVE_SENTIMENT` | 0.5 | Frustrated/negative chat text |
| `SUCCESSFUL_SOLVE` | -0.3 | Problem solved |
| `GHOST_WIN` | -0.2 | Won a ghost race |
| `POSITIVE_SENTIMENT` | -0.2 | Positive/motivated chat text |
| `RETURNING_AFTER_BREAK` | -0.15 | Came back after idle |

### Alignment Detection (Behavior × Sentiment)

| | Positive Sentiment | Negative Sentiment | Neutral |
|---|---|---|---|
| **Low burnout behaviors** | GENUINE_GOOD | VENTING_OK | GENUINE_GOOD |
| **High burnout behaviors** | **MASKING** 🚨 | CONFIRMED_BURNOUT | SILENT_DISENGAGE |

---

## 7. Voice Interface Flow

```
User holds mic button in webview
    → Webview sends { type: 'startRecording' }
        → SidebarProvider._handleStartRecording()
            → new VoiceRecorder()
            → VoiceRecorder.start()
                → Writes PowerShell script using winmm.dll MCI
                → Spawns: powershell.exe -File script.ps1
                → MCI opens waveaudio device, starts recording
            → Webview receives { type: 'voiceStatus', value: 'recording' }

User releases mic button
    → Webview sends { type: 'stopRecording' }
        → SidebarProvider._handleStopRecording()
            → VoiceRecorder.stop()
                → Writes stop flag file
                → PowerShell script detects flag, saves WAV, exits
                → Reads WAV file as Base64 string
            → Gets active editor code (code context)
            → CoachClient.sendVoice(audioBase64, codeContext)
                → POST /api/coach/voice
                    │
                    ├─ Decode Base64 → temp WAV file
                    ├─ genai.upload_file(temp.wav, mime_type="audio/wav")
                    ├─ Build coaching prompt with problem context + code
                    ├─ Gemini 1.5 Pro: generate_content_async([audio_file, prompt])
                    ├─ Delete temp file
                    └─ Return { reply, detected_intent, burnout_score }
                │
            → Webview receives { type: 'addChatMessage' }
            → Duck speech bubble shows AI reply
```

**⚠️ Windows Only:** Uses `winmm.dll` MCI — will not work on macOS/Linux.

---

## 8. Database Schema (MongoDB Atlas)

**Cluster:** `idolcode.q1zez1a.mongodb.net`  
**Database:** `Idolcode`

### Collections

| Collection | Document Shape | Purpose |
|------------|---------------|---------|
| `sessions` | `{ id, userHandle, idolHandle, solvedProblems[], currentProgress, createdAt, updatedAt }` | User-idol pairing and progress |
| `coach_sessions` | `{ user_handle, burnout_score, current_state, emotional_trend[], metrics{}, recent_signals[], recent_sentiments[], failures_since_last_message, message_count_session, last_updated }` | Coach engine state persistence |
| `status_checks` | `{ id, client_name, timestamp }` | Health check log |
| `problems` | `{ problemId, ... }` | Cached problem data (for chat/voice context) |

---

## 9. Known Errors & Missing Pieces

### 🔴 Critical Bugs

| # | Location | Issue | Impact |
|---|----------|-------|--------|
| 1 | `fusion.py` → `load_context()` | Sets `self.state_machine._current_state` but `CoachStateMachine` stores state in `current_context.state` — attribute doesn't exist | **Coach state is never restored from MongoDB.** Every request starts at `NORMAL` regardless of saved state. |
| 2 | `fusion.py` → `load_context()` | Constructs `SentimentResult()` missing required `raw_text` parameter | **Will raise `TypeError`** when loading a session that has saved sentiment data. |
| 3 | `responses.py` → `select_strategy()` | Compares `InterventionLevel.value` strings alphabetically (`"monitor" < "active"`) instead of ordinally | **Intervention escalation logic is broken.** "monitor" is not alphabetically less than "active", so comparisons produce wrong results. |
| 4 | `states.py` → `_get_trigger_reason()` | Same string comparison issue with `CoachState.value` — uses `>` on strings like `"normal"`, `"watching"` | **Trigger reason detection is unreliable** for certain state pairs. |
| 5 | `package.json` | Default `backendUrl` is `http://0.0.0.0:8000` | **Extension can't connect to backend on most systems.** `0.0.0.0` is not a valid client-side address. Should be `http://localhost:8000`. |
| 6 | `VoiceRecorder.ts` | **Windows-only** — hard dependency on `winmm.dll` + PowerShell | **Voice feature completely broken on macOS/Linux.** |

### 🟡 Medium Issues

| # | Location | Issue | Impact |
|---|----------|-------|--------|
| 7 | `cognitive_mirror.py` → `get_archetype_summary()` | Calls `detector.get_dominant_archetype()` and `detector.get_archetype_history()` — **neither method exists** on `FailureArchetypeDetector` | Will raise `AttributeError` if ever called. |
| 8 | `sentiment.py` → `_analyze_with_llm()` | Method is `async` but caller `analyze()` is synchronous | LLM sentiment path can never be used — returns a coroutine object, not a result. |
| 9 | `trends.py` → `MultiMetricTrendAnalyzer.get_composite_trend()` | Method body appears truncated/incomplete | Composite trend analysis won't work correctly. |
| 10 | `fusion.py` | References signal types `"RAGE_PASTE"`, `"LONG_IDLE"`, `"EXCESSIVE_TAB_SWITCHES"` that don't exist in `SignalType` enum | Dead code branches in frustration/fatigue/focus calculations. |
| 11 | `fusion.py` → `_generate_coach_response()` | Returns `None` (not string) when no response needed, but callers may not check for `None` | Potential `NoneType` errors in response handling. |
| 12 | `server.py` → `coach_engine` | Single global `FusionEngine()` instance shared across all requests | **Race condition risk** — concurrent requests for different users will corrupt each other's state since `load_context` mutates the singleton. |
| 13 | `requirements.txt` | `google-generativeai` package not listed | Install will miss the Gemini SDK — must install manually. |
| 14 | `VoiceRecorder.ts` | 30-second hard cap in PowerShell script, no user feedback on timeout | Recording silently dies after 30 seconds. |

### 🟢 Minor / Polish

| # | Location | Issue |
|---|----------|-------|
| 15 | `problem_intent.py` → `_generate_gemini_explanation()` | Stub — always falls back to template. |
| 16 | `scraper.py` | Global `cloudscraper` session shared across users — cookie leakage risk. |
| 17 | `scraper.py` | Problem statement truncated to 2000 chars silently. |
| 18 | `package.json` → `dependencies` | `mongodb` package listed — unusual for extension, bloats VSIX. |
| 19 | `extension.ts` | Idle threshold is 2 minutes — may be too aggressive in competitive programming. |
| 20 | `failure_archetypes.py` | Uses Python 3.10+ `tuple[...]` syntax inconsistently with rest of codebase. |

### 🔵 Not Yet Implemented / Missing Features

| # | Feature | Status |
|---|---------|--------|
| 21 | **Ghost Race UI** | Backend has ghost speed modifier, but no ghost race UI exists in webview. |
| 22 | **Chat Input UI** | `onChatSubmit` handler exists in SidebarProvider, but no chat input field rendered in webview `main.js`. |
| 23 | **Cognitive Mirror UI** | Backend engine exists, not connected to any endpoint or UI. |
| 24 | **Problem Intent Engine** | Backend engine exists, not connected to any endpoint or UI. |
| 25 | **Failure Archetype Display** | Backend detector exists, not surfaced in UI. |
| 26 | **Cross-platform Voice** | Only works on Windows. No macOS (`AVAudioRecorder`) or Linux (`arecord`) fallback. |
| 27 | **User Authentication** | No login/password system. CF handle is self-reported with no verification. |
| 28 | **Idol Journey Caching** | Every workspace load re-fetches idol journey from CF API (slow, rate-limited). |
| 29 | **Problem Context Caching** | Chat/voice context lookup (`db.problems`) depends on problems being cached, but no endpoint populates this collection. |
| 30 | **FusionEngine per-request isolation** | Should create a new `FusionEngine()` per request to avoid shared-state bugs (see #12). |

---

## 10. File Reference Map

### Backend (`backend/`)

```
backend/
├── .env.local                         # Secrets (Gemini key, MongoDB URI)
├── config.py                          # Environment variable loader
├── requirements.txt                   # Python dependencies
├── server.py                          # FastAPI app, all routes (961 lines)
├── models/
│   └── coach_state.py                 # Pydantic request/response models
└── services/
    ├── scraper.py                     # Codeforces HTML scraper
    └── coach_core/
        ├── __init__.py
        ├── cognitive_mirror.py        # Metacognition engine (standalone)
        ├── failure_archetypes.py      # 7 failure archetypes detector
        ├── fusion.py                  # Central orchestrator (FusionEngine)
        ├── gemini_analyzer.py         # Gemini AI client (chat + voice)
        ├── problem_intent.py          # Pedagogical problem selection
        ├── responses.py               # Response template system
        ├── scorer.py                  # Burnout scoring (EMA)
        ├── sentiment.py               # Hybrid sentiment analysis
        ├── signals.py                 # Behavioral signal detection
        ├── states.py                  # Coach state machine
        └── trends.py                  # Trend detection (linear regression)
```

### Extension (`extension/`)

```
extension/
├── package.json                       # Extension manifest
├── tsconfig.json                      # TypeScript config
├── src/
│   ├── extension.ts                   # Entry point, telemetry sensors
│   ├── api.ts                         # Backend HTTP client
│   ├── storage.ts                     # VS Code state persistence
│   ├── SidebarProvider.ts             # Main webview controller
│   ├── runner/
│   │   └── testRunner.ts              # C++ compile + test runner
│   ├── utils/
│   │   ├── CoachClient.ts             # Coach signal/chat/voice client
│   │   ├── CoachPresenter.ts          # VS Code UI interventions
│   │   ├── VoiceRecorder.ts           # Windows MCI audio recorder
│   │   └── workspaceManager.ts        # Problem workspace setup
│   └── webview/
│       └── ProblemPanel.ts            # Separate problem panel
└── webview/
    ├── main.js                        # Webview UI logic (887 lines)
    └── styles.css                     # Webview styles
```

---

*End of documentation.*
