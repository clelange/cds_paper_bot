"""Test environment configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path


if "MAGICK_HOME" not in os.environ and Path("/opt/homebrew/lib").is_dir():
    os.environ["MAGICK_HOME"] = "/opt/homebrew"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
