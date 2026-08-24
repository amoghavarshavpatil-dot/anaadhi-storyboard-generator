import path from "node:path";

function clean(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function normalizeUsername(value: string | undefined): string | undefined {
  return clean(value)?.replace(/^@/, "");
}

function integerEnv(
  name: string,
  fallback: number,
  minimum: number,
  maximum: number,
): number {
  const raw = clean(process.env[name]);
  if (!raw) return fallback;

  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error(`${name} must be an integer from ${minimum} to ${maximum}.`);
  }
  return parsed;
}

const rawPublicBaseUrl = clean(process.env.PUBLIC_BASE_URL)?.replace(/\/+$/, "");

export const config = Object.freeze({
  port: integerEnv("PORT", 8000, 1, 65_535),
  publicBaseUrl: rawPublicBaseUrl,
  dataFile:
    clean(process.env.DATA_FILE) ??
    path.resolve(process.cwd(), "data", "anaadhi-telegram-distribution.json"),
  mcpAccessToken: clean(process.env.MCP_ACCESS_TOKEN),
  telegramBotToken: clean(process.env.TELEGRAM_BOT_TOKEN),
  telegramBotUsername: normalizeUsername(process.env.TELEGRAM_BOT_USERNAME),
  telegramChannelUsername: normalizeUsername(process.env.TELEGRAM_CHANNEL_USERNAME),
  telegramWebhookSecret: clean(process.env.TELEGRAM_WEBHOOK_SECRET),
  broadcastPerSecond: integerEnv("BROADCAST_PER_SECOND", 25, 1, 25),
});

export function telegramIsConfigured(): boolean {
  return Boolean(config.telegramBotToken && config.telegramBotUsername);
}

export function requireTelegramConfiguration(): {
  botToken: string;
  botUsername: string;
  channelUsername: string;
} {
  if (!config.telegramBotToken) {
    throw new Error("TELEGRAM_BOT_TOKEN is not configured.");
  }
  if (!config.telegramBotUsername) {
    throw new Error("TELEGRAM_BOT_USERNAME is not configured.");
  }
  if (!config.telegramChannelUsername) {
    throw new Error("TELEGRAM_CHANNEL_USERNAME is not configured.");
  }

  return {
    botToken: config.telegramBotToken,
    botUsername: config.telegramBotUsername,
    channelUsername: config.telegramChannelUsername,
  };
}
