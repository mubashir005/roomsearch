"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const LINKS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/listings", label: "Listings" },
  { href: "/sources", label: "Sources" },
  { href: "/search-profiles", label: "Search Profiles" },
  { href: "/notifications", label: "Notifications" },
  { href: "/settings", label: "Settings" },
  { href: "/run-history", label: "Run History" },
];

export default function Nav() {
  const pathname = usePathname();
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .getUnreadCount()
        .then((r) => {
          if (!cancelled) setUnread(r.unread);
        })
        .catch(() => {});
    };
    load();
    const interval = setInterval(load, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <nav className="bg-white/90 backdrop-blur-sm border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-14 gap-4">
          <Link href="/dashboard" className="font-bold text-gray-900 flex items-center gap-2 shrink-0">
            <span className="w-7 h-7 rounded-lg bg-brand-600 text-white flex items-center justify-center text-sm">🏠</span>
            <span className="hidden sm:inline">RoomSearch Hannover</span>
          </Link>
          <div className="flex items-center gap-0.5 overflow-x-auto">
            {LINKS.map((link) => {
              const active = pathname?.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`relative px-3 py-2 text-sm rounded-md whitespace-nowrap transition-colors ${
                    active ? "bg-brand-50 text-brand-700 font-semibold" : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  {link.label}
                  {link.href === "/notifications" && unread > 0 && (
                    <span className="ml-1.5 inline-flex items-center justify-center rounded-full bg-rose-500 text-white text-[11px] font-semibold w-5 h-5">
                      {unread}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
