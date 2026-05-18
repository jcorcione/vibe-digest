import * as cp from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const PYTHON_DIR = path.join(__dirname, '..', '..', 'python');
const VENV_DIR = path.join(PYTHON_DIR, '.venv');
const REQUIREMENTS = path.join(PYTHON_DIR, 'requirements.txt');
const DIGEST_SCRIPT = path.join(PYTHON_DIR, 'digest.py');

function getPythonExecutable(): string {
  if (process.platform === 'win32') {
    return path.join(VENV_DIR, 'Scripts', 'python.exe');
  }
  return path.join(VENV_DIR, 'bin', 'python');
}

function isVenvBootstrapped(): boolean {
  return fs.existsSync(getPythonExecutable());
}

async function bootstrapVenv(): Promise<void> {
  return new Promise((resolve, reject) => {
    // Create venv
    const createVenv = cp.spawn(
      process.platform === 'win32' ? 'python' : 'python3',
      ['-m', 'venv', VENV_DIR],
      { cwd: PYTHON_DIR }
    );

    createVenv.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Failed to create Python venv (exit code ${code})`));
        return;
      }

      // Install requirements
      const pipExe =
        process.platform === 'win32'
          ? path.join(VENV_DIR, 'Scripts', 'pip.exe')
          : path.join(VENV_DIR, 'bin', 'pip');

      const install = cp.spawn(pipExe, ['install', '-r', REQUIREMENTS], {
        cwd: PYTHON_DIR,
      });

      install.on('close', (installCode) => {
        if (installCode !== 0) {
          reject(
            new Error(`Failed to install Python requirements (exit code ${installCode})`)
          );
          return;
        }
        resolve();
      });

      install.on('error', reject);
    });

    createVenv.on('error', reject);
  });
}

export async function runDigest(
  workspacePath: string,
  rssUrls: string[],
  licenseKey: string
): Promise<string> {
  if (!isVenvBootstrapped()) {
    await bootstrapVenv();
  }

  return new Promise((resolve, reject) => {
    const args: string[] = [
      DIGEST_SCRIPT,
      '--workspace', workspacePath,
      '--rss', JSON.stringify(rssUrls),
    ];

    if (licenseKey) {
      args.push('--license', licenseKey);
    }

    const pythonExe = getPythonExecutable();
    const proc = cp.spawn(pythonExe, args);

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data: Buffer) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data: Buffer) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Python process exited with code ${code}`));
        return;
      }
      const outputPath = stdout.trim();
      if (!outputPath) {
        reject(new Error('Python script did not output a file path'));
        return;
      }
      resolve(outputPath);
    });

    proc.on('error', (err) => {
      reject(new Error(`Failed to start Python process: ${err.message}`));
    });
  });
}
