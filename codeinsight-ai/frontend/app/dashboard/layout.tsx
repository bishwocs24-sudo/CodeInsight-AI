"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useEffect } from "react";
import {
  LayoutDashboard,
  FilePlus2,
  History,
  Github,
  BarChart3,
  Settings,
  User,
  Sparkles,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { UserMenu } from "@/components/user-menu";
import { NotificationsMenu } from "@/components/notifications-menu";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/new-review", label: "New Review", icon: FilePlus2 },
  { href: "/dashboard/history", label: "History", icon: History },
  { href: "/dashboard/github", label: "GitHub", icon: Github },
  { href: "/dashboard/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      router.push("/login");
    }
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 flex-col border-r border-border px-4 py-6 md:flex">
        <Link href="/" className="mb-8 flex items-center gap-2 px-2 font-display font-semibold tracking-tight">
          <Sparkles className="h-5 w-5 text-primary" />
          CodeInsight AI
        </Link>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
                  active
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <Link
          href="/dashboard/profile"
          className={cn(
            "flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors",
            pathname === "/dashboard/profile"
              ? "bg-muted text-foreground"
              : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
          )}
        >
          <User className="h-4 w-4" />
          Profile
        </Link>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-border px-6 py-4">
          <span className="text-sm text-muted-foreground">{user.email}</span>
          <div className="flex items-center gap-2">
            <NotificationsMenu />
            <UserMenu email={user.email} />
          </div>
        </header>
        <main className="flex-1 px-6 py-8 md:px-10">{children}</main>
      </div>
    </div>
  );
}
