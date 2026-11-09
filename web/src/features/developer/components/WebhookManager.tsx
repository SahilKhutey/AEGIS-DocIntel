"use client";

import React, { useState, useEffect } from "react";
import {
  getWebhookSubscriptions,
  createWebhookSubscription,
  deleteWebhookSubscription,
  getWebhookDeliveryLogs,
} from "../api/developer.api";
import type { WebhookSubscription, WebhookDeliveryLog } from "../types";
import { isSafeWebhookUrl } from "../schemas/developer.schema";
import { Webhook, Plus, Trash2, CheckCircle2, ShieldAlert } from "lucide-react";

const AVAILABLE_WEBHOOK_EVENTS = [
  "document.completed",
  "job.failed",
  "governance.review_required",
  "governance.decision_submitted",
];

export const WebhookManager: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<WebhookSubscription[]>([]);
  const [deliveryLogs, setDeliveryLogs] = useState<WebhookDeliveryLog[]>([]);
  const [isRegistering, setIsRegistering] = useState(false);
  const [url, setUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([
    "document.completed",
    "job.failed",
  ]);
  const [urlError, setUrlError] = useState<string | null>(null);

  const loadData = async () => {
    const [subs, logs] = await Promise.all([
      getWebhookSubscriptions(),
      getWebhookDeliveryLogs(),
    ]);
    setSubscriptions(subs);
    setDeliveryLogs(logs);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setUrlError(null);

    if (!isSafeWebhookUrl(url)) {
      setUrlError(
        "Invalid or unsafe URL: Addresses pointing to localhost, private IP subnets (10.x, 192.168.x, 172.16-31.x), or internal cloud metadata are blocked for SSRF protection.",
      );
      return;
    }

    if (selectedEvents.length === 0) {
      setUrlError("Select at least one event type.");
      return;
    }

    const newSub = await createWebhookSubscription(url, selectedEvents);
    setSubscriptions((prev) => [newSub, ...prev]);
    setIsRegistering(false);
    setUrl("");
  };

  const handleDelete = async (id: string) => {
    if (confirm("Delete this webhook subscription? Events will no longer be dispatched to this destination.")) {
      await deleteWebhookSubscription(id);
      setSubscriptions((prev) => prev.filter((s) => s.id !== id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Webhook Endpoints Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Webhook className="w-4 h-4 text-purple-600" aria-hidden="true" />
              <span>Webhook Subscriptions</span>
            </h3>
            <p className="text-xs text-slate-500">
              Receive automated HTTP POST notifications when document workflows and governance decisions trigger.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsRegistering(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium cursor-pointer shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Register Webhook</span>
          </button>
        </div>

        {/* Registration Modal / Form */}
        {isRegistering && (
          <form onSubmit={handleRegister} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
              <ShieldAlert className="w-4 h-4 text-purple-600" aria-hidden="true" />
              <span>Register New Outbound Destination</span>
            </div>

            {urlError && (
              <div role="alert" className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
                {urlError}
              </div>
            )}

            <div>
              <label htmlFor="wh-url" className="block text-xs font-medium text-slate-700 mb-1">
                Destination HTTPS Endpoint URL
              </label>
              <input
                id="wh-url"
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://api.yourdomain.com/webhooks/aegis"
                className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                required
              />
              <span className="text-[10px] text-slate-400 block mt-1">
                Protected against SSRF: Must be a publicly resolvable hostname. Localhost and RFC1918 IPs are rejected.
              </span>
            </div>

            <div>
              <span className="block text-xs font-medium text-slate-700 mb-2">
                Event Subscriptions
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {AVAILABLE_WEBHOOK_EVENTS.map((evt) => {
                  const isChecked = selectedEvents.includes(evt);
                  return (
                    <label
                      key={evt}
                      className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200 text-xs cursor-pointer hover:bg-slate-50"
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedEvents((s) => [...s, evt]);
                          } else {
                            setSelectedEvents((s) => s.filter((x) => x !== evt));
                          }
                        }}
                        className="rounded border-slate-300 text-purple-600 focus:ring-purple-500"
                      />
                      <span className="font-mono text-[11px] text-slate-800">{evt}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsRegistering(false)}
                className="px-3 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:bg-slate-200 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1.5 text-xs font-medium rounded-lg bg-purple-600 hover:bg-purple-700 text-white cursor-pointer shadow-xs"
              >
                Register Subscription
              </button>
            </div>
          </form>
        )}

        {/* Subscriptions Table */}
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-4 py-3">Endpoint URL</th>
                <th className="px-4 py-3">Subscribed Events</th>
                <th className="px-4 py-3">Secret Token</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {subscriptions.map((sub) => (
                <tr key={sub.id} className="hover:bg-slate-50/50">
                  <td className="px-4 py-3 font-mono font-medium text-slate-900 break-all">
                    {sub.url}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1 max-w-xs">
                      {sub.events.map((e) => (
                        <span
                          key={e}
                          className="px-1.5 py-0.5 rounded bg-purple-50 text-purple-700 font-mono text-[10px]"
                        >
                          {e}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-slate-500">{sub.secretTokenHint}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3" aria-hidden="true" />
                      Active
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => handleDelete(sub.id)}
                      className="inline-flex items-center gap-1 px-2 py-1 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded cursor-pointer"
                      aria-label="Delete subscription"
                    >
                      <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                      <span>Delete</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Delivery Logs Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-slate-900">Recent Webhook Deliveries</h3>
        <div className="overflow-x-auto rounded-lg border border-slate-200">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px] font-sans">
              <tr>
                <th className="px-3 py-2">Event</th>
                <th className="px-3 py-2">HTTP Status</th>
                <th className="px-3 py-2">Latency</th>
                <th className="px-3 py-2">Timestamp</th>
                <th className="px-3 py-2">Response</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 text-[11px]">
              {deliveryLogs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/50">
                  <td className="px-3 py-2 font-bold text-purple-700">{log.event}</td>
                  <td className="px-3 py-2">
                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-bold">
                      {log.statusCode} OK
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-500">{log.durationMs}ms</td>
                  <td className="px-3 py-2 text-slate-500">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="px-3 py-2 text-slate-600 truncate max-w-xs">{log.responseBody}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
