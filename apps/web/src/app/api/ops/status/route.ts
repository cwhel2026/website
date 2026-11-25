import { NextResponse } from "next/server";

/**
 * Operator diagnostics (no secrets). Shows whether the combined sidecar API is up.
 */
export async function GET() {
  const internal = process.env.API_INTERNAL_URL ?? "";
  let api: Record<string, unknown> = { reachable: false };

  if (internal) {
    try {
      const res = await fetch(`${internal.replace(/\/$/, "")}/health`, {
        cache: "no-store",
      });
      const text = await res.text();
      api = {
        reachable: res.ok,
        status: res.status,
        preview: text.slice(0, 200),
      };
    } catch (err) {
      api = { reachable: false, error: String(err) };
    }
  } else {
    api = {
      reachable: false,
      reason: "API_INTERNAL_URL not set — running web-only image (Telegram/FastAPI inactive)",
    };
  }

  const publicApi = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();
  const telegramOnWeb = Boolean(process.env.TELEGRAM_BOT_TOKEN?.trim());

  return NextResponse.json({
    service: "revive-my-drive",
    telegram_native_webhook: telegramOnWeb,
    combined_sidecar: Boolean(internal),
    api_internal_url_set: Boolean(internal),
    next_public_api_url_host: publicApi ? safeHost(publicApi) : null,
    api,
    telegram_hint:
      internal && (api as { reachable?: boolean }).reachable
        ? "FastAPI is up — Telegram webhook hits /api/v1/telegram/webhook."
        : telegramOnWeb
          ? "Web-native Telegram handler active (apps/web). Redeploy sets webhook on boot via instrumentation."
          : "Set TELEGRAM_BOT_TOKEN on this service and redeploy.",
  });
}

function safeHost(url: string): string | null {
  try {
    return new URL(url).host;
  } catch {
    return "invalid-url";
  }
}