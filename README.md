<div align="center">

# checkDK

**Predict. Diagnose. Fix – Before You Waste Time.**

AI-powered CLI tool that detects and fixes Docker/Kubernetes issues before execution.

</div>

## Overview

checkDK wraps your Docker and Kubernetes commands to analyze configurations, predict failures, and suggest fixes.

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
pip install checkdk
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

## What It Detects

- Port conflicts
- Missing environment variables
- Invalid YAML syntax
- Resource limit issues
- Service dependency problems
- Image availability

## Requirements

- Python 3.10+
- Docker 20.10+ (for Docker analysis)
- `kubectl` (for K8s analysis)

## Documentation

- [Requirements Specification](requirements.md)
- [System Design](design.md)

## License

[MIT License](LICENSE)

<div align="center">

**Made with ❤️ for developers who hate debugging configs**

</div>
