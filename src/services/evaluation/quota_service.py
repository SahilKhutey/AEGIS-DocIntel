"""
AEGIS-DocIntel Evaluation Quota Service (PROT-FINAL-02 / REM-04)
Centralized capacity reservation, transactional settlement, rollback,
and usage accounting for evaluation workloads.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from services.evaluation_gateway.quotas import (
    quota_manager as gateway_quota_manager,
    QuotaManager,
    QuotaExceededError,
)
from src.services.evaluation.quota_reservation_service import (
    QuotaReservationService,
    default_quota_reservation_service,
)
from src.services.evaluation.quota_settlement_service import (
    QuotaSettlementService,
    default_quota_settlement_service,
)
from src.services.evaluation.quota_reconciliation_service import (
    QuotaReconciliationService,
    default_quota_reconciliation_service,
)


class EvaluationQuotaService:
    def __init__(
        self,
        manager: Optional[QuotaManager] = None,
        reservation_service: Optional[QuotaReservationService] = None,
        settlement_service: Optional[QuotaSettlementService] = None,
        reconciliation_service: Optional[QuotaReconciliationService] = None,
    ):
        self._manager = manager or gateway_quota_manager
        self._res_service = reservation_service or default_quota_reservation_service
        self._settle_service = settlement_service or default_quota_settlement_service
        self._recon_service = reconciliation_service or default_quota_reconciliation_service

    def reserve_quota(
        self,
        license_id: str,
        metric: str,
        amount: int = 1,
        max_limit: Optional[int] = None,
        reservation_id: Optional[str] = None,
    ) -> str:
        return self._manager.reserve_quota(
            license_id=license_id,
            metric=metric,
            amount=amount,
            max_limit=max_limit,
            reservation_id=reservation_id,
        )

    def settle_quota(
        self,
        license_id: str,
        reservation_id: str,
        actual_amount: Optional[int] = None,
    ) -> None:
        self._manager.settle_reservation(
            license_id=license_id,
            reservation_id=reservation_id,
            actual_amount=actual_amount,
        )

    def rollback_quota(self, license_id: str, reservation_id: str) -> None:
        self._manager.rollback_reservation(license_id, reservation_id)

    def record_document_upload(
        self,
        license_id: str,
        doc_id: str,
        file_size_bytes: int,
        max_limit: Optional[int] = None,
    ) -> None:
        self._manager.record_document_upload(license_id, doc_id, file_size_bytes, max_limit)

    def record_query(self, license_id: str, max_limit: Optional[int] = None) -> int:
        return self._manager.record_query(license_id, max_limit)

    def record_comparison(self, license_id: str, max_limit: Optional[int] = None) -> int:
        return self._manager.record_comparison(license_id, max_limit)

    def get_quota_status(self, license_id: str, quotas: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        return self._manager.get_quota_status(license_id, quotas)

    def reset_usage(self, license_id: str) -> None:
        self._manager.reset_usage(license_id)


quota_service = EvaluationQuotaService()
default_evaluation_quota_service = quota_service
