import React from 'react';
import {Composition} from 'remotion';
import {KaltimRoundup} from './KaltimRoundup';
import {sampleProps} from './sample-props';
import type {RemotionProps} from './types';

export const RemotionRoot: React.FC = () => {
  return (
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
  );
};
