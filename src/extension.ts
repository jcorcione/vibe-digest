import * as vscode from "vscode";
import { runPythonExport } from "./pythonRunner";

export function activate(context: vscode.ExtensionContext): void {
  const exportPdfCmd = vscode.commands.registerCommand(
    "newsletter.exportPdf",
    async () => {
      const config = vscode.workspace.getConfiguration("vibeDigest");
      const licenseKey: string = config.get<string>("licenseKey", "").trim();

      if (!licenseKey) {
        vscode.window.showErrorMessage(
          "PDF export is a Pro feature. Add your license key in settings."
        );
        return;
      }

      const folders = vscode.workspace.workspaceFolders;
      if (!folders || folders.length === 0) {
        vscode.window.showErrorMessage("No workspace folder is open.");
        return;
      }

      const workspaceFolder = folders[0].uri.fsPath;

      try {
        const pdfPath = await runPythonExport(
          context.extensionPath,
          workspaceFolder,
          licenseKey
        );
        await vscode.env.openExternal(vscode.Uri.file(pdfPath));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        vscode.window.showErrorMessage(`PDF export failed: ${message}`);
      }
    }
  );

  context.subscriptions.push(exportPdfCmd);
}

export function deactivate(): void {}
