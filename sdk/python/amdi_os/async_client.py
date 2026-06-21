"""
AMDI-OS Async Client.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

import aiohttp

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


class AsyncAmdiClient:
    """Asynchronous AMDI-OS client."""

    DEFAULT_BASE_URL = "https://api.amdi-os.com"
    DEFAULT_TIMEOUT = 60

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

        # Sub-API clients (async versions)
        self.documents = AsyncDocumentsAPI(self)
        self.retrieval = AsyncRetrievalAPI(self)
        self.context = AsyncContextAPI(self)
        self.export = AsyncExportAPI(self)
        self.agents = AsyncAgentsAPI(self)
        self.verification = AsyncVerificationAPI(self)
        self.engines = AsyncEnginesAPI(self)
        self.memory = AsyncMemoryAPI(self)
        self.dashboards = AsyncDashboardsAPI(self)

    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": "amdi-os-python-sdk/1.0.0",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None:
            raise RuntimeError("Client not initialized. Use 'async with'.")
        return self._session

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}{endpoint}"
        request_headers = headers or {}
        try:
            if files:
                form = aiohttp.FormData()
                for k, v in (data or {}).items():
                    form.add_field(k, str(v))
                for k, v in files.items():
                    form.add_field(k, v[1], filename=v[0])
                async with self.session.post(
                    url, data=form, params=params, headers=request_headers
                ) as resp:
                    return await self._handle_response(resp)
            else:
                async with self.session.request(
                    method, url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=request_headers,
                ) as resp:
                    return await self._handle_response(resp)
        except aiohttp.ClientTimeout:
            raise AmdiTimeoutError(f"Request timed out")
        except aiohttp.ClientConnectionError as exc:
            raise AmdiConnectionError(f"Connection failed: {exc}")

    async def _handle_response(self, response: aiohttp.ClientResponse) -> Any:
        if 200 <= response.status < 300:
            if response.status == 204:
                return None
            text = await response.text()
            if not text:
                return None
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        text = await response.text()
        try:
            error_data = json.loads(text)
        except json.JSONDecodeError:
            error_data = {"message": text}
        message = error_data.get("message", f"HTTP {response.status}")
        status = response.status
        if status in (401, 403):
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


# ========================================================================
# Async Sub-API Clients
# ========================================================================


class AsyncDocumentsAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def upload(
        self,
        file: Union[str, Path, BinaryIO],
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        wait: bool = True,
        timeout: int = 300,
    ) -> DocumentSummary:
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            with open(file_path, "rb") as f:
                return await self._upload(f, file_path.name, tags, metadata, wait, timeout)
        else:
            return await self._upload(
                file, getattr(file, "name", "upload"), tags, metadata, wait, timeout
            )

    async def _upload(
        self,
        file_handle: BinaryIO,
        filename: str,
        tags: Optional[List[str]],
        metadata: Optional[Dict[str, Any]],
        wait: bool,
        timeout: int,
    ) -> DocumentSummary:
        data = aiohttp.FormData()
        data.add_field("file", file_handle, filename=filename)
        if tags:
            data.add_field("tags", json.dumps(tags))
        if metadata:
            data.add_field("metadata", json.dumps(metadata))
        response = await self._client.request(
            "POST", "/api/v1/documents", data=data, timeout=timeout,
        )
        doc = DocumentSummary.from_dict(response)
        if wait:
            await self.wait_for_ready(doc.document_id, timeout=timeout)
        return doc

    async def get(self, document_id: str) -> Document:
        response = await self._client.request("GET", f"/api/v1/documents/{document_id}")
        return Document.from_dict(response)

    async def list(
        self,
        tag: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentSummary]:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if tag:
            params["tag"] = tag
        if file_type:
            params["file_type"] = file_type
        response = await self._client.request("GET", "/api/v1/documents", params=params)
        return [DocumentSummary.from_dict(d) for d in response]

    async def delete(self, document_id: str) -> None:
        await self._client.request("DELETE", f"/api/v1/documents/{document_id}")

    async def process(self, document_id: str, engines: Optional[List[str]] = None) -> Dict[str, EngineOutput]:
        payload = {"document_id": document_id}
        if engines:
            payload["engines"] = engines
        response = await self._client.request(
            "POST", f"/api/v1/documents/{document_id}/process", json_data=payload
        )
        return {name: EngineOutput.from_dict(out) for name, out in response.get("outputs", {}).items()}

    async def wait_for_ready(self, document_id: str, timeout: int = 300, poll_interval: float = 2.0) -> Document:
        import asyncio
        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < timeout:
            doc = await self.get(document_id)
            if doc.engine_reports:
                return doc
            await asyncio.sleep(poll_interval)
        raise AmdiTimeoutError(f"Document {document_id} not ready within {timeout}s")


class AsyncRetrievalAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def search(
        self,
        query: str,
        top_k: int = 10,
        weights: Optional[Dict[str, float]] = None,
        target_levels: Optional[List[int]] = None,
        include_snippets: bool = True,
    ) -> RetrievalResult:
        payload = {
            "query": query,
            "top_k": top_k,
            "include_snippets": include_snippets,
        }
        if weights:
            payload["weights"] = weights
        if target_levels:
            payload["target_levels"] = target_levels
        response = await self._client.request("POST", "/api/v1/search", json_data=payload)
        return RetrievalResult.from_dict(response)


class AsyncContextAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def build(
        self,
        candidates: List[Dict[str, Any]],
        total_budget: int = 4000,
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UniversalExportObject:
        payload = {"candidates": candidates, "total_budget": total_budget}
        if citations:
            payload["citations"] = citations
        if metadata:
            payload["metadata"] = metadata
        response = await self._client.request("POST", "/api/v1/context", json_data=payload)
        return UniversalExportObject.from_dict(response.get("ueo", {}))

    async def build_from_retrieval(
        self,
        retrieval_result: RetrievalResult,
        **kwargs,
    ) -> UniversalExportObject:
        candidates = [
            {
                "candidate_id": hit.doc_id,
                "content": hit.snippet,
                "relevance": hit.fused_score,
            }
            for hit in retrieval_result.hits
        ]
        return await self.build(candidates=candidates, **kwargs)


class AsyncExportAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def to_json(self, ueo: UniversalExportObject) -> str:
        import json as _json
        return _json.dumps(ueo.to_dict(), indent=2)

    async def to_markdown(self, ueo: UniversalExportObject) -> str:
        return await self._client.request(
            "POST", "/api/v1/export/markdown",
            json_data=ueo.to_dict(),
        )

    async def to_yaml(self, ueo: UniversalExportObject) -> str:
        return await self._client.request(
            "POST", "/api/v1/export/yaml",
            json_data=ueo.to_dict(),
        )


class AsyncAgentsAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client
        self.chatgpt = AsyncChatGPTAPI(client)
        self.gemini = AsyncGeminiAPI(client)
        self.claude = AsyncClaudeAPI(client)
        self.deepseek = AsyncDeepSeekAPI(client)
        self.qwen = AsyncQwenAPI(client)
        self.local = AsyncLocalAPI(client)

    async def list_agents(self) -> List[Dict[str, Any]]:
        return await self._client.request("GET", "/api/v1/agents")

    async def send(
        self,
        agent: str,
        ueo: UniversalExportObject,
        question: Optional[str] = None,
        **kwargs,
    ) -> ConnectorResponse:
        payload = {"ueo": ueo.to_dict()}
        if question:
            payload["question"] = question
        payload.update(kwargs)
        response = await self._client.request(
            "POST", f"/api/v1/agents/{agent}/send", json_data=payload,
        )
        return ConnectorResponse.from_dict(response)


class AsyncChatGPTAPI:
    def __init__(self, client):
        self._client = client

    async def send_ueo(self, ueo, question=None, **kwargs):
        return await AsyncAgentsAPI(self._client).send("chatgpt", ueo, question, **kwargs)


class AsyncGeminiAPI:
    def __init__(self, client):
        self._client = client

    async def send_ueo(self, ueo, question=None, **kwargs):
        return await AsyncAgentsAPI(self._client).send("gemini", ueo, question, **kwargs)


class AsyncClaudeAPI:
    def __init__(self, client):
        self._client = client

    async def send_ueo(self, ueo, question=None, **kwargs):
        return await AsyncAgentsAPI(self._client).send("claude", ueo, question, **kwargs)


class AsyncDeepSeekAPI:
    def __init__(self, client):
        self._client = client

    async def send_ueo(self, ueo, question=None, **kwargs):
        return await AsyncAgentsAPI(self._client).send("deepseek", ueo, question, **kwargs)


class AsyncQwenAPI:
    def __init__(self, client):
        self._client = client

    async def send_ueo(self, ueo, question=None, **kwargs):
        return await AsyncAgentsAPI(self._client).send("qwen", ueo, question, **kwargs)


class AsyncLocalAPI:
    def __init__(self, client):
        self._client = client

    async def send_ueo(self, ueo, question=None, **kwargs):
        return await AsyncAgentsAPI(self._client).send("local", ueo, question, **kwargs)


class AsyncVerificationAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def verify(
        self,
        response_text: str,
        source_documents: Optional[Dict[str, Any]] = None,
        knowledge_base: Optional[Dict[str, Any]] = None,
    ) -> VerificationReport:
        payload = {"response_text": response_text}
        if source_documents:
            payload["source_documents"] = source_documents
        if knowledge_base:
            payload["knowledge_base"] = knowledge_base
        response = await self._client.request("POST", "/api/v1/verify", json_data=payload)
        return VerificationReport.from_dict(response)


class AsyncEnginesAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def list(self) -> List[str]:
        response = await self._client.request("GET", "/api/v1/engines")
        return response.get("engines", [])

    async def run(self, engine: str, document_id: str, **params) -> EngineOutput:
        payload = {"document_id": document_id, **params}
        response = await self._client.request(
            "POST", f"/api/v1/engines/{engine}/run", json_data=payload,
        )
        return EngineOutput.from_dict(response)


class AsyncMemoryAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def get_stats(self) -> Dict[str, Any]:
        return await self._client.request("GET", "/api/v1/memory/stats")

    async def promote(self, level: int, max_items: int = 100) -> Dict[str, Any]:
        return await self._client.request(
            "POST", "/api/v1/memory/promote",
            json_data={"level": level, "max_items": max_items},
        )

    async def evict(self, level: int, n: int = 10) -> Dict[str, Any]:
        return await self._client.request(
            "POST", "/api/v1/memory/evict",
            json_data={"level": level, "n": n},
        )

    async def maintenance(self) -> Dict[str, int]:
        return await self._client.request("POST", "/api/v1/memory/maintenance")


class AsyncDashboardsAPI:
    def __init__(self, client: AsyncAmdiClient):
        self._client = client

    async def get(self, dashboard: str) -> Dict[str, Any]:
        return await self._client.request("GET", f"/api/v1/dashboards/{dashboard}")

    async def upload_dashboard(self) -> Dict[str, Any]:
        return await self.get("upload")

    async def document_explorer(self) -> Dict[str, Any]:
        return await self.get("documents")

    async def memory_dashboard(self) -> Dict[str, Any]:
        return await self.get("memory")

    async def analytics(self) -> Dict[str, Any]:
        return await self.get("analytics")

    async def performance(self) -> Dict[str, Any]:
        return await self.get("performance")
