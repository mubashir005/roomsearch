"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { NotificationLogEntry } from "@/lib/types";

export default function NotificationsPage() {
  const [items, setItems] = useState<NotificationLogEntry[]>([]);

  function load() {
    api.getNotifications().then(setItems);
  }

  useEffect(load, []);

  async function markAllRead() {
    await api.markAllNotificationsRead();
    load();
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Notifications</h1>
        <button onClick={markAllRead} className="text-sm px-3 py-1.5 border rounded-md hover:bg-gray-100">
          Mark all read
        </button>
      </div>
      <div className="flex flex-col gap-2">
        {items.length === 0 && <p className="text-gray-500 text-sm">No notifications yet.</p>}
        {items.map((n) => (
          <div
            key={n.id}
            className={`bg-white border rounded-lg p-3 text-sm flex items-start justify-between gap-4 ${
              n.read ? "border-gray-200" : "border-brand-300"
            }`}
          >
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 uppercase text-gray-500">{n.channel}</span>
                {!n.success && <span className="text-xs text-red-600">failed</span>}
                <span className="font-medium">{n.subject || "Notification"}</span>
              </div>
              {n.body_preview && <p className="text-gray-600 mt-1">{n.body_preview}</p>}
              {n.error && <p className="text-red-600 mt-1">{n.error}</p>}
            </div>
            <div className="flex flex-col items-end gap-1">
              <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString("de-DE")}</span>
              {!n.read && (
                <button
                  onClick={() => api.markNotificationRead(n.id).then(load)}
                  className="text-xs text-brand-700 hover:underline"
                >
                  Mark read
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
