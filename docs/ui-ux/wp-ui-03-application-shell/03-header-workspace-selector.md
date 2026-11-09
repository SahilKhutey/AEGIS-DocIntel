# 03 — Application Header & Workspace Selector

**Document Identifier**: `AEGIS-DOCINTEL-WP-UI-03-03`  
**Work Package**: `WP-UI-03: Application Shell`  
**Status**: APPROVED ARCHITECTURE  

---

## 1. Header Layout & Functionality

The application header (`AppHeader`) is a fixed $64\text{px}$ operational bar positioned at the top of the main viewport. It provides:
1. **Mobile Menu Trigger**: Hamburger button (`aria-label="Open navigation"`) visible only below $1024\text{px}$.
2. **Workspace Selector**: Dropdown popover listbox displaying the current workspace and enabling switching.
3. **Global Search**: Search bar with debounced input and clear triggers.
4. **Notification Center**: Bell button with unread count badge and event flyout panel.
5. **User Account Menu**: User display name, email, and sign-out action.

```
+-----------------------------------------------------------------------------------------------+
| [Menu]  [Building2] Primary Workspace [v]  |  [Search] Search docs... (X)  |  [Bell (3)] [User (v)]|
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Workspace Selector Specification

### 2.1 Schema & Data Contract
```ts
export interface Workspace {
  id: string;
  name: string;
  description?: string;
  tenantId?: string;
}

export interface WorkspaceListResponse {
  items: Workspace[];
  activeWorkspaceId: string;
}
```

### 2.2 User Interaction & Keyboard Navigation
- **Trigger**: Button with `aria-haspopup="listbox"`, `aria-expanded={isOpen}`, and accessible label including the active workspace name.
- **Popover**: Modal listbox (`role="listbox"`, `aria-label="Select workspace"`).
- **Options**: Interactive list items (`role="option"`, `aria-selected={item.id === activeId}`).
- **Keyboard Dismissal**: Pressing <kbd>Escape</kbd> immediately closes the dropdown and returns focus to the trigger button.
- **Click Outside**: Clicks outside the popover close the selector.

### 2.3 Backend API Boundary & Multi-Tenancy Truth
- **Backend Contract**: In the current FastAPI OpenAPI contract (`contracts/openapi.yaml`), multi-tenancy is enforced server-side via HTTP header `X-Tenant-ID` or JWT claims.
- **No Dedicated Endpoint**: There is no dedicated `/v1/workspaces` CRUD endpoint in the backend. Multi-workspace listing is managed via client-injected configuration or tenant context.
- **Zero Fake Authorization**: Switching workspaces in the frontend updates the client presentation context but does NOT spoof or bypass backend tenant validation.

---

## 3. User Menu Specification
- **Trigger**: Circular avatar button displaying user initials or icon with `aria-haspopup="menu"`.
- **Panel**: Dropdown menu containing user name (`Analyst`), email (`analyst@aegis.internal`), and a **Sign out** button.
- **Dismissal**: Closes on Escape or outside click.
