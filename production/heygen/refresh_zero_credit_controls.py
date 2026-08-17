#!/usr/bin/env python3
"""Refresh ANAADHI HeyGen blocker matrix, resolution plan, and action queue.

CONTROL / PLANNING ONLY.
- Runs the read-only HEYGEN-BATCH-MEDIA-VALIDATOR locally.
- Writes no media and calls no HeyGen service.
- Never changes APPROVED status.
- Preserves historical packet IDs for unchanged dependencies.
- Preserves AQ-004/AQ-005/AQ-006 as resolved history.
- Allocates new packet IDs only for genuinely new canonical dependencies.

This refresh is specifically safe while paid HeyGen work is deferred.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "production/heygen/HEYGEN_BATCH_BLOCKER_MATRIX.yaml"
PLAN = ROOT / "production/heygen/HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml"
QUEUE = ROOT / "production/heygen/HEYGEN_BATCH_DEPENDENCY_ACTION_QUEUE.yaml"
VALIDATOR = ROOT / "production/heygen/validate_heygen_batch_media.py"
PLAN_BUILDER = ROOT / "production/heygen/build_heygen_blocker_resolution_plan.py"

OLD_V1_QUEUE_BLOB = "6ece360ace926b94d022b6eaa66ac4591db89b6d"
P0_AQ003_PREVIOUS_DEP = "AVATAR_LOOK_SET::B01-AV-03,B01-AV-04,B01-AV-05,B01-AV-06,B01-AV-07,B01-AV-08,B01-AV-09"
P0_AQ003_CURRENT_DEP = "AVATAR_LOOK_SET::B01-AV-08"
LOGICAL_DEPENDENCY_PREFIX_LOCKS = {
    "SPATIAL::B26::PENDING_NAMED_LOCATION::": "HEYGEN-AQ-120",
}
P0_OPEN_IDS = {
    "CONSENT::ANAADHI_PRIVATE_AVATAR": "HEYGEN-AQ-001",
    "CONSENT::production/heygen/avatars/B01/B01_AVATAR_MANIFEST.yaml": "HEYGEN-AQ-002",
}
RESOLVED_HISTORY_IDS = {"HEYGEN-AQ-003", "HEYGEN-AQ-004", "HEYGEN-AQ-005", "HEYGEN-AQ-006"}
OWNER_MAP = {
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
ZERO_CREDIT_ACTIONABLE = {"GITHUB-ONLY", "DRIVE-VERIFY"}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump_yaml(path: Path, value: Any) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=180), encoding="utf-8")


def packet_num(packet_id: str) -> int:
    m = re.fullmatch(r"HEYGEN-AQ-(\d+)", str(packet_id))
    return int(m.group(1)) if m else 0


def batch_num(batch: str) -> int:
    m = re.fullmatch(r"B(\d{2})", str(batch))
    return int(m.group(1)) if m else 999


def validator_report() -> tuple[dict[str, Any], int]:
    proc = subprocess.run([sys.executable, str(VALIDATOR), "--json"], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode not in {0, 2}:
        raise SystemExit(f"Validator config/execution failure {proc.returncode}: {proc.stderr}")
    report = json.loads(proc.stdout)
    return report, proc.returncode


def read_old_v1_queue() -> dict[str, Any]:
    proc = subprocess.run(["git", "cat-file", "-p", OLD_V1_QUEUE_BLOB], cwd=ROOT, text=True, capture_output=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise SystemExit("Historical v1 queue blob unavailable; refuse to renumber packet history")
    return yaml.safe_load(proc.stdout) or {}


def collect_packets(doc: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(doc, dict):
        return out
    for key in ("packets", "new_packets"):
        value = doc.get(key)
        if isinstance(value, list):
            out.extend(x for x in value if isinstance(x, dict) and x.get("packet_id") and x.get("dependency_id"))
    return out


def resolved_history_from_current_queue(doc: dict[str, Any]) -> list[dict[str, Any]]:
    value = doc.get("resolved_history")
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    # v2 queue may encode the resolved set elsewhere; preserve canonical known evidence.
    return [
        {
            "packet_id": "HEYGEN-AQ-004",
            "dependency_id": "AVATAR_SLOT::B24::AVATAR_MANIFEST_UNASSIGNED",
            "status": "DEPENDENCY_RESOLVED_EVIDENCED",
            "active": False,
            "batch_unlocked": False,
        },
        {
            "packet_id": "HEYGEN-AQ-005",
            "dependency_id": "AVATAR_SLOT::B25::AVATAR_MANIFEST_UNASSIGNED",
            "status": "DEPENDENCY_RESOLVED_EVIDENCED",
            "active": False,
            "batch_unlocked": False,
        },
        {
            "packet_id": "HEYGEN-AQ-006",
            "dependency_id": "AVATAR_SLOT::B26::AVATAR_MANIFEST_UNASSIGNED",
            "status": "DEPENDENCY_RESOLVED_EVIDENCED",
            "active": False,
            "batch_unlocked": False,
        },
    ]


def owner_for(dep: dict[str, Any]) -> str:
    lane = str(dep.get("resolution_lane", ""))
    owner = OWNER_MAP.get(lane)
    if not owner:
        raise SystemExit(f"Unsupported resolution lane: {lane}")
    return owner


def handoffs(dep: dict[str, Any]) -> list[dict[str, str]]:
    lane = str(dep.get("resolution_lane", ""))
    need = dep.get("new_work_page_media_required")
    if lane == "DRIVE_EXACT_REUSE_CHECK_THEN_WORK_PAGE_MEDIA_IF_ABSENT":
        return [
            {"condition": "EXACT_APPROVED_CANONICAL_DRIVE_ASSET_FOUND", "to_owner_lane": "GITHUB-ONLY", "action": "Bind exact verified reuse evidence; never auto-promote APPROVED."},
            {"condition": "NO_EXACT_APPROVED_CANONICAL_DRIVE_ASSET_FOUND_AND_SEARCH_EVIDENCE_COMPLETE", "to_owner_lane": "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING", "action": "Defer creation until a later explicit media-creation approval and credit-ready state."},
        ]
    if lane == "SPATIAL_BINDING_FIRST_THEN_EXISTING_ASSET_CHECK":
        return [
            {"condition": "BINDING_CANNOT_BE_CLOSED_FROM_EXISTING_APPROVED_GITHUB_PLATES", "to_owner_lane": "DRIVE-VERIFY", "action": "Search exact canonical Drive reuse and approval evidence."},
            {"condition": "GITHUB_AND_DRIVE_EXACT_REUSE_CHECKS_PROVE_CANONICAL_VISUAL_GAP", "to_owner_lane": "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING", "action": "Defer creation until later explicit approval and credit-ready state."},
        ]
    if lane in {"WORK_PAGE_AVATAR_PARTIAL_REUSE_THEN_GAP_REVIEW", "WORK_PAGE_AVATAR_REUSE_OR_SOURCE_GAP_REVIEW"} and need not in (False, None, "False"):
        return [{"condition": "REUSE_CHAIN_EXHAUSTED_AND_SLOT_UNCOVERED", "to_owner_lane": "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING", "action": "Defer new avatar source creation until credit-ready explicit approval."}]
    if lane == "CONSENT_STATE_UPDATE":
        return [{"condition": "AFFIRMATIVE_CONSENT_STATE_OBSERVED", "to_owner_lane": "GITHUB-ONLY", "action": "Record only authoritative observed consent evidence."}]
    return []


def priority_tuple(packet: dict[str, Any]) -> tuple[Any, ...]:
    dep_id = packet["dependency_id"]
    if dep_id in P0_OPEN_IDS:
        return (0, packet_num(packet["packet_id"]))
    zero = packet["owner_lane"] in ZERO_CREDIT_ACTIONABLE
    shared = packet["scope"] == "SHARED" or packet["batch_impact"] > 1
    earliest = min((batch_num(b) for b in packet["impacted_batches"]), default=999)
    return (
        1 if zero and shared else 2 if zero else 3 if shared else 4,
        -packet["batch_impact"] if shared else 0,
        earliest,
        packet["dependency_id"],
    )


def main() -> None:
    old_matrix = load_yaml(MATRIX)
    old_queue = load_yaml(QUEUE)
    old_v1_queue = read_old_v1_queue()

    report, validator_exit = validator_report()
    if report.get("summary", {}).get("selected_batches") != 34:
        raise SystemExit("Unexpected validator scope")

    p0_overlay = old_matrix.get("p0_packet_overlay", {})
    if isinstance(p0_overlay, dict):
        p0_overlay["highest_priority_open"] = [
            item for item in (p0_overlay.get("highest_priority_open", []) or [])
            if not (isinstance(item, dict) and item.get("packet_id") == "HEYGEN-AQ-003")
        ]
        resolved_overlay = p0_overlay.setdefault("resolved_history", [])
        if not any(isinstance(item, dict) and item.get("packet_id") == "HEYGEN-AQ-003" for item in resolved_overlay):
            resolved_overlay.append({
                "packet_id": "HEYGEN-AQ-003",
                "dependency_id": P0_AQ003_CURRENT_DEP,
                "status": "DEPENDENCY_RESOLVED_EVIDENCED",
                "active": False,
                "batch_unlocked": False,
                "evidence": "B01 manifest is HEYGEN_9_OF_9_COMPLETE and B01-AV-08 is COMPLETE.",
            })

    matrix = {
        "version": 3,
        "project": "ANAADHI",
        "control": "HEYGEN-BATCH-BLOCKER-MATRIX",
        "status": "LIVE_ZERO_CREDIT_POST_ENV6L_SEMANTIC_CORRECTION__HARD_BLOCKS_REMAIN",
        "mode": "VALIDATION_ONLY__ZERO_MEDIA_GENERATION__ZERO_MEDIA_REPLACEMENT__ZERO_HEYGEN_SUBMISSION",
        "validated_scope": "B01-B34 / SC001-SC100",
        "validated_repository_head": os.environ.get("GITHUB_SHA", "LOCAL_CONTROL_REFRESH"),
        "validator_exit_code": validator_exit,
        "gate_result": "PASS" if validator_exit == 0 else "HARD_BLOCKED",
        "report": report,
        "p0_packet_overlay": p0_overlay,
        "resolved_history": old_matrix.get("p0_packet_overlay", {}).get("resolved_history", []),
        "zero_credit_control_sources": {
            "frozen_mapping": "production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml",
            "late_batch_crosswalk": "production/locations/P1_LATE_BATCH_ENV6L_BINDING_CROSSWALK.yaml",
            "late_semantic_audit": "production/locations/P1_LATE_SEMANTIC_REQUIREMENT_AUDIT.yaml",
        },
        "safety": {
            "media_generated": False,
            "media_replaced": False,
            "approved_status_changed": False,
            "heygen_submission": False,
            "heygen_execution": False,
            "paid_heygen_work_deferred": True,
        },
    }
    dump_yaml(MATRIX, matrix)

    subprocess.run([sys.executable, str(PLAN_BUILDER)], cwd=ROOT, check=True)
    plan = load_yaml(PLAN)
    plan["version"] = 3
    plan["status"] = "LIVE_ZERO_CREDIT_POST_ENV6L_SEMANTIC_CORRECTION"
    plan["zero_credit_operating_gate"] = {
        "paid_heygen_work_deferred": True,
        "zero_credit_actionable_owner_lanes": ["GITHUB-ONLY", "DRIVE-VERIFY"],
        "deferred_owner_lanes": ["CONSENT-VERIFY", "WORK-PAGE-AVATAR-COMPLETION", "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING"],
        "rule": "Continue control/reuse/dependency work only; do not initiate paid HeyGen/media execution until the user explicitly opens the credit-ready gate.",
    }
    plan["p0_state"] = {
        "open_packet_ids": ["HEYGEN-AQ-001", "HEYGEN-AQ-002"],
        "resolved_history_packet_ids": ["HEYGEN-AQ-003", "HEYGEN-AQ-004", "HEYGEN-AQ-005", "HEYGEN-AQ-006"],
        "consent_handoff_status": "PREPARED_NOT_INITIATED",
        "aq003_logical_packet_id": "HEYGEN-AQ-003",
        "aq003_previous_dependency_id": P0_AQ003_PREVIOUS_DEP,
        "aq003_final_dependency_id": P0_AQ003_CURRENT_DEP,
        "aq003_status": "DEPENDENCY_RESOLVED_EVIDENCED",
        "aq003_resolution_reason": "B01 is factually HEYGEN_9_OF_9_COMPLETE; B01-AV-08 Allied Gangster completed and may not be resurrected as a live blocker.",
    }
    dump_yaml(PLAN, plan)

    dependencies = [d for d in plan.get("safe_dependency_resolution_order", []) if isinstance(d, dict) and d.get("dependency_id")]
    current_dep_ids = {str(d["dependency_id"]) for d in dependencies}

    prior_packets = collect_packets(old_v1_queue) + collect_packets(old_queue)
    prior_by_dep: dict[str, dict[str, Any]] = {}
    for packet in prior_packets:
        dep_id = str(packet["dependency_id"])
        pid = str(packet["packet_id"])
        existing = prior_by_dep.get(dep_id)
        if existing is None or packet_num(pid) > packet_num(str(existing["packet_id"])):
            prior_by_dep[dep_id] = packet

    aq003_evolution_history = [{
        "logical_packet_id": "HEYGEN-AQ-003",
        "previous_dependency_id": P0_AQ003_PREVIOUS_DEP,
        "final_dependency_id": P0_AQ003_CURRENT_DEP,
        "status": "DEPENDENCY_RESOLVED_EVIDENCED",
        "reason": "B01-AV-08 Allied Gangster completed; B01 is now 9/9 complete.",
        "paid_execution_authorized_by_history": False,
    }]
    # Remove both historical and final live keys so AQ-003 cannot be reallocated or resurrected.
    prior_by_dep.pop(P0_AQ003_PREVIOUS_DEP, None)
    prior_by_dep.pop(P0_AQ003_CURRENT_DEP, None)

    # Hard lock historical P0 logical packet identities to their current live dependencies.
    for dep_id, pid in P0_OPEN_IDS.items():
        if dep_id not in current_dep_ids:
            raise SystemExit(f"P0 dependency disappeared unexpectedly: {dep_id}")
        prior_by_dep[dep_id] = {"packet_id": pid, "dependency_id": dep_id}

    # Preserve logical packet identity when canonical corrections narrow dependency payload text.
    for prefix, locked_packet_id in LOGICAL_DEPENDENCY_PREFIX_LOCKS.items():
        current_matches = [dep_id for dep_id in current_dep_ids if dep_id.startswith(prefix)]
        if not current_matches:
            continue
        if len(current_matches) != 1:
            raise SystemExit(f"Logical dependency prefix is ambiguous: {prefix} -> {current_matches}")
        current_dep_id = current_matches[0]
        prior_matches = [dep_id for dep_id in prior_by_dep if dep_id.startswith(prefix)]
        for prior_dep_id in prior_matches:
            prior_by_dep.pop(prior_dep_id, None)
        prior_by_dep[current_dep_id] = {
            "packet_id": locked_packet_id,
            "dependency_id": current_dep_id,
        }

    resolved_history = resolved_history_from_current_queue(old_queue)
    if not any(str(x.get("packet_id")) == "HEYGEN-AQ-003" for x in resolved_history):
        resolved_history.append({
            "packet_id": "HEYGEN-AQ-003",
            "dependency_id": P0_AQ003_CURRENT_DEP,
            "status": "DEPENDENCY_RESOLVED_EVIDENCED",
            "active": False,
            "batch_unlocked": False,
            "evidence": "B01 manifest HEYGEN_9_OF_9_COMPLETE; B01-AV-08 COMPLETE.",
        })
    resolved_dep_ids = {str(x.get("dependency_id")) for x in resolved_history}
    if current_dep_ids & resolved_dep_ids:
        raise SystemExit("Resolved AQ-004/005/006 dependency unexpectedly returned live")

    high_water = max([167] + [packet_num(str(p.get("packet_id"))) for p in prior_packets])
    next_id = high_water + 1
    packets: list[dict[str, Any]] = []
    new_packet_ids: list[str] = []

    for dep in dependencies:
        dep_id = str(dep["dependency_id"])
        prior = prior_by_dep.get(dep_id)
        if prior:
            packet_id = str(prior["packet_id"])
        else:
            packet_id = f"HEYGEN-AQ-{next_id:03d}"
            next_id += 1
            new_packet_ids.append(packet_id)
        owner = owner_for(dep)
        batches = sorted([str(x) for x in dep.get("batches", [])], key=batch_num)
        impact = int(dep.get("batch_impact", len(batches)))
        priority_class = "P0_OPEN" if dep_id in P0_OPEN_IDS else "P1_SHARED_HIGH_IMPACT" if (dep.get("scope") == "SHARED" or impact > 1) else "P2_BATCH_SPECIFIC"
        zero_state = "ZERO_CREDIT_ACTIONABLE" if owner in ZERO_CREDIT_ACTIONABLE else "DEFERRED_UNTIL_CREDIT_READY_OR_EXPLICIT_EXECUTION_GATE"
        packets.append({
            "packet_id": packet_id,
            "dependency_id": dep_id,
            "active": True,
            "status": "OPEN_UNRESOLVED",
            "priority_class": priority_class,
            "owner_lane": owner,
            "zero_credit_execution_state": zero_state,
            "source_resolution_lane": dep.get("resolution_lane"),
            "scope": dep.get("scope"),
            "batch_impact": impact,
            "impacted_batches": batches,
            "current_new_media_requirement": dep.get("new_work_page_media_required"),
            "safe_first_action": dep.get("safe_first_action"),
            "conditional_handoffs": handoffs(dep),
            "closure_rule": "Dependency remains open until authoritative evidence is recorded and a fresh validator no longer emits the corresponding blocker.",
            "approved_status_change_allowed": False,
            "media_generation_allowed": False,
            "heygen_submission_allowed": False,
        })

    packets.sort(key=priority_tuple)
    for idx, p in enumerate(packets, start=1):
        p["queue_position"] = idx

    # Dependencies from the prior active queue that no longer exist are preserved as superseded history.
    superseded = []
    for dep_id, packet in sorted(prior_by_dep.items(), key=lambda kv: packet_num(str(kv[1]["packet_id"]))):
        pid = str(packet["packet_id"])
        if dep_id not in current_dep_ids and pid not in RESOLVED_HISTORY_IDS:
            superseded.append({
                "packet_id": pid,
                "dependency_id": dep_id,
                "status": "SUPERSEDED_BY_CANONICAL_CONTROL_CORRECTION",
                "active": False,
                "reason": "Fresh validator no longer emits this canonical dependency after frozen ENV-6L metadata/semantic correction.",
            })

    if len(packets) != int(plan.get("deduplication_summary", {}).get("canonical_dependencies", -1)):
        raise SystemExit("Active packet count != canonical dependency count")
    if len({p["packet_id"] for p in packets}) != len(packets) or len({p["dependency_id"] for p in packets}) != len(packets):
        raise SystemExit("Duplicate packet/dependency identity")
    for dep_id, pid in P0_OPEN_IDS.items():
        if next(p["packet_id"] for p in packets if p["dependency_id"] == dep_id) != pid:
            raise SystemExit("P0 packet ID drift")

    owner_counts = Counter(p["owner_lane"] for p in packets)
    zero_counts = Counter(p["zero_credit_execution_state"] for p in packets)
    priority_counts = Counter(p["priority_class"] for p in packets)
    action_views: dict[str, list[str]] = defaultdict(list)
    for p in packets:
        action_views[p["zero_credit_execution_state"]].append(p["packet_id"])

    queue = {
        "version": 3,
        "project": "ANAADHI",
        "control": "HEYGEN-BATCH-DEPENDENCY-ACTION-QUEUE",
        "status": "LIVE_ZERO_CREDIT_QUEUE__PAID_HEYGEN_EXECUTION_DEFERRED",
        "mode": "PLANNING_AND_ZERO_CREDIT_CONTROL_ONLY__ZERO_MEDIA_GENERATION__ZERO_HEYGEN_SUBMISSION",
        "source_plan": "production/heygen/HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml",
        "summary": {
            "active_action_packets": len(packets),
            "resolved_history_packets": len(resolved_history),
            "superseded_history_packets": len(superseded),
            "packet_namespace_high_watermark": f"HEYGEN-AQ-{max(packet_num(p['packet_id']) for p in packets + resolved_history + superseded):03d}",
            "new_packet_ids_allocated_this_refresh": new_packet_ids,
            "priority_class_counts": dict(sorted(priority_counts.items())),
            "owner_lane_counts": dict(sorted(owner_counts.items())),
            "zero_credit_execution_state_counts": dict(sorted(zero_counts.items())),
        },
        "credit_gate": {
            "paid_heygen_work_ready": False,
            "current_action": "CONTINUE_ZERO_CREDIT_REPOSITORY_AND_DRIVE_WORK_ONLY",
            "zero_credit_owner_lanes": ["GITHUB-ONLY", "DRIVE-VERIFY"],
            "deferred_owner_lanes": ["CONSENT-VERIFY", "WORK-PAGE-AVATAR-COMPLETION", "WORK-PAGE-NEW-MEDIA-ONLY-IF-PROVEN-MISSING"],
            "no_heygen_consent_or_media_execution": True,
        },
        "p0_identity_lock": {
            "open": P0_OPEN_IDS,
            "resolved_history_packet_ids": ["HEYGEN-AQ-003", "HEYGEN-AQ-004", "HEYGEN-AQ-005", "HEYGEN-AQ-006"],
            "aq003_evolution_history": aq003_evolution_history,
        },
        "resolved_history": resolved_history,
        "superseded_history": superseded,
        "action_views": dict(action_views),
        "packets": packets,
        "safety": {
            "media_generated": False,
            "media_replaced": False,
            "approved_status_changed": False,
            "heygen_called": False,
            "heygen_submission_or_execution": False,
        },
    }
    dump_yaml(QUEUE, queue)

    print(json.dumps({
        "raw_blockers": report["summary"]["total_blockers"],
        "canonical_dependencies": plan["deduplication_summary"]["canonical_dependencies"],
        "active_packets": len(packets),
        "resolved_history": len(resolved_history),
        "superseded_history": len(superseded),
        "new_packet_ids": new_packet_ids,
        "zero_credit_actionable": zero_counts.get("ZERO_CREDIT_ACTIONABLE", 0),
        "deferred": zero_counts.get("DEFERRED_UNTIL_CREDIT_READY_OR_EXPLICIT_EXECUTION_GATE", 0),
        "validator_exit_code": validator_exit,
    }, indent=2))


if __name__ == "__main__":
    main()
