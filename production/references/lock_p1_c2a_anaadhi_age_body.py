from pathlib import Path
from PIL import Image
import hashlib
import re
import yaml

ROOT = Path('production/references/characters/anaadhi/age_body/P1-C2A')
REGISTRY = Path('production/references/REFERENCE_REGISTRY.yaml')
MATRIX = Path('production/references/ANAADHI_IDENTITY_STATE_MATRIX.yaml')
MASTER = Path('production/references/characters/anaadhi/CHR-ANAADHI_MASTER-IDENTITY-01.yaml')

EXPECTED = {
    'AGE-ANAADHI-NEWBORN': ('CHR-ANAADHI_NEWBORN_AGE-BODY-REF-01.png', '35daf506bc9a64eb4119758adb4a8fd967da797c3e69406e4068fb8404788c07'),
    'AGE-ANAADHI-05': ('CHR-ANAADHI_AGE_05_AGE-BODY-REF-01.png', 'f5b70bc79b54855a0007ad7e0de3d480f80de8ed771a8a5a0bc7c2015a28fc1e'),
    'AGE-ANAADHI-07': ('CHR-ANAADHI_AGE_07_AGE-BODY-REF-01.png', 'b1f621ceb10841b8b149d392f1d0f97e7ff54afb708997b523d9d90512ced4fe'),
    'AGE-ANAADHI-08': ('CHR-ANAADHI_AGE_08_AGE-BODY-REF-01.png', 'dc43f885e6a2d5eb952a51bd8833e9d6995bca2d339e236c8650b6ec60f9ace0'),
    'AGE-ANAADHI-09': ('CHR-ANAADHI_AGE_09_AGE-BODY-REF-01.png', '9b44a897c9480f4d80df091257f805aa6f081fabe114104138b7a0d80d3f9560'),
    'AGE-ANAADHI-10': ('CHR-ANAADHI_AGE_10_AGE-BODY-REF-01.png', '7cbbee63f2b20a9c33411672a252f1ecd42e8c19b2a9a19b332d658ea8291a2c'),
    'AGE-ANAADHI-11': ('CHR-ANAADHI_AGE_11_AGE-BODY-REF-01.png', '269153a48913e34af8920fb083a2db39b8729ed926cfe706fc11cf51ca84379d'),
    'AGE-ANAADHI-12-INSTITUTIONAL': ('CHR-ANAADHI_AGE_12_INSTITUTIONAL_AGE-BODY-REF-01.png', '856081416f6efff073f03ecf59cebf7b60c98dfc957383df9c930d1f72bb536b'),
    'AGE-ANAADHI-12-FOREST': ('CHR-ANAADHI_AGE_12_FOREST_AGE-BODY-REF-01.png', '45422809702503095bf142f5c347f8407f09e0c211d2d0f93391f170366c343c'),
}
CONTACT = ('CHR-ANAADHI_P1-C2A_AGE-BODY-FAMILY_CONTACT-SHEET.png', 'dc17aaf14479ed726ebdd66da006ad36d89ec3868156db0f7a997976e6d35ea7')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_png(path: Path, expected_sha: str):
    if not path.exists():
        raise SystemExit(f'Missing asset: {path}')
    if sha256(path) != expected_sha:
        raise SystemExit(f'SHA mismatch: {path}')
    im = Image.open(path)
    if im.format != 'PNG' or im.size != (1200, 1600):
        raise SystemExit(f'Unexpected plate format/raster: {path} {im.format} {im.size}')


def patch_registry():
    text = REGISTRY.read_text(encoding='utf-8')
    for state, (fname, digest) in EXPECTED.items():
        path = f'production/references/characters/anaadhi/age_body/P1-C2A/{fname}'
        if state == 'AGE-ANAADHI-NEWBORN':
            pattern = re.compile(r'(?ms)^  AGE-ANAADHI-NEWBORN:\n    age: newborn\n    status: MISSING_APPROVED_ASSET\n    path: null\n')
            repl = (
                '  AGE-ANAADHI-NEWBORN:\n'
                '    age: newborn\n'
                '    status: APPROVED\n'
                f'    path: "{path}"\n'
                f'    sha256: "{digest}"\n'
                '    scope: AGE_BODY_GEOMETRY_ONLY\n'
                '    non_authoritative_pixels: [hair, costume, injury]\n'
            )
        else:
            age = '12' if '12-' in state else state.split('-')[-1].lstrip('0')
            escaped = re.escape(state)
            pattern = re.compile(rf'^  {escaped}: \{{age: {age}, status: MISSING_APPROVED_ASSET, path: null\}}\n', re.M)
            repl = (
                f'  {state}:\n'
                f'    age: {age}\n'
                '    status: APPROVED\n'
                f'    path: "{path}"\n'
                f'    sha256: "{digest}"\n'
                '    scope: AGE_BODY_GEOMETRY_ONLY\n'
                '    non_authoritative_pixels: [hair, costume, injury]\n'
            )
        text2, count = pattern.subn(repl, text, count=1)
        if count != 1:
            raise SystemExit(f'Could not patch registry state {state}; matches={count}')
        text = text2
    REGISTRY.write_text(text, encoding='utf-8')


def patch_matrix():
    data = yaml.safe_load(MATRIX.read_text(encoding='utf-8'))
    key_map = {
        'AGE-ANAADHI-NEWBORN': 'NEWBORN',
        'AGE-ANAADHI-05': 'AGE_05',
        'AGE-ANAADHI-07': 'AGE_07',
        'AGE-ANAADHI-08': 'AGE_08',
        'AGE-ANAADHI-09': 'AGE_09',
        'AGE-ANAADHI-10': 'AGE_10',
        'AGE-ANAADHI-11': 'AGE_11',
        'AGE-ANAADHI-12-INSTITUTIONAL': 'AGE_12_INSTITUTIONAL',
        'AGE-ANAADHI-12-FOREST': 'AGE_12_FOREST',
    }
    for state, matrix_key in key_map.items():
        fname, digest = EXPECTED[state]
        node = data['states'][matrix_key]
        node['visual_asset_status'] = 'APPROVED'
        node['age_body_reference'] = f'production/references/characters/anaadhi/age_body/P1-C2A/{fname}'
        node['age_body_reference_sha256'] = digest
        node['age_body_reference_scope'] = 'AGE_BODY_GEOMETRY_ONLY'
        node['reference_pixel_exclusions'] = ['hair', 'costume', 'injury']
    data['qa']['p1_identity_assets_complete'] = False
    data['qa']['p1_c2a_age_body_family'] = 'APPROVED'
    data['qa']['p1_c2a_states'] = list(EXPECTED.keys())
    MATRIX.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120), encoding='utf-8')


def patch_master_identity():
    text = MASTER.read_text(encoding='utf-8')
    text = text.replace('  age_body_states: PENDING\n', '  age_body_states: PARTIAL_APPROVED_P1-C2A_NEWBORN_TO_AGE12\n', 1)
    MASTER.write_text(text, encoding='utf-8')


def write_manifest():
    states = []
    for state, (fname, digest) in EXPECTED.items():
        states.append({
            'state': state,
            'path': f'production/references/characters/anaadhi/age_body/P1-C2A/{fname}',
            'sha256': digest,
            'scope': 'AGE_BODY_GEOMETRY_ONLY',
            'hair_pixels': 'NON_CANONICAL',
            'costume_pixels': 'NON_CANONICAL',
            'injury_pixels': 'NON_CANONICAL',
        })
    manifest = {
        'version': 1,
        'phase': 'P1-C2A',
        'lock_id': 'CHR-ANAADHI_AGE-BODY-FAMILY_01',
        'character_ref': 'CHR-ANAADHI',
        'master_identity': 'CHR-ANAADHI_MASTER-IDENTITY-01',
        'status': 'APPROVED_WITH_SCOPE_LOCK',
        'canonical_adult_height_cm': 193,
        'states': states,
        'contact_sheet': {
            'path': f'production/references/characters/anaadhi/age_body/P1-C2A/{CONTACT[0]}',
            'sha256': CONTACT[1],
            'scope': 'REVIEW_ONLY_NO_METRIC_AUTHORITY',
        },
        'absolute_rules': [
            'These images approve age/body geometry and face-family continuity only.',
            'Do not inherit child heights, weights, dates, labels, measurements or notes from any rejected generator poster.',
            'Do not treat hair pixels as approved hair canon.',
            'Do not treat clothing pixels as approved costume canon.',
            'Do not treat visible marks as approved injury/scar canon.',
            'Do not derive exact child metric heights from these plates; use later approved scale data and scene blocking.',
            'Never shrink an adult body to create child stages; all child and adolescent anatomy is age-correct.',
            'Adult Anaadhi remains exactly 193 cm / 6\'4 wherever adult metric scale applies.',
            'AGE-12-INSTITUTIONAL and AGE-12-FOREST share the same underlying age-12 identity; only body condition/exposure may differ at this layer.',
        ],
        'rejected_generator_board': {
            'status': 'DO_NOT_COMMIT_DO_NOT_USE_AS_CANON',
            'reason': 'Contained invented text, dates, heights, weights and hair/costume claims. Only photographic subject crops were extracted.',
        },
        'drive_backup': {
            'folder_id': '1ICn1lfVq2fJtURedX13rrso7Yhx1w8fb',
            'zip_file_id': '1ybzUSnLGjB33ZxZo_Hp6tM8u_gnKF_1o',
            'contact_sheet_file_id': '1Qut8H40ZZr8ukQ7-SmuL_xe2h6Ct2nnm',
        },
        'next_layer': 'P1-C2B_ANAADHI_AGE-BODY_13_TO_18',
    }
    (ROOT / 'CHR-ANAADHI_AGE-BODY-FAMILY_01.yaml').write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True, width=120), encoding='utf-8'
    )


for state, (fname, digest) in EXPECTED.items():
    verify_png(ROOT / fname, digest)

contact = ROOT / CONTACT[0]
if not contact.exists() or sha256(contact) != CONTACT[1]:
    raise SystemExit('Contact sheet mismatch')

patch_registry()
patch_matrix()
patch_master_identity()
write_manifest()
print('P1-C2A Anaadhi age/body family validated and locked.')
