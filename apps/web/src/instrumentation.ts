export async function register() {
  if (process.env.NEXT_RUNTIME !== "nodejs") return;
  if (process.env.DATABASE_URL?.trim() && !process.env.API_INTERNAL_URL?.trim() && process.env.RUN_EMBEDDED_API !== "1") {
    console.error(
      "[rmd] DATABASE_URL is set but API_INTERNAL_URL is not — web-only image. Railway: clear Root directory (repo root) and redeploy combined. See RAILWAY_LOGIN_FIX.md",
    );
  }
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