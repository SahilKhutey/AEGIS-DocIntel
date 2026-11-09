import { z } from "zod";
import type { GlobalSearchResponse } from "./types";
import { apiRequest } from "@/lib/api-client";

export const SearchResultSchema = z.object({
  id: z.string(),
  category: z.enum(["document", "evidence", "review"]),
  title: z.string(),
  description: z.string().optional(),
  href: z.string(),
});

export const GlobalSearchResponseSchema = z.object({
  items: z.array(SearchResultSchema),
  total: z.number(),
});

export interface SearchService {
  search(query: string, signal?: AbortSignal): Promise<GlobalSearchResponse>;
}

export class DefaultSearchService implements SearchService {
  async search(query: string, signal?: AbortSignal): Promise<GlobalSearchResponse> {
    const params = new URLSearchParams({ q: query });
    return await apiRequest(`/api/v1/search?${params.toString()}`, GlobalSearchResponseSchema, {
      signal,
    });
  }
}

export const searchService = new DefaultSearchService();
