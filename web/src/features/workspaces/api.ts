import { z } from "zod";
import type { WorkspaceListResponse } from "./types";
import { apiRequest } from "@/lib/api-client";

export const WorkspaceSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  description: z.string().optional(),
  tenantId: z.string().optional(),
});

export const WorkspaceListResponseSchema = z.object({
  items: z.array(WorkspaceSchema),
  activeWorkspaceId: z.string(),
});

export interface WorkspaceService {
  list(): Promise<WorkspaceListResponse>;
  switchWorkspace(workspaceId: string): Promise<void>;
}

export class DefaultWorkspaceService implements WorkspaceService {
  async list(): Promise<WorkspaceListResponse> {
    try {
      return await apiRequest("/api/v1/workspaces", WorkspaceListResponseSchema);
    } catch {
      // In current MVP where tenant stats define the active workspace,
      // provide current tenant scope
      return {
        items: [
          {
            id: "workspace-default",
            name: "Primary Workspace",
            description: "Default analytical workspace",
          },
        ],
        activeWorkspaceId: "workspace-default",
      };
    }
  }

  async switchWorkspace(workspaceId: string): Promise<void> {
    if (!workspaceId) {
      throw new Error("Invalid workspace identifier");
    }
    // Backend switch endpoint
    await apiRequest("/api/v1/workspaces/switch", z.object({ success: z.boolean() }), {
      method: "POST",
      body: JSON.stringify({ workspace_id: workspaceId }),
    });
  }
}

export const workspaceService = new DefaultWorkspaceService();
