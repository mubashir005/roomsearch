"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import ListingCard from "@/components/ListingCard";
import type { Listing } from "@/lib/types";

const DISTRICTS = [
  "List", "Vahrenwald", "Vahrenwald-List", "Nordstadt", "Oststadt", "Südstadt", "Mitte",
  "Linden", "Linden-Mitte", "Linden-Nord", "Linden-Süd", "Calenberger Neustadt",
  "Herrenhausen", "Hainholz", "Bothfeld", "Döhren", "Garbsen", "Langenhagen", "Laatzen", "Seelze",
];

export default function ListingsPage() {
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const [priceMax, setPriceMax] = useState(500);
  const [rentType, setRentType] = useState("");
  const [sizeMin, setSizeMin] = useState("");
  const [sizeMax, setSizeMax] = useState("");
  const [district, setDistrict] = useState("");
  const [furnished, setFurnished] = useState("");
  const [anmeldung, setAnmeldung] = useState("");
  const [kitchen, setKitchen] = useState("");
  const [bathroom, setBathroom] = useState("");
  const [balcony, setBalcony] = useState("");
  const [longTerm, setLongTerm] = useState("");
  const [matchScoreMin, setMatchScoreMin] = useState("");
  const [onlyNew, setOnlyNew] = useState(false);
  const [onlyUnseen, setOnlyUnseen] = useState(false);
  const [sort, setSort] = useState("match_score_desc");

  useEffect(() => {
    setLoading(true);
    api
      .getListings({
        price_max: priceMax,
        rent_type: rentType || undefined,
        size_min: sizeMin || undefined,
        size_max: sizeMax || undefined,
        district: district || undefined,
        furnished: furnished || undefined,
        anmeldung: anmeldung || undefined,
        kitchen: kitchen || undefined,
        bathroom: bathroom || undefined,
        balcony: balcony || undefined,
        long_term: longTerm || undefined,
        match_score_min: matchScoreMin || undefined,
        only_new: onlyNew,
        only_unseen: onlyUnseen,
        sort,
        limit: 60,
      })
      .then((r) => {
        setListings(r.items);
        setTotal(r.total);
      })
      .finally(() => setLoading(false));
  }, [priceMax, rentType, sizeMin, sizeMax, district, furnished, anmeldung, kitchen, bathroom, balcony, longTerm, matchScoreMin, onlyNew, onlyUnseen, sort]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-xl font-bold text-gray-900">Listings <span className="text-gray-400 font-normal">({total})</span></h1>
        <div className="flex gap-2">
          <a href="/api/listings/export/csv" className="text-sm px-3 py-1.5 bg-white border border-gray-200 rounded-md hover:bg-gray-50 shadow-sm">
            Export CSV
          </a>
          <a href="/api/listings/export/json" className="text-sm px-3 py-1.5 bg-white border border-gray-200 rounded-md hover:bg-gray-50 shadow-sm">
            Export JSON
          </a>
          <a href="/api/listings/export/csv?only_new=true" className="text-sm px-3 py-1.5 bg-white border border-gray-200 rounded-md hover:bg-gray-50 shadow-sm">
            Export new only
          </a>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 text-sm text-gray-700">
        <label className="flex flex-col gap-1">
          Max price: <span className="font-semibold text-gray-900">€{priceMax}</span>
          <input type="range" min={100} max={1000} step={10} value={priceMax} onChange={(e) => setPriceMax(Number(e.target.value))} />
        </label>
        <label className="flex flex-col gap-1">
          Rent type
          <select className="border rounded px-2 py-1" value={rentType} onChange={(e) => setRentType(e.target.value)}>
            <option value="">Any</option>
            <option value="warmmiete">Warmmiete</option>
            <option value="kaltmiete">Kaltmiete</option>
            <option value="unknown">Unknown</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Size min (m²)
          <input className="border rounded px-2 py-1" type="number" value={sizeMin} onChange={(e) => setSizeMin(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          Size max (m²)
          <input className="border rounded px-2 py-1" type="number" value={sizeMax} onChange={(e) => setSizeMax(e.target.value)} />
        </label>
        <label className="flex flex-col gap-1">
          District
          <select className="border rounded px-2 py-1" value={district} onChange={(e) => setDistrict(e.target.value)}>
            <option value="">Any</option>
            {DISTRICTS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Furnished
          <select className="border rounded px-2 py-1" value={furnished} onChange={(e) => setFurnished(e.target.value)}>
            <option value="">Any</option>
            <option value="furnished">Furnished</option>
            <option value="partially_furnished">Partially</option>
            <option value="unfurnished">Unfurnished</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Anmeldung
          <select className="border rounded px-2 py-1" value={anmeldung} onChange={(e) => setAnmeldung(e.target.value)}>
            <option value="">Any</option>
            <option value="possible">Possible</option>
            <option value="unknown">Unknown</option>
            <option value="impossible">Impossible</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Kitchen
          <select className="border rounded px-2 py-1" value={kitchen} onChange={(e) => setKitchen(e.target.value)}>
            <option value="">Any</option>
            <option value="true">Private</option>
            <option value="false">Shared</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Bathroom
          <select className="border rounded px-2 py-1" value={bathroom} onChange={(e) => setBathroom(e.target.value)}>
            <option value="">Any</option>
            <option value="true">Private</option>
            <option value="false">Shared</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Balcony
          <select className="border rounded px-2 py-1" value={balcony} onChange={(e) => setBalcony(e.target.value)}>
            <option value="">Any</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Rental
          <select className="border rounded px-2 py-1" value={longTerm} onChange={(e) => setLongTerm(e.target.value)}>
            <option value="">Any</option>
            <option value="true">Long-term</option>
            <option value="false">Temporary</option>
          </select>
        </label>
        <label className="flex flex-col gap-1">
          Min match score
          <input className="border rounded px-2 py-1" type="number" value={matchScoreMin} onChange={(e) => setMatchScoreMin(e.target.value)} />
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={onlyNew} onChange={(e) => setOnlyNew(e.target.checked)} /> Only new
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={onlyUnseen} onChange={(e) => setOnlyUnseen(e.target.checked)} /> Only unseen
        </label>
        <label className="flex flex-col gap-1">
          Sort
          <select className="border rounded px-2 py-1" value={sort} onChange={(e) => setSort(e.target.value)}>
            <option value="match_score_desc">Best match</option>
            <option value="newest">Newest</option>
            <option value="price_asc">Price: low to high</option>
            <option value="price_desc">Price: high to low</option>
          </select>
        </label>
      </div>

      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="bg-white border border-gray-200 rounded-xl overflow-hidden animate-pulse">
              <div className="aspect-[4/3] bg-gray-100 m-2 rounded-lg" />
              <div className="p-4 flex flex-col gap-2">
                <div className="h-4 bg-gray-100 rounded w-3/4" />
                <div className="h-5 bg-gray-100 rounded w-1/3" />
                <div className="h-3 bg-gray-100 rounded w-1/2" />
              </div>
            </div>
          ))}
        </div>
      ) : listings.length === 0 ? (
        <div className="bg-white border border-dashed border-gray-300 rounded-xl p-10 text-center">
          <p className="text-gray-500 text-sm">No listings match these filters. Try widening your criteria.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </div>
  );
}
