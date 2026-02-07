"""Tests for port validator."""

import pytest
from checkdk.validators import PortValidator
from checkdk.models import DockerComposeConfig, IssueType, Severity


def test_duplicate_ports_across_services():
    """Test detection of duplicate ports across services."""
    config = DockerComposeConfig(
        services={
            'web1': {
                'image': 'nginx',
                'ports': ['8080:80']
            },
            'web2': {
                'image': 'nginx',
                'ports': ['8080:80']
            }
        }
    )
    
    validator = PortValidator()
    issues = validator.validate(config)
    
    assert len(issues) >= 1
    assert any(issue.type == IssueType.PORT_CONFLICT for issue in issues)
    assert any('8080' in issue.message for issue in issues)


def test_no_port_conflicts():
    """Test that no issues are raised when ports don't conflict."""
    config = DockerComposeConfig(
        services={
            'web': {
                'image': 'nginx',
                'ports': ['8080:80']
            },
            'api': {
                'image': 'node',
                'ports': ['3000:3000']
            }
        }
    )
    
    validator = PortValidator()
    issues = validator.validate(config)
    
    # Filter out system port conflicts (ports actually in use)
    duplicate_issues = [i for i in issues if 'multiple services' in i.message.lower()]
    assert len(duplicate_issues) == 0


def test_extract_host_port_formats():
    """Test extraction of host ports from various formats."""
    validator = PortValidator()
    
    # String format "8080:80"
    assert validator._extract_host_port("8080:80") == 8080
    
    # String format "8080"
    assert validator._extract_host_port("8080") == 8080
    
    # Integer format
    assert validator._extract_host_port(8080) == 8080
    
    # Dict format (long syntax)
    assert validator._extract_host_port({"published": 8080, "target": 80}) == 8080
    
    # Invalid format
    assert validator._extract_host_port("invalid") is None
