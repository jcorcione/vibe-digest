import * as cp from "child_process";
import * as path from "path";

/**
 * Spawns digest.py with --export-pdf to convert the workspace digest markdown
 * to a PDF.  Resolves with the path to the generated PDF file.
 */
export function runPythonExport(
  extensionPath: string,
  workspaceFolder: string,
  licenseKey: string
): Promise<string> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(extensionPath, "digest.py");
    const args = [
      scriptPath,
      "--export-pdf",
      "--workspace",
      workspaceFolder,
      "--license-key",
      licenseKey,
    ];

    const proc = cp.spawn("python3", args, { cwd: workspaceFolder });

    let stdout = "";
    let stderr = "";

    proc.stdout.on("data", (data: Buffer) => {
      stdout += data.toString();
    });

    proc.stderr.on("data", (data: Buffer) => {
      stderr += data.toString();
    });

    proc.on("close", (code: number | null) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `digest.py exited with code ${code}`));
        return;
      }
      const pdfPath = stdout.trim();
      if (!pdfPath) {
        reject(new Error("digest.py did not print a PDF path"));
        return;
      }
      resolve(pdfPath);
    });

    proc.on("error", (err: Error) => {
      reject(err);
    });
  });
}
