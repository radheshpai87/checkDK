# Running checkDK

There are three ways to run the project:

| Mode | What runs |
|------|-----------|
| **Option A** | Docker — backend + frontend together |
| **Option B** | Docker — backend only, then CLI via venv |
| **CLI** | Always a venv, always needs backend running |

---

## Option A — Docker: backend + frontend

Use this when you want the full web UI + API together.

```bash
# 1. Copy the root env template and fill in your API keys
cp .env.example .env
# open .env and set MISTRAL_API_KEY and/or GROQ_API_KEY

# 2. Build and start both containers
docker compose up --build

# 3. Stop
docker compose down
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

---

## Option B — Docker: backend only

Use this when you want to use the CLI without the web frontend.

```bash
# 1. Copy the root env template and fill in your API keys
cp .env.example .env
# open .env and set MISTRAL_API_KEY and/or GROQ_API_KEY

# 2. Start only the backend container
docker compose up --build backend

# 3. Stop
docker compose down
```

- Backend API: http://localhost:8000
- The CLI can now talk to it at `http://localhost:8000`

---

## CLI — venv (works with Option A or B)

The CLI is a standalone Python package. The backend must be running before using it.

```bash
cd cli

# 1. One-shot setup — creates .venv and installs the package
bash setup.sh

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Point the CLI at the running backend
export CHECKDK_API_URL=http://localhost:8000

# 4. Use it
checkdk --help
checkdk docker validate path/to/docker-compose.yml
checkdk docker validate path/to/docker-compose.yml --dry-run
checkdk k8s validate path/to/deployment.yml
checkdk k8s validate path/to/deployment.yml --dry-run
checkdk predict --cpu 85 --memory 78

# 5. Deactivate when done
deactivate
```

---

## Backend Tests

Run these inside the backend Docker container, or with a local venv if you set one up for development:

```bash
# Inside the running backend container
docker compose exec backend bash -c "pip install -e '.[dev]' && pytest tests/ -v"

# Or with a local venv (one-off dev setup)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[api,ml,dev]"
pytest tests/
pytest tests/ -v
pytest tests/ --cov=checkdk
```

---

## Quick reference

| What | Command | URL |
|------|---------|-----|
| Backend + frontend | `docker compose up --build` | :8000 + :3000 |
| Backend only | `docker compose up --build backend` | :8000 |
| CLI | `cd cli && bash setup.sh` → `checkdk --help` | → :8000 |
| Tests | `docker compose exec backend pytest tests/` | — |

