"use client";

import { useEffect, useRef, useState } from "react";
import { Bell, BellOff } from "lucide-react";

export function NotificationsMenu() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Notifications"
        aria-expanded={open}
        className="rounded-lg p-2 text-muted-foreground hover:bg-muted hover:text-foreground"
      >
        <Bell className="h-4 w-4" />
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-30 w-64 overflow-hidden rounded-xl border border-border bg-card shadow-xl">
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-medium">Notifications</p>
          </div>
          <div className="flex flex-col items-center gap-2 px-4 py-8 text-center">
            <BellOff className="h-5 w-5 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              You&apos;re all caught up. Notifications for finished scans arrive here once enabled.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
