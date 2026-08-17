import type {
  DashboardStats,
  Listing,
  ListingListResponse,
  NotificationLogEntry,
  SearchProfile,
  SearchRun,
  Source,
} from "./types";

// Server components run inside the Next.js server and call the backend
// directly with the (server-only) API key attached; client components go
// through the same-origin /api/* route handler in app/api/[...path]/route.ts,
// which forwards to the backend and attaches the key itself -- the browser
// never sees it.
function baseUrl(): string {
  if (typeof window === "undefined") {
    return process.env.BACKEND_URL || "http://localhost:8000";
  }
  return "";
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const isServer = typeof window === "undefined";
  const apiKey = isServer ? process.env.API_KEY : undefined;

  const res = await fetch(`${baseUrl()}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { "X-API-Key": apiKey } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getDashboardStats: () => apiFetch<DashboardStats>("/api/dashboard/stats"),
  getListings: (params: Record<string, string | number | boolean | undefined> = {}) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
    });
    return apiFetch<ListingListResponse>(`/api/listings?${qs.toString()}`);
  },
  getListing: (id: number) => apiFetch<Listing>(`/api/listings/${id}`),
  getSources: () => apiFetch<Source[]>("/api/sources"),
  updateSource: (key: string, payload: Partial<Pick<Source, "enabled" | "priority" | "config">>) =>
    apiFetch<Source>(`/api/sources/${key}`, { method: "PATCH", body: JSON.stringify(payload) }),
  testSource: (key: string) => apiFetch<Record<string, unknown>>(`/api/sources/${key}/test`, { method: "POST" }),
  runSource: (key: string) => apiFetch<Record<string, unknown>>(`/api/sources/${key}/run`, { method: "POST" }),
  getSearchProfiles: () => apiFetch<SearchProfile[]>("/api/search-profiles"),
  createSearchProfile: (payload: Partial<SearchProfile>) =>
    apiFetch<SearchProfile>("/api/search-profiles", { method: "POST", body: JSON.stringify(payload) }),
  updateSearchProfile: (id: number, payload: Partial<SearchProfile>) =>
    apiFetch<SearchProfile>(`/api/search-profiles/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteSearchProfile: (id: number) =>
    apiFetch<{ deleted: boolean }>(`/api/search-profiles/${id}`, { method: "DELETE" }),
  getRunHistory: () => apiFetch<SearchRun[]>("/api/run-history"),
  getNotifications: (unreadOnly = false) =>
    apiFetch<NotificationLogEntry[]>(`/api/notifications?unread_only=${unreadOnly}`),
  getUnreadCount: () => apiFetch<{ unread: number }>("/api/notifications/unread-count"),
  markNotificationRead: (id: number) =>
    apiFetch<{ ok: boolean }>(`/api/notifications/${id}/read`, { method: "POST" }),
  markAllNotificationsRead: () =>
    apiFetch<{ ok: boolean }>("/api/notifications/mark-all-read", { method: "POST" }),
  getSettings: () => apiFetch<Record<string, unknown>>("/api/settings"),
  triggerSearch: () => apiFetch<SearchRun>("/api/search/run", { method: "POST" }),
};
