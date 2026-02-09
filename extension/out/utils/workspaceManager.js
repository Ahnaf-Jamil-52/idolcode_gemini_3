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
Object.defineProperty(exports, "__esModule", { value: true });
exports.setupProblemWorkspace = setupProblemWorkspace;
exports.getProblemFolderPath = getProblemFolderPath;
const vscode = __importStar(require("vscode"));
const util_1 = require("util");
// C++ Competitive Programming Template
const CPP_TEMPLATE = `/**
 * IDOLCODE JOURNEY
 * Problem: {ID} - {TITLE}
 * -----------------------
 * "Follow the path of the master."
 */
#include <bits/stdc++.h>
using namespace std;

void solve() {
    // Your code here
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    solve();
    return 0;
}
`;
/**
 * Sets up a dedicated workspace folder for a competitive programming problem.
 * Creates the folder structure with solution.cpp and tests.json
 */
async function setupProblemWorkspace(problemId, problemTitle, examples) {
    // Check for open workspace
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        vscode.window.showErrorMessage('Idolcode: Please open a folder to start your journey.');
        return false;
    }
    const rootUri = vscode.workspace.workspaceFolders[0].uri;
    // Sanitize Folder Name (Remove spaces/special chars)
    const safeTitle = problemTitle.replace(/[^a-zA-Z0-9]/g, '');
    const folderName = `${problemId}_${safeTitle}`;
    const folderUri = vscode.Uri.joinPath(rootUri, folderName);
    // Create Directory
    try {
        await vscode.workspace.fs.createDirectory(folderUri);
    }
    catch (error) {
        // Directory might already exist, continue
        console.log(`Directory may already exist: ${error}`);
    }
    // Create solution.cpp with template
    const solutionUri = vscode.Uri.joinPath(folderUri, 'solution.cpp');
    const templateContent = CPP_TEMPLATE
        .replace('{ID}', problemId)
        .replace('{TITLE}', problemTitle);
    try {
        await vscode.workspace.fs.writeFile(solutionUri, new util_1.TextEncoder().encode(templateContent));
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to create solution.cpp: ${error}`);
        return false;
    }
    // Create tests.json with example test cases
    const testsUri = vscode.Uri.joinPath(folderUri, 'tests.json');
    const testsContent = JSON.stringify(examples, null, 2);
    try {
        await vscode.workspace.fs.writeFile(testsUri, new util_1.TextEncoder().encode(testsContent));
    }
    catch (error) {
        vscode.window.showErrorMessage(`Failed to create tests.json: ${error}`);
        return false;
    }
    // Open the solution file for the user to start coding
    try {
        const doc = await vscode.workspace.openTextDocument(solutionUri);
        await vscode.window.showTextDocument(doc);
    }
    catch (error) {
        console.error(`Failed to open solution file: ${error}`);
    }
    vscode.window.showInformationMessage(`🚀 Workspace ready: ${problemTitle}`);
    return true;
}
/**
 * Get the folder path for a problem based on problem ID and title
 */
function getProblemFolderPath(problemId, problemTitle) {
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        return undefined;
    }
    const rootPath = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const safeTitle = problemTitle.replace(/[^a-zA-Z0-9]/g, '');
    const folderName = `${problemId}_${safeTitle}`;
    return `${rootPath}/${folderName}`.replace(/\\/g, '/');
}
//# sourceMappingURL=workspaceManager.js.map