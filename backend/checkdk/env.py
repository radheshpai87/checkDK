"""Load environment variables from .env file."""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent.parent / '.env'
    
    if not env_file.exists():
        return
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Only set if not already in environment
                if key and not os.getenv(key):
                    os.environ[key] = value


# Load .env on module import
load_env()
