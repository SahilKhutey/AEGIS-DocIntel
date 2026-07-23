'''
AEGIS-AEL — Google Gemini Connector
=====================================
Format optimized for Gemini 1.5/2.0 — multimodal native.
'''
from __future__ import annotations

import logging
from typing import AsyncIterator

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from src.ael.connectors.base import BaseConnector
from src.ael.formats.markdown_exporter import MarkdownExporter
from src.ael.ueo import UniversalExportObject

logger = logging.getLogger('amdi.ael.connectors.gemini')


class GeminiConnector(BaseConnector):
    '''Google Gemini connector — multimodal native.'''

    def __init__(self, api_key: str, model: str = 'gemini-2.0-flash', **kwargs):
        if not HAS_GEMINI:
            raise ImportError("The 'google-generativeai' package is required to use GeminiConnector. Install it via 'pip install google-generativeai'.")
        super().__init__(model=model, api_key=api_key, **kwargs)
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(model)

    def get_native_format(self) -> dict:
        return {'type': 'gemini_multimodal', 'model': self.model}

    def _build_prompt(self, ueo: UniversalExportObject) -> str:
        system = self.build_system_prompt(ueo)
        context = MarkdownExporter.export(ueo)
        return f'{system}\n\nCONTEXT:\n{context}\n\nQUESTION: {ueo.query}\n\nANSWER:'

    async def send(self, ueo: UniversalExportObject, **kwargs) -> dict:
        prompt = self._build_prompt(ueo)
        try:
            resp = await self._client.generate_content_async(prompt)
            return {
                'agent': 'gemini',
                'model': self.model,
                'answer': resp.text or '',
                'input_tokens': len(prompt) // 4,
                'output_tokens': len(resp.text or '') // 4,
            }
        except Exception as e:
            logger.exception(f'Gemini send failed: {e}')
            return {'agent': 'gemini', 'error': str(e)}

    async def stream(self, ueo: UniversalExportObject, **kwargs) -> AsyncIterator[str]:
        prompt = self._build_prompt(ueo)
        try:
            resp = await self._client.generate_content_async(prompt, stream=True)
            async for chunk in resp:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f'Gemini stream failed: {e}')
            yield f'[Error: {e}]'
