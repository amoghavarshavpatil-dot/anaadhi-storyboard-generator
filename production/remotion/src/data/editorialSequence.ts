export type EditorialSequenceKey =
  | `SC${string}`
  | 'SC074A'
  | 'SC074B'
  | 'SC094A'
  | 'SC094B'
  | 'SC099A'
  | 'SC099B';

const sceneKey = (sceneNumber: number) => `SC${String(sceneNumber).padStart(3, '0')}`;

const sceneRange = (start: number, end: number) =>
  Array.from({length: end - start + 1}, (_, index) => sceneKey(start + index));

export const editorialSequenceKeys: string[] = [
  ...sceneRange(1, 5),
  'SC099B',
  'SC100',
  'SC094B',
  'SC095',
  ...sceneRange(60, 73),
  'SC074A',
  ...sceneRange(6, 59),
  'SC074B',
  ...sceneRange(75, 93),
  'SC094A',
  ...sceneRange(96, 98),
  'SC099A',
];

export const editorialSplitSegments = {
  SC074A: {
    sourceSceneId: 'SC074',
    start: 'SCENE_START',
    endAnchor: 'No triumph—only immediate terror.',
  },
  SC074B: {
    sourceSceneId: 'SC074',
    startSpeaker: 'AARATHI',
    startDialogue: 'Manire!',
    end: 'SCENE_END',
  },
  SC094A: {
    sourceSceneId: 'SC094',
    start: 'SCENE_START',
    endSpeaker: 'UNNATH',
    endDialogue: 'That is the problem.',
  },
  SC094B: {
    sourceSceneId: 'SC094',
    startAnchor: 'Manimantharaa’s members raise weapons and police respond.',
    end: 'SCENE_END',
  },
  SC099A: {
    sourceSceneId: 'SC099',
    start: 'SCENE_START',
    endSpeaker: 'ANAADHI (V.O.)',
    endDialogue: 'The relationship still needs a road.',
  },
  SC099B: {
    sourceSceneId: 'SC099',
    startAnchor:
      'In the independent secure medical unit, Anaadhi sits at a desk with no covered mirrors or carved marks.',
    endAnchor: 'His pen reaches: MALLAYYA. CUT TO:',
  },
} as const;

export const editorialSequenceEntryCount = editorialSequenceKeys.length;
