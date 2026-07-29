"""
Regression test for the text/content key-mismatch bug in
src.compliance.redaction_engine.apply_redaction_policy(), fixed alongside
the Luhn checksum and process-stable tokenization fixes in the same
session.

Why this needs its own test file rather than relying on
tests/test_compliance_redaction.py's existing coverage: that file's tests
(test_redact_geometric_elements, test_orchestrator_ingest_with_pii_redaction)
exclusively pass GeometricElement *objects* through redact_elements(). Per
redact_elements()'s own dispatch logic, the object branch always builds an
intermediate dict keyed 'text' (via elem_dict = {'text': getattr(elem,
'content', ''), ...}) before calling apply_redaction_policy() -- meaning
that branch could never have exercised the bug, structurally, regardless
of whether apply_redaction_policy() itself was correct. The bug lived
exclusively in the *other* branch: a plain dict passed directly, keyed
only 'content' with no 'text' key -- which is exactly the shape every
element in a real HTTP request body takes (the /v1/advanced/compliance/
redact endpoint's Pydantic request model deserializes JSON directly into
plain dicts, never into GeometricElement objects). No existing test in
this codebase exercised that specific branch with a content-only element
before this file.

The bug itself: apply_redaction_policy() read source text via
elem_copy.get('text', '') with no fallback to 'content', while
detect_pii() (which every caller runs first to produce the entities list)
already read via element.get('text', element.get('content', '')). For a
content-only element, detect_pii() correctly found the PII, but
apply_redaction_policy() then read an empty string, matched nothing,
appended a spurious empty 'text' key, and left 'content' -- the field a
real caller reads back -- completely unredacted, while still reporting a
nonzero redactions_applied count. A response that confidently claims
sensitive data was redacted while the actual field a caller reads back
still contains it in full is a worse failure mode than an obvious crash.
"""
from __future__ import annotations

from src.compliance.redaction_engine import (
    RedactionPolicy,
    apply_redaction_policy,
    detect_pii,
    redact_elements,
)


def test_content_only_dict_element_is_actually_redacted_in_content_field():
    """The direct reproduction of the original bug: a plain dict keyed
    only 'content' (no 'text' key at all) must have its PII actually
    removed from the 'content' field itself -- not merely detected."""
    element = {"element_id": "e1", "content": "Patient SSN is 123-45-6789 on file."}

    entities = detect_pii(element)
    assert len(entities) == 1, "Sanity check: detect_pii must find the SSN first."

    redacted, report = apply_redaction_policy(
        element, entities, [RedactionPolicy("US_SSN", "redact")]
    )

    assert "123-45-6789" not in redacted["content"], (
        "The SSN is still present in 'content' -- the field a real API "
        "caller reads back -- even though redaction was reported as applied."
    )
    assert report.redactions_applied == 1


def test_reported_redaction_count_matches_actual_content_mutation():
    """The specific false-claim failure mode: redactions_applied must
    never be nonzero while the actual readable field is unchanged. This
    test would have failed against the pre-fix code (redactions_applied=1,
    content unmodified) and must pass now."""
    element = {"element_id": "e1", "content": "Call 555-123-4567 for support."}
    entities = detect_pii(element)

    original_content = element["content"]
    redacted, report = apply_redaction_policy(
        element, entities, [RedactionPolicy("PHONE_NUMBER", "redact")]
    )

    if report.redactions_applied > 0:
        assert redacted["content"] != original_content, (
            "redactions_applied is nonzero but 'content' was never actually "
            "modified -- exactly the silent-false-claim bug this test guards "
            "against."
        )


def test_end_to_end_redact_elements_with_plain_dict_matching_api_request_shape():
    """Exercises the actual public entry point (redact_elements) with an
    element shaped exactly as the HTTP API's Pydantic model would produce
    it from a JSON request body -- a plain dict, content-keyed, no
    GeometricElement involved anywhere in the call chain."""
    elements = [{"element_id": "e1", "content": "SSN: 987-65-4321 confirmed."}]

    redacted_elements, report = redact_elements(
        elements, policies=[RedactionPolicy("US_SSN", "redact")]
    )

    assert report.redactions_applied == 1
    assert "987-65-4321" not in redacted_elements[0]["content"]


def test_element_with_both_text_and_content_keys_updates_both():
    """An element that happens to carry both keys (a caller migrating
    between conventions, or a dict built from mixed sources) must have
    both updated consistently -- not just whichever key the function
    happened to read from, leaving the other stale and inconsistent."""
    element = {
        "element_id": "e1",
        "text": "Contact SSN 111-22-3333 today.",
        "content": "Contact SSN 111-22-3333 today.",
    }
    entities = detect_pii(element)

    redacted, report = apply_redaction_policy(
        element, entities, [RedactionPolicy("US_SSN", "redact")]
    )

    assert "111-22-3333" not in redacted["text"]
    assert "111-22-3333" not in redacted["content"]
    assert redacted["text"] == redacted["content"], (
        "Both keys were present but ended up with different (inconsistent) "
        "redacted content."
    )


def test_geometric_element_path_is_unaffected_by_this_fix():
    """Regression guard in the other direction: the GeometricElement
    object branch (which was never actually broken -- see this file's
    module docstring) must continue to work exactly as before."""
    from src.engines.geometry.element import GeometricElement

    el = GeometricElement(
        element_id="e1", doc_id="d1", content="SSN 444-55-6666 on record.",
    )
    redacted_elements, report = redact_elements(
        [el], policies=[RedactionPolicy("US_SSN", "redact")]
    )

    assert report.redactions_applied == 1
    assert "444-55-6666" not in redacted_elements[0].content
