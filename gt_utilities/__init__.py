"""gt_utilities

A small, generic package initializer for gt_utilities.
Keep this file minimal: export a version, a tiny logging helper, and a version accessor.
"""

from __future__ import annotations

import logging
from pathlib import Path

__all__ = ["__version__", "get_version", "setup_logger"]

__version__ = "0.0.1"


def get_version() -> str:
    """Return the package version."""
    return __version__


def setup_logger(name: str | None = None, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger for the package.

    - If the logger already has handlers, this is a no-op except for setting level.
    - Otherwise it attaches a StreamHandler with a compact formatter.
    """
    logger = logging.getLogger(name or "gt_utilities")
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
    return logger


# Ensure importing the package doesn't emit logs unless the app configures logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from the given file until we find the project root.

    The root is identified by containing BOTH:
    - pyproject.toml
    - data/ directory
    """
    start = start or Path(__file__).resolve()

    for parent in [start, *start.parents]:
        if (parent / "pyproject.toml").exists() and (parent / "data").exists():
            return parent

    # Fallback: return directory containing gt_utilities
    return Path(__file__).resolve().parent
