#!/usr/bin/env python3
"""Execute the GitHub-only portion of HEYGEN-AQ-001..006 precheck.

Safety:
- verifies existing files only
- creates/updates control manifests only
- creates no media
- calls no HeyGen endpoint
- submits no render/job
- never writes APPROVED status

Authoritative external HeyGen consent and Drive metadata observations are recorded
separately by the connected-app precheck result; this script only records GitHub facts.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
B01 = ROOT / "production/heygen/avatars/B01/B01_AVATAR_MANIFEST.yaml"
INDEX = ROOT / "production/heygen/avatars/AVATAR_BATCH_INDEX.yaml"
P0 = ROOT / "production/batches/ANAADHI_BATCH_FOUNDATION.py"
GITHUB_EVIDENCE = ROOT / "production/heygen/P0_NO_NEW_MEDIA_GITHUB_PRECHECK.yaml"
TARGETS = ("B24", "B25", "B26")
HASH_TARGETS = tuple(f"B01-AV-{n:02d}" for n in range(3, 10))


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_p0_batches() -> dict[str, dict[str, Any]]:
    tree = ast.parse(P0.read_text(encoding="utf-8"), filename=str(P0))
    batches: dict[str, dict[str, Any]] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "BATCHES" for t in node.targets):
            continue
        if not isinstance(node.value, ast.List):
            continue
        for call in node.value.elts:
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "batch":
                continue
            values = [ast.literal_eval(arg) for arg in call.args]
            if len(values) != 8:
                raise ValueError("Unexpected P0 batch() arity")
            bid, title, scenes, epoch, locations, state, characters, props = values
            batches[str(bid)] = {
                "id": bid, "title": title, "scenes": scenes, "epoch": epoch,
                "locations": locations, "character_state": state,
                "characters": characters, "props": props,
            }
        break
    return batches


def slots(text: str) -> list[str]:
    return [x.strip() for x in str(text).split(";") if x.strip()]


def slot_ref(slot: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "-", slot.upper()).strip("-")
    return f"CHR-{token}"


def main() -> int:
    b01 = load_yaml(B01)
    index = load_yaml(INDEX)
    p0 = extract_p0_batches()
    b01_assets = b01.get("assets") or {}
    if not isinstance(b01_assets, dict):
        raise ValueError("B01 assets must be a mapping")

    hash_checks: dict[str, Any] = {}
    for aid in HASH_TARGETS:
        asset = b01_assets.get(aid)
        if not isinstance(asset, dict):
            raise ValueError(f"Missing {aid}")
        rel = asset.get("path")
        expected = asset.get("sha256")
        if not rel or not expected:
            raise ValueError(f"{aid} missing path/sha256")
        path = ROOT / rel
        if not path.is_file():
            raise ValueError(f"{aid} source missing: {rel}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"{aid} SHA-256 mismatch: expected {expected}, got {actual}")
        hash_checks[aid] = {
            "path": rel,
            "expected_sha256": expected,
            "actual_sha256": actual,
            "sha256_match": True,
            "drive_file_id": asset.get("drive_file_id"),
            "drive_status_recorded": asset.get("drive_status"),
        }

    batch_order = index.get("batch_order") or {}
    created_manifests: dict[str, Any] = {}

    for bid in TARGETS:
        record = batch_order.get(bid)
        if not isinstance(record, dict):
            raise ValueError(f"Avatar index missing {bid}")
        original_status = str(record.get("status", ""))
        if "REUSE_B01_CAPTURE_IDENTITIES" not in original_status:
            raise ValueError(f"{bid} is not explicitly designated for B01 identity reuse: {original_status}")
        p0_record = p0.get(bid)
        if not p0_record:
            raise ValueError(f"P0 missing {bid}")
        p0_slots = slots(p0_record["characters"])

        reusable_by_ref: dict[str, tuple[str, dict[str, Any]]] = {}
        for source_id, source in b01_assets.items():
            if not isinstance(source, dict):
                continue
            reuse_batches = source.get("reuse_batches") or []
            ref = source.get("character_ref")
            if bid in reuse_batches and isinstance(ref, str):
                reusable_by_ref.setdefault(ref, (source_id, source))

        assets: dict[str, Any] = {}
        bound = []
        unresolved = []
        for n, slot in enumerate(p0_slots, start=1):
            aid = f"{bid}-AV-{n:02d}"
            ref = slot_ref(slot)
            entry: dict[str, Any] = {
                "character_slot": slot,
                "character_ref": ref,
                "binding_mode": "P0_SLOT_REUSE_PRECHECK",
                "approved_status": None,
                "consent_status_observed": None,
            }
            reusable = reusable_by_ref.get(ref)
            if reusable:
                source_id, source = reusable
                entry.update({
                    "reuse_source_asset": source_id,
                    "reuse_source_manifest": "production/heygen/avatars/B01/B01_AVATAR_MANIFEST.yaml",
                    "source_visual_path": source.get("path"),
                    "source_sha256": source.get("sha256"),
                    "drive_status": source.get("drive_status"),
                    "drive_file_id": source.get("drive_file_id"),
                    "heygen_group_id": source.get("heygen_group_id"),
                    "heygen_look_id": source.get("heygen_look_id"),
                    "heygen_status": source.get("heygen_status", "UNRESOLVED_REUSE_SOURCE_STATUS"),
                    "reuse_evidence": f"B01 {source_id}.reuse_batches explicitly contains {bid}",
                })
                bound.append({"slot": slot, "asset": aid, "source": source_id})
            else:
                entry.update({
                    "reuse_source_asset": None,
                    "heygen_status": "UNRESOLVED_NO_B01_REUSE_BINDING_VERIFIED",
                    "resolution_note": "No B01 reuse binding is evidenced for this P0 character slot. Keep unresolved; do not generate here.",
                })
                unresolved.append({"slot": slot, "asset": aid})
            assets[aid] = entry

        manifest = {
            "version": 1,
            "phase": "P1_CHARACTER_AVATAR_CONTROL",
            "batch_id": bid,
            "batch_title": p0_record["title"],
            "scenes": p0_record["scenes"],
            "status": "PARTIAL_REUSE_B01_CAPTURE_IDENTITIES__UNRESOLVED_SLOTS_REMAIN",
            "control_mode": "P0_NO_NEW_MEDIA_PRECHECK__BINDINGS_ONLY",
            "creation_authority": "WORK_PAGE_ONLY_FOR_ANY_FUTURE_UNCOVERED_SLOT",
            "media_generated_by_this_manifest_update": False,
            "heygen_submission_by_this_manifest_update": False,
            "approved_status_changed_by_this_manifest_update": False,
            "consent_status_observed": None,
            "source_index_status_before_binding": original_status,
            "p0_character_slots": p0_slots,
            "assets": assets,
            "reuse_summary": {
                "p0_slot_count": len(p0_slots),
                "b01_reuse_bound_count": len(bound),
                "unresolved_slot_count": len(unresolved),
                "bound": bound,
                "unresolved": unresolved,
            },
        }
        rel_manifest = f"production/heygen/avatars/{bid}/{bid}_AVATAR_MANIFEST.yaml"
        out = ROOT / rel_manifest
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8")

        record["manifest"] = rel_manifest
        record["status"] = "PARTIAL_REUSE_B01_CAPTURE_IDENTITIES__UNRESOLVED_SLOTS_REMAIN"
        created_manifests[bid] = {
            "manifest": rel_manifest,
            "original_index_status": original_status,
            "p0_slot_count": len(p0_slots),
            "b01_reuse_bound_count": len(bound),
            "unresolved_slot_count": len(unresolved),
            "bound": bound,
            "unresolved": unresolved,
        }

    INDEX.write_text(yaml.safe_dump(index, sort_keys=False, allow_unicode=True, width=180), encoding="utf-8")

    evidence = {
        "version": 1,
        "project": "ANAADHI",
        "control": "P0-NO-NEW-MEDIA-GITHUB-PRECHECK",
        "scope": ["HEYGEN-AQ-003", "HEYGEN-AQ-004", "HEYGEN-AQ-005", "HEYGEN-AQ-006"],
        "safety": {
            "media_generated": False,
            "media_replaced": False,
            "heygen_called": False,
            "heygen_submission": False,
            "approved_status_changed": False,
        },
        "b01_source_integrity": hash_checks,
        "reuse_manifest_bindings": created_manifests,
        "notes": [
            "B24-B26 manifests bind only reuse facts explicitly evidenced by B01 reuse_batches.",
            "Every P0 character slot without an evidenced B01 reuse mapping remains explicitly unresolved.",
            "Manifest assignment resolves only AVATAR_MANIFEST_UNASSIGNED; it does not imply that avatar looks or consent are complete.",
        ],
    }
    GITHUB_EVIDENCE.write_text(yaml.safe_dump(evidence, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8")
    print(yaml.safe_dump({
        "hash_checks_passed": len(hash_checks),
        "manifests_written": list(created_manifests),
        "reuse_counts": {b: created_manifests[b]["b01_reuse_bound_count"] for b in TARGETS},
        "unresolved_counts": {b: created_manifests[b]["unresolved_slot_count"] for b in TARGETS},
    }, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
