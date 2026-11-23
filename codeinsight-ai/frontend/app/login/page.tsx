"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Github, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { ApiError, getAuthOptions, type AuthOptions } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const inputClass =
  "w-full rounded-xl border border-border bg-muted px-3 py-2.5 text-sm outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary/40";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [options, setOptions] = useState<AuthOptions | null>(null);

  useEffect(() => {
    getAuthOptions().then(setOptions).catch(() => {});
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't sign in.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center px-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,hsl(var(--primary)/0.12),transparent)]" />
      <div className="relative w-full max-w-sm">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2 font-display font-semibold tracking-tight">
          <Sparkles className="h-5 w-5 text-primary" />
          CodeGuard AI
        </Link>
        <Card className="shadow-2xl shadow-black/30">
          <CardContent className="p-6">
            <h1 className="mb-1 font-display text-lg font-semibold">Sign in</h1>
            <p className="mb-6 text-sm text-muted-foreground">Welcome back.</p>
            {options?.github && (
              <>
                <a href={`${API_URL}/auth/github/login`} className="queue-secondary mb-4 w-full">
                  <Github className="h-4 w-4" aria-hidden /> Continue with GitHub
                </a>
                <div className="mb-4 flex items-center gap-3 text-xs text-muted-foreground">
                  <div className="h-px flex-1 bg-border" /> or <div className="h-px flex-1 bg-border" />
                </div>
              </>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs text-muted-foreground">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={inputClass}
                  placeholder="you@example.com"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs text-muted-foreground">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputClass}
                  placeholder="••••••••"
                />
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Sign in"}
              </Button>
            </form>
            {options?.signup && (
              <p className="mt-5 text-center text-sm text-muted-foreground">
                Don&apos;t have an account?{" "}
                <Link href="/signup" className="text-foreground underline underline-offset-4">
                  Sign up
                </Link>
              </p>
            )}
            <Link href="/demo" className="mt-4 block text-center text-sm text-teal-300 hover:underline">
              Try sample review
            </Link>
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
