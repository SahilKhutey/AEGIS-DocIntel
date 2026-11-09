export type SearchCategory =
  | "document"
  | "evidence"
  | "review";

export type SearchResult = {
  id: string;
  category: SearchCategory;
  title: string;
  description?: string;
  href: string;
};

export type GlobalSearchResponse = {
  items: SearchResult[];
  total: number;
};
