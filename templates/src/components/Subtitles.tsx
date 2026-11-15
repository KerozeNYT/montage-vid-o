import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT_FAMILY, type Brand, type BrandColors} from '../brands';
import {estimateTextWidth, safeArea, subtitleCenterY} from '../layout';
import type {Word} from '../types';

type Page = {words: Word[]; start: number; end: number};

/** Regroupe les mots en « pages » courtes (2 lignes max), coupées aux pauses et à la ponctuation. */
export const buildPages = (words: Word[], maxWords: number, maxChars: number): Page[] => {
  const pages: Page[] = [];
  let cur: Word[] = [];
  const flush = () => {
    if (cur.length === 0) return;
    pages.push({words: cur, start: cur[0].start, end: cur[cur.length - 1].end});
    cur = [];
  };
  for (const w of words) {
    const prev = cur[cur.length - 1];
    const chars = cur.reduce((n, x) => n + x.text.length + 1, 0) + w.text.length;
    if (prev && (cur.length >= maxWords || chars > maxChars || w.start - prev.end > 0.6)) flush();
    cur.push(w);
    if (/[.!?…]$/.test(w.text) || (/[,;:]$/.test(w.text) && cur.length >= 2)) flush();
  }
  flush();
  // Garde chaque page à l'écran jusqu'à la suivante (au plus +0,5 s) pour éviter le clignotement.
  pages.forEach((p, i) => {
    const next = pages[i + 1];
    const hold = p.end + 0.5;
    p.end = next ? Math.max(p.end, Math.min(next.start, hold)) : hold;
  });
  return pages;
};

const wordStyle = (brand: Brand, colors: BrandColors, fontSize: number): React.CSSProperties =>
  brand.style === 'punchy'
    ? {
        fontWeight: 900,
        textTransform: 'uppercase',
        WebkitTextStroke: `${Math.round(fontSize * 0.1)}px ${colors.stroke}`,
        paintOrder: 'stroke fill',
        textShadow: `0 ${fontSize * 0.06}px ${fontSize * 0.2}px rgba(0,0,0,0.6)`,
        letterSpacing: '0.01em',
      }
    : {
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        textShadow: `0 0 ${fontSize * 0.25}px rgba(0,0,0,0.85), 0 ${fontSize * 0.04}px ${fontSize * 0.08}px rgba(0,0,0,0.9)`,
      };

export const Subtitles: React.FC<{words: Word[]; brand: Brand; colors: BrandColors}> = ({
  words,
  brand,
  colors,
}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const t = frame / fps;
  const portrait = height > width;
  const pages = useMemo(
    () => buildPages(words, portrait ? 3 : 5, portrait ? 18 : 30),
    [words, portrait],
  );
  const page = pages.find((p) => t >= p.start && t < p.end);
  if (!page) return null;

  const safe = safeArea(width, height);
  const avail = width - safe.left - safe.right;
  // Taille de base, réduite si un mot ou la page entière risque de dépasser (2 lignes max).
  let fontSize = Math.min(width, height) * (brand.style === 'punchy' ? 0.088 : 0.07);
  const longest = Math.max(...page.words.map((w) => estimateTextWidth(w.text, fontSize)));
  if (longest > avail) fontSize *= avail / longest;
  const full = estimateTextWidth(page.words.map((w) => w.text).join(' '), fontSize);
  if (full > avail * 1.9) fontSize *= (avail * 1.9) / full;

  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          left: safe.left,
          width: avail,
          top: subtitleCenterY(width, height),
          transform: 'translateY(-50%)',
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          columnGap: fontSize * 0.32,
          rowGap: fontSize * 0.05,
          fontFamily: FONT_FAMILY,
          fontSize,
          lineHeight: 1.12,
          textAlign: 'center',
        }}
      >
        {page.words.map((w, i) => {
          const next = page.words[i + 1];
          const shown = t >= w.start - 0.03;
          const active = shown && t < (next ? next.start : page.end);
          const pop = spring({
            frame: frame - Math.round(w.start * fps),
            fps,
            config: {damping: 14, stiffness: 220, mass: 0.6},
            durationInFrames: 8,
          });
          // Apparition « pop » uniquement (jamais > 1 : les mots ne se chevauchent pas).
          const scale = brand.style === 'punchy' ? interpolate(pop, [0, 1], [0.55, 1]) : 1;
          const opacity = shown ? (brand.style === 'punchy' ? 1 : interpolate(pop, [0, 1], [0, 1])) : 0;
          return (
            <span
              key={`${w.start}-${i}`}
              style={{
                ...wordStyle(brand, colors, fontSize),
                display: 'inline-block',
                color: active ? colors.accent : colors.text,
                opacity,
                transform: `scale(${scale})`,
              }}
            >
              {w.text}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
