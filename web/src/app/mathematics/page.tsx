import React from "react";
import { MathCatalog } from "@/features/mathematics/components/MathCatalog";

export const metadata = {
  title: "Mathematical Representations — AEGIS-DocIntel",
  description: "High-dimensional embeddings, kernel matrices, similarity equations, and provenance",
};

export default function MathematicsPage() {
  return (
    <div className="space-y-6">
      <MathCatalog />
    </div>
  );
}
