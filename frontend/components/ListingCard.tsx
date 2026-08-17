import type { Listing } from "@/lib/types";
import ImageCarousel from "@/components/ImageCarousel";

function rentLabel(l: Listing): string {
  if (l.rent_warm == null) return "Warmmiete unknown";
  if (l.rent_warm_is_estimated) return `~€${Math.round(l.rent_warm)}`;
  return `€${Math.round(l.rent_warm)}`;
}

function fmtDate(iso: string | null): string {
  if (!iso) return "unknown";
  const d = new Date(iso);
  return d.toLocaleDateString("de-DE");
}

function scoreRing(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-500";
  return "bg-gray-400";
}

function featureChip(label: string, state: boolean | null | undefined): { text: string; className: string } {
  if (state === true) return { text: `${label} ✓`, className: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200" };
  if (state === false) return { text: `${label} shared`, className: "bg-gray-50 text-gray-500 ring-1 ring-gray-200" };
  return { text: `${label} ?`, className: "bg-gray-50 text-gray-400 ring-1 ring-gray-200" };
}

export default function ListingCard({ listing }: { listing: Listing }) {
  const sources = Array.from(new Set(listing.source_records.map((r) => r.source_key)));
  const isNew = listing.status === "NEW" || listing.status === "MATCHED";
  const bathroomChip = featureChip("Bath", listing.private_bathroom);
  const kitchenChip = featureChip("Kitchen", listing.private_kitchen);

  return (
    <div className="group bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all flex flex-col">
      <div className="relative p-2 pb-0">
        <ImageCarousel images={listing.images} alt={listing.title} />

        <div className="absolute top-4 left-4 flex items-center gap-1.5 flex-wrap">
          {isNew && (
            <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-bold bg-rose-600 text-white shadow-sm">
              NEW
            </span>
          )}
          {listing.anmeldung === "possible" && (
            <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-semibold bg-white/95 text-emerald-700 shadow-sm">
              Anmeldung ✓
            </span>
          )}
        </div>

        <div className="absolute top-4 right-4 flex items-center gap-1.5 rounded-full bg-white/95 shadow-sm pl-1.5 pr-2.5 py-1">
          <span className={`w-2 h-2 rounded-full ${scoreRing(listing.match_score)}`} />
          <span className="text-xs font-bold text-gray-800">{listing.match_score}%</span>
        </div>
      </div>

      <div className="flex flex-col gap-2.5 p-4 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="font-semibold text-gray-900 leading-snug line-clamp-2">{listing.title}</h3>
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-xl font-bold text-gray-900">{rentLabel(listing)}</span>
          <span className="text-xs text-gray-500">warm{listing.rent_warm_is_estimated ? " (est.)" : ""}</span>
        </div>

        <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm text-gray-600">
          {listing.size_sqm != null && <span>{listing.size_sqm} m²</span>}
          {listing.rooms != null && (
            <span>
              {listing.rooms} room{listing.rooms !== 1 ? "s" : ""}
            </span>
          )}
          <span className="font-medium text-gray-800">{listing.district || listing.city}</span>
        </div>

        <div className="text-sm text-gray-500">Available {fmtDate(listing.availability_date)}</div>

        <div className="flex flex-wrap gap-1.5 text-xs">
          <span className={`px-2 py-0.5 rounded-full ${bathroomChip.className}`}>{bathroomChip.text}</span>
          <span className={`px-2 py-0.5 rounded-full ${kitchenChip.className}`}>{kitchenChip.text}</span>
          {listing.furnished === "furnished" && (
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">Furnished</span>
          )}
          {listing.furnished === "partially_furnished" && (
            <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 ring-1 ring-amber-200">Part-furnished</span>
          )}
          {listing.balcony && (
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200">Balcony</span>
          )}
        </div>

        {listing.match_explanation?.length > 0 && (
          <details className="text-xs text-gray-600 mt-auto pt-1">
            <summary className="cursor-pointer select-none text-brand-700 font-medium">Why it matches</summary>
            <ul className="mt-1.5 space-y-0.5">
              {listing.match_explanation.map((line, i) => (
                <li key={i} className={line.startsWith("✓") ? "text-emerald-700" : "text-rose-600"}>
                  {line}
                </li>
              ))}
            </ul>
          </details>
        )}

        <div className="flex items-center justify-between pt-2 mt-1 border-t border-gray-100 text-xs text-gray-500">
          <span>
            Found on <span className="font-medium text-gray-700">{sources.join(" + ")}</span>
          </span>
          <a
            href={listing.canonical_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-brand-600 font-medium hover:underline"
          >
            View listing →
          </a>
        </div>
      </div>
    </div>
  );
}
