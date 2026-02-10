import axios from 'axios';
import * as vscode from 'vscode';

/* ─── Types ──────────────────────────────────────────────────────── */

export interface UserInfo {
    handle: string;
    rating?: number;
    rank?: string;
    maxRating?: number;
    maxRank?: string;
    avatar?: string;
}

export interface UserStats {
    handle: string;
    rating?: number;
    rank?: string;
    maxRating?: number;
    maxRank?: string;
    problemsSolved: number;
    contestsParticipated: number;
    contestWins: number;
}

export interface ComparisonData {
    user: UserStats;
    idol: UserStats;
    progressPercent: number;
    userAhead: boolean;
}

export interface RecommendedProblem {
    problemId: string;
    contestId: number;
    index: string;
    name: string;
    rating?: number;
    tags: string[];
    difficulty: 'Easy' | 'Medium' | 'Hard';
    url: string;
}

export interface RecommendationResponse {
    recommendations: RecommendedProblem[];
    description: string;
    generatedAt: string;
    cached: boolean;
}

export interface SkillStat {
    topic: string;
    user: number;
    idol: number;
    gap: number;
}

export interface WeakTopic {
    topic: string;
    gap: number;
    problems: { name: string; rating: number; url: string; contestId: number; index: string }[];
}

export interface SkillComparisonData {
    stats: SkillStat[];
    weakestTopics: WeakTopic[];
    userRating: number;
    idolRatingAtComparison: number;
    allTopics: string[];
}

export interface ProblemExample {
    input: string;
    output: string;
}

export interface ProblemContent {
    contestId: number;
    index: string;
    name: string;
    timeLimit: string;
    memoryLimit: string;
    problemStatement: string;
    inputSpecification: string;
    outputSpecification: string;
    examples: ProblemExample[];
    note: string;
    rating?: number;
    tags: string[];
    url: string;
}

export interface DashboardData {
    idol: string;
    comparison: ComparisonData | null;
    recommendations: RecommendationResponse | null;
    skillComparison: SkillComparisonData | null;
    history: HistoryItem[];
}

export interface HistoryItem {
    id?: string;
    problemId: string;
    contestId: number;
    index: string;
    name: string;
    rating?: number;
    tags: string[];
    difficulty: string;
    status: 'solved' | 'failed' | 'attempted';
    attemptedAt?: string;
}

export interface CoderSuggestion {
    handle: string;
    rating?: number;
    rank?: string;
    avatar?: string;
}

export interface AuthResponse {
    success: boolean;
    handle: string;
    rating?: number;
    maxRating?: number;
    avatar?: string;
    idol?: string;
}

export interface TestResult {
    testIndex: number;
    passed: boolean;
    input: string;
    expectedOutput: string;
    actualOutput: string;
    error?: string;
    executionTime?: number;
}

/* ─── Helpers ────────────────────────────────────────────────────── */

function getBackendUrl(): string {
    return vscode.workspace.getConfiguration('idolcode').get('backendUrl') || 'http://localhost:8000';
}

/* ─── API Functions ──────────────────────────────────────────────── */

export async function checkServerHealth(): Promise<boolean> {
    try {
        const r = await axios.get(`${getBackendUrl()}/api/`, { timeout: 10000 });
        return r.status === 200;
    } catch { return false; }
}

export async function wakeUpServer(onStatus?: (msg: string) => void): Promise<boolean> {
    for (let i = 1; i <= 3; i++) {
        onStatus?.(`Waking up server… (attempt ${i}/3)`);
        if (await checkServerHealth()) { onStatus?.('Server is ready!'); return true; }
        if (i < 3) { onStatus?.('Server is sleeping, retrying in 5s…'); await new Promise(r => setTimeout(r, 5000)); }
    }
    onStatus?.('Server could not be reached');
    return false;
}

export async function authLogin(handle: string, password: string): Promise<AuthResponse> {
    const r = await axios.post(`${getBackendUrl()}/api/auth/login`, { handle, password }, { timeout: 15000 });
    return r.data;
}

export async function authRegister(handle: string, password: string): Promise<AuthResponse> {
    const r = await axios.post(`${getBackendUrl()}/api/auth/register`, { handle, password }, { timeout: 30000 });
    return r.data;
}

export async function saveIdol(handle: string, idolHandle: string) {
    return axios.put(`${getBackendUrl()}/api/auth/idol`, { handle, idolHandle }, { timeout: 10000 });
}

export async function searchCoders(query: string): Promise<CoderSuggestion[]> {
    const r = await axios.get(`${getBackendUrl()}/api/coders/search`, { params: { query, limit: 5 }, timeout: 10000 });
    return r.data;
}

export async function getDashboardData(userHandle: string, idolHandle: string, refresh = false): Promise<DashboardData> {
    const r = await axios.get(`${getBackendUrl()}/api/dashboard-data/${userHandle}`, { params: { refresh, idol: idolHandle }, timeout: 120000 });
    return r.data;
}

export async function getSkillComparison(userHandle: string, idolHandle: string, topics?: string[]): Promise<SkillComparisonData> {
    const params: any = {};
    if (topics && topics.length > 0) { params.topics = topics.join(','); }
    const r = await axios.get(`${getBackendUrl()}/api/skill-comparison/${userHandle}/${idolHandle}`, { params, timeout: 30000 });
    return r.data;
}

export async function getProblemContent(contestId: number, index: string): Promise<ProblemContent> {
    const r = await axios.get(`${getBackendUrl()}/api/problem/${contestId}/${index}`, { timeout: 15000 });
    return r.data;
}

export async function testCode(code: string, language: string, testCases: ProblemExample[]): Promise<TestResult[]> {
    const r = await axios.post(`${getBackendUrl()}/api/test-code`, { code, language, testCases }, { timeout: 60000 });
    return r.data.results;
}

export async function checkSubmissions(userHandle: string, problemIds: string[]): Promise<Record<string, { solved: boolean }>> {
    const r = await axios.get(`${getBackendUrl()}/api/check-submissions/${userHandle}`, { params: { problem_ids: problemIds.join(',') }, timeout: 30000 });
    return r.data;
}

export async function recordProblemAttempt(data: any) {
    return axios.post(`${getBackendUrl()}/api/problem-attempt`, data, { timeout: 10000 });
}

export async function getRecommendations(userHandle: string, idolHandle: string, refresh = false): Promise<RecommendationResponse> {
    const r = await axios.get(`${getBackendUrl()}/api/recommendations/${userHandle}/${idolHandle}`, { params: { refresh }, timeout: 60000 });
    return r.data;
}

export async function getUserSolvedProblems(handle: string): Promise<string[]> {
    const r = await axios.get(`${getBackendUrl()}/api/user/${handle}/solved-problems`, { timeout: 10000 });
    return r.data.solvedProblems;
}

export async function getProblemHistory(handle: string): Promise<HistoryItem[]> {
    const r = await axios.get(`${getBackendUrl()}/api/problem-history/${handle}`, { timeout: 10000 });
    return r.data.history || [];
}

export async function recordProblemHistory(data: any) {
    return axios.post(`${getBackendUrl()}/api/problem-history`, data, { timeout: 10000 });
}
