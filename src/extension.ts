import * as vscode from 'vscode';
import { runDigest } from './utils/pythonRunner';
import { parseCronToMs } from './utils/cronHelper';

let autoRunTimer: NodeJS.Timeout | undefined;

export function activate(context: vscode.ExtensionContext): void {
  const command = vscode.commands.registerCommand('newsletter.digest', async () => {
    await runDigestCommand();
  });

  context.subscriptions.push(command);

  scheduleAutoRun(context);

  // Re-schedule when configuration changes
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (
        e.affectsConfiguration('vibeDigest.autoRun') ||
        e.affectsConfiguration('vibeDigest.cron')
      ) {
        scheduleAutoRun(context);
      }
    })
  );
}

async function runDigestCommand(): Promise<void> {
  const config = vscode.workspace.getConfiguration('vibeDigest');
  const rssUrls: string[] = config.get<string[]>('rssUrls', []);
  const licenseKey: string = config.get<string>('licenseKey', '');

  const workspaceFolders = vscode.workspace.workspaceFolders;
  if (!workspaceFolders || workspaceFolders.length === 0) {
    vscode.window.showErrorMessage('Vibe Digest: No workspace folder is open.');
    return;
  }
  const workspacePath = workspaceFolders[0].uri.fsPath;

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: 'Vibe Digest: Generating digest…',
      cancellable: false,
    },
    async () => {
      try {
        const outputPath = await runDigest(workspacePath, rssUrls, licenseKey);
        const outputUri = vscode.Uri.file(outputPath);
        await vscode.commands.executeCommand('markdown.showPreview', outputUri);
        vscode.window.showInformationMessage(
          `Vibe Digest: Digest ready → ${outputPath}`
        );
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`Vibe Digest: ${message}`);
      }
    }
  );
}

function scheduleAutoRun(context: vscode.ExtensionContext): void {
  if (autoRunTimer) {
    clearInterval(autoRunTimer);
    autoRunTimer = undefined;
  }

  const config = vscode.workspace.getConfiguration('vibeDigest');
  const autoRun = config.get<boolean>('autoRun', false);
  if (!autoRun) {
    return;
  }

  const cronExpr = config.get<string>('cron', '0 8 * * *');
  const intervalMs = parseCronToMs(cronExpr);

  autoRunTimer = setInterval(() => {
    runDigestCommand();
  }, intervalMs);

  context.subscriptions.push({
    dispose: () => {
      if (autoRunTimer) {
        clearInterval(autoRunTimer);
      }
    },
  });
}

export function deactivate(): void {
  if (autoRunTimer) {
    clearInterval(autoRunTimer);
  }
}
