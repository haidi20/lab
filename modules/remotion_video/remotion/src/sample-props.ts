import type {RemotionProps} from './types';

export const sampleProps: RemotionProps = {
  width: 1080,
  height: 1920,
  fps: 24,
  title: 'Ringkasan Kaltim',
  source: 'Kaltim',
  voice: 'id-ID-ArdiNeural',
  durationInFrames: 1,
  scenes: [
    {
      index: 1,
      startFrame: 0,
      durationInFrames: 1,
      heading: 'Berita 1/3',
      title: 'Ringkasan Kaltim',
      caption: 'Contoh props untuk Studio.',
      narration: 'Contoh props untuk Studio.',
      layout: 'headline',
      source: 'Kaltim',
      hook: 'Tiga kabar Kaltim hari ini bisa mengubah rencanamu.',
      audioPath: 'audio/scene_01.mp3',
    },
  ],
};
