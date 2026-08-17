"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SearchProfile } from "@/lib/types";

const EMPTY: Partial<SearchProfile> = {
  name: "",
  active: true,
  city: "Hannover",
  max_rent_warm: 500,
  preferred_size_min: 20,
  preferred_size_max: 50,
  max_rooms: 1,
  anmeldung_preference: "preferred",
  notification_mode: "immediate",
  email_enabled: true,
  telegram_enabled: false,
  min_score_to_notify: 50,
};

export default function SearchProfilesPage() {
  const [profiles, setProfiles] = useState<SearchProfile[]>([]);
  const [form, setForm] = useState<Partial<SearchProfile>>(EMPTY);
  const [editingId, setEditingId] = useState<number | null>(null);

  function load() {
    api.getSearchProfiles().then(setProfiles);
  }

  useEffect(load, []);

  async function submit() {
    if (editingId) {
      await api.updateSearchProfile(editingId, form);
    } else {
      await api.createSearchProfile(form);
    }
    setForm(EMPTY);
    setEditingId(null);
    load();
  }

  function edit(p: SearchProfile) {
    setForm(p);
    setEditingId(p.id);
  }

  async function remove(id: number) {
    await api.deleteSearchProfile(id);
    load();
  }

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold">Search Profiles</h1>

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {profiles.map((p) => (
          <div key={p.id} className="bg-white border border-gray-200 rounded-lg p-4 flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{p.name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded ${p.active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                {p.active ? "Active" : "Inactive"}
              </span>
            </div>
            <p className="text-sm text-gray-600">Location: {p.city}</p>
            <p className="text-sm text-gray-600">Max warm: €{p.max_rent_warm}</p>
            <p className="text-sm text-gray-600">Rooms: ≤{p.max_rooms}</p>
            <p className="text-sm text-gray-600">Anmeldung: {p.anmeldung_preference}</p>
            <p className="text-sm text-gray-600">Notify at score ≥ {p.min_score_to_notify}, mode: {p.notification_mode}</p>
            <div className="flex gap-2 mt-2">
              <button onClick={() => edit(p)} className="text-xs px-2 py-1 border rounded hover:bg-gray-100">Edit</button>
              <button onClick={() => remove(p.id)} className="text-xs px-2 py-1 border rounded hover:bg-gray-100 text-red-600">Delete</button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4 max-w-xl">
        <h2 className="font-semibold mb-3">{editingId ? "Edit profile" : "New profile"}</h2>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <label className="flex flex-col gap-1 col-span-2">
            Name
            <input className="border rounded px-2 py-1" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label className="flex flex-col gap-1">
            City
            <input className="border rounded px-2 py-1" value={form.city || ""} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          </label>
          <label className="flex flex-col gap-1">
            Max warm rent (€)
            <input type="number" className="border rounded px-2 py-1" value={form.max_rent_warm ?? 500} onChange={(e) => setForm({ ...form, max_rent_warm: Number(e.target.value) })} />
          </label>
          <label className="flex flex-col gap-1">
            Preferred size min (m²)
            <input type="number" className="border rounded px-2 py-1" value={form.preferred_size_min ?? 20} onChange={(e) => setForm({ ...form, preferred_size_min: Number(e.target.value) })} />
          </label>
          <label className="flex flex-col gap-1">
            Preferred size max (m²)
            <input type="number" className="border rounded px-2 py-1" value={form.preferred_size_max ?? 50} onChange={(e) => setForm({ ...form, preferred_size_max: Number(e.target.value) })} />
          </label>
          <label className="flex flex-col gap-1">
            Max rooms
            <input type="number" className="border rounded px-2 py-1" value={form.max_rooms ?? 1} onChange={(e) => setForm({ ...form, max_rooms: Number(e.target.value) })} />
          </label>
          <label className="flex flex-col gap-1">
            Min score to notify
            <input type="number" className="border rounded px-2 py-1" value={form.min_score_to_notify ?? 50} onChange={(e) => setForm({ ...form, min_score_to_notify: Number(e.target.value) })} />
          </label>
          <label className="flex flex-col gap-1">
            Notification mode
            <select className="border rounded px-2 py-1" value={form.notification_mode || "immediate"} onChange={(e) => setForm({ ...form, notification_mode: e.target.value })}>
              <option value="immediate">Immediate</option>
              <option value="hourly_digest">Hourly digest</option>
              <option value="daily_digest">Daily digest</option>
            </select>
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={form.active ?? true} onChange={(e) => setForm({ ...form, active: e.target.checked })} /> Active
          </label>
        </div>
        <div className="flex gap-2 mt-4">
          <button onClick={submit} className="px-3 py-1.5 bg-brand-600 text-white rounded-md text-sm hover:bg-brand-700">
            {editingId ? "Save changes" : "Create profile"}
          </button>
          {editingId && (
            <button onClick={() => { setForm(EMPTY); setEditingId(null); }} className="px-3 py-1.5 border rounded-md text-sm">
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
