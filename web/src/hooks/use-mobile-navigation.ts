"use client";

import { useState, useCallback, useEffect } from "react";
import { usePathname } from "next/navigation";

export function useMobileNavigation() {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const toggle = useCallback(() => setIsOpen((prev) => !prev), []);

  useEffect(() => {
    setIsOpen(false);
  }, [pathname]);

  return {
    isOpen,
    open,
    close,
    toggle,
  };
}
