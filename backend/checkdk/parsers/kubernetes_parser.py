"""Kubernetes YAML parser."""
import yaml
from pathlib import Path
from typing import List, Dict, Any


class KubernetesParser:
    """Parser for Kubernetes YAML manifests."""
    
    @staticmethod
    def parse(file_path: str) -> List[Dict[str, Any]]:
        """
        Parse Kubernetes YAML file.
        
        Args:
            file_path: Path to k8s YAML file
            
        Returns:
            List of Kubernetes resources
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(path, 'r') as f:
            content = f.read()
        
        # Parse YAML documents (multiple resources in one file)
        resources = []
        for doc in yaml.safe_load_all(content):
            if doc:  # Skip empty documents
                resources.append(doc)
        
        return resources
    
    @staticmethod
    def get_services(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Service resources."""
        return [r for r in resources if r.get('kind') == 'Service']
    
    @staticmethod
    def get_deployments(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Deployment resources."""
        return [r for r in resources if r.get('kind') == 'Deployment']
    
    @staticmethod
    def get_pods(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract Pod resources."""
        return [r for r in resources if r.get('kind') == 'Pod']
    
    @staticmethod
    def get_namespaces(resources: List[Dict[str, Any]]) -> List[str]:
        """Extract all namespaces used."""
        namespaces = set()
        for resource in resources:
            ns = resource.get('metadata', {}).get('namespace')
            if ns:
                namespaces.add(ns)
        return list(namespaces)
