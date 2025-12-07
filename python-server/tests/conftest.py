"""Pytest configuration for bibliophage tests."""

import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import our modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
