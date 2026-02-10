"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.saveSession = saveSession;
exports.getSession = getSession;
exports.clearSession = clearSession;
exports.updateIdol = updateIdol;
exports.saveViewState = saveViewState;
exports.getViewState = getViewState;
exports.saveDashboardData = saveDashboardData;
exports.getDashboardData = getDashboardData;
const SESSION_KEY = 'idolcode.session';
const VIEW_KEY = 'idolcode.viewState';
const DASHBOARD_KEY = 'idolcode.dashboardData';
/* ─── Session ─────────────────────────────────────────────────── */
async function saveSession(ctx, s) {
    await ctx.globalState.update(SESSION_KEY, s);
}
function getSession(ctx) {
    return ctx.globalState.get(SESSION_KEY);
}
async function clearSession(ctx) {
    await ctx.globalState.update(SESSION_KEY, undefined);
    await ctx.globalState.update(VIEW_KEY, undefined);
    await ctx.globalState.update(DASHBOARD_KEY, undefined);
}
async function updateIdol(ctx, idolHandle, idolInfo) {
    const s = getSession(ctx);
    if (s) {
        s.idolHandle = idolHandle;
        s.idolInfo = idolInfo;
        await saveSession(ctx, s);
    }
}
/* ─── View State ──────────────────────────────────────────────── */
async function saveViewState(ctx, vs) {
    await ctx.globalState.update(VIEW_KEY, vs);
}
function getViewState(ctx) {
    return ctx.globalState.get(VIEW_KEY);
}
/* ─── Dashboard Cache ─────────────────────────────────────────── */
async function saveDashboardData(ctx, data) {
    await ctx.globalState.update(DASHBOARD_KEY, data);
}
function getDashboardData(ctx) {
    return ctx.globalState.get(DASHBOARD_KEY);
}
//# sourceMappingURL=storage.js.map