import { spawn } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

/**
 * Ensures the Python venv exists and dependencies are installed.
 * Then spawns digest.py and returns the path to the generated markdown file.
 */
export async function runPythonDigest(
  extensionPath: string,
  workspaceFolder: string,
  rssUrls: string[],
  licenseKey: string
): Promise<string> {
  const pythonDir = path.join(extensionPath, 'python');
  const venvDir = path.join(pythonDir, '.venv');
  const isWin = os.platform() === 'win32';
  const pythonBin = isWin
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python');

  // Bootstrap venv if needed
  if (!fs.existsSync(pythonBin)) {
    await bootstrapVenv(pythonDir, venvDir, isWin);
  }

  const scriptPath = path.join(pythonDir, 'digest.py');

  return new Promise((resolve, reject) => {
    const args = [
      scriptPath,
      '--workspace', workspaceFolder,
      '--rss', JSON.stringify(rssUrls),
    ];
    if (licenseKey) args.push('--license', licenseKey);

    const proc = spawn(pythonBin, args, { cwd: pythonDir });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data: Buffer) => { stdout += data.toString(); });
    proc.stderr.on('data', (data: Buffer) => { stderr += data.toString(); });

    proc.on('close', (code: number) => {
      if (code !== 0) {
        reject(new Error(stderr || `Python exited with code ${code}`));
      } else {
        const outputPath = stdout.trim();
        if (!outputPath || !fs.existsSync(outputPath)) {
          reject(new Error('digest.py did not return a valid file path.'));
        } else {
          resolve(outputPath);
        }
      }
    });

    proc.on('error', (err: Error) => reject(err));
  });
}

/**
 * Spawns digest.py with --export-pdf to convert the workspace digest markdown
 * to a PDF.  Resolves with the path to the generated PDF file.
 */
export function runPythonExport(
  extensionPath: string,
  workspaceFolder: string,
  licenseKey: string
): Promise<string> {
  const pythonDir = path.join(extensionPath, 'python');
  const venvDir = path.join(pythonDir, '.venv');
  const isWin = os.platform() === 'win32';
  const pythonBin = isWin
    ? path.join(venvDir, 'Scripts', 'python.exe')
    : path.join(venvDir, 'bin', 'python');

  const scriptPath = path.join(pythonDir, 'digest.py');

  return new Promise((resolve, reject) => {
    const args = [
      scriptPath,
      '--export-pdf',
      '--workspace', workspaceFolder,
      '--license', licenseKey,
    ];

    const proc = spawn(pythonBin, args, { cwd: pythonDir });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data: Buffer) => { stdout += data.toString(); });
    proc.stderr.on('data', (data: Buffer) => { stderr += data.toString(); });

    proc.on('close', (code: number) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `digest.py exited with code ${code}`));
        return;
      }
      const pdfPath = stdout.trim();
      if (!pdfPath) {
        reject(new Error('digest.py did not print a PDF path'));
        return;
      }
      resolve(pdfPath);
    });

    proc.on('error', (err: Error) => reject(err));
  });
}

function bootstrapVenv(pythonDir: string, venvDir: string, isWin: boolean): Promise<void> {
  return new Promise((resolve, reject) => {
    const proc = spawn('python3', ['-m', 'venv', venvDir], { cwd: pythonDir });
    proc.on('close', (code: number) => {
      if (code !== 0) { reject(new Error('Failed to create Python venv.')); return; }

      const pip = isWin
        ? path.join(venvDir, 'Scripts', 'pip.exe')
        : path.join(venvDir, 'bin', 'pip');

      const install = spawn(pip, ['install', '-r', 'requirements.txt'], { cwd: pythonDir });
      install.on('close', (c: number) => {
        if (c !== 0) reject(new Error('pip install failed.'));
        else resolve();
      });
      install.on('error', reject);
    });
    proc.on('error', reject);
  });
}
