import sc002Json from '../../shot_specs/SC002/SC002_SHOT_PACKAGE.json';
import sc003Json from '../../shot_specs/SC003/SC003_SHOT_PACKAGE.json';
import sc004Json from '../../shot_specs/SC004/SC004_SHOT_PACKAGE.json';
import sc005Json from '../../shot_specs/SC005/SC005_SHOT_PACKAGE.json';
import type {
  CanonMotionMode,
  CanonScene,
  CanonScreenDirection,
  CanonShot,
} from './types';

type RawShot = {
  readonly shot_id: string;
  readonly purpose?: string;
  readonly prompt?: string;
  readonly visual_prompt?: string;
  readonly framing?: string;
  readonly duration_seconds?: number;
  readonly motion_mode?: string;
  readonly screen_direction?: string;
  readonly continuity_anchor?: string;
  readonly character_bindings?: readonly string[];
  readonly prop_bindings?: readonly string[];
  readonly composition?: {
    readonly shot_size?: string;
    readonly screen_direction?: string;
  };
  readonly bindings?: {
    readonly characters?: readonly string[];
    readonly props?: readonly string[];
  };
  readonly generation?: {
    readonly visual_prompt?: string;
    readonly continuity_anchor_summary?: string;
  };
  readonly remotion?: {
    readonly duration_seconds?: number;
    readonly motion_mode?: string;
  };
};

type RawScenePackage = {
  readonly scene_id: string;
  readonly revision_id: string;
  readonly screenplay_source?: {
    readonly heading?: string;
  };
  readonly shots: readonly RawShot[];
};

const motionModes = new Set<CanonMotionMode>([
  'STATIC',
  'SLOW_PUSH_IN',
  'SLOW_PULL_OUT',
  'PAN_LEFT',
  'PAN_RIGHT',
  'TILT_UP',
  'TILT_DOWN',
]);

const screenDirections = new Set<CanonScreenDirection>([
  'LEFT_TO_RIGHT',
  'RIGHT_TO_LEFT',
  'NEUTRAL',
  'AXIS_LOCKED',
  'REDRAFTABLE',
]);

const normalizeMotionMode = (
  raw: string | undefined,
  framing: string,
  screenDirection: CanonScreenDirection,
): CanonMotionMode => {
  if (raw && motionModes.has(raw as CanonMotionMode)) {
    return raw as CanonMotionMode;
  }

  const lower = framing.toLowerCase();
  if (lower.includes('wide') || lower.includes('depth')) {
    return 'SLOW_PUSH_IN';
  }
  if (screenDirection === 'LEFT_TO_RIGHT') {
    return 'PAN_RIGHT';
  }
  if (screenDirection === 'RIGHT_TO_LEFT') {
    return 'PAN_LEFT';
  }
  return 'STATIC';
};

const normalizeScreenDirection = (raw?: string): CanonScreenDirection =>
  raw && screenDirections.has(raw as CanonScreenDirection)
    ? (raw as CanonScreenDirection)
    : 'NEUTRAL';

const inferCharacters = (prompt: string, bound: readonly string[]) => {
  if (bound.length > 0) {
    return [...new Set(bound)];
  }

  const lower = prompt.toLowerCase();
  const inferred: string[] = [];
  if (lower.includes('anaadhi')) inferred.push('ANAADHI');
  if (lower.includes('newborn')) inferred.push('NEWBORN_ANAADHI_REPRESENTED');
  if (lower.includes('child')) inferred.push('CHILD_ANAADHI');
  if (lower.includes('aarathi')) inferred.push('AARATHI_REAL');
  if (lower.includes('semmaa')) inferred.push('SEMMAA');
  if (lower.includes('police commander')) inferred.push('POLICE_COMMANDER');
  if (lower.includes('medical specialist') || lower.includes('specialist')) {
    inferred.push('MEDICAL_SPECIALIST');
  }
  if (lower.includes('sarjanya')) inferred.push('SARJANYA_OFFICER');
  if (lower.includes('allied gangster') || lower.includes('gangster')) {
    inferred.push('ALLIED_GANGSTER');
  }
  return [...new Set(inferred)];
};

const adaptPackage = (rawValue: unknown): CanonScene => {
  const raw = rawValue as RawScenePackage;
  const shots = raw.shots.map((shot): CanonShot => {
    const framing = shot.framing ?? shot.composition?.shot_size ?? 'cinematic insert';
    const screenDirection = normalizeScreenDirection(
      shot.screen_direction ?? shot.composition?.screen_direction,
    );
    const prompt = shot.prompt ?? shot.visual_prompt ?? shot.generation?.visual_prompt ?? shot.purpose ?? '';
    const boundCharacters = shot.character_bindings ?? shot.bindings?.characters ?? [];

    return {
      sceneId: raw.scene_id,
      shotId: shot.shot_id,
      revisionId: raw.revision_id,
      purpose: shot.purpose ?? '',
      prompt,
      framing,
      durationSeconds: shot.duration_seconds ?? shot.remotion?.duration_seconds ?? 3,
      motionMode: normalizeMotionMode(
        shot.motion_mode ?? shot.remotion?.motion_mode,
        framing,
        screenDirection,
      ),
      screenDirection,
      characters: inferCharacters(prompt, boundCharacters),
      props: shot.prop_bindings ?? shot.bindings?.props ?? [],
      continuityAnchor:
        shot.continuity_anchor ?? shot.generation?.continuity_anchor_summary ?? 'physical cabin continuity',
    };
  });

  return {
    sceneId: raw.scene_id,
    revisionId: raw.revision_id,
    heading: raw.screenplay_source?.heading ?? raw.scene_id,
    shots,
  };
};

const sc001Shots: readonly CanonShot[] = [
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH001',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Establish Bhaigaara forest, black rain and raised cabin under covert encirclement',
    prompt:
      'Pre-dawn Karnataka Western Ghats evolved a century into the future, black rain, enormous roots, hidden sensors, raised timber cabin, black-kite-shaped propellerless police drones and camouflaged medical transports.',
    framing: 'very wide anamorphic establishing',
    durationSeconds: 6,
    motionMode: 'SLOW_PUSH_IN',
    screenDirection: 'NEUTRAL',
    characters: [],
    props: [],
    continuityAnchor: 'ENV-CAB-008 exterior / WC001-A',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH002',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Reveal the four-force perimeter and shared Paraane visual language',
    prompt:
      'Kendhalaa Police, Sarjanya, Allied Gangsters and Paraane medical personnel surround the raised cabin under black rain.',
    framing: 'wide lateral operation tableau',
    durationSeconds: 6,
    motionMode: 'PAN_RIGHT',
    screenDirection: 'LEFT_TO_RIGHT',
    characters: ['POLICE_COMMANDER', 'SARJANYA_OFFICER', 'MEDICAL_SPECIALIST', 'ALLIED_GANGSTER'],
    props: ['POLICE_SHIELDS'],
    continuityAnchor: 'ENV-CAB-008 exterior / four-force perimeter',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH003',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Thermal confirmation: one body inside',
    prompt:
      'Wet tactical wrist display in pre-dawn rain shows the thermal silhouette of one human body inside the raised wooden cabin.',
    framing: 'medium close insert on Police Commander wrist',
    durationSeconds: 5,
    motionMode: 'STATIC',
    screenDirection: 'NEUTRAL',
    characters: ['POLICE_COMMANDER'],
    props: ['POLICE_COMMANDER_WRIST_DISPLAY'],
    continuityAnchor: 'one body inside',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH004',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Command exchange without visible lip-sync',
    prompt:
      'Police Commander, Sarjanya officer and Medical Specialist communicate under black rain around the cabin perimeter in restrained tactical profiles.',
    framing: 'intercut tactical profiles',
    durationSeconds: 7,
    motionMode: 'PAN_LEFT',
    screenDirection: 'AXIS_LOCKED',
    characters: ['POLICE_COMMANDER', 'SARJANYA_OFFICER', 'MEDICAL_SPECIALIST'],
    props: [],
    continuityAnchor: 'four-force perimeter / no cabin entry yet',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH005',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Violent THUD shakes cabin and perimeter snaps to aim',
    prompt:
      'Raised forest cabin shudders violently from an unseen internal impact; black rain scatters from roof edges; no shots fired.',
    framing: 'medium-wide cabin exterior',
    durationSeconds: 3,
    motionMode: 'SLOW_PUSH_IN',
    screenDirection: 'NEUTRAL',
    characters: [],
    props: [],
    continuityAnchor: 'pre-breach exterior',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH006',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'First interior reveal of sedated Anaadhi',
    prompt:
      'Inside the raised timber cabin Anaadhi, age 27 and 193 cm, lies face-down and sedated on the wooden floor, reaching toward the split floorboard with an empty injector nearby.',
    framing: 'low floor-level wide/medium',
    durationSeconds: 8,
    motionMode: 'SLOW_PUSH_IN',
    screenDirection: 'NEUTRAL',
    characters: ['ANAADHI'],
    props: ['EMPTY_INJECTOR', 'SPLIT_FLOORBOARD'],
    continuityAnchor: 'ENV-CAB-008 interior / pre-breach',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH007',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Five Parallel Earth fracture montage',
    prompt:
      'Anaadhi vision fractures into five realities: blue-sun cabin, cabin burning while snow rises, Anaadhi dead before the operation, untouched Anaadhi behind glass and futuristic forest city with luminous gopura towers.',
    framing: 'subject-anchored reality shards',
    durationSeconds: 10,
    motionMode: 'SLOW_PULL_OUT',
    screenDirection: 'REDRAFTABLE',
    characters: ['ANAADHI'],
    props: [],
    continuityAnchor: 'TP001 / SB001 / GF10 / represented only',
  },
  {
    sceneId: 'SC001',
    shotId: 'SC001_SH008',
    revisionId: 'R001-REMOTION-SOURCE-REVIEW',
    purpose: 'Return to present; fingers reach floor crack',
    prompt:
      'Anaadhi weak fingers reach the split in the wooden floor; empty injector nearby; body remains face-down; no other character is inside.',
    framing: 'extreme close hand-to-floor crack',
    durationSeconds: 8,
    motionMode: 'PAN_RIGHT',
    screenDirection: 'NEUTRAL',
    characters: ['ANAADHI'],
    props: ['EMPTY_INJECTOR', 'SPLIT_FLOORBOARD'],
    continuityAnchor: 'RST01 physical interior restored',
  },
];

export const sc001: CanonScene = {
  sceneId: 'SC001',
  revisionId: 'R001-REMOTION-SOURCE-REVIEW',
  heading: 'EXT./INT. BHAIGAARA BUFFER FOREST – ANAADHI RAISED CABIN – PRE-DAWN',
  shots: sc001Shots,
};

export const sc002 = adaptPackage(sc002Json);
export const sc003 = adaptPackage(sc003Json);
export const sc004 = adaptPackage(sc004Json);
export const sc005 = adaptPackage(sc005Json);

export const scenes001005: readonly CanonScene[] = [sc001, sc002, sc003, sc004, sc005];

export const durationInFramesForScene = (scene: CanonScene, fps = 30) =>
  scene.shots.reduce(
    (sum, shot) => sum + Math.max(1, Math.round(shot.durationSeconds * fps)),
    0,
  );

export const sc001005DurationInFrames = (fps = 30) =>
  scenes001005.reduce((sum, scene) => sum + durationInFramesForScene(scene, fps), 0);
