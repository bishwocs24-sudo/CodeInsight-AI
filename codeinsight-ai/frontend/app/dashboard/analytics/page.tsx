"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getAnalytics } from "@/lib/api";
import type { AnalyticsSummary } from "@/lib/types";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getAnalytics()
      .then(setAnalytics)
      .catch(() => setError("Couldn't reach the backend."));
  }, []);

  const chartData = analytics
    ? Object.entries(analytics.reviews_by_language).map(([language, count]) => ({ language, count }))
    : [];

  return (
    <div>
      <h1 className="mb-1 font-display text-2xl font-semibold tracking-tight">Analytics</h1>
      <p className="mb-8 text-sm text-muted-foreground">Usage across all your reviews.</p>

      {error && (
        <Card className="mb-6 border-red-500/30">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      <div className="mb-6 grid gap-5 sm:grid-cols-3">
        <Card>
          <CardHeader><CardTitle>Reviews completed</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">{analytics?.reviews_completed ?? "—"}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Average score</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold">{analytics?.average_score ?? "—"}</CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Most reviewed language</CardTitle></CardHeader>
          <CardContent className="text-3xl font-semibold capitalize">{analytics?.most_reviewed_language ?? "—"}</CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Reviews by language</CardTitle></CardHeader>
        <CardContent className="h-80 p-5 pt-2">
          {chartData.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
              No reviews yet — run one to see it here.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(240 6% 16%)" vertical={false} />
                <XAxis dataKey="language" stroke="hsl(240 5% 64%)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="hsl(240 5% 64%)" fontSize={12} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(240 8% 8%)",
                    border: "1px solid hsl(240 6% 16%)",
                    borderRadius: 12,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" fill="hsl(250 84% 65%)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
