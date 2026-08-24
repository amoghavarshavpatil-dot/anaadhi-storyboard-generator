import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const manifestPath = resolve(projectRoot, 'shot_specs/SC001/SC001_SHOT_PACKAGE.json');
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const approved = manifest.shots.filter((shot) => shot.status === 'APPROVED_SHOT');

if (approved.length !== manifest.picture_progress.approved_count) {
  throw new Error(`Approved count mismatch: ${approved.length}`);
}

approved.forEach((shot, index) => {
  const expectedId = `SC001_SH${String(index + 1).padStart(3, '0')}`;
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
});

if (manifest.picture_progress.approved_through !== approved.at(-1)?.shot_id) {
  throw new Error('approved_through does not match the final approved shot');
}

console.log(`Verified ${approved.length} sequential approved SC001 PNGs.`);
