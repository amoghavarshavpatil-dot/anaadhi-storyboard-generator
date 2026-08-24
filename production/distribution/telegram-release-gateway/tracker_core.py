"""Core attribution and verified-download ledger for the ANAADHI release gateway.

This module deliberately contains no Telegram, payment-gateway, or cloud-storage
credentials. Provider adapters must verify their own webhook signatures before
calling ``record_verified_payment``.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

_REFERRAL_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,24}$")


class TokenError(ValueError):
    """Raised when a signed referral or download token is invalid."""


class LedgerError(RuntimeError):
    """Raised when a ledger operation violates the release contract."""


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except Exception as exc:
        raise TokenError("Malformed base64url value") from exc


def _require_secret(secret: str | bytes) -> bytes:
    raw = secret.encode("utf-8") if isinstance(secret, str) else bytes(secret)
    if len(raw) < 32:
        raise ValueError("Signing secrets must contain at least 32 bytes")
    return raw


class ReferralCodec:
    """Issues compact signed referral tokens suitable for Telegram start params."""

    def __init__(self, secret: str | bytes) -> None:
        self._secret = _require_secret(secret)

    def issue(self, referral_id: str) -> str:
        if not _REFERRAL_ID_RE.fullmatch(referral_id):
            raise ValueError("referral_id must be 6-24 URL-safe characters")
        unsigned = f"1.{referral_id}".encode("ascii")
        signature = hmac.new(
            self._secret, b"anaadhi-referral\x00" + unsigned, hashlib.sha256
        ).digest()[:9]
        token = f"1_{referral_id}_{_b64url_encode(signature)}"
        if len(token) > 60:
            raise ValueError("Referral token exceeds the allowed compact size")
        return token

    def verify(self, token: str) -> str:
        try:
            version, referral_id, supplied_signature = token.split("_", 2)
        except ValueError as exc:
            raise TokenError("Malformed referral token") from exc
        if version != "1" or not _REFERRAL_ID_RE.fullmatch(referral_id):
            raise TokenError("Unsupported or malformed referral token")
        unsigned = f"1.{referral_id}".encode("ascii")
        expected = _b64url_encode(
            hmac.new(
                self._secret, b"anaadhi-referral\x00" + unsigned, hashlib.sha256
            ).digest()[:9]
        )
        if not hmac.compare_digest(supplied_signature, expected):
            raise TokenError("Invalid referral signature")
        return referral_id


@dataclass(frozen=True)
class DownloadClaim:
    entitlement_id: str
    expires_at: int
    nonce: str


class DownloadTokenCodec:
    """Issues short-lived signed download claims for the web gateway."""

    def __init__(self, secret: str | bytes) -> None:
        self._secret = _require_secret(secret)

    def issue(
        self, entitlement_id: str, *, ttl_seconds: int = 3600, now: int | None = None
    ) -> str:
        if ttl_seconds < 60 or ttl_seconds > 7 * 24 * 3600:
            raise ValueError("ttl_seconds must be between 60 seconds and 7 days")
        issued_at = int(time.time() if now is None else now)
        payload = {
            "e": entitlement_id,
            "x": issued_at + ttl_seconds,
            "n": secrets.token_urlsafe(8),
        }
        encoded = _b64url_encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        signature = _b64url_encode(
            hmac.new(
                self._secret,
                b"anaadhi-download\x00" + encoded.encode("ascii"),
                hashlib.sha256,
            ).digest()[:16]
        )
        return f"{encoded}.{signature}"

    def verify(self, token: str, *, now: int | None = None) -> DownloadClaim:
        try:
            encoded, supplied_signature = token.split(".", 1)
        except ValueError as exc:
            raise TokenError("Malformed download token") from exc
        expected = _b64url_encode(
            hmac.new(
                self._secret,
                b"anaadhi-download\x00" + encoded.encode("ascii"),
                hashlib.sha256,
            ).digest()[:16]
        )
        if not hmac.compare_digest(supplied_signature, expected):
            raise TokenError("Invalid download signature")
        try:
            payload = json.loads(_b64url_decode(encoded))
            claim = DownloadClaim(
                entitlement_id=str(payload["e"]),
                expires_at=int(payload["x"]),
                nonce=str(payload["n"]),
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise TokenError("Malformed download claim") from exc
        current = int(time.time() if now is None else now)
        if current > claim.expires_at:
            raise TokenError("Download token has expired")
        return claim


class ReleaseLedger:
    """SQLite event ledger for referrals, verified payments and byte ranges.

    Download ranges use half-open byte intervals: ``[start_byte, end_byte)``.
    A verified completion is emitted once cumulative unique bytes reach the
    configured threshold. Overlapping and resumed ranges are de-duplicated.
    """

    def __init__(
        self,
        database: str | Path = ":memory:",
        *,
        privacy_salt: str | bytes,
        completion_threshold: float = 0.95,
    ) -> None:
        if not 0.5 <= completion_threshold <= 1.0:
            raise ValueError("completion_threshold must be between 0.5 and 1.0")
        self._privacy_salt = _require_secret(privacy_salt)
        self._completion_threshold = float(completion_threshold)
        self._db = sqlite3.connect(str(database))
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS referrals (
                referral_id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
            );

            CREATE TABLE IF NOT EXISTS visits (
                visit_id TEXT PRIMARY KEY,
                referral_id TEXT REFERENCES referrals(referral_id),
                telegram_user_hash TEXT,
                source TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entitlements (
                entitlement_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL UNIQUE,
                referral_id TEXT REFERENCES referrals(referral_id),
                provider TEXT NOT NULL,
                provider_payment_id TEXT UNIQUE,
                amount_paise INTEGER NOT NULL CHECK (amount_paise >= 0),
                currency TEXT NOT NULL,
                payment_status TEXT NOT NULL,
                paid_at INTEGER,
                refunded_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS download_state (
                entitlement_id TEXT PRIMARY KEY
                    REFERENCES entitlements(entitlement_id) ON DELETE CASCADE,
                total_bytes INTEGER NOT NULL CHECK (total_bytes > 0),
                unique_bytes INTEGER NOT NULL DEFAULT 0 CHECK (unique_bytes >= 0),
                started_at INTEGER,
                last_seen_at INTEGER,
                completed_at INTEGER
            );

            CREATE TABLE IF NOT EXISTS download_ranges (
                entitlement_id TEXT NOT NULL
                    REFERENCES entitlements(entitlement_id) ON DELETE CASCADE,
                start_byte INTEGER NOT NULL CHECK (start_byte >= 0),
                end_byte INTEGER NOT NULL CHECK (end_byte > start_byte),
                created_at INTEGER NOT NULL,
                UNIQUE (entitlement_id, start_byte, end_byte)
            );

            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                referral_id TEXT,
                entitlement_id TEXT,
                payload_json TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            """
        )
        self._db.commit()

    @staticmethod
    def _now(now: int | None) -> int:
        return int(time.time() if now is None else now)

    def _hash_telegram_user(self, telegram_user_id: int | str) -> str:
        digest = hmac.new(
            self._privacy_salt,
            f"telegram-user:{telegram_user_id}".encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return digest[:16].hex()

    def _event(
        self,
        event_type: str,
        *,
        referral_id: str | None = None,
        entitlement_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        now: int | None = None,
    ) -> str:
        event_id = secrets.token_urlsafe(12)
        self._db.execute(
            """
            INSERT INTO events (
                event_id, event_type, referral_id, entitlement_id,
                payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                referral_id,
                entitlement_id,
                json.dumps(payload or {}, separators=(",", ":"), sort_keys=True),
                self._now(now),
            ),
        )
        return event_id

    def register_referral(
        self, label: str, *, referral_id: str | None = None, now: int | None = None
    ) -> str:
        resolved = referral_id or secrets.token_urlsafe(8)
        if not _REFERRAL_ID_RE.fullmatch(resolved):
            raise ValueError("referral_id must be 6-24 URL-safe characters")
        created_at = self._now(now)
        with self._db:
            self._db.execute(
                """
                INSERT INTO referrals (referral_id, label, created_at, active)
                VALUES (?, ?, ?, 1)
                """,
                (resolved, label.strip() or "unnamed", created_at),
            )
            self._event(
                "referral.created",
                referral_id=resolved,
                payload={"label": label.strip() or "unnamed"},
                now=created_at,
            )
        return resolved

    def record_visit(
        self,
        *,
        referral_id: str | None,
        source: str,
        telegram_user_id: int | str | None = None,
        metadata: Mapping[str, Any] | None = None,
        now: int | None = None,
    ) -> str:
        if referral_id is not None:
            row = self._db.execute(
                "SELECT active FROM referrals WHERE referral_id = ?", (referral_id,)
            ).fetchone()
            if row is None or not bool(row["active"]):
                raise LedgerError("Unknown or inactive referral")
        visit_id = secrets.token_urlsafe(12)
        created_at = self._now(now)
        user_hash = (
            self._hash_telegram_user(telegram_user_id)
            if telegram_user_id is not None
            else None
        )
        metadata_json = json.dumps(
            metadata or {}, separators=(",", ":"), sort_keys=True
        )
        with self._db:
            self._db.execute(
                """
                INSERT INTO visits (
                    visit_id, referral_id, telegram_user_hash, source,
                    metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    visit_id,
                    referral_id,
                    user_hash,
                    source,
                    metadata_json,
                    created_at,
                ),
            )
            self._event(
                "referral.visit",
                referral_id=referral_id,
                payload={"visit_id": visit_id, "source": source},
                now=created_at,
            )
        return visit_id

    def record_verified_payment(
        self,
        *,
        order_id: str,
        provider: str,
        provider_payment_id: str,
        amount_paise: int,
        referral_id: str | None = None,
        currency: str = "INR",
        entitlement_id: str | None = None,
        now: int | None = None,
    ) -> str:
        """Create an entitlement only after a provider webhook is verified upstream.

        Calling this method repeatedly with the same ``order_id`` is idempotent.
        It must never be called from an unverified browser redirect.
        """
        if amount_paise < 0:
            raise ValueError("amount_paise cannot be negative")
        if referral_id is not None:
            exists = self._db.execute(
                "SELECT 1 FROM referrals WHERE referral_id = ? AND active = 1",
                (referral_id,),
            ).fetchone()
            if exists is None:
                raise LedgerError("Unknown or inactive referral")

        existing = self._db.execute(
            """
            SELECT entitlement_id, provider, provider_payment_id, amount_paise,
                   currency, referral_id
            FROM entitlements WHERE order_id = ?
            """,
            (order_id,),
        ).fetchone()
        if existing is not None:
            expected = (
                provider,
                provider_payment_id,
                amount_paise,
                currency,
                referral_id,
            )
            actual = (
                existing["provider"],
                existing["provider_payment_id"],
                existing["amount_paise"],
                existing["currency"],
                existing["referral_id"],
            )
            if actual != expected:
                raise LedgerError("Idempotency conflict for existing order_id")
            return str(existing["entitlement_id"])

        resolved_entitlement = entitlement_id or secrets.token_urlsafe(16)
        paid_at = self._now(now)
        with self._db:
            self._db.execute(
                """
                INSERT INTO entitlements (
                    entitlement_id, order_id, referral_id, provider,
                    provider_payment_id, amount_paise, currency,
                    payment_status, paid_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'PAID', ?)
                """,
                (
                    resolved_entitlement,
                    order_id,
                    referral_id,
                    provider,
                    provider_payment_id,
                    amount_paise,
                    currency,
                    paid_at,
                ),
            )
            self._event(
                "payment.verified",
                referral_id=referral_id,
                entitlement_id=resolved_entitlement,
                payload={
                    "order_id": order_id,
                    "provider": provider,
                    "amount_paise": amount_paise,
                    "currency": currency,
                },
                now=paid_at,
            )
        return resolved_entitlement

    def record_refund(
        self, *, provider_payment_id: str, now: int | None = None
    ) -> str:
        row = self._db.execute(
            """
            SELECT entitlement_id, referral_id, payment_status
            FROM entitlements WHERE provider_payment_id = ?
            """,
            (provider_payment_id,),
        ).fetchone()
        if row is None:
            raise LedgerError("Unknown provider payment")
        if row["payment_status"] == "REFUNDED":
            return str(row["entitlement_id"])
        refunded_at = self._now(now)
        with self._db:
            self._db.execute(
                """
                UPDATE entitlements
                SET payment_status = 'REFUNDED', refunded_at = ?
                WHERE entitlement_id = ?
                """,
                (refunded_at, row["entitlement_id"]),
            )
            self._event(
                "payment.refunded",
                referral_id=row["referral_id"],
                entitlement_id=row["entitlement_id"],
                payload={"provider_payment_id": provider_payment_id},
                now=refunded_at,
            )
        return str(row["entitlement_id"])

    @staticmethod
    def _merge_unique_bytes(ranges: list[tuple[int, int]]) -> int:
        if not ranges:
            return 0
        ranges.sort(key=lambda item: (item[0], item[1]))
        merged_start, merged_end = ranges[0]
        unique = 0
        for start, end in ranges[1:]:
            if start <= merged_end:
                merged_end = max(merged_end, end)
            else:
                unique += merged_end - merged_start
                merged_start, merged_end = start, end
        return unique + (merged_end - merged_start)

    def record_download_range(
        self,
        *,
        entitlement_id: str,
        start_byte: int,
        end_byte: int,
        total_bytes: int,
        now: int | None = None,
    ) -> dict[str, Any]:
        if not (0 <= start_byte < end_byte <= total_bytes):
            raise ValueError("Invalid half-open byte range")
        entitlement = self._db.execute(
            """
            SELECT referral_id, payment_status
            FROM entitlements WHERE entitlement_id = ?
            """,
            (entitlement_id,),
        ).fetchone()
        if entitlement is None:
            raise LedgerError("Unknown entitlement")
        if entitlement["payment_status"] != "PAID":
            raise LedgerError("Only paid, non-refunded entitlements may download")

        observed_at = self._now(now)
        with self._db:
            state = self._db.execute(
                "SELECT * FROM download_state WHERE entitlement_id = ?",
                (entitlement_id,),
            ).fetchone()
            if state is None:
                self._db.execute(
                    """
                    INSERT INTO download_state (
                        entitlement_id, total_bytes, unique_bytes,
                        started_at, last_seen_at
                    ) VALUES (?, ?, 0, ?, ?)
                    """,
                    (entitlement_id, total_bytes, observed_at, observed_at),
                )
                self._event(
                    "download.started",
                    referral_id=entitlement["referral_id"],
                    entitlement_id=entitlement_id,
                    payload={"total_bytes": total_bytes},
                    now=observed_at,
                )
            elif int(state["total_bytes"]) != total_bytes:
                raise LedgerError("total_bytes changed for an existing entitlement")

            self._db.execute(
                """
                INSERT OR IGNORE INTO download_ranges (
                    entitlement_id, start_byte, end_byte, created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (entitlement_id, start_byte, end_byte, observed_at),
            )
            rows = self._db.execute(
                """
                SELECT start_byte, end_byte FROM download_ranges
                WHERE entitlement_id = ? ORDER BY start_byte, end_byte
                """,
                (entitlement_id,),
            ).fetchall()
            unique_bytes = self._merge_unique_bytes(
                [(int(row["start_byte"]), int(row["end_byte"])) for row in rows]
            )
            current_state = self._db.execute(
                "SELECT completed_at FROM download_state WHERE entitlement_id = ?",
                (entitlement_id,),
            ).fetchone()
            completed_at = current_state["completed_at"]
            completion_ratio = unique_bytes / total_bytes
            newly_completed = (
                completed_at is None
                and completion_ratio >= self._completion_threshold
            )
            if newly_completed:
                completed_at = observed_at
                self._event(
                    "download.verified_complete",
                    referral_id=entitlement["referral_id"],
                    entitlement_id=entitlement_id,
                    payload={
                        "unique_bytes": unique_bytes,
                        "total_bytes": total_bytes,
                        "completion_ratio": completion_ratio,
                    },
                    now=observed_at,
                )
            self._db.execute(
                """
                UPDATE download_state
                SET unique_bytes = ?, last_seen_at = ?, completed_at = ?
                WHERE entitlement_id = ?
                """,
                (unique_bytes, observed_at, completed_at, entitlement_id),
            )

        return {
            "entitlement_id": entitlement_id,
            "unique_bytes": unique_bytes,
            "total_bytes": total_bytes,
            "completion_ratio": completion_ratio,
            "verified_complete": completed_at is not None,
            "newly_completed": newly_completed,
        }

    def summary(self) -> dict[str, int]:
        row = self._db.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM referrals WHERE active = 1) AS referrals,
                (SELECT COUNT(*) FROM visits) AS visits,
                (SELECT COUNT(*) FROM entitlements WHERE payment_status = 'PAID')
                    AS paid_orders,
                (SELECT COALESCE(SUM(amount_paise), 0) FROM entitlements
                    WHERE payment_status = 'PAID') AS gross_paid_paise,
                (SELECT COUNT(*) FROM entitlements WHERE payment_status = 'REFUNDED')
                    AS refunds,
                (SELECT COUNT(*) FROM download_state WHERE completed_at IS NOT NULL)
                    AS verified_downloads
            """
        ).fetchone()
        return {key: int(row[key]) for key in row.keys()}

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> "ReleaseLedger":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()
