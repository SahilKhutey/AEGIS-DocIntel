"""
tests.security.privacy.test_privacy_suite
=========================================
Tests for WP-07.03 Privacy & Sensitive Data Detection Security Gate (PRIV-001 through PRIV-012).
"""

import pytest
from aegis.security.privacy import PrivacyDetector, PrivacyBenchmarkRunner, luhn_checksum


@pytest.fixture
def detector():
    return PrivacyDetector()


def test_priv_001_email_detection_and_masking(detector):
    text = "Please reach out to confidential-lead@aegis-intel.org for access."
    entities = detector.detect(text)
    assert any(e.entity_type == "EMAIL_ADDRESS" for e in entities)
    redacted, summary = detector.redact(text, entities)
    assert "[REDACTED_EMAIL]" in redacted
    assert "confidential-lead@aegis-intel.org" not in redacted
    assert "confidential-lead@aegis-intel.org" not in str(summary)


def test_priv_002_phone_detection(detector):
    text = "Helpline is +1 (800) 555-0199 or 555-123-4567."
    entities = detector.detect(text)
    phones = [e for e in entities if e.entity_type == "PHONE_NUMBER"]
    assert len(phones) >= 1


def test_priv_003_ssn_detection(detector):
    text = "Form 1040 SSN: 000-12-3456."
    entities = detector.detect(text)
    ssns = [e for e in entities if e.entity_type == "SSN"]
    assert len(ssns) == 1
    redacted, _ = detector.redact(text, entities)
    assert "[REDACTED_SSN]" in redacted


def test_priv_004_credit_card_luhn_validation(detector):
    valid_card = "4111 1111 1111 1111"
    invalid_card = "4111 1111 1111 1112"
    assert luhn_checksum(valid_card)
    assert not luhn_checksum(invalid_card)

    entities = detector.detect(f"Card number {valid_card} and bogus {invalid_card}")
    cards = [e for e in entities if e.entity_type == "CREDIT_CARD"]
    assert len(cards) == 1
    assert cards[0].raw_value == valid_card


def test_priv_005_api_key_secret_detection(detector):
    text = "OpenAI key sk-proj-1234567890abcdef12345678 and GitHub ghp_123456789012345678901234567890123456"
    entities = detector.detect(text)
    secrets = [e for e in entities if e.entity_type == "API_KEY"]
    assert len(secrets) >= 1
    redacted, _ = detector.redact(text, entities)
    assert "sk-proj-" not in redacted


def test_priv_006_safe_distractor_no_false_positive(detector):
    text = "Package part PART-123-45-67890 and commit hash e3b0c44298fc1c149afbf4c8996fb92427ae41e4"
    entities = detector.detect(text)
    assert len(entities) == 0


def test_priv_007_table_cell_pii_detection(detector):
    text = "| User | SSN |\n| Alice | 123-45-6789 |"
    entities = detector.detect(text)
    assert any(e.entity_type == "SSN" for e in entities)


def test_priv_008_zero_telemetry_leakage(detector):
    raw_secret = "sk-proj-supersecretkey123456789012"
    text = f"My token is {raw_secret}"
    entities = detector.detect(text)
    _, summary = detector.redact(text, entities)
    assert raw_secret not in str(summary)


def test_priv_009_deterministic_reprocessing(detector):
    text = "Report on Alice (user@example.com, phone 555-555-5555)"
    det1 = detector.detect(text)
    det2 = detector.detect(text)
    assert len(det1) == len(det2)
    assert [e.raw_value for e in det1] == [e.raw_value for e in det2]


def test_priv_010_benchmark_runner_full_suite():
    runner = PrivacyBenchmarkRunner()
    report = runner.run_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 12
    assert report["metrics"]["output_leakage_rate"] == 0.0
    assert report["metrics"]["recall"] >= 0.90
