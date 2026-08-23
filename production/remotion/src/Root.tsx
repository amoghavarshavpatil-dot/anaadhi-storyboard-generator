import React from 'react';
import {Composition, Folder} from 'remotion';
import {
  AnaadhiStoryboardAudiobook,
  getDurationFramesForEditorialOrder,
  getDurationFramesForRange,
} from './AnaadhiStoryboardAudiobook';
import {SC001SC005Cut} from './SC001SC005Cut';
import {durationInFramesForScene, sc001, sc001005DurationInFrames, sc002, sc003, sc004, sc005} from './canon/scene-data';
import {SC001} from './scenes/SC001';
import {SC002} from './scenes/SC002';
import {SC003} from './scenes/SC003';
import {SC004} from './scenes/SC004';
import {SC005} from './scenes/SC005';

const FullFeature = () => <AnaadhiStoryboardAudiobook timelineMode="EDITORIAL_LOCKED" />;
const SourceReview01 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={1} endScene={20} />;
const SourceReview02 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={21} endScene={40} />;
const SourceReview03 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={41} endScene={60} />;
const SourceReview04 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={61} endScene={80} />;
const SourceReview05 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={81} endScene={100} />;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ANAADHI-SC001-SC005-SOURCE-REVIEW-4K-SCOPE"
        component={SC001SC005Cut}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={sc001005DurationInFrames(30)}
        defaultProps={{}}
      />
      <Folder name="ANAADHI-SC001-SC005">
        <Composition
          id="ANAADHI-SC001-SOURCE-REVIEW"
          component={SC001}
          width={3840}
          height={1600}
          fps={30}
          durationInFrames={durationInFramesForScene(sc001, 30)}
          defaultProps={{}}
        />
        <Composition
          id="ANAADHI-SC002-SOURCE-REVIEW"
          component={SC002}
          width={3840}
          height={1600}
          fps={30}
          durationInFrames={durationInFramesForScene(sc002, 30)}
          defaultProps={{}}
        />
        <Composition
          id="ANAADHI-SC003-SOURCE-REVIEW"
          component={SC003}
          width={3840}
          height={1600}
          fps={30}
          durationInFrames={durationInFramesForScene(sc003, 30)}
          defaultProps={{}}
        />
        <Composition
          id="ANAADHI-SC004-SOURCE-REVIEW"
          component={SC004}
          width={3840}
          height={1600}
          fps={30}
          durationInFrames={durationInFramesForScene(sc004, 30)}
          defaultProps={{}}
        />
        <Composition
          id="ANAADHI-SC005-SOURCE-REVIEW"
          component={SC005}
          width={3840}
          height={1600}
          fps={30}
          durationInFrames={durationInFramesForScene(sc005, 30)}
          defaultProps={{}}
        />
      </Folder>
      <Composition
        id="ANAADHI-STORYBOARD-AUDIOBOOK-4K-SCOPE"
        component={FullFeature}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForEditorialOrder(30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI-SOURCE-REVIEW-01"
        component={SourceReview01}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(1, 20, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI-SOURCE-REVIEW-02"
        component={SourceReview02}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(21, 40, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI-SOURCE-REVIEW-03"
        component={SourceReview03}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(41, 60, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI-SOURCE-REVIEW-04"
        component={SourceReview04}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(61, 80, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI-SOURCE-REVIEW-05"
        component={SourceReview05}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(81, 100, 30)}
        defaultProps={{}}
      />
    </>
  );
};
