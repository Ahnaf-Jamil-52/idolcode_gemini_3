// Idolcode VS Code Extension - Webview Script

(function () {
    const vscode = acquireVsCodeApi();

    // State
    let currentState = {
        view: 'wakeup',
        session: null,
        comparison: null,
        journey: null,
        problem: null,
        solvedProblems: []
    };
    let searchResults = [];
    let errorMessage = '';
    let wakeupStatus = 'Connecting to server...';
    let wakeupFailed = false;

    // Test Runner State
    let testResults = null;
    let testsRunning = false;
    let duckMood = 'neutral'; // 'neutral', 'happy', 'sad', 'thinking'

    // DOM Elements
    const content = document.getElementById('content');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Message handler
    window.addEventListener('message', event => {
        const message = event.data;

        switch (message.type) {
            case 'updateState':
                currentState = {
                    view: message.view,
                    session: message.session,
                    comparison: message.comparison,
                    journey: message.journey,
                    problem: message.problem,
                    solvedProblems: message.solvedProblems || []
                };
                wakeupFailed = false;
                render();
                break;
            case 'loading':
                loadingOverlay.classList.toggle('hidden', !message.loading);
                break;
            case 'error':
                errorMessage = message.message;
                renderError();
                break;
            case 'searchResults':
                searchResults = message.results;
                renderSearchResults();
                break;
            case 'wakeupStatus':
                wakeupStatus = message.message;
                updateWakeupStatus();
                break;
            case 'wakeupFailed':
                wakeupFailed = true;
                renderWakeup();
                break;
            case 'testResults':
                testResults = message;
                testsRunning = false;
                updateDuckMood();
                renderTestResults();
                break;
            case 'testRunning':
                testsRunning = message.running;
                if (testsRunning) {
                    duckMood = 'thinking';
                    renderTestRunning();
                }
                break;
        }
    });

    // Notify extension we're ready
    vscode.postMessage({ type: 'ready' });

    // Render functions
    function render() {
        errorMessage = '';
        switch (currentState.view) {
            case 'wakeup':
                renderWakeup();
                break;
            case 'login':
                renderLogin();
                break;
            case 'idol-selection':
                renderIdolSelection();
                break;
            case 'workspace':
                renderWorkspace();
                break;
            case 'problem-solving':
                renderProblemSolving();
                break;
        }
    }

    function renderWakeup() {
        content.innerHTML = `
            <div class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24"><path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/></svg>
                </div>
                <span class="logo-text">Idolcode</span>
            </div>
            
            <div class="wakeup-container">
                ${getDuckSVG('white')}
                
                <p id="wakeup-status" class="wakeup-status">${wakeupStatus}</p>
                
                ${wakeupFailed ? `
                    <p class="error-message">Could not connect to server. The server might be sleeping.</p>
                    <button class="btn btn-primary" id="retry-btn">🔄 Wake Up Server</button>
                ` : `
                    <div class="spinner"></div>
                `}
            </div>
            
            <p class="view-subtitle mt-4">The server may take a moment to wake up...</p>
        `;

        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                wakeupFailed = false;
                wakeupStatus = 'Waking up server...';
                renderWakeup();
                vscode.postMessage({ type: 'retryWakeup' });
            });
        }
    }

    function updateWakeupStatus() {
        const statusEl = document.getElementById('wakeup-status');
        if (statusEl) {
            statusEl.textContent = wakeupStatus;
        }
    }

    function renderError() {
        if (errorMessage) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = errorMessage;
            const existing = content.querySelector('.error-message');
            if (existing) existing.remove();
            content.querySelector('.form-group')?.appendChild(errorDiv);
        }
    }

    function renderLogin() {
        content.innerHTML = `
            <div class="logo">
                <div class="logo-icon">
                    <svg viewBox="0 0 24 24"><path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z"/></svg>
                </div>
                <span class="logo-text">Idolcode</span>
            </div>
            
            <h2 class="view-title">Sign In</h2>
            <p class="view-subtitle">Enter your Codeforces handle to continue</p>
            
            <form id="login-form">
                <div class="form-group">
                    <label class="form-label">Codeforces Handle</label>
                    <input type="text" class="input" id="handle-input" placeholder="e.g., tourist" required>
                </div>
                <button type="submit" class="btn btn-primary">Continue →</button>
            </form>
            
            <p class="view-subtitle mt-4">We'll verify your handle with Codeforces</p>
        `;

        document.getElementById('login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            const handle = document.getElementById('handle-input').value.trim();
            if (handle) {
                vscode.postMessage({ type: 'login', handle });
            }
        });
    }

    function renderIdolSelection() {
        const session = currentState.session;

        content.innerHTML = `
            <div class="user-header">
                <div class="user-info">
                    <span class="user-handle ${getRatingClass(session?.userInfo?.rating)}">${session?.userHandle || 'User'}</span>
                    <span class="user-rating">${session?.userInfo?.rating || '—'}</span>
                </div>
                <button class="btn btn-ghost" id="logout-btn">Logout</button>
            </div>
            
            <h2 class="view-title">Who will you chase?</h2>
            <p class="view-subtitle">Choose your idol to follow their path</p>
            
            <div class="form-group">
                <label class="form-label">Search for your idol</label>
                <input type="text" class="input" id="idol-search" placeholder="e.g., tourist, Benq, Petr">
            </div>
            
            <div id="search-results" class="search-results"></div>
            
            ${session?.idolHandle ? `
                <div class="glass-card mt-4">
                    <p class="view-subtitle">Current idol: <strong class="${getRatingClass(session?.idolInfo?.rating)}">${session.idolHandle}</strong></p>
                    <button class="btn btn-secondary" id="continue-btn">Continue with ${session.idolHandle}</button>
                </div>
            ` : ''}
        `;

        document.getElementById('idol-search').addEventListener('input', debounce((e) => {
            const query = e.target.value.trim();
            vscode.postMessage({ type: 'searchIdol', query });
        }, 300));

        document.getElementById('logout-btn').addEventListener('click', () => {
            vscode.postMessage({ type: 'logout' });
        });

        const continueBtn = document.getElementById('continue-btn');
        if (continueBtn) {
            continueBtn.addEventListener('click', () => {
                vscode.postMessage({ type: 'selectIdol', handle: session.idolHandle });
            });
        }
    }

    function renderSearchResults() {
        const resultsContainer = document.getElementById('search-results');
        if (!resultsContainer) return;

        if (searchResults.length === 0) {
            resultsContainer.innerHTML = '';
            return;
        }

        resultsContainer.innerHTML = searchResults.map(coder => `
            <div class="search-item" data-handle="${coder.handle}">
                <img class="search-avatar" src="${coder.avatar || ''}" alt="" onerror="this.style.display='none'">
                <div>
                    <div class="search-handle ${getRatingClass(coder.rating)}">${coder.handle}</div>
                    <div class="search-rating">${coder.rank || 'Unknown'} • ${coder.rating || '—'}</div>
                </div>
            </div>
        `).join('');

        resultsContainer.querySelectorAll('.search-item').forEach(item => {
            item.addEventListener('click', () => {
                const handle = item.dataset.handle;
                vscode.postMessage({ type: 'selectIdol', handle });
            });
        });
    }

    function renderWorkspace() {
        const session = currentState.session;
        const comparison = currentState.comparison;
        const journey = currentState.journey;
        const solvedSet = new Set(currentState.solvedProblems);

        // Calculate progress
        let lastSolvedIndex = -1;
        const problems = journey?.problems || [];
        for (let i = 0; i < problems.length; i++) {
            if (solvedSet.has(problems[i].problemId)) {
                lastSolvedIndex = i;
            } else {
                break;
            }
        }

        const unlockedIndices = new Set();
        let unlockCount = 0;
        for (let i = lastSolvedIndex + 1; i < problems.length && unlockCount < 3; i++) {
            if (!solvedSet.has(problems[i].problemId)) {
                unlockedIndices.add(i);
                unlockCount++;
            }
        }

        content.innerHTML = `
            <div class="user-header">
                <div class="user-info">
                    <span class="user-handle ${getRatingClass(session?.userInfo?.rating)}">${session?.userHandle || 'User'}</span>
                </div>
                <button class="btn btn-ghost" id="change-idol-btn">Change Idol</button>
            </div>
            
            <div class="glass-card">
                <div class="text-center mb-4">
                    <span>Following </span>
                    <strong class="${getRatingClass(comparison?.idol?.rating)}">${session?.idolHandle}</strong>
                </div>
                
                <div class="progress-container">
                    <div class="progress-label">
                        <span>Progress</span>
                        <span>${comparison?.progressPercent?.toFixed(1) || 0}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${comparison?.progressPercent || 0}%"></div>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Your Rating</div>
                        <div class="stat-value ${getRatingClass(comparison?.user?.rating)}">${comparison?.user?.rating || '—'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Idol Rating</div>
                        <div class="stat-value ${getRatingClass(comparison?.idol?.rating)}">${comparison?.idol?.rating || '—'}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">You Solved</div>
                        <div class="stat-value">${comparison?.user?.problemsSolved || 0}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Idol Solved</div>
                        <div class="stat-value">${comparison?.idol?.problemsSolved || 0}</div>
                    </div>
                </div>
            </div>
            
            <div class="section-title">Problem Path</div>
            <div class="problem-list">
                ${problems.slice(0, 20).map((problem, index) => {
            const isSolved = solvedSet.has(problem.problemId);
            const isUnlocked = unlockedIndices.has(index);
            const isLocked = !isSolved && !isUnlocked && index > lastSolvedIndex + 3;
            const isYouAreHere = index === lastSolvedIndex + 1;

            return `
                        <div class="problem-item ${isSolved ? 'solved' : ''} ${isLocked ? 'locked' : ''}" 
                             data-contest="${problem.contestId}" 
                             data-index="${problem.index}"
                             ${isLocked ? '' : 'data-clickable="true"'}>
                            <div class="problem-node ${isSolved ? 'solved' : isUnlocked ? 'unlocked' : 'locked'}">
                                ${isSolved ? '✓' : isUnlocked ? '★' : '🔒'}
                            </div>
                            <div class="problem-info">
                                ${isYouAreHere ? '<div class="you-are-here">📍 You are here</div>' : ''}
                                <div class="problem-id">${problem.problemId}</div>
                                <div class="problem-name">${problem.name}</div>
                            </div>
                            <span class="problem-rating ${getRatingClass(problem.rating)}">${problem.rating || '?'}</span>
                        </div>
                    `;
        }).join('')}
                ${problems.length > 20 ? `<p class="view-subtitle">+ ${problems.length - 20} more problems</p>` : ''}
            </div>
            
            <div class="duck-section">
                <div class="duck-container">
                    ${getDuckSVG('white')}
                    <p class="duck-message">🦆 Quack! Click a problem to start solving!</p>
                </div>
            </div>
        `;

        document.getElementById('change-idol-btn').addEventListener('click', () => {
            vscode.postMessage({ type: 'changeIdol' });
        });

        content.querySelectorAll('.problem-item[data-clickable="true"]').forEach(item => {
            item.addEventListener('click', () => {
                const contestId = parseInt(item.dataset.contest);
                const index = item.dataset.index;
                vscode.postMessage({ type: 'solveProblem', contestId, index });
            });
        });
    }

    function renderProblemSolving() {
        const problem = currentState.problem;
        if (!problem) {
            content.innerHTML = '<p>Loading problem...</p>';
            return;
        }

        content.innerHTML = `
            <div class="problem-header">
                <button class="back-btn" id="back-btn">←</button>
                <div class="problem-title">${problem.contestId}${problem.index}: ${problem.name}</div>
            </div>
            
            <!-- Duck Coach Section -->
            <div class="coach-panel">
                <div class="duck-coach ${duckMood}">
                    ${getDuckSVG(duckMood === 'happy' ? 'green' : duckMood === 'sad' ? 'red' : 'blue')}
                    <div class="duck-speech" id="duck-speech">
                        ${getDuckMessage()}
                    </div>
                </div>
            </div>
            
            <!-- Test Runner Control Panel -->
            <div class="control-panel">
                <div class="test-controls">
                    <button class="btn btn-run" id="run-tests-btn" ${testsRunning ? 'disabled' : ''}>
                        ${testsRunning ? '⏳ Running...' : '▶ Run All Tests'}
                    </button>
                </div>
                
                <div id="test-results-container">
                    ${renderTestResultsHTML()}
                </div>
            </div>
            
            <!-- Problem Essentials -->
            <div class="problem-essentials">
                <div class="problem-meta">
                    <span>⏱️ ${problem.timeLimit}</span>
                    <span>💾 ${problem.memoryLimit}</span>
                    ${problem.rating ? `<span class="${getRatingClass(problem.rating)}">⭐ ${problem.rating}</span>` : ''}
                </div>
            </div>
            
            <!-- Collapsible Problem Statement -->
            <details class="problem-details">
                <summary>📖 Problem Statement</summary>
                <div class="problem-content">
                    <p>${problem.problemStatement || 'No statement available.'}</p>
                    
                    ${problem.inputSpecification ? `
                        <div class="problem-section">
                            <h4>Input</h4>
                            <p>${problem.inputSpecification}</p>
                        </div>
                    ` : ''}
                    
                    ${problem.outputSpecification ? `
                        <div class="problem-section">
                            <h4>Output</h4>
                            <p>${problem.outputSpecification}</p>
                        </div>
                    ` : ''}
                    
                    ${problem.note ? `
                        <div class="problem-section">
                            <h4>Note</h4>
                            <p>${problem.note}</p>
                        </div>
                    ` : ''}
                </div>
            </details>
            
            <!-- Sample Tests Reference -->
            <details class="problem-details" open>
                <summary>🧪 Sample Tests (${problem.examples.length})</summary>
                <div class="examples-compact">
                    ${problem.examples.map((ex, i) => `
                        <div class="example-compact">
                            <div class="example-row">
                                <div class="example-col">
                                    <div class="example-label">Input ${i + 1}</div>
                                    <pre class="example-code">${escapeHtml(ex.input)}</pre>
                                </div>
                                <div class="example-col">
                                    <div class="example-label">Output ${i + 1}</div>
                                    <pre class="example-code">${escapeHtml(ex.output)}</pre>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </details>
            
            <a href="${problem.url}" class="external-link" target="_blank">Open on Codeforces ↗</a>
        `;

        // Event listeners
        document.getElementById('back-btn').addEventListener('click', () => {
            vscode.postMessage({ type: 'backToWorkspace' });
        });

        document.getElementById('run-tests-btn').addEventListener('click', () => {
            testResults = null;
            vscode.postMessage({ type: 'runTests' });
        });
    }

    function getDuckMessage() {
        if (testsRunning) {
            return "🦆 Compiling and running tests...";
        }
        if (!testResults) {
            return "🦆 Ready to test? Hit Run!";
        }
        if (!testResults.success) {
            return `🦆 Oops! ${testResults.error || 'Something went wrong'}`;
        }
        const passed = testResults.results.filter(r => r.passed).length;
        const total = testResults.results.length;
        if (passed === total) {
            return "🦆 All tests passed! Great job!";
        }
        return `🦆 ${passed}/${total} tests passed. Keep trying!`;
    }

    function updateDuckMood() {
        if (!testResults || !testResults.success) {
            duckMood = 'sad';
            return;
        }
        const passed = testResults.results.filter(r => r.passed).length;
        const total = testResults.results.length;
        duckMood = passed === total ? 'happy' : 'sad';
    }

    function renderTestResultsHTML() {
        if (testsRunning) {
            return '<div class="test-running"><div class="spinner-small"></div> Running tests...</div>';
        }
        if (!testResults) {
            return '<div class="test-placeholder">Click "Run All Tests" to start</div>';
        }
        if (!testResults.success) {
            return `<div class="test-error">${escapeHtml(testResults.error)}</div>`;
        }

        return testResults.results.map(result => `
            <details class="test-case-details ${result.passed ? 'pass' : 'fail'}" ${!result.passed ? 'open' : ''}>
                <summary class="test-header">
                    <span class="test-icon">${result.passed ? '✅' : '❌'}</span>
                    <span class="test-name">Test ${result.id}</span>
                    <span class="test-time">${result.time}ms</span>
                </summary>
                <div class="test-body">
                    <div class="test-io-grid">
                        <div class="test-io-section">
                            <div class="io-label">📥 Input</div>
                            <pre class="io-content">${escapeHtml(result.input)}</pre>
                        </div>
                        <div class="test-io-section">
                            <div class="io-label">📤 Expected</div>
                            <pre class="io-content expected">${escapeHtml(result.expected)}</pre>
                        </div>
                    </div>
                    ${!result.passed ? `
                        <div class="test-actual-section">
                            <div class="io-label">❌ Actual Output</div>
                            <pre class="io-content actual">${escapeHtml(result.actual)}</pre>
                        </div>
                    ` : `
                        <div class="test-actual-section passed">
                            <div class="io-label">✅ Your Output (Correct!)</div>
                            <pre class="io-content correct">${escapeHtml(result.actual)}</pre>
                        </div>
                    `}
                </div>
            </details>
        `).join('');
    }

    function renderTestResults() {
        const container = document.getElementById('test-results-container');
        const speech = document.getElementById('duck-speech');
        const duckCoach = document.querySelector('.duck-coach');

        if (container) {
            container.innerHTML = renderTestResultsHTML();
        }
        if (speech) {
            speech.innerHTML = getDuckMessage();
        }
        if (duckCoach) {
            duckCoach.className = `duck-coach ${duckMood}`;
        }
    }

    function renderTestRunning() {
        const container = document.getElementById('test-results-container');
        const speech = document.getElementById('duck-speech');
        const runBtn = document.getElementById('run-tests-btn');
        const duckCoach = document.querySelector('.duck-coach');

        if (container) {
            container.innerHTML = '<div class="test-running"><div class="spinner-small"></div> Compiling and running...</div>';
        }
        if (speech) {
            speech.innerHTML = "🦆 Compiling and running tests...";
        }
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerHTML = '⏳ Running...';
        }
        if (duckCoach) {
            duckCoach.className = 'duck-coach thinking';
        }
    }

    // Helpers
    function getRatingClass(rating) {
        if (!rating) return 'rating-newbie';
        if (rating >= 3000) return 'rating-legendary';
        if (rating >= 2600) return 'rating-grandmaster';
        if (rating >= 2400) return 'rating-international';
        if (rating >= 2100) return 'rating-master';
        if (rating >= 1900) return 'rating-candidate';
        if (rating >= 1600) return 'rating-expert';
        if (rating >= 1400) return 'rating-specialist';
        if (rating >= 1200) return 'rating-pupil';
        return 'rating-newbie';
    }

    function getDuckSVG(mode) {
        const colorMap = { 'white': '#f0f0f0', 'blue': '#3b82f6', 'red': '#ef4444', 'green': '#22c55e' };
        const color = colorMap[mode] || colorMap.blue;
        return `
            <svg viewBox="0 0 100 100" class="duck-mascot">
                <ellipse cx="50" cy="60" rx="30" ry="25" fill="${color}" opacity="0.9"/>
                <circle cx="50" cy="35" r="20" fill="${color}" opacity="0.9"/>
                <ellipse cx="65" cy="38" rx="10" ry="5" fill="#f97316"/>
                <circle cx="55" cy="32" r="4" fill="#1e293b"/>
                <circle cx="56" cy="31" r="1.5" fill="white"/>
                <ellipse cx="40" cy="60" rx="12" ry="15" fill="${color}" opacity="0.7"/>
                ${mode === 'blue' ? `
                    <circle cx="45" cy="32" r="8" fill="none" stroke="#1e293b" stroke-width="2"/>
                    <circle cx="60" cy="32" r="8" fill="none" stroke="#1e293b" stroke-width="2"/>
                    <line x1="53" y1="32" x2="52" y2="32" stroke="#1e293b" stroke-width="2"/>
                ` : ''}
                ${mode === 'red' ? `
                    <rect x="30" y="25" width="40" height="5" fill="#dc2626" rx="2"/>
                    <polygon points="68,20 75,27 70,30 68,25" fill="#dc2626"/>
                ` : ''}
            </svg>
        `;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Initial render
    render();
})();
