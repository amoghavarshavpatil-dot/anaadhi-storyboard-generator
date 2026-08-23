import {copyFile, mkdir, writeFile} from 'node:fs/promises';
import {dirname, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const remotionRoot = resolve(here, '..');
const repositoryRoot = resolve(remotionRoot, '..', '..');

const assets = [
  ['production/heygen/avatars/B01/source_visuals/CHR-ANAADHI_B01_CAPTURE_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/anaadhi.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-AARATHI_B01_FIELD_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/aarathi.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-AARATHI_B01_PARALLEL-MEDICAL_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/aarathi-medical.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-MEDICAL-SPECIALIST_B01_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/medical-specialist.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-POLICE-COMMANDER_B01_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/police-commander.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-SARJANYA-OFFICER_B01_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/sarjanya-officer.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-SEMMAA_B01_FIELD_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/semmaa.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-ALLIED-GANGSTER_B01_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/allied-gangster.jpg'],
  ['production/heygen/avatars/B01/source_visuals/CHR-ANAADHI_B01_NEWBORN-PARALLEL_HEYGEN-UPLOAD-MASTER_2160x3840_FINAL.jpg', 'public/canon/characters/newborn-anaadhi.jpg'],
  ['production/references/characters/anaadhi/age_body/P1-C2A/CHR-ANAADHI_AGE_10_AGE-BODY-REF-01.png', 'public/canon/characters/child-anaadhi.png'],
  ['production/references/locations/LOC-012/LOC-012_MASTER-01_Bhaigaara-Root-Shelter_3840x1600_FINAL.jpg', 'public/canon/locations/bhaigaara-ecology.jpg'],
];

await Promise.all(
  assets.map(async ([source, destination]) => {
    const sourcePath = resolve(repositoryRoot, source);
    const destinationPath = resolve(remotionRoot, destination);
    await mkdir(dirname(destinationPath), {recursive: true});
    await copyFile(sourcePath, destinationPath);
  }),
);

await writeFile(
  resolve(remotionRoot, 'public/canon/ASSET_PROVENANCE.json'),
  `${JSON.stringify(
    {
      generated_by: 'scripts/sync-canon-assets.mjs',
      policy: 'Copies existing canonical GitHub sources only; no media generation.',
      assets: assets.map(([source, destination]) => ({source, destination})),
    },
    null,
    2,
  )}\n`,
  'utf8',
);

console.log(`Synced ${assets.length} canonical assets.`);
