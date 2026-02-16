"""
cgalpha.config — Configuration management.

This sub-package contains:
- paths:    ProjectPaths value object (centralizes all file system paths).
- settings: Settings class for environment-based configuration.
"""

from cgalpha_v2.config.paths import ProjectPaths
from cgalpha_v2.config.settings import Settings

__all__ = ["ProjectPaths", "Settings"]
