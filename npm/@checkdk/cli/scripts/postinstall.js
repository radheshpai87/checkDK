"use strict";

/**
 * postinstall.js
 *
 * Runs after `npm install -g @checkdk/cli`.  Its job is to verify that the
 * platform-specific binary package was successfully installed as an optional
 * dependency, and to print a clear message either way.
 */

const os = require("os");
const path = require("path");

const PLATFORM_MAP = {
  "linux-x64":    "@checkdk/cli-linux-x64",
  "linux-arm64":  "@checkdk/cli-linux-arm64",
  "darwin-x64":   "@checkdk/cli-darwin-x64",
  "darwin-arm64": "@checkdk/cli-darwin-arm64",
  "win32-x64":    "@checkdk/cli-win32-x64",
};

const key = `${os.platform()}-${os.arch()}`;
const pkg = PLATFORM_MAP[key];

if (!pkg) {
  console.warn(
    `\n[checkdk] WARNING: Your platform (${key}) is not supported by the npm binary distribution.\n` +
    `Install via pip instead:\n\n` +
    `    pip install checkdk-cli\n`
  );
  // Exit 0 so the overall install does not fail.
  process.exit(0);
}

// Check if the optional package resolved correctly.
let found = false;
try {
  require.resolve(`${pkg}/package.json`);
  found = true;
} catch {
  // optional dep was not installed (e.g. npm skipped it)
}

if (found) {
  console.log(`\n[checkdk] Successfully installed for ${key} via ${pkg}`);
  console.log(`[checkdk] Run "checkdk --help" to get started.\n`);
} else {
  console.warn(
    `\n[checkdk] WARNING: The optional package "${pkg}" was not installed.\n` +
    `This can happen when npm skips optional dependencies.\n\n` +
    `Try running:\n` +
    `    npm install -g @checkdk/cli --optional\n\n` +
    `Or use pip as a fallback:\n` +
    `    pip install checkdk-cli\n`
  );
}
