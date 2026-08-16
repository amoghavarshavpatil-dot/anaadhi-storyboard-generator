#!/usr/bin/env python3
"""Correct a clean subset of late P1 semantic location requirements.

ZERO MEDIA / ZERO HEYGEN / ZERO APPROVAL PROMOTION.

Targets only B27, B28, B31, B32 and B34, using the exact frozen ENV-6L roots
certified in P1_LATE_SEMANTIC_REQUIREMENT_AUDIT.yaml.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "production/references/REFERENCE_REGISTRY.yaml"
REQUIREMENTS = ROOT / "production/references/BATCH_REFERENCE_REQUIREMENTS.yaml"
BINDINGS = ROOT / "production/batches/P1_BATCH_REFERENCE_BINDINGS.yaml"
SCHEMA = ROOT / "production/heygen/HEYGEN_BATCH_MEDIA_INPUT_SCHEMA.yaml"
AUDIT = ROOT / "production/locations/P1_LATE_SEMANTIC_REQUIREMENT_AUDIT.yaml"
MAPPING = ROOT / "production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml"

TARGETS = {
    "B27": ["LOC-063"],
    "B28": ["LOC-064", "LOC-066"],
    "B31": ["LOC-075"],
    "B32": ["LOC-078", "LOC-079"],
    "B34": ["LOC-087"],
}
NAMES = {
    "LOC-063": "Independent Ayurvedic Surgery Centre",
    "LOC-064": "Forest Transfer Road",
    "LOC-066": "Forest Communications Tower",
    "LOC-075": "Joint Kendhalaa–Adraka Border Checkpoint",
    "LOC-078": "Independent Judicial Complex",
    "LOC-079": "Independent District Court",
    "LOC-087": "Independent Judicial Medical Centre",
}
HELD = ["B29", "B30", "B33"]


def fmt(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"


def span(text: str, batch_id: str) -> tuple[int, int]:
    m = re.search(rf"(?m)^  {re.escape(batch_id)}:\s*$", text)
    if not m:
        raise RuntimeError(f"Missing batch {batch_id}")
    n = re.search(r"(?m)^  B\d{2}:\s*$", text[m.end():])
    return m.start(), (m.end() + n.start()) if n else len(text)


def set_field_in_batch(text: str, batch_id: str, field: str, value: str) -> str:
    a, b = span(text, batch_id)
    block = text[a:b]
    pat = rf"(?m)^    {re.escape(field)}:.*$"
    if not re.search(pat, block):
        raise RuntimeError(f"{batch_id}: missing field {field}")
    block = re.sub(pat, f"    {field}: {value}", block, count=1)
    return text[:a] + block + text[b:]


def registry_append(text: str) -> str:
    marker = "# P1-LATE-ENV6L-NUMERIC-ROOT-REGISTRY-BRIDGE"
    if marker in text:
        return text
    payload = ["", marker, "late_env6l_numeric_root_references:"]
    for loc_id, name in NAMES.items():
        payload.extend([
            f"  {loc_id}:",
            f"    name: \"{name}\"",
            f"    canonical_env6l_root: {loc_id}",
            "    status: MISSING_APPROVED_ASSET",
            "    path: null",
            "    metadata_status: LOCKED",
            "    visual_status: METADATA_LOCKED_VISUAL_PENDING",
            "    visual_approval_implied: false",
            "    authority: production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml",
        ])
    return text.rstrip() + "\n" + "\n".join(payload) + "\n"


def approved_status_snapshot(value: Any, path: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(value, dict):
        for key, child in value.items():
            p = f"{path}.{key}" if path else str(key)
            if key == "status" and isinstance(child, str) and child.upper() == "APPROVED":
                out[path] = child
            out.update(approved_status_snapshot(child, p))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            out.update(approved_status_snapshot(child, f"{path}[{i}]"))
    return out


def main() -> None:
    if not AUDIT.is_file() or not MAPPING.is_file():
        raise SystemExit("Required frozen audit/mapping missing")

    reg_before_text = REGISTRY.read_text(encoding="utf-8")
    req_before_text = REQUIREMENTS.read_text(encoding="utf-8")
    bind_before_text = BINDINGS.read_text(encoding="utf-8")
    schema_before_text = SCHEMA.read_text(encoding="utf-8")

    reg_before = yaml.safe_load(reg_before_text)
    req_before = yaml.safe_load(req_before_text)
    bind_before = yaml.safe_load(bind_before_text)
    schema_before = yaml.safe_load(schema_before_text)

    reg_after_text = registry_append(reg_before_text)
    req_after_text = req_before_text
    bind_after_text = bind_before_text
    schema_after_text = schema_before_text

    for batch_id, locations in TARGETS.items():
        req_after_text = set_field_in_batch(req_after_text, batch_id, "locations", fmt(locations))
        bind_after_text = set_field_in_batch(bind_after_text, batch_id, "pending_named_location_refs", fmt(locations))
        schema_after_text = set_field_in_batch(schema_after_text, batch_id, "pending_named_location_refs", fmt(locations))
        schema_after_text = set_field_in_batch(schema_after_text, batch_id, "required_location_refs", fmt(locations))

    reg_after = yaml.safe_load(reg_after_text)
    req_after = yaml.safe_load(req_after_text)
    bind_after = yaml.safe_load(bind_after_text)
    schema_after = yaml.safe_load(schema_after_text)

    # New numeric roots must be defined but visually unapproved.
    bridge = reg_after.get("late_env6l_numeric_root_references") or {}
    for loc_id, name in NAMES.items():
        rec = bridge.get(loc_id)
        if not isinstance(rec, dict):
            raise SystemExit(f"Registry bridge missing {loc_id}")
        if rec.get("name") != name or rec.get("canonical_env6l_root") != loc_id:
            raise SystemExit(f"Registry identity mismatch for {loc_id}")
        if rec.get("status") != "MISSING_APPROVED_ASSET" or rec.get("path") is not None:
            raise SystemExit(f"{loc_id}: forbidden visual approval promotion")

    # Existing APPROVED statuses must remain byte-semantically untouched.
    if approved_status_snapshot(reg_before) != approved_status_snapshot(reg_after):
        raise SystemExit("Existing APPROVED registry status set changed — forbidden")

    for batch_id, locations in TARGETS.items():
        if req_after["batches"][batch_id]["locations"] != locations:
            raise SystemExit(f"{batch_id}: requirements correction failed")
        if schema_after["batches"][batch_id]["required_location_refs"] != locations:
            raise SystemExit(f"{batch_id}: schema required refs correction failed")
        if schema_after["batches"][batch_id]["pending_named_location_refs"] != locations:
            raise SystemExit(f"{batch_id}: schema pending correction failed")
        if bind_after["location_bindings"][batch_id]["pending_named_location_refs"] != locations:
            raise SystemExit(f"{batch_id}: binding pending correction failed")
        if bind_after["location_bindings"][batch_id].get("approved_root") != bind_before["location_bindings"][batch_id].get("approved_root"):
            raise SystemExit(f"{batch_id}: approved_root changed — forbidden")

    # Held complex batches must remain unchanged in semantic requirements/pending refs.
    for batch_id in HELD:
        if req_after["batches"][batch_id]["locations"] != req_before["batches"][batch_id]["locations"]:
            raise SystemExit(f"{batch_id}: held requirements changed — forbidden")
        if schema_after["batches"][batch_id].get("required_location_refs") != schema_before["batches"][batch_id].get("required_location_refs"):
            raise SystemExit(f"{batch_id}: held schema refs changed — forbidden")
        if bind_after["location_bindings"][batch_id].get("pending_named_location_refs") != bind_before["location_bindings"][batch_id].get("pending_named_location_refs"):
            raise SystemExit(f"{batch_id}: held binding pending refs changed — forbidden")

    REGISTRY.write_text(reg_after_text, encoding="utf-8")
    REQUIREMENTS.write_text(req_after_text, encoding="utf-8")
    BINDINGS.write_text(bind_after_text, encoding="utf-8")
    SCHEMA.write_text(schema_after_text, encoding="utf-8")

    print("LATE_SEMANTIC_REQUIREMENT_CORRECTIONS_APPLIED")
    print("Batches: B27 B28 B31 B32 B34")
    print("New registry refs: 7; all MISSING_APPROVED_ASSET/path=null")
    print("Existing APPROVED status changes: 0")
    print("approved_root changes: 0")
    print("Held B29/B30/B33 semantic changes: 0")
    print("Media generation/replacement: 0")
    print("HeyGen calls/submissions: 0")


if __name__ == "__main__":
    main()
