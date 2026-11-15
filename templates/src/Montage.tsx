import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Sequence, cancelRender, continueRender, delayRender, interpolate, staticFile, useVideoConfig} from 'remotion';
import {TransitionSeries, linearTiming} from '@remotion/transitions';
import {fade} from '@remotion/transitions/fade';
import {slide} from '@remotion/transitions/slide';
import {BRANDS} from './brands';
import {MainVideo} from './components/MainVideo';
import {Outro} from './components/Outro';
import {Subtitles} from './components/Subtitles';
import {TitleCard} from './components/TitleCard';
import {OUTRO_FRAMES, OUTRO_TRANSITION_FRAMES, mainFrames, totalFrames} from './timing';
import type {MontageProps, Word} from './types';

/** Charge la police de la marque (fichier dans le dossier public) avant le rendu. */
const useBrandFont = (font?: string | null) => {
  const [handle] = useState(() => (font ? delayRender(`Police ${font}`) : null));
  useEffect(() => {
    if (!font || handle === null) return;
    const face = new FontFace('BrandFont', `url('${staticFile(font)}')`, {weight: '100 900'});
    face
      .load()
      .then(() => {
        document.fonts.add(face);
        continueRender(handle);
      })
      .catch((err) => cancelRender(err));
  }, [font, handle]);
};

/** Musique baissée automatiquement quand quelqu'un parle. */
const musicVolume = (frame: number, fps: number, words: Word[], base: number, total: number): number => {
  const t = frame / fps;
  let dist = Infinity;
  for (const w of words) {
    if (t >= w.start && t <= w.end) {
      dist = 0;
      break;
    }
    dist = Math.min(dist, Math.abs(t - w.start), Math.abs(t - w.end));
  }
  const duck = interpolate(dist, [0, 0.35], [0.35, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const fades = interpolate(frame, [0, fps * 0.4, total - fps * 1.2, total], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  return base * duck * fades;
};

export const Montage: React.FC<MontageProps> = (props) => {
  const {fps} = useVideoConfig();
  useBrandFont(props.font);
  const brand = BRANDS[props.brand];
  const colors = {...brand.colors, ...(props.colors ?? {})};
  const main = mainFrames(props, fps);
  const total = totalFrames(props, fps);
  const hookFrames = Math.round((props.hookDuration ?? 2.2) * fps);
  const words = props.words ?? [];

  return (
    <AbsoluteFill style={{backgroundColor: colors.bg}}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={main}>
          <MainVideo video={props.video} cuts={props.cuts ?? []} duration={props.videoDuration} brand={brand} />
          {(props.titles ?? []).map((ti, i) => {
            const from = Math.round(ti.start * fps);
            const len = Math.max(1, Math.round((ti.end - ti.start) * fps));
            return (
              <Sequence key={i} from={from} durationInFrames={len} layout="none">
                <TitleCard text={ti.text} brand={brand} colors={colors} durationInFrames={len} size="title" />
              </Sequence>
            );
          })}
          {props.hook ? (
            <Sequence durationInFrames={hookFrames} layout="none">
              <TitleCard
                text={props.hook}
                brand={brand}
                colors={colors}
                durationInFrames={hookFrames}
                size="hook"
                logo={props.logo}
              />
            </Sequence>
          ) : null}
          <Subtitles words={words} brand={brand} colors={colors} />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition
          presentation={brand.style === 'punchy' ? slide({direction: 'from-bottom'}) : fade()}
          timing={linearTiming({durationInFrames: OUTRO_TRANSITION_FRAMES})}
        />
        <TransitionSeries.Sequence durationInFrames={OUTRO_FRAMES}>
          <Outro brand={brand} colors={colors} logo={props.logo} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
      {props.music ? (
        <Audio
          src={staticFile(props.music)}
          loop
          volume={(f) => musicVolume(f, fps, words, props.musicVolume ?? 0.3, total)}
        />
      ) : null}
    </AbsoluteFill>
  );
};
