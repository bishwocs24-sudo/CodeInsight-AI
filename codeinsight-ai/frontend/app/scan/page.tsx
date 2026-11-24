import type { Metadata } from "next";
import { Scanner } from "./scanner";

export const metadata: Metadata = {
  title: "Live code scanner | CodeGuard AI",
  description: "Scan a source snippet and inspect findings with line-level evidence.",
};

export default function ScanPage() {
  return <Scanner />;
}
