# Contributing to checkDK

Thanks for taking the time to contribute! Here's everything you need to get started.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/<your-username>/checkDK.git`
3. Create a branch: `git checkout -b feat/my-feature` or `git checkout -b fix/my-bug`
4. Make your changes, then open a pull request against `main`

---

## Development Setup

**Prerequisites:** Docker + Docker Compose v2, Python 3.11+, Node.js 20+

```bash
# 1. Copy the env template
cp .env.example .env
# Fill in at minimum: JWT_SECRET, and DEV OAuth credentials

# 2. Start the full stack
docker compose up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
# API docs → http://localhost:8000/docs
```

**Backend tests:**

```bash
cd backend
pip install -e ".[api,ml]"
pytest tests/ -v
```

**Frontend lint + type-check:**

```bash
cd frontend
npm ci
npx tsc --noEmit
npm run lint
```

---

## How to Contribute

- **Bug fix** — open an issue first if it's non-trivial, then submit a PR
- **New validator rule** — add it under `backend/checkdk/validators/`, cover it with a test
- **New AI provider** — extend `backend/checkdk/ai/providers.py`, keep Groq as fallback
- **Frontend component** — keep it in the relevant `components/` subdirectory, use TailwindCSS
- **Documentation** — improve README, add code comments, fix typos — all welcome

---

## Pull Request Process

1. Keep PRs focused — one feature or fix per PR
2. Make sure all CI checks pass (pytest, tsc, ESLint) before requesting review
3. Add or update tests if you're changing backend logic
4. Update README if you're adding a user-visible feature
5. A maintainer will review and merge; expect feedback within a few days

**Branch naming:**

| Prefix | Use for |
|---|---|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation only |
| `chore/` | Tooling, deps, config |
| `test/` | Test-only changes |

---

## Coding Standards

**Python (backend):**
- Follow PEP 8; use type hints everywhere
- Docstrings for public functions and classes
- Keep validators stateless and side-effect free

**TypeScript (frontend):**
- No `any` types — use `unknown` or proper interfaces
- Components in `.tsx`, utilities in `.ts`
- Keep components small; extract hooks for logic

**General:**
- Prefer explicit over clever
- Leave code better than you found it

---

## Reporting Bugs

Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) issue template. Please include:

- What you expected to happen
- What actually happened
- Steps to reproduce
- Relevant config file (sanitize any secrets)
- Environment (OS, Docker version, browser if frontend)

---

## Suggesting Features

Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) issue template. Describe the problem you're trying to solve, not just the solution — it helps us find the best approach together.

---

## Code of Conduct

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).
