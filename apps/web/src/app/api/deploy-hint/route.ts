import { NextResponse } from "next/server";

/**
 * Public hint for operators — confirms which env this service reads.
 * Does not expose secret values.
 */
export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  return NextResponse.json({
    service: "revive-my-drive-web",
    role: "Next.js frontend only — not the FastAPI API",
    next_public_api_url_set: Boolean(apiUrl),
    next_public_api_url_host: (() => {
      if (!apiUrl) return null;
      try {
        return new URL(apiUrl).host;
      } catch {
        return "invalid-url";
      }
    })(),
    reminder:
      "TELEGRAM_*, DATABASE_URL, JWT_SECRET, and PUBLIC_API_BASE_URL belong on the Railway API service (apps/api), not here.",
    docs: "See RAILWAY_VARIABLES.md in the repo",
  });
}