"use client";

import React from "react";
import { UploadDialog } from "@/features/uploads/components/upload-dialog";
import type { DocumentItem } from "@/lib/schemas";

export interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (document: DocumentItem) => void;
}

export function UploadModal({ isOpen, onClose, onSuccess }: UploadModalProps) {
  return (
    <UploadDialog
      isOpen={isOpen}
      onClose={onClose}
      onSuccess={onSuccess}
    />
  );
}
