import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "default" | "critical" | "high" | "medium" | "low" | "success";

const toneStyles: Record<Tone, string> = {
  default: "bg-muted text-muted-foreground",
  critical: "bg-red-500/15 text-red-400",
  high: "bg-orange-500/15 text-orange-400",
  medium: "bg-yellow-500/15 text-yellow-400",
  low: "bg-blue-500/15 text-blue-400",
  success: "bg-emerald-500/15 text-emerald-400",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
        toneStyles[tone],
        className
      )}
      {...props}
    />
  );
}
