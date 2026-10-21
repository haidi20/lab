export type RemotionScene = {
  index: number;
  startFrame: number;
  durationInFrames: number;
  heading: string;
  title: string;
  caption: string;
  narration: string;
  layout: string;
  source: string;
  hook: string;
  audioPath: string;
};

export type RemotionProps = {
  width: number;
  height: number;
  fps: number;
  title: string;
  source: string;
  voice: string;
  durationInFrames: number;
  scenes: RemotionScene[];
};
