const staticExport = process.env.CODEGUARD_STATIC_EXPORT === "1";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  ...(staticExport ? { output: "export", trailingSlash: true } : {}),
};

module.exports = nextConfig;
