import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {CanonShotFrame} from './CanonShotFrame';
import type {CanonScene} from './types';

export const CanonSceneCut: React.FC<{readonly scene: CanonScene}> = ({scene}) => {
  const {fps} = useVideoConfig();
  let cursor = 0;

  return (
    <AbsoluteFill style={{backgroundColor: '#020303'}}>
      {scene.shots.map((shot) => {
        const durationInFrames = Math.max(1, Math.round(shot.durationSeconds * fps));
        const from = cursor;
        cursor += durationInFrames;

        return (
          <Sequence
            key={`${shot.shotId}-${shot.revisionId}`}
            name={shot.shotId}
            from={from}
            durationInFrames={durationInFrames}
            premountFor={Math.min(15, durationInFrames)}
          >
            <CanonShotFrame shot={shot} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
