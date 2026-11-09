import { describe, expect, it } from "vitest";
import {
  validateAnswerCitations,
  getClaimCitations,
  getUnreferencedCitations,
  findBrokenCitationReferences,
} from "@/features/intelligence/utils/citation-utils";
import type { AnswerClaim, CitationReference } from "@/features/intelligence/types";

describe("validateAnswerCitations", () => {
  it("accepts claims whose citations exist", () => {
    const result = validateAnswerCitations({
      claims: [
        {
          claimId: "claim-1",
          citationIds: ["citation-1"],
        },
      ],
      citations: [
        {
          citationId: "citation-1",
          documentId: "document-1",
        },
      ],
    });
    expect(result.valid).toBe(true);
    expect(result.brokenReferences).toHaveLength(0);
  });

  it("identifies a broken citation reference", () => {
    const result = validateAnswerCitations({
      claims: [
        {
          claimId: "claim-1",
          citationIds: ["missing-citation"],
        },
      ],
      citations: [],
    });
    expect(result.valid).toBe(false);
    expect(result.brokenReferences).toEqual([
      {
        claimId: "claim-1",
        citationId: "missing-citation",
      },
    ]);
  });

  it("accepts an answer without claims", () => {
    const result = validateAnswerCitations({
      citations: [],
    });
    expect(result.valid).toBe(true);
  });
});

describe("citation utilities", () => {
  const citations: CitationReference[] = [
    {
      citationId: "cit-1",
      documentId: "doc-1",
      documentName: "Annual Report",
      pageNumber: 4,
      quote: "Revenue increased by 15%",
    },
    {
      citationId: "cit-2",
      documentId: "doc-2",
      documentName: "Risk Statement",
      pageNumber: 12,
      quote: "Market fluctuations may impact returns",
    },
    {
      citationId: "cit-3",
      documentId: "doc-1",
      documentName: "Annual Report",
      pageNumber: 7,
      quote: "Operating expenses decreased",
    },
  ];

  const claim: AnswerClaim = {
    claimId: "cl-1",
    text: "The company reported higher revenues.",
    citationIds: ["cit-1"],
    supportStatus: "supported",
  };

  it("extracts citations corresponding to a claim", () => {
    const matched = getClaimCitations(claim, citations);
    expect(matched).toHaveLength(1);
    expect(matched[0].citationId).toBe("cit-1");
  });

  it("identifies unreferenced citations", () => {
    const unreferenced = getUnreferencedCitations([claim], citations);
    expect(unreferenced.map((c) => c.citationId)).toEqual(["cit-2", "cit-3"]);
  });

  it("finds broken citation references as string IDs", () => {
    const claimWithBroken: AnswerClaim = {
      claimId: "cl-2",
      text: "Unverified statement.",
      citationIds: ["cit-non-existent"],
      supportStatus: "unsupported",
    };
    const broken = findBrokenCitationReferences([claimWithBroken], citations);
    expect(broken).toEqual(["cit-non-existent"]);
  });
});
