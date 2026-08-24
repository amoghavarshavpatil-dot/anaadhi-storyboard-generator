import React from 'react';
import {Composition} from 'remotion';
import {
  AnaadhiStoryboardAudiobook,
  getDurationFramesForEditorialOrder,
  getDurationFramesForRange,
} from './AnaadhiStoryboardAudiobook';

const FullFeature = () => <AnaadhiStoryboardAudiobook timelineMode="EDITORIAL_LOCKED" />;
const Scene001Approved = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={1} endScene={1} />;
const SourceReview01 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={1} endScene={20} />;
const SourceReview02 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={21} endScene={40} />;
const SourceReview03 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={41} endScene={60} />;
const SourceReview04 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={61} endScene={80} />;
const SourceReview05 = () => <AnaadhiStoryboardAudiobook timelineMode="SOURCE_RANGE" startScene={81} endScene={100} />;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ANAADHI_STORYBOARD_AUDIOBOOK_4K_SCOPE"
        component={FullFeature}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForEditorialOrder(30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_SC001_APPROVED_V001"
        component={Scene001Approved}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(1, 1, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_SOURCE_REVIEW_01"
        component={SourceReview01}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(1, 20, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_SOURCE_REVIEW_02"
        component={SourceReview02}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(21, 40, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_SOURCE_REVIEW_03"
        component={SourceReview03}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(41, 60, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_SOURCE_REVIEW_04"
        component={SourceReview04}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(61, 80, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_SOURCE_REVIEW_05"
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
