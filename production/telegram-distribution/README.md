# ANAADHI Telegram Whole-Movie Distribution Plugin

Private, tool-only ChatGPT/MCP connector for the authorized Telegram release of **ANAADHI — THE EPIC**.

## What this system does

The full movie is uploaded **once** by the rights holder to the official public Telegram channel. The connector then treats that public post as the single canonical watch/download source and can:

- register and validate the official `t.me/<channel>/<message-id>` movie post;
- create trackable campaign links for posters, trailers, promoters, language audiences and release waves;
- let viewers opt in through an official Telegram bot;
- return the movie link when a viewer uses `/start` or `/movie`;
- publish an approved release announcement in the official channel;
- send controlled batches only to viewers who explicitly started the bot;
- avoid repeat delivery by default;
- count campaign starts, opted-in viewers, deliveries and channel members;
- delete a viewer's subscriber record when they use `/stop`;
- register a secret-protected Telegram webhook after deployment.

It does **not** scrape Telegram users, buy fake members, mass-DM strangers, evade copyright enforcement or mirror third-party films.

## Why the movie is not uploaded by the bot

Telegram's ordinary hosted Bot API is designed for much smaller bot uploads than a feature-length master. The rights holder should upload the final Telegram edition directly through their own Telegram account, copy the public channel post link, and register that link with `set_canonical_movie_post`. Every campaign then points back to the same post, preserving its views, forwards and identity.

Before uploading, export a Telegram release copy that fits the upload limit currently shown by the rights holder's Telegram account while retaining the approved master separately for Filmhub/OTT delivery.

## Audience flow

```text
poster / trailer / promoter / community
        ↓ unique campaign link
official ANAADHI release bot
        ↓ explicit viewer opt-in
canonical whole-movie channel post
        ↓ watch · download · forward
new viewers enter through the same official source
```

Bots cannot initiate a private conversation with arbitrary Telegram users. The audience must first open a campaign link and press **Start**. This opt-in constraint is built into the connector.

## MCP tools

| Tool | Purpose |
|---|---|
| `get_release_status` | Check release, bot, webhook and audience readiness |
| `set_canonical_movie_post` | Register the one authorized whole-movie post |
| `create_distribution_campaign` | Create an attributed bot link and optional channel invite |
| `publish_release_announcement` | Post an explicitly approved channel announcement |
| `broadcast_opt_in_release` | Send one throttled batch to opted-in viewers only |
| `get_distribution_stats` | Read campaign, delivery and optional channel-member statistics |
| `configure_telegram_webhook` | Connect a deployed HTTPS endpoint to Telegram |

All Telegram writes require an explicit confirmation field. Broadcasts are capped at 250 recipients per tool call and 25 sends per second so release waves can grow gradually and remain controlled.

## One-time Telegram setup

1. Create the official public channel, preferably `@ANAADHITheEpic`.
2. Open Telegram's official `@BotFather`, create a bot such as `@ANAADHIReleaseBot`, and securely copy the token.
3. Add the bot as an administrator of the official channel. Grant only the permissions needed to post messages and create invite links.
4. Never paste the bot token into GitHub, a caption, a screenshot or a public chat.
5. Upload the complete Telegram edition of the movie directly to the official channel from the rights holder's Telegram account.
6. Open the uploaded post and copy its public link, for example `https://t.me/ANAADHITheEpic/123`.

## Local development

```bash
cp .env.example .env
npm install
npm run typecheck
npm run dev
```

Health check:

```bash
curl http://localhost:8000/health
```

MCP endpoint:

```text
http://localhost:8000/mcp
```

Telegram webhook endpoint:

```text
http://localhost:8000/telegram/webhook
```

Telegram cannot call a localhost webhook. For a private development test, expose port 8000 through a temporary HTTPS tunnel, set `PUBLIC_BASE_URL`, and call `configure_telegram_webhook` only after verifying the endpoint. Production must use a stable HTTPS domain.

## ChatGPT connection

This is a tool-only MCP app; no widget is required for version 1.

1. Run or deploy the server at a reachable HTTPS domain.
2. In ChatGPT, enable Developer Mode under **Settings → Apps & Connectors → Advanced settings**.
3. Create a private app/connector pointing to `https://your-domain.example/mcp`.
4. Refresh the app after tool descriptions or schemas change.
5. Do not expose a write-capable `/mcp` endpoint without authentication. `MCP_ACCESS_TOKEN` provides a basic bearer-token gate for compatible clients; a production public app should use a proper supported authentication flow.

## Required environment variables

See `.env.example`. The important values are:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_BOT_USERNAME`
- `TELEGRAM_CHANNEL_USERNAME`
- `TELEGRAM_WEBHOOK_SECRET`
- `PUBLIC_BASE_URL`
- `MCP_ACCESS_TOKEN`
- `DATA_FILE`

The JSON data store contains Telegram chat IDs and must live on encrypted persistent storage with restricted access. A container deployment should mount `/data` as a persistent volume.

## Docker

```bash
docker build -t anaadhi-telegram-distribution .
docker run --rm -p 8000:8000 --env-file .env -v anaadhi-telegram-data:/data anaadhi-telegram-distribution
```

## Release gate

Do not activate the broadcast tools until all of these are true:

- the uploader owns or controls all film, music, voice, image and subtitle rights for this Telegram release;
- the official channel and public username are locked;
- the Telegram movie copy has passed picture, audio and subtitle QC;
- the public whole-movie post link is registered as canonical;
- the bot has been tested with a small private opt-in group;
- `/stop` deletes subscriber data correctly;
- the webhook secret and MCP access control are active;
- Filmhub/OTT agreements permit the planned free Telegram release date.

## Version 1 boundary

This scaffold provides the distribution engine and ChatGPT tool surface. It is not live until the owner supplies the Telegram bot/channel credentials through deployment secrets, uploads the final movie post, deploys the HTTPS service, and explicitly configures the webhook.
