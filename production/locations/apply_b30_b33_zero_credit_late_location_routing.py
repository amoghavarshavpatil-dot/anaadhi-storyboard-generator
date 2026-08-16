#!/usr/bin/env python3
"""Apply the audited B30/B33 late-location routing corrections.

CONTROL ONLY / ZERO CREDIT / ZERO MEDIA / ZERO HEYGEN.

This script is intentionally fail-closed:
- changes only registry, P1 requirements, P1 bindings and HeyGen media-input control schema;
- preserves every approved_root value;
- preserves every existing APPROVED status;
- adds numeric late-root registry records only as MISSING_APPROVED_ASSET/path=null;
- preserves LOC-011 vs LOC-072 and LOC-073 vs LOC-074 HOLD separation;
- never turns an XFORM/state into a new root;
- performs no network/API/media work.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "production/locations/P1_B30_B33_ZERO_CREDIT_LATE_LOCATION_ROUTING_AUDIT.yaml"
MAPPING = ROOT / "production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml"
DRIVE_AUDIT = ROOT / "production/references/DRIVE_LOCATION_AUDIT_LOC010_059.yaml"
REGISTRY = ROOT / "production/references/REFERENCE_REGISTRY.yaml"
REQUIREMENTS = ROOT / "production/references/BATCH_REFERENCE_REQUIREMENTS.yaml"
BINDINGS = ROOT / "production/batches/P1_BATCH_REFERENCE_BINDINGS.yaml"
SCHEMA = ROOT / "production/heygen/HEYGEN_BATCH_MEDIA_INPUT_SCHEMA.yaml"

B30_ROOTS = ["LOC-002", "LOC-003", "LOC-011", "LOC-068", "LOC-069", "LOC-070", "LOC-071", "LOC-080"]
B30_MOBILE = ["LOC-076", "LOC-077"]
B30_REQUIRED = [
    "LOC-ADRAKA-SYSTEMS-LAB",
    "LOC-PARAANE-CAMPUS-MATURE",
    "LOC-PARVARAN-JANNE-HOUSE",
    "LOC-068", "LOC-069", "LOC-070", "LOC-071", "LOC-080",
]
B33_ROOTS = [
    "LOC-003", "LOC-070", "LOC-072", "LOC-074", "LOC-080", "LOC-081",
    "LOC-082", "LOC-083", "LOC-084", "LOC-085", "LOC-086", "LOC-087",
]
B33_REQUIRED = [
    "LOC-PARAANE-CAMPUS-MATURE",
    "LOC-070", "LOC-072", "LOC-074", "LOC-080", "LOC-081", "LOC-082",
    "LOC-083", "LOC-084", "LOC-085", "LOC-086", "LOC-087",
]
NEW_NUMERIC_REFS = {
    "LOC-069": "Marsyaa's House",
    "LOC-070": "Kadraayini Media Network",
    "LOC-071": "Abandoned Irrigation Telemetry Shelter",
    "LOC-072": "Janne's Home",
    "LOC-074": "Sarjanya Operations Compound",
    "LOC-080": "Kendhalaa Police Headquarters",
    "LOC-081": "Detention-Review Hall",
    "LOC-082": "Joint Kendhalaa–Adraka Tribunal",
    "LOC-083": "Manimantharaa Hearing Venue",
    "LOC-084": "Kendhalaa Memorial Courtyard",
    "LOC-085": "Independent Secure Medical Unit",
    "LOC-086": "Public Inquiry Venue",
}


def fmt(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"


def batch_span(text: str, batch_id: str) -> tuple[int, int]:
    start_match = re.search(rf"(?m)^  {re.escape(batch_id)}:\s*$", text)
    if not start_match:
        raise RuntimeError(f"Missing batch {batch_id}")
    next_match = re.search(r"(?m)^  B\d{2}:\s*$", text[start_match.end():])
    end = start_match.end() + next_match.start() if next_match else len(text)
    return start_match.start(), end


def set_batch_field(text: str, batch_id: str, field: str, value: str) -> str:
    a, b = batch_span(text, batch_id)
    block = text[a:b]
    pattern = rf"(?m)^    {re.escape(field)}:.*$"
    if not re.search(pattern, block):
        raise RuntimeError(f"{batch_id}: missing {field}")
    block = re.sub(pattern, f"    {field}: {value}", block, count=1)
    return text[:a] + block + text[b:]


def approved_snapshot(value: Any, path: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            p = f"{path}.{key}" if path else str(key)
            if key == "status" and isinstance(child, str) and child.upper() == "APPROVED":
                out[path] = child
            out.update(approved_snapshot(child, p))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            out.update(approved_snapshot(child, f"{path}[{i}]"))
    return out


def enrich_loc011_semantic(text: str) -> str:
    old = '  LOC-PARVARAN-JANNE-HOUSE: {name: "Parvaran and Janne home / tulsi courtyard", status: MISSING_APPROVED_ASSET, path: null}'
    if old not in text:
        # Idempotent rerun allowed only if already enriched exactly.
        if '  LOC-PARVARAN-JANNE-HOUSE:\n    name: "Parvaran and Janne home / tulsi courtyard"' in text:
            return text
        raise RuntimeError("LOC-PARVARAN-JANNE-HOUSE semantic registry record not found")
    new = '''  LOC-PARVARAN-JANNE-HOUSE:
    name: "Parvaran and Janne home / tulsi courtyard"
    env6l_id: LOC-011
    drive_audit_file_id: "1fvisjiZTciVLMrgJgWuTOn6FqbkPxJXD"
    drive_audit_status: PASS
    drive_audit_scope: "root ST00; interior continuity still separate"
    formal_visual_lock_status: "UNVERIFIED_IN_CURRENT_REFERENCE_REGISTRY"
    status: MISSING_APPROVED_ASSET
    path: null
    hold_separated_from: LOC-072
    note: "Operational Drive-audit reuse evidence does not promote P1 visual approval without accepted file + SHA256."'''
    return text.replace(old, new, 1)


def add_numeric_refs(text: str) -> str:
    doc = yaml.safe_load(text)
    bridge = doc.get("late_env6l_numeric_root_references") or {}
    missing = [(loc, name) for loc, name in NEW_NUMERIC_REFS.items() if loc not in bridge]
    if not missing:
        return text
    payload: list[str] = []
    for loc, name in missing:
        payload.extend([
            f"  {loc}:",
            f"    name: \"{name}\"",
            f"    canonical_env6l_root: {loc}",
            "    status: MISSING_APPROVED_ASSET",
            "    path: null",
            "    metadata_status: LOCKED",
            "    visual_status: METADATA_LOCKED_VISUAL_PENDING",
            "    visual_approval_implied: false",
            "    authority: production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml",
        ])
    return text.rstrip() + "\n" + "\n".join(payload) + "\n"


def main() -> None:
    for p in (AUDIT, MAPPING, DRIVE_AUDIT):
        if not p.is_file():
            raise SystemExit(f"Required authority missing: {p.relative_to(ROOT)}")

    reg_before_text = REGISTRY.read_text(encoding="utf-8")
    req_before_text = REQUIREMENTS.read_text(encoding="utf-8")
    bind_before_text = BINDINGS.read_text(encoding="utf-8")
    schema_before_text = SCHEMA.read_text(encoding="utf-8")

    reg_before = yaml.safe_load(reg_before_text)
    req_before = yaml.safe_load(req_before_text)
    bind_before = yaml.safe_load(bind_before_text)
    schema_before = yaml.safe_load(schema_before_text)

    reg_after_text = add_numeric_refs(enrich_loc011_semantic(reg_before_text))

    req_after_text = req_before_text
    req_after_text = set_batch_field(req_after_text, "B30", "locations", fmt(B30_REQUIRED))
    req_after_text = set_batch_field(req_after_text, "B33", "locations", fmt(B33_REQUIRED))

    bind_after_text = bind_before_text
    bind_after_text = set_batch_field(bind_after_text, "B30", "env6l_roots", fmt(B30_ROOTS))
    bind_after_text = set_batch_field(bind_after_text, "B30", "mobile_refs", fmt(B30_MOBILE))
    bind_after_text = set_batch_field(
        bind_after_text, "B30", "canonical_metadata_binding_status",
        "B30_B33_ZERO_CREDIT_ROUTING_AUDITED__VISUAL_APPROVAL_UNCHANGED",
    )
    bind_after_text = set_batch_field(
        bind_after_text, "B30", "remaining_location_work",
        '["LOC-068/069/070/071/080 visual masters", "LOC-070 Executive/News floors", "LOC-011 interior continuity", "Sarjanya HOLD root unresolved", "required late/XFORM states"]',
    )
    bind_after_text = set_batch_field(bind_after_text, "B33", "env6l_roots", fmt(B33_ROOTS))
    bind_after_text = set_batch_field(
        bind_after_text, "B33", "canonical_metadata_binding_status",
        "B30_B33_ZERO_CREDIT_ROUTING_AUDITED__VISUAL_APPROVAL_UNCHANGED",
    )
    bind_after_text = set_batch_field(
        bind_after_text, "B33", "remaining_location_work",
        '["LOC-003 P4 dismantling/reform states", "LOC-070 XFORM state", "LOC-072 later-home interior", "LOC-074 armoury/drug-room nested controls", "LOC-080..LOC-087 visual masters", "LOC-087 SC099 case-review nested identity"]',
    )

    schema_after_text = schema_before_text
    schema_after_text = set_batch_field(schema_after_text, "B30", "env6l_roots", fmt(B30_ROOTS))
    schema_after_text = set_batch_field(schema_after_text, "B30", "mobile_refs", fmt(B30_MOBILE))
    schema_after_text = set_batch_field(
        schema_after_text, "B30", "p1_location_status",
        "ROUTING_AUDITED__EXACT_LATE_ROOTS_BOUND__VISUAL_AND_HELD_BEAT_GAPS_REMAIN",
    )
    schema_after_text = set_batch_field(schema_after_text, "B30", "required_location_refs", fmt(B30_REQUIRED))
    schema_after_text = set_batch_field(schema_after_text, "B33", "env6l_roots", fmt(B33_ROOTS))
    schema_after_text = set_batch_field(
        schema_after_text, "B33", "p1_location_status",
        "ROUTING_AUDITED__EXACT_LATE_ROOTS_BOUND__VISUAL_AND_STATE_GAPS_REMAIN",
    )
    schema_after_text = set_batch_field(schema_after_text, "B33", "required_location_refs", fmt(B33_REQUIRED))

    reg_after = yaml.safe_load(reg_after_text)
    req_after = yaml.safe_load(req_after_text)
    bind_after = yaml.safe_load(bind_after_text)
    schema_after = yaml.safe_load(schema_after_text)

    # Existing APPROVED status set must not change.
    if approved_snapshot(reg_before) != approved_snapshot(reg_after):
        raise SystemExit("Existing APPROVED registry status set changed — forbidden")

    # Numeric bridge must be fail-closed.
    bridge = reg_after.get("late_env6l_numeric_root_references") or {}
    for loc, name in NEW_NUMERIC_REFS.items():
        rec = bridge.get(loc)
        if not isinstance(rec, dict):
            raise SystemExit(f"Missing numeric registry bridge: {loc}")
        if rec.get("name") != name or rec.get("canonical_env6l_root") != loc:
            raise SystemExit(f"Identity drift: {loc}")
        if rec.get("status") != "MISSING_APPROVED_ASSET" or rec.get("path") is not None:
            raise SystemExit(f"Visual approval promotion detected: {loc}")
        if rec.get("visual_approval_implied") is not False:
            raise SystemExit(f"Visual approval implication detected: {loc}")

    # LOC-011 vs LOC-072 HOLD separation.
    loc011 = reg_after["locations"]["LOC-PARVARAN-JANNE-HOUSE"]
    if loc011.get("env6l_id") != "LOC-011" or loc011.get("hold_separated_from") != "LOC-072":
        raise SystemExit("LOC-011/LOC-072 HOLD guard missing")
    if loc011.get("status") != "MISSING_APPROVED_ASSET":
        raise SystemExit("LOC-011 semantic visual status promoted — forbidden")

    # Exact routing and requirements.
    if req_after["batches"]["B30"]["locations"] != B30_REQUIRED:
        raise SystemExit("B30 requirements mismatch")
    if req_after["batches"]["B33"]["locations"] != B33_REQUIRED:
        raise SystemExit("B33 requirements mismatch")
    if bind_after["location_bindings"]["B30"]["env6l_roots"] != B30_ROOTS:
        raise SystemExit("B30 root mismatch")
    if bind_after["location_bindings"]["B30"]["mobile_refs"] != B30_MOBILE:
        raise SystemExit("B30 mobile mismatch")
    if bind_after["location_bindings"]["B33"]["env6l_roots"] != B33_ROOTS:
        raise SystemExit("B33 root mismatch")
    if "LOC-011" in bind_after["location_bindings"]["B33"]["env6l_roots"]:
        raise SystemExit("B33 still aliases LOC-011 — forbidden")
    if "LOC-073" in bind_after["location_bindings"]["B33"]["env6l_roots"]:
        raise SystemExit("B33 incorrectly selected LOC-073 — forbidden")
    if "LOC-072" in bind_after["location_bindings"]["B30"]["env6l_roots"]:
        raise SystemExit("B30 incorrectly aliases later Janne Home — forbidden")
    if schema_after["batches"]["B30"]["required_location_refs"] != B30_REQUIRED:
        raise SystemExit("B30 schema requirement mismatch")
    if schema_after["batches"]["B33"]["required_location_refs"] != B33_REQUIRED:
        raise SystemExit("B33 schema requirement mismatch")

    # approved_root values may not change.
    for batch in ("B30", "B33"):
        if bind_after["location_bindings"][batch].get("approved_root") != bind_before["location_bindings"][batch].get("approved_root"):
            raise SystemExit(f"{batch}: approved_root changed — forbidden")

    # Unrelated held/adjacent batches must remain semantically identical.
    for batch in ("B29", "B31", "B32", "B34"):
        if req_after["batches"][batch] != req_before["batches"][batch]:
            raise SystemExit(f"Unexpected requirement mutation: {batch}")
        if bind_after["location_bindings"][batch] != bind_before["location_bindings"][batch]:
            raise SystemExit(f"Unexpected binding mutation: {batch}")
        if schema_after["batches"][batch] != schema_before["batches"][batch]:
            raise SystemExit(f"Unexpected schema mutation: {batch}")

    REGISTRY.write_text(reg_after_text, encoding="utf-8")
    REQUIREMENTS.write_text(req_after_text, encoding="utf-8")
    BINDINGS.write_text(bind_after_text, encoding="utf-8")
    SCHEMA.write_text(schema_after_text, encoding="utf-8")

    print("B30_B33_ZERO_CREDIT_LATE_LOCATION_ROUTING_APPLIED")
    print("B30 roots unchanged; exact required refs exposed")
    print("B33 LOC-011 -> LOC-072; LOC-074 selected; LOC-070/085 added")
    print("LOC-073 excluded from B33")
    print("Numeric visual refs added fail-closed: %d" % len(NEW_NUMERIC_REFS))
    print("approved_root changes: 0")
    print("APPROVED status changes: 0")
    print("media generation/replacement: 0")
    print("HeyGen/API execution: 0")


if __name__ == "__main__":
    main()
