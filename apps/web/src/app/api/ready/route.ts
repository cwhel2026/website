import { NextResponse } from "next/server";

type CheckStatus = "ok" | "fail" | "skip";

/**
 * Readiness: can this host serve authenticated dashboard traffic?
 * Liveness alone is GET /api/live (Next only).
 */
export async function GET() {
  const internal = (process.env.API_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  const imageKind = process.env.RMD_IMAGE_KIND ?? "unknown";
  const checks: Record<string, CheckStatus | string> = {
    web: "ok",
    image_kind: imageKind,
    fastapi_health: "fail",
    fastapi_ready: "fail",
    database: "fail",
  };

  if (imageKind !== "combined" && process.env.RUN_EMBEDDED_API !== "1") {
    return NextResponse.json(
      {
        status: "not_ready",
        detail: "Not a combined image — clear Railway Root Directory and redeploy with apps/combined/Dockerfile",
        checks,
      },
      { status: 503 },
    );
  }

  try {
    const healthRes = await fetch(`${internal}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(8000),
    });
    checks.fastapi_health = healthRes.ok ? "ok" : "fail";
    const healthBody = (await healthRes.json().catch(() => ({}))) as { status?: string };
    if (healthBody.status) checks.fastapi_health_detail = healthBody.status;
  } catch {
    checks.fastapi_health = "fail";
  }

  try {
    const readyRes = await fetch(`${internal}/ready`, {
      cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    const readyBody = (await readyRes.json().catch(() => ({}))) as { status?: string; database?: string };
    checks.fastapi_ready = readyRes.ok ? "ok" : "fail";
    checks.database = readyBody.database === "ok" ? "ok" : "fail";
  } catch {
    checks.fastapi_ready = "fail";
  }

  const ready =
    checks.fastapi_health === "ok" && checks.fastapi_ready === "ok" && checks.database === "ok";

  return NextResponse.json(
    {
      status: ready ? "ready" : "not_ready",
      checks,
    },
    { status: ready ? 200 : 503 },
  );
}