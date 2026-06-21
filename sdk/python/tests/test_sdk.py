import pytest
from amdi_os import AmdiClient, AsyncAmdiClient
from amdi_os.exceptions import AmdiError
from amdi_os.models import DocumentSummary


def test_imports():
    assert AmdiClient is not None
    assert AsyncAmdiClient is not None
    assert AmdiError is not None


def test_client_init():
    client = AmdiClient(api_key="test-key", base_url="http://localhost:8000")
    assert client.api_key == "test-key"
    assert client.base_url == "http://localhost:8000"
    assert client.documents is not None
    assert client.retrieval is not None
