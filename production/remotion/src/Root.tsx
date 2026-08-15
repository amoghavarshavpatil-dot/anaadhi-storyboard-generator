import React from 'react';
import {Composition} from 'remotion';
import {AnaadhiAssembly} from './AnaadhiAssembly';
import {
  ANAADHI_MASTER_HEIGHT,
  ANAADHI_MASTER_WIDTH,
  ANAADHI_WORKING_FPS,
  BOOTSTRAP_DURATION_IN_FRAMES,
} from './config';
import type {AnaadhiAssemblyProps} from './types';

const EMPTY_SHOTS: AnaadhiAssemblyProps = {shots: []};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="ANAADHI-MASTER-ASSEMBLY"
      component={AnaadhiAssembly}
      width={ANAADHI_MASTER_WIDTH}
      height={ANAADHI_MASTER_HEIGHT}
      fps={ANAADHI_WORKING_FPS}
      durationInFrames={BOOTSTRAP_DURATION_IN_FRAMES}
      defaultProps={EMPTY_SHOTS}
    />
  );
};
