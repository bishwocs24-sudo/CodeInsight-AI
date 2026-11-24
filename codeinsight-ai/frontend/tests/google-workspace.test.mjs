import assert from "node:assert/strict";
import test from "node:test";
import { encode } from "@auth/core/jwt";
import auth from "../api/auth/signin/google.mjs";
import callback from "../api/auth/callback/google.mjs";
import reviews from "../api/reviews.mjs";

const origin = "https://codeguard.example";
const secret = "a".repeat(48);
Object.assign(process.env, { AUTH_URL: origin, AUTH_SECRET: secret, AUTH_GOOGLE_ID: "test.apps.googleusercontent.com", AUTH_GOOGLE_SECRET: "test-only" });

async function signedRequest(init = {}) {
  const salt = "__Secure-authjs.session-token";
  const cookie = await encode({ salt, secret, token: { googleAccess: "dummy", googleExpires: Math.floor(Date.now()/1000) + 300 } });
  return new Request(origin + "/api/reviews", { ...init, headers: { cookie: salt + "=" + cookie, ...init.headers } });
}

test("only Google is advertised with the hosted callback", async () => {
  assert.equal(auth, callback);
  const providers = await (await auth.fetch(new Request(origin + "/api/auth/providers"))).json();
  assert.deepEqual(Object.keys(providers), ["google"]);
  assert.equal(providers.google.callbackUrl, origin + "/api/auth/callback/google");
});

test("private history requires a session", async () => {
  const result = await reviews.fetch(new Request(origin + "/api/reviews"));
  assert.equal(result.status, 401);
  assert.match(result.headers.get("cache-control"), /no-store/);
});

test("cross-origin saves are rejected", async () => {
  const result = await reviews.fetch(await signedRequest({method: "POST", headers: { origin: "https://elsewhere.example" }}));
  assert.equal(result.status, 403);
});

test("list is restricted to app storage and uses user authorization", async (t) => {
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(new URL(url).searchParams.get("spaces"), "appDataFolder");
    assert.equal(options.headers.Authorization, "Bearer dummy");
    return Response.json({ files: [] });
  });
  assert.deepEqual(await (await reviews.fetch(await signedRequest())).json(), { files: [] });
});

test("saves a valid report into the user's app folder", async (t) => {
  t.mock.method(globalThis, "fetch", async (url, opts) => {
    assert.equal(new URL(url).searchParams.get("uploadType"), "multipart");
    assert.match(opts.body, /"parents":\["appDataFolder"\]/);
    return Response.json({ id: "report1" });
  });
  const report = { filename: "example.c", data: { engine: "codeguard-static-v1", findings: [], errors: [], finding_count: 0, lines_of_code: 1 } };
  const request = await signedRequest({method: "POST", headers: {origin, "content-type":"application/json"}, body: JSON.stringify(report)});
  assert.deepEqual(await (await reviews.fetch(request)).json(), {id: "report1"});
});

test("worker dashboard exchange requires a Google identity and a same-origin POST", async (t) => {
  const { default: platform } = await import("../api/platform-session.mjs");
  t.mock.method(globalThis, "fetch", async (url, options) => {
    assert.equal(String(url), "https://backend.example/auth/google/exchange");
    assert.equal(JSON.parse(options.body).id_token, "mock-identity");
    assert.equal(options.redirect, "error");
    return Response.json({ access_token: "temporary-platform-token" });
  });
  process.env.NEXT_PUBLIC_API_URL = "https://backend.example";
  try {
    assert.equal((await platform.fetch(await signedRequest({ method: "POST" }))).status, 403);
    assert.equal((await platform.fetch(await signedRequest({ method: "POST", headers: { origin } }))).status, 401);
    const salt = "__Secure-authjs.session-token";
    const encrypted = await encode({ salt, secret, token: { googleIdentity: "mock-identity", googleExpires: Math.floor(Date.now()/1000) + 60 } });
    const response = await platform.fetch(new Request(origin + "/api/platform-session", {
      method: "POST", headers: { origin, cookie: salt + "=" + encrypted },
    }));
    assert.equal((await response.json()).access_token, "temporary-platform-token");
  } finally { delete process.env.NEXT_PUBLIC_API_URL; }
});
