import { submitReviewDecision } from "./decision.api";
import type { ConflictResolutionInput } from "../schemas/conflict.schema";
import type { ReviewItem, DecisionSubmission } from "../types";

export interface ResolveConflictParams {
  reviewItem: ReviewItem;
  conflictInput: ConflictResolutionInput;
  idempotencyKey?: string;
}

export async function submitConflictResolutionAsDecision(params: ResolveConflictParams) {
  const { reviewItem, conflictInput, idempotencyKey } = params;

  let action: DecisionSubmission["action"] = "approve";
  let correctedValue: string | number | boolean | undefined;
  const quote = conflictInput.reconciled_evidence_quote;

  switch (conflictInput.outcome) {
    case "accepted_first_fact":
      action = "approve";
      break;
    case "accepted_second_fact":
      action = "correct";
      correctedValue = conflictInput.reconciled_value;
      break;
    case "both_valid":
      action = "correct";
      correctedValue = conflictInput.reconciled_value;
      break;
    case "insufficient_evidence":
      action = "request_evidence";
      break;
    case "escalated":
      action = "reject";
      break;
  }

  const payload: DecisionSubmission = {
    action,
    expected_version: reviewItem.version,
    rationale: `[Conflict Resolution - ${conflictInput.outcome}]: ${conflictInput.rationale}`,
    evidence_quote: quote,
    corrected_value: correctedValue,
  };

  return submitReviewDecision(reviewItem.review_id, payload, idempotencyKey);
}
