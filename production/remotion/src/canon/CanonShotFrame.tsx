import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {CharacterLayer, CinematicGrade, EnvironmentLayer} from './Visuals';
import {PerceptionOverlay, PropOverlayLayer} from './PropOverlays';
import type {CanonMotionMode, CanonShot} from './types';

const cameraRanges = (mode: CanonMotionMode) => {
  switch (mode) {
    case 'SLOW_PUSH_IN':
      return {scale: [1, 1.055], x: [0, 0], y: [0, 0]};
    case 'SLOW_PULL_OUT':
      return {scale: [1.055, 1], x: [0, 0], y: [0, 0]};
    case 'PAN_LEFT':
      return {scale: [1.04, 1.04], x: [60, -60], y: [0, 0]};
    case 'PAN_RIGHT':
      return {scale: [1.04, 1.04], x: [-60, 60], y: [0, 0]};
    case 'TILT_UP':
      return {scale: [1.04, 1.04], x: [0, 0], y: [42, -42]};
    case 'TILT_DOWN':
      return {scale: [1.04, 1.04], x: [0, 0], y: [-42, 42]};
    default:
      return {scale: [1, 1], x: [0, 0], y: [0, 0]};
  }
};

export const CanonShotFrame: React.FC<{readonly shot: CanonShot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const ranges = cameraRanges(shot.motionMode);
  const endFrame = Math.max(1, durationInFrames - 1);
  const impact = shot.purpose.toLowerCase().includes('thud')
    ? Math.sin(frame * 2.8) * Math.max(0, 24 - frame * 2)
    : 0;
  const fadeIn = interpolate(frame, [0, Math.min(6, endFrame)], [0.6, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: '#020303', overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          opacity: fadeIn,
          scale: interpolate(frame, [0, endFrame], ranges.scale, {
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            output: 'perceptual-scale',
          }),
          translate: interpolate(
            frame,
            [0, endFrame],
            [`${ranges.x[0] + impact}px ${ranges.y[0]}px`, `${ranges.x[1]}px ${ranges.y[1]}px`],
            {
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            },
          ),
        }}
      >
        <EnvironmentLayer shot={shot} />
        <CharacterLayer shot={shot} />
        <PropOverlayLayer shot={shot} />
        <PerceptionOverlay shot={shot} />
      </AbsoluteFill>
      <CinematicGrade shot={shot} />
    </AbsoluteFill>
  );
};
