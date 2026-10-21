import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {RemotionProps, RemotionScene} from './types';

const colors = {
  background: '#F8FAFC',
  surface: '#FFFFFF',
  text: '#000000',
  subtitle: '#666666',
  primary: '#3578E5',
  brand: '#0B84F3',
  border: '#000000',
};

const splitText = (value: string, width = 28): string[] => {
  const words = value.replace(/\s+/g, ' ').trim().split(' ');
  const lines: string[] = [];
  let current = '';
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length > width && current) {
      lines.push(current);
      current = word;
    } else {
      current = candidate;
    }
  }
  if (current) lines.push(current);
  return lines;
};

const discussionPoints = (caption: string): string[] => {
  return caption
    .replace(/\s+/g, ' ')
    .split(/(?<=[.!?])\s+/)
    .filter(Boolean)
    .slice(0, 3);
};

const Background: React.FC<{frame: number}> = ({frame}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(circle at 30% 18%, #E8F1FF 0%, ${colors.background} 42%, #EFF5FC 100%)`,
    }}
  >
    {[0, 1, 2].map((index) => (
      <div
        key={index}
        style={{
          position: 'absolute',
          left: '50%',
          top: `${28 + index * 14}%`,
          width: `${620 + index * 180}px`,
          height: `${340 + index * 110}px`,
          marginLeft: `${-(310 + index * 90) + Math.sin((frame + index * 18) / 24) * 18}px`,
          marginTop: `${-(170 + index * 55) + Math.cos((frame + index * 12) / 28) * 14}px`,
          border: `${3 + index}px solid rgba(53, 120, 229, ${0.2 + index * 0.08})`,
          borderRadius: '50%',
          borderStyle: 'dashed',
          transform: `rotate(${frame * 0.6 + index * 28}deg)`,
        }}
      />
    ))}
  </AbsoluteFill>
);

const Card: React.FC<{children: React.ReactNode; delay: number}> = ({children, delay}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = spring({frame: frame - delay, fps, config: {damping: 200, mass: 0.7}});
  const translateY = interpolate(entrance, [0, 1], [38, 0]);

  return (
    <div
      style={{
        position: 'relative',
        background: colors.surface,
        border: `6px solid ${colors.border}`,
        borderBottom: `10px solid ${colors.border}`,
        borderRadius: 24,
        padding: '34px 36px',
        boxShadow: '0 18px 35px rgba(15, 23, 42, 0.08)',
        opacity: entrance,
        transform: `translateY(${translateY}px) rotate(${(1 - entrance) * -0.6}deg)`,
      }}
    >
      {children}
    </div>
  );
};

const SceneView: React.FC<{scene: RemotionScene; props: RemotionProps}> = ({scene, props}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const titleLines = splitText(scene.title, 26).slice(0, 5);
  const points = discussionPoints(scene.caption);
  const hookVisible = Boolean(scene.hook) && frame < fps * 3;
  const hookOpacity = hookVisible ? spring({frame, fps, config: {damping: 200}}) : 0;
  const globalProgress = (scene.startFrame + frame) / Math.max(props.durationInFrames, 1);

  return (
    <AbsoluteFill style={{padding: '78px 58px 72px'}}>
      <Background frame={frame} />
      <AbsoluteFill style={{justifyContent: 'space-between'}}>
        <Card delay={2}>
          <div style={{color: colors.primary, fontSize: 26, fontWeight: 800, letterSpacing: 1}}>
            {scene.heading.toUpperCase()}
          </div>
          <div style={{height: 20}} />
          {titleLines.map((line, index) => {
            const delay = 5 + index * 3;
            const opacity = interpolate(frame - delay, [0, 8], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
            const translateY = interpolate(frame - delay, [0, 8], [18, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
            return (
              <div key={index} style={{color: colors.text, fontSize: 58, lineHeight: 1.15, fontWeight: 800, opacity, transform: `translateY(${translateY}px)`}}>
                {line}
              </div>
            );
          })}
          <div style={{height: 24}} />
          <div style={{height: 8, width: `${interpolate(frame, [4, 28], [0, 100], {extrapolateRight: 'clamp'})}%`, background: colors.brand, borderRadius: 8}} />
        </Card>

        <Card delay={9}>
          <div style={{color: colors.primary, fontSize: 24, fontWeight: 800, marginBottom: 24}}>
            {scene.layout === 'conclusion' ? 'KESIMPULAN' : 'PEMBAHASAN'}
          </div>
          {points.map((point, index) => {
            const reveal = spring({frame: frame - 16 - index * 6, fps, config: {damping: 200}});
            return (
              <div key={index} style={{display: 'flex', gap: 18, marginBottom: 28, opacity: reveal, transform: `translateX(${(1 - reveal) * 34}px)`}}>
                <div style={{width: 8, minWidth: 8, background: colors.primary, borderRadius: 8}} />
                <div style={{color: colors.text, fontSize: 32, lineHeight: 1.35}}>{point}</div>
              </div>
            );
          })}
        </Card>

        {hookVisible ? (
          <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: '0 52px'}}>
            <div
              style={{
                width: '100%',
                background: colors.surface,
                border: `6px solid ${colors.border}`,
                borderBottom: `10px solid ${colors.border}`,
                borderRadius: 24,
                padding: '36px 34px',
                opacity: hookOpacity,
                transform: `scale(${interpolate(hookOpacity, [0, 1], [0.94, 1])})`,
              }}
            >
              <div style={{color: colors.brand, fontSize: 24, fontWeight: 900, marginBottom: 18}}>HOOK</div>
              {splitText(scene.hook, 30).map((line, index) => (
                <div key={index} style={{color: colors.text, fontSize: 46, fontWeight: 800, lineHeight: 1.2}}>
                  {line}
                </div>
              ))}
            </div>
          </AbsoluteFill>
        ) : null}

        <div>
          <div style={{color: colors.subtitle, fontSize: 24, marginBottom: 14}}>Sumber: {scene.source}</div>
          <div style={{height: 20, background: colors.surface, border: `3px solid ${colors.border}`, borderRadius: 20, overflow: 'hidden'}}>
            <div style={{width: `${Math.min(100, globalProgress * 100)}%`, height: '100%', background: colors.brand}} />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const KaltimRoundup: React.FC<RemotionProps> = (props) => (
  <AbsoluteFill style={{background: colors.background, fontFamily: 'Inter, Segoe UI, Arial, sans-serif'}}>
    {props.scenes.map((scene) => (
      <Sequence key={scene.index} from={scene.startFrame} durationInFrames={scene.durationInFrames}>
        <Audio src={staticFile(scene.audioPath)} />
        <SceneView scene={scene} props={props} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
