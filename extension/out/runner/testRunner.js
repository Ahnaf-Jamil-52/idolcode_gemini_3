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
exports.testRunner = exports.TestRunner = void 0;
const cp = __importStar(require("child_process"));
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const CoachClient_1 = require("../utils/CoachClient");
class TestRunner {
    constructor() {
        // Track consecutive failures for coach integration
        this.consecutiveFailures = 0;
        this.currentProblemId = '';
    }
    /**
     * Set the current problem ID for context in coach signals
     */
    setProblemContext(problemId) {
        this.currentProblemId = problemId;
    }
    /**
     * Compile C++ file using g++
     */
    async compile(filePath) {
        // On Windows, output .exe; on other platforms, output binary without extension
        const isWindows = process.platform === 'win32';
        const outPath = isWindows
            ? filePath.replace('.cpp', '.exe')
            : filePath.replace('.cpp', '');
        const cmd = `g++ "${filePath}" -o "${outPath}" -std=c++17 -O2`;
        return new Promise((resolve, reject) => {
            cp.exec(cmd, { timeout: 30000 }, (err, stdout, stderr) => {
                if (err) {
                    reject(`Compilation Error:\n${stderr}`);
                }
                else {
                    resolve(outPath);
                }
            });
        });
    }
    /**
     * Run a single test case with timeout handling
     */
    async runTestCase(exePath, input, timeLimit = 2000) {
        return new Promise((resolve) => {
            const child = cp.execFile(exePath, [], { timeout: timeLimit }, (error, stdout, stderr) => {
                if (error && error.killed) {
                    resolve({ output: '', status: 'TLE' });
                }
                else if (error) {
                    resolve({ output: stderr || error.message, status: 'RE' });
                }
                else {
                    resolve({ output: stdout.trim(), status: 'OK' });
                }
            });
            if (child.stdin) {
                child.stdin.write(input);
                child.stdin.end();
            }
        });
    }
    /**
     * Normalize output for comparison (handle whitespace differences)
     */
    normalizeOutput(output) {
        return output
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .join('\n');
    }
    /**
     * Run all tests from tests.json or fetch from API if missing
     */
    async runAllTests(folderPath, fetchTestsFallback) {
        const cppFile = path.join(folderPath, 'solution.cpp');
        const testsFile = path.join(folderPath, 'tests.json');
        // Check if solution.cpp exists
        if (!fs.existsSync(cppFile)) {
            return { success: false, error: 'No solution.cpp found in the problem folder' };
        }
        // Load test cases
        let tests = [];
        // Try to load from tests.json first
        if (fs.existsSync(testsFile)) {
            try {
                const testsContent = fs.readFileSync(testsFile, 'utf-8');
                tests = JSON.parse(testsContent);
            }
            catch (e) {
                console.log('Failed to parse tests.json, will try fallback');
            }
        }
        // If no tests found and we have a fallback, try to fetch from Codeforces
        if ((!tests || tests.length === 0) && fetchTestsFallback) {
            try {
                const fetchedTests = await fetchTestsFallback();
                if (fetchedTests && fetchedTests.length > 0) {
                    tests = fetchedTests;
                    // Save to tests.json for future use
                    fs.writeFileSync(testsFile, JSON.stringify(tests, null, 2));
                }
            }
            catch (e) {
                console.log('Failed to fetch tests from Codeforces:', e);
            }
        }
        if (!tests || tests.length === 0) {
            return { success: false, error: 'No test cases found. Check tests.json or try selecting the problem again.' };
        }
        try {
            // Compile first
            const exePath = await this.compile(cppFile);
            // Run all test cases
            const results = [];
            for (let i = 0; i < tests.length; i++) {
                const test = tests[i];
                const start = Date.now();
                const { output: actual, status } = await this.runTestCase(exePath, test.input);
                const time = Date.now() - start;
                // Handle different statuses
                let displayActual = actual;
                let passed = false;
                if (status === 'TLE') {
                    displayActual = '⏱️ Time Limit Exceeded';
                }
                else if (status === 'RE') {
                    displayActual = `💥 Runtime Error: ${actual}`;
                }
                else {
                    // Compare outputs (normalized)
                    const normalizedActual = this.normalizeOutput(actual);
                    const normalizedExpected = this.normalizeOutput(test.output);
                    passed = normalizedActual === normalizedExpected;
                    displayActual = actual;
                }
                results.push({
                    id: i + 1,
                    passed,
                    input: test.input,
                    expected: test.output,
                    actual: displayActual,
                    time
                });
            }
            // Clean up executable after tests
            try {
                fs.unlinkSync(exePath);
            }
            catch (e) {
                // Ignore cleanup errors
            }
            // ==================== COACH INTEGRATION ====================
            const allPassed = results.every(r => r.passed);
            const failedCount = results.filter(r => !r.passed).length;
            if (allPassed) {
                // Reset consecutive failures on success
                this.consecutiveFailures = 0;
                CoachClient_1.CoachClient.sendSignal('run_success', 1, {
                    problem_id: this.currentProblemId,
                    tests_passed: results.length
                });
                console.log(`✅ All tests passed - coach notified`);
            }
            else {
                // Increment consecutive failures
                this.consecutiveFailures++;
                // Send signal on first failure or repeated failures
                if (this.consecutiveFailures >= 3) {
                    // 🚨 TRIGGER: Repeated failures = potential frustration
                    CoachClient_1.CoachClient.sendSignal('repeated_failure', this.consecutiveFailures, {
                        problem_id: this.currentProblemId,
                        failed_tests: failedCount,
                        total_tests: results.length,
                        error_type: 'wrong_answer'
                    });
                    console.log(`🔥 Repeated failures (${this.consecutiveFailures}) - coach notified`);
                }
                else {
                    // Single failure
                    CoachClient_1.CoachClient.sendSignal('run_failure', 1, {
                        problem_id: this.currentProblemId,
                        failed_tests: failedCount,
                        consecutive: this.consecutiveFailures
                    });
                }
            }
            return { success: true, results };
        }
        catch (compilationError) {
            return {
                success: false,
                error: typeof compilationError === 'string' ? compilationError : compilationError.message
            };
        }
    }
}
exports.TestRunner = TestRunner;
// Singleton instance
exports.testRunner = new TestRunner();
//# sourceMappingURL=testRunner.js.map