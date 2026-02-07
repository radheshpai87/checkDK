"""Tests for Docker Compose parser."""

import pytest
from pathlib import Path
import tempfile
import yaml

from checkdk.parsers import DockerComposeParser
from checkdk.models import IssueType, Severity


def test_parse_valid_compose_file():
    """Test parsing a valid Docker Compose file."""
    config = {
        'version': '3.8',
        'services': {
            'web': {
                'image': 'nginx:latest',
                'ports': ['8080:80']
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        parser = DockerComposeParser(temp_path)
        result = parser.parse()
        
        assert result.version == '3.8'
        assert 'web' in result.services
        assert result.services['web']['image'] == 'nginx:latest'
        assert len(parser.issues) == 0
    finally:
        Path(temp_path).unlink()


def test_parse_missing_file():
    """Test parsing a non-existent file."""
    parser = DockerComposeParser('/nonexistent/file.yml')
    result = parser.parse()
    
    assert len(parser.issues) == 1
    assert parser.issues[0].type == IssueType.INVALID_YAML
    assert parser.issues[0].severity == Severity.CRITICAL


def test_parse_invalid_yaml():
    """Test parsing invalid YAML."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        f.write("invalid: yaml: content:")
        temp_path = f.name
    
    try:
        parser = DockerComposeParser(temp_path)
        result = parser.parse()
        
        assert len(parser.issues) >= 1
        assert any(issue.type == IssueType.INVALID_YAML for issue in parser.issues)
    finally:
        Path(temp_path).unlink()


def test_service_without_image_or_build():
    """Test detecting service without image or build."""
    config = {
        'version': '3.8',
        'services': {
            'web': {
                'ports': ['8080:80']
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config, f)
        temp_path = f.name
    
    try:
        parser = DockerComposeParser(temp_path)
        result = parser.parse()
        
        assert len(parser.issues) >= 1
        assert any('image' in issue.message.lower() or 'build' in issue.message.lower() 
                   for issue in parser.issues)
    finally:
        Path(temp_path).unlink()
