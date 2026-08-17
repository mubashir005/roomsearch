import { api } from "@/lib/api";

export default async function RunHistoryPage() {
  const runs = await api.getRunHistory();

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-xl font-semibold">Run History</h1>
      <div className="flex flex-col gap-3">
        {runs.length === 0 && <p className="text-gray-500 text-sm">No search runs yet.</p>}
        {runs.map((run) => (
          <div key={run.id} className="bg-white border border-gray-200 rounded-lg p-4 text-sm">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="font-medium">
                {new Date(run.started_at).toLocaleString("de-DE")}
                <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-gray-100 text-gray-500 uppercase">{run.trigger}</span>
              </div>
              <div className="text-gray-600">
                {run.total_discovered} discovered &middot; {run.total_parsed} parsed &middot; {run.total_matching} matching
                &middot; {run.total_new} new &middot; {run.total_duplicates_merged} duplicates merged
              </div>
            </div>
            <ul className="mt-2 grid sm:grid-cols-2 lg:grid-cols-3 gap-1 text-gray-600">
              {run.source_results.map((s: any, i: number) => (
                <li key={i}>
                  {s.error ? `❌ ${s.source}: ${s.error}` : `✓ ${s.source}: ${s.found} found, ${s.new} new, ${s.matches} matches`}
                </li>
              ))}
            </ul>
            {run.errors.length > 0 && (
              <div className="mt-2 text-red-600">
                {run.errors.map((e: any, i: number) => (
                  <p key={i}>⚠ {e.source}: {e.error}</p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
