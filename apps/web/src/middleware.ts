import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

/**
 * API proxying is handled by next.config rewrites (combined build) and
 * `app/api/v1/[...path]/route.ts` — not Edge middleware (runtime env is unreliable).
 */
export function middleware(request: NextRequest) {
  const res = NextResponse.next();
  if (request.nextUrl.pathname.startsWith("/dashboard")) {
    res.headers.set("X-Frame-Options", "DENY");
  }
  return res;
}

export const config = {
  matcher: ["/dashboard/:path*"],
};