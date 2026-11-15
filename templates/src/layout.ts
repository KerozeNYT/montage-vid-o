// Zones sûres : rien d'important sous l'interface TikTok / Reels / YouTube.
export type Safe = {top: number; bottom: number; left: number; right: number};

export const safeArea = (width: number, height: number): Safe => {
  if (height > width) {
    const s = width / 1080; // 9:16
    return {top: 250 * s, bottom: 450 * s, left: 120 * s, right: 120 * s};
  }
  if (height === width) {
    const s = width / 1080; // 1:1
    return {top: 90 * s, bottom: 130 * s, left: 70 * s, right: 70 * s};
  }
  const s = width / 1920; // 16:9
  return {top: 70 * s, bottom: 100 * s, left: 110 * s, right: 110 * s};
};

/** Hauteur (px) du centre des sous-titres. */
export const subtitleCenterY = (width: number, height: number): number => {
  if (height > width) return height * 0.62;
  if (height === width) return height * 0.74;
  return height * 0.8;
};

/** Haut du bloc accroche / titres. */
export const titleTopY = (width: number, height: number): number => {
  const safe = safeArea(width, height);
  if (height > width) return safe.top + height * 0.06;
  return safe.top + height * 0.04;
};

/** Largeur estimée d'un texte en capitales grasses (prudente, pour éviter tout débordement). */
export const estimateTextWidth = (text: string, fontSize: number): number =>
  text.length * fontSize * 0.68;
