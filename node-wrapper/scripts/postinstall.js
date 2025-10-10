#!/usr/bin/env node

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Postinstall script for mcp-test-mcp
 *
 * This script:
 * 1. Checks for Python 3.11+ availability
 * 2. Creates a virtual environment
 * 3. Installs the bundled Python package
 */

const isWindows = process.platform === 'win32';
const packageRoot = path.join(__dirname, '..');
const venvPath = path.join(packageRoot, '.venv');
const pythonSrcPath = path.join(packageRoot, 'python-src');

console.log('🔧 Setting up mcp-test-mcp...');

/**
 * Find Python 3.11+ executable
 */
function findPython() {
  const pythonCommands = isWindows
    ? ['python', 'python3', 'py']
    : ['python3.13', 'python3.12', 'python3.11', 'python3', 'python'];

  for (const cmd of pythonCommands) {
    try {
      const version = execSync(`${cmd} --version`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      }).trim();

      // Extract version number (e.g., "Python 3.11.5" -> "3.11")
      const match = version.match(/Python (\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);

        if (major === 3 && minor >= 11) {
          console.log(`✓ Found ${version}`);
          return cmd;
        }
      }
    } catch (error) {
      // Command not found, try next one
      continue;
    }
  }

  return null;
}

/**
 * Create virtual environment
 */
function createVenv(pythonCmd) {
  console.log('📦 Creating virtual environment...');

  try {
    execSync(`${pythonCmd} -m venv "${venvPath}"`, {
      stdio: 'inherit',
      cwd: packageRoot
    });
    console.log('✓ Virtual environment created');
    return true;
  } catch (error) {
    console.error('✗ Failed to create virtual environment:', error.message);
    return false;
  }
}

/**
 * Install Python package
 */
function installPythonPackage() {
  console.log('📥 Installing mcp-test-mcp Python package...');

  const pipExecutable = isWindows
    ? path.join(venvPath, 'Scripts', 'pip.exe')
    : path.join(venvPath, 'bin', 'pip');

  try {
    // Upgrade pip first
    execSync(`"${pipExecutable}" install --upgrade pip`, {
      stdio: 'inherit',
      cwd: packageRoot
    });

    // Install the bundled Python package
    execSync(`"${pipExecutable}" install "${pythonSrcPath}"`, {
      stdio: 'inherit',
      cwd: packageRoot
    });

    console.log('✓ Python package installed successfully');
    return true;
  } catch (error) {
    console.error('✗ Failed to install Python package:', error.message);
    return false;
  }
}

/**
 * Main installation flow
 */
function main() {
  // Check if Python source exists
  if (!fs.existsSync(pythonSrcPath)) {
    console.error('✗ Error: Python source code not found at:', pythonSrcPath);
    console.error('This is a packaging issue. Please report this bug.');
    process.exit(1);
  }

  // Find Python
  const pythonCmd = findPython();
  if (!pythonCmd) {
    console.error('✗ Error: Python 3.11 or higher is required but not found.');
    console.error('Please install Python 3.11+ from https://www.python.org/downloads/');
    process.exit(1);
  }

  // Create virtual environment
  if (!createVenv(pythonCmd)) {
    process.exit(1);
  }

  // Install Python package
  if (!installPythonPackage()) {
    process.exit(1);
  }

  console.log('\n✅ Installation complete!');
  console.log('You can now use: npx mcp-test-mcp');
}

// Run installation
main();
