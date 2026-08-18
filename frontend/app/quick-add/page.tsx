"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import ListingCard from "@/components/ListingCard";
import type { QuickAddResponse } from "@/lib/types";

export default function QuickAddPage() {
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QuickAddResponse | null>(null);

  async function submit() {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.quickAdd({ text, url: url.trim() || undefined });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add listing");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Quick Add</h1>
        <p className="text-sm text-gray-500 mt-1">
          Found something yourself — via ChatGPT, WG-Gesucht, a friend&apos;s tip, anywhere? Paste what you know
          below. It runs through the same scoring, duplicate-detection, and notification pipeline as every
          automated source.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 flex flex-col gap-3">
        <label className="flex flex-col gap-1 text-sm">
          Listing text
          <textarea
            className="border rounded-md px-3 py-2 min-h-[160px] text-sm"
            placeholder={
              "Paste the listing description here, e.g.:\n\n1-Zimmer-Wohnung in Hannover-List, Warmmiete 480 €, 32 m², möbliert, eigenes Bad, Anmeldung möglich..."
            }
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          Source link (optional, but recommended)
          <input
            className="border rounded-md px-3 py-2"
            placeholder="https://www.wg-gesucht.de/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </label>
        <button
          onClick={submit}
          disabled={loading || !text.trim()}
          className="inline-flex items-center justify-center rounded-md bg-brand-600 text-white text-sm font-medium px-4 py-2 hover:bg-brand-700 disabled:opacity-50 w-fit"
        >
          {loading ? "Adding…" : "Add listing"}
        </button>
        {error && <p className="text-sm text-rose-600">{error}</p>}
      </div>

      {result && (
        <div className="flex flex-col gap-3">
          <div className="text-sm text-gray-600">
            {result.is_new ? (
              <span className="text-emerald-700 font-medium">✓ Added as a new listing.</span>
            ) : (
              <span className="text-amber-700 font-medium">
                ↻ Matched an existing listing — merged as another source instead of duplicating.
              </span>
            )}
            {result.used_ai_fallback && result.ai_fields_filled.length > 0 && (
              <span className="ml-2 text-gray-500">
                AI filled in: {result.ai_fields_filled.join(", ")}
              </span>
            )}
          </div>
          <ListingCard listing={result.listing} />
        </div>
      )}
    </div>
  );
}
