'''
AEGIS-AEL — DeepSeek Connector
=================================
DeepSeek V3 / R1 — reasoning-optimized.
'''
from __future__ import annotations

import logging
from typing import AsyncIterator

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from src.ael.connectors.base import BaseConnector
from src.ael.formats.markdown_exporter import MarkdownExporter
from src.ael.ueo import UniversalExportObject

logger = logging.getLogger('amdi.ael.connectors.deepseek')


class DeepSeekConnector(BaseConnector):
    '''DeepSeek connector (OpenAI-compatible API).'''

    def __init__(self, api_key: str, model: str = 'deepseek-chat', **kwargs):
        if not HAS_OPENAI:
            raise ImportError("The 'openai' package is required to use DeepSeekConnector. Install it via 'pip install openai'.")
        super().__init__(model=model, api_key=api_key, **kwargs)
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=kwargs.get('base_url', 'https://api.deepseek.com/v1'),
        )

    def get_native_format(self) -> dict:
        return {'type': 'deepseek_chat', 'model': self.model}

    def _build_messages(self, ueo: UniversalExportObject) -> list[dict]:
        system = self.build_system_prompt(ueo)
        context = MarkdownExporter.export(ueo)
        return [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': f'CONTEXT:\n{context}\n\nQUESTION: {ueo.query}\n\nANSWER:'},
        ]

    async def send(self, ueo: UniversalExportObject, **kwargs) -> dict:
        messages = self._build_messages(ueo)
        try:
            resp = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 4096),
            )
            return {
                'agent': 'deepseek',
                'model': self.model,
                'answer': resp.choices[0].message.content,
                'input_tokens': resp.usage.prompt_tokens if resp.usage else 0,
                'output_tokens': resp.usage.completion_tokens if resp.usage else 0,
            }
        except Exception as e:
            logger.exception(f'DeepSeek send failed: {e}')
            return {'agent': 'deepseek', 'error': str(e)}

    async def stream(self, ueo: UniversalExportObject, **kwargs) -> AsyncIterator[str]:
        messages = self._build_messages(ueo)
        try:
            stream = await self._client.chat.completions.create(
                model=self.model, messages=messages, stream=True,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 4096),
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f'DeepSeek stream failed: {e}')
            yield f'[Error: {e}]'
