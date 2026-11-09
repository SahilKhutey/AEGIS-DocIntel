"use client";

import { useState, useCallback } from "react";
import { askAegis } from "../api/ask.api";
import type { AskRequest, AskResponse } from "../types";

export function useAskAegis() {
  const [data, setData] = useState<AskResponse | null>(null);
  const [isPending, setIsPending] = useState(false);
  const [isError, setIsError] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const mutateAsync = useCallback(async (payload: AskRequest): Promise<AskResponse> => {
    setIsPending(true);
    setIsError(false);
    setError(null);
    try {
      const res = await askAegis(payload);
      setData(res);
      return res;
    } catch (err) {
      setIsError(true);
      const e = err instanceof Error ? err : new Error("Failed to ask AEGIS");
      setError(e);
      throw e;
    } finally {
      setIsPending(false);
    }
  }, []);

  return {
    data,
    isPending,
    isError,
    error,
    mutateAsync,
  };
}
