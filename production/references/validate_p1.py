"""Validate ANAADHI P1 visual-reference coverage.

Run from repository root:
    python production/references/validate_p1.py

This script does NOT approve assets. It checks that:
1. B01-B34 exist.
2. SC001-SC100 are covered exactly once.
3. Every reference ID used by a batch exists in REFERENCE_REGISTRY.yaml.
4. It reports which required assets are still not APPROVED.
"""

from pathlib import Path
import sys

try:
    import yaml
except ImportError:
    raise SystemExit("PyYAML is required: pip install pyyaml")

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "production" / "references" / "REFERENCE_REGISTRY.yaml"
REQUIREMENTS_PATH = ROOT / "production" / "references" / "BATCH_REFERENCE_REQUIREMENTS.yaml"

registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
requirements = yaml.safe_load(REQUIREMENTS_PATH.read_text(encoding="utf-8"))

batches = requirements["batches"]
expected_batches = [f"B{i:02d}" for i in range(1, 35)]
assert list(batches.keys()) == expected_batches, (
    "Batch IDs must be exactly B01-B34 in order. "
    f"Found: {list(batches.keys())}"
)

scene_hits = {}
for batch_id, data in batches.items():
    for scene in data["scenes"]:
        scene_hits.setdefault(scene, []).append(batch_id)

missing_scenes = [s for s in range(1, 101) if s not in scene_hits]
duplicate_scenes = {s: ids for s, ids in scene_hits.items() if len(ids) != 1}
extra_scenes = sorted(s for s in scene_hits if not 1 <= s <= 100)

assert not missing_scenes, f"Missing scenes: {missing_scenes}"
assert not duplicate_scenes, f"Duplicate scene coverage: {duplicate_scenes}"
assert not extra_scenes, f"Out-of-range scenes: {extra_scenes}"

# Flatten all registered reference-ID namespaces.
registered = {}
for namespace, values in registry.items():
    if isinstance(values, dict):
        for ref_id, record in values.items():
            if isinstance(ref_id, str) and (
                ref_id.startswith("CHR-")
                or ref_id.startswith("AGE-")
                or ref_id.startswith("HR-")
                or ref_id.startswith("CST-")
                or ref_id.startswith("INJ-")
                or ref_id.startswith("LOC-")
                or ref_id.startswith("PRP-")
                or ref_id.startswith("VEH-")
                or ref_id.startswith("TEC-")
                or ref_id.startswith("ENV-")
                or ref_id.startswith("GF-")
            ):
                registered[ref_id] = record

used = []
for batch_id, data in batches.items():
    for field in ("anaadhi", "locations", "props"):
        for ref_id in data.get(field, []):
            used.append((batch_id, field, ref_id))

undefined = [(b, f, r) for b, f, r in used if r not in registered]
assert not undefined, "Undefined reference IDs:\n" + "\n".join(map(str, undefined))

pending = []
for batch_id, field, ref_id in used:
    record = registered[ref_id]
    if record.get("status") != "APPROVED" or not record.get("path"):
        pending.append((batch_id, ref_id, record.get("status"), record.get("path")))

print("P1 STRUCTURE VALID")
print("Batches: 34")
print("Scenes: 001-100 exactly once")
print("Reference IDs used:", len({r for _, _, r in used}))
print("Pending required references:", len(pending))

if pending:
    print("\nP1 is NOT visually locked yet. Missing/unapproved references:")
    seen = set()
    for batch_id, ref_id, status, path in pending:
        key = ref_id
        if key in seen:
            continue
        seen.add(key)
        print(f"- {ref_id}: status={status}, path={path}")
    sys.exit(2)

print("\nALL USED P1 REFERENCES APPROVED — P1_LOCKED")
