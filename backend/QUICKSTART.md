# checkDK Quick Start Guide

## Installation

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install checkDK in development mode:**
   ```bash
   pip install -e .
   ```

## Basic Usage

### Test with Example File

1. **Copy the example docker-compose file:**
   ```bash
   cp example-docker-compose.yml docker-compose.yml
   ```

2. **Run checkDK analysis:**
   ```bash
   checkdk docker compose up
   ```

   This will:
   - Analyze the docker-compose.yml file
   - Check for port conflicts
   - Validate the configuration
   - Show any issues found
   - Execute the command if no critical errors

### Dry Run (Analysis Only)

To analyze without executing:
```bash
checkdk docker compose up --dry-run
```

### Force Execution

To execute even with critical errors:
```bash
checkdk docker compose up --force
```

## Examples

### Example 1: Detect Port Conflict

If port 8080 is already in use:

```bash
checkdk docker compose up
```

**Output:**
```
✗ Critical Issues:

1. Port 8080 on service 'web' is already in use by nginx (PID 1234)
   Service: web

   💡 Suggested Fix:
   Option 1: Stop the process using port 8080
     sudo kill 1234  # Stop nginx
   Option 2: Change the port mapping in docker-compose.yml
     ports:
       - "8081:80"  # Change 8080 to 8081

✗ Execution blocked due to critical issues.
```

### Example 2: Missing Environment Variable

If `API_KEY` is not set:

```bash
checkdk docker compose up
```

**Output:**
```
⚠ Warnings:

1. Environment variable not set: API_KEY

Summary
─────────────
Warnings: 1

⚠ Warnings detected. Proceed with execution?
Continue? (y/N):
```

### Example 3: Valid Configuration

If everything is good:

```bash
checkdk docker compose up
```

**Output:**
```
✓ No issues found!
Your configuration looks good.

→ Executing: docker compose up
```

## Initialize Configuration

Set up AI features (optional):

```bash
checkdk init
```

This creates `~/.checkdk/config.yaml` with your preferences.

## Run Tests

```bash
pytest
```

## What's Implemented

✅ **CLI Framework**
- Command interception
- Docker Compose support
- Rich terminal output
- Dry-run mode

✅ **Docker Compose Parser**
- YAML parsing with validation
- Environment variable resolution
- Service extraction

✅ **Port Validator**
- Duplicate port detection
- System port conflict detection
- Process information lookup
- Fix suggestions

✅ **Command Executor**
- Safe pass-through to Docker
- Error handling
- User prompts

## What's Next

🚧 **Coming Soon:**
- Image availability validator
- Resource limit validator
- Volume mount validator
- Network configuration validator
- AI-powered explanations (AWS Bedrock/Claude)
- Kubernetes support
- Web dashboard

## Troubleshooting

### Command not found: checkdk

Make sure you've installed the package:
```bash
pip install -e .
```

And that your virtual environment is activated.

### Docker not found

Make sure Docker is installed and running:
```bash
docker --version
docker ps
```

### Permission errors checking ports

On Linux, you may need to run with sudo or add your user to the docker group:
```bash
sudo usermod -aG docker $USER
```

## Project Structure

```
backend/
├── checkdk/
│   ├── __init__.py
│   ├── cli.py              # CLI entry point ✅
│   ├── config.py           # Configuration management ✅
│   ├── models.py           # Data models ✅
│   ├── parsers/
│   │   ├── __init__.py
│   │   └── docker_compose.py  # Docker Compose parser ✅
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── port_validator.py  # Port conflict checker ✅
│   └── executors/
│       ├── __init__.py
│       └── docker_executor.py  # Command executor ✅
├── tests/
│   ├── __init__.py
│   ├── test_docker_compose_parser.py
│   └── test_port_validator.py
├── pyproject.toml
├── README.md
└── QUICKSTART.md
```

## Contributing

Feel free to add more validators, parsers, or features! The architecture is modular and extensible.
