"""Base validator class."""

from abc import ABC, abstractmethod
from typing import List
from ..models import Issue, DockerComposeConfig


class BaseValidator(ABC):
    """Base class for all validators."""
    
    def __init__(self):
        self.issues: List[Issue] = []
    
    @abstractmethod
    def validate(self, config: DockerComposeConfig) -> List[Issue]:
        """Validate the configuration and return list of issues."""
        pass
    
    def clear_issues(self):
        """Clear the issues list."""
        self.issues = []
