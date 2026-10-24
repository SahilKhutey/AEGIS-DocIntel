"""
evaluation/scripts/evaluate_privacy.py
======================================
Evaluates PII redaction and privacy compliance:
- Precision, Recall, and F1 on labeled synthetic PII corpus
- 0% downstream leakage rate for high-risk secrets
- Safe aggregate telemetry verification
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aegis_docprep.pii_redaction import (
    PIIRedactionPolicyError,
    detect_pii,
    redact_or_block,
)


def evaluate_privacy(dataset_path: Path | str | None = None) -> Dict[str, Any]:
    if dataset_path is None:
        dataset_path = Path(__file__).resolve().parent.parent / "datasets" / "qa_eval_dataset.json"
    else:
        dataset_path = Path(dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    privacy_cases = data.get("privacy_cases", [])
    tp = 0
    fp = 0
    fn = 0
    leaked_secrets = 0
    total_expected = 0

    for case in privacy_cases:
        text = case["text"]
        expected_items = case["expected_pii"]
        distractors = case.get("safe_distractors", [])
        total_expected += len(expected_items)

        redacted_text, report = redact_or_block(text, mandatory=True)

        # Check safe summary does not leak raw secrets
        summary = report.safe_summary()
        summary_str = str(summary)
        for exp in expected_items:
            secret = exp["entity"]
            assert secret not in summary_str, f"Secret '{secret}' leaked in telemetry summary!"

            # Check leakage in redacted text
            if secret in redacted_text:
                leaked_secrets += 1

        # Check detection against expected entities
        detected_spans = {m.text for m in report.entities_found}

        for exp in expected_items:
            # Check if expected entity was detected (exact or substring)
            if any(exp["entity"] in span or span in exp["entity"] for span in detected_spans):
                tp += 1
            else:
                fn += 1

        # Check if safe distractors were falsely flagged as PII
        for dist in distractors:
            if any(dist == span for span in detected_spans):
                fp += 1

    precision = tp / max(1, tp + fp)
    recall = tp / max(1, total_expected)
    f1 = (2 * precision * recall) / max(1e-6, precision + recall)
    leakage_rate = leaked_secrets / max(1, total_expected)

    # Fail-closed enforcement check
    blocked_successfully = False
    try:
        # Mocking or testing mandatory failure block
        class FailingText:
            def __str__(self) -> str:
                raise RuntimeError("Catastrophic regex failure")
        redact_or_block(FailingText(), mandatory=True)  # type: ignore[arg-type]
    except PIIRedactionPolicyError:
        blocked_successfully = True

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "leakage_rate": round(leakage_rate, 4),
        "fail_closed_blocked": blocked_successfully,
        "cases_evaluated": len(privacy_cases),
        "passed": (precision >= 0.85 and recall >= 0.85 and leakage_rate == 0.0 and blocked_successfully),
    }


if __name__ == "__main__":
    results = evaluate_privacy()
    print(json.dumps(results, indent=2))
