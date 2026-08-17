"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Source } from "@/lib/types";

function statusBadge(status: string) {
  const map: Record<string, string> = {
    ok: "bg-green-100 text-green-800",
    limited: "bg-yellow-100 text-yellow-800",
    error: "bg-red-100 text-red-800",
    disabled: "bg-gray-100 text-gray-500",
  };
  const emoji: Record<string, string> = { ok: "🟢", limited: "🟡", error: "🔴", disabled: "⚪" };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${map[status] || map.disabled}`}>
      {emoji[status] || "⚪"} {status.toUpperCase()}
    </span>
  );
}

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, string>>({});

  function load() {
    api.getSources().then(setSources);
  }

  useEffect(load, []);

  async function toggle(source: Source) {
    setBusy(source.key);
    try {
      await api.updateSource(source.key, { enabled: !source.enabled });
      load();
    } catch (e) {
      setMessages((m) => ({ ...m, [source.key]: e instanceof Error ? e.message : "Failed to update" }));
    } finally {
      setBusy(null);
    }
  }

  async function test(source: Source) {
    setBusy(source.key);
    try {
      const result = await api.testSource(source.key);
      setMessages((m) => ({ ...m, [source.key]: JSON.stringify(result) }));
      load();
    } finally {
      setBusy(null);
    }
  }

  async function runNow(source: Source) {
    setBusy(source.key);
    try {
      const result = await api.runSource(source.key);
      setMessages((m) => ({ ...m, [source.key]: JSON.stringify(result) }));
      load();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-bold text-gray-900">Sources</h1>
      <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Last success</th>
              <th className="px-4 py-3">Last error</th>
              <th className="px-4 py-3">Found</th>
              <th className="px-4 py-3">Matches</th>
              <th className="px-4 py-3">Response</th>
              <th className="px-4 py-3">Priority</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s) => (
              <tr key={s.key} className="border-t border-gray-100 hover:bg-gray-50/60 transition-colors">
                <td className="px-4 py-3 font-medium text-gray-900">
                  {s.name}
                  {s.unavailable_reason && (
                    <p className="text-xs text-gray-400 mt-0.5 max-w-xs font-normal">{s.unavailable_reason}</p>
                  )}
                </td>
                <td className="px-4 py-3">{statusBadge(s.status)}</td>
                <td className="px-4 py-3 text-xs">{s.last_success_at ? new Date(s.last_success_at).toLocaleString("de-DE") : "—"}</td>
                <td className="px-4 py-3 text-xs text-red-600 max-w-xs truncate" title={s.last_error || ""}>{s.last_error || "—"}</td>
                <td className="px-4 py-3">{s.last_listings_found}</td>
                <td className="px-4 py-3">{s.last_matching_found}</td>
                <td className="px-4 py-3">{s.last_response_time_ms != null ? `${s.last_response_time_ms}ms` : "—"}</td>
                <td className="px-4 py-3">{s.priority}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2 flex-wrap">
                    <button
                      disabled={busy === s.key || (!s.enabled && !!s.unavailable_reason)}
                      onClick={() => toggle(s)}
                      className="text-xs px-2 py-1 border rounded hover:bg-gray-100 disabled:opacity-40"
                    >
                      {s.enabled ? "Disable" : "Enable"}
                    </button>
                    <button disabled={busy === s.key} onClick={() => test(s)} className="text-xs px-2 py-1 border rounded hover:bg-gray-100">
                      Test
                    </button>
                    <button disabled={busy === s.key || !s.enabled} onClick={() => runNow(s)} className="text-xs px-2 py-1 border rounded hover:bg-gray-100 disabled:opacity-40">
                      Run now
                    </button>
                  </div>
                  {messages[s.key] && <p className="text-xs text-gray-500 mt-1 max-w-xs truncate">{messages[s.key]}</p>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
