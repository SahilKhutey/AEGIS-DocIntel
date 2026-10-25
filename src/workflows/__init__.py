'''
AMDI-OS Workflows — Pipeline Compatibility Layer.

DEPRECATION NOTICE:
The standalone workflow classes in this package (IngestWorkflow, QueryWorkflow,
ExportWorkflow, BatchWorkflow) are maintained as backward-compatibility pipeline
wrappers.

The canonical, production-grade end-to-end pipeline entry point is
`AMDIOrchestrator` located in `src.core.orchestrator`, which wires together
the 16 mathematical engines, storage persistence, caching, and hybrid retrieval.
'''

from __future__ import annotations

from src.workflows.ingest_workflow import IngestWorkflow
from src.workflows.query_workflow import QueryWorkflow
from src.workflows.export_workflow import ExportWorkflow
from src.workflows.batch_workflow import BatchWorkflow

__all__ = ['IngestWorkflow', 'QueryWorkflow', 'ExportWorkflow', 'BatchWorkflow']
