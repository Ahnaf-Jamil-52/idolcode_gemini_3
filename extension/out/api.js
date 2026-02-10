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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.checkServerHealth = checkServerHealth;
exports.wakeUpServer = wakeUpServer;
exports.authLogin = authLogin;
exports.authRegister = authRegister;
exports.saveIdol = saveIdol;
exports.searchCoders = searchCoders;
exports.getDashboardData = getDashboardData;
exports.getSkillComparison = getSkillComparison;
exports.getProblemContent = getProblemContent;
exports.testCode = testCode;
exports.checkSubmissions = checkSubmissions;
exports.recordProblemAttempt = recordProblemAttempt;
exports.getRecommendations = getRecommendations;
exports.getUserSolvedProblems = getUserSolvedProblems;
exports.getProblemHistory = getProblemHistory;
exports.recordProblemHistory = recordProblemHistory;
const axios_1 = __importDefault(require("axios"));
const vscode = __importStar(require("vscode"));
/* ─── Helpers ────────────────────────────────────────────────────── */
function getBackendUrl() {
    return vscode.workspace.getConfiguration('idolcode').get('backendUrl') || 'http://localhost:8000';
}
/* ─── API Functions ──────────────────────────────────────────────── */
async function checkServerHealth() {
    try {
        const r = await axios_1.default.get(`${getBackendUrl()}/api/`, { timeout: 10000 });
        return r.status === 200;
    }
    catch {
        return false;
    }
}
async function wakeUpServer(onStatus) {
    for (let i = 1; i <= 3; i++) {
        onStatus?.(`Waking up server… (attempt ${i}/3)`);
        if (await checkServerHealth()) {
            onStatus?.('Server is ready!');
            return true;
        }
        if (i < 3) {
            onStatus?.('Server is sleeping, retrying in 5s…');
            await new Promise(r => setTimeout(r, 5000));
        }
    }
    onStatus?.('Server could not be reached');
    return false;
}
async function authLogin(handle, password) {
    const r = await axios_1.default.post(`${getBackendUrl()}/api/auth/login`, { handle, password }, { timeout: 15000 });
    return r.data;
}
async function authRegister(handle, password) {
    const r = await axios_1.default.post(`${getBackendUrl()}/api/auth/register`, { handle, password }, { timeout: 30000 });
    return r.data;
}
async function saveIdol(handle, idolHandle) {
    return axios_1.default.put(`${getBackendUrl()}/api/auth/idol`, { handle, idolHandle }, { timeout: 10000 });
}
async function searchCoders(query) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/coders/search`, { params: { query, limit: 5 }, timeout: 10000 });
    return r.data;
}
async function getDashboardData(userHandle, idolHandle, refresh = false) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/dashboard-data/${userHandle}`, { params: { refresh, idol: idolHandle }, timeout: 120000 });
    return r.data;
}
async function getSkillComparison(userHandle, idolHandle, topics) {
    const params = {};
    if (topics && topics.length > 0) {
        params.topics = topics.join(',');
    }
    const r = await axios_1.default.get(`${getBackendUrl()}/api/skill-comparison/${userHandle}/${idolHandle}`, { params, timeout: 30000 });
    return r.data;
}
async function getProblemContent(contestId, index) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/problem/${contestId}/${index}`, { timeout: 15000 });
    return r.data;
}
async function testCode(code, language, testCases) {
    const r = await axios_1.default.post(`${getBackendUrl()}/api/test-code`, { code, language, testCases }, { timeout: 60000 });
    return r.data.results;
}
async function checkSubmissions(userHandle, problemIds) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/check-submissions/${userHandle}`, { params: { problem_ids: problemIds.join(',') }, timeout: 30000 });
    return r.data;
}
async function recordProblemAttempt(data) {
    return axios_1.default.post(`${getBackendUrl()}/api/problem-attempt`, data, { timeout: 10000 });
}
async function getRecommendations(userHandle, idolHandle, refresh = false) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/recommendations/${userHandle}/${idolHandle}`, { params: { refresh }, timeout: 60000 });
    return r.data;
}
async function getUserSolvedProblems(handle) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/user/${handle}/solved-problems`, { timeout: 10000 });
    return r.data.solvedProblems;
}
async function getProblemHistory(handle) {
    const r = await axios_1.default.get(`${getBackendUrl()}/api/problem-history/${handle}`, { timeout: 10000 });
    return r.data.history || [];
}
async function recordProblemHistory(data) {
    return axios_1.default.post(`${getBackendUrl()}/api/problem-history`, data, { timeout: 10000 });
}
//# sourceMappingURL=api.js.map