"""
tests/corpus/test_adapters.py
=============================
Tests ADP-001 through ADP-010 verifying dataset adapters, schema normalization,
robustness, and registry auto-detection.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.corpus.adapters import (
    AdapterRegistry,
    BoundingBoxItem,
    CanonicalAnnotation,
    CanonicalDocument,
    CanonicalEvaluationItem,
    CORDAdapter,
    CustomJSONAdapter,
    DatasetAdapter,
    DocVQAAdapter,
    FUNSDAdapter,
    GenericPDFAdapter,
    PubLayNetAdapter,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas" / "corpus"


@pytest.fixture
def schemas():
    with open(SCHEMAS_DIR / "document.schema.json", "r", encoding="utf-8") as f:
        doc_schema = json.load(f)
    with open(SCHEMAS_DIR / "annotation.schema.json", "r", encoding="utf-8") as f:
        anno_schema = json.load(f)
    with open(SCHEMAS_DIR / "evaluation_item.schema.json", "r", encoding="utf-8") as f:
        eval_schema = json.load(f)
    return {
        "document": doc_schema,
        "annotation": anno_schema,
        "evaluation_item": eval_schema,
    }


def test_adp_001_protocol_compliance():
    """Verify that all adapters inherit from DatasetAdapter and satisfy required properties."""
    adapters = [
        DocVQAAdapter(),
        FUNSDAdapter(),
        CORDAdapter(),
        PubLayNetAdapter(),
        GenericPDFAdapter(),
        CustomJSONAdapter(),
    ]
    for adapter in adapters:
        assert isinstance(adapter, DatasetAdapter)
        assert len(adapter.adapter_name) > 0
        assert len(adapter.supported_formats) > 0
        meta = adapter.get_metadata()
        assert meta["adapter_name"] == adapter.adapter_name
        assert "supported_formats" in meta


def test_adp_002_docvqa_adapter_conversion(tmp_path, schemas):
    """Test DocVQAAdapter correctly parses DocVQA json into canonical records."""
    docvqa_data = {
        "dataset_name": "docvqa",
        "data": [
            {
                "questionId": 1001,
                "question": "What is the document date?",
                "image": "documents/doc_1001.png",
                "docId": "doc_1001",
                "ucsf_document_id": "rnbx0001",
                "answers": ["January 15, 1999", "Jan 15, 1999"],
                "ocr_tokens": ["Date:", "January", "15,", "1999"],
                "ocr_boxes": [[10, 10, 40, 20], [45, 10, 85, 20], [90, 10, 110, 20], [115, 10, 150, 20]],
            }
        ]
    }
    sample_file = tmp_path / "docvqa_sample.json"
    sample_file.write_text(json.dumps(docvqa_data), encoding="utf-8")

    adapter = DocVQAAdapter()
    assert adapter.validate_source(sample_file) is True

    docs, annos, evals, report = adapter.convert(sample_file)
    assert report.success is True
    assert len(docs) == 1
    assert len(annos) == 1
    assert len(evals) == 1

    doc = docs[0]
    assert doc.document_id == "DOCVQA_RNBX0001"
    assert doc.source_id == "SRC-DOCVQA"
    assert doc.rights.status == "CONDITIONAL"

    anno = annos[0]
    assert anno.task == "question_answering"
    assert len(anno.bounding_boxes) == 4

    item = evals[0]
    assert item.task == "question_answering"
    assert item.input["question"] == "What is the document date?"

    # Verify against schemas
    jsonschema.validate(doc.to_schema_dict(), schemas["document"])
    jsonschema.validate(anno.to_schema_dict(), schemas["annotation"])
    jsonschema.validate(item.to_schema_dict(), schemas["evaluation_item"])


def test_adp_003_funsd_adapter_conversion(tmp_path, schemas):
    """Test FUNSDAdapter parses form understanding structure into canonical records."""
    funsd_data = {
        "form": [
            {
                "id": 0,
                "text": "Name:",
                "box": [50, 50, 90, 70],
                "label": "question",
                "linking": [[0, 1]],
            },
            {
                "id": 1,
                "text": "John Doe",
                "box": [95, 50, 180, 70],
                "label": "answer",
                "linking": [[0, 1]],
            }
        ]
    }
    sample_file = tmp_path / "0001.json"
    sample_file.write_text(json.dumps(funsd_data), encoding="utf-8")

    adapter = FUNSDAdapter()
    assert adapter.validate_source(sample_file) is True

    docs, annos, evals, report = adapter.convert(sample_file)
    assert report.success is True
    assert len(docs) == 1
    assert len(annos) == 1
    assert len(evals) == 1

    doc = docs[0]
    assert doc.source_id == "SRC-FUNSD"
    assert doc.rights.licence_id == "LIC-FUNSD-ACAD-001"

    anno = annos[0]
    assert anno.task == "entity_extraction"
    assert len(anno.bounding_boxes) == 2

    jsonschema.validate(doc.to_schema_dict(), schemas["document"])
    jsonschema.validate(anno.to_schema_dict(), schemas["annotation"])
    jsonschema.validate(evals[0].to_schema_dict(), schemas["evaluation_item"])


def test_adp_004_cord_adapter_conversion(tmp_path, schemas):
    """Test CORDAdapter parses receipt lines and quad boxes into canonical bounding boxes."""
    cord_data = {
        "valid_line": [
            {
                "category": "menu.nm",
                "words": [
                    {
                        "text": "ESPRESSO",
                        "quad": {"x1": 10, "y1": 20, "x2": 60, "y2": 20, "x3": 60, "y3": 35, "x4": 10, "y4": 35}
                    }
                ]
            },
            {
                "category": "total.total_price",
                "words": [
                    {
                        "text": "$3.50",
                        "quad": {"x1": 150, "y1": 100, "x2": 190, "y2": 100, "x3": 190, "y3": 115, "x4": 150, "y4": 115}
                    }
                ]
            }
        ]
    }
    sample_file = tmp_path / "receipt_01.json"
    sample_file.write_text(json.dumps(cord_data), encoding="utf-8")

    adapter = CORDAdapter()
    assert adapter.validate_source(sample_file) is True

    docs, annos, evals, report = adapter.convert(sample_file)
    assert report.success is True
    assert len(docs) == 1
    assert len(annos) == 1
    assert len(evals) == 1

    anno = annos[0]
    assert len(anno.bounding_boxes) == 2
    assert anno.bounding_boxes[0].bbox == [10.0, 20.0, 60.0, 35.0]

    jsonschema.validate(docs[0].to_schema_dict(), schemas["document"])
    jsonschema.validate(anno.to_schema_dict(), schemas["annotation"])
    jsonschema.validate(evals[0].to_schema_dict(), schemas["evaluation_item"])


def test_adp_005_publaynet_adapter_conversion(tmp_path, schemas):
    """Test PubLayNetAdapter converts COCO layout annotations to canonical schema."""
    coco_data = {
        "images": [
            {"id": 501, "file_name": "paper_page_01.jpg", "width": 600, "height": 800}
        ],
        "annotations": [
            {"id": 1, "image_id": 501, "category_id": 2, "bbox": [50, 40, 500, 30]},
            {"id": 2, "image_id": 501, "category_id": 1, "bbox": [50, 80, 240, 200]},
            {"id": 3, "image_id": 501, "category_id": 4, "bbox": [300, 80, 250, 150]},
        ],
        "categories": [
            {"id": 1, "name": "text"},
            {"id": 2, "name": "title"},
            {"id": 3, "name": "list"},
            {"id": 4, "name": "table"},
            {"id": 5, "name": "figure"},
        ]
    }
    sample_file = tmp_path / "publaynet_coco.json"
    sample_file.write_text(json.dumps(coco_data), encoding="utf-8")

    adapter = PubLayNetAdapter()
    assert adapter.validate_source(sample_file) is True

    docs, annos, evals, report = adapter.convert(sample_file)
    assert report.success is True
    assert len(docs) == 1
    assert len(annos) == 1

    anno = annos[0]
    assert anno.task == "layout_detection"
    assert len(anno.bounding_boxes) == 3
    # Check bbox converted from [x, y, w, h] to [x0, y0, x0+w, y0+h]
    assert anno.bounding_boxes[0].bbox == [50.0, 40.0, 550.0, 70.0]
    assert anno.bounding_boxes[0].category == "title"

    jsonschema.validate(docs[0].to_schema_dict(), schemas["document"])
    jsonschema.validate(anno.to_schema_dict(), schemas["annotation"])
    jsonschema.validate(evals[0].to_schema_dict(), schemas["evaluation_item"])


def test_adp_006_generic_pdf_adapter(schemas):
    """Test GenericPDFAdapter with real workspace PDF files."""
    fixtures_dir = REPO_ROOT / "tests" / "fixtures"
    pdf_file = fixtures_dir / "sample.pdf"
    if not pdf_file.exists():
        pytest.skip("sample.pdf not found in tests/fixtures")

    adapter = GenericPDFAdapter()
    assert adapter.validate_source(pdf_file) is True

    docs, annos, evals, report = adapter.convert(pdf_file)
    assert report.success is True
    assert len(docs) == 1
    assert len(annos) == 1
    assert len(evals) == 1

    doc = docs[0]
    assert doc.content.format == "application/pdf"
    assert len(doc.content.sha256) == 64
    assert doc.metadata.page_count >= 1

    jsonschema.validate(doc.to_schema_dict(), schemas["document"])
    jsonschema.validate(annos[0].to_schema_dict(), schemas["annotation"])
    jsonschema.validate(evals[0].to_schema_dict(), schemas["evaluation_item"])


def test_adp_007_custom_json_adapter(tmp_path, schemas):
    """Test CustomJSONAdapter parsing native canonical JSON format."""
    native_data = [
        {
            "document_id": "CUSTOM_DOC_001",
            "source_id": "SRC-SEC-EDGAR",
            "dataset_id": "SEC_10K",
            "content": {
                "uri": "sec/filing_001.pdf",
                "format": "application/pdf",
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "size_bytes": 10240,
            },
            "metadata": {
                "title": "SEC 10-K Filing",
                "document_type": "regulatory_filing",
                "language": ["en"],
                "page_count": 45,
            },
            "rights": {
                "licence_id": "LIC-USGOV-PD-001",
                "status": "APPROVED",
                "attribution_required": False,
            },
            "annotations": [
                {
                    "annotation_id": "ANNO-CUSTOM-001",
                    "document_id": "CUSTOM_DOC_001",
                    "task": "citation_validation",
                    "labels": {"section": "Item 1A Risk Factors"},
                    "bounding_boxes": [{"page": 3, "bbox": [10.0, 20.0, 300.0, 40.0], "category": "heading"}],
                    "evidence_spans": [{"page": 3, "chunk_id": "c1", "text": "Cybersecurity risks"}],
                }
            ],
            "evaluations": [
                {
                    "item_id": "EVAL-CUSTOM-001",
                    "document_id": "CUSTOM_DOC_001",
                    "task": "citation_validation",
                    "input": {"query": "Find cybersecurity risk section"},
                    "ground_truth": {"page": 3, "chunk_id": "c1"},
                }
            ]
        }
    ]
    sample_file = tmp_path / "custom_sec.json"
    sample_file.write_text(json.dumps(native_data), encoding="utf-8")

    adapter = CustomJSONAdapter()
    assert adapter.validate_source(sample_file) is True

    docs, annos, evals, report = adapter.convert(sample_file)
    assert report.success is True
    assert len(docs) == 1
    assert len(annos) == 1
    assert len(evals) == 1

    jsonschema.validate(docs[0].to_schema_dict(), schemas["document"])
    jsonschema.validate(annos[0].to_schema_dict(), schemas["annotation"])
    jsonschema.validate(evals[0].to_schema_dict(), schemas["evaluation_item"])


def test_adp_008_adapter_registry_resolution(tmp_path):
    """Test registry lookup and automatic format detection."""
    assert AdapterRegistry.get_adapter("docvqa") is not None
    assert AdapterRegistry.get_adapter("FUNSD") is not None
    assert AdapterRegistry.get_adapter("publaynet") is not None
    assert AdapterRegistry.get_adapter("nonexistent") is None

    # Auto-detection on DocVQA sample
    docvqa_sample = tmp_path / "detect_docvqa.json"
    docvqa_sample.write_text(json.dumps({"dataset_name": "docvqa", "data": []}), encoding="utf-8")
    detected = AdapterRegistry.detect_adapter(docvqa_sample)
    assert detected is not None
    assert detected.adapter_name == "DocVQA"

    # Auto-detection on FUNSD sample
    funsd_sample = tmp_path / "detect_funsd.json"
    funsd_sample.write_text(json.dumps({"form": [{"id": 0, "box": [0, 0, 10, 10]}]}), encoding="utf-8")
    detected = AdapterRegistry.detect_adapter(funsd_sample)
    assert detected is not None
    assert detected.adapter_name == "FUNSD"


def test_adp_009_coordinate_normalization_and_bbox():
    """Verify BoundingBoxItem coordinate representation and validation."""
    bbox = BoundingBoxItem(page=1, bbox=[10.5, 20.0, 150.0, 80.0], category="header")
    assert bbox.bbox == [10.5, 20.0, 150.0, 80.0]
    assert bbox.page == 1

    with pytest.raises(Exception):
        # Invalid bbox length (3 items instead of 4)
        BoundingBoxItem(page=1, bbox=[10.0, 20.0, 30.0], category="error")


def test_adp_010_schema_conformance_validation(schemas):
    """Test that CanonicalDocument, CanonicalAnnotation, and CanonicalEvaluationItem validate cleanly against JSON schema."""
    doc = CanonicalDocument(
        document_id="WB_DEV_REPORT_2023",
        source_id="SRC-WORLD-BANK",
        dataset_id="WORLD_BANK_REPORTS",
        content={
            "uri": "reports/wb_2023.pdf",
            "format": "application/pdf",
            "sha256": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "size_bytes": 5000000,
        },
        metadata={
            "title": "World Development Report 2023",
            "document_type": "development_report",
            "language": ["en"],
            "page_count": 320,
        },
        rights={
            "licence_id": "LIC-CC-BY-4-001",
            "status": "APPROVED",
            "attribution_required": True,
            "attribution_text": "World Bank Group CC-BY 4.0",
        }
    )
    jsonschema.validate(doc.to_schema_dict(), schemas["document"])

    anno = CanonicalAnnotation(
        annotation_id="ANNO-WB-001",
        document_id="WB_DEV_REPORT_2023",
        task="table_extraction",
        labels={"table_type": "statistical_indicators"},
        bounding_boxes=[BoundingBoxItem(page=15, bbox=[50.0, 100.0, 550.0, 700.0], category="table")],
    )
    jsonschema.validate(anno.to_schema_dict(), schemas["annotation"])

    item = CanonicalEvaluationItem(
        item_id="EVAL-WB-001",
        document_id="WB_DEV_REPORT_2023",
        task="table_extraction",
        input={"page": 15, "query": "Extract table: remittance flows"},
        ground_truth={"table_rows": 24, "table_cols": 6},
    )
    jsonschema.validate(item.to_schema_dict(), schemas["evaluation_item"])
