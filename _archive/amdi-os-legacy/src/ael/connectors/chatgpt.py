'''
AEGIS-AEL — ChatGPT / OpenAI Connector
========================================
Format optimized for GPT-4o, GPT-4 Turbo, o1 models.
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

logger = logging.getLogger('amdi.ael.connectors.chatgpt')


class ChatGPTConnector(BaseConnector):
    '''OpenAI ChatGPT connector.'''

    def __init__(self, api_key: str, model: str = 'gpt-4o', **kwargs):
        if not HAS_OPENAI:
            raise ImportError("The 'openai' package is required to use ChatGPTConnector. Install it via 'pip install openai'.")
        super().__init__(model=model, api_key=api_key, **kwargs)
        self._client = AsyncOpenAI(api_key=api_key)

    def get_native_format(self) -> dict:
        return {'type': 'openai_chat', 'messages': [], 'model': self.model}

    def _build_messages(self, ueo: UniversalExportObject) -> list[dict]:
        system = self.build_system_prompt(ueo)
        context = MarkdownExporter.export(ueo)
        user = f'CONTEXT:\n{context}\n\nQUESTION: {ueo.query}\n\nANSWER (with [page, section] citations):'
        return [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
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
                'agent': 'chatgpt',
                'model': self.model,
                'answer': resp.choices[0].message.content,
                'input_tokens': resp.usage.prompt_tokens if resp.usage else 0,
                'output_tokens': resp.usage.completion_tokens if resp.usage else 0,
                'finish_reason': resp.choices[0].finish_reason,
            }
        except Exception as e:
            logger.exception(f'ChatGPT send failed: {e}')
            return {'agent': 'chatgpt', 'error': str(e)}

    async def stream(self, ueo: UniversalExportObject, **kwargs) -> AsyncIterator[str]:
        messages = self._build_messages(ueo)
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get('temperature', 0.1),
                max_tokens=kwargs.get('max_tokens', 4096),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f'ChatGPT stream failed: {e}')
            yield f'[Error: {e}]'
