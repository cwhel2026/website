import { NextResponse } from "next/server";

import { registerTelegramWebhook } from "@/lib/telegram/server";

/** Re-register webhook (no secrets in response). Protect with setup key if set. */
export async function POST(request: Request) {
  const setupKey = process.env.TELEGRAM_WEBHOOK_SETUP_KEY?.trim();
  if (setupKey) {
    const got = request.headers.get("X-Telegram-Setup-Key") ?? "";
    if (got !== setupKey) {
      return NextResponse.json({ error: "unauthorised" }, { status: 401 });
    }
  }
  const result = await registerTelegramWebhook();
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }
  return NextResponse.json({ status: "ok", webhook_url: result.webhookUrl });
}