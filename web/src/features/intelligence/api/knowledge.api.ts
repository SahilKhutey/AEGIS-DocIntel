import { apiRequest } from "@/lib/api-client";
import { knowledgeGraphResponseSchema, type KnowledgeGraphResponse } from "../schemas/knowledge.schema";
import { ExtractedFactSchema } from "@/lib/schemas";
import { z } from "zod";

export async function getKnowledgeGraph(
  documentIds: string[],
  signal?: AbortSignal,
): Promise<KnowledgeGraphResponse> {
  // If no document selected, return empty
  if (documentIds.length === 0) {
    return { nodes: [], edges: [] };
  }

  try {
    return await apiRequest<KnowledgeGraphResponse>(
      "/api/v1/intelligence/graph",
      knowledgeGraphResponseSchema,
      {
        method: "POST",
        body: JSON.stringify({ documentIds }),
        signal,
      },
    );
  } catch {
    // Graceful fallback to mapping extracted facts from /v1/documents/{id}/facts
    try {
      const allNodes = new Map<string, { id: string; label: string; type: string; documentIds?: string[] }>();
      const edges: Array<{ id: string; source: string; target: string; relationship: string }> = [];

      for (const docId of documentIds) {
        // Add document node
        if (!allNodes.has(docId)) {
          allNodes.set(docId, {
            id: docId,
            label: docId,
            type: "document",
            documentIds: [docId],
          });
        }

        try {
          const facts = await apiRequest(
            `/api/v1/documents/${encodeURIComponent(docId)}/facts`,
            z.array(ExtractedFactSchema),
            { signal },
          );

          facts.forEach((fact, idx) => {
            const entityId = `entity-${fact.subject.toLowerCase().replace(/\s+/g, "-")}`;
            if (!allNodes.has(entityId)) {
              allNodes.set(entityId, {
                id: entityId,
                label: fact.subject,
                type: "entity",
                documentIds: [docId],
              });
            }

            edges.push({
              id: `edge-${docId}-${idx}`,
              source: entityId,
              target: docId,
              relationship: `${fact.attribute}: ${fact.raw_value}`,
            });
          });
        } catch {
          // If facts endpoint fails for this doc, continue
        }
      }

      return {
        nodes: Array.from(allNodes.values()),
        edges,
      };
    } catch {
      return { nodes: [], edges: [] };
    }
  }
}
