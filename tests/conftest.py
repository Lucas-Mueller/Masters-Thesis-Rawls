"""
Common test configuration for the MAAI framework.
Handles path setup and common imports for all test files.
"""

import sys
import os
from pathlib import Path
import pytest

# Add src directory to path for all test files
repo_root = Path(__file__).parent.parent
src_path = repo_root / 'src'
sys.path.insert(0, str(src_path))

# Also add the main project directory for imports that expect it
sys.path.insert(0, str(repo_root))

# Set up test environment
os.environ['TESTING'] = '1'

# Configure pytest-asyncio
pytest_plugins = ['pytest_asyncio']