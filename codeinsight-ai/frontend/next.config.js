const staticExport = process.env.CODEGUARD_STATIC_EXPORT === "1";
const demoOnly = process.env.VERCEL === "1" && !process.env.NEXT_PUBLIC_API_URL;

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: { NEXT_PUBLIC_HOSTED_GOOGLE: process.env.VERCEL === "1" ? "1" : "0", NEXT_PUBLIC_DEMO_ONLY: demoOnly ? "1" : "0" },
  ...(staticExport ? { output: "export", trailingSlash: true } : {}),
};

module.exports = nextConfig;
