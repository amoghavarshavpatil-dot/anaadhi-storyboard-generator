export type MotionMode =
  | 'STATIC'
  | 'SLOW_PUSH_IN'
  | 'SLOW_PULL_OUT'
  | 'PAN_LEFT'
  | 'PAN_RIGHT'
  | 'TILT_UP'
  | 'TILT_DOWN'
  | 'CUSTOM';

export type ShotSpec = {
  sceneId: string;
  shotId: string;
  revisionId: string;
  imagePath: string | null;
  durationSeconds: number;
  motionMode: MotionMode;
  screenDirection: 'LEFT_TO_RIGHT' | 'RIGHT_TO_LEFT' | 'NEUTRAL' | 'AXIS_LOCKED' | 'REDRAFTABLE';
  startScale?: number;
  endScale?: number;
  startX?: number;
  endX?: number;
  startY?: number;
  endY?: number;
};

export type AudioStem = {
  path: string;
  fromSeconds?: number;
  volume?: number;
};

export type SceneSpec = {
  sceneId: string;
  sourceSceneId?: string;
  editorialSegmentId?: string;
  revisionId: string;
  status: 'SPEC_DRAFT' | 'SPEC_READY' | 'GENERATED' | 'REVIEW' | 'LOCKED_PICTURE' | 'FINAL';
  shots: ShotSpec[];
  dialogue?: AudioStem[];
  bgmSfx?: AudioStem[];
};

export type MasterTimeline = {
  width: number;
  height: number;
  fps: number;
  lockedAudioPrefixSeconds: number;
  scenes: SceneSpec[];
};

export type AnaadhiAssemblyProps = {
  shots: Array<{
    shotId: string;
    source: string;
    durationInFrames: number;
    trimBefore?: number;
    volume?: number;
  }>;
};
