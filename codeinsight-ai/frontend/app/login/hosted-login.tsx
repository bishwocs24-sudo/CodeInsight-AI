"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Github, ShieldCheck } from "lucide-react";

type User = { name?: string | null; email?: string | null };
type LoginStatus = "loading" | "ready" | "unavailable";
const authPath = "/api/auth";

async function getJson<T>(resource: string): Promise<T> {
  const response = await fetch(`${authPath}/${resource}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Authentication request failed");
  return response.json();
}

export function HostedLogin() {
  const [status, setStatus] = useState<LoginStatus>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    if (new URLSearchParams(window.location.search).has("error")) {
      setError("GitHub sign-in could not be completed. Try again.");
    }

    Promise.all([
      getJson<{ github?: unknown }>("providers"),
      getJson<{ user?: User } | null>("session"),
    ]).then(([providers, session]) => {
      if (!mounted) return;
      setStatus(providers.github ? "ready" : "unavailable");
      setUser(session?.user ?? null);
    }).catch(() => {
      if (mounted) setStatus("unavailable");
    });
    return () => { mounted = false; };
  }, []);

  async function submit(action: "signin/github" | "signout") {
    setBusy(true);
    setError("");
    try {
      const { csrfToken } = await getJson<{ csrfToken?: string }>("csrf");
      if (!csrfToken) throw new Error("Missing CSRF token");
      const form = document.createElement("form");
      form.method = "post";
      form.action = `${authPath}/${action}`;
      for (const [name, value] of Object.entries({ csrfToken, callbackUrl: "/login/" })) {
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name;
        input.value = value;
        form.appendChild(input);
      }
      document.body.appendChild(form);
      form.submit();
    } catch {
      setError("Could not connect to GitHub sign-in. Try again.");
      setBusy(false);
    }
  }

  return (
    <main className="queue-workspace flex min-h-screen max-w-lg flex-col justify-center px-5 py-10">
      <Link href="/" className="mb-5 flex w-fit items-center gap-2 font-semibold">
        <ShieldCheck size={21} className="text-teal-300" aria-hidden /> CodeGuard AI
      </Link>
      <section className="queue-hero !block">
        <h1>{user ? "Your account" : "Sign in to CodeGuard"}</h1>
        {user ? (
          <>
            <p>Signed in with GitHub as {user.name || user.email || "a GitHub user"}.</p>
            <button className="queue-secondary mt-5" type="button" disabled={busy}
              onClick={() => submit("signout")}>
              {busy ? "Signing out…" : "Sign out"}
            </button>
          </>
        ) : (
          <>
            <p>Use your GitHub account to sign in.</p>
            <button className="queue-primary mt-5" type="button" disabled={status !== "ready" || busy}
              onClick={() => submit("signin/github")}>
              <Github size={17} aria-hidden /> {busy ? "Opening GitHub…" : "Continue with GitHub"}
            </button>
            <p role="status">
              {status === "loading" && "Checking GitHub sign-in…"}
              {status === "unavailable" && "GitHub sign-in is unavailable until the deployment is configured."}
            </p>
          </>
        )}
        {error && <p role="alert" className="!text-rose-300">{error}</p>}
      </section>
      <Link className="queue-link w-fit text-sm" href="/demo">Open the public sample review</Link>
    </main>
  );
}
