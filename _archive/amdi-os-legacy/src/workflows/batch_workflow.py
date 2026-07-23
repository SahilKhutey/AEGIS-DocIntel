'''Batch Workflow - Process many documents in parallel.'''

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.document_object import DocumentFormat, DocumentObject
from src.workflows.ingest_workflow import IngestWorkflow
from src.workflows.query_workflow import QueryWorkflow


class BatchWorkflow:
    '''
    Process multiple documents concurrently with rate limiting.

    Use cases:
    - Bulk ingestion of document directories
    - Batch queries against multiple documents
    - Benchmarking across datasets
    '''

    def __init__(self, max_concurrent: int = 4, **ingest_kwargs):
        self.max_concurrent = max_concurrent
        self.ingest_kwargs = ingest_kwargs
        self._workflows: dict[str, IngestWorkflow] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def process_directory(
        self,
        directory: str,
        pattern: str = '*.pdf',
        queries: list[str] | None = None,
    ) -> list[dict]:
        '''Process all files in a directory matching pattern.'''
        path = Path(directory)
        if not path.exists():
            return [{'error': f'Directory not found: {directory}'}]
        files = sorted(path.glob(pattern))
        logger.info(f'Processing {len(files)} files from {directory}')
        tasks = [self._process_file(f, queries) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for f, r in zip(files, results):
            if isinstance(r, Exception):
                processed.append({'file': str(f), 'error': str(r)})
            else:
                processed.append(r)
        return processed

    async def process_files(
        self,
        file_paths: list[str],
        queries: list[str] | None = None,
    ) -> list[dict]:
        '''Process specific files.'''
        tasks = [self._process_file(Path(p), queries) for p in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        processed = []
        for p, r in zip(file_paths, results):
            if isinstance(r, Exception):
                processed.append({'file': p, 'error': str(r)})
            else:
                processed.append(r)
        return processed

    async def _process_file(
        self, file_path: Path, queries: list[str] | None = None
    ) -> dict:
        '''Process single file with rate limiting.'''
        async with self._semaphore:
            try:
                # Determine format
                fmt = self._detect_format(file_path)
                if fmt is None:
                    return {'file': str(file_path), 'error': 'Unsupported format'}

                # Create workflow for this document
                workflow = IngestWorkflow(**self.ingest_kwargs)
                await workflow.initialize()
                try:
                    # Read file
                    raw = file_path.read_bytes()
                    doc = DocumentObject(
                        filename=file_path.name,
                        format=fmt,
                        raw_bytes=raw,
                    )
                    # Ingest
                    info = await workflow.ingest(doc)
                    result = {
                        'file': str(file_path),
                        'filename': file_path.name,
                        'doc_id': info['doc_id'],
                        'status': 'indexed',
                        'pages': info['pages'],
                        'blocks': info['blocks'],
                        'tables': info['tables'],
                        'templates': info['templates'],
                        'timings': info['timings'],
                    }
                    # Optional: run queries
                    if queries:
                        query_wf = QueryWorkflow(
                            ingest=workflow,
                            llm_provider=self.ingest_kwargs.get('llm_provider', 'openai'),
                            llm_model=self.ingest_kwargs.get('llm_model', 'gpt-4o-mini'),
                            llm_api_key=self.ingest_kwargs.get('llm_api_key', ''),
                        )
                        query_results = []
                        for q in queries:
                            try:
                                qr = await query_wf.query(q)
                                query_results.append({
                                    'question': q,
                                    'answer': qr['answer'][:500],
                                    'query_type': qr['query_type'],
                                })
                            except Exception as e:
                                query_results.append({'question': q, 'error': str(e)})
                        result['queries'] = query_results
                    return result
                finally:
                    await workflow.shutdown()
            except Exception as e:
                logger.exception(f'Failed to process {file_path}')
                return {'file': str(file_path), 'error': str(e)}

    @staticmethod
    def _detect_format(file_path: Path) -> DocumentFormat | None:
        '''Detect file format.'''
        ext = file_path.suffix.lower()
        if ext == '.pdf':
            return DocumentFormat.PDF
        elif ext == '.docx':
            return DocumentFormat.DOCX
        elif ext == '.pptx':
            return DocumentFormat.PPTX
        elif ext == '.xlsx':
            return DocumentFormat.XLSX
        elif ext in {'.png', '.jpg', '.jpeg', '.tiff'}:
            return DocumentFormat.IMAGE
        elif ext in {'.txt', '.md'}:
            return DocumentFormat.TEXT
        return None

    async def close_all(self):
        '''Cleanup all workflows.'''
        for wf in self._workflows.values():
            try:
                await wf.shutdown()
            except Exception:
                pass
        self._workflows.clear()
