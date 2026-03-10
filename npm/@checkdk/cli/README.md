# @checkdk/cli

AI-powered Docker/Kubernetes issue detector — available globally via npm.

## Install

```bash
npm install -g @checkdk/cli
```

No Python required. A pre-compiled native binary is automatically selected for
your platform (Linux x64/arm64, macOS x64/arm64, Windows x64).

## Authentication (required)

checkDK requires authentication before you can use any command (except `checkdk auth` and `checkdk init`).

```bash
# Sign in — opens your browser for GitHub/Google OAuth
checkdk auth login
```

This starts a local callback server, opens the sign-in page in your browser,
and receives the token automatically — no copy-pasting needed.
Once authenticated, your session is stored locally at `~/.checkdk/.env` and
persists until you explicitly log out or the token expires (7 days).

If you try to run any command without logging in first, the CLI will prompt:

```
Not logged in.
Run checkdk auth login to authenticate with your GitHub or Google account.
```

```bash
# Check who you're logged in as
checkdk auth whoami

# Log out (removes stored token)
checkdk auth logout
```

## Uninstall

```bash
npm uninstall -g @checkdk/cli

# Optionally remove stored config and credentials
rm -rf ~/.checkdk
```

## Usage

```bash
# Authenticate (required before using any command)
checkdk auth login

# Analyse a Docker Compose file (dry-run, no changes applied)
checkdk playground -f docker-compose.yml

# Analyse and then run
checkdk docker compose up -d

# Analyse a Kubernetes manifest and then apply
checkdk kubectl apply -f deployment.yaml

# Predict pod failure risk from live metrics
checkdk predict --cpu 85 --memory 78

# Real-time container monitoring
checkdk monitor docker my-container

# Inject chaos experiments
checkdk chaos docker my-container --experiment cpu --duration 60
```

Run `checkdk --help` for the full command reference.

## Platform support

| Platform                    | Installed package           |
| --------------------------- | --------------------------- |
| Linux x64                   | `@checkdk/cli-linux-x64`    |
| Linux arm64                 | `@checkdk/cli-linux-arm64`  |
| macOS x64 (Intel)           | `@checkdk/cli-darwin-x64`   |
| macOS arm64 (Apple Silicon) | `@checkdk/cli-darwin-arm64` |
| Windows x64                 | `@checkdk/cli-win32-x64`    |

If your platform is not listed, install via pip instead:

```bash
pip install checkdk-cli
```

## How it works

`@checkdk/cli` is an orchestrator package. When you install it, npm also
installs the platform-specific optional package that matches your OS and CPU
architecture. The `checkdk` binary inside that optional package is a
self-contained, standalone executable — no Python runtime is required.

The `bin/checkdk` entry point is a small Node.js shim that resolves the
correct binary path and exec-replaces itself, so all stdio and signal
handling work exactly as if you invoked the binary directly.

## Links

- Documentation: <https://checkdk.app/docs>
- Issues: <https://github.com/radheshpai87/checkDK/issues>
- PyPI: <https://pypi.org/project/checkdk-cli/>
