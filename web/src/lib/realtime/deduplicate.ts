/**
 * Client-side deduplication helper with bounded memory cache
 */
export function createEventDeduplicator(maxSize = 1000) {
  const seen = new Set<string>();

  return {
    isDuplicate(eventId: string): boolean {
      if (seen.has(eventId)) {
        return true;
      }
      seen.add(eventId);

      if (seen.size > maxSize) {
        const oldest = seen.values().next().value;
        if (oldest !== undefined) {
          seen.delete(oldest);
        }
      }
      return false;
    },
    clear(): void {
      seen.clear();
    },
    size(): number {
      return seen.size;
    },
  };
}
