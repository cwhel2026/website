import { NextResponse } from "next/server";

/**
 * Public hint for operators — confirms which env this service reads.
 * Does not expose secret values.
 */
export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  const internal = Boolean(process.env.API_INTERNAL_URL?.trim());
  const hasDb = Boolean(process.env.DATABASE_URL?.trim());
  const imageKind = process.env.RMD_IMAGE_KIND ?? "unknown";
  const combined = imageKind === "combined" || (internal && hasDb);

  return NextResponse.json({
    service: "revive-my-drive",
    image_kind: imageKind,
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
      imageKind === "web-only"
        ? "Still on web-only image. Railway → website → Settings → Deploy → Start command: /app/start.sh, Health: /health. Build → Dockerfile: Dockerfile (repo root). Redeploy. Or clear Root directory to empty."
        : "Railway → Dockerfile = repo root Dockerfile, Start = /app/start.sh. Set DEFAULT_ADMIN_EMAIL/PASSWORD to match login.",
    docs: "RAILWAY_COMBINED.md",
  });
}