"use client";

import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getHistory, downloadReviewPdf } from "@/lib/api";
import type { ReviewHistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const [items, setItems] = useState<ReviewHistoryItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory()
      .then(setItems)
      .catch(() => setError("Couldn't load history. Is the backend running?"));
  }, []);

  return (
    <div>
      <h1 className="mb-1 font-display text-2xl font-semibold tracking-tight">History</h1>
      <p className="mb-8 text-sm text-muted-foreground">Every review you&rsquo;ve run.</p>

      {error && (
        <Card className="border-red-500/30">
          <CardContent className="p-4 text-sm text-red-400">{error}</CardContent>
        </Card>
      )}

      {items && items.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center text-sm text-muted-foreground">
            No reviews yet. Run one from New Review.
          </CardContent>
        </Card>
      )}

      {items && items.length > 0 && (
        <div className="space-y-3">
          {items.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div className="flex items-center gap-3">
                  <Badge className="capitalize">{item.review_type}</Badge>
                  <span className="text-sm capitalize">{item.language}</span>
                </div>
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  {item.overall_score !== null && <span>{Math.round(item.overall_score)}/100</span>}
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                  <Button variant="ghost" size="sm" onClick={() => downloadReviewPdf(item.id)}>
                    <FileText className="h-4 w-4" /> PDF
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
