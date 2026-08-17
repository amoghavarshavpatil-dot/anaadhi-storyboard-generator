import React from 'react';
import {
  AbsoluteFill,
  CanvasImage,
  Easing,
  Interactive,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {Audio} from '@remotion/media';
import {editorialSequenceKeys} from './data/editorialSequence';
import {masterTimeline} from './data/masterTimeline';
import type {MotionMode, SceneSpec, ShotSpec} from './types';

const motionValues = (mode: MotionMode) => {
  switch (mode) {
    case 'SLOW_PUSH_IN':
      return {startScale: 1, endScale: 1.06, startX: 0, endX: 0, startY: 0, endY: 0};
    case 'SLOW_PULL_OUT':
      return {startScale: 1.06, endScale: 1, startX: 0, endX: 0, startY: 0, endY: 0};
    case 'PAN_LEFT':
      return {startScale: 1.04, endScale: 1.04, startX: 40, endX: -40, startY: 0, endY: 0};
    case 'PAN_RIGHT':
      return {startScale: 1.04, endScale: 1.04, startX: -40, endX: 40, startY: 0, endY: 0};
    case 'TILT_UP':
      return {startScale: 1.04, endScale: 1.04, startX: 0, endX: 0, startY: 35, endY: -35};
    case 'TILT_DOWN':
      return {startScale: 1.04, endScale: 1.04, startX: 0, endX: 0, startY: -35, endY: 35};
    default:
      return {startScale: 1, endScale: 1, startX: 0, endX: 0, startY: 0, endY: 0};
  }
};

const StoryboardShot: React.FC<{shot: ShotSpec}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durationInFrames = Math.max(1, Math.round(shot.durationSeconds * fps));
  const motionEndFrame = Math.max(1, durationInFrames - 1);
  const fallback = motionValues(shot.motionMode);
  const startScale = shot.startScale ?? fallback.startScale;
  const endScale = shot.endScale ?? fallback.endScale;
  const startX = shot.startX ?? fallback.startX;
  const endX = shot.endX ?? fallback.endX;
  const startY = shot.startY ?? fallback.startY;
  const endY = shot.endY ?? fallback.endY;

  if (!shot.imagePath) {
    return (
      <AbsoluteFill style={{backgroundColor: 'black', justifyContent: 'center', alignItems: 'center'}}>
        <Interactive.Div name={`${shot.shotId} missing visual`} style={{fontSize: 54, color: 'white'}}>
          {shot.shotId} — visual not materialized
        </Interactive.Div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: 'black'}}>
      <CanvasImage
        name={shot.shotId}
        src={staticFile(shot.imagePath)}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          scale: interpolate(frame, [0, motionEndFrame], [startScale, endScale], {
            easing: Easing.bezier(0.16, 1, 0.3, 1),
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
            output: 'perceptual-scale',
          }),
          translate: interpolate(
            frame,
            [0, motionEndFrame],
            [`${startX}px ${startY}px`, `${endX}px ${endY}px`],
            {
              easing: Easing.bezier(0.16, 1, 0.3, 1),
              extrapolateLeft: 'clamp',
              extrapolateRight: 'clamp',
            },
          ),
        }}
      />
    </AbsoluteFill>
  );
};

const Scene: React.FC<{scene: SceneSpec}> = ({scene}) => {
  const {fps} = useVideoConfig();
  let shotStart = 0;

  return (
    <AbsoluteFill>
      {scene.shots.map((shot) => {
        const durationInFrames = Math.max(1, Math.round(shot.durationSeconds * fps));
        const start = shotStart;
        shotStart += durationInFrames;
        return (
          <Sequence key={`${shot.shotId}-${shot.revisionId}`} name={shot.shotId} from={start} durationInFrames={durationInFrames}>
            <StoryboardShot shot={shot} />
          </Sequence>
        );
      })}
      {scene.dialogue?.map((stem, index) => (
        <Audio
          key={`dialogue-${index}-${stem.path}`}
          src={staticFile(stem.path)}
          from={Math.round((stem.fromSeconds ?? 0) * fps)}
          volume={stem.volume ?? 1}
        />
      ))}
      {scene.bgmSfx?.map((stem, index) => (
        <Audio
          key={`bgm-sfx-${index}-${stem.path}`}
          src={staticFile(stem.path)}
          from={Math.round((stem.fromSeconds ?? 0) * fps)}
          volume={stem.volume ?? 1}
        />
      ))}
    </AbsoluteFill>
  );
};

const sourceSceneNumber = (scene: SceneSpec) =>
  Number((scene.sourceSceneId ?? scene.sceneId).replace('SC', ''));

const editorialKey = (scene: SceneSpec) => scene.editorialSegmentId ?? scene.sceneId;

export const getScenesInRange = (startScene = 1, endScene = 100) =>
  masterTimeline.scenes.filter((scene) => {
    const n = sourceSceneNumber(scene);
    return n >= startScene && n <= endScene;
  });

export const getScenesInEditorialOrder = () => {
  const byKey = new Map(masterTimeline.scenes.map((scene) => [editorialKey(scene), scene]));
  return editorialSequenceKeys
    .map((key) => byKey.get(key))
    .filter((scene): scene is SceneSpec => Boolean(scene));
};

const durationSecondsForScenes = (scenes: SceneSpec[]) =>
  scenes.reduce(
    (sceneTotal, scene) =>
      sceneTotal + scene.shots.reduce((shotTotal, shot) => shotTotal + shot.durationSeconds, 0),
    0,
  );

export const getDurationFramesForRange = (startScene = 1, endScene = 100, fps = 30) =>
  Math.max(1, Math.round(durationSecondsForScenes(getScenesInRange(startScene, endScene)) * fps));

export const getDurationFramesForEditorialOrder = (fps = 30) =>
  Math.max(1, Math.round(durationSecondsForScenes(getScenesInEditorialOrder()) * fps));

export const AnaadhiStoryboardAudiobook: React.FC<{
  timelineMode?: 'EDITORIAL_LOCKED' | 'SOURCE_RANGE';
  startScene?: number;
  endScene?: number;
}> = ({
  timelineMode = 'EDITORIAL_LOCKED',
  startScene = 1,
  endScene = 100,
}) => {
  const {fps} = useVideoConfig();
  const scenes =
    timelineMode === 'EDITORIAL_LOCKED'
      ? getScenesInEditorialOrder()
      : getScenesInRange(startScene, endScene);
  let sceneStart = 0;

  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {scenes.map((scene) => {
        const durationInFrames = Math.max(
          1,
          Math.round(scene.shots.reduce((sum, shot) => sum + shot.durationSeconds, 0) * fps),
        );
        const start = sceneStart;
        sceneStart += durationInFrames;
        const sequenceName = scene.editorialSegmentId ?? scene.sceneId;
        return (
          <Sequence key={`${sequenceName}-${scene.revisionId}`} name={sequenceName} from={start} durationInFrames={durationInFrames}>
            <Scene scene={scene} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
