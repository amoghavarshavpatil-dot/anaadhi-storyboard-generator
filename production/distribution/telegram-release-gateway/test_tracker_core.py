import unittest

from tracker_core import (
    DownloadTokenCodec,
    LedgerError,
    ReferralCodec,
    ReleaseLedger,
    TokenError,
)

SECRET = b"s" * 32
SALT = b"p" * 32


class ReferralCodecTests(unittest.TestCase):
    def test_round_trip_and_length(self):
        codec = ReferralCodec(SECRET)
        token = codec.issue("creator01")
        self.assertLessEqual(len("r_" + token), 64)
        self.assertEqual(codec.verify(token), "creator01")

    def test_tampering_is_rejected(self):
        codec = ReferralCodec(SECRET)
        token = codec.issue("creator01")
        with self.assertRaises(TokenError):
            codec.verify(token[:-1] + ("A" if token[-1] != "A" else "B"))


class DownloadTokenCodecTests(unittest.TestCase):
    def test_expiry(self):
        codec = DownloadTokenCodec(SECRET)
        token = codec.issue("ent-1", ttl_seconds=60, now=100)
        self.assertEqual(codec.verify(token, now=160).entitlement_id, "ent-1")
        with self.assertRaises(TokenError):
            codec.verify(token, now=161)


class ReleaseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = ReleaseLedger(
            privacy_salt=SALT, completion_threshold=0.95
        )
        self.referral_id = self.ledger.register_referral(
            "official-channel", referral_id="creator01", now=10
        )

    def tearDown(self):
        self.ledger.close()

    def test_overlapping_ranges_are_deduplicated(self):
        self.ledger.record_visit(
            referral_id=self.referral_id,
            source="telegram-bot",
            telegram_user_id=12345,
            now=20,
        )
        entitlement = self.ledger.record_verified_payment(
            order_id="order-1",
            provider="test-provider",
            provider_payment_id="pay-1",
            amount_paise=4900,
            referral_id=self.referral_id,
            now=30,
        )
        first = self.ledger.record_download_range(
            entitlement_id=entitlement,
            start_byte=0,
            end_byte=700,
            total_bytes=1000,
            now=40,
        )
        self.assertFalse(first["verified_complete"])
        second = self.ledger.record_download_range(
            entitlement_id=entitlement,
            start_byte=600,
            end_byte=950,
            total_bytes=1000,
            now=50,
        )
        self.assertEqual(second["unique_bytes"], 950)
        self.assertTrue(second["verified_complete"])
        self.assertTrue(second["newly_completed"])
        third = self.ledger.record_download_range(
            entitlement_id=entitlement,
            start_byte=0,
            end_byte=950,
            total_bytes=1000,
            now=60,
        )
        self.assertFalse(third["newly_completed"])
        self.assertEqual(self.ledger.summary()["verified_downloads"], 1)
        self.assertEqual(self.ledger.summary()["gross_paid_paise"], 4900)

    def test_payment_webhook_is_idempotent(self):
        first = self.ledger.record_verified_payment(
            order_id="order-idempotent",
            provider="test-provider",
            provider_payment_id="pay-idempotent",
            amount_paise=7900,
            referral_id=self.referral_id,
        )
        second = self.ledger.record_verified_payment(
            order_id="order-idempotent",
            provider="test-provider",
            provider_payment_id="pay-idempotent",
            amount_paise=7900,
            referral_id=self.referral_id,
        )
        self.assertEqual(first, second)
        self.assertEqual(self.ledger.summary()["paid_orders"], 1)

    def test_refund_blocks_further_download(self):
        entitlement = self.ledger.record_verified_payment(
            order_id="order-refund",
            provider="test-provider",
            provider_payment_id="pay-refund",
            amount_paise=4900,
            referral_id=self.referral_id,
        )
        self.ledger.record_refund(provider_payment_id="pay-refund")
        with self.assertRaises(LedgerError):
            self.ledger.record_download_range(
                entitlement_id=entitlement,
                start_byte=0,
                end_byte=1,
                total_bytes=100,
            )

    def test_unknown_entitlement_is_blocked(self):
        with self.assertRaises(LedgerError):
            self.ledger.record_download_range(
                entitlement_id="missing",
                start_byte=0,
                end_byte=1,
                total_bytes=100,
            )


if __name__ == "__main__":
    unittest.main()
