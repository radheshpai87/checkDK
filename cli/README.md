# checkDK CLI

Thin CLI tool that wraps `docker` and `kubectl` commands with pre-execution
analysis, and provides a `predict` command for pod failure detection.

All analysis is delegated to the **checkDK backend API** running in Docker.
The CLI itself has no ML or LLM dependencies — it is just an HTTP client with
a rich terminal UI.

---

## Quick start

```bash
# 1. Clone and enter the cli folder
cd cli

# 2. Run the setup script (creates .venv + installs the package)
bash setup.sh

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Point at the backend (start it first with docker compose)
export CHECKDK_API_URL=http://localhost:8000
# — or save it permanently:
checkdk init
```

---

## Start the backend first

```bash
# From the repo root
cp .env.example .env          # add GROQ_API_KEY / GEMINI_API_KEY
docker compose up --build     # starts backend on :8000, frontend on :3000
```

---

## Commands

| Command | Description |
|---|---|
| `checkdk init` | Save API URL + keys to `~/.checkdk/.env` |
| `checkdk docker compose up -d` | Analyse `docker-compose.yml`, then run the command |
| `checkdk docker compose up --dry-run` | Analyse only, do not execute |
| `checkdk kubectl apply -f deploy.yaml` | Analyse Kubernetes manifest, then apply |
| `checkdk predict --cpu 93 --memory 91` | Predict pod failure risk |
| `checkdk predict --cpu 93 --memory 91 --no-ai` | ML prediction only, skip LLM |

### Predict options

```
  --cpu            CPU usage % (required)
  --memory         Memory usage % (required)
  --disk           Disk usage % (default 50)
  --latency        Network latency ms (default 10)
  --restarts       Restart count (default 0)
  --probe-failures Probe failure count (default 0)
  --cpu-pressure   Node CPU pressure 0/1 (default 0)
  --mem-pressure   Node memory pressure 0/1 (default 0)
  --age            Pod age in minutes (default 60)
  --service        Service/pod name (optional label)
  --platform       docker | kubernetes (default docker)
  --no-ai          Skip LLM analysis
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `CHECKDK_API_URL` | `http://localhost:8000` | Backend API base URL |

The CLI auto-loads `~/.checkdk/.env` and `./.env` on startup.

---

## Development

```bash
# Install with dev extras
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```
