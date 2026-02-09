"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.saveSession = saveSession;
exports.getSession = getSession;
exports.clearSession = clearSession;
exports.updateIdol = updateIdol;
exports.saveViewState = saveViewState;
exports.getViewState = getViewState;
exports.updateCurrentProblem = updateCurrentProblem;
exports.updateCurrentView = updateCurrentView;
const SESSION_KEY = 'idolcode.session';
const VIEW_STATE_KEY = 'idolcode.viewState';
function saveSession(context, session) {
    context.globalState.update(SESSION_KEY, session);
}
function getSession(context) {
    return context.globalState.get(SESSION_KEY);
}
function clearSession(context) {
    context.globalState.update(SESSION_KEY, undefined);
    context.globalState.update(VIEW_STATE_KEY, undefined);
}
function updateIdol(context, idolHandle, idolInfo) {
    const session = getSession(context);
    if (session) {
        session.idolHandle = idolHandle;
        session.idolInfo = idolInfo;
        saveSession(context, session);
    }
}
function saveViewState(context, viewState) {
    context.globalState.update(VIEW_STATE_KEY, viewState);
}
function getViewState(context) {
    return context.globalState.get(VIEW_STATE_KEY);
}
function updateCurrentProblem(context, problem) {
    const viewState = {
        currentView: 'problem-solving',
        currentProblemId: `${problem.contestId}${problem.index}`,
        currentProblem: problem
    };
    saveViewState(context, viewState);
}
function updateCurrentView(context, view) {
    const existing = getViewState(context);
    const viewState = {
        currentView: view,
        currentProblemId: existing?.currentProblemId,
        currentProblem: view === 'problem-solving' ? existing?.currentProblem : undefined
    };
    saveViewState(context, viewState);
}
//# sourceMappingURL=storage.js.map