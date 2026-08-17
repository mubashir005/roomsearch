"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { SearchRun } from "@/lib/types";

export default function SearchNowButton() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleClick() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const run = await api.triggerSearch();
      setResult(run);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <button
        onClick={handleClick}
        disabled={loading}
        className="inline-flex items-center justify-center gap-2 rounded-lg bg-white text-brand-700 text-sm font-semibold px-4 py-2.5 shadow-sm hover:bg-brand-50 disabled:opacity-60 w-fit transition-colors"
      >
        {loading ? (
          <>
            <span className="w-3.5 h-3.5 rounded-full border-2 border-brand-600 border-t-transparent animate-spin" />
            Searching all sources…
          </>
        ) : (
          <>🔍 Search Now</>
        )}
      </button>
      {error && <p className="text-sm text-rose-100 bg-rose-600/30 rounded px-2 py-1">{error}</p>}
      {result && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 text-sm shadow-sm">
          <div className="font-medium mb-2 text-gray-900">
            {result.total_discovered} total &middot; {result.total_matching} matches &middot; {result.total_new} new
            &middot; {result.total_duplicates_merged} duplicates merged
          </div>
          <ul className="space-y-1">
            {result.source_results.map((s: any, i: number) => (
              <li key={i} className="text-gray-600">
                {s.source}: {s.error ? `❌ ${s.error}` : `✓ ${s.found} listings (${s.new} new, ${s.matches} matches)`}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
