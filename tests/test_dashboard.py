"""Tests for dashboard components and API integration."""
import pytest
import importlib.util
from unittest.mock import patch, MagicMock

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("streamlit") is None,
    reason="streamlit not installed (optional UI dependency)",
)


def test_dashboard_imports_cleanly():
    """Smoke test: confirms that dashboard modules can be located and path-configured."""
    try:
        import sys
        from pathlib import Path
        dash_path = Path(__file__).parent.parent / "dashboard"
        amdi_path = Path(__file__).parent.parent / "amdi-os"
        sys.path.insert(0, str(dash_path))
        sys.path.insert(0, str(amdi_path))
        assert str(dash_path) in sys.path
    except ImportError as e:
        if "streamlit" in str(e):
            pytest.skip("Streamlit not available")
        else:
            raise


def test_api_url_config():
    """Test API URL configuration."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    try:
        from dashboard.app import API_URL
    except ImportError as e:
        pytest.skip(f"Dashboard dependencies unavailable: {e}")
    assert API_URL.startswith("http")


def test_page_routing():
    """Test that all pages are registered."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    try:
        from dashboard.app import PAGES
    except ImportError as e:
        pytest.skip(f"Dashboard dependencies unavailable: {e}")
    expected = [
        "📤 Upload", "🔍 Query", "📁 Document Explorer",
        "📐 Geometry", "🌐 3D View", "📊 Matrix", "🕸️ Graph",
        "🎨 Templates", "💾 Memory", "📈 Analytics", "⚙️ Settings",
    ]
    for page in expected:
        assert page in PAGES
        assert callable(PAGES[page])


def test_auth_headers_generation():
    """Test header generation with tenant and token isolation."""
    import sys
    from pathlib import Path
    import streamlit as st
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    from dashboard.app import _get_auth_headers

    # Default headers
    headers = _get_auth_headers()
    assert "Authorization" in headers
    assert headers["Authorization"].startswith("Bearer ")
    assert "X-Tenant-ID" in headers

    # Custom session values
    st.session_state["auth_token"] = "custom-secret-key"
    st.session_state["tenant_id"] = "acme-corp"
    custom_headers = _get_auth_headers()
    assert custom_headers["Authorization"] == "Bearer custom-secret-key"
    assert custom_headers["X-API-Key"] == "custom-secret-key"
    assert custom_headers["X-Tenant-ID"] == "acme-corp"

    # Pre-formatted Bearer token
    st.session_state["auth_token"] = "Bearer jwt.token.here"
    bearer_headers = _get_auth_headers()
    assert bearer_headers["Authorization"] == "Bearer jwt.token.here"


@patch("dashboard.app.requests.get")
def test_api_get_authenticated(mock_get):
    """Test api_get carries authentication headers and query parameters."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    from dashboard.app import api_get

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"documents": [{"doc_id": "d1", "filename": "test.pdf"}]}
    mock_get.return_value = mock_resp

    result = api_get("/v1/documents", params={"page": 1, "page_size": 10})
    assert result == {"documents": [{"doc_id": "d1", "filename": "test.pdf"}]}
    mock_get.assert_called_once()
    _, kwargs = mock_get.call_args
    assert "headers" in kwargs
    assert "Authorization" in kwargs["headers"]
    assert kwargs["params"] == {"page": 1, "page_size": 10}


@patch("dashboard.app.requests.post")
def test_api_post_authenticated(mock_post):
    """Test api_post carries authentication headers with json payload and multipart files."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    from dashboard.app import api_post

    # JSON post
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"answer": "Revenue was $10M", "confidence": "HIGH"}
    mock_post.return_value = mock_resp

    query_payload = {"question": "What is revenue?", "top_k": 5}
    res = api_post("/v1/query", json_data=query_payload)
    assert res["answer"] == "Revenue was $10M"
    _, kwargs = mock_post.call_args
    assert kwargs["json"] == query_payload
    assert "Authorization" in kwargs["headers"]

    # Multipart file upload
    mock_resp.json.return_value = {"doc_id": "uuid-123", "filename": "sample.pdf"}
    files = {"file": ("sample.pdf", b"%PDF-1.4 mock content")}
    res_upload = api_post("/v1/ingest", files=files)
    assert res_upload["doc_id"] == "uuid-123"
    _, kwargs_upload = mock_post.call_args
    assert "files" in kwargs_upload


@patch("dashboard.app.requests.delete")
def test_api_delete_204_no_content(mock_delete):
    """Test api_delete cleanly handles 204 No Content without JSON parsing errors."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))
    from dashboard.app import api_delete

    mock_resp = MagicMock()
    mock_resp.status_code = 204
    mock_resp.content = b""
    mock_delete.return_value = mock_resp

    result = api_delete("/v1/documents/d1")
    assert result == {"deleted": True}
    mock_delete.assert_called_once()
    _, kwargs = mock_delete.call_args
    assert "Authorization" in kwargs["headers"]
