import React from "react";
import { notFound } from "next/navigation";
import { getRepresentationById } from "@/features/mathematics/api/mathematics.api";
import { VectorViewer } from "@/features/mathematics/components/VectorViewer";
import { MatrixViewer } from "@/features/mathematics/components/MatrixViewer";
import { ProvenanceViewer } from "@/features/mathematics/components/ProvenanceViewer";

export interface RepresentationDetailPageProps {
  params: Promise<{ representationId: string }>;
}

export default async function RepresentationDetailPage({
  params,
}: RepresentationDetailPageProps) {
  const { representationId } = await params;
  const representation = await getRepresentationById(representationId);

  if (!representation) {
    notFound();
  }

  return (
    <div className="space-y-6">
      {representation.type === "vector" && (
        <VectorViewer vector={representation} />
      )}
      {representation.type === "matrix" && (
        <MatrixViewer matrix={representation} />
      )}
      <ProvenanceViewer provenance={representation.provenance} />
    </div>
  );
}
