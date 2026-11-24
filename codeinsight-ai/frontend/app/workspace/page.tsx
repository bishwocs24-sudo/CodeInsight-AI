"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Scanner } from "../scan/scanner";

export default function Workspace() {
  const [user, setUser] = useState<{ name?: string; email?: string } | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/auth/session", { cache: "no-store", signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error();
        const session = await response.json();
        if (session?.user?.email) setUser(session.user);
        else window.location.replace("/login/");
      })
      .catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => controller.abort();
  }, []);
  if (user) return <Scanner workspaceUser={user} />;
  return <main className="queue-workspace scanner-shell p-8">
    <h1 className="text-3xl font-semibold">Review workspace</h1>
    <p className="my-4" role="status">{failed ? "Could not check your session." : "Checking your session…"}</p>
    {failed && <Link href="/login/" className="queue-secondary">Return to sign in</Link>}
  </main>;
}
