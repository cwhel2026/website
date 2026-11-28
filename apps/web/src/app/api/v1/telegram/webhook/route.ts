import { timingSafeEqual } from "node:crypto";
import { NextRequest, NextResponse } from "next/server";
import { expectedWebhookSecret } from "@/lib/telegram/server";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const secret = expectedWebhookSecret();
  if (!secret) return NextResponse.json({ status: "secret_not_configured" }, { status: 503 });
  const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token") ?? "";
  if (Buffer.byteLength(got) !== Buffer.byteLength(secret) || !timingSafeEqual(Buffer.from(got), Buffer.from(secret))) {
    return NextResponse.json({ status: "invalid_secret" }, { status: 401 });
  }
  let update;
  try { update = await request.json(); } catch {
    return NextResponse.json({ status: "bad_json" }, { status: 400 });
  }
  if (!update || !Number.isSafeInteger(update.update_id)) return NextResponse.json({ status: "bad_update" }, { status: 400 });
  const base = process.env.API_INTERNAL_URL?.trim().replace(/\/+$/, "");
  if (!base) return NextResponse.json({ status: "api_not_configured" }, { status: 503 });
  try {
    const upstream = await fetch(base + "/api/v1/telegram/webhook", {
      method: "POST", redirect: "error", signal: AbortSignal.timeout(120000),
      headers: { "Content-Type": "application/json", "X-Telegram-Bot-Api-Secret-Token": secret },
      body: JSON.stringify(update),
    });
    if (!upstream.ok) {
      console.error("Telegram API forwarding failed", upstream.status);
      return NextResponse.json({ status: "upstream_failed" }, { status: 502 });
    }
    return NextResponse.json(await upstream.json());
  } catch {
    console.error("Telegram API forwarding unavailable");
    return NextResponse.json({ status: "upstream_unavailable" }, { status: 503 });
  }
}
