"use client";

import React from "react";

export interface PermissionGateProps {
  granted?: readonly string[];
  required: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function PermissionGate({
  granted = [],
  required,
  children,
  fallback = null,
}: PermissionGateProps) {
  const hasAccess = granted.includes(required);

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
