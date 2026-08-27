import type {SceneSpec} from '../types';

export const sc002ApprovedScene: SceneSpec = {
  sceneId: 'SC002',
  revisionId: 'V001',
  status: 'SPEC_READY',
  shots: [
    {
      sceneId: 'SC002',
      shotId: 'SC002_SH001',
      revisionId: 'V001',
      imagePath: 'shots/SC002/SC002_SH001_V001.png',
      durationSeconds: 3,
      motionMode: 'STATIC',
      screenDirection: 'AXIS_LOCKED',
    },
  ],
};
