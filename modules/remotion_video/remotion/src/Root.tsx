import React from 'react';
import {Composition} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Poppins';
import {KaltimCover} from './KaltimCover';
import {KaltimRoundup} from './KaltimRoundup';
import {sampleProps} from './sample-props';
import type {CoverProps, RemotionProps} from './types';

loadFont('normal', {
  weights: ['400', '500', '600', '700', '800', '900'],
  subsets: ['latin', 'latin-ext'],
});

const coverProps: CoverProps = {
  width: 1080,
  height: 1350,
  title: '3 Berita Terbaru Kaltim',
  articles: [1, 2, 3].map((index) => ({
    index,
    title: `Berita terbaru Kaltim ${index}`,
    source: 'Sumber Kaltim',
  })),
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="KaltimRoundup"
        component={KaltimRoundup}
        durationInFrames={sampleProps.durationInFrames}
        fps={sampleProps.fps}
        width={sampleProps.width}
        height={sampleProps.height}
        defaultProps={sampleProps}
        calculateMetadata={({props}: {props: RemotionProps}) => ({
          durationInFrames: props.durationInFrames,
          fps: props.fps,
          width: props.width,
          height: props.height,
        })}
      />
      <Composition
        id="KaltimCover"
        component={KaltimCover}
        durationInFrames={180}
        fps={30}
        width={coverProps.width}
        height={coverProps.height}
        defaultProps={coverProps}
        calculateMetadata={({props}: {props: CoverProps}) => ({
          width: props.width,
          height: props.height,
        })}
      />
    </>
  );
};
