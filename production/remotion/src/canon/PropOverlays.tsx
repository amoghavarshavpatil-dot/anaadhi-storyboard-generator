import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import type {CanonShot} from './types';

const ParaaneEmblem: React.FC<{readonly large?: boolean; readonly rotate?: boolean}> = ({
  large = false,
  rotate = false,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: large ? 1120 : 360,
        height: large ? 1120 : 360,
        translate: '-50% -50%',
        rotate: rotate ? `${frame * 0.23}deg` : '0deg',
        borderRadius: '50%',
        border: `${large ? 34 : 15}px solid rgba(213,154,62,0.94)`,
        boxShadow: '0 0 80px rgba(213,154,62,0.42), inset 0 0 70px rgba(213,154,62,0.2)',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '20%',
          width: '26%',
          height: '62%',
          translate: '-50% 0',
          border: `${large ? 30 : 12}px solid rgba(213,154,62,0.94)`,
          borderTop: 0,
          borderRadius: '0 0 50% 50%',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '43%',
          width: '58%',
          height: '18%',
          translate: '-50% 0',
          borderTop: `${large ? 30 : 12}px solid rgba(213,154,62,0.94)`,
          borderRadius: '50%',
        }}
      />
    </div>
  );
};

const MedicalCase: React.FC<{readonly showCartridge: boolean}> = ({showCartridge}) => (
  <div
    style={{
      position: 'absolute',
      left: '50%',
      top: '56%',
      width: 1180,
      height: 640,
      translate: '-50% -50%',
      borderRadius: 34,
      border: '18px solid #636965',
      background: 'linear-gradient(145deg, #222825, #070a09)',
      boxShadow: '0 60px 130px rgba(0,0,0,0.84), inset 0 0 70px rgba(255,255,255,0.08)',
    }}
  >
    <ParaaneEmblem />
    {showCartridge ? (
      <div
        style={{
          position: 'absolute',
          right: 120,
          top: 150,
          width: 310,
          height: 100,
          borderRadius: 50,
          border: '10px solid rgba(198,212,207,0.8)',
          background: 'linear-gradient(90deg, #341b18, #b13a2a 58%, #d9d8c2)',
          boxShadow: '0 0 55px rgba(198,59,40,0.62)',
        }}
      >
        <div
          style={{
            fontFamily: 'Arial, sans-serif',
            fontWeight: 800,
            fontSize: 38,
            letterSpacing: 6,
            color: '#f7d8c9',
            textAlign: 'center',
            lineHeight: '82px',
          }}
        >
          ADK-7
        </div>
      </div>
    ) : null}
  </div>
);

const Injector: React.FC<{readonly needleOnly?: boolean}> = ({needleOnly = false}) => (
  <div
    style={{
      position: 'absolute',
      left: needleOnly ? '38%' : '50%',
      top: '50%',
      width: needleOnly ? 1900 : 1500,
      height: 190,
      translate: '-50% -50%',
      rotate: '-14deg',
      background: needleOnly
        ? 'linear-gradient(90deg, transparent 0%, transparent 9%, #d7ded8 9%, #f8ffff 100%)'
        : 'linear-gradient(90deg, #1e2927, #afb9b1 43%, #5e7771 72%, #d9e6df)',
      clipPath: needleOnly
        ? 'polygon(0 47%, 100% 43%, 100% 57%, 0 53%)'
        : 'polygon(0 26%, 82% 26%, 100% 47%, 82% 74%, 0 74%)',
      boxShadow: '0 0 70px rgba(181,218,211,0.48)',
    }}
  />
);

const WristDisplay: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '51%',
        width: 1180,
        height: 700,
        translate: '-50% -50%',
        borderRadius: 100,
        border: '30px solid #171b1b',
        background: 'radial-gradient(circle at 50% 50%, #58271d, #180d0a 62%, #030504)',
        boxShadow: '0 0 100px rgba(212,78,41,0.22), inset 0 0 80px black',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          width: 220,
          height: 500,
          translate: '-50% -50%',
          borderRadius: '50% 50% 36% 36%',
          background: 'linear-gradient(180deg, #ffd278, #e14a2f 55%, #781914)',
          opacity: 0.72 + 0.15 * Math.sin(frame / 5),
          filter: 'blur(10px)',
          boxShadow: '0 0 90px #ff4b26',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 46,
          border: '5px solid rgba(255,130,72,0.34)',
          background:
            'repeating-linear-gradient(0deg, transparent 0px, transparent 46px, rgba(255,119,64,0.13) 49px)',
        }}
      />
    </div>
  );
};

const Floorboard: React.FC = () => (
  <AbsoluteFill>
    <div
      style={{
        position: 'absolute',
        left: 270,
        right: 150,
        bottom: 190,
        height: 360,
        background:
          'repeating-linear-gradient(177deg, #271d12 0px, #271d12 72px, #5d3f23 78px, #100d09 84px)',
        boxShadow: '0 -30px 100px rgba(0,0,0,0.62)',
      }}
    />
    <svg
      viewBox="0 0 3840 1600"
      style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}
    >
      <path
        d="M 1160 1360 C 1430 1260, 1640 1420, 1870 1290 S 2320 1380, 2680 1220"
        stroke="#020303"
        strokeWidth="34"
        fill="none"
      />
      <path
        d="M 1160 1358 C 1430 1258, 1640 1418, 1870 1288 S 2320 1378, 2680 1218"
        stroke="rgba(151,104,53,0.55)"
        strokeWidth="8"
        fill="none"
      />
    </svg>
    <div
      style={{
        position: 'absolute',
        left: 1560,
        bottom: 130,
        width: 930,
        height: 210,
        borderRadius: '70% 15% 55% 30%',
        background: 'linear-gradient(160deg, #3e2519, #100908)',
        rotate: '-6deg',
        opacity: 0.86,
        boxShadow: '0 16px 40px rgba(0,0,0,0.65)',
      }}
    />
  </AbsoluteFill>
);

const Shields: React.FC = () => (
  <AbsoluteFill>
    {Array.from({length: 4}, (_, index) => (
      <div
        key={`shield-${index}`}
        style={{
          position: 'absolute',
          left: 580 + index * 760,
          top: 180 + (index % 2) * 80,
          width: 500,
          height: 1060,
          border: '18px solid rgba(98,115,115,0.74)',
          borderRadius: '42% 42% 24% 24%',
          background: 'linear-gradient(100deg, rgba(30,41,42,0.74), rgba(92,126,130,0.24))',
          boxShadow: '0 30px 80px rgba(0,0,0,0.8)',
          opacity: 0.62,
        }}
      />
    ))}
  </AbsoluteFill>
);

const IronHook: React.FC = () => (
  <svg
    viewBox="0 0 3840 1600"
    style={{position: 'absolute', inset: 0, width: '100%', height: '100%'}}
  >
    <path
      d="M 2720 80 L 2320 720 C 2120 1040, 2260 1320, 2580 1290 C 2780 1270, 2910 1110, 2910 930"
      stroke="#a8aaa1"
      strokeWidth="72"
      strokeLinecap="round"
      fill="none"
      style={{filter: 'drop-shadow(0 40px 28px rgba(0,0,0,0.8))'}}
    />
  </svg>
);

const Weapons: React.FC = () => (
  <AbsoluteFill style={{opacity: 0.72}}>
    {Array.from({length: 7}, (_, index) => {
      const left = 190 + index * 560;
      const fromLeft = index < 3;
      return (
        <div
          key={`weapon-${index}`}
          style={{
            position: 'absolute',
            left,
            top: 310 + (index % 3) * 150,
            width: 820,
            height: 74,
            background: 'linear-gradient(90deg, #111, #5c625f 62%, #111)',
            rotate: fromLeft ? '14deg' : '-14deg',
            clipPath: 'polygon(0 25%, 84% 25%, 100% 0, 98% 100%, 84% 72%, 0 72%)',
            boxShadow: '0 24px 38px black',
          }}
        />
      );
    })}
  </AbsoluteFill>
);

const FourRoads: React.FC = () => (
  <AbsoluteFill
    style={{
      background: 'radial-gradient(circle at 50% 45%, rgba(223,195,102,0.33), #050708 34%)',
    }}
  >
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: 3100,
        height: 240,
        translate: '-50% -50%',
        rotate: '0deg',
        background: 'linear-gradient(180deg, #0b0c0c, #3a3c38, #0a0b0b)',
      }}
    />
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: '50%',
        width: 3100,
        height: 240,
        translate: '-50% -50%',
        rotate: '90deg',
        background: 'linear-gradient(180deg, #0b0c0c, #3a3c38, #0a0b0b)',
      }}
    />
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: 170,
        width: 34,
        height: 610,
        translate: '-50% 0',
        background: '#222826',
      }}
    />
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: 130,
        width: 220,
        height: 220,
        translate: '-50% 0',
        borderRadius: '50%',
        background: '#d3b56b',
        filter: 'blur(9px)',
        boxShadow: '0 0 150px #d3b56b',
      }}
    />
  </AbsoluteFill>
);

const MedicineCup: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: '50%',
      top: '53%',
      width: 920,
      height: 660,
      translate: '-50% -50%',
      borderRadius: '48% 48% 25% 25%',
      background: 'linear-gradient(105deg, #161918, #e0e3dc 32%, #4c514e 62%, #f8faf5 84%, #191b1a)',
      clipPath: 'polygon(7% 0, 93% 0, 79% 100%, 21% 100%)',
      boxShadow: '0 70px 120px rgba(0,0,0,0.75)',
    }}
  />
);

const ObservationGlass: React.FC = () => (
  <AbsoluteFill>
    <div
      style={{
        position: 'absolute',
        left: 700,
        right: 700,
        top: 130,
        bottom: 120,
        border: '30px solid rgba(119,137,137,0.7)',
        background: 'linear-gradient(145deg, rgba(102,137,140,0.18), rgba(2,5,6,0.76))',
        boxShadow: 'inset 0 0 120px rgba(0,0,0,0.82)',
      }}
    />
    <div
      style={{
        position: 'absolute',
        left: '50%',
        top: 390,
        width: 440,
        height: 880,
        translate: '-50% 0',
        borderRadius: '48% 48% 18% 18%',
        background: '#020303',
        filter: 'blur(15px)',
      }}
    />
  </AbsoluteFill>
);

const PulseDisplay: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        position: 'absolute',
        right: 220,
        bottom: 160,
        width: 1100,
        height: 390,
        borderRadius: 34,
        border: '14px solid rgba(102,126,121,0.8)',
        background: 'rgba(4,12,11,0.92)',
        boxShadow: '0 24px 70px rgba(0,0,0,0.8)',
      }}
    >
      <svg viewBox="0 0 1100 390" style={{width: '100%', height: '100%'}}>
        <path
          d={`M 0 210 L 180 210 L 250 ${205 - 42 * Math.sin(frame / 4)} L 310 210 L 470 210 L 540 72 L 620 324 L 700 210 L 1100 210`}
          fill="none"
          stroke="#62e0a4"
          strokeWidth="18"
          style={{filter: 'drop-shadow(0 0 16px #62e0a4)'}}
        />
      </svg>
    </div>
  );
};

const AcademicDiagram: React.FC<{readonly stage: number}> = ({stage}) => {
  const frame = useCurrentFrame();
  const nodes = [
    {label: 'CARE', angle: -90},
    {label: 'POLICE', angle: 0},
    {label: 'GOVERNANCE', angle: 90},
    {label: 'COMMUNITY RESPONSE', angle: 180},
  ].slice(0, Math.max(1, stage));
  return (
    <AbsoluteFill
      style={{
        background: 'radial-gradient(circle at 50% 50%, rgba(17,70,70,0.58), rgba(2,5,6,0.96) 62%)',
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: '50%',
          width: 1240,
          height: 1240,
          translate: '-50% -50%',
          rotate: `${frame * 0.16}deg`,
          borderRadius: '50%',
          border: '8px solid rgba(195,159,79,0.42)',
        }}
      >
        <ParaaneEmblem />
        {nodes.map((node) => {
          const radians = (node.angle * Math.PI) / 180;
          const x = 520 + Math.cos(radians) * 470;
          const y = 520 + Math.sin(radians) * 470;
          return (
            <React.Fragment key={node.label}>
              <div
                style={{
                  position: 'absolute',
                  left: 620,
                  top: 620,
                  width: 470,
                  height: 6,
                  rotate: `${node.angle}deg`,
                  transformOrigin: '0 50%',
                  background: 'linear-gradient(90deg, rgba(216,180,94,0.9), rgba(216,180,94,0.1))',
                }}
              />
              <div
                style={{
                  position: 'absolute',
                  left: x,
                  top: y,
                  width: 300,
                  height: 128,
                  translate: '-50% -50%',
                  borderRadius: 80,
                  border: '7px solid rgba(218,180,90,0.92)',
                  background: 'rgba(7,18,17,0.92)',
                  color: '#f0d899',
                  fontFamily: 'Arial, sans-serif',
                  fontSize: node.label.length > 12 ? 25 : 34,
                  fontWeight: 700,
                  letterSpacing: 2,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  textAlign: 'center',
                  rotate: `${-frame * 0.16}deg`,
                  boxShadow: '0 0 40px rgba(216,180,94,0.22)',
                }}
              >
                {node.label}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const ParallelShards: React.FC = () => {
  const colors = ['#1a5272', '#78342d', '#5b6073', '#2a7167', '#67602d'];
  return (
    <AbsoluteFill>
      {colors.map((color, index) => (
        <div
          key={`shard-${color}`}
          style={{
            position: 'absolute',
            left: index * 770 - 90,
            top: index % 2 === 0 ? -80 : 90,
            width: 1020,
            height: 1750,
            rotate: `${-9 + index * 4}deg`,
            background: `linear-gradient(160deg, ${color}, rgba(0,0,0,0.88))`,
            border: '9px solid rgba(173,218,221,0.22)',
            clipPath: 'polygon(17% 0, 100% 6%, 83% 100%, 0 91%)',
            mixBlendMode: 'screen',
            opacity: 0.48,
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

export const PropOverlayLayer: React.FC<{readonly shot: CanonShot}> = ({shot}) => {
  const text = `${shot.purpose} ${shot.prompt} ${shot.props.join(' ')}`.toLowerCase();
  const has = (value: string) => text.includes(value);

  if (has('five parallel earth') || has('five realities')) return <ParallelShards />;
  if (has('thermal') || has('wrist display')) return <WristDisplay />;
  if (has('four roads') || has('four-road')) return <FourRoads />;
  if (has('metal medicine cup')) return <MedicineCup />;
  if (has('observation glass') || has('faceless man')) return <ObservationGlass />;
  if (has('academic diagram')) {
    const stage = has('community response') || has('complete') || has('system concept')
      ? 4
      : has('governance')
        ? 3
        : has('police')
          ? 2
          : 1;
    return <AcademicDiagram stage={stage} />;
  }
  if (has('emblem')) {
    return <ParaaneEmblem large rotate={has('rotate') || has('rotation') || has('shifts')} />;
  }
  if (has('pulse display')) return <PulseDisplay />;
  if (has('medical case') || has('cartridge case') || has('case opens')) {
    return <MedicalCase showCartridge={has('adk-7') || has('distinct')} />;
  }
  if (has('adk-7 cartridge') || has('cartridge reveal') || has('load adk-7')) {
    return <MedicalCase showCartridge />;
  }
  if (has('needle')) return <Injector needleOnly />;
  if (has('injector') || has('compressed discharge')) return <Injector />;
  if (has('iron hook') || has('hook threat') || has('hook wrist')) return <IronHook />;
  if (has('shield')) return <Shields />;
  if (has('every weapon') || has('weapons rise') || has('firing line') || has('aims a weapon')) {
    return <Weapons />;
  }
  if (has('split floor') || has('floor crack') || has('palm presses floor') || has('fingers stop')) {
    return <Floorboard />;
  }
  return null;
};

export const PerceptionOverlay: React.FC<{readonly shot: CanonShot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const text = `${shot.purpose} ${shot.prompt}`.toLowerCase();
  const fracture =
    text.includes('parallel') ||
    text.includes('variant') ||
    text.includes('alternate') ||
    text.includes('subjective') ||
    text.includes('flash') ||
    text.includes('represented');

  if (!fracture) return null;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          opacity: interpolate(frame, [0, Math.min(10, durationInFrames - 1)], [0.2, 0.68], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          }),
          background:
            'repeating-linear-gradient(114deg, transparent 0px, transparent 150px, rgba(81,209,220,0.14) 154px, transparent 163px), radial-gradient(circle at 51% 48%, transparent 14%, rgba(24,108,118,0.25) 60%, rgba(2,4,5,0.72))',
          mixBlendMode: 'screen',
        }}
      />
      <svg viewBox="0 0 3840 1600" style={{position: 'absolute', inset: 0}}>
        <path
          d="M 290 -40 L 1050 550 L 800 1660 M 1410 -30 L 1790 470 L 1510 940 L 1940 1640 M 2850 -40 L 2510 520 L 3200 1080 L 2920 1640"
          stroke="rgba(172,231,235,0.25)"
          strokeWidth="12"
          fill="none"
        />
      </svg>
    </AbsoluteFill>
  );
};
