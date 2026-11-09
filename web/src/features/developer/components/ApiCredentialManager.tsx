"use client";

import React, { useState, useEffect } from "react";
import {
  getApiKeys,
  createApiKey,
  revokeApiKey,
} from "../api/developer.api";
import type { ApiKeyItem, CreatedApiKeyResult } from "../types";
import { ApiKeyCreationSchema } from "../schemas/developer.schema";
import { Key, Plus, Trash2, Copy, Check, AlertTriangle } from "lucide-react";

const AVAILABLE_SCOPES = [
  { id: "documents.read", label: "documents.read — View documents & metadata" },
  { id: "documents.upload", label: "documents.upload — Ingest new documents" },
  { id: "processing.read", label: "processing.read — View pipeline runs" },
  { id: "intelligence.query", label: "intelligence.query — Ask AEGIS questions" },
  { id: "evidence.read", label: "evidence.read — Inspect citations & evidence" },
  { id: "governance.read", label: "governance.read — Read review queue" },
  { id: "admin.stats", label: "admin.stats — Access telemetry & usage metrics" },
];

export const ApiCredentialManager: React.FC = () => {
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [selectedScopes, setSelectedScopes] = useState<string[]>([
    "documents.read",
    "intelligence.query",
  ]);
  const [createdResult, setCreatedResult] = useState<CreatedApiKeyResult | null>(null);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadKeys = async () => {
    const data = await getApiKeys();
    setKeys(data);
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const validation = ApiKeyCreationSchema.safeParse({
      name: newKeyName,
      scopes: selectedScopes,
    });

    if (!validation.success) {
      setError(validation.error.issues[0]?.message || "Invalid key data");
      return;
    }

    const result = await createApiKey(newKeyName, selectedScopes);
    setCreatedResult(result);
    setKeys((prev) => [result.key, ...prev]);
    setIsCreating(false);
    setNewKeyName("");
  };

  const handleRevoke = async (id: string) => {
    if (confirm("Are you sure you want to revoke this API credential? Any client using this key will immediately be denied access.")) {
      await revokeApiKey(id);
      setKeys((prev) => prev.filter((k) => k.id !== id));
    }
  };

  const handleCopySecret = async () => {
    if (!createdResult) return;
    try {
      await navigator.clipboard.writeText(createdResult.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2500);
    } catch {
      //
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Key className="w-4 h-4 text-blue-600" aria-hidden="true" />
            <span>API Credentials & Access Keys</span>
          </h3>
          <p className="text-xs text-slate-500">
            Provision and revoke cryptographically signed Bearer tokens for external service integrations.
          </p>
        </div>

        <button
          type="button"
          onClick={() => {
            setIsCreating(true);
            setCreatedResult(null);
          }}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium cursor-pointer shadow-xs"
        >
          <Plus className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Generate API Key</span>
        </button>
      </div>

      {/* One-Time Secret Display Modal / Alert */}
      {createdResult && (
        <div role="alert" className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-3">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-xs">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" aria-hidden="true" />
            <span>Save your secret key now. It will never be displayed again!</span>
          </div>

          <div className="flex items-center justify-between gap-2 p-3 rounded-lg bg-slate-900 text-slate-100 font-mono text-xs">
            <span className="truncate select-all text-amber-300 font-bold">{createdResult.secret}</span>
            <button
              type="button"
              onClick={handleCopySecret}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition-colors cursor-pointer shrink-0"
              aria-label="Copy API secret to clipboard"
            >
              {copiedSecret ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" aria-hidden="true" />
                  <span className="text-emerald-400 font-sans">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" aria-hidden="true" />
                  <span className="font-sans">Copy</span>
                </>
              )}
            </button>
          </div>

          <p className="text-[11px] text-amber-800">
            For security, this token is hashed in AEGIS storage. If lost, you must revoke it and generate a new key.
          </p>
          <button
            type="button"
            onClick={() => setCreatedResult(null)}
            className="text-xs font-semibold text-amber-900 hover:underline cursor-pointer"
          >
            I have stored this secret safely
          </button>
        </div>
      )}

      {/* Creation Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreate} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
          <h4 className="text-xs font-bold text-slate-900">Provision New API Key</h4>

          {error && (
            <p className="text-xs text-rose-600">{error}</p>
          )}

          <div>
            <label htmlFor="key-name" className="block text-xs font-medium text-slate-700 mb-1">
              Key Identifier / Application Name
            </label>
            <input
              id="key-name"
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="e.g. ERP Ingestion Service"
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <span className="block text-xs font-medium text-slate-700 mb-2">
              Assigned Scopes & Boundaries
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {AVAILABLE_SCOPES.map((scope) => {
                const isChecked = selectedScopes.includes(scope.id);
                return (
                  <label
                    key={scope.id}
                    className="flex items-center gap-2 p-2 rounded-lg bg-white border border-slate-200 text-xs cursor-pointer hover:bg-slate-50"
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedScopes((s) => [...s, scope.id]);
                        } else {
                          setSelectedScopes((s) => s.filter((x) => x !== scope.id));
                        }
                      }}
                      className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="font-mono text-[11px] text-slate-800">{scope.label}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreating(false)}
              className="px-3 py-1.5 text-xs font-medium rounded-lg text-slate-600 hover:bg-slate-200 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-3 py-1.5 text-xs font-medium rounded-lg bg-blue-600 hover:bg-blue-700 text-white cursor-pointer shadow-xs"
            >
              Generate Credential
            </button>
          </div>
        </form>
      )}

      {/* Keys Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-4 py-3">Name / Label</th>
              <th className="px-4 py-3">Key Prefix</th>
              <th className="px-4 py-3">Assigned Scopes</th>
              <th className="px-4 py-3">Created</th>
              <th className="px-4 py-3">Last Used</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-slate-700">
            {keys.map((k) => (
              <tr key={k.id} className="hover:bg-slate-50/50">
                <td className="px-4 py-3 font-semibold text-slate-900">{k.name}</td>
                <td className="px-4 py-3 font-mono text-slate-600">{k.prefix}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1 max-w-xs">
                    {k.scopes.map((scope) => (
                      <span
                        key={scope}
                        className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono text-[10px]"
                      >
                        {scope}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                  {new Date(k.createdAt).toLocaleDateString()}
                </td>
                <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                  {k.lastUsedAt ? new Date(k.lastUsedAt).toLocaleDateString() : "Never"}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => handleRevoke(k.id)}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 rounded cursor-pointer"
                    aria-label={`Revoke key ${k.name}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" aria-hidden="true" />
                    <span>Revoke</span>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
