import type {MontageProps} from './types';

export const FPS = 30;
/** Durée de l'outro (2,8 s). */
export const OUTRO_FRAMES = 84;
/** Durée de la transition vidéo → outro (0,4 s). */
export const OUTRO_TRANSITION_FRAMES = 12;

export const mainFrames = (props: MontageProps, fps: number): number =>
  Math.max(1, Math.round(props.videoDuration * fps));

export const totalFrames = (props: MontageProps, fps: number): number =>
  mainFrames(props, fps) + OUTRO_FRAMES - OUTRO_TRANSITION_FRAMES;
