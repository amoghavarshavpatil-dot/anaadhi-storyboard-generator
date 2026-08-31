import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { JsonStore } from "../dist/store.js";

test("campaign opt-in, deduplication, statistics and deletion", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "anaadhi-telegram-store-"));
  const filename = path.join(directory, "store.json");

  try {
    const store = new JsonStore(filename);
    const release = await store.setRelease({
      movieTitle: "ANAADHI — THE EPIC",
      edition: "Official Full Movie",
      canonicalPostUrl: "https://t.me/ANAADHITheEpic/123",
      channelUsername: "ANAADHITheEpic",
      messageId: "123",
      runtimeMinutes: 120,
      fileSizeBytes: 1_234_567,
    });
    assert.equal(release.messageId, "123");

    let campaign = await store.createCampaign({
      name: "Trailer Wave 1",
      sourceLabel: "instagram-trailer",
      botStartUrl: null,
      inviteLink: null,
    });
    campaign = await store.setCampaignLinks(campaign.id, {
      botStartUrl: `https://t.me/ANAADHIReleaseBot?start=${campaign.code}`,
      inviteLink: null,
    });

    await store.recordStart("111", campaign.code);
    await store.recordStart("111", campaign.code);
    await store.recordStart("222", "organic");

    const targets = await store.getBroadcastTargets({
      campaignId: campaign.id,
      broadcastKey: "release-1",
      limit: 250,
      allowRepeat: false,
    });
    assert.deepEqual(targets, ["111"]);

    await store.recordBroadcastResults({
      campaignId: campaign.id,
      broadcastKey: "release-1",
      startedAt: new Date().toISOString(),
      successfulChatIds: ["111"],
      failedChatIds: [],
      inactiveChatIds: [],
    });

    const duplicateTargets = await store.getBroadcastTargets({
      campaignId: campaign.id,
      broadcastKey: "release-1",
      limit: 250,
      allowRepeat: false,
    });
    assert.deepEqual(duplicateTargets, []);

    const stats = await store.getCampaignStats(campaign.id);
    assert.equal(stats.campaign?.starts, 1);
    assert.equal(stats.campaign?.successfulDeliveries, 1);
    assert.equal(stats.activeOptInSubscribers, 2);

    assert.equal(await store.removeSubscriber("111"), true);
    const afterStop = await store.getCampaignStats(null);
    assert.equal(afterStop.activeOptInSubscribers, 1);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
