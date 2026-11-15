import React from 'react';
import {AbsoluteFill, Easing, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Brand} from '../brands';

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/**
 * Vidéo principale + effets de rythme :
 * - léger zoom continu sur chaque plan (évite les plans figés) ;
 * - à chaque coupe : zoom « punch » + flou de mouvement + flash (style CapCut).
 */
export const MainVideo: React.FC<{video: string; cuts: number[]; duration: number; brand: Brand}> = ({
  video,
  cuts,
  duration,
  brand,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const punchy = brand.style === 'punchy';

  // Zoom lent sur le plan en cours.
  const bounds = [0, ...cuts.filter((c) => c > 0 && c < duration), duration];
  let segStart = 0;
  let segEnd = duration;
  for (let i = 0; i < bounds.length - 1; i++) {
    if (t >= bounds[i] && t < bounds[i + 1]) {
      segStart = bounds[i];
      segEnd = bounds[i + 1];
    }
  }
  const drift = interpolate(t, [segStart, segEnd], [1, punchy ? 1.045 : 1.025], clamp);

  // Effet de coupe.
  const peak = punchy ? 1.14 : 1.05;
  let punch = 1;
  let blur = 0;
  let flash = 0;
  for (const c of cuts) {
    const d = frame - c * fps;
    if (d >= -5 && d < 0) {
      punch *= interpolate(d, [-5, 0], [1, peak], {...clamp, easing: Easing.in(Easing.quad)});
      blur = Math.max(blur, interpolate(d, [-5, 0], [0, punchy ? 10 : 4], clamp));
    } else if (d >= 0 && d < 8) {
      punch *= interpolate(d, [0, 8], [peak, 1], {...clamp, easing: Easing.out(Easing.cubic)});
      blur = Math.max(blur, interpolate(d, [0, 6], [punchy ? 10 : 4, 0], clamp));
      flash = Math.max(flash, interpolate(d, [0, 5], [punchy ? 0.35 : 0, 0], clamp));
    }
  }

  return (
    <AbsoluteFill style={{backgroundColor: '#000', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `scale(${drift * punch})`, filter: blur > 0.2 ? `blur(${blur}px)` : undefined}}>
        <OffthreadVideo src={staticFile(video)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </AbsoluteFill>
      {flash > 0 ? <AbsoluteFill style={{backgroundColor: '#FFFFFF', opacity: flash}} /> : null}
    </AbsoluteFill>
  );
};
