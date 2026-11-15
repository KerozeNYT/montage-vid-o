import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_FAMILY, type Brand, type BrandColors} from '../brands';
import {estimateTextWidth, safeArea} from '../layout';

/** Carton de fin : logo + nom + téléphone + compte / site (textes imposés par la marque). */
export const Outro: React.FC<{brand: Brand; colors: BrandColors; logo?: string | null}> = ({brand, colors, logo}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const safe = safeArea(width, height);
  const avail = width - safe.left - safe.right;
  const base = Math.min(width, height);
  const punchy = brand.style === 'punchy';

  const appear = (delay: number) =>
    spring({frame: frame - delay, fps, config: {damping: 15, stiffness: 140}, durationInFrames: 14});

  const [name, phone, handle] = brand.outro;
  const fit = (text: string, size: number) => Math.min(size, (avail * 0.95 * size) / estimateTextWidth(text, size));
  const nameSize = fit(name, base * 0.1);
  const phoneSize = fit(phone, base * 0.085);
  const handleSize = fit(handle, base * 0.055);

  const line = (text: string, size: number, delay: number, style: React.CSSProperties) => {
    const p = appear(delay);
    return (
      <div
        style={{
          fontFamily: FONT_FAMILY,
          fontSize: size,
          lineHeight: 1.1,
          textAlign: 'center',
          opacity: p,
          transform: `translateY(${interpolate(p, [0, 1], [30, 0])}px)`,
          ...style,
        }}
      >
        {text}
      </div>
    );
  };

  const logoP = appear(0);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.bg,
        justifyContent: 'center',
        alignItems: 'center',
        // Centré dans la zone sûre.
        paddingTop: safe.top,
        paddingBottom: safe.bottom,
        paddingLeft: safe.left,
        paddingRight: safe.right,
      }}
    >
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: base * 0.035}}>
        {logo ? (
          <Img
            src={staticFile(logo)}
            style={{
              height: base * 0.26,
              maxWidth: avail * 0.8,
              objectFit: 'contain',
              opacity: logoP,
              transform: `scale(${interpolate(logoP, [0, 1], [0.7, 1])})`,
            }}
          />
        ) : null}
        {line(name, nameSize, logo ? 6 : 0, {
          fontWeight: 900,
          letterSpacing: punchy ? '0.02em' : '0.12em',
          color: punchy ? colors.text : colors.accent,
        })}
        <div
          style={{
            width: interpolate(appear(10), [0, 1], [0, avail * 0.35]),
            height: Math.max(2, base * 0.004),
            backgroundColor: colors.accent,
          }}
        />
        {line(phone, phoneSize, 12, {fontWeight: 800, color: punchy ? colors.accent : colors.text, letterSpacing: '0.04em'})}
        {line(handle, handleSize, 18, {fontWeight: 600, color: colors.text, letterSpacing: '0.03em'})}
      </div>
    </AbsoluteFill>
  );
};
