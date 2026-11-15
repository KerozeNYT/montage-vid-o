// Charte de chaque marque. Les textes d'outro sont imposés par CLAUDE.md : ne pas les modifier.
export type BrandId = 'solar-car' | 'solar-home';

export type BrandColors = {
  bg: string; // fond de l'outro
  text: string; // texte principal
  accent: string; // mot actif des sous-titres, titres
  stroke: string; // contour des sous-titres
};

export type Brand = {
  name: string;
  outro: [string, string, string];
  colors: BrandColors;
  /** punchy = style CapCut appuyé ; sobre = élégant, peu d'effets */
  style: 'punchy' | 'sobre';
  /** true tant que l'utilisateur n'a pas fourni ses codes couleur exacts */
  provisionalColors: boolean;
};

export const BRANDS: Record<BrandId, Brand> = {
  'solar-car': {
    name: 'SOLAR CAR 37',
    outro: ['SOLAR CAR 37', '06 12 04 57 00', '@solarcar37'],
    // PROVISOIRE : couleurs à confirmer par l'utilisateur.
    colors: {bg: '#0A0A0A', text: '#FFFFFF', accent: '#FFD60A', stroke: '#000000'},
    style: 'punchy',
    provisionalColors: true,
  },
  'solar-home': {
    name: 'SOLAR HOME 37',
    outro: ['SOLAR HOME 37', '06 07 49 31 83', 'www.solarhome37.fr'],
    // Noir et doré. PROVISOIRE : code exact du doré à confirmer par l'utilisateur.
    colors: {bg: '#000000', text: '#FFFFFF', accent: '#C9A24A', stroke: '#000000'},
    style: 'sobre',
    provisionalColors: true,
  },
};

export const FONT_FAMILY = "'BrandFont', 'Inter', 'Helvetica Neue', Arial, sans-serif";
