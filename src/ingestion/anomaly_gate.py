'''
AEGIS-DocIntel / AMDI-OS — Ingestion Anomaly & Adversarial Gate
================================================================
Evaluates statistical outliers and prompt-injection adversarial content before downstream engines execute.
'''
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AnomalyFlag:
    flag_type: str  # "statistical_outlier" | "injection_suspected" | "structural_malformation"
    score: float
    evidence: str
    element_id: Optional[str] = None


@dataclass
class IngestionGateResult:
    document_id: str
    flags: List[AnomalyFlag] = field(default_factory=list)
    action: str = "pass"  # "pass" | "quarantine" | "reject"


INJECTION_PATTERNS = [
    re.compile(r'ignore\s+previous\s+instructions', re.IGNORECASE),
    re.compile(r'you\s+are\s+now\s+in\s+developer\s+mode', re.IGNORECASE),
    re.compile(r'system\s+prompt\s+override', re.IGNORECASE),
]


def scan_for_injection_patterns(elements: List[Dict[str, Any]]) -> List[AnomalyFlag]:
    '''Scans element content for known prompt-injection attack payloads.'''
    flags = []
    for elem in elements:
        text = str(elem.get('text', elem.get('content', '')))
        elem_id = str(elem.get('id', 'elem_0'))
        for pat in INJECTION_PATTERNS:
            if pat.search(text):
                flags.append(
                    AnomalyFlag(
                        flag_type='injection_suspected',
                        score=0.99,
                        evidence=f"Matched adversarial pattern: '{pat.pattern}'",
                        element_id=elem_id,
                    )
                )
    return flags


def detect_statistical_outliers(document: Dict[str, Any]) -> Optional[AnomalyFlag]:
    '''Detects statistical anomaly outliers (e.g. extreme element count or missing content).'''
    elements = document.get('elements', [])
    elem_count = len(elements)
    if elem_count > 10000 or (elem_count == 0 and document.get('pages', 1) > 0):
        return AnomalyFlag(
            flag_type='statistical_outlier',
            score=0.92,
            evidence=f"Extreme element count: {elem_count}",
        )
    return None


def run_ingestion_gate(document: Dict[str, Any]) -> IngestionGateResult:
    '''Combines statistical outlier and adversarial prompt-injection checks into pass/quarantine/reject decision.'''
    doc_id = str(document.get('id', 'doc_0'))
    elements = document.get('elements', [])

    flags = scan_for_injection_patterns(elements)
    outlier = detect_statistical_outliers(document)
    if outlier is not None:
        flags.append(outlier)

    action = "pass"
    if any(f.flag_type == 'injection_suspected' for f in flags):
        action = "reject"
    elif any(f.flag_type == 'statistical_outlier' for f in flags):
        action = "quarantine"

    return IngestionGateResult(
        document_id=doc_id,
        flags=flags,
        action=action,
    )
