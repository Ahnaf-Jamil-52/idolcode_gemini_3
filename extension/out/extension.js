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
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const SidebarProvider_1 = require("./SidebarProvider");
const storage_1 = require("./storage");
function activate(context) {
    console.log('Idolcode extension is now active!');
    // Create sidebar provider
    const sidebarProvider = new SidebarProvider_1.SidebarProvider(context.extensionUri, context);
    // Register the webview view provider
    context.subscriptions.push(vscode.window.registerWebviewViewProvider('idolcode-panel', sidebarProvider));
    // Register logout command
    context.subscriptions.push(vscode.commands.registerCommand('idolcode.logout', () => {
        (0, storage_1.clearSession)(context);
        sidebarProvider.refresh();
        vscode.window.showInformationMessage('Logged out of Idolcode');
    }));
    // Register change idol command
    context.subscriptions.push(vscode.commands.registerCommand('idolcode.changeIdol', () => {
        sidebarProvider.showIdolSelection();
    }));
}
function deactivate() {
    console.log('Idolcode extension deactivated');
}
//# sourceMappingURL=extension.js.map