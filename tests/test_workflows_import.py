"""
AEGIS-DocIntel — Workflows Package Import Regression Test
==========================================================
Verifies that importing src.workflows imports all four primary workflows
(IngestWorkflow, BatchWorkflow, QueryWorkflow, ExportWorkflow) without errors.
This prevents regressions where individual engine tests pass while the unified
workflow orchestration layer cannot be imported.
"""
from __future__ import annotations

import pytest


def test_all_workflows_import_cleanly_from_package():
    """Verify package-level import of all four workflows."""
    import src.workflows as workflows
    from src.workflows import (
        BatchWorkflow,
        ExportWorkflow,
        IngestWorkflow,
        QueryWorkflow,
    )

    assert IngestWorkflow is not None
    assert BatchWorkflow is not None
    assert QueryWorkflow is not None
    assert ExportWorkflow is not None

    assert hasattr(workflows, "IngestWorkflow")
    assert hasattr(workflows, "BatchWorkflow")
    assert hasattr(workflows, "QueryWorkflow")
    assert hasattr(workflows, "ExportWorkflow")


def test_workflow_classes_instantiable():
    """Verify that workflow classes can be instantiated cleanly with mock configurations."""
    from src.workflows import (
        BatchWorkflow,
        ExportWorkflow,
        IngestWorkflow,
        QueryWorkflow,
    )

    ingest = IngestWorkflow(llm_provider="mock")
    assert ingest is not None
    assert hasattr(ingest, "graph_engine")
    assert hasattr(ingest, "graph_builder")

    batch = BatchWorkflow(ingest_workflow=ingest)
    assert batch is not None

    query = QueryWorkflow(ingest_workflow=ingest, llm_provider="mock")
    assert query is not None

    export = ExportWorkflow(ingest=ingest, query=query)
    assert export is not None
    assert hasattr(export, "verifier")
    assert len(export.list_agents()) > 0
