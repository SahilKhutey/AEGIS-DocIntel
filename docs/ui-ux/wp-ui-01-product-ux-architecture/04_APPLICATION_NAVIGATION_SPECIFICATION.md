# AEGIS-DocIntel — Application Navigation Specification

## 1. Single Source of Truth

Application navigation is defined and governed by [`web/src/config/navigation.ts`](file:///c:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/ui_ux_development_strategy/web/src/config/navigation.ts). All desktop, mobile, breadcrumb, and automated navigation tests import from this module.

## 2. Navigation Contract & Rules

```typescript
export type NavigationStatus = "active" | "planned";

export type NavigationItem = {
  label: string;
  href: string;
  description: string;
  status: NavigationStatus;
  match: "exact" | "prefix";
};

export type NavigationGroup = {
  id: string;
  label: string;
  items: NavigationItem[];
};
```

### Core Invariants:
1. **Planned Feature Protection**: Items with `status: "planned"` are strictly omitted from rendered active navigation links to prevent deceptive UI states.
2. **Deterministic Route Matching**:
   - `exact`: Matches only exact pathname (e.g. `/`).
   - `prefix`: Matches parent route and nested child routes (e.g. `/documents` remains active for `/documents/doc-123`).
3. **No Unrelated Prefix Bleed**: Route matching prevents false positives (e.g. `/documents-old` will not trigger active status for `/documents`).

## 3. Registered Navigation Groups

| Group ID | Group Label | Items | Initial Status | Match Mode |
| :--- | :--- | :--- | :---: | :---: |
| `workspace` | Workspace | Overview (`/`) | Active | exact |
| `documents` | Documents | Document Library (`/documents`) | Active | prefix |
| `intelligence` | Intelligence | Ask AEGIS (`/ask`)<br>Compare Documents (`/compare`)<br>Evidence Explorer (`/evidence`) | Active<br>Active<br>Planned | prefix<br>prefix<br>prefix |
| `governance` | Governance | Review Queue (`/reviews`) | Active | prefix |
| `system` | System | Processing Jobs (`/processing`)<br>Analytics (`/analytics`)<br>Settings (`/settings`) | Planned<br>Planned<br>Planned | prefix<br>prefix<br>prefix |

## 4. Deep-Linking & URL Contracts

- **Document Library**: `/documents?status={pending|indexing|ready|failed}&search={query}&page={n}`
- **Document Inspection**: `/documents/{documentId}?tab={overview|chunks|elements}&page={n}`
- **Ask AEGIS**: `/ask?doc_id={id}&q={query}&citation={evidence_id}`
- **Compare Documents**: `/compare?doc_a={id}&doc_b={id}&conflicts_only={true|false}`
- **Review Queue**: `/reviews?status={pending|in_review|approved|corrected}&type={fact|conflict}`
- **Review Details**: `/reviews/{reviewId}`

## 5. Responsive Behavior

- **Desktop (`>= 1024px`)**: Grouped horizontal or sidebar navigation with uppercase category labels.
- **Mobile / Tablet (`< 1024px`)**: Horizontal scrolling action bar rendered with clean touch targets.
- **Accessibility**: Pinned navigation landmark `<nav aria-label="Primary navigation">`, `<main id="main-content">`, and valid `aria-current="page"` indicators on active links.
