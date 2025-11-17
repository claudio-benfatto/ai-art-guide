"""Test configuration and shared fixtures for Barcelona AI Art Guide tests."""

import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
