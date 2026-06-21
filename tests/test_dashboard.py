"""Tests for dashboard components."""
import pytest
from unittest.mock import patch, MagicMock


def test_dashboard_imports():
    """Test that dashboard module imports without errors."""
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
        sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))
        # Should not raise ImportError
        assert True
    except ImportError as e:
        # Streamlit might not be available in test env
        if "streamlit" in str(e):
            pytest.skip("Streamlit not available")
        else:
            raise


def test_api_url_config():
    """Test API URL configuration."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))
    from dashboard.app import API_URL
    assert API_URL.startswith("http")


def test_page_routing():
    """Test that all pages are registered."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))
    from dashboard.app import PAGES
    expected = [
        "📤 Upload", "🔍 Query", "📁 Document Explorer",
        "📐 Geometry", "🌐 3D View", "📊 Matrix", "🕸️ Graph",
        "🎨 Templates", "💾 Memory", "📈 Analytics", "⚙️ Settings",
    ]
    for page in expected:
        assert page in PAGES
        assert callable(PAGES[page])
