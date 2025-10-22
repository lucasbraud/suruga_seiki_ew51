"""Global configuration settings."""

import os
from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent.parent

# DLL directory
DLL_DIR = PACKAGE_ROOT / "io" / "dll"

# DLL paths
SRGMC_DLL_PATH = str(DLL_DIR / "srgmc.dll")