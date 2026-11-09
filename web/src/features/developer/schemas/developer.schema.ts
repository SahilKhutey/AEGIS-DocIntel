import { z } from "zod";

/**
 * Validates webhook URLs to protect against Server-Side Request Forgery (SSRF).
 * Blocks loopback addresses, RFC1918 private IP ranges, and cloud metadata endpoints.
 */
export function isSafeWebhookUrl(urlStr: string): boolean {
  try {
    const url = new URL(urlStr);
    if (url.protocol !== "https:" && url.protocol !== "http:") {
      return false;
    }

    const host = url.hostname.toLowerCase();

    // Block localhost and standard loopback
    if (
      host === "localhost" ||
      host === "127.0.0.1" ||
      host === "0.0.0.0" ||
      host === "::1" ||
      host.endsWith(".localhost") ||
      host.endsWith(".local")
    ) {
      return false;
    }

    // Block cloud metadata IPs
    if (host === "169.254.169.254" || host === "metadata.google.internal") {
      return false;
    }

    // Block private RFC1918 IPv4
    const ipMatch = host.match(/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/);
    if (ipMatch) {
      const b0 = parseInt(ipMatch[1], 10);
      const b1 = parseInt(ipMatch[2], 10);
      if (b0 === 10) return false; // 10.0.0.0/8
      if (b0 === 127) return false; // 127.0.0.0/8
      if (b0 === 169 && b1 === 254) return false; // 169.254.0.0/16
      if (b0 === 172 && b1 >= 16 && b1 <= 31) return false; // 172.16.0.0/12
      if (b0 === 192 && b1 === 168) return false; // 192.168.0.0/16
    }

    return true;
  } catch {
    return false;
  }
}

export const WebhookRegistrationSchema = z.object({
  url: z
    .string()
    .url("Must be a valid HTTP or HTTPS URL")
    .refine(
      (url) => isSafeWebhookUrl(url),
      "Webhook URL must not point to localhost, private IP ranges, or internal cloud metadata (SSRF protection).",
    ),
  events: z.array(z.string()).min(1, "Select at least one event subscription"),
});

export const ApiKeyCreationSchema = z.object({
  name: z.string().min(2, "Key name must be at least 2 characters"),
  scopes: z.array(z.string()).min(1, "Select at least one permission scope"),
});
