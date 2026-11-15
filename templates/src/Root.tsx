import React from 'react';
import {Composition, type CalculateMetadataFunction} from 'remotion';
import {Montage} from './Montage';
import {FPS, totalFrames} from './timing';
import type {MontageProps} from './types';

// Les vraies valeurs viennent de work/<projet>/props.json (voir scripts/montage.py).
const defaultProps: MontageProps = {
  brand: 'solar-car',
  video: 'main.mp4',
  videoDuration: 5,
  words: [],
  cuts: [],
  hook: 'Accroche',
  titles: [],
  music: null,
  musicVolume: 0.3,
  logo: null,
  font: null,
  colors: null,
};

const calculateMetadata: CalculateMetadataFunction<MontageProps> = ({props}) => ({
  durationInFrames: totalFrames(props, FPS),
});

const FORMATS = [
  {id: 'Reel-9x16', width: 1080, height: 1920},
  {id: 'Carre-1x1', width: 1080, height: 1080},
  {id: 'Paysage-16x9', width: 1920, height: 1080},
] as const;

export const RemotionRoot: React.FC = () => (
  <>
    {FORMATS.map((f) => (
      <Composition
        key={f.id}
        id={f.id}
        component={Montage}
        width={f.width}
        height={f.height}
        fps={FPS}
        durationInFrames={totalFrames(defaultProps, FPS)}
        defaultProps={defaultProps}
        calculateMetadata={calculateMetadata}
      />
    ))}
  </>
);
