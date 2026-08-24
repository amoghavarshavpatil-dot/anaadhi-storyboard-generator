import { randomBytes, randomUUID } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import path from "node:path";

export interface ReleaseRecord {
  movieTitle: string;
  edition: string;
  canonicalPostUrl: string;
  channelUsername: string;
  messageId: string;
  runtimeMinutes: number | null;
  fileSizeBytes: number | null;
  updatedAt: string;
}

export interface CampaignRecord {
  id: string;
  code: string;
  name: string;
  sourceLabel: string | null;
  createdAt: string;
  active: boolean;
  starts: number;
  successfulDeliveries: number;
  failedDeliveries: number;
  botStartUrl: string | null;
  inviteLink: string | null;
}

interface SubscriberRecord {
  chatId: string;
  active: boolean;
  subscribedAt: string;
  lastSeenAt: string;
  campaignCodes: string[];
  startCount: number;
  deliveryKeys: string[];
}

interface BroadcastRecord {
  id: string;
  campaignId: string | null;
  broadcastKey: string;
  startedAt: string;
  completedAt: string;
  requestedRecipients: number;
  successful: number;
  failed: number;
}

interface Database {
  version: 1;
  release: ReleaseRecord | null;
  campaigns: Record<string, CampaignRecord>;
  subscribers: Record<string, SubscriberRecord>;
  broadcasts: BroadcastRecord[];
}

export interface CampaignStats {
  campaign: CampaignRecord | null;
  totalOptInSubscribers: number;
  activeOptInSubscribers: number;
  campaignActiveSubscribers: number | null;
  broadcasts: {
    total: number;
    successfulDeliveries: number;
    failedDeliveries: number;
  };
}

function emptyDatabase(): Database {
  return {
    version: 1,
    release: null,
    campaigns: {},
    subscribers: {},
    broadcasts: [],
  };
}

function slug(value: string): string {
  const result = value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 36);
  return result || "campaign";
}

function now(): string {
  return new Date().toISOString();
}

export class JsonStore {
  private queue: Promise<void> = Promise.resolve();

  constructor(private readonly filename: string) {}

  private async readDatabase(): Promise<Database> {
    try {
      const raw = await readFile(this.filename, "utf8");
      const parsed = JSON.parse(raw) as Database;
      if (parsed.version !== 1) {
        throw new Error(`Unsupported database version: ${String(parsed.version)}`);
      }
      return parsed;
    } catch (error) {
      const code = (error as NodeJS.ErrnoException).code;
      if (code === "ENOENT") return emptyDatabase();
      throw error;
    }
  }

  private async writeDatabase(database: Database): Promise<void> {
    await mkdir(path.dirname(this.filename), { recursive: true });
    const temporary = `${this.filename}.${process.pid}.${Date.now()}.tmp`;
    await writeFile(temporary, `${JSON.stringify(database, null, 2)}\n`, {
      encoding: "utf8",
      mode: 0o600,
    });
    await rename(temporary, this.filename);
  }

  private mutate<T>(operation: (database: Database) => T | Promise<T>): Promise<T> {
    const run = this.queue.then(async () => {
      const database = await this.readDatabase();
      const result = await operation(database);
      await this.writeDatabase(database);
      return result;
    });

    this.queue = run.then(
      () => undefined,
      () => undefined,
    );
    return run;
  }

  async snapshot(): Promise<Database> {
    await this.queue;
    return this.readDatabase();
  }

  async getRelease(): Promise<ReleaseRecord | null> {
    return (await this.snapshot()).release;
  }

  async setRelease(
    input: Omit<ReleaseRecord, "updatedAt">,
  ): Promise<ReleaseRecord> {
    return this.mutate((database) => {
      const release: ReleaseRecord = { ...input, updatedAt: now() };
      database.release = release;
      return release;
    });
  }

  async createCampaign(input: {
    name: string;
    sourceLabel: string | null;
    botStartUrl: string | null;
    inviteLink: string | null;
  }): Promise<CampaignRecord> {
    return this.mutate((database) => {
      let code = `${slug(input.name)}-${randomBytes(4).toString("hex")}`;
      while (Object.values(database.campaigns).some((item) => item.code === code)) {
        code = `${slug(input.name)}-${randomBytes(4).toString("hex")}`;
      }

      const campaign: CampaignRecord = {
        id: randomUUID(),
        code,
        name: input.name,
        sourceLabel: input.sourceLabel,
        createdAt: now(),
        active: true,
        starts: 0,
        successfulDeliveries: 0,
        failedDeliveries: 0,
        botStartUrl: input.botStartUrl,
        inviteLink: input.inviteLink,
      };
      database.campaigns[campaign.id] = campaign;
      return campaign;
    });
  }

  async setCampaignLinks(
    campaignId: string,
    links: { botStartUrl: string | null; inviteLink: string | null },
  ): Promise<CampaignRecord> {
    return this.mutate((database) => {
      const campaign = database.campaigns[campaignId];
      if (!campaign) throw new Error(`Campaign not found: ${campaignId}`);
      campaign.botStartUrl = links.botStartUrl;
      campaign.inviteLink = links.inviteLink;
      return campaign;
    });
  }

  async recordStart(chatId: string, campaignCode: string): Promise<void> {
    await this.mutate((database) => {
      let campaign = Object.values(database.campaigns).find(
        (item) => item.code === campaignCode,
      );

      if (!campaign && campaignCode === "organic") {
        campaign = {
          id: randomUUID(),
          code: "organic",
          name: "Organic Telegram discovery",
          sourceLabel: "telegram-organic",
          createdAt: now(),
          active: true,
          starts: 0,
          successfulDeliveries: 0,
          failedDeliveries: 0,
          botStartUrl: null,
          inviteLink: null,
        };
        database.campaigns[campaign.id] = campaign;
      }

      const timestamp = now();
      const existing = database.subscribers[chatId];
      const subscriber: SubscriberRecord = existing ?? {
        chatId,
        active: true,
        subscribedAt: timestamp,
        lastSeenAt: timestamp,
        campaignCodes: [],
        startCount: 0,
        deliveryKeys: [],
      };

      const isNewCampaign = !subscriber.campaignCodes.includes(campaignCode);
      if (isNewCampaign) subscriber.campaignCodes.push(campaignCode);
      subscriber.active = true;
      subscriber.lastSeenAt = timestamp;
      subscriber.startCount += 1;
      database.subscribers[chatId] = subscriber;

      if (campaign && isNewCampaign) campaign.starts += 1;
    });
  }

  async removeSubscriber(chatId: string): Promise<boolean> {
    return this.mutate((database) => {
      const existed = Boolean(database.subscribers[chatId]);
      delete database.subscribers[chatId];
      return existed;
    });
  }

  async markSubscriberInactive(chatId: string): Promise<void> {
    await this.mutate((database) => {
      const subscriber = database.subscribers[chatId];
      if (subscriber) {
        subscriber.active = false;
        subscriber.lastSeenAt = now();
      }
    });
  }

  async getCampaign(campaignId: string): Promise<CampaignRecord | null> {
    const database = await this.snapshot();
    return database.campaigns[campaignId] ?? null;
  }

  async getCampaignStats(campaignId: string | null): Promise<CampaignStats> {
    const database = await this.snapshot();
    const subscribers = Object.values(database.subscribers);
    const campaign = campaignId ? (database.campaigns[campaignId] ?? null) : null;
    if (campaignId && !campaign) throw new Error(`Campaign not found: ${campaignId}`);

    const relevantBroadcasts = campaignId
      ? database.broadcasts.filter((item) => item.campaignId === campaignId)
      : database.broadcasts;

    return {
      campaign,
      totalOptInSubscribers: subscribers.length,
      activeOptInSubscribers: subscribers.filter((item) => item.active).length,
      campaignActiveSubscribers: campaign
        ? subscribers.filter(
            (item) => item.active && item.campaignCodes.includes(campaign.code),
          ).length
        : null,
      broadcasts: {
        total: relevantBroadcasts.length,
        successfulDeliveries: relevantBroadcasts.reduce(
          (sum, item) => sum + item.successful,
          0,
        ),
        failedDeliveries: relevantBroadcasts.reduce(
          (sum, item) => sum + item.failed,
          0,
        ),
      },
    };
  }

  async getBroadcastTargets(input: {
    campaignId: string | null;
    broadcastKey: string;
    limit: number;
    allowRepeat: boolean;
  }): Promise<string[]> {
    const database = await this.snapshot();
    const campaign = input.campaignId
      ? (database.campaigns[input.campaignId] ?? null)
      : null;
    if (input.campaignId && !campaign) {
      throw new Error(`Campaign not found: ${input.campaignId}`);
    }

    return Object.values(database.subscribers)
      .filter((subscriber) => subscriber.active)
      .filter((subscriber) =>
        campaign ? subscriber.campaignCodes.includes(campaign.code) : true,
      )
      .filter((subscriber) =>
        input.allowRepeat ? true : !subscriber.deliveryKeys.includes(input.broadcastKey),
      )
      .sort((a, b) => a.subscribedAt.localeCompare(b.subscribedAt))
      .slice(0, input.limit)
      .map((subscriber) => subscriber.chatId);
  }

  async recordBroadcastResults(input: {
    campaignId: string | null;
    broadcastKey: string;
    startedAt: string;
    successfulChatIds: string[];
    failedChatIds: string[];
    inactiveChatIds: string[];
  }): Promise<BroadcastRecord> {
    return this.mutate((database) => {
      for (const chatId of input.successfulChatIds) {
        const subscriber = database.subscribers[chatId];
        if (subscriber && !subscriber.deliveryKeys.includes(input.broadcastKey)) {
          subscriber.deliveryKeys.push(input.broadcastKey);
        }
      }

      for (const chatId of input.inactiveChatIds) {
        const subscriber = database.subscribers[chatId];
        if (subscriber) subscriber.active = false;
      }

      if (input.campaignId) {
        const campaign = database.campaigns[input.campaignId];
        if (campaign) {
          campaign.successfulDeliveries += input.successfulChatIds.length;
          campaign.failedDeliveries += input.failedChatIds.length;
        }
      }

      const record: BroadcastRecord = {
        id: randomUUID(),
        campaignId: input.campaignId,
        broadcastKey: input.broadcastKey,
        startedAt: input.startedAt,
        completedAt: now(),
        requestedRecipients:
          input.successfulChatIds.length + input.failedChatIds.length,
        successful: input.successfulChatIds.length,
        failed: input.failedChatIds.length,
      };
      database.broadcasts.push(record);
      if (database.broadcasts.length > 1_000) {
        database.broadcasts.splice(0, database.broadcasts.length - 1_000);
      }
      return record;
    });
  }
}
