import type {MasterTimeline} from '../types';
import {sc001ApprovedScene} from './sc001Approved';

export const masterTimeline: MasterTimeline = {
  width: 3840,
  height: 1600,
  fps: 30,
  lockedAudioPrefixSeconds: 134.293333,
  scenes: [sc001ApprovedScene],
};

export const totalTimelineSeconds = masterTimeline.scenes.reduce(
  (sceneTotal, scene) =>
    sceneTotal + scene.shots.reduce((shotTotal, shot) => shotTotal + shot.durationSeconds, 0),
  0,
);
