# checkDK

**AI-powered Docker Compose & Kubernetes configuration validator — available at [checkdk.app](https://checkdk.app)**

Catch port conflicts, security misconfigurations, missing health probes, and more before they cost you time in production. Upload a config file, get an instant analysis with AI-generated fix suggestions, and keep a searchable history of every scan.

---

## Features

- **Web UI** — upload or paste a config file and get results instantly at [checkdk.app](https://checkdk.app)
- **Docker Compose analysis** — port conflicts, broken dependencies, missing resource limits, undefined env vars, `:latest` tags
- **Kubernetes analysis** — NodePort conflicts, selector/label mismatches, privilege escalation, missing health probes
- **AI-powered fixes** — Mistral & Groq LLMs explain each issue and give you copy-paste-ready remediation steps
- **ML risk prediction** — RandomForest model estimates the probability of pod/container failure
- **Analysis history** — every scan is stored per-user; search and re-open past results
- **GitHub & Google OAuth** — sign in with your existing account, no password required
- **CLI** — optional `checkdk` CLI wrapper for local use (see [cli/README.md](cli/README.md))

---

## Live Demo

Visit **[checkdk.app](https://checkdk.app)** — no sign-up required for the playground.

Sign in with GitHub or Google to save your analysis history.

---

## Architecture

```
Browser
  │
  ├─▶  CloudFront CDN  ──▶  S3 (React SPA)
  │
  └─▶  CloudFront /api/*  ──▶  AWS App Runner (FastAPI backend)
                                        │
                                        ├── DynamoDB  (users + history)
                                        ├── Mistral / Groq  (AI fixes)
                                        └── RandomForest model  (risk score)
```

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite 7, TailwindCSS 4 |
| Backend | FastAPI, Python 3.11, Uvicorn |
| Auth | GitHub OAuth, Google OAuth, JWT (HS256) |
| Database | AWS DynamoDB |
| AI | Mistral AI, Groq (Llama 3.3 70B) |
| ML | scikit-learn RandomForest |
| Hosting | AWS App Runner (backend), S3 + CloudFront (frontend) |
| CI/CD | GitHub Actions → ECR → App Runner + S3 |

---

## Local Development

### Prerequisites

- Docker and Docker Compose v2
- An `.env` file in the project root (see below)

### 1. Create `.env`

```bash
# OAuth (create apps at github.com/settings/developers and console.cloud.google.com)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# JWT
JWT_SECRET=change-me-to-a-long-random-string

# AI providers (optional — analysis still works without them)
GROQ_API_KEY=
MISTRAL_API_KEY=

# AWS (required for DynamoDB history storage)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
DYNAMODB_REGION=us-east-1
DYNAMODB_USERS_TABLE=checkdk_users
DYNAMODB_HISTORY_TABLE=checkdk_history
```

### 2. Start the stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

> **Note:** The custom `10.201.0.0/24` subnet is set in `docker-compose.yml` to avoid conflicts with common home-network ranges.

### 3. Run backend tests

```bash
cd backend
pip install -e ".[api,ml]"
pytest tests/ -v
```

### 4. CLI (optional)

The CLI is a separate Python package. The backend must be running first.

```bash
cd cli
bash setup.sh                    # creates .venv and installs the package
source .venv/bin/activate
export CHECKDK_API_URL=http://localhost:8000

checkdk docker validate path/to/docker-compose.yml --dry-run
checkdk k8s validate path/to/deployment.yml --dry-run
checkdk predict --cpu 85 --memory 78

deactivate
```

To use the CLI against production, set `CHECKDK_API_URL=https://checkdk.app/api`.

---

## What It Validates

### Docker Compose
- Port conflicts between services
- Missing images or build specs
- Broken service dependencies (`depends_on`)
- Undefined environment variables
- Missing resource limits (`deploy.resources`)
- `:latest` image tags
- Undefined volumes / networks

### Kubernetes
- NodePort conflicts
- Duplicate ports within a Service
- Selector / label mismatches
- Security issues (privileged containers, running as root)
- Missing liveness / readiness probes
- Missing resource limits / requests
- `:latest` image tags

---

## Example Output

```
┌─────────────────────── Analysis ───────────────────────┐
│ File: docker-compose-complex.yml                       │
│ Score: 23 / 100  ▓░░░░░░░░░░░░░░░                      │
└────────────────────────────────────────────────────────┘

🔴 Critical Issues (7)

1. Port conflict — services 'web' and 'web2' both bind port 8080
   Fix: Change 'web2' port mapping to 8081:80

2. Undefined variable — 'backend' references ${DB_URL} (not set)
   Fix: Add DB_URL to your .env file or remove the reference

⚠  Warnings (10)

1. 'frontend' uses :latest tag — pin to a specific digest for reproducibility
2. 'backend' has no CPU/memory limits — at risk in resource-constrained environments

╭────────────── AI Suggestion ──────────────╮
│ Top priority: resolve the port conflict.  │
│ Both containers will fail to start until  │
│ one of them is remapped.                  │
╰───────────────────────────────────────────╯
```

---

## CI / CD

GitHub Actions runs automatically on every pull request and every merge to `main`.

| Workflow | Trigger | Steps |
|---|---|---|
| **CI** | PR to `main` | pytest, `tsc --noEmit`, ESLint |
| **Deploy** | Push to `main` | Build & push Docker image to ECR → deploy to App Runner → build frontend → sync to S3 → invalidate CloudFront |

AWS authentication uses OIDC (no long-lived AWS keys stored in GitHub). See [.github/iam-policy-github-actions.json](.github/iam-policy-github-actions.json) for the minimum required permissions.

Required GitHub repository secrets:

| Secret | Value |
|---|---|
| `AWS_ROLE_ARN` | IAM role ARN for OIDC |
| `VITE_API_BASE_URL` | Production API URL |
| `VITE_GITHUB_CLIENT_ID` | GitHub OAuth app client ID |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth app client ID |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID |

---

## Roadmap

| Phase | Feature | Status |
|---|---|---|
| 1 | AWS infrastructure (App Runner, S3, CloudFront, ECR) | ✅ Complete |
| 2 | Auth + Database (GitHub/Google OAuth, JWT, DynamoDB history) | ✅ Complete |
| 3 | Post-login app interface (dashboard, playground, get-started) | ✅ Complete |
| 4 | CI/CD (GitHub Actions — pytest, lint, ECR deploy, S3 sync) | ✅ Complete |
| 5 | Real-time monitoring (WebSocket pod metrics stream, recharts) | 🔲 Planned |
| 6 | Chaos dataset + ML retraining (real EKS failure data via Chaos Mesh) | 🔲 Planned |
| 7 | Amazon Bedrock (replace Mistral with Claude Haiku via IAM role) | 🔲 Planned |

---

## ML Prediction API

The backend exposes four prediction endpoints for Kubernetes pod failure risk:

| Endpoint | Model |
|---|---|
| `POST /predict/random-forest` | scikit-learn RandomForest |
| `POST /predict/xgboost` | XGBoost |
| `POST /predict/lstm` | PyTorch LSTM |
| `POST /predict/ensemble` | Majority vote across all three |

**Request fields:** `cpu_usage`, `memory_usage`, `disk_usage`, `network_latency`, `restart_count`, `probe_failures`, `node_cpu_pressure`, `node_memory_pressure`, `pod_age_minutes`

Example — ensemble prediction (failure case):

```bash
curl -X POST https://checkdk.app/api/predict/ensemble \
  -H "Content-Type: application/json" \
  -d '{
    "cpu_usage": 94.5,
    "memory_usage": 96.2,
    "disk_usage": 88.0,
    "network_latency": 45.0,
    "restart_count": 7,
    "probe_failures": 4,
    "node_cpu_pressure": 1,
    "node_memory_pressure": 1,
    "pod_age_minutes": 95
  }'
```

```json
{
  "ensemble_label": "failure",
  "ensemble_confidence": 0.87,
  "random_forest": { "label": "failure", "confidence": 0.62 },
  "xgboost":       { "label": "failure", "confidence": 1.00 },
  "lstm":          { "label": "failure", "confidence": 1.00 }
}
```

Replace `https://checkdk.app/api` with `http://localhost:8000` for local use.

---

## Project Structure

```
checkDK/
├── backend/                   # FastAPI application
│   └── checkdk/
│       ├── api/               # Routes (auth, analysis, history)
│       ├── ai/                # Mistral & Groq providers
│       ├── ml/                # RandomForest predictor + training
│       ├── parsers/           # Docker Compose & Kubernetes YAML parsers
│       ├── validators/        # Rule-based validators
│       └── services/          # Business logic
├── frontend/                  # React + Vite SPA
│   └── src/
│       ├── components/        # UI components + dashboard + playground
│       ├── contexts/          # AuthContext
│       ├── lib/               # API client, mock analyzer, utilities
│       └── pages/
├── cli/                       # Optional CLI wrapper (`checkdk` command)
├── ml-models/                 # Standalone model training scripts
├── .github/
│   ├── workflows/
│   │   ├── ci.yml             # PR checks
│   │   └── deploy.yml         # Production deployment
│   ├── iam-policy-github-actions.json
│   └── trust-policy.json
├── docker-compose.yml         # Local development stack
└── .env                       # Local secrets (not committed)
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make your changes — CI will run automatically on your PR
4. Open a pull request against `main`

Please keep pull requests focused; one feature or fix per PR.

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Support

- **Bugs / feature requests**: [open an issue](https://github.com/radheshpai87/checkDK/issues)
- **Questions**: open a discussion

---

**Made with ❤️ for developers who want to catch issues early**
