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
exports.validateUser = validateUser;
exports.getUserStats = getUserStats;
exports.getIdolJourney = getIdolJourney;
exports.compareUsers = compareUsers;
exports.getProblemContent = getProblemContent;
exports.searchCoders = searchCoders;
exports.getUserSolvedProblems = getUserSolvedProblems;
const axios_1 = __importDefault(require("axios"));
const vscode = __importStar(require("vscode"));
function getBackendUrl() {
    return vscode.workspace.getConfiguration('idolcode').get('backendUrl') || 'http://localhost:8000';
}
async function checkServerHealth() {
    try {
        const response = await axios_1.default.get(`${getBackendUrl()}/api/`, { timeout: 30000 });
        return response.status === 200;
    }
    catch (error) {
        return false;
    }
}
async function wakeUpServer(onStatusUpdate) {
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
async function validateUser(handle) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/user/${handle}/info`);
    return response.data;
}
async function getUserStats(handle) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/user/${handle}/stats`);
    return response.data;
}
async function getIdolJourney(handle, offset = 0, limit = 100) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/idol/${handle}/journey`, {
        params: { offset, limit }
    });
    return response.data;
}
async function compareUsers(userHandle, idolHandle) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/compare/${userHandle}/${idolHandle}`);
    return response.data;
}
async function getProblemContent(contestId, problemIndex) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/problem/${contestId}/${problemIndex}`);
    return response.data;
}
async function searchCoders(query) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/coders/search`, {
        params: { query, limit: 5 }
    });
    return response.data;
}
async function getUserSolvedProblems(handle) {
    const response = await axios_1.default.get(`${getBackendUrl()}/api/user/${handle}/solved-problems`);
    return response.data.solvedProblems;
}
//# sourceMappingURL=api.js.map