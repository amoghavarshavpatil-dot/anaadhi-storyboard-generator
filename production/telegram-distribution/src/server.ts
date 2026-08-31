import { createHash, timingSafeEqual } from "node:crypto";
import express, {
  type NextFunction,
  type Request,
  type Response,
} from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import {
  config,
  requireTelegramConfiguration,
  telegramIsConfigured,
} from "./config.js";
import { JsonStore, type ReleaseRecord } from "./store.js";
import {
  campaignStartUrl,
  publicChannelUrl,
  shareUrl,
  sleep,
  TelegramApiError,
  TelegramClient,
  type InlineKeyboardButton,
  type TelegramUpdate,
} from "./telegram.js";

const store = new JsonStore(config.dataFile);
const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "1mb" }));

function jsonToolResult(summary: string, data: Record<string, unknown>) {
  return {
    content: [{ type: "text" as const, text: summary }],
    structuredContent: data,
  };
}

function cleanUsername(value: string): string {
  const username = value.trim().replace(/^@/, "");
  if (!/^[A-Za-z0-9_]{5,32}$/.test(username)) {
    throw new Error("Telegram username must be 5-32 letters, numbers or underscores.");
  }
  return username;
}

function canonicalizeMoviePost(
  inputUrl: string,
  requestedChannelUsername: string,
): { url: string; channelUsername: string; messageId: string } {
  const parsed = new URL(inputUrl);
  const host = parsed.hostname.toLowerCase();
  if (!new Set(["t.me", "www.t.me", "telegram.me", "www.telegram.me"]).has(host)) {
    throw new Error("The canonical movie post must be an official t.me Telegram link.");
  }

  const segments = parsed.pathname.split("/").filter(Boolean);
  if (segments[0] === "s") segments.shift();
  if (segments[0] === "c") {
    throw new Error("Use a public-channel post link, not a private /c/ message link.");
  }
  if (segments.length !== 2) {
    throw new Error("Expected a public post link like https://t.me/ChannelUsername/123.");
  }

  const channelUsername = cleanUsername(segments[0] ?? "");
  const requested = cleanUsername(requestedChannelUsername);
  if (channelUsername.toLowerCase() !== requested.toLowerCase()) {
    throw new Error(
      `The post belongs to @${channelUsername}, not the requested @${requested}.`,
    );
  }

  const messageId = segments[1] ?? "";
  if (!/^\d+$/.test(messageId)) {
    throw new Error("Telegram message ID must be numeric.");
  }

  return {
    url: `https://t.me/${channelUsername}/${messageId}`,
    channelUsername,
    messageId,
  };
}

function getTelegramClient(): TelegramClient {
  const { botToken } = requireTelegramConfiguration();
  return new TelegramClient(botToken);
}

function telegramButtons(release: ReleaseRecord): InlineKeyboardButton[][] {
  const sharing = shareUrl(
    release.canonicalPostUrl,
    `${release.movieTitle} — official whole-movie release`,
  );
  return [
    [{ text: "WATCH / DOWNLOAD WHOLE MOVIE", url: release.canonicalPostUrl }],
    [
      { text: "SHARE WITH TELEGRAM USERS", url: sharing },
      { text: "OFFICIAL CHANNEL", url: publicChannelUrl(release.channelUsername) },
    ],
  ];
}

function broadcastKeyFor(release: ReleaseRecord, campaignId: string | null): string {
  const digest = createHash("sha256")
    .update(`${release.canonicalPostUrl}|${campaignId ?? "all"}`)
    .digest("hex")
    .slice(0, 20);
  return `anaadhi-release-${release.messageId}-${digest}`;
}

function secretsMatch(actual: string | undefined, expected: string): boolean {
  if (!actual) return false;
  const left = Buffer.from(actual);
  const right = Buffer.from(expected);
  return left.length === right.length && timingSafeEqual(left, right);
}

function requireMcpAccess(req: Request, res: Response, next: NextFunction): void {
  if (!config.mcpAccessToken) {
    next();
    return;
  }
  const expected = `Bearer ${config.mcpAccessToken}`;
  if (!secretsMatch(req.header("authorization"), expected)) {
    res.status(401).json({ error: "Unauthorized MCP request." });
    return;
  }
  next();
}

function requireConfirmed(value: boolean): void {
  if (!value) {
    throw new Error("No Telegram write was performed because confirm was not true.");
  }
}

async function sendWithOneRateLimitRetry(input: {
  client: TelegramClient;
  chatId: string;
  text: string;
  silent: boolean;
  buttons: InlineKeyboardButton[][];
}): Promise<void> {
  try {
    await input.client.sendMessage({
      chatId: input.chatId,
      text: input.text,
      silent: input.silent,
      buttons: input.buttons,
    });
  } catch (error) {
    if (
      error instanceof TelegramApiError &&
      error.errorCode === 429 &&
      error.retryAfterSeconds !== null
    ) {
      await sleep((error.retryAfterSeconds + 1) * 1_000);
      await input.client.sendMessage({
        chatId: input.chatId,
        text: input.text,
        silent: input.silent,
        buttons: input.buttons,
      });
      return;
    }
    throw error;
  }
}

async function handlePrivateBotMessage(update: TelegramUpdate): Promise<void> {
  const message = update.message;
  if (!message || message.chat.type !== "private" || !message.text) return;

  const [rawCommand = "", rawArgument = ""] = message.text.trim().split(/\s+/, 2);
  const command = rawCommand.toLowerCase().split("@")[0] ?? "";
  const client = getTelegramClient();
  const chatId = String(message.chat.id);

  if (command === "/stop" || command === "/unsubscribe") {
    await store.removeSubscriber(chatId);
    await client.sendMessage({
      chatId,
      text: "You are unsubscribed. This bot will not send further ANAADHI release messages unless you start it again.",
    });
    return;
  }

  if (command === "/privacy") {
    await client.sendMessage({
      chatId,
      text:
        "Privacy: the bot stores your Telegram chat ID, opt-in time, campaign source and delivery history only to send the authorized ANAADHI release. Use /stop to delete your subscriber record.",
    });
    return;
  }

  if (command === "/help") {
    await client.sendMessage({
      chatId,
      text: "Commands: /movie — get the official whole-movie link; /stop — unsubscribe and delete your bot subscriber record; /privacy — read the data policy.",
    });
    return;
  }

  if (command === "/start") {
    const campaignCode = /^[A-Za-z0-9_-]{1,64}$/.test(rawArgument)
      ? rawArgument
      : "organic";
    await store.recordStart(chatId, campaignCode);
  } else if (command !== "/movie") {
    return;
  }

  const release = await store.getRelease();
  if (!release) {
    await client.sendMessage({
      chatId,
      text: "ANAADHI's official whole-movie Telegram release is not live yet. You are opted in and will receive the authorized link after release.",
    });
    return;
  }

  const greeting = message.from?.first_name
    ? `${message.from.first_name}, the official release is ready.`
    : "The official release is ready.";
  await client.sendMessage({
    chatId,
    text: `${greeting}\n\n${release.movieTitle}\n${release.edition}\n\nUse the official channel post below to watch, download and forward the whole movie.`,
    buttons: telegramButtons(release),
  });
}

app.get("/health", async (_req, res) => {
  const stats = await store.getCampaignStats(null);
  res.json({
    ok: true,
    service: "anaadhi-telegram-distribution-plugin",
    version: "0.1.0",
    telegramConfigured: telegramIsConfigured(),
    channelConfigured: Boolean(config.telegramChannelUsername),
    webhookBaseConfigured: Boolean(config.publicBaseUrl),
    webhookSecretConfigured: Boolean(config.telegramWebhookSecret),
    mcpProtected: Boolean(config.mcpAccessToken),
    releaseConfigured: Boolean(await store.getRelease()),
    activeOptInSubscribers: stats.activeOptInSubscribers,
  });
});

app.post("/telegram/webhook", async (req, res) => {
  if (!config.telegramWebhookSecret) {
    res.status(503).json({ error: "TELEGRAM_WEBHOOK_SECRET is not configured." });
    return;
  }
  if (
    !secretsMatch(
      req.header("x-telegram-bot-api-secret-token"),
      config.telegramWebhookSecret,
    )
  ) {
    res.status(401).json({ error: "Invalid Telegram webhook secret." });
    return;
  }

  try {
    const update = req.body as TelegramUpdate;
    const membership = update.my_chat_member;
    if (
      membership?.chat.type === "private" &&
      new Set(["kicked", "left"]).has(membership.new_chat_member.status)
    ) {
      await store.markSubscriberInactive(String(membership.chat.id));
    }
    await handlePrivateBotMessage(update);
    res.json({ ok: true });
  } catch (error) {
    console.error("Telegram webhook processing failed:", error);
    res.status(500).json({ error: "Webhook processing failed." });
  }
});

function createMcpServer(): McpServer {
  const server = new McpServer(
    {
      name: "anaadhi-telegram-distribution",
      version: "0.1.0",
    },
    {
      instructions:
        "Use this private tool-only app to manage the authorized ANAADHI whole-movie Telegram release. The full movie binary is uploaded once by the rights holder to the official public channel; tools register and distribute that canonical post. Never scrape Telegram users, send unsolicited messages, expose bot tokens, or mirror third-party copyrighted films. Broadcast only to users who explicitly started the bot and can unsubscribe with /stop.",
    },
  );

  server.registerTool(
    "get_release_status",
    {
      title: "Get ANAADHI Telegram release status",
      description:
        "Use this when the user asks whether the whole-movie post, Telegram bot, channel, webhook, audience or campaign system is ready.",
      inputSchema: {
        verifyTelegram: z
          .boolean()
          .optional()
          .describe("When true, call Telegram to verify bot identity and channel member count."),
      },
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
      },
    },
    async ({ verifyTelegram }) => {
      const release = await store.getRelease();
      const stats = await store.getCampaignStats(null);
      let botIdentity: Record<string, unknown> | null = null;
      let channelMemberCount: number | null = null;
      let telegramVerificationError: string | null = null;

      if (verifyTelegram) {
        try {
          const client = getTelegramClient();
          const identity = await client.getMe();
          botIdentity = {
            id: identity.id,
            username: identity.username,
            displayName: identity.first_name,
          };
          const { channelUsername } = requireTelegramConfiguration();
          channelMemberCount = await client.getChatMemberCount(channelUsername);
        } catch (error) {
          telegramVerificationError =
            error instanceof Error ? error.message : "Unknown Telegram verification error";
        }
      }

      const data = {
        release,
        telegramConfigured: telegramIsConfigured(),
        channelUsername: config.telegramChannelUsername ?? null,
        publicBaseUrl: config.publicBaseUrl ?? null,
        webhookConfigured: Boolean(
          config.publicBaseUrl && config.telegramWebhookSecret,
        ),
        mcpProtected: Boolean(config.mcpAccessToken),
        audience: {
          totalOptInSubscribers: stats.totalOptInSubscribers,
          activeOptInSubscribers: stats.activeOptInSubscribers,
        },
        botIdentity,
        channelMemberCount,
        telegramVerificationError,
      };
      return jsonToolResult(
        release
          ? `The canonical whole-movie post is registered at ${release.canonicalPostUrl}.`
          : "The plugin is staged, but no canonical whole-movie Telegram post is registered yet.",
        data,
      );
    },
  );

  server.registerTool(
    "set_canonical_movie_post",
    {
      title: "Register the official whole-movie Telegram post",
      description:
        "Use this after the rights holder uploads the complete movie once to the official public Telegram channel and supplies that post link.",
      inputSchema: {
        movieTitle: z.string().min(1).max(160),
        edition: z.string().min(1).max(120).optional(),
        canonicalPostUrl: z.string().url(),
        channelUsername: z.string().min(5).max(33).optional(),
        runtimeMinutes: z.number().positive().max(600).optional(),
        fileSizeBytes: z.number().int().positive().optional(),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
      },
    },
    async ({
      movieTitle,
      edition,
      canonicalPostUrl,
      channelUsername,
      runtimeMinutes,
      fileSizeBytes,
    }) => {
      const channel = cleanUsername(
        channelUsername ?? config.telegramChannelUsername ?? "",
      );
      const canonical = canonicalizeMoviePost(canonicalPostUrl, channel);
      const release = await store.setRelease({
        movieTitle: movieTitle.trim(),
        edition: edition?.trim() || "Official Full Movie",
        canonicalPostUrl: canonical.url,
        channelUsername: canonical.channelUsername,
        messageId: canonical.messageId,
        runtimeMinutes: runtimeMinutes ?? null,
        fileSizeBytes: fileSizeBytes ?? null,
      });
      return jsonToolResult(
        `Registered ${release.movieTitle} as the single authorized Telegram whole-movie source.`,
        { release },
      );
    },
  );

  server.registerTool(
    "create_distribution_campaign",
    {
      title: "Create a Telegram distribution campaign",
      description:
        "Use this to create a trackable bot start link for a specific promoter, community, language, poster, trailer or release wave. It may also create a channel invite link when explicitly confirmed.",
      inputSchema: {
        name: z.string().min(1).max(100),
        sourceLabel: z.string().max(100).optional(),
        createChannelInvite: z.boolean().optional(),
        inviteExpiresAt: z.string().datetime().optional(),
        confirmExternalInvite: z.boolean().optional(),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
      },
    },
    async ({
      name,
      sourceLabel,
      createChannelInvite,
      inviteExpiresAt,
      confirmExternalInvite,
    }) => {
      if (createChannelInvite) requireConfirmed(Boolean(confirmExternalInvite));

      const campaign = await store.createCampaign({
        name: name.trim(),
        sourceLabel: sourceLabel?.trim() || null,
        botStartUrl: null,
        inviteLink: null,
      });

      const botStart = config.telegramBotUsername
        ? campaignStartUrl(config.telegramBotUsername, campaign.code)
        : null;
      let inviteLink: string | null = null;
      if (createChannelInvite) {
        const { channelUsername } = requireTelegramConfiguration();
        const result = await getTelegramClient().createChatInviteLink({
          channelUsername,
          name: campaign.name,
          ...(inviteExpiresAt ? { expireAt: inviteExpiresAt } : {}),
        });
        inviteLink = result.invite_link;
      }

      const updated = await store.setCampaignLinks(campaign.id, {
        botStartUrl: botStart,
        inviteLink,
      });
      const release = await store.getRelease();
      const preferredShareTarget = botStart ?? inviteLink ?? release?.canonicalPostUrl ?? null;
      const telegramShareUrl = preferredShareTarget
        ? shareUrl(
            preferredShareTarget,
            "Watch and download ANAADHI from its official Telegram release source.",
          )
        : null;

      return jsonToolResult(
        `Created campaign “${updated.name}” with attribution code ${updated.code}.`,
        {
          campaign: updated,
          campaignEntryUrl: preferredShareTarget,
          telegramShareUrl,
          canonicalMovieUrl: release?.canonicalPostUrl ?? null,
        },
      );
    },
  );

  server.registerTool(
    "publish_release_announcement",
    {
      title: "Publish the whole-movie release announcement",
      description:
        "Use this when the user explicitly approves posting an announcement in the official Telegram channel that points to the registered whole-movie post.",
      inputSchema: {
        caption: z.string().min(1).max(3_500),
        silent: z.boolean().optional(),
        confirm: z.boolean(),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
      },
    },
    async ({ caption, silent, confirm }) => {
      requireConfirmed(confirm);
      const release = await store.getRelease();
      if (!release) throw new Error("Register the canonical whole-movie post first.");
      const client = getTelegramClient();
      const sent = await client.sendMessage({
        chatId: `@${release.channelUsername}`,
        text: `${caption.trim()}\n\nOfficial whole-movie source:\n${release.canonicalPostUrl}`,
        silent: silent ?? false,
        buttons: telegramButtons(release),
      });
      const announcementUrl = `https://t.me/${release.channelUsername}/${sent.message_id}`;
      return jsonToolResult(
        "Published the approved release announcement to the official Telegram channel.",
        {
          announcementMessageId: sent.message_id,
          announcementUrl,
          canonicalMovieUrl: release.canonicalPostUrl,
        },
      );
    },
  );

  server.registerTool(
    "broadcast_opt_in_release",
    {
      title: "Broadcast the whole-movie link to opted-in viewers",
      description:
        "Use this only after explicit approval to send the official whole-movie post to viewers who voluntarily started the bot. It sends one controlled batch and excludes prior recipients by default.",
      inputSchema: {
        caption: z.string().min(1).max(3_000),
        campaignId: z.string().uuid().optional(),
        maxRecipients: z.number().int().min(1).max(250).optional(),
        broadcastKey: z.string().min(1).max(80).optional(),
        allowRepeat: z.boolean().optional(),
        silent: z.boolean().optional(),
        confirm: z.boolean(),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: false,
        openWorldHint: true,
      },
    },
    async ({
      caption,
      campaignId,
      maxRecipients,
      broadcastKey,
      allowRepeat,
      silent,
      confirm,
    }) => {
      requireConfirmed(confirm);
      const release = await store.getRelease();
      if (!release) throw new Error("Register the canonical whole-movie post first.");
      const campaign = campaignId ? await store.getCampaign(campaignId) : null;
      if (campaignId && !campaign) throw new Error(`Campaign not found: ${campaignId}`);

      const key =
        broadcastKey?.trim() || broadcastKeyFor(release, campaignId ?? null);
      const targets = await store.getBroadcastTargets({
        campaignId: campaignId ?? null,
        broadcastKey: key,
        limit: maxRecipients ?? 250,
        allowRepeat: allowRepeat ?? false,
      });
      if (targets.length === 0) {
        return jsonToolResult(
          "No eligible opted-in viewers remained for this broadcast batch.",
          {
            campaignId: campaignId ?? null,
            broadcastKey: key,
            requestedRecipients: 0,
            successful: 0,
            failed: 0,
          },
        );
      }

      const startedAt = new Date().toISOString();
      const client = getTelegramClient();
      const text = `${caption.trim()}\n\n${release.movieTitle}\n${release.edition}\n\nOfficial watch/download source:\n${release.canonicalPostUrl}`;
      const successfulChatIds: string[] = [];
      const failedChatIds: string[] = [];
      const inactiveChatIds: string[] = [];
      const perSecond = config.broadcastPerSecond;

      for (let offset = 0; offset < targets.length; offset += perSecond) {
        const batch = targets.slice(offset, offset + perSecond);
        const outcomes = await Promise.all(
          batch.map(async (chatId) => {
            try {
              await sendWithOneRateLimitRetry({
                client,
                chatId,
                text,
                silent: silent ?? false,
                buttons: telegramButtons(release),
              });
              return { chatId, ok: true, inactive: false };
            } catch (error) {
              const inactive =
                error instanceof TelegramApiError &&
                new Set([400, 403]).has(error.errorCode);
              return { chatId, ok: false, inactive };
            }
          }),
        );

        for (const outcome of outcomes) {
          if (outcome.ok) successfulChatIds.push(outcome.chatId);
          else failedChatIds.push(outcome.chatId);
          if (outcome.inactive) inactiveChatIds.push(outcome.chatId);
        }
        if (offset + perSecond < targets.length) await sleep(1_000);
      }

      const record = await store.recordBroadcastResults({
        campaignId: campaignId ?? null,
        broadcastKey: key,
        startedAt,
        successfulChatIds,
        failedChatIds,
        inactiveChatIds,
      });
      const remaining = await store.getBroadcastTargets({
        campaignId: campaignId ?? null,
        broadcastKey: key,
        limit: 1,
        allowRepeat: false,
      });

      return jsonToolResult(
        `Completed one opted-in release batch: ${record.successful} delivered, ${record.failed} failed.`,
        {
          broadcast: record,
          remainingEligibleViewers: remaining.length > 0,
          canonicalMovieUrl: release.canonicalPostUrl,
        },
      );
    },
  );

  server.registerTool(
    "get_distribution_stats",
    {
      title: "Get Telegram distribution statistics",
      description:
        "Use this to review opt-in audience size, campaign starts, delivery totals and optionally the official channel member count.",
      inputSchema: {
        campaignId: z.string().uuid().optional(),
        verifyChannelMemberCount: z.boolean().optional(),
      },
      annotations: {
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
      },
    },
    async ({ campaignId, verifyChannelMemberCount }) => {
      const stats = await store.getCampaignStats(campaignId ?? null);
      let channelMemberCount: number | null = null;
      let channelVerificationError: string | null = null;
      if (verifyChannelMemberCount) {
        try {
          const { channelUsername } = requireTelegramConfiguration();
          channelMemberCount = await getTelegramClient().getChatMemberCount(
            channelUsername,
          );
        } catch (error) {
          channelVerificationError =
            error instanceof Error ? error.message : "Unknown channel verification error";
        }
      }
      return jsonToolResult("Retrieved ANAADHI Telegram distribution statistics.", {
        stats,
        channelMemberCount,
        channelVerificationError,
      });
    },
  );

  server.registerTool(
    "configure_telegram_webhook",
    {
      title: "Connect the deployed plugin to the Telegram bot",
      description:
        "Use this after the plugin has a stable public HTTPS domain and the user explicitly approves registering its webhook with Telegram.",
      inputSchema: {
        confirm: z.boolean(),
      },
      annotations: {
        readOnlyHint: false,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: true,
      },
    },
    async ({ confirm }) => {
      requireConfirmed(confirm);
      if (!config.publicBaseUrl) {
        throw new Error("PUBLIC_BASE_URL is not configured.");
      }
      if (!config.telegramWebhookSecret) {
        throw new Error("TELEGRAM_WEBHOOK_SECRET is not configured.");
      }
      const webhookUrl = `${config.publicBaseUrl}/telegram/webhook`;
      const configured = await getTelegramClient().setWebhook({
        url: webhookUrl,
        secretToken: config.telegramWebhookSecret,
      });
      return jsonToolResult("Connected Telegram to the deployed webhook.", {
        configured,
        webhookUrl,
      });
    },
  );

  return server;
}

app.post("/mcp", requireMcpAccess, async (req, res) => {
  const server = createMcpServer();
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
  });

  res.on("close", () => {
    void transport.close();
    void server.close();
  });

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("MCP request failed:", error);
    if (!res.headersSent) {
      res.status(500).json({ error: "MCP request failed." });
    }
  }
});

app.get("/mcp", requireMcpAccess, (_req, res) => {
  res.status(405).json({ error: "Use POST for this stateless MCP endpoint." });
});

app.delete("/mcp", requireMcpAccess, (_req, res) => {
  res.status(405).json({ error: "This stateless MCP endpoint has no sessions." });
});

app.listen(config.port, () => {
  console.log(`ANAADHI Telegram distribution plugin listening on port ${config.port}.`);
  if (!config.mcpAccessToken) {
    console.warn(
      "MCP_ACCESS_TOKEN is empty. Do not expose this server publicly until access control is configured.",
    );
  }
});
