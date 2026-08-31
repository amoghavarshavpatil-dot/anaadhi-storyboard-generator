export interface TelegramUser {
  id: number;
  is_bot: boolean;
  first_name: string;
  username?: string;
}

export interface TelegramChat {
  id: number;
  type: "private" | "group" | "supergroup" | "channel";
  username?: string;
}

export interface TelegramMessage {
  message_id: number;
  from?: TelegramUser;
  chat: TelegramChat;
  date: number;
  text?: string;
}

export interface TelegramChatMemberUpdated {
  chat: TelegramChat;
  from: TelegramUser;
  date: number;
  old_chat_member: { status: string; user: TelegramUser };
  new_chat_member: { status: string; user: TelegramUser };
}

export interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
  my_chat_member?: TelegramChatMemberUpdated;
  chat_member?: TelegramChatMemberUpdated;
}

interface TelegramFailure {
  ok: false;
  error_code: number;
  description: string;
  parameters?: {
    retry_after?: number;
    migrate_to_chat_id?: number;
  };
}

interface TelegramSuccess<T> {
  ok: true;
  result: T;
}

type TelegramResponse<T> = TelegramSuccess<T> | TelegramFailure;

export class TelegramApiError extends Error {
  constructor(
    message: string,
    readonly errorCode: number,
    readonly retryAfterSeconds: number | null,
  ) {
    super(message);
    this.name = "TelegramApiError";
  }
}

export interface InlineKeyboardButton {
  text: string;
  url: string;
}

export interface TelegramBotIdentity {
  id: number;
  is_bot: true;
  first_name: string;
  username: string;
}

export class TelegramClient {
  constructor(private readonly botToken: string) {}

  private async request<T>(
    method: string,
    payload: Record<string, unknown>,
  ): Promise<T> {
    const response = await fetch(
      `https://api.telegram.org/bot${this.botToken}/${method}`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
        signal: AbortSignal.timeout(20_000),
      },
    );

    let body: TelegramResponse<T>;
    try {
      body = (await response.json()) as TelegramResponse<T>;
    } catch {
      throw new TelegramApiError(
        `Telegram ${method} returned non-JSON HTTP ${response.status}.`,
        response.status,
        null,
      );
    }

    if (!body.ok) {
      throw new TelegramApiError(
        body.description,
        body.error_code,
        body.parameters?.retry_after ?? null,
      );
    }
    return body.result;
  }

  getMe(): Promise<TelegramBotIdentity> {
    return this.request<TelegramBotIdentity>("getMe", {});
  }

  sendMessage(input: {
    chatId: string | number;
    text: string;
    silent?: boolean;
    buttons?: InlineKeyboardButton[][];
  }): Promise<TelegramMessage> {
    const payload: Record<string, unknown> = {
      chat_id: input.chatId,
      text: input.text,
      disable_notification: input.silent ?? false,
    };
    if (input.buttons?.length) {
      payload.reply_markup = { inline_keyboard: input.buttons };
    }
    return this.request<TelegramMessage>("sendMessage", payload);
  }

  createChatInviteLink(input: {
    channelUsername: string;
    name: string;
    expireAt?: string;
  }): Promise<{ invite_link: string }> {
    const payload: Record<string, unknown> = {
      chat_id: `@${input.channelUsername.replace(/^@/, "")}`,
      name: input.name.slice(0, 32),
    };
    if (input.expireAt) {
      const epochSeconds = Math.floor(new Date(input.expireAt).getTime() / 1000);
      if (!Number.isFinite(epochSeconds)) {
        throw new Error("expireAt is not a valid ISO date-time.");
      }
      payload.expire_date = epochSeconds;
    }
    return this.request<{ invite_link: string }>("createChatInviteLink", payload);
  }

  getChatMemberCount(channelUsername: string): Promise<number> {
    return this.request<number>("getChatMemberCount", {
      chat_id: `@${channelUsername.replace(/^@/, "")}`,
    });
  }

  setWebhook(input: {
    url: string;
    secretToken: string;
  }): Promise<boolean> {
    return this.request<boolean>("setWebhook", {
      url: input.url,
      secret_token: input.secretToken,
      allowed_updates: ["message", "my_chat_member", "chat_member"],
      drop_pending_updates: false,
    });
  }
}

export function campaignStartUrl(botUsername: string, campaignCode: string): string {
  return `https://t.me/${botUsername.replace(/^@/, "")}?start=${encodeURIComponent(campaignCode)}`;
}

export function publicChannelUrl(channelUsername: string): string {
  return `https://t.me/${channelUsername.replace(/^@/, "")}`;
}

export function shareUrl(url: string, text: string): string {
  const query = new URLSearchParams({ url, text });
  return `https://t.me/share/url?${query.toString()}`;
}

export function sleep(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}
