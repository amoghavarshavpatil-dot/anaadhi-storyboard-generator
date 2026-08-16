#!/usr/bin/env python3
"""ANAADHI HeyGen batch-media validator.

Validation only. This program is deliberately read-only: it does not generate media,
upload assets, call HeyGen, create payload jobs, or submit renders.

Run from repository root:
    python production/heygen/validate_heygen_batch_media.py
    python production/heygen/validate_heygen_batch_media.py --batch B01
    python production/heygen/validate_heygen_batch_media.py --json

Exit codes:
    0  all selected batches pass every hard gate
    2  one or more hard blockers were found
    3  validator configuration/source loading failed
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency failure is explicit
    raise SystemExit("PyYAML is required: pip install pyyaml") from exc


ROOT = Path(__file__).resolve().parents[2]

SCHEMA_PATH = ROOT / "production" / "heygen" / "HEYGEN_BATCH_MEDIA_INPUT_SCHEMA.yaml"
REQUIREMENTS_PATH = ROOT / "production" / "references" / "BATCH_REFERENCE_REQUIREMENTS.yaml"
BINDINGS_PATH = ROOT / "production" / "batches" / "P1_BATCH_REFERENCE_BINDINGS.yaml"
REGISTRY_PATH = ROOT / "production" / "references" / "REFERENCE_REGISTRY.yaml"
CONTRACT_PATH = ROOT / "production" / "heygen" / "HEYGEN_API_ACCEPTANCE_CONTRACT.yaml"
P0_PATH = ROOT / "production" / "batches" / "ANAADHI_BATCH_FOUNDATION.py"
AVATAR_INDEX_PATH = ROOT / "production" / "heygen" / "avatars" / "AVATAR_BATCH_INDEX.yaml"

EXPECTED_BATCHES = [f"B{i:02d}" for i in range(1, 35)]
EXPECTED_SCENES = list(range(1, 101))
REFERENCE_PREFIXES = (
    "CHR-",
    "AGE-",
    "HR-",
    "CST-",
    "INJ-",
    "LOC-",
    "PRP-",
    "VEH-",
    "TEC-",
    "ENV-",
    "GF-",
    "VAR-",
)
CONSENT_OK = {"APPROVED", "COMPLETE", "COMPLETED", "VERIFIED", "NOT_REQUIRED"}

# Payload validation is intentionally fail-closed. These are the fields whose forms
# are explicitly represented by HEYGEN_API_ACCEPTANCE_CONTRACT.yaml in this project.
# Unknown endpoint families or unknown fields are blockers until the acceptance
# contract is deliberately expanded.
PAYLOAD_ALLOWLISTS: dict[str, set[str]] = {
    "avatar_video": {
        "avatar_id",
        "script",
        "audioUrl",
        "audioAssetId",
        "output_format",
        "aspect_ratio",
        "resolution",
        "motion_prompt",
        "captions",
        "watermark",
        "background",
    },
    "create_video_from_avatar_or_image": {
        "avatar_id",
        "image",
        "script",
        "audioUrl",
        "audioAssetId",
        "output_format",
        "aspect_ratio",
        "resolution",
        "motion_prompt",
        "captions",
        "watermark",
        "background",
    },
    "create_video_from_image": {
        "image",
        "script",
        "audioUrl",
        "audioAssetId",
        "output_format",
        "aspect_ratio",
        "resolution",
        "motion_prompt",
        "captions",
        "watermark",
    },
    "HeyGen_lipsync": {
        "video",
        "audio",
        "mode",
        "enable_caption",
        "enable_watermark",
        "enable_speech_enhancement",
        "disable_music_track",
        "fps_mode",
        "keep_the_same_format",
        "enable_dynamic_duration",
    },
    "lipsync": {
        "video",
        "audio",
        "mode",
        "enable_caption",
        "enable_watermark",
        "enable_speech_enhancement",
        "disable_music_track",
        "fps_mode",
        "keep_the_same_format",
        "enable_dynamic_duration",
    },
}
FORBIDDEN_PAYLOAD_FIELDS = {
    "prop",
    "props",
    "prop_reference_array",
    "environment_reference_array",
    "video_background",
}


@dataclass(frozen=True)
class Blocker:
    batch_id: str
    category: str
    code: str
    message: str


class ValidationConfigError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationConfigError(f"Required YAML missing: {path.relative_to(ROOT)}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValidationConfigError(f"YAML root must be a mapping: {path.relative_to(ROOT)}")
    return data


def get_path(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def canonical_string_list(value: Any) -> list[str]:
    return [str(item) for item in as_list(value)]


def exact_batch_map(source: dict[str, Any], key: str, source_name: str) -> dict[str, Any]:
    batches = source.get(key)
    if not isinstance(batches, dict):
        raise ValidationConfigError(f"{source_name}.{key} must be a mapping")
    return batches


def extract_p0_batches(path: Path) -> dict[str, dict[str, Any]]:
    """Read the literal batch(...) calls from P0 without importing/executing the file."""
    if not path.is_file():
        raise ValidationConfigError(f"P0 foundation missing: {path.relative_to(ROOT)}")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    target: ast.AST | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(t, ast.Name) and t.id == "BATCHES" for t in node.targets):
                target = node.value
                break
    if not isinstance(target, ast.List):
        raise ValidationConfigError("P0 BATCHES must be a literal list of batch(...) calls")

    result: dict[str, dict[str, Any]] = {}
    arg_names = ["id", "title", "scenes", "epoch", "locations", "character_state", "characters", "props"]
    for item in target.elts:
        if not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name) or item.func.id != "batch":
            raise ValidationConfigError("P0 BATCHES contains a non-batch(...) entry")
        if len(item.args) != len(arg_names):
            raise ValidationConfigError("P0 batch(...) call shape changed; validator requires 8 literal args")
        try:
            values = [ast.literal_eval(arg) for arg in item.args]
        except (ValueError, TypeError) as exc:
            raise ValidationConfigError("P0 batch(...) args must remain literal/read-only parseable") from exc
        record = dict(zip(arg_names, values))
        result[str(record["id"])] = record
    return result


def flatten_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Collect all reference-ID keyed records regardless of registry namespace depth."""
    found: dict[str, dict[str, Any]] = {}

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if isinstance(key, str) and key.startswith(REFERENCE_PREFIXES) and isinstance(child, dict):
                    found[key] = child
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(registry)
    return found


def status_is_approved(record: dict[str, Any]) -> bool:
    return str(record.get("status", "")).upper() == "APPROVED" and bool(record.get("path"))


def classify_reference(ref_id: str) -> str:
    if ref_id.startswith("LOC-"):
        return "location"
    if ref_id.startswith(("AGE-", "HR-", "CST-", "INJ-", "CHR-", "VAR-")):
        return "character-state"
    if ref_id.startswith("PRP-"):
        return "prop"
    if ref_id.startswith("VEH-"):
        return "vehicle"
    if ref_id.startswith("TEC-"):
        return "technology"
    if ref_id.startswith(("ENV-", "GF-")):
        return "environment"
    return "reference"


def split_named_characters(raw: Any) -> list[str]:
    if not isinstance(raw, str):
        return []
    return [part.strip() for part in raw.split(";") if part.strip()]


def load_avatar_manifest_for_batch(
    batch_id: str,
    avatar_index: dict[str, Any] | None,
) -> tuple[Path | None, dict[str, Any] | None]:
    if not avatar_index:
        return None, None
    entry = get_path(avatar_index, "batch_order", batch_id)
    if not isinstance(entry, dict):
        return None, None
    manifest = entry.get("manifest")
    if not manifest:
        return None, None
    path = ROOT / str(manifest)
    if not path.is_file():
        return path, None
    return path, load_yaml(path)


def collect_consent_values(value: Any) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_l = str(key).lower()
            if "consent" in key_l and not isinstance(child, (dict, list)):
                values.append("" if child is None else str(child).upper())
            collect = collect_consent_values(child)
            values.extend(collect)
    elif isinstance(value, list):
        for child in value:
            values.extend(collect_consent_values(child))
    return values


def validate_payload_node(
    batch_id: str,
    endpoint_family: Any,
    payload: Any,
    blockers: list[Blocker],
    location: str,
) -> None:
    if not isinstance(payload, dict):
        blockers.append(Blocker(batch_id, "api-field", "PAYLOAD_NOT_MAPPING", f"{location}: heygen_payload must be a mapping"))
        return

    endpoint = str(endpoint_family or "")
    allowlist = PAYLOAD_ALLOWLISTS.get(endpoint)
    if allowlist is None:
        blockers.append(
            Blocker(
                batch_id,
                "api-field",
                "UNVERIFIED_ENDPOINT_FAMILY",
                f"{location}: endpoint family {endpoint!r} has no locked field allowlist; fail closed",
            )
        )
        return

    keys = {str(k) for k in payload}
    forbidden = sorted(keys & FORBIDDEN_PAYLOAD_FIELDS)
    if forbidden:
        blockers.append(
            Blocker(
                batch_id,
                "api-field",
                "FORBIDDEN_HEYGEN_FIELD",
                f"{location}: unsupported/forbidden HeyGen field(s): {', '.join(forbidden)}",
            )
        )
    unknown = sorted(keys - allowlist)
    if unknown:
        blockers.append(
            Blocker(
                batch_id,
                "api-field",
                "UNSUPPORTED_HEYGEN_FIELD",
                f"{location}: field(s) not locked by HEYGEN_API_ACCEPTANCE_CONTRACT: {', '.join(unknown)}",
            )
        )

    # Contract-level mutual exclusivity checks.
    if "audioUrl" in payload and "audioAssetId" in payload:
        blockers.append(Blocker(batch_id, "api-field", "AUDIO_INPUT_NOT_EXCLUSIVE", f"{location}: audioUrl and audioAssetId cannot both be supplied"))
    if "script" in payload and ("audioUrl" in payload or "audioAssetId" in payload):
        blockers.append(Blocker(batch_id, "api-field", "SPEAKING_INPUT_NOT_EXCLUSIVE", f"{location}: exactly one of script/audioUrl/audioAssetId is allowed"))
    if isinstance(payload.get("script"), str) and len(payload["script"]) > 4999:
        blockers.append(Blocker(batch_id, "api-field", "TEXT_TOO_LONG", f"{location}: script exceeds 4999 Unicode characters"))

    def check_asset_form(name: str, asset: Any) -> None:
        if not isinstance(asset, dict):
            return
        pairs = [
            ("url", "asset_id"),
            ("url", "video_asset_id"),
        ]
        for left, right in pairs:
            if left in asset and right in asset:
                blockers.append(
                    Blocker(
                        batch_id,
                        "api-field",
                        "ASSET_INPUT_NOT_EXCLUSIVE",
                        f"{location}.{name}: {left} and {right} cannot both be supplied",
                    )
                )
        if "url" in asset and not str(asset["url"]).startswith("https://"):
            blockers.append(Blocker(batch_id, "api-field", "NON_HTTPS_MEDIA_URL", f"{location}.{name}: media URL must be public HTTPS"))

    for asset_key in ("image", "video", "audio", "background"):
        if asset_key in payload:
            check_asset_form(asset_key, payload[asset_key])


def scan_payloads(batch_id: str, value: Any, blockers: list[Blocker], path: str = "schema") -> None:
    if isinstance(value, dict):
        if "heygen_payload" in value:
            validate_payload_node(
                batch_id=batch_id,
                endpoint_family=value.get("heygen_endpoint_family"),
                payload=value.get("heygen_payload"),
                blockers=blockers,
                location=path,
            )
        for key, child in value.items():
            scan_payloads(batch_id, child, blockers, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_payloads(batch_id, child, blockers, f"{path}[{index}]")


def validate_global_safety(schema: dict[str, Any], contract: dict[str, Any]) -> list[Blocker]:
    blockers: list[Blocker] = []
    global_id = "GLOBAL"

    schema_status = str(schema.get("status", ""))
    if "NO_GENERATION" not in schema_status or "SUBMITTED" not in schema_status:
        blockers.append(Blocker(global_id, "safety", "SCHEMA_STATUS_NOT_READ_ONLY", f"Schema status must visibly lock no-generation/no-submission; found {schema_status!r}"))

    if get_path(contract, "job_payload_authoring_rule", "no_execution_by_default") is not True:
        blockers.append(Blocker(global_id, "safety", "EXECUTION_DEFAULT_NOT_LOCKED", "Acceptance contract must keep no_execution_by_default=true"))

    default_submission = get_path(schema, "batch_defaults", "heygen_submission_status")
    if default_submission != "NOT_SUBMITTED":
        blockers.append(Blocker(global_id, "safety", "SUBMISSION_DEFAULT_NOT_LOCKED", f"batch_defaults.heygen_submission_status must be NOT_SUBMITTED; found {default_submission!r}"))

    this_chat_forbidden = canonical_string_list(get_path(contract, "execution_ownership", "this_chat", "forbidden", default=[]))
    forbidden_blob = "\n".join(this_chat_forbidden).lower()
    for phrase, code in (
        ("generate new character", "CHARACTER_GENERATION_NOT_FORBIDDEN"),
        ("generate new location", "LOCATION_GENERATION_NOT_FORBIDDEN"),
        ("generate new prop", "PROP_GENERATION_NOT_FORBIDDEN"),
        ("submit paid heygen", "HEYGEN_SUBMISSION_NOT_FORBIDDEN"),
    ):
        if phrase not in forbidden_blob:
            blockers.append(Blocker(global_id, "safety", code, f"Acceptance contract must explicitly forbid: {phrase}"))

    # No literal secret may be embedded in either control file.
    for source_name, source in (("schema", schema), ("contract", contract)):
        text = json.dumps(source, ensure_ascii=False)
        if re.search(r"(?i)sk-[A-Za-z0-9_-]{12,}", text):
            blockers.append(Blocker(global_id, "security", "SECRET_EMBEDDED", f"Possible API secret embedded in {source_name}"))

    return blockers


def validate_schema_contract_semantics(schema: dict[str, Any], contract: dict[str, Any]) -> list[Blocker]:
    """Cross-check duplicated HeyGen media rules and fail on contract drift."""
    blockers: list[Blocker] = []
    global_id = "GLOBAL"

    schema_prop_slot = get_path(schema, "heygen_supported_media_forms", "props", "generic_direct_prop_field")
    contract_prop_slot = get_path(contract, "prop_vehicle_technology_contract", "direct_avatar_video_prop_slot_available")
    if schema_prop_slot is not False or contract_prop_slot is not False:
        blockers.append(
            Blocker(
                global_id,
                "api-field",
                "DIRECT_PROP_SLOT_CONTRACT_DRIFT",
                f"Direct generic prop slot must remain false in both schema and acceptance contract; schema={schema_prop_slot!r}, contract={contract_prop_slot!r}",
            )
        )

    if get_path(schema, "execution_ownership", "locations_and_props", "regenerate_in_this_chat") is not False:
        blockers.append(Blocker(global_id, "safety", "LOCATION_PROP_REGEN_ENABLED_HERE", "Schema must keep location/prop regeneration disabled in this chat"))
    if get_path(schema, "execution_ownership", "locations_and_props", "regenerate_in_work_page") is not False:
        blockers.append(Blocker(global_id, "safety", "LOCATION_PROP_REGEN_ENABLED_WORK_PAGE", "Schema must keep approved location/prop regeneration disabled on the work page"))

    # The acceptance contract is the later/harder lock. Any duplicated lipsync default
    # in the batch-media schema must agree before payload authoring can pass.
    schema_lipsync = get_path(schema, "heygen_supported_media_forms", "precision_lipsync", default={})
    if not isinstance(schema_lipsync, dict):
        blockers.append(Blocker(global_id, "api-field", "LIPSYNC_SCHEMA_MISSING", "precision_lipsync contract block is missing from HEYGEN_BATCH_MEDIA_INPUT_SCHEMA"))
    else:
        comparisons = (
            ("enable_dynamic_duration", get_path(contract, "kannada_lipsync_contract", "dynamic_duration_default")),
            ("enable_caption", get_path(contract, "kannada_lipsync_contract", "enable_caption")),
            ("enable_watermark", get_path(contract, "kannada_lipsync_contract", "enable_watermark")),
            ("enable_speech_enhancement", get_path(contract, "kannada_lipsync_contract", "enable_speech_enhancement")),
            ("keep_same_format", get_path(contract, "kannada_lipsync_contract", "keep_the_same_format")),
        )
        for schema_key, contract_value in comparisons:
            schema_value = schema_lipsync.get(schema_key)
            if schema_value != contract_value:
                blockers.append(
                    Blocker(
                        global_id,
                        "api-field",
                        "LIPSYNC_DEFAULT_CONTRACT_DRIFT",
                        f"precision_lipsync.{schema_key}={schema_value!r} disagrees with HEYGEN_API_ACCEPTANCE_CONTRACT value {contract_value!r}",
                    )
                )

    # Accepted arbitrary image forms must remain the two contract-approved transport forms.
    accepted = get_path(schema, "heygen_supported_media_forms", "arbitrary_source_image", "accepted", default=[])
    accepted_types = {item.get("type") for item in accepted if isinstance(item, dict)}
    if accepted_types != {"url", "asset_id"}:
        blockers.append(Blocker(global_id, "api-field", "IMAGE_ASSET_FORM_DRIFT", f"arbitrary_source_image accepted types must be url + asset_id; found {sorted(x for x in accepted_types if x is not None)}"))

    return blockers


def validate_contract_paths(schema: dict[str, Any]) -> list[Blocker]:
    expected = {
        "p1_requirements": "production/references/BATCH_REFERENCE_REQUIREMENTS.yaml",
        "p1_bindings": "production/batches/P1_BATCH_REFERENCE_BINDINGS.yaml",
        "p1_registry": "production/references/REFERENCE_REGISTRY.yaml",
        "heygen_acceptance_contract": "production/heygen/HEYGEN_API_ACCEPTANCE_CONTRACT.yaml",
        "p0_foundation": "production/batches/ANAADHI_BATCH_FOUNDATION.py",
    }
    blockers: list[Blocker] = []
    sources = schema.get("canonical_sources", {})
    for key, path in expected.items():
        if sources.get(key) != path:
            blockers.append(Blocker("GLOBAL", "structure", "CANONICAL_SOURCE_MISMATCH", f"canonical_sources.{key} must be {path!r}; found {sources.get(key)!r}"))
    return blockers


def validate_scene_coverage(
    schema_batches: dict[str, Any],
    req_batches: dict[str, Any],
    binding_batches: dict[str, Any],
    p0_batches: dict[str, Any],
) -> list[Blocker]:
    blockers: list[Blocker] = []
    for name, mapping in (
        ("schema", schema_batches),
        ("requirements", req_batches),
        ("bindings", binding_batches),
        ("P0", p0_batches),
    ):
        found = list(mapping.keys())
        if found != EXPECTED_BATCHES:
            blockers.append(Blocker("GLOBAL", "structure", "BATCH_SET_MISMATCH", f"{name} batch IDs must be exactly B01-B34 in order; found {found}"))

        hits: dict[int, list[str]] = {}
        for batch_id, record in mapping.items():
            for scene in as_list(record.get("scenes")):
                try:
                    scene_i = int(scene)
                except (TypeError, ValueError):
                    blockers.append(Blocker(batch_id, "structure", "INVALID_SCENE_ID", f"{name}: non-integer scene ID {scene!r}"))
                    continue
                hits.setdefault(scene_i, []).append(batch_id)
        missing = [s for s in EXPECTED_SCENES if s not in hits]
        duplicate = {s: ids for s, ids in hits.items() if len(ids) != 1}
        extra = sorted(s for s in hits if s not in EXPECTED_SCENES)
        if missing:
            blockers.append(Blocker("GLOBAL", "structure", "MISSING_SCENES", f"{name}: missing scenes {missing}"))
        if duplicate:
            blockers.append(Blocker("GLOBAL", "structure", "DUPLICATE_SCENES", f"{name}: duplicate scene coverage {duplicate}"))
        if extra:
            blockers.append(Blocker("GLOBAL", "structure", "OUT_OF_RANGE_SCENES", f"{name}: out-of-range scenes {extra}"))
    return blockers


def validate_batch(
    batch_id: str,
    schema_record: dict[str, Any],
    req_record: dict[str, Any],
    binding_record: dict[str, Any],
    p0_record: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    avatar_index: dict[str, Any] | None,
    contract: dict[str, Any],
) -> list[Blocker]:
    blockers: list[Blocker] = []

    # Cross-file structural equality.
    scene_sets = {
        "schema": as_list(schema_record.get("scenes")),
        "requirements": as_list(req_record.get("scenes")),
        "bindings": as_list(binding_record.get("scenes")),
        "P0": as_list(p0_record.get("scenes")),
    }
    if len({tuple(v) for v in scene_sets.values()}) != 1:
        blockers.append(Blocker(batch_id, "structure", "SCENE_CROSSCHECK_MISMATCH", f"Scene lists disagree: {scene_sets}"))

    crosswalk = (
        ("required_location_refs", "locations"),
        ("required_anaadhi_refs", "anaadhi"),
        ("required_prop_refs", "props"),
    )
    for schema_key, req_key in crosswalk:
        left = canonical_string_list(schema_record.get(schema_key, []))
        right = canonical_string_list(req_record.get(req_key, []))
        if left != right:
            blockers.append(Blocker(batch_id, "structure", "REFERENCE_CROSSCHECK_MISMATCH", f"{schema_key} != requirements.{req_key}: {left} != {right}"))

    # Root/nested-space binding cross-check.
    for key in ("env6l_roots", "pending_named_location_refs"):
        left = canonical_string_list(schema_record.get(key, []))
        right = canonical_string_list(binding_record.get(key, []))
        if left != right:
            blockers.append(Blocker(batch_id, "location", "LOCATION_BINDING_MISMATCH", f"{key} disagrees with P1_BATCH_REFERENCE_BINDINGS: {left} != {right}"))

    approved_root = binding_record.get("approved_root")
    if approved_root is not True:
        blockers.append(Blocker(batch_id, "location", "ROOT_LOCATION_UNRESOLVED", f"approved_root must be boolean true; found {approved_root!r}"))

    pending_named = canonical_string_list(binding_record.get("pending_named_location_refs", []))
    if pending_named:
        blockers.append(Blocker(batch_id, "location", "PENDING_NAMED_LOCATION", f"Unresolved named location binding(s): {', '.join(pending_named)}"))

    remaining_location_work = canonical_string_list(binding_record.get("remaining_location_work", []))
    if remaining_location_work:
        blockers.append(Blocker(batch_id, "nested-space", "REMAINING_LOCATION_WORK", "Unresolved location/nested-space/state work: " + " | ".join(remaining_location_work)))

    # Registry gates for every required visual reference.
    required_refs = (
        canonical_string_list(schema_record.get("required_location_refs", []))
        + canonical_string_list(schema_record.get("required_anaadhi_refs", []))
        + canonical_string_list(schema_record.get("required_prop_refs", []))
    )
    for ref_id in required_refs:
        category = classify_reference(ref_id)
        record = registry.get(ref_id)
        if record is None:
            blockers.append(Blocker(batch_id, category, "REFERENCE_UNDEFINED", f"Required reference {ref_id} is not defined in REFERENCE_REGISTRY.yaml"))
            continue
        if not status_is_approved(record):
            blockers.append(Blocker(batch_id, category, "REFERENCE_NOT_APPROVED", f"{ref_id}: status={record.get('status')!r}, path={record.get('path')!r}"))

    # Character/avatar-slot gate. Named character intent is inherited from P0, but a
    # batch cannot pass until the work-page-owned avatar manifest exists and every
    # listed avatar asset needed by that manifest is complete with a HeyGen look ID.
    named_characters = split_named_characters(p0_record.get("characters"))
    if not named_characters:
        blockers.append(Blocker(batch_id, "avatar-slot", "P0_CHARACTER_SLOTS_EMPTY", "P0 named-character list is empty or unreadable"))

    manifest_path, manifest = load_avatar_manifest_for_batch(batch_id, avatar_index)
    if manifest_path is None:
        blockers.append(Blocker(batch_id, "avatar-slot", "AVATAR_MANIFEST_UNASSIGNED", "No avatar manifest is assigned for this batch; inherited P0 slots remain unresolved"))
    elif manifest is None:
        blockers.append(Blocker(batch_id, "avatar-slot", "AVATAR_MANIFEST_MISSING", f"Assigned avatar manifest does not exist: {manifest_path.relative_to(ROOT)}"))
    else:
        manifest_scenes = as_list(manifest.get("scenes"))
        if manifest.get("batch_id") != batch_id or manifest_scenes != as_list(schema_record.get("scenes")):
            blockers.append(Blocker(batch_id, "avatar-slot", "AVATAR_MANIFEST_SCOPE_MISMATCH", "Avatar manifest batch/scenes do not match the batch-media schema"))
        assets = manifest.get("assets")
        if not isinstance(assets, dict) or not assets:
            blockers.append(Blocker(batch_id, "avatar-slot", "AVATAR_ASSETS_EMPTY", "Avatar manifest contains no assets"))
        else:
            unresolved_assets = []
            for asset_id, asset in assets.items():
                if not isinstance(asset, dict):
                    unresolved_assets.append(str(asset_id))
                    continue
                if str(asset.get("heygen_status", "")).upper() not in {"COMPLETE", "COMPLETED"} or not asset.get("heygen_look_id"):
                    unresolved_assets.append(str(asset_id))
            if unresolved_assets:
                blockers.append(Blocker(batch_id, "avatar-slot", "AVATAR_LOOKS_UNRESOLVED", "Avatar asset(s) not COMPLETE with look IDs: " + ", ".join(unresolved_assets)))

        # Consent is fail-closed. A private-avatar render cannot pass because a group
        # exists; an affirmative consent state must be recorded for every selected
        # private avatar or at batch manifest level.
        consent_values = collect_consent_values(manifest)
        if not consent_values or any(v not in CONSENT_OK for v in consent_values):
            blockers.append(Blocker(batch_id, "consent", "CONSENT_UNRESOLVED", f"Private-avatar consent is not explicitly COMPLETE/APPROVED/VERIFIED/NOT_REQUIRED in {manifest_path.relative_to(ROOT)}"))

    # The acceptance contract itself currently records Anaadhi consent as observed null;
    # keep that visible as a hard global-to-batch constraint wherever avatars are used.
    observed = get_path(contract, "avatar_input_contract", "photo_avatar", "current_anaadhi_group", "consent_status_observed")
    if observed is not None and str(observed).upper() not in CONSENT_OK:
        blockers.append(Blocker(batch_id, "consent", "CONTRACT_CONSENT_NOT_ACCEPTED", f"Acceptance contract consent_status_observed={observed!r}"))
    elif observed is None and any("anaadhi" in name.lower() for name in named_characters):
        blockers.append(Blocker(batch_id, "consent", "ANAADHI_CONSENT_UNVERIFIED", "Acceptance contract records Anaadhi private-avatar consent_status_observed=null"))

    # Validate any future embedded payloads without creating/submitting them.
    scan_payloads(batch_id, schema_record, blockers, f"batches.{batch_id}")

    return blockers


def build_report(selected_batch: str | None = None) -> dict[str, Any]:
    schema = load_yaml(SCHEMA_PATH)
    requirements = load_yaml(REQUIREMENTS_PATH)
    bindings = load_yaml(BINDINGS_PATH)
    registry_source = load_yaml(REGISTRY_PATH)
    contract = load_yaml(CONTRACT_PATH)
    p0_batches = extract_p0_batches(P0_PATH)
    avatar_index = load_yaml(AVATAR_INDEX_PATH) if AVATAR_INDEX_PATH.is_file() else None

    schema_batches = exact_batch_map(schema, "batches", "schema")
    req_batches = exact_batch_map(requirements, "batches", "requirements")
    binding_batches = exact_batch_map(bindings, "location_bindings", "bindings")
    registry = flatten_registry(registry_source)

    blockers: list[Blocker] = []
    blockers.extend(validate_global_safety(schema, contract))
    blockers.extend(validate_contract_paths(schema))
    blockers.extend(validate_schema_contract_semantics(schema, contract))
    blockers.extend(validate_scene_coverage(schema_batches, req_batches, binding_batches, p0_batches))

    if selected_batch is not None:
        if selected_batch not in EXPECTED_BATCHES:
            raise ValidationConfigError(f"--batch must be B01-B34; found {selected_batch!r}")
        batch_ids = [selected_batch]
    else:
        batch_ids = EXPECTED_BATCHES

    for batch_id in batch_ids:
        missing_sources = [
            name
            for name, mapping in (
                ("schema", schema_batches),
                ("requirements", req_batches),
                ("bindings", binding_batches),
                ("P0", p0_batches),
            )
            if batch_id not in mapping
        ]
        if missing_sources:
            blockers.append(Blocker(batch_id, "structure", "BATCH_SOURCE_MISSING", f"Batch missing from: {', '.join(missing_sources)}"))
            continue
        blockers.extend(
            validate_batch(
                batch_id=batch_id,
                schema_record=schema_batches[batch_id],
                req_record=req_batches[batch_id],
                binding_record=binding_batches[batch_id],
                p0_record=p0_batches[batch_id],
                registry=registry,
                avatar_index=avatar_index,
                contract=contract,
            )
        )

    selected_blockers = [b for b in blockers if b.batch_id == "GLOBAL" or b.batch_id in batch_ids]
    by_batch: dict[str, list[dict[str, str]]] = {batch_id: [] for batch_id in batch_ids}
    global_blockers: list[dict[str, str]] = []
    for blocker in selected_blockers:
        payload = asdict(blocker)
        if blocker.batch_id == "GLOBAL":
            global_blockers.append(payload)
        else:
            by_batch[blocker.batch_id].append(payload)

    passed = [batch_id for batch_id, items in by_batch.items() if not items and not global_blockers]
    blocked = [batch_id for batch_id, items in by_batch.items() if items or global_blockers]

    return {
        "validator": "HEYGEN-BATCH-MEDIA-VALIDATOR",
        "mode": "VALIDATION_ONLY__ZERO_MEDIA_GENERATION__ZERO_HEYGEN_SUBMISSION",
        "scope": selected_batch or "B01-B34 / SC001-SC100",
        "source_files": [
            str(SCHEMA_PATH.relative_to(ROOT)),
            str(REQUIREMENTS_PATH.relative_to(ROOT)),
            str(BINDINGS_PATH.relative_to(ROOT)),
            str(REGISTRY_PATH.relative_to(ROOT)),
            str(CONTRACT_PATH.relative_to(ROOT)),
            str(P0_PATH.relative_to(ROOT)),
            str(AVATAR_INDEX_PATH.relative_to(ROOT)) if AVATAR_INDEX_PATH.is_file() else None,
        ],
        "summary": {
            "selected_batches": len(batch_ids),
            "passed_batches": len(passed),
            "blocked_batches": len(blocked),
            "global_blockers": len(global_blockers),
            "total_blockers": len(selected_blockers),
        },
        "passed_batches": passed,
        "blocked_batches": blocked,
        "global": global_blockers,
        "batches": by_batch,
    }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        "HEYGEN-BATCH-MEDIA-VALIDATOR",
        "MODE: VALIDATION ONLY — ZERO MEDIA GENERATION — ZERO HEYGEN SUBMISSION",
        f"Scope: {report['scope']}",
        "",
    ]
    summary = report["summary"]
    lines.extend(
        [
            f"Selected batches: {summary['selected_batches']}",
            f"Passed batches:   {summary['passed_batches']}",
            f"Blocked batches:  {summary['blocked_batches']}",
            f"Global blockers:  {summary['global_blockers']}",
            f"Total blockers:   {summary['total_blockers']}",
        ]
    )

    if report["global"]:
        lines.append("\nGLOBAL HARD BLOCKERS")
        for item in report["global"]:
            lines.append(f"- [{item['category']}/{item['code']}] {item['message']}")

    for batch_id in report["blocked_batches"]:
        items = report["batches"][batch_id]
        if not items:
            continue
        lines.append(f"\n{batch_id} HARD BLOCKED")
        for item in items:
            lines.append(f"- [{item['category']}/{item['code']}] {item['message']}")

    if report["passed_batches"]:
        lines.append("\nPASS: " + ", ".join(report["passed_batches"]))

    if report["blocked_batches"]:
        lines.append("\nRESULT: BLOCKED — no batch may advance through this validator until its blockers are resolved.")
    else:
        lines.append("\nRESULT: PASS — validation gate satisfied. This validator still performs no generation or submission.")
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ANAADHI B01-B34 HeyGen media readiness without generation/submission.")
    parser.add_argument("--batch", help="Validate one batch only (B01-B34). Default: all batches.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON to stdout.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    selected = args.batch.upper() if args.batch else None
    try:
        report = build_report(selected)
    except (ValidationConfigError, yaml.YAMLError, SyntaxError) as exc:
        print(f"VALIDATOR CONFIG ERROR: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_text(report))

    return 2 if report["blocked_batches"] or report["global"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
