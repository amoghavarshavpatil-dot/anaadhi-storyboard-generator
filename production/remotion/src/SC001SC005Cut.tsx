import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {CanonSceneCut} from './canon/CanonSceneCut';
import {durationInFramesForScene, scenes001005} from './canon/scene-data';

export const SC001SC005Cut: React.FC = () => {
  const {fps} = useVideoConfig();
  let cursor = 0;

  return (
    <AbsoluteFill style={{backgroundColor: '#020303'}}>
      {scenes001005.map((scene) => {
        const durationInFrames = durationInFramesForScene(scene, fps);
        const from = cursor;
        cursor += durationInFrames;
        return (
          <Sequence
            key={`${scene.sceneId}-${scene.revisionId}`}
            name={scene.sceneId}
            from={from}
            durationInFrames={durationInFrames}
            premountFor={Math.min(30, durationInFrames)}
          >
            <CanonSceneCut scene={scene} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
