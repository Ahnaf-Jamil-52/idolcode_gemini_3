import * as vscode from 'vscode';
import { UserInfo, UserStats, ProblemContent, ComparisonData, RecommendedProblem, SkillComparisonData, HistoryItem } from './api';

export type ViewState = 'wakeup' | 'login' | 'idol-selection' | 'dashboard' | 'problem';

export interface StoredSession {
    userHandle: string;
    userInfo: UserInfo;
    idolHandle?: string;
    idolInfo?: UserStats;
}

export interface SavedViewState {
    currentView: ViewState;
    currentProblem?: ProblemContent;
}

export interface SavedDashboardData {
    comparison: ComparisonData | null;
    recommendations: RecommendedProblem[];
    recDescription: string;
    skillComparison: SkillComparisonData | null;
    history: HistoryItem[];
    solvedProblems: string[];
}

const SESSION_KEY = 'idolcode.session';
const VIEW_KEY = 'idolcode.viewState';
const DASHBOARD_KEY = 'idolcode.dashboardData';

/* ─── Session ─────────────────────────────────────────────────── */
export async function saveSession(ctx: vscode.ExtensionContext, s: StoredSession) {
    await ctx.globalState.update(SESSION_KEY, s);
}

export function getSession(ctx: vscode.ExtensionContext): StoredSession | undefined {
    return ctx.globalState.get<StoredSession>(SESSION_KEY);
}

export async function clearSession(ctx: vscode.ExtensionContext) {
    await ctx.globalState.update(SESSION_KEY, undefined);
    await ctx.globalState.update(VIEW_KEY, undefined);
    await ctx.globalState.update(DASHBOARD_KEY, undefined);
}

export async function updateIdol(ctx: vscode.ExtensionContext, idolHandle: string, idolInfo: UserStats) {
    const s = getSession(ctx);
    if (s) {
        s.idolHandle = idolHandle;
        s.idolInfo = idolInfo;
        await saveSession(ctx, s);
    }
}

/* ─── View State ──────────────────────────────────────────────── */
export async function saveViewState(ctx: vscode.ExtensionContext, vs: SavedViewState) {
    await ctx.globalState.update(VIEW_KEY, vs);
}

export function getViewState(ctx: vscode.ExtensionContext): SavedViewState | undefined {
    return ctx.globalState.get<SavedViewState>(VIEW_KEY);
}

/* ─── Dashboard Cache ─────────────────────────────────────────── */
export async function saveDashboardData(ctx: vscode.ExtensionContext, data: SavedDashboardData) {
    await ctx.globalState.update(DASHBOARD_KEY, data);
}

export function getDashboardData(ctx: vscode.ExtensionContext): SavedDashboardData | undefined {
    return ctx.globalState.get<SavedDashboardData>(DASHBOARD_KEY);
}
