import { NextResponse } from "next/server";

/**
 * Public hint for operators — confirms which env this service reads.
 * Does not expose secret values.
 */
async function apiSidecarReachable(): Promise<boolean> {
  const base = process.env.API_INTERNAL_URL?.trim() || "http://127.0.0.1:8000";
  try {
    const res = await fetch(`${base.replace(/\/$/, "")}/health`, {
      signal: AbortSignal.timeout(2500),
      cache: "no-store",
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { status?: string };
    return data.status === "ok";
  } catch {
    return false;
  }
}

export async function GET() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
  const internal = Boolean(process.env.API_INTERNAL_URL?.trim());
  const hasDb = Boolean(process.env.DATABASE_URL?.trim());
  const imageKind = process.env.RMD_IMAGE_KIND ?? "unknown";
  const apiUp = await apiSidecarReachable();
  const combined = imageKind === "combined" && apiUp;

  return NextResponse.json({
    service: "revive-my-drive",
    image_kind: imageKind,
    api_sidecar_reachable: apiUp,
    database_url_configured: hasDb,
    api_internal_url_configured: internal,
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
        ? "Web-only image (Root=apps/web). For login: Root Directory EMPTY, Config /railway.toml, Dockerfile apps/combined/Dockerfile, Start /app/start.sh, redeploy."
        : "Railway → Dockerfile = repo root Dockerfile, Start = /app/start.sh. Set DEFAULT_ADMIN_EMAIL/PASSWORD to match login.",
    docs: "RAILWAY_COMBINED.md",
  });
}