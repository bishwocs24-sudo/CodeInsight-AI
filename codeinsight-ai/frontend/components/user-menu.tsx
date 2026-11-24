"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, Settings, UserCircle } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function UserMenu({ email }: { email: string }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const { logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  function handleLogout() {
    setOpen(false);
    logout();
    router.push(process.env.NEXT_PUBLIC_HOSTED_GOOGLE === "1" ? "/login/" : "/");
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Account menu"
        aria-expanded={open}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary to-accent text-xs font-medium text-primary-foreground"
      >
        {(email[0] ?? "?").toUpperCase()}
      </button>

      {open && (
        <div className="absolute right-0 top-10 z-30 w-56 overflow-hidden rounded-xl border border-border bg-card shadow-xl">
          <div className="border-b border-border px-4 py-3">
            <p className="truncate text-sm">{email}</p>
          </div>
          <nav className="p-1.5">
            <Link
              href="/dashboard/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <UserCircle className="h-4 w-4" /> Profile
            </Link>
            <Link
              href="/dashboard/settings"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              <Settings className="h-4 w-4" /> Settings
            </Link>
            <button
              onClick={handleLogout}
              className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10"
            >
              <LogOut className="h-4 w-4" /> {process.env.NEXT_PUBLIC_HOSTED_GOOGLE === "1" ? "Account and sign out" : "Sign out"}
            </button>
          </nav>
        </div>
      )}
    </div>
  );
}
