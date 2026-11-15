import React from 'react';
import {AbsoluteFill, Easing, Img, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_FAMILY, type Brand, type BrandColors} from '../brands';
import {estimateTextWidth, safeArea, subtitleCenterY} from '../layout';
import type {Reveal} from '../types';
import {TitleCard} from './TitleCard';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/**
 * Révélation avant / après : une ligne lumineuse balaie l'image de gauche à droite
 * et dévoile la photo « après ». Étiquettes AVANT → APRÈS, légende à la fin.
 * Les temps de `reveal` sont relatifs à la vidéo principale ; ce composant est placé
 * dans une <Sequence from={start}>.
 */
export const BeforeAfter: React.FC<{reveal: Reveal; brand: Brand; colors: BrandColors}> = ({reveal, brand, colors}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const total = Math.round((reveal.end - reveal.start) * fps);
  const wipeFrom = Math.round((reveal.wipeStart - reveal.start) * fps);
  const wipeLen = Math.max(1, Math.round(reveal.wipeDuration * fps));
  const wipeTo = wipeFrom + wipeLen;
  const midWipe = wipeFrom + Math.round(wipeLen / 2);

  const p = interpolate(frame, [wipeFrom, wipeTo], [0, 1], {...clamp, easing: Easing.inOut(Easing.cubic)});
  // Entrée « punch » + zoom lent continu.
  const punch = interpolate(frame, [0, 8], [1.12, 1], {...clamp, easing: Easing.out(Easing.cubic)});
  const zoom = punch * interpolate(frame, [0, total], [1, 1.05], clamp);
  // Petit flash uniquement juste après le balayage.
  const flash = frame >= wipeTo ? interpolate(frame, [wipeTo, wipeTo + 6], [0.3, 0], clamp) : 0;
  const lineOpacity = interpolate(p, [0, 0.04, 0.96, 1], [0, 1, 1, 0], clamp);

  const objectPosition = `${(reveal.positionX ?? 0.5) * 100}% ${(reveal.positionY ?? 0.5) * 100}%`;
  const img: React.CSSProperties = {width: '100%', height: '100%', objectFit: 'cover', objectPosition};
  const lineX = p * width;

  const safe = safeArea(width, height);
  const avail = width - safe.left - safe.right;
  let capSize = Math.min(width, height) * 0.075;
  if (reveal.caption) {
    const longest = Math.max(...reveal.caption.split(/\s+/).map((w) => estimateTextWidth(w, capSize)));
    if (longest > avail) capSize *= avail / longest;
  }
  // Légende sous le sujet, au-dessus de la zone basse réservée à l'interface.
  const captionY = height > width ? height * 0.705 : subtitleCenterY(width, height);
  const capIn = spring({frame: frame - (wipeTo + 4), fps, config: {damping: 13, stiffness: 180}, durationInFrames: 10});

  return (
    <AbsoluteFill style={{backgroundColor: '#000', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${zoom})`}}>
        <Img src={staticFile(reveal.before)} style={img} />
        <AbsoluteFill style={{clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`}}>
          <Img src={staticFile(reveal.after)} style={img} />
        </AbsoluteFill>
      </AbsoluteFill>
      {lineOpacity > 0 ? (
        <div
          style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            left: lineX - 3,
            width: 6,
            backgroundColor: '#FFFFFF',
            opacity: lineOpacity,
            boxShadow: `0 0 10px 2px rgba(255,255,255,0.85), 0 0 22px 4px ${colors.accent}66`,
          }}
        />
      ) : null}
      {flash > 0 ? <AbsoluteFill style={{backgroundColor: '#FFFFFF', opacity: flash}} /> : null}
      <Sequence durationInFrames={midWipe} layout="none">
        <TitleCard text="Avant" brand={brand} colors={colors} durationInFrames={midWipe} size="title" />
      </Sequence>
      <Sequence from={midWipe} durationInFrames={total - midWipe} layout="none">
        <TitleCard text="Après" brand={brand} colors={colors} durationInFrames={total - midWipe + 6} size="title" />
      </Sequence>
      {reveal.caption && frame >= wipeTo + 4 ? (
        <div
          style={{
            position: 'absolute',
            left: safe.left,
            width: avail,
            top: captionY,
            transform: `translateY(-50%) scale(${interpolate(capIn, [0, 1], [0.6, 1])})`,
            opacity: capIn,
            textAlign: 'center',
            fontFamily: FONT_FAMILY,
            fontSize: capSize,
            fontWeight: 900,
            lineHeight: 1.1,
            textTransform: 'uppercase',
            color: colors.text,
            WebkitTextStroke: `${Math.round(capSize * 0.1)}px ${colors.stroke}`,
            paintOrder: 'stroke fill',
            textShadow: `0 ${capSize * 0.06}px ${capSize * 0.2}px rgba(0,0,0,0.6)`,
          }}
        >
          {reveal.caption}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};
