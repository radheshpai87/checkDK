"""AI provider implementations – Mistral (primary) + Groq (fallback)."""

from abc import ABC, abstractmethod
from typing import Optional
import json
import logging
import os
import re

# Ensure .env is loaded before reading API keys from os.getenv().
# env.py is a thin python-dotenv wrapper; the try/except guards against
# import errors during tests or unusual install layouts.
try:
    from ..env import load_env as _load_env
    _load_env()
except Exception:  # ImportError or any unexpected error — fall back to env
    pass

logger = logging.getLogger(__name__)

# ── System prompt shared by the playground analysis endpoint ──────────────────

PLAYGROUND_SYSTEM_PROMPT = """You are an expert DevOps security auditor specialising in AWS, Docker, and Kubernetes configurations.
Analyse the provided configuration file and identify ALL security vulnerabilities, misconfigurations, and best-practice violations.

Check for (not limited to):
- IAM over-permissive policies (Action:"*", Resource:"*", wildcard principals)
- Public S3 buckets / missing bucket policies / ACL issues
- Unencrypted storage (EBS, RDS, S3, Secrets Manager)
- Security groups with 0.0.0.0/0 open on sensitive ports (22, 3389, etc.)
- Missing CloudTrail / VPC flow logs / access logging
- Hardcoded secrets, passwords, or API keys
- Missing MFA enforcement on IAM
- Outdated / deprecated runtimes or API versions
- Missing backup / retention policies
- Non-compliant or missing resource tags
- Missing VPC or overly-permissive network exposure
- Overly-permissive trust relationships
- Docker: root containers, missing resource limits, hardcoded secrets, :latest tags
- Kubernetes: missing resource limits, no liveness/readiness probes, privileged containers, host networking

Respond ONLY with a valid JSON object matching this exact schema — no markdown, no explanation, no code fences:

{
  "score": number,          // 0-100 security score (100 = fully secure)
  "status": "secure" | "warning" | "critical",
  "summary": string,        // 2-3 sentence overall summary
  "issues": [
    {
      "severity": "critical" | "high" | "medium" | "low" | "info",
      "title": string,
      "description": string,
      "line": number | null,
      "recommendation": string
    }
  ],
  "highlights": [
    {
      "type": "good" | "bad" | "neutral",
      "text": string
    }
  ]
}

Be precise and specific — cite exact resource names, values, and line numbers where possible.
Do NOT hallucinate issues that are not present. If the config is clean, say so with a high score."""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_fences(raw: str) -> str:
    """Remove markdown code fences from LLM output."""
    return re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE).rstrip("`").strip()


def _build_user_message(content: str, filename: str | None = None) -> str:
    tag = f" ({filename})" if filename else ""
    return (
        f"Analyse this configuration file{tag}:\n\n{content}\n\n"
        "Return ONLY the JSON object — no markdown, no code fences, no explanation."
    )


# ── Base class ────────────────────────────────────────────────────────────────


class AIProvider(ABC):
    """Base class for AI providers."""

    @abstractmethod
    def analyze_error(self, error_message: str, config_snippet: str, context: dict) -> dict:
        """Analyze an error and return explanation and fixes."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        ...

    @abstractmethod
    def analyze_pod_health(self, prediction: dict) -> dict:
        """Analyse a Random Forest prediction result and return a risk assessment."""
        ...

    @abstractmethod
    def analyze_config(self, content: str, filename: str | None = None) -> dict:
        """Full security / best-practice audit used by the Playground endpoint.

        Returns a dict matching the PlaygroundResult schema:
            score, status, summary, issues[], highlights[]
        """
        ...

    # ── Shared prompt builders ────────────────────────────────────────────────

    @staticmethod
    def _build_error_prompt(error_message: str, config_snippet: str, context: dict) -> str:
        service = context.get("service_name", "unknown")
        return f"""Analyze this Docker Compose configuration error:

**Error**: {error_message}
**Service**: {service}
**Configuration**:
```yaml
{config_snippet}
```

Provide:
1. **Explanation**: What's wrong in plain English (1-2 sentences)
2. **Root Cause**: Why this happens (1 sentence)
3. **Fix**: Exact steps to resolve (2-3 actionable steps)

Keep it concise and practical."""

    @staticmethod
    def _build_pod_health_prompt(prediction: dict) -> str:
        metrics = prediction.get("metrics", {})
        label = prediction.get("label", "unknown")
        confidence = round(prediction.get("confidence", 0) * 100, 1)
        risk = prediction.get("risk_level", "unknown")
        service = prediction.get("service_name") or "unknown"
        platform = prediction.get("platform") or "Docker/Kubernetes"

        metrics_str = "\n".join(
            f"  - {k.replace('_', ' ').title()}: {v}" for k, v in metrics.items()
        )

        return f"""A machine learning model (Random Forest) has analysed the runtime metrics
of a {platform} pod/container and produced the following result:

**Service**: {service}
**Prediction**: {label.upper()}
**Failure Probability**: {confidence}%
**Risk Level**: {risk}

**Runtime Metrics**:
{metrics_str}

Based on these metrics and the ML model's prediction, provide:
1. **Assessment**: A clear 1-2 sentence summary of the pod's health status.
2. **Root Cause**: The most likely contributing factor to this risk level.
3. **Recommendations**: 2-3 specific, actionable steps an engineer should take right now.

Be concise and practical. Focus on the highest-impact metrics."""

    # ── Shared response parsers ───────────────────────────────────────────────

    @staticmethod
    def _parse_error_response(response: str) -> dict:
        """Parse a free-text error analysis response into structured dict."""
        lines = response.strip().split("\n")
        result: dict = {"explanation": "", "root_cause": "", "fix_steps": []}
        current_section: str | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if "explanation" in lower and ":" in line:
                current_section = "explanation"
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    result["explanation"] = parts[1].strip()
            elif "root cause" in lower and ":" in line:
                current_section = "root_cause"
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    result["root_cause"] = parts[1].strip()
            elif "fix" in lower and ":" in line:
                current_section = "fix_steps"
            elif current_section == "fix_steps" and (
                line.startswith("-")
                or line.startswith("•")
                or line.startswith("*")
                or (len(line) > 0 and line[0].isdigit())
            ):
                clean = line.lstrip("-•*0123456789. ").strip()
                if clean:
                    result["fix_steps"].append(clean)
            elif current_section and not any(
                x in lower for x in ("explanation", "root", "fix")
            ):
                if current_section == "explanation" and not result["explanation"]:
                    result["explanation"] = line
                elif current_section == "root_cause" and not result["root_cause"]:
                    result["root_cause"] = line

        if not result["explanation"]:
            result["explanation"] = response[:200]
        return result

    @staticmethod
    def _parse_pod_health_response(response: str) -> dict:
        """Parse a free-text pod health response into structured dict."""
        lines = response.strip().split("\n")
        result: dict = {"assessment": "", "root_cause": "", "recommendations": []}
        current_section: str | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if "assessment" in lower and ":" in line:
                current_section = "assessment"
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    result["assessment"] = parts[1].strip()
            elif "root cause" in lower and ":" in line:
                current_section = "root_cause"
                parts = line.split(":", 1)
                if len(parts) > 1 and parts[1].strip():
                    result["root_cause"] = parts[1].strip()
            elif "recommendation" in lower and ":" in line:
                current_section = "recommendations"
            elif current_section == "recommendations" and (
                line.startswith("-")
                or line.startswith("•")
                or line.startswith("*")
                or (len(line) > 0 and line[0].isdigit())
            ):
                clean = line.lstrip("-•*0123456789. ").strip()
                if clean:
                    result["recommendations"].append(clean)
            elif current_section in ("assessment", "root_cause") and not any(
                x in lower for x in ("assessment", "root cause", "recommendation")
            ):
                if current_section == "assessment" and not result["assessment"]:
                    result["assessment"] = line
                elif current_section == "root_cause" and not result["root_cause"]:
                    result["root_cause"] = line

        if not result["assessment"]:
            result["assessment"] = response[:250]
        return result

    @staticmethod
    def _parse_config_response(raw: str) -> dict:
        """Parse JSON returned by the playground-style config audit."""
        cleaned = _strip_fences(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(
                f"LLM returned unparseable JSON. First 400 chars: {raw[:400]}"
            )


# ── Mistral (primary) ────────────────────────────────────────────────────────


class MistralProvider(AIProvider):
    """Mistral AI provider (primary)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        self.model = "mistral-large-latest"

    _PLACEHOLDERS = {"your_mistral_api_key_here", "your_api_key_here", "", "placeholder", "changeme"}

    def is_available(self) -> bool:
        return bool(self.api_key) and self.api_key.strip().lower() not in self._PLACEHOLDERS

    def analyze_error(self, error_message: str, config_snippet: str, context: dict) -> dict:
        if not self.is_available():
            return {"error": "Mistral API key not configured"}
        try:
            from mistralai import Mistral

            client = Mistral(api_key=self.api_key)
            prompt = self._build_error_prompt(error_message, config_snippet, context)
            response = client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Docker and Kubernetes expert. Provide concise, actionable advice."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            text = response.choices[0].message.content or ""
            return self._parse_error_response(text)
        except ImportError:
            return {"error": "Mistral package not installed. Run: pip install mistralai"}
        except Exception as e:
            return {"error": f"Mistral API error: {e}"}

    def analyze_pod_health(self, prediction: dict) -> dict:
        if not self.is_available():
            return {"error": "Mistral API key not configured"}
        try:
            from mistralai import Mistral

            client = Mistral(api_key=self.api_key)
            prompt = self._build_pod_health_prompt(prediction)
            response = client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": (
                        "You are a DevOps SRE expert specialising in Docker and Kubernetes "
                        "reliability. Provide concise, actionable pod health assessments."
                    )},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            text = response.choices[0].message.content or ""
            return self._parse_pod_health_response(text)
        except ImportError:
            return {"error": "Mistral package not installed. Run: pip install mistralai"}
        except Exception as e:
            return {"error": f"Mistral API error: {e}"}

    def analyze_config(self, content: str, filename: str | None = None) -> dict:
        if not self.is_available():
            raise RuntimeError("Mistral API key not configured")
        try:
            from mistralai import Mistral

            client = Mistral(api_key=self.api_key)
            response = client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": PLAYGROUND_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_message(content, filename)},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            raw = response.choices[0].message.content or ""
            result = self._parse_config_response(raw)
            result["provider"] = "mistral"
            return result
        except ImportError:
            raise RuntimeError("Mistral package not installed. Run: pip install mistralai")
        except Exception as e:
            logger.error("Mistral analyze_config error: %s", e)
            return {"error": f"Mistral API error: {e}", "score": 0, "status": "critical", "summary": str(e), "issues": [], "highlights": []}


# ── Groq (fallback) ──────────────────────────────────────────────────────────


class GroqProvider(AIProvider):
    """Groq AI provider (fast, free fallback)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = "llama-3.3-70b-versatile"

    _PLACEHOLDERS = {"your_groq_api_key_here", "your_api_key_here", "", "placeholder", "changeme"}

    def is_available(self) -> bool:
        return bool(self.api_key) and self.api_key.strip().lower() not in self._PLACEHOLDERS

    def analyze_error(self, error_message: str, config_snippet: str, context: dict) -> dict:
        if not self.is_available():
            return {"error": "Groq API key not configured"}
        try:
            from groq import Groq

            client = Groq(api_key=self.api_key)
            prompt = self._build_error_prompt(error_message, config_snippet, context)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Docker and Kubernetes expert. Provide concise, actionable advice."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            text = response.choices[0].message.content or ""
            return self._parse_error_response(text)
        except ImportError:
            return {"error": "Groq package not installed. Run: pip install groq"}
        except Exception as e:
            return {"error": f"Groq API error: {e}"}

    def analyze_pod_health(self, prediction: dict) -> dict:
        if not self.is_available():
            return {"error": "Groq API key not configured"}
        try:
            from groq import Groq

            client = Groq(api_key=self.api_key)
            prompt = self._build_pod_health_prompt(prediction)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": (
                        "You are a DevOps SRE expert specialising in Docker and Kubernetes "
                        "reliability. Provide concise, actionable pod health assessments."
                    )},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            text = response.choices[0].message.content or ""
            return self._parse_pod_health_response(text)
        except ImportError:
            return {"error": "Groq package not installed. Run: pip install groq"}
        except Exception as e:
            return {"error": f"Groq API error: {e}"}

    def analyze_config(self, content: str, filename: str | None = None) -> dict:
        if not self.is_available():
            raise RuntimeError("Groq API key not configured")
        try:
            from groq import Groq

            client = Groq(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": PLAYGROUND_SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_message(content, filename)},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            raw = response.choices[0].message.content or ""
            result = self._parse_config_response(raw)
            result["provider"] = "groq"
            return result
        except ImportError:
            raise RuntimeError("Groq package not installed. Run: pip install groq")
        except Exception as e:
            logger.error("Groq analyze_config error: %s", e)
            return {"error": f"Groq API error: {e}", "score": 0, "status": "critical", "summary": str(e), "issues": [], "highlights": []}


# ── Factory ───────────────────────────────────────────────────────────────────


def get_ai_provider(config=None) -> Optional[AIProvider]:
    """Get the best available AI provider (Mistral first, Groq fallback)."""
    if config is None:
        from ..config import get_config
        config = get_config()

    # Respect user preference from config if set
    preferred = getattr(getattr(config, "ai", None), "provider", "mistral")
    api_key = getattr(getattr(config, "ai", None), "api_key", None)

    # config.ai.api_key is the key **for the preferred provider only**.
    # The fallback provider always reads its key from the environment so
    # that a single config.ai.api_key value is never passed to the wrong SDK.
    if preferred == "groq":
        groq = GroqProvider(api_key=api_key)  # use config key for Groq
        if groq.is_available():
            return groq
        mistral = MistralProvider()           # fallback: use MISTRAL_API_KEY env var
        if mistral.is_available():
            return mistral
    else:
        # Default: Mistral primary, Groq fallback
        mistral = MistralProvider(api_key=api_key if preferred == "mistral" else None)
        if mistral.is_available():
            return mistral
        groq = GroqProvider()                  # fallback: use GROQ_API_KEY env var
        if groq.is_available():
            return groq

    return None
