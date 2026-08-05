"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Github,
  ShieldCheck,
  Gauge,
  Wand2,
  FileText,
  Sparkles,
  CircleAlert,
  CircleCheck,
  TriangleAlert,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const NAV_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#pricing", label: "Pricing" },
  { href: "#testimonials", label: "Testimonials" },
  { href: "#faq", label: "FAQ" },
];

const FEATURES = [
  {
    icon: Sparkles,
    title: "In-depth AI review",
    desc: "Get readability, performance, and maintainability feedback in seconds, not a code-review meeting.",
  },
  {
    icon: ShieldCheck,
    title: "Security analysis",
    desc: "Catch injection flaws, unsafe input handling, and other vulnerabilities before they ship.",
  },
  {
    icon: Gauge,
    title: "Complexity analysis",
    desc: "Instant time and space complexity breakdowns with concrete optimization suggestions.",
  },
  {
    icon: Wand2,
    title: "One-click refactor",
    desc: "Generate a cleaner, faster version of your code without changing its behavior.",
  },
  {
    icon: FileText,
    title: "Unit test generation",
    desc: "Idiomatic tests for your language and framework, covering the edge cases you'd miss.",
  },
  {
    icon: Github,
    title: "GitHub integration",
    desc: "Connect a repo, review files individually, and get a repository health score.",
  },
];

const PLANS = [
  { name: "Free", price: "$0", blurb: "For trying it out", features: ["25 reviews / month", "1 language at a time", "Community support"] },
  { name: "Pro", price: "$19", blurb: "For individual developers", features: ["Unlimited reviews", "All 13 languages", "GitHub integration", "PDF export"] },
  { name: "Team", price: "$49", blurb: "Per seat, for teams", features: ["Everything in Pro", "Shared history", "Repo health scoring", "Priority support"] },
];

const FAQS = [
  { q: "What languages are supported?", a: "Python, Java, JavaScript, TypeScript, Go, Rust, C, C++, C#, Kotlin, Swift, Ruby, and PHP." },
  { q: "Does CodeInsight AI store my code?", a: "Reviews are saved to your account so you can revisit them later. You can delete any review or your whole account from Settings." },
  { q: "Can I use my own AI provider?", a: "The backend is built around a single AI service layer, so swapping providers is a config change, not a rewrite." },
];

function DiagnosticRow({
  severity,
  label,
  line,
}: {
  severity: "critical" | "warn" | "pass";
  label: string;
  line: number;
}) {
  const Icon = severity === "critical" ? CircleAlert : severity === "warn" ? TriangleAlert : CircleCheck;
  const color =
    severity === "critical" ? "text-red-400" : severity === "warn" ? "text-primary" : "text-accent";
  return (
    <div className="flex items-center gap-2.5 px-4 py-2.5 text-xs">
      <Icon className={`h-3.5 w-3.5 shrink-0 ${color}`} />
      <span className="flex-1 text-muted-foreground">{label}</span>
      <span className="font-display text-muted-foreground/60">L{line}</span>
    </div>
  );
}

function ReviewMockup() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.15 }}
      className="mx-auto w-full max-w-md overflow-hidden rounded-2xl border border-border bg-card shadow-2xl shadow-black/40"
    >
      <div className="flex items-center gap-2 border-b border-border bg-muted/40 px-4 py-3">
        <div className="flex gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-primary/70" />
          <span className="h-2.5 w-2.5 rounded-full bg-accent/70" />
        </div>
        <span className="ml-2 font-display text-[11px] text-muted-foreground">
          payment_processor.py — review
        </span>
      </div>
      <div className="border-b border-border px-4 py-4 font-mono text-[11px] leading-relaxed text-muted-foreground">
        <div><span className="text-primary/80">def</span> charge(amount, card_id):</div>
        <div className="pl-4">query = <span className="text-accent/80">f</span>&quot;INSERT INTO charges...&quot;</div>
        <div className="pl-4">db.execute(query)</div>
        <div className="pl-4"><span className="text-primary/80">return</span> {`{"ok": True}`}</div>
      </div>
      <div className="divide-y divide-border">
        <DiagnosticRow severity="critical" label="SQL built with string concatenation" line={42} />
        <DiagnosticRow severity="warn" label="No input validation on amount" line={17} />
        <DiagnosticRow severity="pass" label="Idempotency key correctly checked" line={9} />
      </div>
      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        <span className="font-display text-[11px] uppercase tracking-wide text-muted-foreground">
          Overall score
        </span>
        <span className="font-display text-lg font-semibold text-primary">
          62<span className="text-xs text-muted-foreground">/100</span>
        </span>
      </div>
    </motion.div>
  );
}

export default function LandingPage() {
  return (
    <main className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,hsl(var(--primary)/0.14),transparent)]" />

      <nav className="sticky top-0 z-20 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="flex items-center justify-between px-6 py-4 md:px-12">
          <Link href="/" className="flex items-center gap-2 font-display font-semibold tracking-tight">
            <Sparkles className="h-5 w-5 text-primary" />
            CodeInsight AI
          </Link>
          <div className="hidden items-center gap-8 md:flex">
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                className="text-sm text-muted-foreground transition-colors hover:text-foreground"
              >
                {l.label}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm">Sign in</Button>
            </Link>
            <Link href="/signup">
              <Button size="sm">Start Reviewing</Button>
            </Link>
          </div>
        </div>
      </nav>

      <section className="relative px-6 pb-24 pt-16 md:px-12 md:pt-24">
        <div className="mx-auto grid max-w-6xl items-center gap-14 md:grid-cols-2">
          <div className="text-center md:text-left">
            <motion.h1
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="font-display text-4xl font-semibold leading-[1.05] tracking-tight md:text-5xl"
            >
              AI Code Reviews<br />in Seconds
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mx-auto mt-5 max-w-md text-lg text-muted-foreground md:mx-0"
            >
              Paste code, upload a file, or connect a repo. Get security, performance,
              and readability feedback — plus refactors and tests — powered by AI.
            </motion.p>
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="mt-8 flex flex-col items-center gap-3 sm:flex-row md:justify-start"
            >
              <Link href="/signup">
                <Button size="lg">
                  Start Reviewing <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <a href={`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/auth/github/login`}>
                <Button size="lg" variant="outline">
                  <Github className="h-4 w-4" /> GitHub Login
                </Button>
              </a>
            </motion.div>
          </div>
          <ReviewMockup />
        </div>
      </section>

      <section id="features" className="relative px-6 py-20 md:px-12">
        <h2 className="text-center font-display text-2xl font-semibold tracking-tight md:text-3xl">
          Everything a code review should catch
        </h2>
        <div className="mx-auto mt-12 grid max-w-6xl gap-5 md:grid-cols-3">
          {FEATURES.map((f) => (
            <Card key={f.title} className="p-1 transition-colors hover:border-primary/40">
              <CardContent className="p-5">
                <f.icon className="mb-4 h-6 w-6 text-primary" />
                <h3 className="mb-1.5 font-medium">{f.title}</h3>
                <p className="text-sm text-muted-foreground">{f.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="pricing" className="relative px-6 py-20 md:px-12">
        <h2 className="text-center font-display text-2xl font-semibold tracking-tight md:text-3xl">
          Simple pricing
        </h2>
        <div className="mx-auto mt-12 grid max-w-5xl gap-5 md:grid-cols-3">
          {PLANS.map((p) => (
            <Card key={p.name} className={p.name === "Pro" ? "border-primary/50" : ""}>
              <CardContent className="p-6">
                <h3 className="font-medium">{p.name}</h3>
                <p className="text-sm text-muted-foreground">{p.blurb}</p>
                <div className="my-4 font-display text-3xl font-semibold">
                  {p.price}
                  <span className="text-sm font-normal text-muted-foreground">/mo</span>
                </div>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  {p.features.map((f) => (
                    <li key={f}>• {f}</li>
                  ))}
                </ul>
                {p.name === "Free" ? (
                  <Link href="/signup">
                    <Button className="mt-6 w-full" variant="outline">Choose Free</Button>
                  </Link>
                ) : (
                  <Button
                    className="mt-6 w-full"
                    variant={p.name === "Pro" ? "default" : "outline"}
                    disabled
                    title="Billing isn't set up yet - the Free plan currently has no usage limits, so it covers everything for now."
                  >
                    Choose {p.name} (coming soon)
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="testimonials" className="relative px-6 py-20 md:px-12">
        <h2 className="text-center font-display text-2xl font-semibold tracking-tight md:text-3xl">
          Developers ship faster with it
        </h2>
        <div className="mx-auto mt-12 grid max-w-5xl gap-5 md:grid-cols-3">
          {[
            { name: "Priya S.", role: "Backend Engineer", quote: "Cut our PR review time roughly in half." },
            { name: "Diego M.", role: "Indie Developer", quote: "Feels like having a senior engineer on call." },
            { name: "Amara O.", role: "Eng Manager", quote: "Security catches alone paid for the team plan." },
          ].map((t) => (
            <Card key={t.name}>
              <CardContent className="p-6">
                <p className="text-sm text-foreground">&ldquo;{t.quote}&rdquo;</p>
                <p className="mt-4 text-xs text-muted-foreground">{t.name} — {t.role}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section id="faq" className="relative px-6 py-20 md:px-12">
        <h2 className="text-center font-display text-2xl font-semibold tracking-tight md:text-3xl">FAQ</h2>
        <div className="mx-auto mt-10 max-w-2xl space-y-4">
          {FAQS.map((f) => (
            <Card key={f.q}>
              <CardContent className="p-5">
                <h3 className="mb-1.5 font-medium">{f.q}</h3>
                <p className="text-sm text-muted-foreground">{f.a}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      <footer className="relative border-t border-border px-6 py-10 text-center text-sm text-muted-foreground md:px-12">
        © {new Date().getFullYear()} CodeInsight AI. Built with Next.js and FastAPI.
      </footer>
    </main>
  );
}
