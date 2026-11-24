import { getToken } from "@auth/core/jwt";

const files = "https://www.googleapis.com/drive/v3/files";
const upload = "https://www.googleapis.com/upload/drive/v3/files";
const marker = "codeguard-review-v1";

function reply(data, status = 200) {
  return Response.json(data, { status, headers: { "Cache-Control": "private, no-store" } });
}

function validReport(report) {
  const data = report?.data;
  return typeof report?.filename === "string" && report.filename.length > 0 && report.filename.length <= 255
    && data?.engine === "codeguard-static-v1"
    && Number.isSafeInteger(data.lines_of_code) && data.lines_of_code >= 0
    && Number.isSafeInteger(data.finding_count) && data.finding_count >= 0
    && Array.isArray(data.errors) && data.errors.every(item => typeof item === "string")
    && Array.isArray(data.findings) && data.findings.length <= 200
    && data.findings.every(f => Number.isSafeInteger(f?.line) && f.line > 0
      && (f.disposition === undefined || ["confirmed", "dismissed"].includes(f.disposition))
      && ["high", "medium", "low"].includes(f.severity)
      && [f.rule_id, f.message, f.evidence].every(item => typeof item === "string"));
}

const handler = {
  async fetch(req) {
    const url = new URL(req.url);
    const secret = process.env.AUTH_SECRET?.trim();
    if (!secret) return reply({ error: "Sign in to open your review history." }, 401);
    const token = await getToken({ req, secret, secureCookie: url.protocol === "https:" });
    if (!token?.googleAccess || !(token.googleExpires > Date.now() / 1000)) {
      return reply({ error: "Sign in with Google again to access your saved reviews." }, 401);
    }
    const headers = { Authorization: "Bearer " + token.googleAccess };
    let response;
    try {
      if (req.method === "GET") {
        const id = url.searchParams.get("id");
        if (id !== null) {
          if (!/^[\w-]{1,200}$/.test(id)) return reply({ error: "Invalid report ID." }, 400);
          response = await fetch(files + "/" + id + "?alt=media", { headers });
        } else {
          const query = new URLSearchParams({
            spaces: "appDataFolder", pageSize: "50", orderBy: "createdTime desc",
            q: "trashed = false and appProperties has { key='kind' and value='" + marker + "' }",
            fields: "nextPageToken,files(id,name,createdTime,appProperties)",
          });
          const cursor = url.searchParams.get("cursor");
          if (cursor) query.set("pageToken", cursor);
          response = await fetch(files + "?" + query, { headers });
        }
      } else if (req.method === "POST") {
        if (req.headers.get("origin") !== url.origin) return reply({ error: "Invalid request origin." }, 403);
        if (req.headers.get("content-type")?.split(";")[0] !== "application/json") return reply({ error: "JSON required." }, 415);
        const body = await req.text();
        if (body.length > 240000) return reply({ error: "Report is too large." }, 413);
        let report;
        try { report = JSON.parse(body); } catch { return reply({ error: "Invalid JSON." }, 400); }
        if (!validReport(report)) return reply({ error: "Invalid review report." }, 400);
        const boundary = crypto.randomUUID();
        const metadata = { name: report.filename, parents: ["appDataFolder"], mimeType: "application/json",
          appProperties: { kind: marker, findings: String(report.data.finding_count) } };
        const multipart = ["--" + boundary, "Content-Type: application/json", "", JSON.stringify(metadata),
          "--" + boundary, "Content-Type: application/json", "", body, "--" + boundary + "--", ""].join("\r\n");
        response = await fetch(upload + "?uploadType=multipart&fields=id,name,createdTime,appProperties", {
          method: "POST", headers: { ...headers, "Content-Type": "multipart/related; boundary=" + boundary }, body: multipart,
        });
      } else return reply({ error: "Method unavailable." }, 405);
      if (!response.ok) {
        const status = [401, 403, 404, 429].includes(response.status) ? response.status : 502;
        return reply({ error: status === 401 ? "Your Google session expired. Sign in again."
          : status === 403 ? "Drive access is unavailable. Check consent and the Google Drive API configuration."
          : "Google Drive could not complete this request." }, status);
      }
      const result = await response.json();
      if (req.method === "GET" && url.searchParams.has("id") && !validReport(result)) {
        return reply({ error: "This file is not a CodeGuard report." }, 422);
      }
      return reply(result);
    } catch { return reply({ error: "Could not reach Google Drive. Try again." }, 502); }
  },
};
export default handler;
