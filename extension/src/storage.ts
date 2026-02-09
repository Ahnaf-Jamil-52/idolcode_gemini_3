import * as vscode from 'vscode';
import { UserInfo, UserStats } from './api';

export interface StoredSession {
    userHandle: string;
    userInfo: UserInfo;
    idolHandle?: string;
    idolInfo?: UserStats;
}

const SESSION_KEY = 'idolcode.session';

export function saveSession(context: vscode.ExtensionContext, session: StoredSession): void {
    context.globalState.update(SESSION_KEY, session);
}

export function getSession(context: vscode.ExtensionContext): StoredSession | undefined {
    return context.globalState.get<StoredSession>(SESSION_KEY);
}

export function clearSession(context: vscode.ExtensionContext): void {
    context.globalState.update(SESSION_KEY, undefined);
}

export function updateIdol(context: vscode.ExtensionContext, idolHandle: string, idolInfo: UserStats): void {
    const session = getSession(context);
    if (session) {
        session.idolHandle = idolHandle;
        session.idolInfo = idolInfo;
        saveSession(context, session);
    }
}
