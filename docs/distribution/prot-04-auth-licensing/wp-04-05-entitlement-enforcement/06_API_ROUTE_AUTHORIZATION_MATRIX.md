# WP-04.05 Dossier 06: API Route Authorization Matrix

**Work Package:** PROT-04.05  
**Title:** Comprehensive API Route-to-Permission Register & Protection Model  
**Status:** **PASSED / IMPLEMENTED & VERIFIED**  
**Classification:** Restricted Evaluation Distribution  

---

## 1. Overview & Route Protection Standard

Every public-facing and evaluation-facing HTTP and WebSocket endpoint is cataloged in the authoritative register [`audit/prot-04-05/inventory/route-entitlement-matrix.csv`](file:///C:/Users/ASUS/.gemini/antigravity/worktrees/Aegis-DocIntel/product_hunt_launch_packaging/audit/prot-04-05/inventory/route-entitlement-matrix.csv).

An unmapped route is a **strict release blocker**. Any attempt to access an unmapped or internal endpoint fails closed with `HTTP 404 Not Found` or `HTTP 401 Unauthorized`.

---

## 2. Protected Route Inventory & Authorization Register

| HTTP Method | Route Path | Operation | Required Feature | Required Permission | Resource Scope | Auth Required | Quota Required |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :---: |
| `GET` | `/v1/evaluation/health` | Health Check | `dashboard.view` | `usage.read` | Public | No | No |
| `POST` | `/v1/evaluation/activate` | License Activation | `license.view` | `license.read` | License | Yes | No |
| `POST` | `/v1/evaluation/device/challenge` | Device Challenge | `device.manage` | `device.deactivate` | Device | Yes | No |
| `POST` | `/v1/evaluation/device/activate` | Device Proof | `device.manage` | `device.deactivate` | Device | Yes | No |
| `GET` | `/v1/evaluation/devices` | Device Inventory | `device.manage` | `device.deactivate` | License | Yes | No |
| `POST` | `/v1/evaluation/devices/{id}/deactivate` | Deactivate Device | `device.manage` | `device.deactivate` | Device | Yes | No |
| `GET` | `/v1/evaluation/license` | License Info | `license.view` | `license.read` | License | Yes | No |
| `GET` | `/v1/evaluation/license/verify` | Verify License | `license.view` | `license.read` | License | Yes | No |
| `GET` | `/v1/evaluation/license/entitlements` | Get Entitlements | `dashboard.view` | `usage.read` | License | Yes | No |
| `GET` | `/v1/evaluation/usage` | Usage Status | `usage.view` | `usage.read` | License | Yes | No |
| `POST` | `/v1/evaluation/documents` | Upload Document | `document.upload` | `document.upload` | Tenant | Yes | **Yes** |
| `GET` | `/v1/evaluation/documents` | List Documents | `document.metadata` | `document.read` | Tenant | Yes | No |
| `GET` | `/v1/evaluation/documents/{id}` | Read Document | `document.preview` | `document.read` | Document | Yes | No |
| `POST` | `/v1/evaluation/query` | Ask AEGIS | `document.query` | `document.query` | Document | Yes | **Yes** |
| `POST` | `/v1/evaluation/compare` | Compare Documents | `document.compare` | `document.compare` | Documents | Yes | **Yes** |
| `POST` | `/v1/admin/users` | Create User | `admin.manage_users` | `admin.users.manage` | Platform | **Admin Only** | No |
| `POST` | `/v1/admin/platform/config` | Platform Config | `engine.admin` | `admin.engine.manage` | Platform | **Admin Only** | No |
| `POST` | `/v1/admin/evaluation/licenses` | Issue License | `admin.issue_license`| `admin.evaluation.issue` | Platform | **Admin Only** | No |
| `POST` | `/v1/admin/evaluation/licenses/{id}/override` | Add Override | `admin.issue_license`| `admin.evaluation.issue` | License | **Admin Only** | No |

---

## 3. Private Engine Protection

The underlying computational engines (Sheaf Laplacian topology solvers, Knapsack context pack optimizers, OCR parsing engines) reside strictly on the server behind the Evaluation Gateway:
- Zero downloadable client packages contain direct connections to the engine.
- Direct access attempts (e.g. `/private/engine/...`) fail closed with `HTTP 404 Not Found` (`BYPASS-004`).
- All evaluator interactions must route through gateway endpoints (`/v1/evaluation/...`) where quotas and entitlements are verified before computation starts.
