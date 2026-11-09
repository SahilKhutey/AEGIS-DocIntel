/**
 * AEGIS Design System Specification & Token Manifest
 * Work Package: WP-UI-02
 */

import { BREAKPOINTS } from "./breakpoints";

export const DESIGN_SYSTEM_META = {
  name: "AEGIS Design System",
  version: "2.0.0",
  targetStandard: "WCAG 2.2 Level AA",
  baseSpacingUnit: 4, // 4px grid
} as const;

export const COLOR_TOKENS = {
  light: {
    background: "#f8fafc",
    surface: "#ffffff",
    surfaceMuted: "#f1f5f9",
    foreground: "#111827",
    muted: "#64748b",
    border: "#e2e8f0",
    primary: "#2563eb",
    primaryHover: "#1d4ed8",
    primaryForeground: "#ffffff",
    success: "#15803d",
    warning: "#b45309",
    danger: "#b91c1c",
    info: "#0369a1",
  },
  dark: {
    background: "#0b1220",
    surface: "#111827",
    surfaceMuted: "#1e293b",
    foreground: "#f8fafc",
    muted: "#a1a1aa",
    border: "#334155",
    primary: "#60a5fa",
    primaryHover: "#93c5fd",
    primaryForeground: "#0b1220",
    success: "#4ade80",
    warning: "#fbbf24",
    danger: "#f87171",
    info: "#38bdf8",
  },
} as const;

export const TYPOGRAPHY_TOKENS = {
  fontFamilies: {
    sans: "Arial, Helvetica, sans-serif",
    mono: '"Cascadia Code", Consolas, monospace',
  },
  fontSize: {
    xs: "0.75rem",
    sm: "0.875rem",
    base: "1rem",
    lg: "1.125rem",
    xl: "1.25rem",
    "2xl": "1.5rem",
    "3xl": "1.875rem",
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.65,
  },
} as const;

export const SPACING_TOKENS = {
  "space-1": "0.25rem", // 4px
  "space-2": "0.5rem",  // 8px
  "space-3": "0.75rem", // 12px
  "space-4": "1rem",    // 16px
  "space-5": "1.25rem", // 20px
  "space-6": "1.5rem",  // 24px
  "space-8": "2rem",    // 32px
  "space-10": "2.5rem", // 40px
  "space-12": "3rem",   // 48px
  "space-16": "4rem",   // 64px
} as const;

export const RADIUS_TOKENS = {
  sm: "0.25rem",
  md: "0.5rem",
  lg: "0.75rem",
  xl: "1rem",
} as const;

export const ELEVATION_TOKENS = {
  sm: "0 1px 2px rgb(15 23 42 / 0.06)",
  md: "0 4px 12px rgb(15 23 42 / 0.08)",
} as const;

export const LAYOUT_TOKENS = {
  sidebarWidth: "16rem",
  contentMaxWidth: "90rem",
  headerHeight: "4rem",
  breakpoints: BREAKPOINTS,
} as const;
