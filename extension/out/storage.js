"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.saveSession = saveSession;
exports.getSession = getSession;
exports.clearSession = clearSession;
exports.updateIdol = updateIdol;
const SESSION_KEY = 'idolcode.session';
function saveSession(context, session) {
    context.globalState.update(SESSION_KEY, session);
}
function getSession(context) {
    return context.globalState.get(SESSION_KEY);
}
function clearSession(context) {
    context.globalState.update(SESSION_KEY, undefined);
}
function updateIdol(context, idolHandle, idolInfo) {
    const session = getSession(context);
    if (session) {
        session.idolHandle = idolHandle;
        session.idolInfo = idolInfo;
        saveSession(context, session);
    }
}
//# sourceMappingURL=storage.js.map