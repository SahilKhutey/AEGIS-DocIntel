"""Tests for document annotation system (models, store, engine, AI, and endpoints)."""
import os
import sys
from pathlib import Path
from datetime import datetime
import pytest
from fastapi.testclient import TestClient

# Add amdi-os to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "amdi-os"))

from src.annotations.models import (
    Annotation, AnnotationPosition, AnnotationStatus, AnnotationThread, AnnotationType,
)
from src.annotations.store import AnnotationStore
from src.annotations.engine import AnnotationEngine
from src.annotations.ai_assist import AIAnnotationAssistant
from src.engines.geometry.element import GeometricElement, ElementType, BoundingBox


TEST_DB_PATH = "data/test_annotations.db"


@pytest.fixture(scope="function")
def test_store():
    # Setup
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass
    store = AnnotationStore(TEST_DB_PATH)
    yield store
    # Teardown
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


@pytest.fixture(scope="function")
def test_engine(test_store):
    return AnnotationEngine(test_store)


@pytest.fixture(scope="function")
def test_ai(test_engine):
    return AIAnnotationAssistant(test_engine)


def test_models():
    """Test annotation data models serialization and structure."""
    pos = AnnotationPosition(page=2, bbox=(0.1, 0.2, 0.3, 0.4), char_start=5, char_end=15, section="Intro", element_id="el_1")
    pos_dict = pos.to_dict()
    assert pos_dict["page"] == 2
    assert pos_dict["bbox"] == [0.1, 0.2, 0.3, 0.4]
    assert pos_dict["char_start"] == 5
    assert pos_dict["element_id"] == "el_1"

    ann = Annotation(
        doc_id="doc_123",
        user_id="user_test",
        type=AnnotationType.HIGHLIGHT,
        status=AnnotationStatus.ACTIVE,
        position=pos,
        content="Testing content",
        color="#ffffff",
        tags=["important"]
    )
    
    ann_dict = ann.to_dict()
    assert ann_dict["doc_id"] == "doc_123"
    assert ann_dict["type"] == "highlight"
    assert ann_dict["status"] == "active"
    assert ann_dict["content"] == "Testing content"
    assert ann_dict["color"] == "#ffffff"
    assert ann_dict["tags"] == ["important"]
    assert "created_at" in ann_dict


def test_store_crud(test_store):
    """Test SQLite store create, read, update, delete operations."""
    pos = AnnotationPosition(page=1)
    ann = Annotation(
        doc_id="doc_x",
        user_id="alice",
        type=AnnotationType.NOTE,
        position=pos,
        content="A note content",
        tags=["review"]
    )
    
    # Create
    aid = test_store.create_annotation(ann)
    assert aid == ann.id

    # Read
    fetched = test_store.get_annotation(aid)
    assert fetched is not None
    assert fetched.doc_id == "doc_x"
    assert fetched.user_id == "alice"
    assert fetched.content == "A note content"
    assert fetched.tags == ["review"]

    # List & Search
    listed = test_store.list_annotations(doc_id="doc_x")
    assert len(listed) == 1
    assert listed[0].id == aid

    results = test_store.search_annotations(doc_id="doc_x", query="note")
    assert len(results) == 1
    assert results[0].id == aid

    # Update
    updated = test_store.update_annotation(aid, content="Updated note content", tags=["completed"])
    assert updated is True
    
    fetched = test_store.get_annotation(aid)
    assert fetched.content == "Updated note content"
    assert fetched.tags == ["completed"]

    # Soft Delete
    deleted = test_store.delete_annotation(aid, soft=True)
    assert deleted is True
    
    fetched = test_store.get_annotation(aid)
    assert fetched.status == AnnotationStatus.DELETED

    # Hard Delete
    hard_deleted = test_store.delete_annotation(aid, soft=False)
    assert hard_deleted is True
    assert test_store.get_annotation(aid) is None


def test_threads_and_stats(test_store):
    """Test annotation threads and stats in SQLite."""
    ann1 = Annotation(doc_id="doc_y", content="Question 1", type=AnnotationType.QUESTION)
    ann2 = Annotation(doc_id="doc_y", content="Reply 1", type=AnnotationType.COMMENT, parent_id=ann1.id)
    
    test_store.create_annotation(ann1)
    test_store.create_annotation(ann2)

    # Thread creation
    thread = AnnotationThread(doc_id="doc_y", title="Clarification Topic", annotation_ids=[ann1.id])
    tid = test_store.create_thread(thread)
    assert tid == thread.id

    # Add reply
    test_store.add_reply(ann1.id, ann2.id)
    fetched_ann1 = test_store.get_annotation(ann1.id)
    assert ann2.id in fetched_ann1.replies

    # List threads
    threads = test_store.list_threads("doc_y")
    assert len(threads) == 1
    assert threads[0].title == "Clarification Topic"

    # Stats
    stats = test_store.statistics("doc_y")
    assert stats["n_total"] == 2
    assert stats["by_type"]["question"] == 1
    assert stats["by_type"]["comment"] == 1


def test_import_export(test_store):
    """Test importing and exporting annotations to/from JSON."""
    ann1 = Annotation(doc_id="doc_z", content="Note to export", type=AnnotationType.NOTE)
    test_store.create_annotation(ann1)
    
    # Export
    json_str = test_store.export_to_json("doc_z")
    assert "Note to export" in json_str

    # Setup a new clean store
    new_store = AnnotationStore("data/test_import.db")
    try:
        count = new_store.import_from_json(json_str)
        assert count == 1
        imported = new_store.list_annotations("doc_z")
        assert len(imported) == 1
        assert imported[0].content == "Note to export"
    finally:
        if os.path.exists("data/test_import.db"):
            os.remove("data/test_import.db")


def test_engine_operations(test_engine):
    """Test high-level engine business logic methods."""
    doc_id = "doc_eng"
    
    # note
    nid = test_engine.add_note(doc_id, page=1, content="Test note")
    # highlight
    hid = test_engine.highlight(doc_id, page=2, bbox=(0.1, 0.2, 0.3, 0.4), text="high text")
    # correction
    cid = test_engine.add_correction(doc_id, page=1, original_text="bad", corrected_text="good")
    # question
    qid = test_engine.ask_question(doc_id, page=3, question="Why?")
    # tag
    tid = test_engine.tag_element(doc_id, page=1, element_id="el_x", tags=["important"])
    # verify
    vid = test_engine.verify_claim(doc_id, page=1, claim="Claim text", is_correct=True)
    # rate
    rid = test_engine.rate_element(doc_id, page=2, element_id="el_y", rating=4, comment="Nice")
    # bookmark
    bid = test_engine.bookmark(doc_id, page=5, label="Bookmarks")

    # Fetch and verify types
    assert test_engine.store.get_annotation(nid).type == AnnotationType.NOTE
    assert test_engine.store.get_annotation(hid).type == AnnotationType.HIGHLIGHT
    assert test_engine.store.get_annotation(cid).type == AnnotationType.CORRECTION
    assert test_engine.store.get_annotation(qid).type == AnnotationType.QUESTION
    assert test_engine.store.get_annotation(tid).type == AnnotationType.TAG
    assert test_engine.store.get_annotation(vid).type == AnnotationType.VERIFICATION
    assert test_engine.store.get_annotation(rid).type == AnnotationType.RATING
    assert test_engine.store.get_annotation(bid).type == AnnotationType.BOOKMARK

    # Threading
    thread_id = test_engine.start_thread(doc_id, "Discussion", qid)
    assert thread_id is not None
    
    reply_id = test_engine.add_note(doc_id, page=3, content="Reply content", parent_id=qid)
    success = test_engine.reply_to_thread(thread_id, reply_id)
    assert success is True


def test_ai_assistance(test_ai):
    """Test AI pattern matching and suggestions engine."""
    elements = [
        GeometricElement(
            element_id="el1", page=1, content="We reached revenue of $1,250,000 this year with contract terms.",
            type=ElementType.TEXT, bbox=BoundingBox(0, 0, 1, 1)
        ),
        GeometricElement(
            element_id="el2", page=2, content="The experiment shows roughly 25% growth, which might be correct.",
            type=ElementType.TEXT, bbox=BoundingBox(0, 0, 1, 1)
        ),
        GeometricElement(
            element_id="el3", page=2, content="TODO check magnitude discrepancy: 10.5M versus $15B.",
            type=ElementType.TEXT, bbox=BoundingBox(0, 0, 1, 1)
        )
    ]

    # auto-tagging
    tags_created = test_ai.auto_tag("doc_ai", elements)
    assert len(tags_created) > 0
    # verify tags created
    ann_tags = test_ai.engine.store.list_annotations("doc_ai", type=AnnotationType.TAG)
    assert len(ann_tags) > 0

    # numerical claims
    claims_flagged = test_ai.verify_numerical_claims("doc_ai", elements)
    assert len(claims_flagged) > 0

    # suggest questions
    questions_suggested = test_ai.suggest_questions("doc_ai", elements)
    assert len(questions_suggested) > 0

    # magnitude inconsistencies
    inconsistencies_flagged = test_ai.detect_inconsistencies("doc_ai", elements)
    assert len(inconsistencies_flagged) > 0


def test_api_endpoints():
    """Test FastAPI endpoint handlers using TestClient."""
    from src.api.api_server import app
    client = TestClient(app)

    # 1. Create note
    payload = {
        "doc_id": "api_doc_1",
        "type": "note",
        "position": {
            "page": 1,
            "bbox": [0.1, 0.2, 0.3, 0.4]
        },
        "content": "API created note content",
        "color": "#ff0000",
        "tags": ["api-test"]
    }
    
    response = client.post("/v1/annotations/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "created"
    aid = data["id"]

    # 2. Get annotation
    response = client.get(f"/v1/annotations/{aid}")
    assert response.status_code == 200
    ann_data = response.json()
    assert ann_data["content"] == "API created note content"
    assert ann_data["color"] == "#ff0000"

    # 3. List annotations
    response = client.get("/v1/annotations/?doc_id=api_doc_1")
    assert response.status_code == 200
    listed_data = response.json()
    assert listed_data["count"] == 1
    assert listed_data["annotations"][0]["id"] == aid

    # 4. Search annotations
    response = client.get("/v1/annotations/search/?doc_id=api_doc_1&q=created")
    assert response.status_code == 200
    search_data = response.json()
    assert search_data["count"] == 1

    # 5. Update
    response = client.patch(f"/v1/annotations/{aid}", json={"content": "Modified API note content"})
    assert response.status_code == 200
    assert response.json()["status"] == "updated"

    # 6. Resolve
    response = client.post(f"/v1/annotations/{aid}/resolve")
    assert response.status_code == 200
    assert response.json()["status"] == "resolved"

    # 7. Delete
    response = client.delete(f"/v1/annotations/{aid}")
    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
