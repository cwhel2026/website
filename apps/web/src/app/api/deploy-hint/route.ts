import { NextResponse } from "next/server";

/**
 * Public hint for operators — confirms which env this service reads.
 * Does not expose secret values.
 */
export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  const internal = Boolean(process.env.API_INTERNAL_URL?.trim());
  const hasDb = Boolean(process.env.DATABASE_URL?.trim());
  const combined = internal && hasDb;

  return NextResponse.json({
    service: "revive-my-drive",
    combined_deploy: combined,
    role: combined
      ? "Combined site + FastAPI (variables on this service are correct)"
      : "Web-only image — dashboard login and DB features need the combined deploy",
    next_public_api_url_set: Boolean(apiUrl),
    next_public_api_url_host: (() => {
      if (!apiUrl) return null;
      try {
        return new URL(apiUrl).host;
      } catch {
        return "invalid-url";
      }
    })(),
    fix_when_login_fails:
      "Railway → website → Settings → Source → Root directory: leave empty (repo root, not apps/web). Redeploy. Keep DATABASE_URL, JWT_SECRET, DEFAULT_ADMIN_* on this service.",
    docs: "RAILWAY_COMBINED.md",
  });
}