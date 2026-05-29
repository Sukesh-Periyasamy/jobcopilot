"""Shared test configuration and fixtures for backend tests."""

import sys
from unittest.mock import MagicMock

# Mock jobspy module if not available (it has heavy external dependencies
# like tls_client that may not be installed in the test environment).
if "jobspy" not in sys.modules:
    try:
        import jobspy  # noqa: F401
    except (ImportError, ModuleNotFoundError):
        sys.modules["jobspy"] = MagicMock()
