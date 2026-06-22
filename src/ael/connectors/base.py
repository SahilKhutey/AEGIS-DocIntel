'''
AEGIS-AEL — Base Agent Connector
==================================
All agent connectors inherit from this.
'''
from __future__ import annotations

import abc
import logging
from typing import Any, AsyncIterator

from src.ael.ueo import UniversalExportObject

logger = logging.getLogger('amdi.ael.connectors.base')


class BaseConnector(abc.ABC):
    '''Base class for all agent connectors.'''

    def __init__(self, model: str = '', api_key: str = '', **kwargs):
        self.model = model
        self.api_key = api_key
        self.kwargs = kwargs
        self._client: Any = None

    @abc.abstractmethod
    def get_native_format(self) -> dict:
        '''Convert UEO to the agent's native format.'''
        raise NotImplementedError

    @abc.abstractmethod
    async def send(self, ueo: UniversalExportObject, **kwargs) -> dict:
        '''Send UEO to the agent and return the response.'''
        raise NotImplementedError

    @abc.abstractmethod
    async def stream(self, ueo: UniversalExportObject, **kwargs) -> AsyncIterator[str]:
        '''Stream response from the agent.'''
        raise NotImplementedError

    def build_system_prompt(self, ueo: UniversalExportObject) -> str:
        '''Default system prompt. Subclasses can override.'''
        return f'You are a precise document intelligence assistant. The user has asked:\n\nQUERY: {ueo.query}\n\nYou have been provided a structured Context Object (UEO) extracted by AEGIS-AMDI-OS containing:\n- Document summary ({ueo.metadata.pages} pages, {ueo.metadata.document_type})\n- {ueo.matrix.n_tables} pre-processed tables with computed metrics\n- {len(ueo.citations)} citations with confidence scores\n- Overall confidence: {ueo.confidence.overall:.3f}\n\nRULES:\n1. Answer ONLY using the provided context.\n2. For numerical questions, use the table\'s pre-computed metrics.\n3. Reference sources using [page, section] notation.\n4. If unsure, say \"I don\'t know\" rather than fabricate.\n5. Match the user\'s language.'
