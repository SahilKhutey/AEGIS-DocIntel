'''
AEGIS-AEL — Anthropic Claude Connector
========================================
Format optimized for Claude 3.5 Sonnet / Opus / Haiku.
Leverages Claude's long-context + citation primitives.
'''
from __future__ import annotations

import logging
from typing import AsyncIterator

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from src.ael.connectors.base import BaseConnector
from src.ael.formats.markdown_exporter import MarkdownExporter
from src.ael.ueo import UniversalExportObject

logger = logging.getLogger('amdi.ael.connectors.claude')


class ClaudeConnector(BaseConnector):
    '''Anthropic Claude connector.'''

    def __init__(self, api_key: str, model: str = 'claude-3-5-sonnet-20241022', **kwargs):
        if not HAS_ANTHROPIC:
            raise ImportError("The 'anthropic' package is required to use ClaudeConnector. Install it via 'pip install anthropic'.")
        super().__init__(model=model, api_key=api_key, **kwargs)
        self._client = AsyncAnthropic(api_key=api_key)

    def get_native_format(self) -> dict:
        return {'type': 'anthropic_messages', 'model': self.model}

    def _build_messages(self, ueo: UniversalExportObject) -> tuple[str, list[dict]]:
        system = self.build_system_prompt(ueo)
        documents = []
        for cite in ueo.citations[:20]:
            documents.append({
                'type': 'document',
                'source': {
                    'type': 'text',
                    'media_type': 'text/plain',
                    'data': cite.snippet,
                },
                'title': f'Page {cite.page}' + (f' - {cite.section}' if cite.section else ''),
                'context': f'From {ueo.metadata.document_name}',
                'citations': {'enabled': True},
            })
        user_content: list[dict] = []
        if documents:
            user_content.append({'type': 'document', 'source': documents[0]['source'], 'title': documents[0]['title']})
        context_md = MarkdownExporter.export(ueo)
        user_content.append({'type': 'text', 'text': f'CONTEXT:\n{context_md}\n\nQUESTION: {ueo.query}\n\nANSWER:'})
        return system, [{'role': 'user', 'content': user_content}]

    async def send(self, ueo: UniversalExportObject, **kwargs) -> dict:
        system, messages = self._build_messages(ueo)
        try:
            resp = await self._client.messages.create(
                model=self.model,
                system=system,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.1),
            )
            citations = []
            for block in resp.content:
                if hasattr(block, 'citations') and block.citations:
                    for c in block.citations:
                        citations.append({
                            'text': getattr(c, 'cited_text', ''),
                            'page': getattr(c, 'page_number', None),
                        })
            return {
                'agent': 'claude',
                'model': self.model,
                'answer': ''.join(b.text for b in resp.content if hasattr(b, 'text')),
                'input_tokens': resp.usage.input_tokens if resp.usage else 0,
                'output_tokens': resp.usage.output_tokens if resp.usage else 0,
                'citations': citations,
            }
        except Exception as e:
            logger.exception(f'Claude send failed: {e}')
            return {'agent': 'claude', 'error': str(e)}

    async def stream(self, ueo: UniversalExportObject, **kwargs) -> AsyncIterator[str]:
        system, messages = self._build_messages(ueo)
        try:
            async with self._client.messages.stream(
                model=self.model,
                system=system,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', 4096),
                temperature=kwargs.get('temperature', 0.1),
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f'Claude stream failed: {e}')
            yield f'[Error: {e}]'
