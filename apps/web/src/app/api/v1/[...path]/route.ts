import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

const internalBase = (process.env.API_INTERNAL_URL ?? "").replace(/\/$/, "");

async function proxy(request: NextRequest, apiPath: string): Promise<NextResponse> {
  const query = request.nextUrl.search;
  const url = `${internalBase}${apiPath}${query}`;
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
    upstream = await fetch(url, { method: request.method, headers, body: body as BodyInit | undefined });
  } catch {
    return NextResponse.json(
      { detail: "FastAPI sidecar refused connection — check Railway logs for uvicorn startup errors." },
      { status: 503 },
    );
  }
  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (key === "transfer-encoding") return;
    responseHeaders.set(key, value);
  });
  return new NextResponse(upstream.body, { status: upstream.status, headers: responseHeaders });
}

function webOnlyHelp(): NextResponse {
  const hasDb = Boolean(process.env.DATABASE_URL?.trim());
  const hasJwt = Boolean(process.env.JWT_SECRET?.trim());
  return NextResponse.json(
    {
      detail: "FastAPI is not running in this container.",
      fix: hasDb && hasJwt
        ? "Railway → website service → Settings → Source → Root directory = empty (repo root), then redeploy. Keep all variables on this service (combined image runs site + API)."
        : "Set DATABASE_URL and JWT_SECRET on this service, use combined deploy (see RAILWAY_COMBINED.md).",
      ops: "/api/ops/status",
    },
    { status: 503 },
  );
}

type Ctx = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const apiPath = `/api/v1/${path.join("/")}`;
  if (!internalBase) return webOnlyHelp();
  return proxy(request, apiPath);
}

export async function POST(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const apiPath = `/api/v1/${path.join("/")}`;
  if (!internalBase) return webOnlyHelp();
  return proxy(request, apiPath);
}

export async function PATCH(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const apiPath = `/api/v1/${path.join("/")}`;
  if (!internalBase) return webOnlyHelp();
  return proxy(request, apiPath);
}

export async function PUT(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const apiPath = `/api/v1/${path.join("/")}`;
  if (!internalBase) return webOnlyHelp();
  return proxy(request, apiPath);
}

export async function DELETE(request: NextRequest, ctx: Ctx) {
  const { path } = await ctx.params;
  const apiPath = `/api/v1/${path.join("/")}`;
  if (!internalBase) return webOnlyHelp();
  return proxy(request, apiPath);
}