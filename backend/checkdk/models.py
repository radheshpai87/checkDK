"""Data models for checkDK."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class IssueType(str, Enum):
    """Types of issues that can be detected."""
    PORT_CONFLICT = "port_conflict"
    MISSING_IMAGE = "missing_image"
    RESOURCE_LIMIT = "resource_limit"
    IMAGE_VERSION = "image_version"
    INVALID_YAML = "invalid_yaml"
    MISSING_ENV_VAR = "missing_env_var"
    VOLUME_MOUNT = "volume_mount"
    NETWORK_CONFIG = "network_config"
    SERVICE_DEPENDENCY = "service_dependency"
    SECURITY_ISSUE = "security_issue"
    HEALTH_CHECK = "health_check"
    LABEL_MISMATCH = "label_mismatch"


class Issue(BaseModel):
    """Represents a detected issue."""
    type: IssueType
    severity: Severity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    service_name: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class Fix(BaseModel):
    """Represents a suggested fix."""
    description: str
    steps: List[str]
    code_snippet: Optional[str] = None
    auto_applicable: bool = False
    # AI-specific fields
    explanation: Optional[str] = None
    root_cause: Optional[str] = None


class AnalysisResult(BaseModel):
    """Result of configuration analysis."""
    success: bool
    issues: List[Issue] = Field(default_factory=list)
    fixes: List[Fix] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == Severity.CRITICAL for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return any(issue.severity == Severity.WARNING for issue in self.issues) or bool(self.warnings)


class DockerComposeConfig(BaseModel):
    """Parsed Docker Compose configuration."""
    version: Optional[str] = None
    services: Dict[str, Any] = Field(default_factory=dict)
    networks: Dict[str, Any] = Field(default_factory=dict)
    volumes: Dict[str, Any] = Field(default_factory=dict)
    raw_config: Dict[str, Any] = Field(default_factory=dict)


# --------------- Playground (LLM audit) models ---------------

class IssueSeverity(str, Enum):
    """Severity levels for playground analysis issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    WARNING = "warning"
    INFO = "info"


class PlaygroundIssue(BaseModel):
    """A single issue returned by playground analysis (LLM or rule-based)."""
    title: str = ""
    severity: IssueSeverity = IssueSeverity.INFO
    description: str = ""
    recommendation: Optional[str] = None
    suggestion: Optional[str] = None  # backward compat alias
    line: Optional[int] = None
    category: Optional[str] = None    # dedup key (e.g. "port_conflict", "security")


class PlaygroundHighlight(BaseModel):
    """A positive aspect found during playground analysis."""
    type: Optional[str] = None        # "good" | "bad" | "neutral"
    text: Optional[str] = None
    title: Optional[str] = None       # backward compat
    description: Optional[str] = None  # backward compat


class PlaygroundResult(BaseModel):
    """Full result from the /analyze/playground endpoint."""
    score: int = Field(ge=0, le=100)
    status: str  # "secure" | "warning" | "critical"
    summary: str
    issues: List[PlaygroundIssue] = Field(default_factory=list)
    highlights: List[PlaygroundHighlight] = Field(default_factory=list)
    provider: Optional[str] = None    # "mistral", "groq", "mistral+rules", "rule-engine"
