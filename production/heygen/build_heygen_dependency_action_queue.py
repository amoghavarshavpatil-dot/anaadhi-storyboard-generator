#!/usr/bin/env python3
"""Build an owner-separated action queue from HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml.

PLANNING ONLY:
- does not generate or replace media
- does not call or submit to HeyGen
- does not change APPROVED status
- does not mutate registries, bindings, avatar manifests, or consent records

The output contains exactly one action packet per canonical dependency. Packets may
contain conditional handoffs between owners, but no packet is auto-closed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "production/heygen/HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml"
DEFAULT_OUT = ROOT / "production/heygen/HEYGEN_BATCH_DEPENDENCY_ACTION_QUEUE.yaml"

OWNER_LANES = [
    "GITHUB-ONLY",
    "DRIVE-VERIFY",
    "WORK-PAGE-AVATAR-COMPLETION",
    "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING",
    "CONSENT-VERIFY",
]


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def batch_num(batch: str) -> int:
    m = re.fullmatch(r"B(\d{2})", str(batch))
    return int(m.group(1)) if m else 999


def get_dependencies(plan: dict[str, Any]) -> list[dict[str, Any]]:
    deps = plan.get("safe_dependency_resolution_order")
    if not isinstance(deps, list):
        raise ValueError("safe_dependency_resolution_order is missing or not a list")
    out = [d for d in deps if isinstance(d, dict) and d.get("dependency_id")]
    expected = int(plan.get("deduplication_summary", {}).get("canonical_dependencies", len(out)))
    if len(out) != expected:
        raise ValueError(f"Dependency count mismatch: plan says {expected}, found {len(out)}")
    ids = [str(d["dependency_id"]) for d in out]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate dependency_id values found in source plan")
    return out


def primary_owner(dep: dict[str, Any]) -> str:
    lane = str(dep.get("resolution_lane", ""))
    mapping = {
        "CONSENT_STATE_UPDATE": "CONSENT-VERIFY",
        "DRIVE_EXACT_REUSE_CHECK_THEN_WORK_PAGE_MEDIA_IF_ABSENT": "DRIVE-VERIFY",
        "SPATIAL_BINDING_FIRST_THEN_EXISTING_ASSET_CHECK": "GITHUB-ONLY",
        "WORK_PAGE_AVATAR_LOOK_COMPLETION_FROM_EXISTING_GITHUB_DRIVE_SOURCE": "WORK-PAGE-AVATAR-COMPLETION",
        "WORK_PAGE_AVATAR_MANIFEST_BINDING_TO_EXISTING_B01_IDENTITIES": "GITHUB-ONLY",
        "WORK_PAGE_AVATAR_PARTIAL_REUSE_THEN_GAP_REVIEW": "WORK-PAGE-AVATAR-COMPLETION",
        "WORK_PAGE_AVATAR_REUSE_OR_SOURCE_GAP_REVIEW": "WORK-PAGE-AVATAR-COMPLETION",
        "GITHUB_CONTROL_OR_SCHEMA_CORRECTION": "GITHUB-ONLY",
        "EXISTING_GITHUB_ASSET_REVIEW_THEN_REGISTRY_OR_BINDING_CORRECTION": "GITHUB-ONLY",
        "REGISTRY_OR_BINDING_REVIEW": "GITHUB-ONLY",
        "FAIL_CLOSED_REVIEW_REQUIRED": "GITHUB-ONLY",
    }
    owner = mapping.get(lane)
    if owner is None:
        raise ValueError(f"Unsupported resolution lane: {lane}")
    return owner


def conditional_handoffs(dep: dict[str, Any], owner: str) -> list[dict[str, Any]]:
    lane = str(dep.get("resolution_lane", ""))
    need = dep.get("new_work_page_media_required")
    handoffs: list[dict[str, Any]] = []

    if lane == "DRIVE_EXACT_REUSE_CHECK_THEN_WORK_PAGE_MEDIA_IF_ABSENT":
        handoffs.extend([
            {
                "condition": "EXACT_APPROVED_CANONICAL_DRIVE_ASSET_FOUND",
                "to_owner_lane": "GITHUB-ONLY",
                "action": "Bind the exact verified asset to the canonical reference/registry entry without changing APPROVED status; then rerun the validator.",
            },
            {
                "condition": "NO_EXACT_APPROVED_CANONICAL_DRIVE_ASSET_FOUND_AND_SEARCH_EVIDENCE_COMPLETE",
                "to_owner_lane": "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING",
                "action": "Create only the proven-missing canonical asset on the Work page; never substitute a similar asset merely for variety.",
            },
        ])
    elif lane == "SPATIAL_BINDING_FIRST_THEN_EXISTING_ASSET_CHECK":
        handoffs.extend([
            {
                "condition": "BINDING_CANNOT_BE_CLOSED_FROM_EXISTING_APPROVED_GITHUB_PLATES",
                "to_owner_lane": "DRIVE-VERIFY",
                "action": "Search Drive for the exact canonical root/nested-space/state asset and real approval evidence.",
            },
            {
                "condition": "GITHUB_AND_DRIVE_EXACT_REUSE_CHECKS_PROVE_CANONICAL_VISUAL_GAP",
                "to_owner_lane": "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING",
                "action": "Create only the missing canonical spatial/state asset on the Work page.",
            },
        ])
    elif lane in {"WORK_PAGE_AVATAR_PARTIAL_REUSE_THEN_GAP_REVIEW", "WORK_PAGE_AVATAR_REUSE_OR_SOURCE_GAP_REVIEW"}:
        if need not in (False, "False", None):
            handoffs.append({
                "condition": "EXISTING_IDENTITY_LOOK_SOURCE_AND_REUSE_CHAIN_EXHAUSTED_AND_AVATAR_SLOT_STILL_UNCOVERED",
                "to_owner_lane": "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING",
                "action": "Create a new avatar source visual only for the uncovered canonical slot on the Work page.",
            })
    elif lane == "CONSENT_STATE_UPDATE":
        handoffs.append({
            "condition": "AFFIRMATIVE_CONSENT_STATE_OBSERVED_FROM_REAL_SOURCE",
            "to_owner_lane": "GITHUB-ONLY",
            "action": "Record only the observed consent evidence in the appropriate control/manifest field; do not infer or fabricate consent.",
        })

    return handoffs


def exact_action(dep: dict[str, Any], owner: str) -> str:
    dep_id = str(dep["dependency_id"])
    source_action = str(dep.get("safe_first_action", "Review the dependency evidence and preserve the hard block."))
    prefix = {
        "GITHUB-ONLY": "Resolve control, binding, registry, manifest, or canonical-reference evidence in GitHub only.",
        "DRIVE-VERIFY": "Verify whether an exact already-approved canonical asset exists in Drive before any creation request.",
        "WORK-PAGE-AVATAR-COMPLETION": "Complete/reuse the canonical avatar identity or look on the Work page using existing sources first.",
        "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING": "Create media on the Work page only after exact GitHub/Drive/reuse evidence proves the canonical asset is missing.",
        "CONSENT-VERIFY": "Verify the real consent state from an authoritative source; never infer consent.",
    }[owner]
    return f"{prefix} Dependency: {dep_id}. Source-plan action: {source_action}"


def closure_evidence(dep: dict[str, Any], owner: str) -> dict[str, Any]:
    common = [
        "dependency_id matches the canonical dependency in HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml",
        "evidence identifies every impacted batch and preserves the same canonical reference/identity/state",
        "a fresh HEYGEN-BATCH-MEDIA-VALIDATOR report no longer emits this dependency/blocker for all impacted batches",
        "git diff / recorded change evidence shows no APPROVED status was fabricated or changed by this queue step",
    ]
    lane_specific: dict[str, list[str]] = {
        "CONSENT-VERIFY": [
            "authoritative consent source and observed state",
            "observation timestamp/date and subject/group/identity identifier",
            "manifest/contract field location where the observed state is recorded",
        ],
        "GITHUB-ONLY": [
            "exact source file/path/blob SHA or canonical binding record used to resolve the dependency",
            "before/after binding or registry/manifest diff limited to factual metadata/control correction",
            "no new media file was introduced as part of the GitHub-only closure",
        ],
        "DRIVE-VERIFY": [
            "Drive search query terms and search scope",
            "if found: exact Drive file id, title, MIME/type, and canonical-match evidence",
            "if found: independent approval evidence; file presence alone is not approval",
            "if not found: explicit no-exact-match result sufficient to justify conditional Work-page handoff",
        ],
        "WORK-PAGE-AVATAR-COMPLETION": [
            "canonical character/variant/state refs for the avatar slot",
            "existing GitHub source path and checksum or documented reusable identity/look id when available",
            "Drive file id/status when source archive is already documented",
            "returned HeyGen group/look identity metadata only after Work-page completion; no replacement visual unless gap proof exists",
        ],
        "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING": [
            "GitHub exact-reuse check evidence",
            "Drive exact-approved-asset check evidence",
            "reuse/alias/binding check evidence showing no canonical substitute exists",
            "canonical creation brief tied to the exact dependency and impacted scenes/batches",
            "new asset approval must occur separately; creation itself never implies APPROVED",
        ],
    }
    return {
        "required": common + lane_specific[owner],
        "not_accepted_as_closure": [
            "fuzzy filename similarity without canonical identity evidence",
            "folder presence without exact asset evidence",
            "media generation or upload alone",
            "manual status flip to APPROVED",
            "HeyGen submission success without validator clearance",
        ],
        "closure_rule": "ALL required evidence must be present and the dependency must disappear from a fresh validator report; otherwise packet remains OPEN_UNRESOLVED.",
    }


def priority_key(dep: dict[str, Any], no_new_media: set[str]) -> tuple[Any, ...]:
    dep_id = str(dep["dependency_id"])
    impact = int(dep.get("batch_impact", len(dep.get("batches") or [])))
    scope = str(dep.get("scope", "BATCH_SPECIFIC"))
    source_step = int(dep.get("step", 9999))
    batches = [str(x) for x in (dep.get("batches") or [])]
    earliest = min((batch_num(b) for b in batches), default=999)

    if dep_id in no_new_media:
        tier = 0
    elif scope == "SHARED" or impact > 1:
        tier = 1
    else:
        tier = 2
    return (tier, -impact if tier < 2 else 0, earliest, source_step, dep_id)


def build_queue() -> dict[str, Any]:
    plan = load_yaml(PLAN)
    deps = get_dependencies(plan)
    no_new_media = set(str(x) for x in plan.get("hard_separation", {}).get("no_new_media_required", []) or [])
    if len(no_new_media) != 6:
        raise ValueError(f"Expected 6 proven no-new-media dependencies, found {len(no_new_media)}")

    deps = sorted(deps, key=lambda d: priority_key(d, no_new_media))
    packets: list[dict[str, Any]] = []
    owner_queues: dict[str, list[str]] = defaultdict(list)
    lane_counts: Counter[str] = Counter()
    priority_counts: Counter[str] = Counter()

    for idx, dep in enumerate(deps, start=1):
        dep_id = str(dep["dependency_id"])
        owner = primary_owner(dep)
        batches = sorted([str(x) for x in dep.get("batches", [])], key=batch_num)
        impact = int(dep.get("batch_impact", len(batches)))
        if dep_id in no_new_media:
            priority_class = "P0_PROVEN_NO_NEW_MEDIA"
        elif str(dep.get("scope")) == "SHARED" or impact > 1:
            priority_class = "P1_SHARED_HIGH_IMPACT"
        else:
            priority_class = "P2_BATCH_SPECIFIC"

        packet_id = f"HEYGEN-AQ-{idx:03d}"
        packet = {
            "packet_id": packet_id,
            "queue_position": idx,
            "dependency_id": dep_id,
            "priority_class": priority_class,
            "source_dependency_step": dep.get("step"),
            "source_resolution_lane": dep.get("resolution_lane"),
            "owner_lane": owner,
            "conditional_handoffs": conditional_handoffs(dep, owner),
            "scope": dep.get("scope"),
            "batch_impact": impact,
            "impacted_batches": batches,
            "continuity_guard": {
                "dependency_resolution_may_precede_batch_execution": True,
                "batch_media_execution_order_remains": "B01_THROUGH_B34",
                "do_not_regenerate_for_variety": True,
                "preserve_existing_identity_location_prop_state_reuse": True,
                "earliest_impacted_batch": batches[0] if batches else None,
                "latest_impacted_batch": batches[-1] if batches else None,
            },
            "current_new_media_requirement": dep.get("new_work_page_media_required"),
            "proven_no_new_media": dep_id in no_new_media,
            "exact_action": exact_action(dep, owner),
            "source_evidence": dep.get("evidence") or {},
            "closure_evidence": closure_evidence(dep, owner),
            "status": "OPEN_UNRESOLVED",
            "automatic_closure_allowed": False,
            "approved_status_change_allowed": False,
            "heygen_submission_allowed_by_this_packet": False,
            "media_generation_allowed_by_queue_builder": False,
        }
        packets.append(packet)
        owner_queues[owner].append(packet_id)
        lane_counts[owner] += 1
        priority_counts[priority_class] += 1

    packet_ids = [p["packet_id"] for p in packets]
    dep_ids = [p["dependency_id"] for p in packets]
    if len(packets) != 161:
        raise ValueError(f"Expected 161 packets, built {len(packets)}")
    if len(packet_ids) != len(set(packet_ids)) or len(dep_ids) != len(set(dep_ids)):
        raise ValueError("Packet or dependency IDs are not unique")
    if any(p["owner_lane"] not in OWNER_LANES for p in packets):
        raise ValueError("Unknown owner lane present")
    if any(p["proven_no_new_media"] is False for p in packets[:6]):
        raise ValueError("First six packets are not all proven no-new-media dependencies")

    return {
        "version": 1,
        "project": "ANAADHI",
        "control": "HEYGEN-BATCH-DEPENDENCY-ACTION-QUEUE",
        "mode": "PLANNING_ONLY__ZERO_MEDIA_GENERATION__ZERO_HEYGEN_SUBMISSION",
        "source_plan": "production/heygen/HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml",
        "source_plan_sha256": sha256(PLAN),
        "scope": "161_CANONICAL_DEPENDENCIES__B01-B34__SC001-SC100",
        "invariants": {
            "packet_count_must_equal_canonical_dependency_count": True,
            "one_packet_per_dependency": True,
            "fabricate_or_change_approved_status": False,
            "generate_or_replace_media_in_queue_build": False,
            "heygen_submission_or_execution": False,
            "existing_assets_and_reuse_first": True,
            "batch_media_execution_order": "B01_THROUGH_B34",
            "shared_dependency_resolution_can_be_prioritized_before_later_batch_execution": True,
        },
        "summary": {
            "action_packets": len(packets),
            "proven_no_new_media_packets": len(no_new_media),
            "owner_lane_counts": dict(sorted(lane_counts.items())),
            "priority_class_counts": dict(sorted(priority_counts.items())),
            "first_six_packet_ids": packet_ids[:6],
            "first_six_dependency_ids": dep_ids[:6],
        },
        "owner_queues": {lane: owner_queues.get(lane, []) for lane in OWNER_LANES},
        "priority_policy": [
            "P0: the six source-plan dependencies proven to require no new media",
            "P1: shared dependencies ordered by descending batch impact, then earliest impacted batch/source step",
            "P2: batch-specific dependencies ordered by earliest impacted batch/source step",
            "dependency resolution priority does not authorize out-of-order media execution; B01-through-B34 continuity remains locked",
        ],
        "packets": packets,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    queue = build_queue()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(queue, sort_keys=False, allow_unicode=True, width=140), encoding="utf-8")

    if args.json:
        print(json.dumps({
            "action_packets": queue["summary"]["action_packets"],
            "proven_no_new_media_packets": queue["summary"]["proven_no_new_media_packets"],
            "owner_lane_counts": queue["summary"]["owner_lane_counts"],
            "priority_class_counts": queue["summary"]["priority_class_counts"],
            "first_six_dependency_ids": queue["summary"]["first_six_dependency_ids"],
            "output": out.as_posix(),
        }, indent=2))
    else:
        print(f"Built {len(queue['packets'])} action packets -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
