"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteAccount, getSettings, updateSettings } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { LANGUAGES } from "@/lib/types";
import type { AppSettings } from "@/lib/types";

const MODELS = ["gemini-flash-latest", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.1-pro"];

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className={`h-6 w-11 rounded-full transition-colors ${checked ? "bg-primary" : "bg-muted"}`}
    >
      <span
        className={`block h-5 w-5 translate-y-0.5 rounded-full bg-white transition-transform ${
          checked ? "translate-x-5" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

export default function SettingsPage() {
  const { logout } = useAuth();
  const router = useRouter();
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    getSettings().then(setSettings).catch(() => setError("Couldn't load settings."));
  }, []);

  async function patch(update: Partial<AppSettings>) {
    if (!settings) return;
    setSettings({ ...settings, ...update }); // optimistic
    setSaving(true);
    try {
      const saved = await updateSettings(update);
      setSettings(saved);
    } catch {
      setError("Couldn't save that change.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteAccount();
      logout();
      router.replace("/");
    } catch {
      setError("Couldn't delete account data.");
      setDeleting(false);
    }
  }

  if (!settings) {
    return (
      <div className="flex h-40 items-center justify-center text-muted-foreground">
        {error ?? <Loader2 className="h-5 w-5 animate-spin" />}
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight">Settings</h1>
          <p className="text-sm text-muted-foreground">Preferences for how CodeGuard AI behaves.</p>
        </div>
        {saving && <span className="text-xs text-muted-foreground">Saving…</span>}
      </div>

      <Card className="mb-5">
        <CardHeader><CardTitle>Preferences</CardTitle></CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Dark mode</p>
              <p className="text-xs text-muted-foreground">CodeGuard AI is dark-mode-first by design.</p>
            </div>
            <Toggle checked={settings.dark_mode} onChange={(v) => patch({ dark_mode: v })} />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Email notifications</p>
              <p className="text-xs text-muted-foreground">Get notified when a long-running scan finishes.</p>
            </div>
            <Toggle checked={settings.email_notifications} onChange={(v) => patch({ email_notifications: v })} />
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm">Preferred AI model</p>
            <select
              value={settings.preferred_ai_model}
              onChange={(e) => patch({ preferred_ai_model: e.target.value })}
              className="rounded-lg border border-border bg-muted px-3 py-1.5 text-sm outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary/40"
            >
              {MODELS.map((m) => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>

          <div className="flex items-center justify-between">
            <p className="text-sm">Default language</p>
            <select
              value={settings.preferred_language}
              onChange={(e) => patch({ preferred_language: e.target.value })}
              className="rounded-lg border border-border bg-muted px-3 py-1.5 text-sm outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary/40"
            >
              {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
            </select>
          </div>
        </CardContent>
      </Card>

      <Card className="border-red-500/30">
        <CardHeader><CardTitle>Danger zone</CardTitle></CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm">Delete account data</p>
              <p className="text-xs text-muted-foreground">Permanently deletes all locally stored reviews and settings.</p>
            </div>
            {!confirmDelete ? (
              <Button variant="outline" size="sm" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="h-4 w-4" /> Delete
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>Cancel</Button>
                <Button variant="default" size="sm" onClick={handleDelete} disabled={deleting} className="bg-red-600 hover:bg-red-500">
                  {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirm delete"}
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
