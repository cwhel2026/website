import { NextResponse } from "next/server";

export const runtime = "nodejs";

import { publicSiteBaseUrl } from "@/lib/telegram/server";

/** Safe Telegram diagnostics (no tokens in response). */
export async function GET() {
  const token = process.env.TELEGRAM_BOT_TOKEN?.trim();
  if (!token) {
    return NextResponse.json({ configured: false, reason: "TELEGRAM_BOT_TOKEN not set" });
  }

  const res = await fetch(`https://api.telegram.org/bot${token}/getWebhookInfo`);
  const data = (await res.json()) as { ok?: boolean; result?: Record<string, unknown> };
  const info = data.result ?? {};
  const expected = publicSiteBaseUrl();
  const webhookUrl = expected ? `${expected.replace(/\/$/, "")}/api/v1/telegram/webhook` : null;

  return NextResponse.json({
    configured: true,
    admin_ids_count: (process.env.TELEGRAM_ADMIN_IDS ?? "")
      .split(",")
      .map((s) => s.trim())
      .filter((s) => /^-?\d+$/.test(s)).length,
    webhook_secret_set: Boolean(process.env.TELEGRAM_WEBHOOK_SECRET?.trim()),
    expected_webhook_url: expected ? webhookUrl : null,
    telegram: {
      url: info.url ?? "",
      pending_update_count: info.pending_update_count,
      last_error_message: info.last_error_message,
      last_error_date: info.last_error_date,
    },
    url_matches_site: Boolean(
      expected && typeof info.url === "string" && String(info.url).startsWith(expected),
    ),
  });
}