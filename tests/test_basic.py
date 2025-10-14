"""Basic tests to verify setup."""

import beast_orchestrator


def test_version():
    """Test that version is defined."""
    assert hasattr(beast_orchestrator, "__version__")
    assert beast_orchestrator.__version__ == "0.1.0"


def test_import():
    """Test that package can be imported."""
    assert beast_orchestrator is not None

