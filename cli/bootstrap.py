"""Bootstrap entry point for PyInstaller builds.

PyInstaller executes the entry-point file as a top-level script (__main__),
which means relative imports inside checkdkcli/ would fail with:

    ImportError: attempted relative import with no known parent package

This tiny wrapper uses an absolute import so that checkdkcli is loaded as
a proper package and all relative imports within it resolve correctly.

This file is ONLY used by PyInstaller (checkdk.spec) — the pip-installed
CLI uses the entry point defined in pyproject.toml (checkdkcli.main:main),
which is completely unaffected.
"""

import warnings

# Suppress harmless RequestsDependencyWarning from requests when running
# inside a PyInstaller frozen binary (charset_normalizer version detection
# fails in the frozen environment).
warnings.filterwarnings("ignore", message="Unable to find acceptable character detection dependency")

from checkdkcli.main import main

main()
