"""Pytest configuration for the Mazda SDK test suite.

Makes the repository root importable so the tests can import the Home
Assistant custom component under ``custom_components/mazda_6e_cx6`` no matter
how pytest is invoked.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
