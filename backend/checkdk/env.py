"""Load environment variables from .env using python-dotenv.

python-dotenv is already a declared dependency, so we use it instead of a
hand-rolled parser.  This correctly handles quoted values, export-prefixed
lines, and inline comments that the previous implementation got wrong.
"""

from pathlib import Path


def load_env() -> None:
    """Load .env from the backend package root (backend/.env).

    Uses ``override=False`` so variables already present in the process
    environment (e.g. injected by Docker Compose) always take precedence.
    """
    try:
        from dotenv import load_dotenv
        env_file = Path(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_file, override=False)
    except ImportError:
        pass  # python-dotenv not installed; rely on the existing environment


# Load on module import so any code that imports this module gets env vars
load_env()
