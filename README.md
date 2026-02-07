# checkDK

**Predict. Diagnose. Fix – Before You Waste Time.**

AI-powered CLI tool that detects and fixes Docker/Kubernetes issues before execution.

---

## Overview

checkDK is a CLI tool that wraps your Docker and Kubernetes commands to analyze configurations, predict failures, and suggest fixes before execution.

### Before
```bash
docker compose up
```
*Output:*
```text
❌ Error: port 8080 already in use
```

### After
```bash
checkDK docker compose up
```
*Output:*
```text
⚠️  Port conflict detected on 'web' service
💡 Fix: Port 8080 is used by nginx (PID 1234)
   Change to 8081:80 or run: sudo systemctl stop nginx
```

## Features

- **Pre-execution validation** of Docker/K8s configs
- **Detects issues**: Port conflicts, missing images, resource issues
- **AI-powered explanations** in plain English
- **Step-by-step fix suggestions**
- **Works offline** for core validation

## Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

Verify installation:
```bash
checkdk --version
```

## Usage

**Docker Compose**
```bash
checkDK docker compose up -d
```

**Kubernetes**
```bash
checkDK kubectl apply -f deployment.yaml
```

**Dry Run (No Execution)**
```bash
checkDK docker compose up --dry-run
```

## Configuration

Initialize the configuration:
```bash
checkDK init
```

Edit `~/.checkdk/config.yaml`:
```yaml
ai:
  provider: aws-bedrock
  model: claude-3-sonnet
```

## Requirements

- Python 3.10+
- Docker 20.10+ (for Docker analysis)
- `kubectl` (for K8s analysis - coming soon)

## Project Structure

```
checkDK/
├── backend/                    # Python CLI application
│   ├── checkdk/               # Main package
│   │   ├── cli.py            # CLI entry point
│   │   ├── parsers/          # Configuration parsers
│   │   ├── validators/       # Validation engines
│   │   └── executors/        # Command execution
│   ├── tests/                # Test suite
│   └── pyproject.toml        # Package configuration
├── frontend/                  # Web dashboard (React)
├── design.md                 # System design document
└── requirements.md           # Requirements specification
```

## How It Works

checkDK follows a simple flow:

1. **Parse**: Reads and validates your Docker Compose YAML
2. **Validate**: Checks for issues (port conflicts, missing images, etc.)
3. **Report**: Shows issues with fix suggestions
4. **Execute**: Runs your command (or blocks if critical errors found)

## What It Detects Now

✅ **Port Conflicts**
- Duplicate ports across services
- Ports already in use by system processes
- Shows which process is using the port

✅ **YAML Validation**
- Syntax errors
- Structural issues
- Missing required fields

✅ **Environment Variables**
- Missing environment variables (warnings)

## Example Output

**No issues:**
```bash
$ checkdk docker compose up --dry-run
✓ No issues found!
```

**Port conflict detected:**
```bash
$ checkdk docker compose up

✗ Critical Issues:

1. Port 8080 is used by multiple services: 'web1' and 'web2'
   💡 Suggested Fix:
   Change the port mapping to: "8081:80"
```

## Documentation

- [Quick Start Guide](backend/QUICKSTART.md)
- [Implementation Guide](IMPLEMENTATION.md)
- [Requirements Specification](requirements.md)
- [System Design](design.md)

## Coming Soon

- Image availability validation
- Resource limit validation
- AI-powered explanations
- Kubernetes support
- Auto-fix capabilities

## License

[MIT License](LICENSE)

---

**Made with ❤️ for developers who hate debugging configs**
