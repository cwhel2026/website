import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({
    service: "revive-my-drive-web",
    git_commit: process.env.NEXT_PUBLIC_GIT_COMMIT ?? "unknown",
    build_time: process.env.NEXT_PUBLIC_BUILD_TIME ?? null,
    api_url_configured: Boolean(process.env.NEXT_PUBLIC_API_URL),
    node_env: process.env.NODE_ENV,
  });
}