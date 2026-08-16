#!/usr/bin/env python3
"""Apply frozen ENV-6L metadata bindings to B27-B34 control files.

CONTROL-ONLY / ZERO MEDIA / ZERO HEYGEN.

This script intentionally:
- updates only P1_BATCH_REFERENCE_BINDINGS.yaml and HEYGEN_BATCH_MEDIA_INPUT_SCHEMA.yaml;
- records canonical LOC-062..LOC-087 root/mobile identities proven by the late-batch crosswalk;
- does NOT change approved_root;
- does NOT remove or invent pending semantic references;
- does NOT change APPROVED reference/media status;
- does NOT generate, upload, replace, or submit media.
"""
from __future__ import annotations

import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
BINDINGS = ROOT / "production/batches/P1_BATCH_REFERENCE_BINDINGS.yaml"
SCHEMA = ROOT / "production/heygen/HEYGEN_BATCH_MEDIA_INPUT_SCHEMA.yaml"
MAPPING = ROOT / "production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml"
CROSSWALK = ROOT / "production/locations/P1_LATE_BATCH_ENV6L_BINDING_CROSSWALK.yaml"

EXPECTED_ROOTS = {
    "B27": ["LOC-063"],
    "B28": ["LOC-064", "LOC-066"],
    "B29": ["LOC-003", "LOC-067", "LOC-068"],
    "B30": ["LOC-002", "LOC-003", "LOC-011", "LOC-068", "LOC-069", "LOC-070", "LOC-071", "LOC-080"],
    "B31": ["LOC-075"],
    "B32": ["LOC-078", "LOC-079"],
    "B33": ["LOC-003", "LOC-011", "LOC-080", "LOC-081", "LOC-082", "LOC-083", "LOC-084", "LOC-086", "LOC-087"],
    "B34": ["LOC-087"],
}
EXPECTED_MOBILE = {
    "B27": ["LOC-062"],
    "B28": ["LOC-065"],
    "B30": ["LOC-076", "LOC-077"],
    "B31": ["LOC-076", "LOC-077"],
}
SCHEMA_STATUS = {
    "B27": "CANONICAL_ROOT_METADATA_BOUND__VISUAL_AND_SEMANTIC_GAPS_REMAIN",
    "B28": "PARTIAL__LATE_ROOT_METADATA_BOUND__VISUAL_AND_SEMANTIC_GAPS_REMAIN",
    "B29": "PARTIAL__LATE_ROOT_METADATA_BOUND__VISUAL_AND_SEMANTIC_GAPS_REMAIN",
    "B30": "PARTIAL__LATE_ROOT_METADATA_BOUND__VISUAL_AND_HOLD_REVIEW_GAPS_REMAIN",
    "B31": "CANONICAL_ROOT_METADATA_BOUND__VISUAL_AND_STALE_SEMANTIC_GAPS_REMAIN",
    "B32": "CANONICAL_ROOT_METADATA_BOUND__VISUAL_AND_STALE_SEMANTIC_GAPS_REMAIN",
    "B33": "PARTIAL__LATE_ROOT_METADATA_BOUND__VISUAL_AND_STATE_GAPS_REMAIN",
    "B34": "CANONICAL_ROOT_METADATA_BOUND__VISUAL_AND_NESTED_GAPS_REMAIN",
}


def fmt_list(items: list[str]) -> str:
    return "[" + ", ".join(items) + "]"


def batch_span(text: str, batch_id: str) -> tuple[int, int]:
    start_match = re.search(rf"(?m)^  {re.escape(batch_id)}:\s*$", text)
    if not start_match:
        raise RuntimeError(f"Missing {batch_id}")
    start = start_match.start()
    next_match = re.search(r"(?m)^  B\d{2}:\s*$", text[start_match.end():])
    end = start_match.end() + next_match.start() if next_match else len(text)
    return start, end


def replace_or_insert_field(block: str, field: str, value: str, after_field: str) -> str:
    pat = rf"(?m)^    {re.escape(field)}:.*$"
    replacement = f"    {field}: {value}"
    if re.search(pat, block):
        return re.sub(pat, replacement, block, count=1)
    anchor = rf"(?m)^(    {re.escape(after_field)}:.*)$"
    if not re.search(anchor, block):
        raise RuntimeError(f"Cannot insert {field}; missing anchor {after_field}")
    return re.sub(anchor, rf"\1\n{replacement}", block, count=1)


def update_batch(text: str, batch_id: str, *, is_schema: bool) -> str:
    start, end = batch_span(text, batch_id)
    block = text[start:end]
    block = replace_or_insert_field(block, "env6l_roots", fmt_list(EXPECTED_ROOTS[batch_id]), "scenes")
    if batch_id in EXPECTED_MOBILE:
        block = replace_or_insert_field(block, "mobile_refs", fmt_list(EXPECTED_MOBILE[batch_id]), "env6l_roots")
    if is_schema:
        block = replace_or_insert_field(block, "p1_location_status", SCHEMA_STATUS[batch_id], "env6l_roots")
    else:
        block = replace_or_insert_field(
            block,
            "canonical_metadata_binding_status",
            "ENV6L_LOC062_087_CROSSWALK_APPLIED__VISUAL_APPROVAL_UNCHANGED",
            "approved_root",
        )
    return text[:start] + block + text[end:]


def insert_once_after(text: str, anchor_line: str, new_lines: list[str]) -> str:
    if all(line in text for line in new_lines):
        return text
    anchor = anchor_line + "\n"
    if anchor not in text:
        raise RuntimeError(f"Missing anchor: {anchor_line}")
    payload = "".join(line + "\n" for line in new_lines if line not in text)
    return text.replace(anchor, anchor + payload, 1)


def main() -> None:
    if not MAPPING.is_file() or not CROSSWALK.is_file():
        raise SystemExit("Frozen mapping/crosswalk missing; refuse to mutate controls")

    bindings_before_text = BINDINGS.read_text(encoding="utf-8")
    schema_before_text = SCHEMA.read_text(encoding="utf-8")
    bindings_before = yaml.safe_load(bindings_before_text)
    schema_before = yaml.safe_load(schema_before_text)

    bindings_after_text = bindings_before_text
    schema_after_text = schema_before_text
    for batch_id in EXPECTED_ROOTS:
        bindings_after_text = update_batch(bindings_after_text, batch_id, is_schema=False)
        schema_after_text = update_batch(schema_after_text, batch_id, is_schema=True)

    bindings_after_text = insert_once_after(
        bindings_after_text,
        '  location_queue: "production/locations/LOCATION_GENERATION_QUEUE.yaml"',
        [
            '  late_env6l_mapping: "production/locations/ENV6L_LOC062_087_CANONICAL_MAPPING.yaml"',
            '  late_batch_crosswalk: "production/locations/P1_LATE_BATCH_ENV6L_BINDING_CROSSWALK.yaml"',
        ],
    )
    bindings_after_text = insert_once_after(
        bindings_after_text,
        '  root_masters_remaining: 26',
        [
            '  late_env6l_id_name_mapping_imported: true',
            '  late_env6l_mapping_scope: "LOC-062..LOC-087"',
            '  late_env6l_visual_coverage_increment_from_metadata_binding: 0',
            '  p1_l1_metadata_mapping_status: COMPLETE__VISUALS_STILL_PENDING',
        ],
    )

    # Parse and assert before writing.
    bindings_after = yaml.safe_load(bindings_after_text)
    schema_after = yaml.safe_load(schema_after_text)
    for batch_id, roots in EXPECTED_ROOTS.items():
        b_before = bindings_before["location_bindings"][batch_id]
        b_after = bindings_after["location_bindings"][batch_id]
        s_before = schema_before["batches"][batch_id]
        s_after = schema_after["batches"][batch_id]
        if b_after.get("env6l_roots") != roots or s_after.get("env6l_roots") != roots:
            raise SystemExit(f"{batch_id}: root mismatch after update")
        if b_after.get("approved_root") != b_before.get("approved_root"):
            raise SystemExit(f"{batch_id}: approved_root changed — forbidden")
        if b_after.get("pending_named_location_refs") != b_before.get("pending_named_location_refs"):
            raise SystemExit(f"{batch_id}: binding pending refs changed — forbidden in this step")
        if s_after.get("pending_named_location_refs") != s_before.get("pending_named_location_refs"):
            raise SystemExit(f"{batch_id}: schema pending refs changed — forbidden in this step")
        expected_mobile = EXPECTED_MOBILE.get(batch_id)
        if expected_mobile is not None:
            if b_after.get("mobile_refs") != expected_mobile or s_after.get("mobile_refs") != expected_mobile:
                raise SystemExit(f"{batch_id}: mobile metadata mismatch")

    # Scope safety: only these two control files are written.
    BINDINGS.write_text(bindings_after_text, encoding="utf-8")
    SCHEMA.write_text(schema_after_text, encoding="utf-8")
    print("LATE_ENV6L_METADATA_BINDINGS_APPLIED")
    print("Batches: B27-B34")
    print("approved_root changes: 0")
    print("pending semantic reference changes: 0")
    print("visual approval changes: 0")
    print("media generation/replacement: 0")
    print("HeyGen calls/submissions: 0")


if __name__ == "__main__":
    main()
