'''
AEGIS-MIOS — Command Line Interface
====================================
Complete CLI supporting ingestion, queries, batch processing, exports, and server execution.
'''

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator
from src.workflows.ingest_workflow import IngestWorkflow
from src.workflows.query_workflow import QueryWorkflow
from src.workflows.export_workflow import ExportWorkflow
from src.workflows.batch_workflow import BatchWorkflow


def get_llm_config() -> dict[str, str]:
    '''Retrieve LLM credentials and provider settings from environment.'''
    return {
        'llm_provider': os.environ.get('LLM_PROVIDER', 'openai'),
        'llm_model': os.environ.get('LLM_MODEL', 'gpt-4o-mini'),
        'llm_api_key': os.environ.get('LLM_API_KEY', ''),
    }


async def run_ingest(filepath: str) -> None:
    '''Ingest a single document and print statistics.'''
    path = Path(filepath)
    if not path.exists():
        print(f'Error: File {filepath} not found.', file=sys.stderr)
        sys.exit(1)

    print(f'Ingesting {path.name}...')
    config = get_llm_config()
    wf = IngestWorkflow(**config)
    await wf.initialize()
    try:
        res = await wf.ingest(path)
        print('Ingestion successful!')
        print(json.dumps(res, indent=2))
        Path('.amdi_last_doc').write_text(res['doc_id'], encoding='utf-8')
    except Exception as e:
        print(f'Ingestion failed: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        await wf.shutdown()


async def run_query(question: str, doc_id: str | None) -> None:
    '''Execute a query against ingested documents.'''
    if not doc_id:
        cache_file = Path('.amdi_last_doc')
        if cache_file.exists():
            doc_id = cache_file.read_text(encoding='utf-8').strip()
            print(f'Using last ingested doc_id: {doc_id}')
        else:
            print('Warning: No doc_id specified and no last document found.', file=sys.stderr)

    # Use the unified orchestrator to run retrieval + reasoning over database state
    orchestrator = AMDIOrchestrator()
    try:
        print(f'Executing query: "{question}"...')
        res = await orchestrator.query(question, doc_id=doc_id)
        print('\n--- Answer ---')
        print(res.get('answer', ''))
        print('\n--- Metadata ---')
        print(f"Confidence: {res.get('confidence', 0.0)} ({res.get('confidence_label', 'MEDIUM')})")
        print(f"Grounded: {res.get('grounded', False)}")
        print(f"Latency: {res.get('latency_ms', 0)} ms")
        print(f"Tokens Used: {res.get('tokens_used', 0)}")
    except Exception as e:
        print(f'Query failed: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        await orchestrator.close()


async def run_batch(directory: str, pattern: str) -> None:
    '''Process multiple documents in a directory in parallel.'''
    config = get_llm_config()
    bw = BatchWorkflow(max_concurrent=4, **config)
    try:
        print(f'Starting batch processing of {directory} matching {pattern}...')
        results = await bw.process_directory(directory, pattern)
        print('Batch processing completed!')
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f'Batch failed: {e}', file=sys.stderr)
        sys.exit(1)


async def run_export(filepath: str, question: str, agent: str) -> None:
    '''Ingest document, run query, and export context packages to agent.'''
    path = Path(filepath)
    if not path.exists():
        print(f'Error: File {filepath} not found.', file=sys.stderr)
        sys.exit(1)

    config = get_llm_config()
    ingest_wf = IngestWorkflow(**config)
    await ingest_wf.initialize()
    try:
        print(f'Ingesting {path.name} for agent export...')
        await ingest_wf.ingest(path)
        query_wf = QueryWorkflow(ingest_wf, **config)
        export_wf = ExportWorkflow(ingest_wf, query_wf)

        print(f'Exporting query "{question}" to agent "{agent}"...')
        res = await export_wf.export(question, agent=agent)
        print('\n--- Export Result ---')
        print(json.dumps(res, indent=2))
    except Exception as e:
        print(f'Export failed: {e}', file=sys.stderr)
        sys.exit(1)
    finally:
        await ingest_wf.shutdown()


def run_serve() -> None:
    '''Start FastAPI production API server.'''
    try:
        import uvicorn
        from src.api.api_server import app
    except ImportError as e:
        print(f'Failed to start server: {e}. Ensure fastapi and uvicorn are installed.', file=sys.stderr)
        sys.exit(1)

    print('Starting AEGIS-MIOS API Server...')
    uvicorn.run(app, host='0.0.0.0', port=8000)


def main() -> None:
    '''Main entry point for CLI command parsing.'''
    parser = argparse.ArgumentParser(description='AEGIS-MIOS CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest a document')
    ingest_parser.add_argument('filepath', type=str, help='Path to document file')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query ingested document')
    query_parser.add_argument('question', type=str, help='Natural language question')
    query_parser.add_argument('--doc-id', type=str, default=None, help='Document ID filter')

    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Batch process a directory of files')
    batch_parser.add_argument('directory', type=str, help='Directory path')
    batch_parser.add_argument('--pattern', type=str, default='*.pdf', help='File glob pattern')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export query context to LLM agent')
    export_parser.add_argument('filepath', type=str, help='Path to document file')
    export_parser.add_argument('question', type=str, help='Query question')
    export_parser.add_argument('agent', type=str, help='Target agent name (e.g. chatgpt, claude, gemini)')

    # Serve command
    subparsers.add_parser('serve', help='Run the API server')

    args = parser.parse_args()

    if args.command == 'ingest':
        asyncio.run(run_ingest(args.filepath))
    elif args.command == 'query':
        asyncio.run(run_query(args.question, args.doc_id))
    elif args.command == 'batch':
        asyncio.run(run_batch(args.directory, args.pattern))
    elif args.command == 'export':
        asyncio.run(run_export(args.filepath, args.question, args.agent))
    elif args.command == 'serve':
        run_serve()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
