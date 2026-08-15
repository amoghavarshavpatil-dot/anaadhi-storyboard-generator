from pathlib import Path
from PIL import Image
import hashlib
import re

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = ROOT / "production" / "references" / "characters" / "anaadhi"
FACE = ASSET_DIR / "CHR-ANAADHI_MASTER-IDENTITY-01_FACE_SOURCE.jpg"
BODY = ASSET_DIR / "CHR-ANAADHI_MASTER-IDENTITY-01_BODY_PROPORTION_SOURCE.jpg"
MANIFEST = ASSET_DIR / "CHR-ANAADHI_MASTER-IDENTITY-01.yaml"
REGISTRY = ROOT / "production" / "references" / "REFERENCE_REGISTRY.yaml"
MATRIX = ROOT / "production" / "references" / "ANAADHI_IDENTITY_STATE_MATRIX.yaml"


def verify_image(path: Path) -> None:
    if not path.exists() or path.stat().st_size < 100_000:
        raise SystemExit(f"Missing or unexpectedly small blueprint: {path}")
    with Image.open(path) as im:
        im.verify()


ASSET_DIR.mkdir(parents=True, exist_ok=True)
verify_image(FACE)
verify_image(BODY)
face_sha = hashlib.sha256(FACE.read_bytes()).hexdigest()
body_sha = hashlib.sha256(BODY.read_bytes()).hexdigest()

manifest = f'''version: 1
phase: P1_CHARACTER_IDENTITY_CONTROL
lock_id: CHR-ANAADHI_MASTER-IDENTITY-01
character_ref: CHR-ANAADHI
status: APPROVED
adult_height_cm: 193
adult_height_display: "6'4"

source_authority:
  face_identity:
    role: PRIMARY_CANONICAL_FACE_AUTHORITY
    path: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01_FACE_SOURCE.jpg"
    sha256: "{face_sha}"
    drive_file_id: "1S9ATxjhCp3tQp5jCmaY58v_DeliDgA7f"
    source_printed_height: "6'4 / 193 cm"
    height_status: MATCHES_CANON
  body_proportion:
    role: APPROVED_RELATIVE_ANATOMY_REFERENCE_NON_METRIC
    path: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01_BODY_PROPORTION_SOURCE.jpg"
    sha256: "{body_sha}"
    drive_file_id: "14xjdKBff58tJ8IWXEPkFbQrZb7nPACeK"
    source_printed_height: "6'2 / 188 cm"
    height_status: SOURCE_LABEL_CONFLICT
    canonical_override: "Ignore the printed 188 cm / 6'2 ruler. Preserve relative anatomy/proportion logic only and scale adult Anaadhi to exactly 193 cm / 6'4."

identity_lock:
  face:
    - "same cranial width and facial silhouette family"
    - "thick straight/naturally arched brow structure"
    - "deep-set brown eye character"
    - "straight strong-base nose"
    - "balanced controlled lip structure"
    - "strong masculine jaw and chin definition"
    - "medium-brown Karnataka/South-Indian skin identity with natural texture"
  morphology:
    - "tall masculine frame"
    - "long-limbed adult proportions"
    - "broad-shouldered but not bodybuilder-exaggerated"
    - "lean-defined Scene-100 morphology is a final-state subcondition, not the universal body condition"
    - "all adult metric scaling resolves to 193 cm"

non_inheritance_rules:
  - "Do not freeze Scene-100 hair into earlier ages."
  - "Do not freeze Scene-100 beard/moustache into childhood, teen or earlier adult states."
  - "Do not freeze Scene-100 healed scars into pre-surgery states."
  - "Do not freeze Scene-100 lean post-recovery body condition into forest/capture states."
  - "Do not use the body source's 188 cm ruler in any generated shot, scale sheet or camera blocking calculation."
  - "Child and teen states require separate age/body reconstructions; never shrink the adult body."

p1_dependencies_remaining:
  age_body_states: PENDING
  hair_facial_hair_states: PENDING
  costume_states: PENDING
  injury_scar_states: PENDING
  scene_specific_parallel_variants: PENDING_WHERE_REQUIRED

approval_scope: >-
  This lock approves the underlying Anaadhi identity family and adult relative proportion logic only.
  It does not approve any specific age, hair, costume, injury, scene action, dialogue, lip-sync,
  BGM, SFX, or camera treatment.
'''
MANIFEST.write_text(manifest, encoding="utf-8")

registry_text = REGISTRY.read_text(encoding="utf-8")
pattern = re.compile(r"(?ms)^  CHR-ANAADHI:\n.*?(?=^  CHR-[A-Z0-9-]+:|^anaadhi_age_body_states:)")
replacement = '''  CHR-ANAADHI:
    name: Anaadhi
    status: APPROVED
    path: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01.yaml"
    notes: "Underlying identity family locked. Exact age/body/hair/costume/injury substates remain mandatory and independent."
    face_reference_path: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01_FACE_SOURCE.jpg"
    body_proportion_reference_path: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01_BODY_PROPORTION_SOURCE.jpg"
    adult_height_cm: 193
    body_metric_override: "Body blueprint source prints 188 cm / 6'2; that printed ruler is non-canonical. Use relative anatomy only and scale adult Anaadhi to 193 cm / 6'4."
'''
patched, count = pattern.subn(replacement, registry_text, count=1)
if count != 1:
    raise SystemExit(f"Could not patch CHR-ANAADHI registry block; matches={count}")
REGISTRY.write_text(patched, encoding="utf-8")

matrix_text = MATRIX.read_text(encoding="utf-8")
if "master_identity_status: MISSING_APPROVED_ASSET" in matrix_text:
    matrix_text = matrix_text.replace(
        "master_identity_status: MISSING_APPROVED_ASSET",
        "master_identity_status: APPROVED",
        1,
    )
elif "master_identity_status: APPROVED" not in matrix_text:
    raise SystemExit("Unexpected Anaadhi master identity status")

marker = "adult_height_display: \"6'4\"\n"
addition = '''identity_lock_manifest: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01.yaml"
face_identity_reference: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01_FACE_SOURCE.jpg"
body_proportion_reference: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01_BODY_PROPORTION_SOURCE.jpg"
body_reference_height_override: "Source ruler says 188 cm / 6'2; canonical adult height remains 193 cm / 6'4."
'''
if "identity_lock_manifest:" not in matrix_text:
    if marker not in matrix_text:
        raise SystemExit("Could not find matrix height marker")
    matrix_text = matrix_text.replace(marker, marker + addition, 1)
MATRIX.write_text(matrix_text, encoding="utf-8")

# Final targeted validation.
reg = REGISTRY.read_text(encoding="utf-8")
mat = MATRIX.read_text(encoding="utf-8")
assert "CHR-ANAADHI:" in reg
assert 'path: "production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01.yaml"' in reg
assert "adult_height_cm: 193" in reg
assert "188 cm / 6'2" in reg
assert "master_identity_status: APPROVED" in mat
assert MANIFEST.exists()
print("P1-C1 CHR-ANAADHI master identity lock validated.")
print("Face SHA256:", face_sha)
print("Body SHA256:", body_sha)
