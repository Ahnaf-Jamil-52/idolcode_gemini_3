import * as vscode from 'vscode';
import { UserInfo, UserStats, ProblemContent } from './api';

export type ViewState = 'wakeup' | 'login' | 'idol-selection' | 'workspace' | 'problem-solving';

export interface StoredSession {
    userHandle: string;
    userInfo: UserInfo;
    idolHandle?: string;
    idolInfo?: UserStats;
}

export interface StoredViewState {
    currentView: ViewState;
    currentProblemId?: string;
    currentProblem?: ProblemContent;
}

const SESSION_KEY = 'idolcode.session';
const VIEW_STATE_KEY = 'idolcode.viewState';

export function saveSession(context: vscode.ExtensionContext, session: StoredSession): void {
    context.globalState.update(SESSION_KEY, session);
}

export function getSession(context: vscode.ExtensionContext): StoredSession | undefined {
    return context.globalState.get<StoredSession>(SESSION_KEY);
}

export function clearSession(context: vscode.ExtensionContext): void {
    context.globalState.update(SESSION_KEY, undefined);
    context.globalState.update(VIEW_STATE_KEY, undefined);
}

export function updateIdol(context: vscode.ExtensionContext, idolHandle: string, idolInfo: UserStats): void {
    const session = getSession(context);
    if (session) {
        session.idolHandle = idolHandle;
        session.idolInfo = idolInfo;
        saveSession(context, session);
    }
}

export function saveViewState(context: vscode.ExtensionContext, viewState: StoredViewState): void {
    context.globalState.update(VIEW_STATE_KEY, viewState);
}

export function getViewState(context: vscode.ExtensionContext): StoredViewState | undefined {
    return context.globalState.get<StoredViewState>(VIEW_STATE_KEY);
}

export function updateCurrentProblem(context: vscode.ExtensionContext, problem: ProblemContent): void {
    const viewState: StoredViewState = {
        currentView: 'problem-solving',
        currentProblemId: `${problem.contestId}${problem.index}`,
        currentProblem: problem
    };
    saveViewState(context, viewState);
}

export function updateCurrentView(context: vscode.ExtensionContext, view: ViewState): void {
    const existing = getViewState(context);
    const viewState: StoredViewState = {
        currentView: view,
        currentProblemId: existing?.currentProblemId,
        currentProblem: view === 'problem-solving' ? existing?.currentProblem : undefined
    };
    saveViewState(context, viewState);
}
