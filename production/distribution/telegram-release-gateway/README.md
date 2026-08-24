# ANAADHI Telegram Whole-Movie Release Gateway

**Status:** Foundation built; not deployed; no live payment or movie file attached.

## Objective

Distribute the authorized full ANAADHI movie to audiences originating on Telegram while preserving referral attribution, payment evidence, verified download accounting and settlement to the creator's merchant bank account.

## Non-negotiable technical truth

A raw movie file uploaded into a public Telegram channel can be forwarded, copied or re-uploaded without passing through a controlled payment or analytics system. It therefore cannot be the canonical revenue-bearing asset.

The official Telegram channel and bot are the discovery and sharing layer. The private release gateway is the revenue and delivery layer.

## Locked flow

1. A viewer opens a signed Telegram deep link containing a referral code.
2. The bot records the referral visit and presents the official release page.
3. An INR purchase is completed on the independent release website through an approved Indian payment gateway.
4. Only a cryptographically verified payment webhook creates a movie entitlement.
5. The gateway issues a short-lived signed download token.
6. The movie is streamed from private object storage through a range-aware delivery endpoint.
7. Overlapping and resumed HTTP byte ranges are de-duplicated.
8. A download is counted as verified only after at least 95% of unique movie bytes have been served for a paid, non-refunded entitlement.
9. The dashboard reports referral visits, paid orders, gross revenue, refunds, verified downloads and settlement reconciliation.

## Revenue modes

### Default: paid whole-movie access

Revenue is created by verified paid orders. The payment provider settles eligible funds to the creator's verified merchant bank account, subject to its fees, settlement cycle, refunds and compliance checks.

### Optional: sponsor-funded free access

The gateway can count verified free downloads, but those counts generate money only when a sponsor or advertiser has a written payment agreement tied to them. Tracking alone does not create revenue.

### Optional: Telegram-native Stars

Digital goods sold inside a Telegram bot or Mini App must follow Telegram's Stars requirements. This mode is separate from direct INR bank settlement and is disabled in this foundation.

## Attribution contract

Canonical share format:

`https://t.me/<BOT_USERNAME>?start=r_<SIGNED_REFERRAL_TOKEN>`

The bot verifies the signed token and associates the visit, order and download entitlement with the referral ID. Attribution is preserved only while users share the official tracked link or bot-generated Share button. Copying or re-uploading the movie file bypasses attribution.

## Verified download definition

A verified download requires all of the following:

- successful provider webhook signature verification upstream;
- a paid, non-refunded entitlement;
- a valid unexpired signed download token;
- a consistent canonical movie size;
- cumulative unique bytes served of at least 95%;
- one completion event per entitlement, even with retries or resume requests.

Raw link clicks, Telegram views and browser redirects are not counted as paid downloads.

## Security rules

- Never commit Telegram bot tokens, payment secrets, webhook secrets, storage keys or signing secrets.
- Keep the movie master in private object storage, never in this public repository.
- Use provider-signed webhooks, idempotency keys and constant-time signature checks.
- Hash Telegram user identifiers before analytics storage.
- Use short-lived bearer download tokens, rate limits and refund revocation.
- Test with a harmless dummy file before attaching the full movie.

## Current hard blockers

- Telegram bot username and BotFather token are not yet supplied.
- Public release domain is not yet supplied.
- Indian payment gateway and merchant KYC account are not yet selected/connected.
- Settlement bank account remains solely inside the payment provider; it must never be stored in GitHub.
- Private object-storage account and movie object key are not yet supplied.
- Final movie price is not yet locked.
- Direct-to-consumer release rights and any Filmhub/OTT window restrictions must be cleared before launch.

## Included foundation

- `tracker_core.py`: compact signed referral codes, expiring download claims, payment-entitlement ledger, range de-duplication, verified-completion accounting and refund blocking.
- `test_tracker_core.py`: standard-library unit tests covering tampering, expiry, payment idempotency, overlap/resume accounting and refund revocation.
- `RELEASE_GATEWAY_CONTRACT.yaml`: canonical architecture and launch gates.
- `.env.example`: names of required deployment secrets without any secret values.
