import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

const displayFont = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  variable: "--font-display",
});

const bodyFont = Inter({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "CodeInsight AI — AI Code Reviews in Seconds",
  description:
    "AI-powered code review, security analysis, and refactoring for developers who ship fast.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${displayFont.variable} ${bodyFont.variable}`}>
      <body className="min-h-screen antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
