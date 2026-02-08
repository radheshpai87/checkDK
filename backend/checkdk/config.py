"""Configuration management for checkDK."""

import os
from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field


class AIConfig(BaseModel):
    """AI provider configuration."""
    provider: str = "groq"  # groq, gemini, aws-bedrock, or openai
    model: str = "llama-3.3-70b-versatile"
    api_key: Optional[str] = None
    enabled: bool = True
    fallback_provider: Optional[str] = "gemini"


class CheckDKConfig(BaseModel):
    """Main checkDK configuration."""
    ai: AIConfig = Field(default_factory=AIConfig)
    auto_fix: bool = False
    offline_mode: bool = False
    timeout: int = 30
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "CheckDKConfig":
        """Load configuration from file or defaults."""
        if config_path is None:
            config_path = Path.home() / ".checkdk" / "config.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                data = yaml.safe_load(f)
                return cls(**data)
        
        return cls()
    
    def save(self, config_path: Optional[Path] = None):
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.home() / ".checkdk" / "config.yaml"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)


def get_config() -> CheckDKConfig:
    """Get the current configuration."""
    return CheckDKConfig.load()
