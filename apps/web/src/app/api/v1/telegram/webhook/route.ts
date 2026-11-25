import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

import { assistantLiteReply } from "@/lib/telegram/assistant-lite";
import {
  TELEGRAM_START_MESSAGE,
  expectedWebhookSecret,
  markUpdateSeen,
  telegramAdminIds,
  telegramSendMessage,
} from "@/lib/telegram/server";

type TgUpdate = {
  update_id: number;
  message?: {
    text?: string;
    photo?: Array<{ file_id?: string; file_size?: number }>;
    from?: { id?: number };
    chat?: { id?: number };
  };
};

export async function POST(request: NextRequest) {
  if (!process.env.TELEGRAM_BOT_TOKEN?.trim()) {
    return NextResponse.json({ status: "telegram_not_configured" }, { status: 503 });
  }

  const expectedSecret = expectedWebhookSecret();
  if (expectedSecret) {
    const got = request.headers.get("X-Telegram-Bot-Api-Secret-Token") ?? "";
    if (got !== expectedSecret) {
      return NextResponse.json({ status: "invalid_secret" }, { status: 401 });
    }
  }

  let update: TgUpdate;
  try {
    update = (await request.json()) as TgUpdate;
  } catch {
    return NextResponse.json({ status: "bad_json" }, { status: 400 });
  }

  if (markUpdateSeen(update.update_id)) {
    return NextResponse.json({ status: "duplicate" });
  }

  const message = update.message;
  if (!message) {
    return NextResponse.json({ status: "ignored" });
  }

  const userId = message.from?.id;
  const chatId = message.chat?.id;
  const text = (message.text ?? "").trim();

  if (chatId == null) {
    return NextResponse.json({ status: "no_chat" });
  }

  const admins = telegramAdminIds();
  const authorised = userId != null && admins.length > 0 && admins.includes(userId);

  if (!authorised) {
    const hint =
      admins.length === 0
        ? `Telegram is not fully configured: TELEGRAM_ADMIN_IDS is empty.\n\nYour Telegram user ID is: ${userId}\n\nAdd it on Railway and redeploy.`
        : `This bot is private (Revive My Drive).\n\nYour Telegram user ID is: ${userId}\n\nAdd it to TELEGRAM_ADMIN_IDS on Railway and redeploy.`;
    await telegramSendMessage(chatId, hint);
    return NextResponse.json({ status: "unauthorised", hint_sent: true });
  }

  const photos = message.photo ?? [];
  const photoId =
    photos.length > 0
      ? [...photos].sort((a, b) => (b.file_size ?? 0) - (a.file_size ?? 0))[0]?.file_id
      : undefined;

  const apiBase = process.env.API_INTERNAL_URL?.trim().replace(/\/$/, "");
  const ingestKey = process.env.FINANCE_TELEGRAM_INGEST_KEY?.trim();

  if (photoId && apiBase && ingestKey) {
    const res = await fetch(`${apiBase}/api/v1/finance/bookkeeping/receipts/telegram`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Finance-Telegram-Ingest-Key": ingestKey,
      },
      body: JSON.stringify({ file_id: photoId }),
    });
    if (res.ok) {
      const data = (await res.json()) as { reply?: string };
      const reply = data.reply ?? "Receipt saved.";
      await telegramSendMessage(chatId, reply);
      return NextResponse.json({ status: "receipt_ok" });
    }
  }

  if (photoId && apiBase) {
    const secret = expectedWebhookSecret();
    const fwd = await fetch(`${apiBase}/api/v1/telegram/webhook`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(secret ? { "X-Telegram-Bot-Api-Secret-Token": secret } : {}),
      },
      body: JSON.stringify(update),
    });
    const body = (await fwd.json()) as { status?: string };
    return NextResponse.json({ status: body.status ?? "forwarded", forwarded: true });
  }

  if (photoId && !text) {
    await telegramSendMessage(
      chatId,
      "Receipt photos need the API service. Set API_INTERNAL_URL (or use combined deploy) and FINANCE_TELEGRAM_INGEST_KEY.",
    );
    return NextResponse.json({ status: "receipt_needs_api" });
  }

  if (!text) {
    await telegramSendMessage(chatId, "Send text, a receipt photo, or /start");
    return NextResponse.json({ status: "no_text" });
  }

  let reply: string;
  if (text === "/start" || text.startsWith("/start ")) {
    reply =
      TELEGRAM_START_MESSAGE +
      "\n\nSend a receipt photo here when the API is connected.";
  } else if (apiBase) {
    const secret = expectedWebhookSecret();
    const fwd = await fetch(`${apiBase}/api/v1/telegram/webhook`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(secret ? { "X-Telegram-Bot-Api-Secret-Token": secret } : {}),
      },
      body: JSON.stringify(update),
    });
    if (fwd.ok) {
      const body = (await fwd.json()) as { status?: string };
      return NextResponse.json({ status: body.status ?? "forwarded" });
    }
    reply = "Could not reach the business API — try again shortly.";
  } else {
    reply = await assistantLiteReply(text);
  }

  const sent = await telegramSendMessage(chatId, reply);
  return NextResponse.json({ status: sent ? "ok" : "send_failed", delivered: sent });
}