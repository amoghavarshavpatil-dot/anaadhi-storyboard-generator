export type CanonMotionMode =
  | 'STATIC'
  | 'SLOW_PUSH_IN'
  | 'SLOW_PULL_OUT'
  | 'PAN_LEFT'
  | 'PAN_RIGHT'
  | 'TILT_UP'
  | 'TILT_DOWN';

export type CanonScreenDirection =
  | 'LEFT_TO_RIGHT'
  | 'RIGHT_TO_LEFT'
  | 'NEUTRAL'
  | 'AXIS_LOCKED'
  | 'REDRAFTABLE';

export type CanonShot = {
  readonly sceneId: string;
  readonly shotId: string;
  readonly revisionId: string;
  readonly purpose: string;
  readonly prompt: string;
  readonly framing: string;
  readonly durationSeconds: number;
  readonly motionMode: CanonMotionMode;
  readonly screenDirection: CanonScreenDirection;
  readonly characters: readonly string[];
  readonly props: readonly string[];
  readonly continuityAnchor: string;
};

export type CanonScene = {
  readonly sceneId: string;
  readonly revisionId: string;
  readonly heading: string;
  readonly shots: readonly CanonShot[];
};
