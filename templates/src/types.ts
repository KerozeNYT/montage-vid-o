import type {BrandColors, BrandId} from './brands';

/** Un mot prononcé, en secondes sur la timeline de la vidéo principale. */
export type Word = {text: string; start: number; end: number};

/** Texte affiché à l'écran entre deux instants (secondes). */
export type Title = {text: string; start: number; end: number};

export type MontageProps = {
  brand: BrandId;
  /** Vidéo principale déjà coupée et cadrée, relative au dossier public. */
  video: string;
  /** Durée de la vidéo principale, en secondes. */
  videoDuration: number;
  /** Sous-titres mot par mot (vides = pas de sous-titres). */
  words: Word[];
  /** Instants (s) des changements de plan : effet de transition à chaque coupe. */
  cuts: number[];
  /** Accroche des 2 premières secondes. */
  hook?: string | null;
  hookDuration?: number;
  titles?: Title[];
  music?: string | null;
  /** Volume de la musique quand personne ne parle (0–1). */
  musicVolume?: number;
  logo?: string | null;
  font?: string | null;
  /** Remplace les couleurs de la marque (optionnel). */
  colors?: Partial<BrandColors> | null;
};
