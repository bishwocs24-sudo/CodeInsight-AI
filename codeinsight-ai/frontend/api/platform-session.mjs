import { getToken } from "@auth/core/jwt";

function reply(data, status) {
  return Response.json(data, { status, headers: { "Cache-Control": "private, no-store" } });
}

const handler = {
  async fetch(request) {
    const origin = new URL(request.url).origin;
    if (request.method !== "POST") return reply({ error: "POST required." }, 405);
    if (request.headers.get("origin") !== origin) return reply({ error: "Invalid origin." }, 403);
    const api = process.env.NEXT_PUBLIC_API_URL;
    const secret = process.env.AUTH_SECRET?.trim();
    if (!api?.startsWith("https://") || !secret) return reply({ error: "Review backend is unavailable." }, 503);
    const token = await getToken({ req: request, secret, secureCookie: true });
    if (!token?.googleIdentity || !(token.googleExpires > Date.now() / 1000)) return reply({ error: "Sign in again with Google." }, 401);
    try {
      const upstream = await fetch(new URL("/auth/google/exchange", api), {
        method: "POST", redirect: "error", signal: AbortSignal.timeout(10000),
        headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id_token: token.googleIdentity }),
      });
      const data = await upstream.json();
      if (!upstream.ok) return reply({ error: typeof data.detail === "string" ? data.detail : "Review backend access failed." }, upstream.status);
      return reply({ access_token: data.access_token }, 200);
    } catch { return reply({ error: "Could not reach the review backend." }, 502); }
  },
};
export default handler;
