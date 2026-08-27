import {createHash} from 'node:crypto';
import {existsSync, readFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const cursorPath = resolve(projectRoot, 'PICTURE_APPROVAL_CURSOR.json');
const cursor = JSON.parse(readFileSync(cursorPath, 'utf8'));
const idPattern = /^SC(\d{3})_SH(\d{3})$/;

const parseShotId = (shotId) => {
  const match = shotId.match(idPattern);
  if (!match) {
    throw new Error(`Invalid shot ID: ${shotId}`);
  }

  return {scene: Number(match[1]), shot: Number(match[2])};
};

const first = parseShotId(cursor.sequence_scope.first_shot);
const last = parseShotId(cursor.sequence_scope.last_shot);
const approvedAcrossScope = [];
let encounteredIncompleteScene = false;
let expectedNextShot = null;

for (let sceneNumber = first.scene; sceneNumber <= last.scene; sceneNumber += 1) {
  const sceneId = `SC${String(sceneNumber).padStart(3, '0')}`;
  const manifestPath = resolve(projectRoot, `shot_specs/${sceneId}/${sceneId}_SHOT_PACKAGE.json`);
  if (!existsSync(manifestPath)) {
    throw new Error(`Missing shot package in approval scope: ${sceneId}`);
  }

  const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
  const approved = manifest.shots.filter((shot) => shot.status === 'APPROVED_SHOT');

  if (encounteredIncompleteScene && approved.length > 0) {
    throw new Error(`${sceneId} has approved shots after an incomplete earlier scene`);
  }

  if (approved.length > 0 && approved.length !== manifest.picture_progress?.approved_count) {
    throw new Error(`${sceneId} approved count mismatch: ${approved.length}`);
  }

  approved.forEach((shot, index) => {
    const expectedId = `${sceneId}_SH${String(index + 1).padStart(3, '0')}`;
    if (shot.shot_id !== expectedId) {
      throw new Error(`Non-sequential shot: expected ${expectedId}, got ${shot.shot_id}`);
    }

    const assetPath = resolve(projectRoot, 'public', shot.remotion_static_file);
    const bytes = readFileSync(assetPath);
    const pngSignature = bytes.subarray(0, 8).toString('hex');
    if (pngSignature !== '89504e470d0a1a0a') {
      throw new Error(`${shot.shot_id} is not a valid PNG`);
    }

    const width = bytes.readUInt32BE(16);
    const height = bytes.readUInt32BE(20);
    if (width !== shot.source_dimensions.width || height !== shot.source_dimensions.height) {
      throw new Error(`${shot.shot_id} dimension mismatch: ${width}x${height}`);
    }

    const sha256 = createHash('sha256').update(bytes).digest('hex');
    if (sha256 !== shot.sha256) {
      throw new Error(`${shot.shot_id} SHA-256 mismatch`);
    }

    approvedAcrossScope.push(shot);
  });

  if (approved.length < manifest.shots.length && expectedNextShot === null) {
    expectedNextShot = `${sceneId}_SH${String(approved.length + 1).padStart(3, '0')}`;
    encounteredIncompleteScene = true;
  }
}

if (approvedAcrossScope.length !== cursor.progress.approved_count) {
  throw new Error(`Global approved count mismatch: ${approvedAcrossScope.length}`);
}

if (cursor.progress.last_approved_shot !== approvedAcrossScope.at(-1)?.shot_id) {
  throw new Error('Cursor last_approved_shot does not match the final approved shot');
}

if (cursor.progress.next_shot !== expectedNextShot) {
  throw new Error(`Cursor next_shot mismatch: expected ${expectedNextShot}`);
}

console.log(
  `Verified ${approvedAcrossScope.length} sequential approved PNGs from ${cursor.sequence_scope.first_shot} through ${cursor.progress.last_approved_shot}.`,
);
