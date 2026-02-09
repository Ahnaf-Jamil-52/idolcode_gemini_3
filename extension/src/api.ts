import axios from 'axios';
import * as vscode from 'vscode';

// Types matching backend models
export interface UserInfo {
    handle: string;
    rating?: number;
    rank?: string;
    maxRating?: number;
    maxRank?: string;
    avatar?: string;
    titlePhoto?: string;
    contribution?: number;
    friendOfCount?: number;
    registrationTimeSeconds?: number;
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

export interface ProblemInfo {
    contestId?: number;
    index: string;
    name: string;
    rating?: number;
    tags: string[];
    problemId: string;
    solvedAt?: number;
    ratingAtSolve?: number;
    wasContestSolve: boolean;
}

export interface IdolJourney {
    problems: ProblemInfo[];
    totalProblems: number;
    hasMore: boolean;
}

export interface ComparisonData {
    user: UserStats;
    idol: UserStats;
    progressPercent: number;
    userAhead: boolean;
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

export interface CoderSuggestion {
    handle: string;
    rating?: number;
    rank?: string;
    maxRating?: number;
    maxRank?: string;
    avatar?: string;
}

function getBackendUrl(): string {
    return vscode.workspace.getConfiguration('idolcode').get('backendUrl') || 'http://localhost:8000';
}

export async function checkServerHealth(): Promise<boolean> {
    try {
        const response = await axios.get(`${getBackendUrl()}/api/`, { timeout: 30000 });
        return response.status === 200;
    } catch (error) {
        return false;
    }
}

export async function wakeUpServer(onStatusUpdate?: (message: string) => void): Promise<boolean> {
    const maxRetries = 3;
    const retryDelay = 5000;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        onStatusUpdate?.(`Waking up server... (attempt ${attempt}/${maxRetries})`);

        const isHealthy = await checkServerHealth();
        if (isHealthy) {
            onStatusUpdate?.('Server is ready!');
            return true;
        }

        if (attempt < maxRetries) {
            onStatusUpdate?.(`Server is sleeping, retrying in ${retryDelay / 1000}s...`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
    }

    onStatusUpdate?.('Server could not be reached');
    return false;
}

export async function validateUser(handle: string): Promise<UserInfo> {
    const response = await axios.get(`${getBackendUrl()}/api/user/${handle}/info`);
    return response.data;
}

export async function getUserStats(handle: string): Promise<UserStats> {
    const response = await axios.get(`${getBackendUrl()}/api/user/${handle}/stats`);
    return response.data;
}

export async function getIdolJourney(handle: string, offset: number = 0, limit: number = 100): Promise<IdolJourney> {
    const response = await axios.get(`${getBackendUrl()}/api/idol/${handle}/journey`, {
        params: { offset, limit }
    });
    return response.data;
}

export async function compareUsers(userHandle: string, idolHandle: string): Promise<ComparisonData> {
    const response = await axios.get(`${getBackendUrl()}/api/compare/${userHandle}/${idolHandle}`);
    return response.data;
}

export async function getProblemContent(contestId: number, problemIndex: string): Promise<ProblemContent> {
    const response = await axios.get(`${getBackendUrl()}/api/problem/${contestId}/${problemIndex}`);
    return response.data;
}

export async function searchCoders(query: string): Promise<CoderSuggestion[]> {
    const response = await axios.get(`${getBackendUrl()}/api/coders/search`, {
        params: { query, limit: 5 }
    });
    return response.data;
}

export async function getUserSolvedProblems(handle: string): Promise<string[]> {
    const response = await axios.get(`${getBackendUrl()}/api/user/${handle}/solved-problems`);
    return response.data.solvedProblems;
}
