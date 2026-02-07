# checkDK Backend

AI-powered CLI tool that detects and fixes Docker/Kubernetes issues before execution.

## Installation

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install with AI features
pip install -e ".[dev,ai]"

# Install with Kubernetes support
pip install -e ".[dev,k8s]"
```

## Usage

```bash
# Basic usage
checkdk docker compose up

# With flags
checkdk docker compose up -d

# Kubernetes
checkdk kubectl apply -f deployment.yaml

# Dry run (analysis only, no execution)
checkdk docker compose up --dry-run

# Show version
checkdk --version

# Initialize configuration
checkdk init
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black checkdk/
ruff check checkdk/
```

### Type Checking

```bash
mypy checkdk/
```

## Project Structure

```
backend/
├── checkdk/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── config.py           # Configuration management
│   ├── models.py           # Data models
│   ├── parsers/            # Configuration parsers
│   ├── validators/         # Validation rules
│   ├── predictors/         # Runtime prediction
│   ├── ai/                 # AI integration
│   └── executors/          # Command execution
├── tests/
├── pyproject.toml
└── README.md
```
