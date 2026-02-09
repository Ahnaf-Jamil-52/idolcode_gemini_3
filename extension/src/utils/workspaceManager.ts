import * as vscode from 'vscode';
import { TextEncoder } from 'util';

// Define the shape of your example data based on your API
interface ProblemExample {
    input: string;
    output: string;
}

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
export async function setupProblemWorkspace(
    problemId: string,
    problemTitle: string,
    examples: ProblemExample[]
): Promise<boolean> {
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
    } catch (error) {
        // Directory might already exist, continue
        console.log(`Directory may already exist: ${error}`);
    }

    // Create solution.cpp with template
    const solutionUri = vscode.Uri.joinPath(folderUri, 'solution.cpp');
    const templateContent = CPP_TEMPLATE
        .replace('{ID}', problemId)
        .replace('{TITLE}', problemTitle);

    try {
        await vscode.workspace.fs.writeFile(
            solutionUri,
            new TextEncoder().encode(templateContent)
        );
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to create solution.cpp: ${error}`);
        return false;
    }

    // Create tests.json with example test cases
    const testsUri = vscode.Uri.joinPath(folderUri, 'tests.json');
    const testsContent = JSON.stringify(examples, null, 2);

    try {
        await vscode.workspace.fs.writeFile(
            testsUri,
            new TextEncoder().encode(testsContent)
        );
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to create tests.json: ${error}`);
        return false;
    }

    // Open the solution file for the user to start coding
    try {
        const doc = await vscode.workspace.openTextDocument(solutionUri);
        await vscode.window.showTextDocument(doc);
    } catch (error) {
        console.error(`Failed to open solution file: ${error}`);
    }

    vscode.window.showInformationMessage(`🚀 Workspace ready: ${problemTitle}`);
    return true;
}

/**
 * Get the folder path for a problem based on problem ID and title
 */
export function getProblemFolderPath(problemId: string, problemTitle: string): string | undefined {
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        return undefined;
    }

    const rootPath = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const safeTitle = problemTitle.replace(/[^a-zA-Z0-9]/g, '');
    const folderName = `${problemId}_${safeTitle}`;

    return `${rootPath}/${folderName}`.replace(/\\/g, '/');
}

