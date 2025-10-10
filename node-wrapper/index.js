#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Node.js wrapper for mcp-test-mcp Python FastMCP server
 *
 * This script spawns the Python MCP server process and handles stdio communication.
 */

// Handle --version flag
if (process.argv.includes('--version') || process.argv.includes('-v')) {
  const packageJson = require('./package.json');
  console.log(`mcp-test-mcp v${packageJson.version}`);
  process.exit(0);
}

// Determine the path to the Python executable in the virtual environment
const isWindows = process.platform === 'win32';
const venvPath = path.join(__dirname, '.venv');
const pythonExecutable = isWindows
  ? path.join(venvPath, 'Scripts', 'python.exe')
  : path.join(venvPath, 'bin', 'python');

// Check if the virtual environment exists
if (!fs.existsSync(pythonExecutable)) {
  console.error('Error: Python virtual environment not found.');
  console.error('The postinstall script should have created it automatically.');
  console.error('Please try reinstalling: npm install -g mcp-test-mcp');
  console.error(`Expected Python at: ${pythonExecutable}`);
  process.exit(1);
}

// Arguments to pass to the Python server
// Format: python -m mcp_test_mcp [args...]
const args = ['-m', 'mcp_test_mcp', ...process.argv.slice(2)];

// Spawn the Python process
const pythonProcess = spawn(pythonExecutable, args, {
  stdio: ['inherit', 'inherit', 'inherit'],
  env: { ...process.env }
});

// Handle process termination
pythonProcess.on('error', (error) => {
  console.error('Failed to start Python MCP server:', error.message);
  process.exit(1);
});

pythonProcess.on('exit', (code, signal) => {
  if (signal) {
    process.exit(128 + (signal === 'SIGINT' ? 2 : 15));
  } else {
    process.exit(code || 0);
  }
});

// Handle signals gracefully
const handleSignal = (signal) => {
  if (pythonProcess && !pythonProcess.killed) {
    pythonProcess.kill(signal);
  }
};

process.on('SIGINT', () => handleSignal('SIGINT'));
process.on('SIGTERM', () => handleSignal('SIGTERM'));
process.on('SIGHUP', () => handleSignal('SIGHUP'));
