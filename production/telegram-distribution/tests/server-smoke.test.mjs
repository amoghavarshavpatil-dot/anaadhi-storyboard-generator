import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

test("compiled server starts and exposes a safe health endpoint", async (context) => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "anaadhi-telegram-server-"));
  const port = 18_000 + Math.floor(Math.random() * 1_000);
  let logs = "";

  const child = spawn(process.execPath, ["dist/server.js"], {
    env: {
      ...process.env,
      PORT: String(port),
      DATA_FILE: path.join(directory, "store.json"),
      MCP_ACCESS_TOKEN: "test-only-access-token",
      TELEGRAM_BOT_TOKEN: "",
      TELEGRAM_BOT_USERNAME: "",
      TELEGRAM_CHANNEL_USERNAME: "ANAADHITheEpic",
      TELEGRAM_WEBHOOK_SECRET: "test-only-webhook-secret",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  child.stdout.on("data", (chunk) => {
    logs += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    logs += chunk.toString();
  });

  context.after(async () => {
    child.kill("SIGTERM");
    await rm(directory, { recursive: true, force: true });
  });

  let response;
  for (let attempt = 0; attempt < 40; attempt += 1) {
    if (child.exitCode !== null) {
      assert.fail(`Server exited before health check. Logs:\n${logs}`);
    }
    try {
      response = await fetch(`http://127.0.0.1:${port}/health`);
      if (response.ok) break;
    } catch {
      // Startup race; retry briefly.
    }
    await delay(100);
  }

  assert.ok(response, `Server did not become reachable. Logs:\n${logs}`);
  assert.equal(response.ok, true);
  const health = await response.json();
  assert.equal(health.ok, true);
  assert.equal(health.service, "anaadhi-telegram-distribution-plugin");
  assert.equal(health.releaseConfigured, false);
  assert.equal(health.mcpProtected, true);
});
