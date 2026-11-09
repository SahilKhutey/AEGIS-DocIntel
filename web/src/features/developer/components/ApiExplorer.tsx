"use client";

import React, { useState } from "react";
import { OPENAPI_ENDPOINTS } from "../api/developer.api";
import type { OpenApiEndpoint } from "../types";
import { JsonViewer } from "@/components/advanced/JsonViewer";
import { Copy, Check, ChevronRight } from "lucide-react";

export const ApiExplorer: React.FC = () => {
  const [selectedEndpoint, setSelectedEndpoint] = useState<OpenApiEndpoint>(
    OPENAPI_ENDPOINTS[0],
  );
  const [codeLanguage, setCodeLanguage] = useState<"curl" | "python" | "typescript">("curl");
  const [copiedCode, setCopiedCode] = useState(false);

  const getMethodBadge = (method: string) => {
    switch (method) {
      case "GET":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "POST":
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
      case "DELETE":
        return "bg-rose-50 text-rose-700 border-rose-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const generateSnippet = (ep: OpenApiEndpoint, lang: "curl" | "python" | "typescript"): string => {
    const hasBody = ep.method === "POST" && ep.requestBodySample;
    const bodyStr = hasBody ? JSON.stringify(ep.requestBodySample, null, 2) : "";

    switch (lang) {
      case "python":
        return `import requests

url = "https://api.aegis.enterprise.internal${ep.path}"
headers = {
    "Authorization": "Bearer $AEGIS_API_KEY",
    "Content-Type": "application/json"
}
${hasBody ? `payload = ${bodyStr}\n\nresponse = requests.${ep.method.toLowerCase()}(url, json=payload, headers=headers)` : `response = requests.${ep.method.toLowerCase()}(url, headers=headers)`}

print(response.status_code)
print(response.json())`;

      case "typescript":
        return `const response = await fetch("https://api.aegis.enterprise.internal${ep.path}", {
  method: "${ep.method}",
  headers: {
    "Authorization": "Bearer $AEGIS_API_KEY",
    "Content-Type": "application/json"
  }${hasBody ? `,\n  body: JSON.stringify(${bodyStr.replace(/\n/g, "\n  ")})` : ""}
});

const data = await response.json();
console.log(data);`;

      case "curl":
      default:
        return `curl -X ${ep.method} "https://api.aegis.enterprise.internal${ep.path}" \\
  -H "Authorization: Bearer $AEGIS_API_KEY" \\
  -H "Content-Type: application/json"${hasBody ? ` \\\n  -d '${JSON.stringify(ep.requestBodySample)}'` : ""}`;
    }
  };

  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(generateSnippet(selectedEndpoint, codeLanguage));
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    } catch {
      //
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Endpoints Sidebar */}
      <div className="lg:col-span-4 bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
          OpenAPI REST Endpoints
        </h3>
        <div className="space-y-1.5">
          {OPENAPI_ENDPOINTS.map((ep) => {
            const isSelected = selectedEndpoint.path === ep.path && selectedEndpoint.method === ep.method;
            return (
              <button
                key={`${ep.method}-${ep.path}`}
                type="button"
                onClick={() => setSelectedEndpoint(ep)}
                className={`w-full text-left p-2.5 rounded-lg border transition-all text-xs cursor-pointer flex items-center justify-between gap-2 ${
                  isSelected
                    ? "bg-blue-50/60 border-blue-300 ring-1 ring-blue-500"
                    : "bg-white border-slate-200 hover:bg-slate-50"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border ${getMethodBadge(
                      ep.method,
                    )}`}
                  >
                    {ep.method}
                  </span>
                  <span className="font-mono text-slate-800 truncate text-[11px]">{ep.path}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-400 shrink-0" aria-hidden="true" />
              </button>
            );
          })}
        </div>
      </div>

      {/* Endpoint Details & Playground */}
      <div className="lg:col-span-8 space-y-6">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <span
              className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${getMethodBadge(
                selectedEndpoint.method,
              )}`}
            >
              {selectedEndpoint.method}
            </span>
            <span className="font-mono text-sm font-bold text-slate-900">{selectedEndpoint.path}</span>
          </div>

          <div>
            <h4 className="text-sm font-bold text-slate-900 mb-1">{selectedEndpoint.summary}</h4>
            {selectedEndpoint.description && (
              <p className="text-xs text-slate-500">{selectedEndpoint.description}</p>
            )}
          </div>

          {/* Parameters if present */}
          {selectedEndpoint.parameters && selectedEndpoint.parameters.length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Parameters
              </h5>
              <div className="overflow-x-auto rounded-lg border border-slate-200">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px] font-sans">
                    <tr>
                      <th className="px-3 py-1.5">Name</th>
                      <th className="px-3 py-1.5">In</th>
                      <th className="px-3 py-1.5">Type</th>
                      <th className="px-3 py-1.5">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-[11px]">
                    {selectedEndpoint.parameters.map((p) => (
                      <tr key={p.name}>
                        <td className="px-3 py-1.5 font-bold text-blue-700">{p.name}</td>
                        <td className="px-3 py-1.5 text-slate-500">{p.in}</td>
                        <td className="px-3 py-1.5 text-purple-700">{p.type}</td>
                        <td className="px-3 py-1.5 font-sans text-slate-600">{p.description || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Code Snippets */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs">
                {(["curl", "python", "typescript"] as const).map((lang) => (
                  <button
                    key={lang}
                    type="button"
                    onClick={() => setCodeLanguage(lang)}
                    className={`px-2.5 py-1 rounded font-medium capitalize cursor-pointer transition-all ${
                      codeLanguage === lang
                        ? "bg-white text-slate-900 shadow-xs"
                        : "text-slate-600 hover:text-slate-900"
                    }`}
                  >
                    {lang === "typescript" ? "TypeScript (Fetch)" : lang === "python" ? "Python (Requests)" : "cURL"}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={handleCopyCode}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium cursor-pointer shadow-2xs"
                aria-label="Copy code snippet"
              >
                {copiedCode ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
                    <span className="text-emerald-700 font-semibold">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
                    <span>Copy Snippet</span>
                  </>
                )}
              </button>
            </div>

            <pre className="p-3.5 rounded-xl bg-slate-900 text-slate-100 font-mono text-xs overflow-x-auto leading-relaxed border border-slate-800">
              <code>{generateSnippet(selectedEndpoint, codeLanguage)}</code>
            </pre>
          </div>

          {/* Response Schema Sample */}
          {selectedEndpoint.responseSample !== undefined && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                Sample Verified Response (200 OK)
              </h5>
              <JsonViewer data={selectedEndpoint.responseSample} title="Response Body" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
