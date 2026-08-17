import React from 'react';
import {Composition} from 'remotion';
import {AnaadhiStoryboardAudiobook, getDurationFramesForRange} from './AnaadhiStoryboardAudiobook';

const FullFeature = () => <AnaadhiStoryboardAudiobook startScene={1} endScene={100} />;
const Reel01 = () => <AnaadhiStoryboardAudiobook startScene={1} endScene={20} />;
const Reel02 = () => <AnaadhiStoryboardAudiobook startScene={21} endScene={40} />;
const Reel03 = () => <AnaadhiStoryboardAudiobook startScene={41} endScene={60} />;
const Reel04 = () => <AnaadhiStoryboardAudiobook startScene={61} endScene={80} />;
const Reel05 = () => <AnaadhiStoryboardAudiobook startScene={81} endScene={100} />;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ANAADHI_STORYBOARD_AUDIOBOOK_4K_SCOPE"
        component={FullFeature}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(1, 100, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_REEL_01"
        component={Reel01}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(1, 20, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_REEL_02"
        component={Reel02}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(21, 40, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_REEL_03"
        component={Reel03}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(41, 60, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_REEL_04"
        component={Reel04}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(61, 80, 30)}
        defaultProps={{}}
      />
      <Composition
        id="ANAADHI_REEL_05"
        component={Reel05}
        width={3840}
        height={1600}
        fps={30}
        durationInFrames={getDurationFramesForRange(81, 100, 30)}
        defaultProps={{}}
      />
    </>
  );
};
