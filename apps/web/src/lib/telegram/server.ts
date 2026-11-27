/** Telegram Bot API helpers for Next.js (single Railway web service). */

import { normaliseTelegramWebhookSecret } from "@/lib/telegram/secret";

const TELEGRAM_API = "https://api.telegram.org";

export function expectedWebhookSecret(): string {
  const raw = process.env.TELEGRAM_WEBHOOK_SECRET?.trim() ?? "";
  return normaliseTelegramWebhookSecret(raw);
}

export function telegramAdminIds(): number[] {
  const raw = process.env.TELEGRAM_ADMIN_IDS ?? "";
  return raw
    .split(",")
    .map((s) => s.trim())
    .filter((s) => /^\d+$/.test(s))
    .map((s) => Number(s));
}

export function publicSiteBaseUrl(): string | null {
  const explicit = (process.env.PUBLIC_API_BASE_URL ?? "").trim().replace(/\/$/, "");
  if (explicit) return explicit;
  const site = (process.env.NEXT_PUBLIC_SITE_URL ?? "").trim().replace(/\/$/, "");
  if (site) return site;
  const railway = (process.env.RAILWAY_PUBLIC_DOMAIN ?? "").trim();
  if (railway) return `https://${railway}`;
  return null;
}

export async function telegramSendMessage(chatId: number, text: string): Promise<boolean> {
  const token = process.env.TELEGRAM_BOT_TOKEN?.trim();
  if (!token) return false;
  const res = await fetch(`${TELEGRAM_API}/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text: text.slice(0, 4096) }),
  });
  const data = (await res.json()) as { ok?: boolean };
  return Boolean(res.ok && data.ok);
}

export async function registerTelegramWebhook(): Promise<{
  ok: boolean;
  webhookUrl?: string;
  error?: string;
}> {
  const token = process.env.TELEGRAM_BOT_TOKEN?.trim();
  const rawSecret = process.env.TELEGRAM_WEBHOOK_SECRET?.trim();
  const secret = rawSecret ? normaliseTelegramWebhookSecret(rawSecret) : "";
  const base = publicSiteBaseUrl();
  if (!token || !secret || !base) {
    return { ok: false, error: "TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, or site URL missing" };
  }
  const webhookUrl = `${base}/api/v1/telegram/webhook`;
  const set = await fetch(`${TELEGRAM_API}/bot${token}/setWebhook`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      url: webhookUrl,
      secret_token: secret,
      drop_pending_updates: true,
      allowed_updates: ["message"],
    }),
  });
  const body = (await set.json()) as { ok?: boolean; description?: string };
  if (!set.ok || !body.ok) {
    return { ok: false, error: body.description ?? `HTTP ${set.status}` };
  }
  return { ok: true, webhookUrl };
}

export const TELEGRAM_START_MESSAGE =
  "SurfaceCoat assistant is connected.\n\n" +
  "Ask about today's jobs, weather, quotations, or marketing — private owner access only.";

const seenUpdates = new Set<number>();
const SEEN_MAX = 500;

export function markUpdateSeen(updateId: number): boolean {
  if (seenUpdates.has(updateId)) return true;
  seenUpdates.add(updateId);
  if (seenUpdates.size > SEEN_MAX) {
    const first = seenUpdates.values().next().value;
    if (first !== undefined) seenUpdates.delete(first);
  }
  return false;
}