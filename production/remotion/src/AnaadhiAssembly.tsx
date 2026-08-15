import React from 'react';
import {AbsoluteFill, Sequence} from 'remotion';
import {Video} from '@remotion/media';
import type {AnaadhiAssemblyProps} from './types';

export const AnaadhiAssembly: React.FC<AnaadhiAssemblyProps> = ({shots}) => {
  let cursor = 0;

  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {shots.map((shot) => {
        const from = cursor;
        cursor += shot.durationInFrames;

        return (
          <Sequence
            key={shot.shotId}
            from={from}
            durationInFrames={shot.durationInFrames}
            layout="absolute-fill"
          >
            <Video
              src={shot.source}
              durationInFrames={shot.durationInFrames}
              trimBefore={shot.trimBefore ?? 0}
              volume={shot.volume ?? 1}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
