import os
import pytest
from fastapi.testclient import TestClient
from src.main import app
from amdi_os import AmdiClient
from amdi_os.exceptions import AmdiNotFoundError


@pytest.fixture(scope="module")
def live_api_client():
    """
    Real integration harness: runs the actual FastAPI app in-process and
    points the real SDK client at it — this is what should have existed
    from day one and would have caught every path mismatch in Step 13.1
    on the first run.
    """
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["AEGIS_ENVIRONMENT"] = "development"
    with TestClient(app) as test_client:
        sdk_client = AmdiClient(api_key="dev-test-tenant", base_url="http://testserver")
        orig_req = test_client.request

        def adapted_req(method, url, **kwargs):
            kwargs.pop("timeout", None)
            return orig_req(method, url, **kwargs)

        sdk_client.session.request = adapted_req
        yield sdk_client


def test_sdk_upload_hits_real_endpoint(live_api_client, tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello, this is a real test document.")
    doc = live_api_client.documents.upload(str(f), wait=False)
    assert doc.document_id is not None  # would have failed with a 404 before this phase's fix
    assert doc.name == "test.txt"


def test_sdk_search_hits_real_endpoint(live_api_client):
    result = live_api_client.retrieval.search(query="test query")
    assert result is not None  # would have hit a nonexistent /api/v1/search before this fix
    assert result.latency_ms >= 0


def test_sdk_get_and_delete_hit_real_endpoints(live_api_client, tmp_path):
    f = tmp_path / "test_doc.txt"
    f.write_text("Document to test get and delete endpoints.")
    doc = live_api_client.documents.upload(str(f), wait=False)
    doc_id = doc.document_id

    # Test get
    fetched = live_api_client.documents.get(doc_id)
    assert fetched.document_id == doc_id

    # Test delete
    live_api_client.documents.delete(doc_id)

    # Verify deleted returns 404
    with pytest.raises(AmdiNotFoundError):
        live_api_client.documents.get(doc_id)


def test_sdk_process_hits_real_reindex_endpoint(live_api_client, tmp_path):
    f = tmp_path / "reindex_doc.txt"
    f.write_text("Document to test reindexing process endpoint.")
    doc = live_api_client.documents.upload(str(f), wait=False)
    doc_id = doc.document_id

    # Calling process hits /v1/documents/{doc_id}/reindex
    res = live_api_client.documents.process(doc_id)
    assert res is not None
    assert "doc_id" in res
