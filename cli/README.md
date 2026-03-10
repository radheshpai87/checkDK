# checkDK CLI

AI-powered CLI for Docker and Kubernetes — wraps `docker` and `kubectl` with
pre-execution analysis, real-time monitoring, chaos testing, and pod failure
prediction.

All analysis is delegated to the **checkDK backend API** at
[checkdk.app](https://checkdk.app). The CLI itself has no ML or LLM
dependencies — it is a thin HTTP/WebSocket client with a rich terminal UI.

---

## Install

```bash
# Recommended — isolated install, checkdk on PATH globally
pipx install checkdk-cli

# Or with plain pip
pip install checkdk-cli
```

Requires Python 3.10 or later.

The `checkdk` command is available immediately after install.
No configuration required — the CLI talks to `https://checkdk.app/api` by default.

---

## Authentication (required)

checkDK requires authentication before you can use any command (except `checkdk auth` and `checkdk init`).

```bash
# Sign in — opens your browser for GitHub/Google OAuth
checkdk auth login
```

This starts a local callback server, opens the sign-in page in your browser,
and receives the token automatically — no copy-pasting required.
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

---

## Uninstall

```bash
# If installed with pipx
pipx uninstall checkdk-cli

# If installed with pip
pip uninstall checkdk-cli

# Optionally remove stored config and credentials
rm -rf ~/.checkdk
```

---

## Commands

### Authentication

```bash
checkdk auth login       # open browser → OAuth sign-in → token saved to ~/.checkdk/.env
checkdk auth logout      # remove stored token
checkdk auth whoami      # show current logged-in user
```

> **Note:** You must be logged in to use any command other than `auth` and `init`.
> If your session has expired, the CLI will prompt you to log in again.

### Docker

```bash
checkdk docker compose up -d              # analyse docker-compose.yml, then run
checkdk docker compose up --dry-run       # analyse only, do not execute
checkdk docker -f custom.yml compose up   # specify a compose file explicitly
```

### Kubernetes

```bash
checkdk kubectl apply -f deploy.yaml      # analyse manifest, then apply
checkdk kubectl apply -f ./manifests/     # analyse an entire directory of YAMLs
```

### Playground

```bash
checkdk playground -f docker-compose.yml  # full AI + rule-based analysis
checkdk playground -f k8s/deploy.yaml
checkdk playground -f docker-compose.yml --json   # raw JSON output
```

### Predict

```bash
checkdk predict --cpu 93 --memory 91
checkdk predict --cpu 93 --memory 91 --no-ai            # ML only, skip LLM
checkdk predict --cpu 93 --memory 91 --restarts 3 \
                --probe-failures 2 --cpu-pressure 1 \
                --mem-pressure 1 --platform kubernetes
checkdk predict --cpu 85 --memory 70 --json             # CI/scripting output
```

| Option             | Default  | Description                       |
| ------------------ | -------- | --------------------------------- |
| `--cpu`            | required | CPU usage %                       |
| `--memory`         | required | Memory usage %                    |
| `--disk`           | 50       | Disk usage %                      |
| `--latency`        | 10       | Network latency ms                |
| `--restarts`       | 0        | Container restart count           |
| `--probe-failures` | 0        | Liveness/readiness probe failures |
| `--cpu-pressure`   | 0        | Node CPU pressure (0 or 1)        |
| `--mem-pressure`   | 0        | Node memory pressure (0 or 1)     |
| `--age`            | 60       | Pod age in minutes                |
| `--service`        | —        | Service/pod name (label only)     |
| `--platform`       | docker   | `docker` or `kubernetes`          |
| `--no-ai`          | —        | Skip LLM, return ML result only   |
| `--json`           | —        | Raw JSON output for scripting     |

### Monitor (real-time)

Polls live container/pod metrics and sends each sample to the prediction API,
displaying failure risk, confidence, and risk level in a Rich Live table.
Requires the container/pod to be running.

```bash
checkdk monitor docker my-container
checkdk monitor docker my-container --duration 120 --interval 3
checkdk monitor docker my-container --no-ai          # ML prediction only, skip LLM
checkdk monitor k8s my-pod -n production
checkdk monitor k8s my-pod -n production --no-ai
```

| Option       | Default | Description                                  |
| ------------ | ------- | -------------------------------------------- |
| `--duration` | 60      | How long to monitor, in seconds              |
| `--interval` | 5       | Seconds between each sample                  |
| `--no-ai`    | —       | Skip LLM analysis, return ML risk score only |
| `-n`         | default | Kubernetes namespace (k8s only)              |

### Chaos

Injects CPU/memory/disk/network stress or kills pods. Requires `stress-ng`
installed inside the container/pod image.

```bash
checkdk chaos docker my-container --experiment cpu --duration 60
checkdk chaos docker my-db --experiment memory --yes      # skip confirmation
checkdk chaos k8s my-pod -n production --experiment cpu
checkdk chaos k8s my-pod --experiment pod-kill --yes
```

Experiments: `cpu`, `memory`, `disk`, `network`, `pod-kill` (k8s only).

---

## Environment variables

| Variable          | Default                   | Description                                  |
| ----------------- | ------------------------- | -------------------------------------------- |
| `CHECKDK_API_URL` | `https://checkdk.app/api` | Backend API base URL                         |
| `CHECKDK_TOKEN`   | —                         | JWT auth token (set by `checkdk auth login`) |

The CLI auto-loads `~/.checkdk/.env` and `./.env` on startup.

---

## Local development

```bash
# From repo root — start backend on :8000
cp .env.example .env
docker compose up --build

# Point CLI at local backend
export CHECKDK_API_URL=http://localhost:8000

# Install CLI from source
cd cli
pip install -e ".[dev]"
```

```bash
# Run tests
pytest

# Lint
ruff check .
```
