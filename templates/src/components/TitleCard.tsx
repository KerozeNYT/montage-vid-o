import React from 'react';
import {Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_FAMILY, type Brand, type BrandColors} from '../brands';
import {estimateTextWidth, safeArea, titleTopY} from '../layout';

/**
 * Texte à l'écran (accroche ou titre), en haut de la zone sûre.
 * Affiché de `from` à `to` (frames, relatives au début de la séquence).
 */
export const TitleCard: React.FC<{
  text: string;
  brand: Brand;
  colors: BrandColors;
  durationInFrames: number;
  size: 'hook' | 'title';
  logo?: string | null;
}> = ({text, brand, colors, durationInFrames, size, logo}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const safe = safeArea(width, height);
  const avail = width - safe.left - safe.right;

  const enter = spring({frame, fps, config: {damping: 13, stiffness: 160}, durationInFrames: 12});
  const exit = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const punchy = brand.style === 'punchy';
  let fontSize = Math.min(width, height) * (size === 'hook' ? 0.082 : 0.062);
  // 2 lignes max : on réduit si nécessaire.
  const longestWord = Math.max(...text.split(/\s+/).map((w) => estimateTextWidth(w, fontSize)));
  const innerAvail = avail * 0.9;
  if (longestWord > innerAvail) fontSize *= innerAvail / longestWord;
  const full = estimateTextWidth(text, fontSize);
  if (full > innerAvail * 1.9) fontSize *= (innerAvail * 1.9) / full;

  const logoHeight = Math.min(width, height) * 0.11;

  return (
    <div
      style={{
        position: 'absolute',
        left: safe.left,
        width: avail,
        top: titleTopY(width, height),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: fontSize * 0.35,
        opacity: exit,
        transform: `translateY(${interpolate(enter, [0, 1], [-40, 0])}px) scale(${interpolate(enter, [0, 1], [0.85, 1])})`,
      }}
    >
      {logo ? (
        <Img src={staticFile(logo)} style={{height: logoHeight, objectFit: 'contain'}} />
      ) : null}
      <div
        style={{
          fontFamily: FONT_FAMILY,
          fontSize,
          fontWeight: punchy ? 900 : 700,
          textTransform: 'uppercase',
          letterSpacing: punchy ? '0.01em' : '0.06em',
          lineHeight: 1.1,
          textAlign: 'center',
          maxWidth: avail,
          padding: punchy ? `${fontSize * 0.18}px ${fontSize * 0.4}px` : `${fontSize * 0.25}px ${fontSize * 0.3}px`,
          borderRadius: punchy ? fontSize * 0.2 : 0,
          color: punchy ? '#000000' : colors.text,
          background: punchy ? colors.accent : 'rgba(0,0,0,0.55)',
          borderTop: punchy ? undefined : `2px solid ${colors.accent}`,
          borderBottom: punchy ? undefined : `2px solid ${colors.accent}`,
          boxShadow: punchy ? `0 ${fontSize * 0.1}px ${fontSize * 0.3}px rgba(0,0,0,0.45)` : undefined,
        }}
      >
        {text}
      </div>
    </div>
  );
};
