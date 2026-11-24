"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { Scanner } from "../scan/scanner";

export default function Workspace() {
  const [user, setUser] = useState<{ name?: string; email?: string } | null>(null);
  const { loginWithToken } = useAuth();
  const router = useRouter();
  const [platformError, setPlatformError] = useState("");
  const [opening, setOpening] = useState(false);
  async function openDashboard() {
    setOpening(true);
    setPlatformError("");
    try {
      const response = await fetch("/api/platform-session", { method: "POST" });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not open the dashboard.");
      await loginWithToken(result.access_token);
      router.push("/dashboard/");
    } catch (error) {
      setPlatformError(error instanceof Error ? error.message : "Could not reach the review backend.");
      setOpening(false);
    }
  }
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
  if (user) return <>
    {process.env.NEXT_PUBLIC_API_URL && <section className="queue-workspace scanner-shell px-5 pt-4 sm:px-8">
      <button className="queue-primary" disabled={opening} onClick={openDashboard}>{opening ? "Opening dashboard…" : "Open full review dashboard"}</button>
      {platformError && <p role="alert" className="mt-2 text-rose-300">{platformError}</p>}
    </section>}
    <Scanner workspaceUser={user} />
  </>;
  return <main className="queue-workspace scanner-shell p-8">
    <h1 className="text-3xl font-semibold">Review workspace</h1>
    <p className="my-4" role="status">{failed ? "Could not check your session." : "Checking your session…"}</p>
    {failed && <Link href="/login/" className="queue-secondary">Return to sign in</Link>}
  </main>;
}
