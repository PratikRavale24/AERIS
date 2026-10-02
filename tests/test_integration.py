"""AERIS — System Integration Test Runner."""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app.core.config import APP_NAME


def test_system_name_constant() -> None:
    """Verify system name configuration constant."""
    assert APP_NAME == "AERIS"
