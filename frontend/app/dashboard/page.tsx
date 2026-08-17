import { api } from "@/lib/api";
import StatTile from "@/components/StatTile";
import SearchNowButton from "@/components/SearchNowButton";
import ListingCard from "@/components/ListingCard";

export default async function DashboardPage() {
  const [stats, topListings] = await Promise.all([
    api.getDashboardStats(),
    api.getListings({ limit: 6, sort: "match_score_desc" }),
  ]);

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-700 text-white p-6 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Hannover apartment search</h1>
          <p className="text-brand-100 text-sm mt-1">
            Checking WG-Gesucht-style sources every hour · {stats.sources_online}/{stats.sources_total} sources online
          </p>
        </div>
        <SearchNowButton />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <StatTile label="New Today" value={stats.new_today} icon="🆕" accent="rose" />
        <StatTile label="High Priority" value={stats.high_priority} icon="⭐" accent="amber" />
        <StatTile label="Under €400" value={stats.under_400} icon="💶" accent="emerald" />
        <StatTile label="€400–€500" value={stats.between_400_and_500} icon="💰" accent="emerald" />
        <StatTile label="Anmeldung OK" value={stats.anmeldung_confirmed} icon="📝" accent="brand" />
        <StatTile label="Furnished" value={stats.furnished} icon="🛋" accent="brand" />
        <StatTile label="Unseen" value={stats.unseen} icon="👀" accent="gray" />
        <StatTile label="Sources Online" value={`${stats.sources_online}/${stats.sources_total}`} icon="🔌" accent="gray" />
      </div>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-900">Top matches</h2>
          <a href="/listings" className="text-sm text-brand-600 hover:underline font-medium">
            View all →
          </a>
        </div>
        {topListings.items.length === 0 ? (
          <div className="bg-white border border-dashed border-gray-300 rounded-xl p-10 text-center">
            <p className="text-gray-500 text-sm">
              No listings yet. Click &quot;Search Now&quot; to run the search pipeline, or wait for the next hourly run.
            </p>
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {topListings.items.map((listing) => (
              <ListingCard key={listing.id} listing={listing} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
