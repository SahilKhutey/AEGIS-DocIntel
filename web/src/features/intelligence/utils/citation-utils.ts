import type { AnswerClaim, CitationReference } from "../types";

export type BrokenCitationReference = {
  claimId: string;
  citationId: string;
};

export type CitationValidationResult = {
  valid: boolean;
  brokenReferences: BrokenCitationReference[];
};

/**
 * Returns citations referenced by a specific claim.
 */
export function getClaimCitations(
  claim: AnswerClaim | { citationIds: string[] },
  citations: CitationReference[],
): CitationReference[] {
  const allowedIds = new Set(claim.citationIds);
  return citations.filter((citation) => allowedIds.has(citation.citationId));
}

/**
 * Returns citations that are not referenced by any claim.
 */
export function getUnreferencedCitations(
  claims: (AnswerClaim | { citationIds: string[] })[],
  citations: CitationReference[],
): CitationReference[] {
  const referenced = new Set(claims.flatMap((claim) => claim.citationIds));
  return citations.filter(
    (citation) => !referenced.has(citation.citationId),
  );
}

/**
 * Identifies citation IDs that are referenced by claims but not present in available citations.
 */
export function findBrokenCitationReferences(
  claims: (AnswerClaim | { citationIds: string[] })[],
  citations: CitationReference[],
): string[] {
  const available = new Set(citations.map((c) => c.citationId));
  return claims.flatMap((claim) =>
    claim.citationIds.filter((id) => !available.has(id)),
  );
}

/**
 * Validates integrity between claims and citations for an answer.
 */
export function validateAnswerCitations(answer: {
  claims?: { claimId: string; citationIds: string[] }[];
  citations: { citationId: string; documentId?: string }[];
}): CitationValidationResult {
  const available = new Set(answer.citations.map((c) => c.citationId));
  const brokenReferences: BrokenCitationReference[] = [];

  if (answer.claims) {
    for (const claim of answer.claims) {
      for (const citationId of claim.citationIds) {
        if (!available.has(citationId)) {
          brokenReferences.push({
            claimId: claim.claimId,
            citationId,
          });
        }
      }
    }
  }

  return {
    valid: brokenReferences.length === 0,
    brokenReferences,
  };
}
