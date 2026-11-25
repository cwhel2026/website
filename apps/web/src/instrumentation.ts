export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  if (process.env.API_INTERNAL_URL?.trim()) return;
  if (process.env.TELEGRAM_AUTO_REGISTER_WEBHOOK === "false") return;

  const { registerTelegramWebhook } = await import("@/lib/telegram/server");
  const result = await registerTelegramWebhook();
  if (result.ok) {
    console.info("[telegram] webhook registered", result.webhookUrl);
  } else if (process.env.TELEGRAM_BOT_TOKEN) {
    console.warn("[telegram] webhook registration skipped:", result.error);
  }
}