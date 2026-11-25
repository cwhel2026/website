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

  if (!text) {
    await telegramSendMessage(chatId, "Send a text message or use /start");
    return NextResponse.json({ status: "no_text" });
  }

  let reply: string;
  if (text === "/start" || text.startsWith("/start ")) {
    reply = TELEGRAM_START_MESSAGE;
  } else if (process.env.API_INTERNAL_URL?.trim()) {
    reply = "Use the combined FastAPI path for full assistant tools.";
  } else {
    reply = await assistantLiteReply(text);
  }

  const sent = await telegramSendMessage(chatId, reply);
  return NextResponse.json({ status: sent ? "ok" : "send_failed", delivered: sent });
}