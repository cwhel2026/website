import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/**
 * Combined Railway deploy: proxy API traffic to internal uvicorn at runtime.
 * (Build-time rewrites alone are brittle; this reads API_INTERNAL_URL at run time.)
 */
const internalBase = (process.env.API_INTERNAL_URL ?? "").replace(/\/$/, "");

async function proxyToApi(request: NextRequest, targetPath: string): Promise<NextResponse> {
  const query = request.nextUrl.search;
  const url = `${internalBase}${targetPath}${query}`;

  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (key === "host") return;
    headers.set(key, value);
  });

  let body: ArrayBuffer | undefined;
  if (request.method !== "GET" && request.method !== "HEAD") {
    body = await request.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, {
      method: request.method,
      headers,
      body: body as BodyInit | undefined,
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "FastAPI sidecar is not reachable on API_INTERNAL_URL. Check Railway deploy logs for uvicorn startup errors (DATABASE_URL, JWT_SECRET, SYNC_DATABASE_URL).",
      },
      { status: 503 },
    );
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (key === "transfer-encoding") return;
    responseHeaders.set(key, value);
  });

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export async function middleware(request: NextRequest) {
  if (!internalBase) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;

  if (pathname === "/health" || pathname === "/ready") {
    return proxyToApi(request, pathname);
  }

  if (pathname.startsWith("/api/v1/")) {
    return proxyToApi(request, pathname);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/api/v1/:path*", "/health", "/ready"],
};