import * as vscode from 'vscode';
import { SidebarProvider } from './SidebarProvider';
import { clearSession } from './storage';

export function activate(context: vscode.ExtensionContext) {
    console.log('Idolcode extension is now active!');

    // Create sidebar provider
    const sidebarProvider = new SidebarProvider(context.extensionUri, context);

    // Register the webview view provider
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(
            'idolcode-panel',
            sidebarProvider
        )
    );

    // Track active editor changes to auto-detect problem folders
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor) {
                sidebarProvider.handleActiveFileChange(editor.document.uri);
            }
        })
    );

    // Register logout command
    context.subscriptions.push(
        vscode.commands.registerCommand('idolcode.logout', () => {
            clearSession(context);
            sidebarProvider.refresh();
            vscode.window.showInformationMessage('Logged out of Idolcode');
        })
    );

    // Register change idol command
    context.subscriptions.push(
        vscode.commands.registerCommand('idolcode.changeIdol', () => {
            sidebarProvider.showIdolSelection();
        })
    );
}

export function deactivate() {
    console.log('Idolcode extension deactivated');
}

