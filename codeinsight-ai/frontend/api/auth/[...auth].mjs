import { Auth } from "@auth/core";
import GitHub from "@auth/core/providers/github";

const basePath = "/api/auth";

function getTrustedOrigin() {
  const url = process.env.AUTH_URL?.trim()
    ?? (process.env.VERCEL_PROJECT_PRODUCTION_URL
      ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
      : "");
  try {
    const { origin, hostname, protocol } = new URL(url);
    if (protocol === "https:" || (protocol === "http:" && hostname === "localhost")) return origin;
  } catch {
    return undefined;
  }
}

const handler = {
  /** @param {Request} request */
  async fetch(request) {
    const url = new URL(request.url);
    const trustedOrigin = getTrustedOrigin();
    const secret = process.env.AUTH_SECRET?.trim();
    const clientId = process.env.AUTH_GITHUB_ID?.trim();
    const clientSecret = process.env.AUTH_GITHUB_SECRET?.trim();

    if (url.origin !== trustedOrigin || !secret || secret.length < 32 || !clientId || !clientSecret) {
      const readable = request.method === "GET"
        && [`${basePath}/providers`, `${basePath}/session`].includes(url.pathname);
      return Response.json(readable ? {} : { error: "GitHub sign-in is unavailable" }, {
        status: readable ? 200 : 503,
        headers: { "Cache-Control": "no-store" },
      });
    }

    return Auth(request, {
      basePath,
      secret,
      // Only requests for the configured origin reach Auth.js.
      trustHost: true,
      providers: [GitHub({ clientId, clientSecret, checks: ["state"] })],
      session: { strategy: "jwt", maxAge: 60 * 60 * 24 * 7 },
      pages: { signIn: "/login/", error: "/login/" },
    });
  },
};

export default handler;
