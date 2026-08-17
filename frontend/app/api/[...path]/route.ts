import { NextRequest, NextResponse } from "next/server";

// Proxies every same-origin /api/* call the browser makes to the backend,
// attaching the (server-only) API key along the way. The key lives only in
// this server-side env var -- it is never sent to or readable by the
// browser, unlike a client-side fetch header would be.
export const dynamic = "force-dynamic";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";
const API_KEY = process.env.API_KEY || "";

async function handler(req: NextRequest, context: { params: { path: string[] } }) {
  const { path } = context.params;
  const url = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers();
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  if (API_KEY) headers.set("x-api-key", API_KEY);

  const hasBody = !["GET", "HEAD"].includes(req.method);

  let res: Response;
  try {
    res = await fetch(url, {
      method: req.method,
      headers,
      body: hasBody ? await req.text() : undefined,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Backend unreachable" }, { status: 502 });
  }

  const body = await res.arrayBuffer();
  const outHeaders = new Headers();
  for (const h of ["content-type", "content-disposition"]) {
    const v = res.headers.get(h);
    if (v) outHeaders.set(h, v);
  }

  return new NextResponse(body, { status: res.status, headers: outHeaders });
}

export { handler as GET, handler as POST, handler as PUT, handler as PATCH, handler as DELETE };
