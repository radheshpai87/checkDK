# checkDK

**AI-powered Docker and Kubernetes configuration validator**

🔍 Predict. Diagnose. Fix – Before You Waste Time.

---

## What is checkDK?

checkDK analyzes your Docker Compose and Kubernetes configurations **before** you run them, catching errors and suggesting fixes.

```bash
# Instead of this... 
docker compose up
# ❌ Error: port 8080 already in use

# Do this...
checkdk docker compose up --dry-run
# ✅ Found 7 issues with AI-powered fixes
```

---

## Installation

```bash
# 1. Clone and install
cd backend
pip install -e .

# 2. Add API keys to .env file
echo "GROQ_API_KEY=your_groq_key" >> .env
echo "GEMINI_API_KEY=your_gemini_key" >> .env

# 3. Run
checkdk docker compose up --dry-run
```

**Get Free API Keys:**
- [Groq Console](https://console.groq.com) - 14,400 requests/day
- [Google AI](https://ai.google.dev) - 60 requests/minute

---

## Usage

### Docker Compose

```bash
# Analyze without running
checkdk docker compose up --dry-run

# Analyze specific file
checkdk docker compose -f my-compose.yml up --dry-run

# Run after analysis passes
checkdk docker compose up

# Force run despite errors
checkdk docker compose up --force
```

### Kubernetes

```bash
# Analyze manifest
checkdk kubectl apply -f deployment.yml --dry-run

# Apply after analysis
checkdk kubectl apply -f deployment.yml

# Force apply
checkdk kubectl apply -f deployment.yml --force
```

---

## Example Output

```
checkDK v0.1.0
Predict. Diagnose. Fix – Before You Waste Time.

Analyzing: docker-compose.yml

🤖 AI analysis enabled

✗ Critical Issues:

1. Port 8080 is used by multiple services: 'web1' and 'web2'
   Service: web2

   💡 AI-Enhanced Fix:
   The error occurs because both services are trying to use port 8080
   on the host machine, which is not allowed.

   Root Cause: Docker Compose does not allow multiple services to 
   bind to the same port on the host machine.

   Steps:
   • Change the port mapping for 'web2' to '8081:80'
   • Update the Docker Compose configuration file
   • Restart the services

⚠ Warnings:

1. Service 'frontend' uses 'latest' tag for image
2. Service 'backend' references undefined environment variable '${DB_URL}'
3. Production service 'backend' has no resource limits

╭──────────────────── Summary ────────────────────╮
│ Critical:  7                                    │
│ Warnings:  10                                   │
╰─────────────────────────────────────────────────╯

--dry-run: Analysis complete. Skipping execution.
```

---

## What It Detects

### Docker Compose
- ✅ Port conflicts between services
- ✅ Missing images or build specs
- ✅ Broken service dependencies
- ✅ Undefined environment variables
- ✅ Missing resource limits
- ✅ Using `:latest` image tags
- ✅ Undefined volumes/networks

### Kubernetes
- ✅ NodePort conflicts
- ✅ Duplicate ports in services
- ✅ Selector/label mismatches
- ✅ Security issues (privileged containers, running as root)
- ✅ Missing health probes (liveness/readiness)
- ✅ Missing resource limits
- ✅ Using `:latest` image tags

---

## Test Examples

Try checkDK with provided test files:

```bash
# Simple port conflict
checkdk docker compose -f test-configs/docker-compose.yml up --dry-run

# Complex (7 critical + 10 warnings)
checkdk docker compose -f test-configs/docker-compose-complex.yml up --dry-run

# Kubernetes (4 critical + 24 warnings)
checkdk kubectl apply -f test-configs/k8s-complex.yml --dry-run
```

---

## Configuration

### Basic Setup (.env file)

```bash
# Required for AI analysis
GROQ_API_KEY=your_groq_key_here
GEMINI_API_KEY=your_gemini_key_here
```

### Advanced (Optional)

Create `~/.checkdk/config.yaml`:

```yaml
ai:
  enabled: true
  provider: groq
  model: llama-3.3-70b-versatile
```

---

## How It Works

```
┌─────────────┐
│   checkDK   │ 
└──────┬──────┘
       │
       ├─> Parse YAML files
       ├─> Run validators (port conflicts, security, etc.)
       ├─> AI analysis (Groq → Gemini fallback)
       ├─> Generate fixes with explanations
       └─> Display results
```

---

## Development

### Project Structure

```
backend/
├── checkdk/
│   ├── cli.py                  # Main CLI
│   ├── models.py               # Data models
│   ├── config.py               # Configuration
│   ├── ai/
│   │   └── providers.py        # Groq & Gemini
│   ├── parsers/
│   │   ├── docker_compose.py
│   │   └── kubernetes_parser.py
│   └── validators/
│       ├── port_validator.py
│       ├── compose_validator.py
│       └── k8s_validator.py
├── test-configs/               # Sample YAML files
├── tests/                      # Test suite
└── .env                        # Your API keys
```

### Running Tests

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Test manually
./demo.sh
```

---

## Troubleshooting

### AI not working?
1. Check `.env` file has valid API keys
2. Test keys at provider consoles
3. Check rate limits (Groq: 14,400/day)

### Command not found?
```bash
pip install -e .
# or
python -m checkdk docker compose up --dry-run
```

### Import errors?
```bash
pip install -r requirements.txt
```

---

## Features

✨ **Port Conflict Detection** - Finds duplicate ports before runtime  
🤖 **AI-Enhanced Fixes** - Clear explanations with actionable steps  
🔒 **Security Validation** - Detects privileged containers, root users  
📊 **Best Practices** - Checks health probes, resource limits  
🐳 **Docker Compose** - Full support with env var resolution  
☸️ **Kubernetes** - Deployments, Services, security contexts  
🆓 **Free AI** - Uses Groq & Gemini (no AWS/OpenAI needed)  
🎨 **Rich Output** - Beautiful terminal colors and formatting  

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `checkdk docker compose up --dry-run` | Analyze Docker Compose |
| `checkdk docker compose -f file.yml up --dry-run` | Analyze specific file |
| `checkdk docker compose up --force` | Run despite errors |
| `checkdk kubectl apply -f deploy.yml --dry-run` | Analyze Kubernetes |
| `checkdk kubectl apply -f deploy.yml --force` | Apply despite errors |
| `checkdk --version` | Show version |
| `checkdk --help` | Show help |

---

## Contributing

Contributions welcome! 

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Support

- 🐛 **Issues**: Report bugs on GitHub
- 💬 **Questions**: Open a discussion
- 📧 **Contact**: Create an issue

---

**Made with ❤️ for developers who want to catch issues early**
