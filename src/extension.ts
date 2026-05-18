import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { runPythonDigest } from './utils/pythonRunner';
import { parseCronToMs } from './utils/cronHelper';

let autoRunTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext) {
  console.log('Vibe Digest extension activated.');

  const disposable = vscode.commands.registerCommand('newsletter.digest', async () => {
    await runDigest(context);
  });

  context.subscriptions.push(disposable);

  // Set up auto-run if configured
  setupAutoRun(context);

  // Re-setup auto-run if settings change
  vscode.workspace.onDidChangeConfiguration(e => {
    if (
      e.affectsConfiguration('vibeDigest.autoRun') ||
      e.affectsConfiguration('vibeDigest.cron')
    ) {
      setupAutoRun(context);
    }
  });
}

async function runDigest(context: vscode.ExtensionContext) {
  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showErrorMessage('Vibe Digest: No workspace folder open.');
    return;
  }

  const workspaceFolder = workspaceFolders[0].uri.fsPath;
  const config = vscode.workspace.getConfiguration('vibeDigest');
  const rssUrls: string[] = config.get('rssUrls') || [];
  const licenseKey: string = config.get('licenseKey') || '';

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: 'Vibe Digest: Generating digest…',
      cancellable: false,
    },
    async () => {
      try {
        const outputPath = await runPythonDigest(context.extensionPath, workspaceFolder, rssUrls, licenseKey);
        const uri = vscode.Uri.file(outputPath);
        await vscode.commands.executeCommand('markdown.showPreview', uri);
        vscode.window.showInformationMessage('✅ Newsletter digest ready!', 'Open File').then(sel => {
          if (sel === 'Open File') {
            vscode.window.showTextDocument(uri);
          }
        });
      } catch (err: any) {
        vscode.window.showErrorMessage(`Vibe Digest Error: ${err.message}`, 'View Log').then(sel => {
          if (sel === 'View Log') {
            vscode.commands.executeCommand('workbench.action.toggleDevTools');
          }
        });
      }
    }
  );
}

function setupAutoRun(context: vscode.ExtensionContext) {
  if (autoRunTimer) {
    clearTimeout(autoRunTimer);
    autoRunTimer = undefined;
  }

  const config = vscode.workspace.getConfiguration('vibeDigest');
  const autoRun: boolean = config.get('autoRun') || false;
  const cronExpr: string = config.get('cron') || '0 8 * * *';

  if (!autoRun) return;

  const msUntilNext = parseCronToMs(cronExpr);
  if (msUntilNext <= 0) return;

  autoRunTimer = setTimeout(() => {
    vscode.commands.executeCommand('newsletter.digest');
    setupAutoRun(context); // reschedule
  }, msUntilNext);

  console.log(`Vibe Digest: auto-run scheduled in ${Math.round(msUntilNext / 60000)} minutes.`);
}

export function deactivate() {
  if (autoRunTimer) {
    clearTimeout(autoRunTimer);
  }
}
