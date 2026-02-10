import * as vscode from 'vscode';
import { SidebarProvider } from './SidebarProvider';

export function activate(context: vscode.ExtensionContext) {
    const provider = new SidebarProvider(context.extensionUri, context);

    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider(SidebarProvider.viewType, provider, {
            webviewOptions: { retainContextWhenHidden: true },
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('idolcode.refresh', () => {
            vscode.commands.executeCommand('workbench.view.extension.idolcode-panel');
        }),
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('idolcode.resetData', async () => {
            const keys = ['idolcode.session', 'idolcode.viewState', 'idolcode.dashboardData'];
            for (const k of keys) await context.globalState.update(k, undefined);
            vscode.window.showInformationMessage('Idolcode data cleared. Reload to start fresh.');
        }),
    );
}

export function deactivate() {}
