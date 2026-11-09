"use client";

import React, { useState, useId } from "react";
import { cn } from "@/lib/cn";

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement<{
    "aria-describedby"?: string;
    onMouseEnter?: React.MouseEventHandler;
    onMouseLeave?: React.MouseEventHandler;
    onFocus?: React.FocusEventHandler;
    onBlur?: React.FocusEventHandler;
  }>;
  className?: string;
}

export function Tooltip({ content, children, className }: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const id = useId();

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {React.cloneElement(children, {
        "aria-describedby": visible ? id : undefined,
      })}

      {visible && (
        <div
          id={id}
          role="tooltip"
          className={cn(
            "absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2",
            "whitespace-nowrap rounded-[var(--radius-sm)] bg-[var(--foreground)] px-2.5 py-1 text-xs font-normal text-[var(--surface)]",
            "shadow-[var(--shadow-sm)] pointer-events-none transition-opacity",
            className
          )}
        >
          {content}
        </div>
      )}
    </div>
  );
}
