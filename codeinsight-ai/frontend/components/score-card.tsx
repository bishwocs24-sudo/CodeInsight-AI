"use client";

import { motion } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function scoreColor(score: number) {
  if (score >= 80) return "bg-emerald-400";
  if (score >= 60) return "bg-yellow-400";
  if (score >= 40) return "bg-orange-400";
  return "bg-red-400";
}

export function ScoreCard({ label, score }: { label: string; score: number }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{label}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-end justify-between mb-3">
          <span className="text-3xl font-semibold tracking-tight">{Math.round(score)}</span>
          <span className="text-sm text-muted-foreground">/ 100</span>
        </div>
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(0, Math.min(100, score))}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className={`h-full rounded-full ${scoreColor(score)}`}
          />
        </div>
      </CardContent>
    </Card>
  );
}
