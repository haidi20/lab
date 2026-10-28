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
  background: '#0B1323',
  surface: '#0D1729',
  text: '#F5FAFF',
  subtitle: '#8A97B1',
  primary: '#A3E635',
  brand: '#F59E0B',
  border: '#1D2B45',
};

const layoutLabels: Record<string, string> = {
  headline: 'SOROTAN UTAMA',
  detail: 'PEMBAHASAN LENGKAP',
  metrics: 'FAKTA & DAMPAK',
  process: 'TAHAPAN & TINDAK LANJUT',
  conclusion: 'KESIMPULAN',
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
    .map((sentence) => sentence.trim())
    .filter(Boolean)
    .slice(0, 3);
};

const layoutAccents: Record<string, string> = {
  headline: colors.primary,
  detail: '#60A5FA',
  metrics: '#F472B6',
  process: colors.brand,
  conclusion: colors.primary,
};

const layoutMotifs: Record<string, string> = {
  headline: '+',
  detail: '…',
  metrics: '%',
  process: '→',
  conclusion: '✓',
};

const topicKeywords = (caption: string): string[] => {
  const stopWords = new Set([
    'adalah', 'agar', 'atau', 'bagi', 'bisa', 'dalam', 'dari', 'dengan', 'demikian',
    'hal', 'ini', 'itu', 'karena', 'kepada', 'lagi', 'masih', 'melalui', 'menjadi',
    'oleh', 'pada', 'sebagai', 'serta', 'tetapi', 'tidak', 'untuk', 'yang',
  ]);
  return Array.from(new Set(
    caption
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter((word) => word.length > 4 && !stopWords.has(word)),
  )).slice(0, 3);
};

const TopicChips: React.FC<{caption: string; accent: string}> = ({caption, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  return (
    <div style={{display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 22}}>
      {topicKeywords(caption).map((keyword, index) => {
        const chipReveal = spring({
          frame: frame - 18 - index * 4,
          fps,
          config: {damping: 150, mass: 0.55},
        });
        const pulse = 0.92 + Math.sin((frame + index * 13) / 11) * 0.08;

        return (
          <div
            key={keyword}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 9,
              padding: '9px 14px',
              background: 'rgba(13, 23, 41, 0.88)',
              border: `2px solid ${accent}`,
              borderRadius: 999,
              color: colors.text,
              fontSize: 18,
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: 0.7,
              opacity: chipReveal,
              transform: `translateY(${(1 - chipReveal) * 18}px) scale(${chipReveal * pulse})`,
              boxShadow: `0 10px 24px ${accent}22`,
            }}
          >
            <span style={{width: 8, height: 8, borderRadius: 8, background: accent}} />
            {keyword}
          </div>
        );
      })}
    </div>
  );
};

const Background: React.FC<{frame: number}> = ({frame}) => (
  <AbsoluteFill
    style={{
      background: `radial-gradient(circle at 28% 12%, #101B34 0%, ${colors.background} 48%, #08101F 100%)`,
    }}
  >
    <div
      style={{
        position: 'absolute',
        inset: -160,
        backgroundImage:
          'linear-gradient(rgba(163, 230, 53, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(163, 230, 53, 0.05) 1px, transparent 1px)',
        backgroundSize: '96px 96px',
        transform: `translate3d(${Math.sin(frame / 46) * 28}px, ${Math.cos(frame / 58) * 22}px, 0)`,
      }}
    />
    {[0, 1, 2].map((index) => (
      <div
        key={index}
        style={{
          position: 'absolute',
          left: `${18 + index * 27}%`,
          top: `${20 + index * 21}%`,
          width: `${420 + index * 130}px`,
          height: `${420 + index * 130}px`,
          borderRadius: '50%',
          border: `${2 + index}px dashed rgba(129, 140, 248, ${0.10 + index * 0.05})`,
          transform: `translate3d(${Math.sin((frame + index * 22) / 27) * 34}px, ${Math.cos((frame + index * 17) / 31) * 26}px, 0) rotate(${frame * (0.3 + index * 0.16)}deg)`,
        }}
      />
    ))}
    <div
      style={{
        position: 'absolute',
        inset: -280,
        background:
          'conic-gradient(from 210deg at 50% 42%, rgba(163, 230, 53, 0.07), transparent 30%, rgba(129, 140, 248, 0.08) 58%, transparent 82%)',
        transform: `rotate(${frame * 0.35}deg) scale(${1.04 + Math.sin(frame / 38) * 0.02})`,
      }}
    />
  </AbsoluteFill>
);

const Card: React.FC<{
  children: React.ReactNode;
  delay?: number;
  amplitude?: number;
  style?: React.CSSProperties;
}> = ({children, delay = 0, amplitude = 4, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const entrance = spring({frame: frame - delay, fps, config: {damping: 180, mass: 0.72}});
  const floatY = Math.sin((frame + delay * 8) / 31) * amplitude;
  const floatRotate = Math.cos((frame + delay * 7) / 39) * 0.22;

  return (
    <div
      style={{
        position: 'relative',
        background: colors.surface,
        border: `6px solid ${colors.border}`,
        borderBottom: `10px solid ${colors.border}`,
        borderRadius: 26,
        padding: '30px 32px',
        boxShadow: '0 24px 48px rgba(0, 0, 0, 0.34)',
        opacity: entrance,
        transform: `translate3d(0, ${interpolate(entrance, [0, 1], [42, 0]) + floatY}px, 0) rotate(${(1 - entrance) * -1.1 + floatRotate}deg)`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

const TitleCard: React.FC<{scene: RemotionScene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const titleLines = splitText(scene.title, 24).slice(0, 4);
  const accent = layoutAccents[scene.layout] ?? colors.primary;

  return (
    <Card delay={1} amplitude={3}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: colors.primary,
          fontSize: 23,
          fontWeight: 900,
          letterSpacing: 1.4,
        }}
      >
        <span>{layoutLabels[scene.layout] ?? 'RINGKASAN'}</span>
        <span style={{opacity: 0.58}}>KALTIM HARI INI</span>
      </div>
      <div style={{height: 18}} />
      {titleLines.map((line, index) => {
        const reveal = spring({frame: frame - 4 - index * 3, fps: 24, config: {damping: 170}});
        const drift = Math.sin((frame + index * 16) / 24) * 2;

        return (
          <div
            key={index}
            style={{
              color: colors.text,
              fontSize: 54,
              lineHeight: 1.13,
              fontWeight: 900,
              opacity: reveal,
              transform: `translate3d(${(1 - reveal) * -28 + drift}px, ${(1 - reveal) * 18}px, 0)`,
            }}
          >
            {line}
          </div>
        );
      })}
      <div style={{height: 22}} />
      <TopicChips caption={scene.caption} accent={accent} />
      <div style={{height: 18}} />
      <div
        style={{
          height: 7,
          borderRadius: 8,
          overflow: 'hidden',
          background: '#1D2B45',
        }}
      >
        <div
          style={{
            width: `${interpolate(frame, [3, 26], [8, 100], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}%`,
            height: '100%',
            background: colors.brand,
            transform: `translateX(${Math.sin(frame / 17) * 3}px)`,
          }}
        />
      </div>
    </Card>
  );
};

const PointContent: React.FC<{
  points: string[];
  layout: string;
}> = ({points, layout}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const accent = layoutAccents[layout] ?? colors.primary;

  return (
    <div
      style={{
        position: 'relative',
        overflow: 'hidden',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          position: 'absolute',
          right: -54,
          top: -24,
          color: `${accent}12`,
          fontSize: 120,
          fontWeight: 900,
          transform: `translateY(${Math.sin(frame / 22) * 8}px) rotate(${Math.cos(frame / 31) * 3}deg)`,
        }}
      >
        {layout === 'conclusion' ? '✓' : layout === 'process' ? '→' : '+'}
      </div>
      <div style={{color: accent, fontSize: 22, fontWeight: 900, marginBottom: 20, letterSpacing: 1.2}}>
        {layoutLabels[layout] ?? 'PEMBAHASAN'}
      </div>
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-evenly',
        }}
      >
        {points.map((point, index) => {
          const reveal = spring({frame: frame - 13 - index * 5, fps, config: {damping: 170}});
          const pulse = 0.72 + Math.sin((frame - index * 14) / 13) * 0.28;
          const lines = splitText(point, 38).slice(0, 4);

          return (
            <div
              key={index}
              style={{
                position: 'relative',
                display: 'flex',
                gap: 18,
                padding: '18px 0',
                borderTop: index === 0 ? 'none' : '2px solid #1D2B45',
                opacity: reveal,
                transform: `translate3d(${(1 - reveal) * (layout === 'process' ? 38 : 26)}px, ${(1 - reveal) * 8}px, 0)`,
              }}
            >
              <div
                style={{
                  flex: '0 0 auto',
                  width: 54,
                  height: 54,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: 18,
                  background: accent,
                  color: colors.surface,
                  fontSize: 22,
                  fontWeight: 900,
                  opacity: layout === 'conclusion' || layout === 'detail' ? pulse : 1,
                  transform: `scale(${layout === 'metrics' ? 0.96 + pulse * 0.08 : 1}) rotate(${layout === 'process' ? Math.sin(frame / 20 + index) * 3 : 0}deg)`,
                }}
              >
                {layout === 'conclusion' ? '✓' : String(index + 1).padStart(2, '0')}
              </div>
              <div style={{minWidth: 0}}>
                {lines.map((line, lineIndex) => (
                  <div
                    key={lineIndex}
                    style={{
                      color: colors.text,
                      fontSize: 27,
                      lineHeight: 1.34,
                      fontWeight: lineIndex === 0 ? 800 : 500,
                      transform: `translateX(${Math.sin((frame + index * 20 + lineIndex * 8) / 29) * 2}px)`,
                    }}
                  >
                    {line}
                  </div>
                ))}
                <div style={{height: 12}} />
                <div style={{height: 5, borderRadius: 8, background: '#1D2B45', overflow: 'hidden'}}>
                  <div
                    style={{
                      width: `${interpolate(reveal, [0, 1], [12, 100])}%`,
                      height: '100%',
                      background: colors.primary,
                      opacity: 0.75,
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const HookOverlay: React.FC<{hook: string; visible: boolean}> = ({hook, visible}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const reveal = spring({frame, fps, config: {damping: 160, mass: 0.65}});
  const exit = interpolate(frame, [fps * 3 - 8, fps * 3], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  if (!visible) return null;

  return (
    <AbsoluteFill style={{alignItems: 'center', justifyContent: 'center', padding: '0 46px'}}>
      <div
        style={{
          width: '100%',
          background: colors.surface,
          border: `7px solid ${colors.border}`,
          borderBottom: `11px solid ${colors.border}`,
          borderRadius: 28,
          padding: '34px 32px',
          boxShadow: '0 32px 64px rgba(0, 0, 0, 0.40)',
          opacity: reveal * exit,
          transform: `scale(${interpolate(reveal, [0, 1], [0.92, 1]) + Math.sin(frame / 16) * 0.006}) rotate(${Math.sin(frame / 24) * 0.35}deg)`,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 12}}>
          <div style={{width: 12, height: 12, borderRadius: 8, background: colors.brand, opacity: 0.6 + Math.sin(frame / 7) * 0.4}} />
          <div style={{color: colors.brand, fontSize: 21, fontWeight: 900, letterSpacing: 1.6}}>SOROTAN CEPAT</div>
        </div>
        {splitText(hook, 26).map((line, index) => (
          <div
            key={index}
            style={{
              color: colors.text,
              fontSize: 47,
              fontWeight: 900,
              lineHeight: 1.17,
              marginTop: index === 0 ? 18 : 0,
              opacity: spring({frame: frame - 3 - index * 2, fps, config: {damping: 170}}),
              transform: `translateY(${(1 - spring({frame: frame - 3 - index * 2, fps, config: {damping: 170}})) * 20}px)`,
            }}
          >
            {line}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const HighlightedCaption: React.FC<{scene: RemotionScene; accent: string}> = ({scene, accent}) => {
  const frame = useCurrentFrame();
  const phrases = discussionPoints(scene.caption);
  const segment = Math.max(scene.durationInFrames / Math.max(phrases.length, 1), 1);
  const activeIndex = Math.min(Math.floor(frame / segment), Math.max(phrases.length - 1, 0));
  const phraseProgress = (frame % segment) / segment;
  const words = (phrases[activeIndex] ?? '').split(/\s+/).filter(Boolean).slice(0, 14);

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 14,
        padding: '16px 20px',
        background: 'rgba(13, 23, 41, 0.92)',
        border: `3px solid ${colors.border}`,
        borderLeft: `8px solid ${accent}`,
        borderRadius: 20,
        boxShadow: '0 16px 32px rgba(0, 0, 0, 0.26)',
      }}
    >
      <div
        style={{
          flex: '0 0 auto',
          width: 36,
          height: 36,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 12,
          background: accent,
          color: colors.surface,
          fontWeight: 900,
        }}
      >
        {layoutMotifs[scene.layout] ?? '+'}
      </div>
      <div style={{minWidth: 0, fontSize: 21, lineHeight: 1.35, fontWeight: 600}}>
        {words.map((word, index) => {
          const wordProgress = Math.min(1, Math.max(0, phraseProgress * words.length - index));
          return (
            <span
              key={`${word}-${index}`}
              style={{
                color: wordProgress > 0.65 ? colors.primary : wordProgress > 0.25 ? colors.text : colors.subtitle,
                marginRight: 7,
                opacity: 0.65 + wordProgress * 0.35,
                transform: `translateY(${(1 - wordProgress) * 2}px)`,
                display: 'inline-block',
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    </div>
  );
};

const SceneView: React.FC<{scene: RemotionScene; props: RemotionProps}> = ({scene, props}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const points = discussionPoints(scene.caption);
  const globalProgress = (scene.startFrame + frame) / Math.max(props.durationInFrames, 1);
  const entrance = spring({frame, fps, config: {damping: 190, mass: 0.75}});
  const exit = interpolate(frame, [scene.durationInFrames - 8, scene.durationInFrames - 1], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{opacity: Math.min(entrance, exit)}}>
      <Background frame={frame} />
      <AbsoluteFill style={{padding: '68px 52px 66px', justifyContent: 'space-between'}}>
        <TitleCard scene={scene} />
        <Card
          delay={8}
          amplitude={5}
          style={{
            flex: '0 1 880px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            margin: '24px 0',
          }}
        >
          <PointContent points={points} layout={scene.layout} />
        </Card>
        <HookOverlay
          hook={scene.hook}
          visible={Boolean(scene.hook) && frame < fps * 3}
        />
        <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
          <HighlightedCaption scene={scene} accent={layoutAccents[scene.layout] ?? colors.primary} />
          <div style={{display: 'flex', justifyContent: 'space-between', color: colors.subtitle, fontSize: 22, marginBottom: 12}}>
            <span>PROGRESS</span>
            <span>{Math.round(globalProgress * 100)}%</span>
          </div>
          <div
            style={{
              height: 12,
              background: colors.surface,
              border: `3px solid ${colors.border}`,
              borderRadius: 20,
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${Math.min(100, globalProgress * 100)}%`,
                height: '100%',
                background: colors.brand,
                transform: `translateX(${Math.sin(frame / 24) * 2}px)`,
              }}
            />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const KaltimRoundup: React.FC<RemotionProps> = (props) => (
  <AbsoluteFill style={{background: colors.background, fontFamily: 'Poppins, Inter, Segoe UI, Arial, sans-serif'}}>
    {props.scenes.map((scene) => (
      <Sequence key={scene.index} from={scene.startFrame} durationInFrames={scene.durationInFrames}>
        <Audio src={staticFile(scene.audioPath)} />
        <SceneView scene={scene} props={props} />
      </Sequence>
    ))}
  </AbsoluteFill>
);
