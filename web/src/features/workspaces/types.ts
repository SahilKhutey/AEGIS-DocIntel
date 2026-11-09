export type Workspace = {
  id: string;
  name: string;
  description?: string;
  tenantId?: string;
};

export type WorkspaceListResponse = {
  items: Workspace[];
  activeWorkspaceId: string;
};
