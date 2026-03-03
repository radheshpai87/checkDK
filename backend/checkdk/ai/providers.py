"""AI provider implementations."""

from abc import ABC, abstractmethod
from typing import Optional
import os

# Load .env file if it exists
try:
    from ..env import load_env
    load_env()
except ImportError:
    pass


class AIProvider(ABC):
    """Base class for AI providers."""
    
    @abstractmethod
    def analyze_error(self, error_message: str, config_snippet: str, context: dict) -> dict:
        """Analyze an error and return explanation and fixes."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured."""
        pass

    @abstractmethod
    def analyze_pod_health(self, prediction: dict) -> dict:
        """
        Analyse a Random Forest prediction result and return a natural-language
        risk assessment with actionable recommendations.

        Args:
            prediction: dict with keys:
                label         – "healthy" | "failure"
                confidence    – float [0, 1] probability of failure
                risk_level    – "low" | "medium" | "high" | "critical"
                metrics       – dict of raw pod metric values
                service_name  – optional str
                platform      – optional str ("docker" | "kubernetes")

        Returns:
            {
                "assessment": str,       # 1-2 sentence summary
                "root_cause": str,       # likely contributing factor
                "recommendations": list  # 2-3 actionable steps
            }
        """
        pass

    @staticmethod
    def _build_pod_health_prompt(prediction: dict) -> str:
        """Shared prompt builder for pod health analysis."""
        metrics      = prediction.get("metrics", {})
        label        = prediction.get("label", "unknown")
        confidence   = round(prediction.get("confidence", 0) * 100, 1)
        risk         = prediction.get("risk_level", "unknown")
        service      = prediction.get("service_name") or "unknown"
        platform     = prediction.get("platform") or "Docker/Kubernetes"

        metrics_str = "\n".join(
            f"  - {k.replace('_', ' ').title()}: {v}"
            for k, v in metrics.items()
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


class GroqProvider(AIProvider):
    """Groq AI provider (fast, free)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.model = "llama-3.3-70b-versatile"  # Latest Groq model
    
    def is_available(self) -> bool:
        """Check if Groq is configured."""
        return bool(self.api_key)
    
    def analyze_error(self, error_message: str, config_snippet: str, context: dict) -> dict:
        """Analyze error using Groq."""
        if not self.is_available():
            return {"error": "Groq API key not configured"}
        
        try:
            from groq import Groq
            
            client = Groq(api_key=self.api_key)
            
            prompt = self._build_prompt(error_message, config_snippet, context)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Docker and Kubernetes expert. Provide concise, actionable advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except ImportError:
            return {"error": "Groq package not installed. Run: pip install groq"}
        except Exception as e:
            return {"error": f"Groq API error: {str(e)}"}

    def analyze_pod_health(self, prediction: dict) -> dict:
        """Analyse ML prediction result using Groq LLM."""
        if not self.is_available():
            return {"error": "Groq API key not configured"}
        try:
            from groq import Groq
            client   = Groq(api_key=self.api_key)
            prompt   = self._build_pod_health_prompt(prediction)
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
            return self._parse_pod_health_response(
                response.choices[0].message.content
            )
        except ImportError:
            return {"error": "Groq package not installed. Run: pip install groq"}
        except Exception as e:
            return {"error": f"Groq API error: {str(e)}"}
    
    def _build_prompt(self, error_message: str, config_snippet: str, context: dict) -> str:
        """Build the prompt for the AI."""
        service = context.get('service_name', 'unknown')

        prompt = f"""Analyze this Docker Compose configuration error:

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

        return prompt

    def _parse_pod_health_response(self, response: str) -> dict:
        """Parse LLM pod health response into structured format."""
        lines = response.strip().split('\n')
        result = {"assessment": "", "root_cause": "", "recommendations": []}
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if "assessment" in lower and ":" in line:
                current_section = "assessment"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["assessment"] = parts[1].strip()
            elif "root cause" in lower and ":" in line:
                current_section = "root_cause"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["root_cause"] = parts[1].strip()
            elif "recommendation" in lower and ":" in line:
                current_section = "recommendations"
            elif current_section == "recommendations" and (
                line.startswith('-') or line.startswith('•') or
                line.startswith('*') or (line and line[0].isdigit())
            ):
                clean = line.lstrip('-•*0123456789. ').strip()
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

    def _parse_response(self, response: str) -> dict:
        """Parse AI response into structured format."""
        lines = response.strip().split('\n')
        
        result = {
            "explanation": "",
            "root_cause": "",
            "fix_steps": []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if "explanation" in line.lower() and ":" in line:
                current_section = "explanation"
                # Try to extract content after the colon
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["explanation"] = parts[1].strip()
            elif "root cause" in line.lower() and ":" in line:
                current_section = "root_cause"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["root_cause"] = parts[1].strip()
            elif "fix" in line.lower() and ":" in line:
                current_section = "fix_steps"
            elif current_section == "fix_steps" and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                # Clean up bullet points and numbers
                clean_line = line.lstrip('-•*0123456789. ').strip()
                if clean_line:
                    result["fix_steps"].append(clean_line)
            elif current_section and not any(x in line.lower() for x in ["explanation", "root", "fix"]):
                # Continue current section
                if current_section == "explanation" and not result["explanation"]:
                    result["explanation"] = line
                elif current_section == "root_cause" and not result["root_cause"]:
                    result["root_cause"] = line
        
        # Fallback: if parsing failed, use the whole response
        if not result["explanation"]:
            result["explanation"] = response[:200]
        
        return result


class GeminiProvider(AIProvider):
    """Google Gemini provider (fallback)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        self.model = "gemini-1.5-flash"  # Fast and free
    
    def is_available(self) -> bool:
        """Check if Gemini is configured."""
        return bool(self.api_key)
    
    def analyze_error(self, error_message: str, config_snippet: str, context: dict) -> dict:
        """Analyze error using Gemini."""
        if not self.is_available():
            return {"error": "Gemini API key not configured"}
        
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model)
            
            prompt = self._build_prompt(error_message, config_snippet, context)
            
            response = model.generate_content(prompt)
            
            return self._parse_response(response.text)
            
        except ImportError:
            return {"error": "Google AI package not installed. Run: pip install google-generativeai"}
        except Exception as e:
            return {"error": f"Gemini API error: {str(e)}"}

    def analyze_pod_health(self, prediction: dict) -> dict:
        """Analyse ML prediction result using Gemini LLM."""
        if not self.is_available():
            return {"error": "Gemini API key not configured"}
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model    = genai.GenerativeModel(self.model)
            prompt   = self._build_pod_health_prompt(prediction)
            response = model.generate_content(prompt)
            return self._parse_pod_health_response(response.text)
        except ImportError:
            return {"error": "Google AI package not installed. Run: pip install google-generativeai"}
        except Exception as e:
            return {"error": f"Gemini API error: {str(e)}"}

    def _parse_pod_health_response(self, response: str) -> dict:
        """Parse LLM pod health response into structured format."""
        lines = response.strip().split('\n')
        result = {"assessment": "", "root_cause": "", "recommendations": []}
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue
            lower = line.lower()
            if "assessment" in lower and ":" in line:
                current_section = "assessment"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["assessment"] = parts[1].strip()
            elif "root cause" in lower and ":" in line:
                current_section = "root_cause"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["root_cause"] = parts[1].strip()
            elif "recommendation" in lower and ":" in line:
                current_section = "recommendations"
            elif current_section == "recommendations" and (
                line.startswith('-') or line.startswith('•') or
                line.startswith('*') or (line and line[0].isdigit())
            ):
                clean = line.lstrip('-•*0123456789. ').strip()
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

    def _build_prompt(self, error_message: str, config_snippet: str, context: dict) -> str:
        """Build the prompt for Gemini."""
        service = context.get('service_name', 'unknown')
        
        prompt = f"""Analyze this Docker Compose error:

Error: {error_message}
Service: {service}
Config:
{config_snippet}

Provide:
1. Explanation (1-2 sentences, plain English)
2. Root Cause (1 sentence)
3. Fix Steps (2-3 actionable steps)

Be concise."""
        
        return prompt
    
    def _parse_response(self, response: str) -> dict:
        """Parse Gemini response."""
        # Similar parsing logic to Groq
        lines = response.strip().split('\n')
        
        result = {
            "explanation": "",
            "root_cause": "",
            "fix_steps": []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if "explanation" in line.lower() and ":" in line:
                current_section = "explanation"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["explanation"] = parts[1].strip()
            elif "root cause" in line.lower() and ":" in line:
                current_section = "root_cause"
                parts = line.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    result["root_cause"] = parts[1].strip()
            elif "fix" in line.lower() and ":" in line:
                current_section = "fix_steps"
            elif current_section == "fix_steps" and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                clean_line = line.lstrip('-•0123456789. ').strip()
                if clean_line:
                    result["fix_steps"].append(clean_line)
            elif current_section and not any(x in line.lower() for x in ["explanation", "root", "fix"]):
                if current_section == "explanation" and not result["explanation"]:
                    result["explanation"] = line
                elif current_section == "root_cause" and not result["root_cause"]:
                    result["root_cause"] = line
        
        if not result["explanation"]:
            result["explanation"] = response[:200]
        
        return result


def get_ai_provider(config=None) -> Optional[AIProvider]:
    """Get the best available AI provider."""
    if config is None:
        from ..config import get_config
        config = get_config()
    
    # Try Groq first (fastest)
    groq = GroqProvider()
    if groq.is_available():
        return groq
    
    # Fallback to Gemini
    gemini = GeminiProvider()
    if gemini.is_available():
        return gemini
    
    # No AI available
    return None
