# System Design Document

## 1. Architecture Overview

checkDK follows a modular, layered architecture with three primary components:

```
┌─────────────────────────────────────────────────────────────┐
│                         User Layer                          │
│                    (CLI / Web Interface)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Command Layer                          │
│              (Interceptor & Parser Module)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Analysis Layer                         │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │   Validator  │  │  Predictor   │  │  AI Engine   │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Execution Layer                        │
│              (Docker/Kubernetes Pass-through)               │
└─────────────────────────────────────────────────────────────┘
```

### 1.1 Design Principles

- **Non-invasive:** Wrapper approach without modifying Docker/K8s internals
- **Fail-safe:** Graceful degradation to native commands if analysis fails
- **Modular:** Pluggable validators and analyzers
- **Fast:** Minimal overhead (< 2 seconds)
- **Offline-first:** Core functionality works without internet

---

## 2. Component Architecture

### 2.1 CLI Layer

**Purpose:** Entry point for user commands

**Components:**
- **Command Parser:** Parses user input and extracts Docker/K8s commands
- **Argument Handler:** Preserves all flags and options for pass-through
- **Output Formatter:** Displays analysis results in terminal

**Flow:**
```
User Input → Parse Command → Identify Target Files → Trigger Analysis
```

**Key Responsibilities:**
- Intercept `checkDK docker ...` and `checkDK kubectl ...` commands
- Maintain compatibility with all Docker/K8s flags
- Handle interactive prompts (e.g., apply fixes?)
- Display colored, formatted output

### 2.2 Command Interceptor

**Purpose:** Route commands to appropriate analyzers

**Components:**
- **Docker Handler:** Processes Docker and Docker Compose commands
- **Kubernetes Handler:** Processes kubectl commands
- **File Locator:** Finds relevant configuration files

**Logic:**
```python
if command.startswith('docker compose'):
    files = locate_compose_files()
    analyze_docker_compose(files)
elif command.startswith('kubectl apply'):
    files = extract_manifest_files(command)
    analyze_kubernetes(files)
```

### 2.3 Configuration Parser

**Purpose:** Parse and normalize configuration files

**Supported Formats:**
- Docker Compose YAML (v2, v3)
- Kubernetes manifests (YAML/JSON)
- Dockerfiles
- .env files

**Components:**
- **YAML Parser:** Safe YAML loading with schema validation
- **JSON Parser:** Kubernetes JSON manifest support
- **Dockerfile Parser:** Instruction-level parsing
- **Environment Resolver:** Resolve variables and substitutions

**Output:** Normalized configuration object for analysis

### 2.4 Validation Engine

**Purpose:** Static analysis of configurations

**Validators:**

| Validator | Checks |
|-----------|--------|
| **Schema Validator** | YAML structure, required fields, data types |
| **Port Validator** | Port conflicts, valid ranges, host availability |
| **Resource Validator** | Memory/CPU limits, valid resource syntax |
| **Network Validator** | Network names, driver compatibility |
| **Volume Validator** | Mount paths, permissions, host path existence |
| **Image Validator** | Image name format, tag validity |
| **Dependency Validator** | Service dependencies, circular references |

**Architecture:**
```
┌─────────────────────────────────────────┐
│         Validation Engine               │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │   Rule Registry                   │  │
│  │   (Pluggable Validators)          │  │
│  └───────────────────────────────────┘  │
│                 │                       │
│                 ▼                       │
│  ┌───────────────────────────────────┐  │
│  │   Validation Pipeline             │  │
│  │   (Sequential Execution)          │  │
│  └───────────────────────────────────┘  │
│                 │                       │
│                 ▼                       │
│  ┌───────────────────────────────────┐  │
│  │   Result Aggregator               │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 2.5 Prediction Engine

**Purpose:** Predict runtime failures before execution

**Prediction Models:**

1. **Environment Checker**
   - Verify required environment variables
   - Check Docker daemon status
   - Validate Kubernetes cluster connectivity

2. **Resource Checker**
   - Available system memory vs. requested
   - CPU availability
   - Disk space for volumes

3. **Conflict Detector**
   - Port conflicts with running containers
   - Volume mount conflicts
   - Network name collisions

4. **Dependency Analyzer**
   - Image availability (local/registry)
   - Service startup order issues
   - Missing ConfigMaps/Secrets (K8s)

**Data Sources:**
- Docker daemon API
- Kubernetes API server
- System resource APIs
- Local image cache

### 2.6 AI Analysis Layer

**Purpose:** Intelligent error explanation and fix generation

**Architecture:**
```
┌─────────────────────────────────────────────────────────┐
│                    AI Analysis Layer                    │
│                                                         │
│  ┌─────────────────┐         ┌─────────────────┐        │
│  │  Context Builder│────────▶│   LLM Service   │       │
│  └─────────────────┘         └─────────────────┘        │
│          │                            │                 │
│          │                            ▼                 │
│          │                   ┌─────────────────┐        │
│          └──────────────────▶│ Response Parser │       │
│                               └─────────────────┘       │
│                                        │                │
│                                        ▼                │
│                               ┌─────────────────┐       │
│                               │  Fix Generator  │       │
│                               └─────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

**Components:**

1. **Context Builder**
   - Collects validation errors
   - Gathers configuration snippets
   - Includes system environment info
   - Builds structured prompt

2. **LLM Service**
   - API client for AI provider (AWS Bedrock, OpenAI, etc.)
   - Prompt templates for different error types
   - Response caching for common issues
   - Fallback to local rules if API unavailable

3. **Response Parser**
   - Extracts explanations from LLM output
   - Parses suggested fixes
   - Validates fix applicability

4. **Fix Generator**
   - Generates code patches
   - Creates step-by-step instructions
   - Offers multiple fix options

**Prompt Template:**
```
You are a Docker/Kubernetes expert. Analyze this configuration error:

Error: {error_message}
File: {file_path}
Line: {line_number}
Context: {code_snippet}

Provide:
1. Plain English explanation
2. Root cause
3. Step-by-step fix
4. Code example
```

### 2.7 Execution Layer

**Purpose:** Pass-through to native Docker/Kubernetes

**Behavior:**
- If analysis passes: Execute command directly
- If warnings found: Show warnings, prompt user, then execute
- If critical errors: Block execution, show fixes
- If analysis fails: Warn user, offer to proceed anyway

**Implementation:**
```python
def execute_command(original_command, analysis_result):
    if analysis_result.has_critical_errors():
        display_errors(analysis_result)
        return EXIT_CODE_ERROR
    
    if analysis_result.has_warnings():
        display_warnings(analysis_result)
        if not prompt_continue():
            return EXIT_CODE_CANCELLED
    
    return subprocess.run(original_command, shell=True)
```

---

## 3. CLI Command Flow

### 3.1 Docker Compose Example

```
$ checkDK docker compose up -d

Step 1: Parse Command
├─ Command: docker compose up
├─ Flags: -d
└─ Config: docker-compose.yml (auto-detected)

Step 2: Load Configuration
├─ Parse docker-compose.yml
├─ Resolve environment variables
└─ Build service dependency graph

Step 3: Validate
├─ Schema validation ✓
├─ Port check: Port 8080 already in use ✗
└─ Image check: postgres:14 available ✓

Step 4: Predict Issues
├─ Port conflict detected on service 'web'
└─ Severity: CRITICAL

Step 5: AI Analysis
├─ Explanation: "Port 8080 is already bound by process 'nginx' (PID 1234)"
└─ Fix: "Change port mapping to 8081:80 or stop nginx"

Step 6: Display Results
┌─────────────────────────────────────────┐
│ ✗ Critical Issue Found                  │
│                                         │
│ Port Conflict on 'web' service          │
│ Port 8080 is already in use by nginx    │
│                                         │
│ Suggested Fix:                          │
│ 1. Stop nginx: sudo systemctl stop nginx│
│ 2. Or change port in docker-compose.yml:│
│    ports:                               │
│      - "8081:80"                        │
└─────────────────────────────────────────┘

Execution blocked. Fix issues and try again.
```

### 3.2 Kubernetes Example

```
$ checkDK kubectl apply -f deployment.yaml

Step 1: Parse Command
├─ Command: kubectl apply
├─ Files: deployment.yaml
└─ Namespace: default (from context)

Step 2: Load Manifests
├─ Parse deployment.yaml
└─ Detected: Deployment, Service

Step 3: Validate
├─ Schema validation ✓
├─ Resource limits defined ✓
└─ Selector matches labels ✗

Step 4: AI Analysis
├─ Error: Service selector doesn't match Deployment labels
├─ Explanation: "Service will not route traffic to pods"
└─ Fix: Update Service selector to match Deployment labels

Step 5: Offer Auto-Fix
Apply suggested fix? (y/n): y
├─ Patching deployment.yaml...
└─ Fixed ✓

Step 6: Execute
Running: kubectl apply -f deployment.yaml
deployment.apps/myapp created
service/myapp created
```

---

## 4. Web Dashboard Architecture

### 4.1 Overview

Optional web interface for viewing analysis reports and history.

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (React)                     │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │ Dashboard  │  │  Reports   │  │  Settings  │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼ REST API
┌──────────────────────────────────────────────────────────┐
│                  Backend (FastAPI/Express)               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │   Auth     │  │  Analysis  │  │  Storage   │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└──────────────────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              Database (SQLite/PostgreSQL)                │
│              File Storage (Local/S3)                     │
└──────────────────────────────────────────────────────────┘
```

### 4.2 Features

**Dashboard:**
- Recent analysis runs
- Success/failure statistics
- Common issues chart

**Reports:**
- Detailed analysis results
- Configuration file viewer with annotations
- Fix history

**Settings:**
- API key configuration
- Analysis preferences
- Export options

### 4.3 API Endpoints

```
POST   /api/analyze          - Submit configuration for analysis
GET    /api/reports          - List analysis reports
GET    /api/reports/:id      - Get specific report
POST   /api/reports/:id/fix  - Apply suggested fix
GET    /api/stats            - Get usage statistics
```

### 4.4 Data Storage

**Analysis Report Schema:**
```json
{
  "id": "uuid",
  "timestamp": "2026-02-06T22:44:03Z",
  "command": "docker compose up",
  "files": ["docker-compose.yml"],
  "status": "failed",
  "errors": [
    {
      "severity": "critical",
      "type": "port_conflict",
      "message": "Port 8080 already in use",
      "file": "docker-compose.yml",
      "line": 15,
      "explanation": "...",
      "fixes": [...]
    }
  ],
  "execution_time_ms": 1234
}
```

---

## 5. Technology Stack

### 5.1 CLI Application

**Language:** Python 3.10+
- **Rationale:** Rich ecosystem, excellent YAML/Docker/K8s libraries, rapid development

**Alternative:** Go
- **Rationale:** Single binary distribution, better performance, smaller footprint

**Core Libraries:**
```
- click/typer          # CLI framework
- pyyaml               # YAML parsing
- docker               # Docker SDK
- kubernetes           # Kubernetes client
- rich                 # Terminal formatting
- pydantic             # Data validation
- requests             # HTTP client for AI APIs
```

### 5.2 AI Integration

**Primary:** AWS Bedrock (Claude/Titan)
- **Rationale:** Enterprise-grade, AWS integration, cost-effective

**Alternatives:**
- OpenAI GPT-4
- Anthropic Claude API
- Local LLM (Ollama) for offline mode

### 5.3 Web Dashboard

**Frontend:**
```
- React 18             # UI framework
- TypeScript           # Type safety
- TailwindCSS          # Styling
- React Query          # Data fetching
- Monaco Editor        # Code editor
```

**Backend:**
```
- FastAPI (Python)     # REST API
- SQLAlchemy           # ORM
- PostgreSQL           # Database (production)
- SQLite               # Database (development)
- Redis                # Caching (optional)
```

### 5.4 Infrastructure

**Development:**
- Docker for containerization
- Docker Compose for local development

**Production:**
- AWS ECS/EKS for container orchestration
- AWS RDS for database
- AWS S3 for file storage
- CloudFront for CDN

---

## 6. Security Considerations

### 6.1 Data Privacy

**Sensitive Data Handling:**
- Never log or transmit secrets, API keys, passwords
- Redact sensitive values before AI analysis
- Local-only mode for air-gapped environments

**Implementation:**
```python
SENSITIVE_KEYS = ['password', 'secret', 'token', 'key', 'credential']

def redact_sensitive(config):
    for key in config:
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            config[key] = '***REDACTED***'
    return config
```

### 6.2 Command Injection Prevention

**Risk:** User input passed to shell commands

**Mitigation:**
- Use subprocess with argument lists (not shell=True)
- Validate command structure before execution
- Whitelist allowed Docker/K8s commands

```python
ALLOWED_COMMANDS = ['docker', 'kubectl', 'docker-compose']

def validate_command(cmd):
    base_cmd = cmd.split()[0]
    if base_cmd not in ALLOWED_COMMANDS:
        raise SecurityError(f"Command not allowed: {base_cmd}")
```

### 6.3 API Security

**Web Dashboard:**
- JWT-based authentication
- Rate limiting (100 requests/minute)
- HTTPS only
- CORS restrictions

**AI API:**
- API key rotation
- Request/response encryption
- No PII in prompts

### 6.4 File System Access

**Restrictions:**
- Read-only access to configuration files
- No write access without explicit user confirmation
- Validate file paths to prevent directory traversal

---

## 7. Performance Optimization

### 7.1 Analysis Speed

**Target:** < 5 seconds for typical configurations

**Optimizations:**
1. **Parallel Validation:** Run independent validators concurrently
2. **Lazy Loading:** Load Docker/K8s APIs only when needed
3. **Caching:** Cache image availability checks, port scans
4. **Early Exit:** Stop analysis on critical errors

**Implementation:**
```python
async def analyze_config(config):
    validators = [
        validate_schema(config),
        validate_ports(config),
        validate_resources(config),
        validate_images(config)
    ]
    results = await asyncio.gather(*validators)
    return aggregate_results(results)
```

### 7.2 Caching Strategy

**Cache Layers:**

| Data | TTL | Storage |
|------|-----|---------|
| Image availability | 1 hour | In-memory |
| AI responses | 24 hours | Disk |
| Port scans | 5 minutes | In-memory |
| Validation rules | Indefinite | Disk |

### 7.3 Resource Usage

**Constraints:**
- Memory: < 100MB baseline
- CPU: < 10% during analysis
- Disk: < 50MB for cache

---

## 8. Scalability

### 8.1 CLI Scalability

**Single-user tool:** No horizontal scaling needed

**Considerations:**
- Handle large configuration files (10MB+)
- Support multi-file projects (50+ manifests)
- Efficient memory usage for large YAML parsing

### 8.2 Web Dashboard Scalability

**Expected Load:**
- 1,000 users
- 10,000 analyses/day
- 100 concurrent requests

**Architecture:**
```
┌─────────────┐
│   CDN       │
└─────────────┘
       │
┌─────────────┐
│Load Balancer│
└─────────────┘
       │
   ┌───┴───┐
   │       │
┌──▼──┐ ┌──▼──┐
│ API │ │ API │  (Auto-scaling)
└──┬──┘ └──┬──┘
   │       │
   └───┬───┘
       │
┌──────▼──────┐
│  Database   │
│  (Primary)  │
└─────────────┘
       │
┌──────▼──────┐
│  Database   │
│  (Replica)  │
└─────────────┘
```

**Scaling Strategy:**
- Horizontal scaling of API servers
- Database read replicas
- Redis for session/cache
- S3 for report storage

---

## 9. Error Handling & Resilience

### 9.1 Failure Modes

| Failure | Behavior | Fallback |
|---------|----------|----------|
| YAML parse error | Show syntax error | None (block execution) |
| Docker daemon down | Show connection error | None (block execution) |
| AI API unavailable | Use rule-based explanations | Continue with basic analysis |
| Network timeout | Retry 3x with backoff | Skip network-dependent checks |
| Invalid command | Show usage help | None |

### 9.2 Graceful Degradation

**Priority Levels:**
1. **Critical:** Schema validation, syntax checking (must work)
2. **High:** Port conflicts, resource checks (work offline)
3. **Medium:** Image availability (requires Docker daemon)
4. **Low:** AI explanations (requires internet)

**Strategy:** Continue analysis even if lower-priority checks fail

### 9.3 Logging

**Levels:**
- ERROR: Analysis failures, API errors
- WARN: Degraded functionality, timeouts
- INFO: Analysis results, command execution
- DEBUG: Detailed validation steps

**Storage:**
- Local: `~/.checkdk/logs/`
- Rotation: 7 days, 10MB max per file

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Coverage Target:** 80%+

**Focus Areas:**
- YAML parsing edge cases
- Validation logic
- Error message generation
- Fix suggestion accuracy

### 10.2 Integration Tests

**Scenarios:**
- Docker Compose with various configurations
- Kubernetes manifests (Deployment, Service, ConfigMap, etc.)
- Command pass-through with different flags
- AI API integration (mocked)

### 10.3 End-to-End Tests

**Test Cases:**
1. Successful analysis → execution
2. Critical error → blocked execution
3. Warning → user prompt → execution
4. Auto-fix → modified config → execution

### 10.4 Performance Tests

**Benchmarks:**
- Analysis time for 1KB, 100KB, 1MB configs
- Memory usage during analysis
- Concurrent analysis runs

---

## 11. Deployment & Distribution

### 11.1 CLI Distribution

**Methods:**
1. **PyPI:** `pip install checkdk`
2. **Homebrew:** `brew install checkdk`
3. **Binary Releases:** GitHub releases (if using Go)
4. **Docker Image:** `docker run checkdk/cli`

**Installation:**
```bash
# Python
pip install checkdk

# Verify
checkdk --version

# Setup (optional)
checkdk init  # Configure AI API keys
```

### 11.2 Web Dashboard Deployment

**Options:**
1. **Self-hosted:** Docker Compose bundle
2. **Cloud:** AWS ECS/EKS deployment
3. **SaaS:** Hosted version at checkdk.io

**Docker Compose:**
```yaml
services:
  api:
    image: checkdk/api:latest
    environment:
      - DATABASE_URL=postgresql://...
      - AI_API_KEY=${AI_API_KEY}
  
  frontend:
    image: checkdk/frontend:latest
    ports:
      - "3000:80"
  
  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
```

---

## 12. Monitoring & Observability

### 12.1 Metrics

**CLI Metrics (Local):**
- Analysis success/failure rate
- Average analysis time
- Most common errors
- Command usage frequency

**Web Dashboard Metrics:**
- API response times
- Error rates
- Active users
- Database query performance

### 12.2 Instrumentation

**Tools:**
- Prometheus for metrics collection
- Grafana for visualization
- CloudWatch for AWS infrastructure
- Sentry for error tracking

**Key Dashboards:**
1. System health (uptime, latency, errors)
2. User activity (analyses per day, popular commands)
3. AI usage (API calls, costs, response times)

---

## 13. Future Enhancements

### 13.1 Phase 2 Features

**IDE Integration:**
- VS Code extension
- IntelliJ plugin
- Real-time validation in editor

**Advanced Analysis:**
- Security vulnerability scanning
- Cost estimation for cloud resources
- Performance optimization suggestions

**Collaboration:**
- Team workspaces
- Shared configuration templates
- Analysis report sharing

### 13.2 Phase 3 Features

**CI/CD Integration:**
- GitHub Actions plugin
- GitLab CI integration
- Jenkins plugin

**Multi-tool Support:**
- Terraform validation
- Helm chart analysis
- AWS CloudFormation

**Enterprise Features:**
- SSO authentication
- Custom validation rules
- Audit logging
- Role-based access control

### 13.3 Technical Debt & Improvements

**Performance:**
- Migrate to Go for better performance
- Implement incremental analysis (only changed files)
- Add GPU acceleration for local LLM

**Architecture:**
- Plugin system for custom validators
- gRPC API for better performance
- Event-driven architecture for real-time updates

---

## 14. Appendix

### 14.1 Configuration File

**~/.checkdk/config.yaml:**
```yaml
ai:
  provider: aws-bedrock  # aws-bedrock, openai, anthropic, local
  model: claude-3-sonnet
  api_key: ${CHECKDK_API_KEY}
  
analysis:
  timeout: 30  # seconds
  parallel: true
  cache_ttl: 3600
  
execution:
  auto_fix: false  # prompt user
  block_on_critical: true
  show_warnings: true
  
logging:
  level: info
  file: ~/.checkdk/logs/checkdk.log
  
dashboard:
  enabled: false
  url: http://localhost:3000
```

### 14.2 Plugin System (Future)

**Custom Validator Example:**
```python
from checkdk.plugin import Validator

class CustomPortValidator(Validator):
    def validate(self, config):
        # Custom validation logic
        errors = []
        for service in config.services:
            if service.port < 1024:
                errors.append(Error(
                    severity="warning",
                    message=f"Service {service.name} uses privileged port"
                ))
        return errors

# Register plugin
checkdk.register_validator(CustomPortValidator)
```

