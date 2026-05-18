// __mocks__/vscode.ts
// Minimal VS Code API mock for Jest tests

const vscode = {
  commands: {
    registerCommand: jest.fn(),
    executeCommand: jest.fn(),
  },
  window: {
    showInformationMessage: jest.fn(),
    showErrorMessage: jest.fn(),
    withProgress: jest.fn((_opts: unknown, task: () => Promise<void>) => task()),
    createOutputChannel: jest.fn(() => ({
      appendLine: jest.fn(),
      show: jest.fn(),
    })),
  },
  workspace: {
    getConfiguration: jest.fn(() => ({
      get: jest.fn(),
    })),
    workspaceFolders: [],
    onDidChangeConfiguration: jest.fn(() => ({ dispose: jest.fn() })),
  },
  ProgressLocation: {
    Notification: 15,
    SourceControl: 1,
    Window: 10,
  },
  Uri: {
    file: jest.fn((p: string) => ({ fsPath: p })),
  },
  EventEmitter: jest.fn(() => ({
    event: jest.fn(),
    fire: jest.fn(),
    dispose: jest.fn(),
  })),
};

export = vscode;
