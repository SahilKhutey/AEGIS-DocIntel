import { apiRequest } from "@/lib/api-client";
import { DocumentComparisonSchema, type DocumentComparison } from "@/lib/schemas";
import type { ComparisonRequest, ComparisonResponse, ComparisonDifference } from "../types";

export async function compareDocuments(
  payload: ComparisonRequest,
  signal?: AbortSignal,
): Promise<ComparisonResponse> {
  if (payload.documentIds.length < 2) {
    throw new Error("Select at least two documents.");
  }

  const result = await apiRequest<DocumentComparison>(
    "/api/v1/intelligence/compare",
    DocumentComparisonSchema,
    {
      method: "POST",
      body: JSON.stringify({ document_ids: payload.documentIds }),
      signal,
    },
  );

  const differences: ComparisonDifference[] = [];

  // Map conflicts to differences
  (result.conflicts || []).forEach((conf: Record<string, unknown>, idx: number) => {
    differences.push({
      differenceId: `diff-conflict-${idx}`,
      category: String(conf.attribute || conf.subject || "Discrepancy"),
      description: String(conf.description || `Discrepancy in ${String(conf.attribute || "attribute")}`),
      significance: "high",
    });
  });

  // Map aligned comparison facts
  (result.comparisons || []).forEach((comp: Record<string, unknown>, idx: number) => {
    if (!comp.is_match) {
      differences.push({
        differenceId: `diff-fact-${idx}`,
        category: String(comp.attribute || "Fact"),
        description: `Value variance: "${String(comp.val_a ?? "—")}" vs "${String(comp.val_b ?? "—")}"`,
        significance: "medium",
      });
    }
  });

  return {
    comparisonId: `cmp-${Date.now()}`,
    documentIds: result.document_ids,
    differences,
    summary: `Compared ${result.total_pairs} pairs across ${result.document_ids.length} documents. Found ${result.matching_pairs} matches and ${result.conflicting_pairs} conflicts.`,
  };
}
