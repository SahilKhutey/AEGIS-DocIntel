"""
AMDI-OS Python Client.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, Iterator, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    AmdiAuthError,
    AmdiConnectionError,
    AmdiError,
    AmdiNotFoundError,
    AmdiRateLimitError,
    AmdiServerError,
    AmdiTimeoutError,
    AmdiValidationError,
)
from .models import (
    ConnectorResponse,
    Document,
    DocumentSummary,
    EngineOutput,
    RetrievalResult,
    UniversalExportObject,
    VerificationReport,
)


class AmdiClient:
    """
    Synchronous AMDI-OS client.

    Usage:
        client = AmdiClient(api_key="...", base_url="...")
        doc = client.documents.upload("file.pdf")
        result = client.retrieval.search("query")
    """

    DEFAULT_BASE_URL = "https://api.amdi-os.com"
    DEFAULT_TIMEOUT = 60
    MAX_RETRIES = 3

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = self._create_session(max_retries)

        # Sub-clients
        self.documents = DocumentsAPI(self)
        self.retrieval = RetrievalAPI(self)
        self.context = ContextAPI(self)
        self.export = ExportAPI(self)
        self.agents = AgentsAPI(self)
        self.verification = VerificationAPI(self)
        self.engines = EnginesAPI(self)
        self.memory = MemoryAPI(self)
        self.dashboards = DashboardsAPI(self)

    def _create_session(self, max_retries: int) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "amdi-os-python-sdk/1.0.0",
            "Content-Type": "application/json",
        })
        return session

    def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Make an HTTP request."""
        url = f"{self.base_url}{endpoint}"
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                data=data,
                files=files,
                headers=request_headers,
                timeout=timeout or self.timeout,
            )
        except requests.exceptions.Timeout as exc:
            raise AmdiTimeoutError(f"Request timed out: {exc}")
        except requests.exceptions.ConnectionError as exc:
            raise AmdiConnectionError(f"Connection failed: {exc}")
        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Any:
        if 200 <= response.status_code < 300:
            if response.status_code == 204 or not response.content:
                return None
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.text
        # error
        try:
            error_data = response.json()
        except json.JSONDecodeError:
            error_data = {"message": response.text}
        message = error_data.get("message", f"HTTP {response.status_code}")
        status = response.status_code
        if status == 401 or status == 403:
            raise AmdiAuthError(message, status_code=status, response=error_data)
        if status == 404:
            raise AmdiNotFoundError(message, status_code=status, response=error_data)
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise AmdiRateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                status_code=status,
                response=error_data,
            )
        if 400 <= status < 500:
            raise AmdiValidationError(message, status_code=status, response=error_data)
        if status >= 500:
            raise AmdiServerError(message, status_code=status, response=error_data)
        raise AmdiError(message, status_code=status, response=error_data)

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class DocumentsAPI:
    """Document management API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def upload(
        self,
        file: Union[str, Path, BinaryIO],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        wait: bool = True,
        timeout: int = 300,
    ) -> DocumentSummary:
        """Upload a document."""
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            file_handle = open(file_path, "rb")
            should_close = True
        else:
            file_handle = file
            should_close = False
        try:
            files = {"file": (getattr(file, "name", "upload"), file_handle)}
            data = {}
            if tags:
                data["tags"] = json.dumps(tags)
            if metadata:
                data["metadata"] = json.dumps(metadata)
            response = self._client.request(
                "POST",
                "/api/v1/documents",
                data=data,
                files=files,
                timeout=timeout,
            )
            doc = DocumentSummary.from_dict(response)
            if wait:
                self.wait_for_ready(doc.document_id, timeout=timeout)
            return doc
        finally:
            if should_close:
                file_handle.close()

    def get(self, document_id: str) -> Document:
        """Get a document by ID."""
        response = self._client.request("GET", f"/api/v1/documents/{document_id}")
        return Document.from_dict(response)

    def list(
        self,
        tag: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentSummary]:
        """List documents."""
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tag:
            params["tag"] = tag
        if file_type:
            params["file_type"] = file_type
        response = self._client.request("GET", "/api/v1/documents", params=params)
        return [DocumentSummary.from_dict(d) for d in response]

    def delete(self, document_id: str) -> None:
        """Delete a document."""
        self._client.request("DELETE", f"/api/v1/documents/{document_id}")

    def process(self, document_id: str, engines: Optional[List[str]] = None) -> Dict[str, EngineOutput]:
        """Run processing engines on a document."""
        payload = {"document_id": document_id}
        if engines:
            payload["engines"] = engines
        response = self._client.request("POST", f"/api/v1/documents/{document_id}/process", json_data=payload)
        return {name: EngineOutput.from_dict(out) for name, out in response.get("outputs", {}).items()}

    def wait_for_ready(self, document_id: str, timeout: int = 300, poll_interval: float = 2.0) -> Document:
        """Wait for document to be processed."""
        start = time.time()
        while time.time() - start < timeout:
            doc = self.get(document_id)
            if doc.engine_reports:
                return doc
            time.sleep(poll_interval)
        raise AmdiTimeoutError(f"Document {document_id} not ready within {timeout}s")


class RetrievalAPI:
    """Hybrid retrieval API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def search(
        self,
        query: str,
        top_k: int = 10,
        weights: Optional[Dict[str, float]] = None,
        target_levels: Optional[List[int]] = None,
        include_snippets: bool = True,
    ) -> RetrievalResult:
        """Execute a hybrid retrieval query."""
        payload = {
            "query": query,
            "top_k": top_k,
            "include_snippets": include_snippets,
        }
        if weights:
            payload["weights"] = weights
        if target_levels:
            payload["target_levels"] = target_levels
        response = self._client.request("POST", "/api/v1/search", json_data=payload)
        return RetrievalResult.from_dict(response)

    def semantic(self, embedding: List[float], top_k: int = 10) -> RetrievalResult:
        """Semantic-only search."""
        return self.search(query="", top_k=top_k)

    def graph(self, seed_nodes: List[str], top_k: int = 10) -> RetrievalResult:
        """Graph-based search (PPR)."""
        return self.search(query="", top_k=top_k)


class ContextAPI:
    """Context building API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def build(
        self,
        candidates: List[Dict[str, Any]],
        total_budget: int = 4000,
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UniversalExportObject:
        """Build an optimized context."""
        payload = {
            "candidates": candidates,
            "total_budget": total_budget,
        }
        if citations:
            payload["citations"] = citations
        if metadata:
            payload["metadata"] = metadata
        response = self._client.request("POST", "/api/v1/context", json_data=payload)
        return UniversalExportObject.from_dict(response.get("ueo", {}))

    def build_from_retrieval(
        self,
        retrieval_result: RetrievalResult,
        **kwargs,
    ) -> UniversalExportObject:
        """Build context from a retrieval result."""
        candidates = [
            {
                "candidate_id": hit.doc_id,
                "content": hit.snippet,
                "relevance": hit.fused_score,
            }
            for hit in retrieval_result.hits
        ]
        return self.build(candidates=candidates, **kwargs)


class ExportAPI:
    """Export API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def to_json(self, ueo: UniversalExportObject) -> str:
        """Export UEO to JSON."""
        import json
        return json.dumps(ueo.to_dict(), indent=2)

    def to_markdown(self, ueo: UniversalExportObject) -> str:
        """Export UEO to Markdown."""
        return self._client.request(
            "POST", "/api/v1/export/markdown",
            json_data=ueo.to_dict(),
        )

    def to_yaml(self, ueo: UniversalExportObject) -> str:
        """Export UEO to YAML."""
        return self._client.request(
            "POST", "/api/v1/export/yaml",
            json_data=ueo.to_dict(),
        )

    def save(
        self,
        ueo: UniversalExportObject,
        output_dir: str,
        base_name: str = "context",
        formats: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Save UEO to files."""
        return self._client.request(
            "POST", "/api/v1/export/files",
            json_data={
                "ueo": ueo.to_dict(),
                "output_dir": output_dir,
                "base_name": base_name,
                "formats": formats or ["json", "markdown", "yaml"],
            },
        )


class AgentsAPI:
    """AI agent connectors API."""

    def __init__(self, client: AmdiClient):
        self._client = client
        # Agent-specific sub-clients
        self.chatgpt = ChatGPTAPI(client)
        self.gemini = GeminiAPI(client)
        self.claude = ClaudeAPI(client)
        self.deepseek = DeepSeekAPI(client)
        self.qwen = QwenAPI(client)
        self.local = LocalAPI(client)

    def list_agents(self) -> List[Dict[str, Any]]:
        """List available agents."""
        return self._client.request("GET", "/api/v1/agents")

    def send(
        self,
        agent: str,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        **kwargs,
    ) -> ConnectorResponse:
        """Send UEO to a specific agent."""
        payload = {"ueo": ueo.to_dict()}
        if question:
            payload["question"] = question
        payload.update(kwargs)
        response = self._client.request(
            "POST", f"/api/v1/agents/{agent}/send",
            json_data=payload,
        )
        return ConnectorResponse.from_dict(response)


class ChatGPTAPI:
    def __init__(self, client):
        self._client = client

    def send_ueo(
        self,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ConnectorResponse:
        return AgentsAPI(self._client).send(
            "chatgpt", ueo, question,
            model=model, temperature=temperature, max_tokens=max_tokens,
        )


class GeminiAPI:
    def __init__(self, client):
        self._client = client

    def send_ueo(
        self,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ConnectorResponse:
        return AgentsAPI(self._client).send(
            "gemini", ueo, question,
            model=model, temperature=temperature, max_tokens=max_tokens,
        )


class ClaudeAPI:
    def __init__(self, client):
        self._client = client

    def send_ueo(
        self,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        model: str = "claude-3.5-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ConnectorResponse:
        return AgentsAPI(self._client).send(
            "claude", ueo, question,
            model=model, temperature=temperature, max_tokens=max_tokens,
        )


class DeepSeekAPI:
    def __init__(self, client):
        self._client = client

    def send_ueo(
        self,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ConnectorResponse:
        return AgentsAPI(self._client).send(
            "deepseek", ueo, question,
            model=model, temperature=temperature, max_tokens=max_tokens,
        )


class QwenAPI:
    def __init__(self, client):
        self._client = client

    def send_ueo(
        self,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        model: str = "qwen-2.5",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ConnectorResponse:
        return AgentsAPI(self._client).send(
            "qwen", ueo, question,
            model=model, temperature=temperature, max_tokens=max_tokens,
        )


class LocalAPI:
    def __init__(self, client):
        self._client = client

    def send_ueo(
        self,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        model: str = "llama3",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> ConnectorResponse:
        return AgentsAPI(self._client).send(
            "local", ueo, question,
            model=model, temperature=temperature, max_tokens=max_tokens,
        )


class VerificationAPI:
    """Verification API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def verify(
        self,
        response_text: str,
        source_documents: Optional[Dict[str, Any]] = None,
        knowledge_base: Optional[Dict[str, Any]] = None,
    ) -> VerificationReport:
        """Verify an AI response."""
        payload = {"response_text": response_text}
        if source_documents:
            payload["source_documents"] = source_documents
        if knowledge_base:
            payload["knowledge_base"] = knowledge_base
        response = self._client.request("POST", "/api/v1/verify", json_data=payload)
        return VerificationReport.from_dict(response)


class EnginesAPI:
    """Engine management API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def list(self) -> List[str]:
        """List available engines."""
        response = self._client.request("GET", "/api/v1/engines")
        return response.get("engines", [])

    def run(
        self,
        engine: str,
        document_id: str,
        **params,
    ) -> EngineOutput:
        """Run a specific engine on a document."""
        payload = {"document_id": document_id, **params}
        response = self._client.request(
            "POST", f"/api/v1/engines/{engine}/run",
            json_data=payload,
        )
        return EngineOutput.from_dict(response)


class MemoryAPI:
    """Memory management API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return self._client.request("GET", "/api/v1/memory/stats")

    def promote(self, level: int, max_items: int = 100) -> Dict[str, Any]:
        """Promote items to higher levels."""
        return self._client.request(
            "POST", "/api/v1/memory/promote",
            json_data={"level": level, "max_items": max_items},
        )

    def evict(self, level: int, n: int = 10) -> Dict[str, Any]:
        """Evict items from a level."""
        return self._client.request(
            "POST", "/api/v1/memory/evict",
            json_data={"level": level, "n": n},
        )

    def maintenance(self) -> Dict[str, int]:
        """Run memory maintenance."""
        return self._client.request("POST", "/api/v1/memory/maintenance")


class DashboardsAPI:
    """Dashboard data API."""

    def __init__(self, client: AmdiClient):
        self._client = client

    def get(self, dashboard: str) -> Dict[str, Any]:
        """Get dashboard data."""
        return self._client.request("GET", f"/api/v1/dashboards/{dashboard}")

    def upload_dashboard(self) -> Dict[str, Any]:
        return self.get("upload")

    def document_explorer(self) -> Dict[str, Any]:
        return self.get("documents")

    def memory_dashboard(self) -> Dict[str, Any]:
        return self.get("memory")

    def analytics(self) -> Dict[str, Any]:
        return self.get("analytics")

    def performance(self) -> Dict[str, Any]:
        return self.get("performance")
