import React from 'react';
import {AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {CanonScreenDirection, CanonShot} from './types';

const characterAssets: Readonly<Record<string, string>> = {
  ANAADHI: 'canon/characters/anaadhi.jpg',
  ANAADHI_REPRESENTED_POV: 'canon/characters/anaadhi.jpg',
  AARATHI: 'canon/characters/aarathi.jpg',
  AARATHI_REAL: 'canon/characters/aarathi.jpg',
  AARATHI_PARALLEL_MEDICAL: 'canon/characters/aarathi-medical.jpg',
  MEDICAL_SPECIALIST: 'canon/characters/medical-specialist.jpg',
  POLICE_COMMANDER: 'canon/characters/police-commander.jpg',
  SARJANYA_OFFICER: 'canon/characters/sarjanya-officer.jpg',
  SEMMAA: 'canon/characters/semmaa.jpg',
  ALLIED_GANGSTER: 'canon/characters/allied-gangster.jpg',
  NEWBORN_ANAADHI_FLASH: 'canon/characters/newborn-anaadhi.jpg',
  NEWBORN_ANAADHI_REPRESENTED: 'canon/characters/newborn-anaadhi.jpg',
  CHILD_ANAADHI: 'canon/characters/child-anaadhi.png',
};

const seedFrom = (value: string) =>
  [...value].reduce((total, char) => (total * 33 + char.charCodeAt(0)) % 104729, 17);

const directionSign = (direction: CanonScreenDirection) =>
  direction === 'RIGHT_TO_LEFT' ? -1 : direction === 'LEFT_TO_RIGHT' ? 1 : 0;

export const RainLayer: React.FC<{readonly intensity?: number; readonly seed: string}> = ({
  intensity = 1,
  seed,
}) => {
  const frame = useCurrentFrame();
  const baseSeed = seedFrom(seed);
  const drops = Array.from({length: Math.round(34 * intensity)}, (_, index) => {
    const x = (baseSeed * (index + 7) * 17) % 3840;
    const length = 80 + ((baseSeed + index * 71) % 230);
    const speed = 48 + ((baseSeed + index * 29) % 62);
    const top = ((frame * speed + index * 113 + baseSeed) % 1900) - 220;
    const opacity = 0.12 + (((baseSeed + index * 13) % 30) / 100) * intensity;
    return {x, length, top, opacity};
  });

  return (
    <AbsoluteFill style={{overflow: 'hidden', pointerEvents: 'none'}}>
      {drops.map((drop, index) => (
        <div
          key={`${seed}-rain-${index}`}
          style={{
            position: 'absolute',
            left: drop.x,
            top: drop.top,
            width: 3,
            height: drop.length,
            rotate: '12deg',
            opacity: drop.opacity,
            background:
              'linear-gradient(180deg, rgba(123,162,176,0), rgba(157,191,199,0.85), rgba(63,92,98,0))',
            filter: 'blur(0.7px)',
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

const CabinSilhouette: React.FC<{readonly breached: boolean}> = ({breached}) => (
  <div
    style={{
      position: 'absolute',
      left: 1380,
      bottom: 210,
      width: 1500,
      height: 760,
      background: 'linear-gradient(150deg, #161713, #070908 64%)',
      clipPath: 'polygon(0 23%, 22% 23%, 29% 0, 76% 0, 84% 23%, 100% 23%, 100% 100%, 0 100%)',
      boxShadow: '0 80px 160px rgba(0,0,0,0.85)',
      border: '6px solid rgba(87,74,52,0.65)',
    }}
  >
    <div
      style={{
        position: 'absolute',
        left: 550,
        bottom: 0,
        width: 420,
        height: 550,
        background: breached
          ? 'linear-gradient(145deg, rgba(47,65,71,0.86), rgba(2,4,4,0.98))'
          : 'linear-gradient(110deg, #1b1711, #090a08)',
        clipPath: breached
          ? 'polygon(8% 0, 100% 3%, 91% 33%, 100% 61%, 83% 100%, 0 100%, 14% 74%, 0 42%)'
          : undefined,
        border: '5px solid rgba(121,91,50,0.38)',
      }}
    />
    {Array.from({length: 10}, (_, index) => (
      <div
        key={`cabin-board-${index}`}
        style={{
          position: 'absolute',
          left: 70,
          right: 70,
          top: 150 + index * 48,
          height: 4,
          opacity: 0.3,
          background: '#776548',
        }}
      />
    ))}
  </div>
);

const CabinInterior: React.FC<{readonly breached: boolean}> = ({breached}) => (
  <AbsoluteFill
    style={{
      background:
        'radial-gradient(ellipse at 55% 38%, rgba(124,126,99,0.42), transparent 48%), repeating-linear-gradient(0deg, #24241d 0px, #24241d 74px, #45402e 78px, #101312 82px)',
    }}
  >
    <div
      style={{
        position: 'absolute',
        inset: '58% 0 0 0',
        background:
          'repeating-linear-gradient(171deg, #261d14 0px, #261d14 98px, #67482b 102px, #11100d 108px)',
        clipPath: 'polygon(0 12%, 100% 0, 100% 100%, 0 100%)',
      }}
    />
    <div
      style={{
        position: 'absolute',
        left: 120,
        top: 100,
        width: 720,
        height: 1120,
        background: breached
          ? 'radial-gradient(ellipse at 50% 50%, rgba(112,169,180,0.86), rgba(8,13,13,0.94) 75%)'
          : '#080907',
        clipPath: breached
          ? 'polygon(13% 0, 94% 5%, 83% 21%, 100% 43%, 86% 69%, 98% 100%, 8% 96%, 17% 76%, 0 53%, 15% 30%)'
          : undefined,
        border: '7px solid rgba(98,74,47,0.5)',
        boxShadow: 'inset 0 0 140px black, 0 0 90px rgba(84,127,135,0.18)',
      }}
    />
    {breached ? (
      <div
        style={{
          position: 'absolute',
          left: 650,
          top: 1120,
          width: 800,
          height: 260,
          background: 'linear-gradient(135deg, transparent, rgba(120,91,52,0.42), transparent)',
          clipPath: 'polygon(0 80%, 16% 10%, 24% 75%, 41% 2%, 50% 83%, 67% 15%, 75% 85%, 100% 26%, 100% 100%, 0 100%)',
        }}
      />
    ) : null}
  </AbsoluteFill>
);

const CorridorEnvironment: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  return (
    <AbsoluteFill
      style={{
        background:
          'radial-gradient(circle at 50% 48%, rgba(162,153,114,0.18), rgba(7,8,9,0.99) 54%), linear-gradient(180deg, #131516, #030404)',
        scale: interpolate(frame, [0, durationInFrames - 1], [1.04, 1.13], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        }),
      }}
    >
      {Array.from({length: 7}, (_, index) => {
        const inset = index * 210;
        return (
          <div
            key={`corridor-${index}`}
            style={{
              position: 'absolute',
              left: inset,
              right: inset,
              top: 80 + index * 65,
              bottom: 70 + index * 42,
              border: `${18 - index}px solid rgba(156,139,96,${0.24 - index * 0.02})`,
              clipPath: 'polygon(0 0, 100% 0, 88% 100%, 12% 100%)',
            }}
          />
        );
      })}
      {Array.from({length: 6}, (_, index) => (
        <React.Fragment key={`doors-${index}`}>
          <div
            style={{
              position: 'absolute',
              left: 180 + index * 250,
              top: 430 + index * 28,
              width: 150,
              height: 520 - index * 45,
              background: 'linear-gradient(90deg, #080908, #393223, #080908)',
              border: '4px solid rgba(188,159,93,0.35)',
              transform: 'skewX(-7deg)',
            }}
          />
          <div
            style={{
              position: 'absolute',
              right: 180 + index * 250,
              top: 430 + index * 28,
              width: 150,
              height: 520 - index * 45,
              background: 'linear-gradient(90deg, #080908, #393223, #080908)',
              border: '4px solid rgba(188,159,93,0.35)',
              transform: 'skewX(7deg)',
            }}
          />
        </React.Fragment>
      ))}
    </AbsoluteFill>
  );
};

const UniversityLab: React.FC = () => (
  <AbsoluteFill
    style={{
      background:
        'linear-gradient(180deg, rgba(242,247,244,1), rgba(196,216,210,1) 62%, rgba(113,141,137,1))',
    }}
  >
    <div
      style={{
        position: 'absolute',
        left: 240,
        right: 240,
        top: 170,
        height: 820,
        border: '10px solid rgba(35,72,69,0.32)',
        background:
          'repeating-linear-gradient(90deg, rgba(255,255,255,0.62) 0px, rgba(255,255,255,0.62) 260px, rgba(43,92,87,0.18) 264px, rgba(43,92,87,0.18) 272px)',
        boxShadow: '0 40px 100px rgba(22,54,53,0.22)',
      }}
    />
    {Array.from({length: 6}, (_, index) => (
      <div
        key={`lab-bench-${index}`}
        style={{
          position: 'absolute',
          left: 330 + index * 540,
          bottom: 210,
          width: 380,
          height: 300,
          background: 'linear-gradient(180deg, #eef7f4, #7d9a95)',
          borderTop: '18px solid #284e4b',
          boxShadow: '0 36px 60px rgba(20,45,44,0.28)',
        }}
      />
    ))}
  </AbsoluteFill>
);

export const EnvironmentLayer: React.FC<{readonly shot: CanonShot}> = ({shot}) => {
  const text = `${shot.purpose} ${shot.prompt}`.toLowerCase();
  const exterior = shot.sceneId === 'SC001' && Number(shot.shotId.slice(-3)) <= 5;
  const corridor = text.includes('corridor') || text.includes('door-framed');
  const lab = text.includes('university laboratory') || text.includes('university-laboratory');

  if (lab) return <UniversityLab />;
  if (corridor) return <CorridorEnvironment />;

  if (exterior) {
    return (
      <AbsoluteFill style={{backgroundColor: '#020605'}}>
        <Img
          name="Bhaigaara ecology plate"
          src={staticFile('canon/locations/bhaigaara-ecology.jpg')}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            filter: 'brightness(0.48) contrast(1.24) saturate(0.72) hue-rotate(158deg)',
          }}
        />
        <CabinSilhouette breached={false} />
        <RainLayer intensity={1.35} seed={shot.shotId} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill>
      <CabinInterior breached={shot.sceneId !== 'SC001'} />
      <RainLayer intensity={0.34} seed={shot.shotId} />
    </AbsoluteFill>
  );
};

const portraitPosition = (
  index: number,
  count: number,
  direction: CanonScreenDirection,
) => {
  const usableWidth = 3160;
  const spacing = count <= 1 ? 0 : Math.min(820, usableWidth / (count - 1));
  const natural = count <= 1 ? 1920 : 340 + index * spacing;
  const x = direction === 'RIGHT_TO_LEFT' ? 3840 - natural : natural;
  return x;
};

export const CharacterLayer: React.FC<{readonly shot: CanonShot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const text = `${shot.purpose} ${shot.prompt}`.toLowerCase();
  const uniqueCharacters = [...new Set(shot.characters)].filter(
    (character) => characterAssets[character],
  );
  const characterList = uniqueCharacters.slice(0, 5);
  const direction = directionSign(shot.screenDirection);

  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {characterList.map((character, index) => {
        const isNewborn = character.includes('NEWBORN');
        const isChild = character === 'CHILD_ANAADHI';
        const isDeadVariant = text.includes('dead') || text.includes('dies unnamed');
        const isParallel =
          text.includes('parallel') ||
          text.includes('variant') ||
          text.includes('alternate') ||
          text.includes('represented');
        const width = isNewborn ? 840 : isChild ? 820 : characterList.length >= 4 ? 670 : 900;
        const height = isNewborn ? 1050 : 1640;
        const x = portraitPosition(index, characterList.length, shot.screenDirection);
        const left = x - width / 2;
        const opacity = isDeadVariant ? 0.5 : 1;
        const entrance = interpolate(frame, [0, Math.min(18, durationInFrames - 1)], [26 * (index + 1) * direction, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        return (
          <Img
            key={`${shot.shotId}-${character}-${index}`}
            name={`${shot.shotId} ${character}`}
            src={staticFile(characterAssets[character])}
            style={{
              position: 'absolute',
              left,
              top: isNewborn ? 290 : isChild ? 70 : -20,
              width,
              height,
              objectFit: 'cover',
              objectPosition: isNewborn ? '50% 38%' : '50% 18%',
              opacity,
              translate: `${entrance}px 0px`,
              filter: isDeadVariant
                ? 'grayscale(1) contrast(1.2) brightness(0.55) sepia(0.42)'
                : isParallel
                  ? 'contrast(1.08) saturate(0.82) brightness(1.02) hue-rotate(172deg)'
                  : 'contrast(1.08) saturate(0.94) brightness(1.02)',
              clipPath: isNewborn
                ? 'ellipse(46% 46% at 50% 48%)'
                : 'polygon(8% 0, 92% 0, 100% 88%, 78% 100%, 22% 100%, 0 88%)',
              maskImage: 'linear-gradient(to bottom, black 0%, black 80%, transparent 100%)',
              WebkitMaskImage: 'linear-gradient(to bottom, black 0%, black 80%, transparent 100%)',
              boxShadow: isParallel
                ? '0 0 100px rgba(95,202,223,0.34)'
                : '0 0 90px rgba(0,0,0,0.8)',
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

export const CinematicGrade: React.FC<{readonly shot: CanonShot}> = ({shot}) => {
  const text = `${shot.purpose} ${shot.prompt}`.toLowerCase();
  const represented =
    text.includes('parallel') ||
    text.includes('variant') ||
    text.includes('alternate') ||
    text.includes('subjective') ||
    text.includes('represented') ||
    text.includes('flash');

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: represented
            ? 'radial-gradient(ellipse at 50% 48%, transparent 24%, rgba(4,26,30,0.3) 68%, rgba(0,0,0,0.72) 100%)'
            : 'radial-gradient(ellipse at 50% 46%, transparent 38%, rgba(0,0,0,0.38) 80%, rgba(0,0,0,0.74) 100%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.06,
          mixBlendMode: 'soft-light',
          background:
            'repeating-linear-gradient(0deg, transparent 0px, transparent 4px, rgba(255,255,255,0.12) 5px)',
        }}
      />
    </AbsoluteFill>
  );
};
