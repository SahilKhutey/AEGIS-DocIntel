# 08 — Webhook Architecture and SSRF Prevention

## 1. Functional Scope
The Webhook Interface (`WebhookManager.tsx`, `/developer/webhooks`) allows external systems to subscribe to asynchronous document processing milestones and governance review events.

## 2. Server-Side Request Forgery (SSRF) Prevention
Because webhook URLs are invoked outbound by AEGIS servers, stringent validation prevents internal network probing:

```ts
// Evaluated both client-side and server-side
export function isSafeWebhookUrl(urlStr: string): boolean {
  // Rejects non-HTTP(S) protocols
  // Rejects 'localhost', '127.0.0.1', '0.0.0.0', '::1', '*.localhost', '*.local'
  // Rejects RFC1918 Private IP ranges: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
  // Rejects Cloud Metadata IPs: 169.254.169.254, metadata.google.internal
}
```

## 3. Delivery Auditing
Every outbound event dispatch records:
- Target Subscription ID
- Event Topic (`document.completed`, `job.failed`, etc.)
- HTTP Status Code (e.g. `200 OK`, `500 Error`)
- Round-trip Latency (ms)
- Response summary and timestamp
