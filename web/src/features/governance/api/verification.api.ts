import { submitReviewDecision } from "./decision.api";
import { mapVerificationToDecision } from "../utils/verification-utils";
import type { FactVerificationInput } from "../schemas/verification.schema";
import type { ReviewItem, DecisionSubmission } from "../types";

export interface RecordVerificationParams {
  reviewItem: ReviewItem;
  verificationInput: FactVerificationInput;
  correctedValue?: string | number | boolean;
  correctedType?: string;
  unit?: string;
  idempotencyKey?: string;
}

export async function submitVerificationAsDecision(params: RecordVerificationParams) {
  const { reviewItem, verificationInput, correctedValue, correctedType, unit, idempotencyKey } = params;

  const action = mapVerificationToDecision(verificationInput.verification_status);

  const payload: DecisionSubmission = {
    action,
    expected_version: reviewItem.version,
    rationale: verificationInput.rationale,
    evidence_quote: verificationInput.verified_quote,
    corrected_value: action === "correct" ? correctedValue : undefined,
    corrected_type: action === "correct" ? correctedType : undefined,
    unit: action === "correct" && unit ? unit : undefined,
  };

  return submitReviewDecision(reviewItem.review_id, payload, idempotencyKey);
}
