"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FilePlus2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAnalytics } from "@/lib/api";
import type { AnalyticsSummary } from "@/lib/types";

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .catch(() => setError("Couldn't reach the backend. Is it running on :8000?"));
  }, []);

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Your review activity at a glance.</p>
        </div>
        <Link href="/dashboard/new-review">
          <Button>
            <FilePlus2 className="h-4 w-4" /> New Review
          </Button>
        </Link>
      </div>

      {error && (
        <Card className="mb-6 border-red-500/30">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader><CardTitle>Reviews completed</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">
            {analytics?.reviews_completed ?? "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Average score</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">
            {analytics?.average_score ?? "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Most reviewed language</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold capitalize">
            {analytics?.most_reviewed_language ?? "—"}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Languages used</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">
            {analytics ? Object.keys(analytics.reviews_by_language).length : "—"}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
