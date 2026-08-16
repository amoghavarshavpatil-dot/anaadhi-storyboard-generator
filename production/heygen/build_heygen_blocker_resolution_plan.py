#!/usr/bin/env python3
"""Build a fail-closed resolution plan from HEYGEN_BATCH_BLOCKER_MATRIX.yaml.

READ/PLAN ONLY:
- does not generate or replace media
- does not call HeyGen
- does not submit jobs
- does not fabricate APPROVED status
- does not mutate source registries/bindings/manifests

The output is a machine-readable dependency graph that deduplicates raw validator
blockers, classifies their safest resolution lane, and computes a dependency-first
batch unlock order.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "production/heygen/HEYGEN_BATCH_BLOCKER_MATRIX.yaml"
REGISTRY = ROOT / "production/references/REFERENCE_REGISTRY.yaml"
BINDINGS = ROOT / "production/batches/P1_BATCH_REFERENCE_BINDINGS.yaml"
AVATAR_INDEX = ROOT / "production/heygen/avatars/AVATAR_BATCH_INDEX.yaml"
CONTRACT = ROOT / "production/heygen/HEYGEN_API_ACCEPTANCE_CONTRACT.yaml"
DEFAULT_OUT = ROOT / "production/heygen/HEYGEN_BATCH_BLOCKER_RESOLUTION_PLAN.yaml"

MEDIA_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp",
    ".mp4", ".mov", ".mkv", ".webm", ".wav", ".mp3", ".m4a", ".flac",
}
AFFIRMATIVE = {"APPROVED", "COMPLETE", "COMPLETED", "VERIFIED", "NOT_REQUIRED"}
REF_RE = re.compile(r"(?P<ref>[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+):\s+status=")
AVATAR_ASSET_RE = re.compile(r"B\d{2}-AV-\d{2}")
MANIFEST_PATH_RE = re.compile(r"(production/heygen/avatars/[^\s'\"]+\.ya?ml)")


def load_yaml(path: Path) -> Any:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_nodes(obj: Any) -> Iterable[Any]:
    yield obj
    if isinstance(obj, dict):
        for value in obj.values():
            yield from iter_nodes(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from iter_nodes(value)


def flatten_registry(registry: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}

    def walk(obj: Any, key_hint: str | None = None) -> None:
        if isinstance(obj, dict):
            if key_hint and re.fullmatch(r"[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+", key_hint):
                out.setdefault(key_hint, obj)
            for field in ("id", "ref_id", "asset_id", "reference_id"):
                value = obj.get(field)
                if isinstance(value, str) and re.fullmatch(r"[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+", value):
                    out.setdefault(value, obj)
            for key, value in obj.items():
                walk(value, str(key))
        elif isinstance(obj, list):
            for value in obj:
                walk(value, key_hint)

    walk(registry)
    return out


def repo_media_candidates(ref_id: str) -> list[str]:
    token = ref_id.lower().replace("-", "")
    candidates: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in MEDIA_EXTENSIONS:
            continue
        compact = path.name.lower().replace("-", "").replace("_", "")
        if token in compact:
            candidates.append(path.relative_to(ROOT).as_posix())
    return sorted(set(candidates))[:20]


def registry_path_evidence(record: dict[str, Any] | None) -> tuple[str | None, bool]:
    if not record:
        return None, False
    for field in ("path", "repo_path", "asset_path", "file", "source_path"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            p = ROOT / value
            return value, p.exists() and p.is_file()
    return None, False


def normalized_message(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip())


def canonical_key(blocker: dict[str, Any]) -> str:
    code = str(blocker.get("code", "UNKNOWN"))
    category = str(blocker.get("category", "unknown"))
    message = normalized_message(str(blocker.get("message", "")))
    batch = str(blocker.get("batch_id", "GLOBAL"))

    if code == "REFERENCE_NOT_APPROVED":
        match = REF_RE.search(message)
        if match:
            return f"REF::{match.group('ref')}"
    if code == "ANAADHI_CONSENT_UNVERIFIED":
        return "CONSENT::ANAADHI_PRIVATE_AVATAR"
    if code == "CONSENT_UNRESOLVED":
        match = MANIFEST_PATH_RE.search(message)
        if match:
            return f"CONSENT::{match.group(1)}"
        return f"CONSENT::{batch}"
    if category == "avatar-slot":
        assets = sorted(set(AVATAR_ASSET_RE.findall(message)))
        if assets:
            return "AVATAR_LOOK_SET::" + ",".join(assets)
        return f"AVATAR_SLOT::{batch}::{code}"
    if category in {"nested-space", "location"} and code in {
        "REMAINING_LOCATION_WORK", "PENDING_NAMED_LOCATION_REFS", "PENDING_NAMED_LOCATION", "APPROVED_ROOT_FALSE",
        "ROOT_NOT_APPROVED", "ROOT_LOCATION_UNRESOLVED", "NESTED_SPACE_UNRESOLVED",
    }:
        return f"SPATIAL::{batch}::{code}::{message}"
    return f"{category.upper()}::{code}::{message}"


def avatar_index_map(index: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                if re.fullmatch(r"B\d{2}", str(key)) and isinstance(value, dict):
                    out.setdefault(str(key), value)
                if isinstance(value, dict):
                    bid = value.get("batch_id") or value.get("batch") or value.get("id")
                    if isinstance(bid, str) and re.fullmatch(r"B\d{2}", bid):
                        out.setdefault(bid, value)
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(index)
    return out


def find_manifest_path(batch: str, avatar_index: dict[str, dict[str, Any]]) -> str | None:
    record = avatar_index.get(batch, {})
    for field in ("manifest", "manifest_path", "avatar_manifest"):
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return None


def manifest_assets(manifest_path: str | None) -> list[dict[str, Any]]:
    if not manifest_path:
        return []
    doc = load_yaml(ROOT / manifest_path)
    for key in ("assets", "avatar_assets", "avatars"):
        value = doc.get(key) if isinstance(doc, dict) else None
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]
        if isinstance(value, dict):
            found = []
            for aid, payload in value.items():
                if not isinstance(payload, dict):
                    continue
                item = dict(payload)
                item.setdefault("_manifest_asset_id", str(aid))
                if AVATAR_ASSET_RE.fullmatch(str(aid)):
                    item.setdefault("asset_id", str(aid))
                found.append(item)
            return found
    found: list[dict[str, Any]] = []
    for node in iter_nodes(doc):
        if isinstance(node, dict):
            aid = node.get("asset_id") or node.get("id") or node.get("_manifest_asset_id")
            if isinstance(aid, str) and AVATAR_ASSET_RE.fullmatch(aid):
                found.append(node)
    return found


def asset_source_path(asset: dict[str, Any]) -> str | None:
    for field in ("source_visual", "source_visual_path", "source_path", "image_path", "source_image"):
        value = asset.get(field)
        if isinstance(value, str) and value.strip():
            return value
    for node in iter_nodes(asset):
        if isinstance(node, dict):
            for field in ("path", "source_path", "image_path"):
                value = node.get(field)
                if isinstance(value, str) and value.startswith("production/"):
                    return value
    return None


def classify_dependency(dep: dict[str, Any], registry_map: dict[str, dict[str, Any]], avatar_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    blocker = dep["representative_blocker"]
    code = str(blocker.get("code", ""))
    category = str(blocker.get("category", ""))
    message = str(blocker.get("message", ""))
    batches = dep["batches"]

    result = {
        "resolution_lane": "FAIL_CLOSED_REVIEW_REQUIRED",
        "new_work_page_media_required": "UNDETERMINED",
        "safe_first_action": "Review the canonical dependency without changing any approval state.",
        "evidence": {},
    }

    if code in {"ANAADHI_CONSENT_UNVERIFIED", "CONSENT_UNRESOLVED"} or category == "consent":
        result.update({
            "resolution_lane": "CONSENT_STATE_UPDATE",
            "new_work_page_media_required": False,
            "safe_first_action": "Verify the actual private-avatar consent state, then record only the observed affirmative state; do not infer consent.",
        })
        return result

    if category in {"api-field", "api", "safety", "security", "contract", "schema"} or any(
        token in code for token in ("UNSUPPORTED", "UNKNOWN_FIELD", "FIELD_", "CONTRACT", "SCHEMA", "SECRET")
    ):
        result.update({
            "resolution_lane": "GITHUB_CONTROL_OR_SCHEMA_CORRECTION",
            "new_work_page_media_required": False,
            "safe_first_action": "Correct only machine-readable control/payload fields, then rerun the validator.",
        })
        return result

    if code == "REFERENCE_NOT_APPROVED":
        match = REF_RE.search(message)
        ref_id = match.group("ref") if match else None
        record = registry_map.get(ref_id or "")
        record_path, record_path_exists = registry_path_evidence(record)
        candidates = repo_media_candidates(ref_id) if ref_id else []
        current_status = record.get("status") if isinstance(record, dict) else None
        result["evidence"] = {
            "reference_id": ref_id,
            "registry_status": current_status,
            "registry_path": record_path,
            "registry_path_exists": record_path_exists,
            "github_exact_id_media_candidates": candidates,
            "drive_exact_approved_match": None,
        }
        if record_path_exists or candidates:
            result.update({
                "resolution_lane": "EXISTING_GITHUB_ASSET_REVIEW_THEN_REGISTRY_OR_BINDING_CORRECTION",
                "new_work_page_media_required": False,
                "safe_first_action": "Review the existing repository candidate against canon. Only after explicit approval, correct the registry/binding; never auto-promote status.",
            })
        elif category in {"location", "prop", "vehicle", "technology", "environment", "character-state"}:
            result.update({
                "resolution_lane": "DRIVE_EXACT_REUSE_CHECK_THEN_WORK_PAGE_MEDIA_IF_ABSENT",
                "new_work_page_media_required": "CONDITIONAL_ON_NO_EXACT_APPROVED_DRIVE_ASSET",
                "safe_first_action": "Search Drive for an exact already-approved canonical asset. If none exists, route creation exclusively to the Work page.",
            })
        else:
            result.update({
                "resolution_lane": "REGISTRY_OR_BINDING_REVIEW",
                "new_work_page_media_required": "UNDETERMINED",
                "safe_first_action": "Verify whether the blocker is metadata-only before requesting any media work.",
            })
        return result

    if category == "avatar-slot":
        batch = batches[0] if len(batches) == 1 else None
        index_record = avatar_index.get(batch, {}) if batch else {}
        index_status = str(index_record.get("status", "")) if isinstance(index_record, dict) else ""
        manifest_path = find_manifest_path(batch, avatar_index) if batch else None
        assets = manifest_assets(manifest_path)
        unresolved_ids = set(AVATAR_ASSET_RE.findall(message))
        targeted = []
        for asset in assets:
            aid = asset.get("asset_id") or asset.get("id") or asset.get("_manifest_asset_id")
            if unresolved_ids and aid not in unresolved_ids:
                continue
            src = asset_source_path(asset)
            targeted.append({
                "asset_id": aid,
                "source_path": src,
                "source_exists": bool(src and (ROOT / src).exists()),
                "drive_status": asset.get("drive_status"),
                "drive_file_id_present": bool(asset.get("drive_file_id")),
                "heygen_status": asset.get("heygen_status") or asset.get("status"),
                "heygen_look_id_present": bool(asset.get("heygen_look_id") or asset.get("look_id")),
            })
        all_source_existing = bool(targeted) and all(x["source_exists"] for x in targeted)

        b01_manifest = "production/heygen/avatars/B01/B01_AVATAR_MANIFEST.yaml"
        b01_reusable = []
        if batch and batch != "B01":
            for asset in manifest_assets(b01_manifest):
                reuse = asset.get("reuse_batches") or []
                if batch in reuse:
                    src = asset_source_path(asset)
                    b01_reusable.append({
                        "asset_id": asset.get("asset_id") or asset.get("_manifest_asset_id"),
                        "character_ref": asset.get("character_ref"),
                        "source_path": src,
                        "source_exists": bool(src and (ROOT / src).exists()),
                        "drive_status": asset.get("drive_status"),
                        "heygen_look_id_present": bool(asset.get("heygen_look_id") or asset.get("look_id")),
                    })

        result["evidence"] = {
            "avatar_index_status": index_status or None,
            "manifest": manifest_path,
            "targeted_avatar_assets": targeted,
            "b01_reuse_evidence": b01_reusable,
        }
        if all_source_existing:
            result.update({
                "resolution_lane": "WORK_PAGE_AVATAR_LOOK_COMPLETION_FROM_EXISTING_GITHUB_DRIVE_SOURCE",
                "new_work_page_media_required": False,
                "safe_first_action": "Use the exact existing GitHub source visual already archived to Drive to complete the HeyGen look on the Work page; do not regenerate the source visual.",
            })
        elif "REUSE_B01_CAPTURE_IDENTITIES" in index_status:
            result.update({
                "resolution_lane": "WORK_PAGE_AVATAR_MANIFEST_BINDING_TO_EXISTING_B01_IDENTITIES",
                "new_work_page_media_required": False,
                "safe_first_action": "Author the batch avatar manifest by binding the explicitly designated B01 capture identities/looks; do not create replacement identity media.",
            })
        elif b01_reusable:
            result.update({
                "resolution_lane": "WORK_PAGE_AVATAR_PARTIAL_REUSE_THEN_GAP_REVIEW",
                "new_work_page_media_required": "CONDITIONAL_ON_UNCOVERED_AVATAR_SLOTS",
                "safe_first_action": "Bind every documented B01 reusable identity/source first. Only uncovered named-character slots may proceed to new Work-page avatar-source creation.",
            })
        else:
            result.update({
                "resolution_lane": "WORK_PAGE_AVATAR_REUSE_OR_SOURCE_GAP_REVIEW",
                "new_work_page_media_required": "CONDITIONAL_ON_REUSE_SOURCE_AVAILABILITY",
                "safe_first_action": "Check the avatar index/reuse chain first. Create a new source visual only on the Work page and only when no approved reusable source exists.",
            })
        return result

    if category in {"nested-space", "location"} and code in {
        "REMAINING_LOCATION_WORK", "PENDING_NAMED_LOCATION_REFS", "PENDING_NAMED_LOCATION", "APPROVED_ROOT_FALSE", "ROOT_NOT_APPROVED", "ROOT_LOCATION_UNRESOLVED", "NESTED_SPACE_UNRESOLVED"
    }:
        result.update({
            "resolution_lane": "SPATIAL_BINDING_FIRST_THEN_EXISTING_ASSET_CHECK",
            "new_work_page_media_required": "CONDITIONAL_ON_MISSING_CANONICAL_SPACE_ASSET",
            "safe_first_action": "Resolve root/nested-space identity and binding from existing approved plates first. Only unresolved canonical visual gaps may be routed to Work-page creation.",
        })
        return result

    result["safe_first_action"] = "Resolve metadata/control evidence first; preserve the hard block until the validator proves the dependency cleared."
    return result


def lane_priority(lane: str) -> int:
    order = {
        "GITHUB_CONTROL_OR_SCHEMA_CORRECTION": 10,
        "CONSENT_STATE_UPDATE": 20,
        "EXISTING_GITHUB_ASSET_REVIEW_THEN_REGISTRY_OR_BINDING_CORRECTION": 30,
        "SPATIAL_BINDING_FIRST_THEN_EXISTING_ASSET_CHECK": 40,
        "WORK_PAGE_AVATAR_LOOK_COMPLETION_FROM_EXISTING_GITHUB_DRIVE_SOURCE": 50,
        "WORK_PAGE_AVATAR_MANIFEST_BINDING_TO_EXISTING_B01_IDENTITIES": 52,
        "WORK_PAGE_AVATAR_PARTIAL_REUSE_THEN_GAP_REVIEW": 55,
        "WORK_PAGE_AVATAR_REUSE_OR_SOURCE_GAP_REVIEW": 60,
        "DRIVE_EXACT_REUSE_CHECK_THEN_WORK_PAGE_MEDIA_IF_ABSENT": 70,
        "REGISTRY_OR_BINDING_REVIEW": 80,
        "FAIL_CLOSED_REVIEW_REQUIRED": 90,
    }
    return order.get(lane, 99)


def build_plan() -> dict[str, Any]:
    matrix = load_yaml(MATRIX)
    report = matrix.get("report", {}) if isinstance(matrix, dict) else {}
    batches = report.get("batches", {}) if isinstance(report, dict) else {}
    summary = report.get("summary", {}) if isinstance(report, dict) else {}
    registry = load_yaml(REGISTRY)
    registry_map = flatten_registry(registry)
    bindings = load_yaml(BINDINGS)
    avatar_index_doc = load_yaml(AVATAR_INDEX)
    avatar_index = avatar_index_map(avatar_index_doc)
    contract = load_yaml(CONTRACT)

    raw_blockers: list[dict[str, Any]] = []
    for batch_id in sorted(batches):
        values = batches.get(batch_id) or []
        for blocker in values:
            if not isinstance(blocker, dict):
                continue
            item = dict(blocker)
            item.setdefault("batch_id", batch_id)
            raw_blockers.append(item)

    deps: dict[str, dict[str, Any]] = {}
    for i, blocker in enumerate(raw_blockers, start=1):
        key = canonical_key(blocker)
        dep = deps.setdefault(key, {
            "dependency_id": key,
            "batches": set(),
            "raw_blocker_count": 0,
            "raw_blocker_numbers": [],
            "representative_blocker": blocker,
        })
        dep["batches"].add(str(blocker.get("batch_id", "GLOBAL")))
        dep["raw_blocker_count"] += 1
        dep["raw_blocker_numbers"].append(i)

    dependency_list: list[dict[str, Any]] = []
    for dep in deps.values():
        dep["batches"] = sorted(dep["batches"])
        dep["batch_impact"] = len(dep["batches"])
        dep["scope"] = "SHARED" if dep["batch_impact"] > 1 else "BATCH_SPECIFIC"
        dep.update(classify_dependency(dep, registry_map, avatar_index))
        dependency_list.append(dep)

    dependency_list.sort(key=lambda d: (
        lane_priority(str(d["resolution_lane"])),
        -int(d["batch_impact"]),
        str(d["dependency_id"]),
    ))

    dep_order = {dep["dependency_id"]: idx for idx, dep in enumerate(dependency_list, start=1)}
    batch_deps: dict[str, set[str]] = defaultdict(set)
    for dep in dependency_list:
        for batch in dep["batches"]:
            if re.fullmatch(r"B\d{2}", batch):
                batch_deps[batch].add(dep["dependency_id"])

    unlock_rows = []
    for batch in [f"B{i:02d}" for i in range(1, 35)]:
        keys = sorted(batch_deps.get(batch, set()), key=lambda k: dep_order[k])
        unlock_index = max((dep_order[k] for k in keys), default=0)
        lane_counts = Counter(next(d["resolution_lane"] for d in dependency_list if d["dependency_id"] == k) for k in keys)
        unlock_rows.append({
            "batch_id": batch,
            "canonical_dependency_count": len(keys),
            "unlock_after_dependency_step": unlock_index,
            "dependencies_in_safe_order": keys,
            "resolution_lane_counts": dict(sorted(lane_counts.items())),
        })
    unlock_rows.sort(key=lambda r: (r["unlock_after_dependency_step"], r["canonical_dependency_count"], r["batch_id"]))

    lane_counts = Counter(str(d["resolution_lane"]) for d in dependency_list)
    media_requirement_counts = Counter(str(d["new_work_page_media_required"]) for d in dependency_list)
    shared = [d["dependency_id"] for d in dependency_list if d["scope"] == "SHARED"]
    batch_specific = [d["dependency_id"] for d in dependency_list if d["scope"] == "BATCH_SPECIFIC"]
    work_page_definite = [d["dependency_id"] for d in dependency_list if d["new_work_page_media_required"] is True]
    work_page_conditional = [d["dependency_id"] for d in dependency_list if isinstance(d["new_work_page_media_required"], str) and d["new_work_page_media_required"].startswith("CONDITIONAL")]
    no_new_media = [d["dependency_id"] for d in dependency_list if d["new_work_page_media_required"] is False]

    plan = {
        "version": 1,
        "project": "ANAADHI",
        "control": "HEYGEN-BATCH-BLOCKER-RESOLUTION-PLAN",
        "mode": "PLANNING_ONLY__ZERO_MEDIA_GENERATION__ZERO_HEYGEN_SUBMISSION",
        "source_matrix": MATRIX.relative_to(ROOT).as_posix(),
        "source_matrix_sha256": sha256(MATRIX),
        "validated_scope": "B01-B34 / SC001-SC100",
        "invariants": {
            "fabricate_approved_status": False,
            "generate_or_replace_media_in_this_chat": False,
            "heygen_submission_or_execution": False,
            "existing_assets_first": True,
            "work_page_is_exclusive_owner_of_new_media_and_avatar_visual_creation": True,
            "drive_reuse_requires_exact_asset_and_real_approval_evidence": True,
        },
        "source_snapshot": {
            "raw_matrix_summary": summary,
            "raw_blockers_seen": len(raw_blockers),
            "binding_source_loaded": bool(bindings),
            "registry_source_loaded": bool(registry),
            "avatar_index_loaded": bool(avatar_index_doc),
            "acceptance_contract_loaded": bool(contract),
        },
        "deduplication_summary": {
            "canonical_dependencies": len(dependency_list),
            "shared_dependencies": len(shared),
            "batch_specific_dependencies": len(batch_specific),
            "raw_blockers_collapsed": max(0, len(raw_blockers) - len(dependency_list)),
            "resolution_lane_counts": dict(sorted(lane_counts.items())),
            "new_work_page_media_requirement_counts": dict(sorted(media_requirement_counts.items())),
        },
        "hard_separation": {
            "no_new_media_required": no_new_media,
            "conditional_work_page_media_only_after_existing_asset_checks_fail": work_page_conditional,
            "definite_new_work_page_media_required": work_page_definite,
            "rule": "A conditional dependency must not be sent for creation until GitHub/Drive exact-reuse and binding/reuse checks are exhausted.",
        },
        "drive_reuse_evidence": {
            "status": "NO_EXACT_APPROVED_DRIVE_MATCH_CONFIRMED_BY_CURRENT_CONNECTOR_SEARCH",
            "note": "Drive reuse remains fail-closed. The planner does not infer approval from folder/project presence or fuzzy naming.",
        },
        "safe_dependency_resolution_order": [
            {
                "step": idx,
                "dependency_id": dep["dependency_id"],
                "scope": dep["scope"],
                "batch_impact": dep["batch_impact"],
                "batches": dep["batches"],
                "resolution_lane": dep["resolution_lane"],
                "new_work_page_media_required": dep["new_work_page_media_required"],
                "safe_first_action": dep["safe_first_action"],
            }
            for idx, dep in enumerate(dependency_list, start=1)
        ],
        "batch_unlock_order": unlock_rows,
        "canonical_dependencies": dependency_list,
    }
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    plan = build_plan()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(yaml.safe_dump(plan, sort_keys=False, allow_unicode=True, width=180), encoding="utf-8")

    summary = {
        "raw_blockers": plan["source_snapshot"]["raw_blockers_seen"],
        **plan["deduplication_summary"],
        "first_10_batch_unlock_order": [x["batch_id"] for x in plan["batch_unlock_order"][:10]],
        "output": out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else str(out),
    }
    print(json.dumps(summary, indent=2) if args.json else yaml.safe_dump(summary, sort_keys=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
