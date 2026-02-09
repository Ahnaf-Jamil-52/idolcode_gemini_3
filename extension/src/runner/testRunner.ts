import * as cp from 'child_process';
import * as path from 'path';
import * as vscode from 'vscode';
import * as fs from 'fs';
import { CoachClient } from '../utils/CoachClient';

export interface TestResult {
    id: number;
    passed: boolean;
    input: string;
    expected: string;
    actual: string;
    time: number;
}

export interface RunResult {
    success: boolean;
    results?: TestResult[];
    error?: string;
    compilationOutput?: string;
}

export class TestRunner {
    // Track consecutive failures for coach integration
    private consecutiveFailures: number = 0;
    private currentProblemId: string = '';

    /**
     * Set the current problem ID for context in coach signals
     */
    setProblemContext(problemId: string) {
        this.currentProblemId = problemId;
    }

    /**
     * Compile C++ file using g++
     */
    async compile(filePath: string): Promise<string> {
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
                } else {
                    resolve(outPath);
                }
            });
        });
    }

    /**
     * Run a single test case with timeout handling
     */
    async runTestCase(exePath: string, input: string, timeLimit: number = 2000): Promise<{ output: string; status: 'OK' | 'TLE' | 'RE' }> {
        return new Promise((resolve) => {
            const child = cp.execFile(exePath, [], { timeout: timeLimit }, (error, stdout, stderr) => {
                if (error && error.killed) {
                    resolve({ output: '', status: 'TLE' });
                } else if (error) {
                    resolve({ output: stderr || error.message, status: 'RE' });
                } else {
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
    private normalizeOutput(output: string): string {
        return output
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0)
            .join('\n');
    }

    /**
     * Run all tests from tests.json or fetch from API if missing
     */
    async runAllTests(
        folderPath: string,
        fetchTestsFallback?: () => Promise<{ input: string; output: string }[] | null>
    ): Promise<RunResult> {
        const cppFile = path.join(folderPath, 'solution.cpp');
        const testsFile = path.join(folderPath, 'tests.json');

        // Check if solution.cpp exists
        if (!fs.existsSync(cppFile)) {
            return { success: false, error: 'No solution.cpp found in the problem folder' };
        }

        // Load test cases
        let tests: { input: string; output: string }[] = [];

        // Try to load from tests.json first
        if (fs.existsSync(testsFile)) {
            try {
                const testsContent = fs.readFileSync(testsFile, 'utf-8');
                tests = JSON.parse(testsContent);
            } catch (e) {
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
            } catch (e) {
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
            const results: TestResult[] = [];
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
                } else if (status === 'RE') {
                    displayActual = `💥 Runtime Error: ${actual}`;
                } else {
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
            } catch (e) {
                // Ignore cleanup errors
            }

            // ==================== COACH INTEGRATION ====================
            const allPassed = results.every(r => r.passed);
            const failedCount = results.filter(r => !r.passed).length;

            if (allPassed) {
                // Reset consecutive failures on success
                this.consecutiveFailures = 0;
                CoachClient.sendSignal('run_success', 1, {
                    problem_id: this.currentProblemId,
                    tests_passed: results.length
                });
                console.log(`✅ All tests passed - coach notified`);
            } else {
                // Increment consecutive failures
                this.consecutiveFailures++;

                // Send signal on first failure or repeated failures
                if (this.consecutiveFailures >= 3) {
                    // 🚨 TRIGGER: Repeated failures = potential frustration
                    CoachClient.sendSignal('repeated_failure', this.consecutiveFailures, {
                        problem_id: this.currentProblemId,
                        failed_tests: failedCount,
                        total_tests: results.length,
                        error_type: 'wrong_answer'
                    });
                    console.log(`🔥 Repeated failures (${this.consecutiveFailures}) - coach notified`);
                } else {
                    // Single failure
                    CoachClient.sendSignal('run_failure', 1, {
                        problem_id: this.currentProblemId,
                        failed_tests: failedCount,
                        consecutive: this.consecutiveFailures
                    });
                }
            }

            return { success: true, results };

        } catch (compilationError: any) {
            return {
                success: false,
                error: typeof compilationError === 'string' ? compilationError : compilationError.message
            };
        }
    }
}

// Singleton instance
export const testRunner = new TestRunner();
