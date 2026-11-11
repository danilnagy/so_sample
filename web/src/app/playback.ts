/**
 * Preview scheduling: what the device plays for one bar of a pattern, from the measured
 * laws (docs/format-reference.md). Step times carry the swing; every note takes the
 * parameters its sound holds (the last lock, as the device keeps them across steps and
 * bars); pitch, volume and filter follow the measured tables; four voices with the
 * measured priority and release. The punch-in effects are not reproduced.
 *
 * This module is pure: it turns a project into timed note events and keeps the
 * per-sound and per-voice state between bars. The player turns the events into audio.
 */

import { SAMPLE_RATE } from '../core/mulaw';
import { DEFAULT_PARAMETERS, PARAMETER_NAMES, type Parameters, STEPS, readCell } from '../core/pattern';
import type { Clip, Project } from '../core/project';
import { VOICE_RANK, keySemitones, resonanceLevel, volumeDb } from './laws';

export const VOICES = 4;
/** A voice takes a new note when it is free or this close to its end (voice-release). */
export const VOICE_RELEASE_SECONDS = 0.1;
/** A pitch change glides from the previous pitch for about this long (pitch-law). */
export const GLIDE_SECONDS = 0.03;
/** Peak response at the filter edge per resonance level 1..8 (resonance-law). */
export const RESONANCE_PEAK_DB = [-6.8, -2.8, -0.3, 1.2, 3.8, 5.8, 8.9, 13.1];

export interface FilterSettings {
  type: 'lowpass' | 'highpass';
  hz: number;
  /** The peak at the edge, in dB, from the resonance level. */
  peakDb: number;
}

export interface NoteEvent {
  step: number;
  sound: number;
  key: number;
  /** Absolute time, in the player's clock. */
  time: number;
  clip: Clip;
  /** Playback rate against the stored sample. */
  rate: number;
  /** Where the glide starts, or null when the pitch has not changed. */
  glideFromRate: number | null;
  gainDb: number;
  filter: FilterSettings | null;
  voice: number;
  /** Seconds the note sounds at its rate. */
  duration: number;
  /** Silenced by the preview's mix; the note still takes its voice, as the device would play it. */
  muted: boolean;
}

/** What the preview silences: mute and solo per sound, and per key of each drum sound (8 kits x 16 keys). */
export interface Mix {
  mutes: boolean[];
  solos: boolean[];
  sliceMutes: boolean[][];
  sliceSolos: boolean[][];
}

export const SILENT_MIX: Mix = { mutes: [], solos: [], sliceMutes: [], sliceSolos: [] };

/** Whether the mix silences a whole sound: muted, or left out of the solo set. */
export function soundSilent(mix: Mix, sound: number): boolean {
  return !!mix.mutes[sound - 1] || (mix.solos.some(Boolean) && !mix.solos[sound - 1]);
}

/** Whether the mix silences a note; a solo anywhere silences everything not soloed at that level. */
export function isMuted(mix: Mix, sound: number, key: number): boolean {
  if (soundSilent(mix, sound)) return true;
  if (sound <= 8) return false;
  const mutes = mix.sliceMutes[sound - 9] ?? [];
  const solos = mix.sliceSolos[sound - 9] ?? [];
  return !!mutes[key - 1] || (solos.some(Boolean) && !solos[key - 1]);
}

export interface DroppedNote {
  step: number;
  sound: number;
  key: number;
}

/** What carries from bar to bar: held parameters and last pitch per sound, and when each voice ends. */
export interface PlaybackState {
  held: Parameters[];
  lastPitch: (number | null)[];
  /** When each voice's note started and ends. */
  voiceStarts: number[];
  voiceEnds: number[];
}

export function initialPlaybackState(): PlaybackState {
  return {
    held: Array.from({ length: 16 }, () => ({ ...DEFAULT_PARAMETERS })),
    lastPitch: new Array(16).fill(null),
    voiceStarts: new Array(VOICES).fill(-Infinity),
    voiceEnds: new Array(VOICES).fill(-Infinity),
  };
}

/** Seconds per step: sixteen steps to a bar of four beats. */
export function stepSeconds(tempo: number): number {
  return 60 / tempo / 4;
}

/** Offset of each step from the bar's start; even steps are delayed by swing/24 of a step (swing-law). */
export function stepOffsets(tempo: number, swing: number): number[] {
  const step = stepSeconds(tempo);
  return Array.from({ length: STEPS }, (_, i) => i * step + (i % 2 === 1 ? (swing / 24) * step : 0));
}

export function barSeconds(tempo: number): number {
  return stepSeconds(tempo) * STEPS;
}

/** The filter a code sets, with the resonance level's peak; null where the device is flat (filter-law). */
export function filterSettings(filterCode: number, resonanceCode: number): FilterSettings | null {
  const peakDb = RESONANCE_PEAK_DB[resonanceLevel(Math.max(1, Math.min(63, resonanceCode))) - 1];
  if (filterCode >= 1 && filterCode <= 31) return { type: 'lowpass', hz: Math.min(11000, 2 ** (0.234 * filterCode + 6.66)), peakDb };
  if (filterCode >= 44 && filterCode <= 62) return { type: 'highpass', hz: Math.max(20, 2 ** (0.262 * filterCode - 2.94)), peakDb };
  return null;
}

/** Playback rate of a note: the key's interval for a melodic sound, and the pitch code for every sound (pitch-law, drum-pitch). */
export function noteRate(sound: number, key: number, pitch: number): number {
  const semitones = (sound <= 8 ? keySemitones(key) : 0) + pitch - 13;
  return 2 ** (semitones / 12);
}

function clipOf(project: Project, sound: number, key: number): Clip | null {
  if (sound <= 8) return project.melodic[sound - 1];
  return project.drums[sound - 9]?.slices[key - 1] ?? null;
}

export interface Scheduled {
  events: NoteEvent[];
  dropped: DroppedNote[];
  state: PlaybackState;
}

function copyState(state: PlaybackState): PlaybackState {
  return {
    held: state.held.map((p) => ({ ...p })),
    lastPitch: state.lastPitch.slice(),
    voiceStarts: state.voiceStarts.slice(),
    voiceEnds: state.voiceEnds.slice(),
  };
}

/**
 * The notes of one bar of a pattern, starting at `barStart`. Returns the events, the
 * notes the four voices could not take, and the state to carry into the next bar.
 */
export function scheduleBar(
  project: Project,
  sampleLength: (sampleId: string) => number,
  patternIndex: number,
  barStart: number,
  state: PlaybackState,
  mix: Mix = SILENT_MIX,
): Scheduled {
  const offsets = stepOffsets(project.tempo, project.swing);
  let next = state;
  const events: NoteEvent[] = [];
  const dropped: DroppedNote[] = [];
  for (let step = 1; step <= STEPS; step++) {
    const result = scheduleStep(project, sampleLength, patternIndex, step, barStart + offsets[step - 1], next, mix);
    next = result.state;
    events.push(...result.events);
    dropped.push(...result.dropped);
  }
  return { events, dropped, state: next };
}

/**
 * The notes of one step of a pattern at `time`, from the pattern as it is now, so an edit
 * reaches the next step the player schedules rather than the next bar.
 */
export function scheduleStep(
  project: Project,
  sampleLength: (sampleId: string) => number,
  patternIndex: number,
  step: number,
  time: number,
  state: PlaybackState,
  mix: Mix = SILENT_MIX,
): Scheduled {
  const data = project.patterns[patternIndex];
  const next = copyState(state);
  const events: NoteEvent[] = [];
  const dropped: DroppedNote[] = [];
  {
    // Locks apply first, note or not; then the notes on this step take voices in rank order.
    const notes: { sound: number; key: number }[] = [];
    for (const sound of VOICE_RANK) {
      const cell = readCell(data, step, sound);
      if (!cell) continue;
      const held = next.held[sound - 1];
      for (const p of PARAMETER_NAMES) if (cell[p]) held[p] = cell[p];
      if (cell.key) notes.push({ sound, key: cell.key });
    }
    for (const { sound, key } of notes) {
      const clip = clipOf(project, sound, key);
      if (!clip) continue;
      const length = sampleLength(clip.sampleId);
      const end = Math.min(clip.end, length);
      if (end <= clip.start) continue;
      const held = next.held[sound - 1];
      const rate = noteRate(sound, key, held.pitch);
      const previous = next.lastPitch[sound - 1];
      const glideFromRate = previous !== null && previous !== held.pitch ? rate * 2 ** ((previous - held.pitch) / 12) : null;
      next.lastPitch[sound - 1] = held.pitch;
      const duration = (end - clip.start) / SAMPLE_RATE / rate;
      // A voice is free when its note ends within the release window; a note that starts on this
      // very step is sounding, however short, and is never cut for another.
      const voice = next.voiceEnds.findIndex((voiceEnd, i) => voiceEnd - time <= VOICE_RELEASE_SECONDS && next.voiceStarts[i] < time);
      if (voice < 0) {
        dropped.push({ step, sound, key });
        continue;
      }
      next.voiceStarts[voice] = time;
      next.voiceEnds[voice] = time + duration;
      events.push({
        step,
        sound,
        key,
        time,
        clip: { ...clip, end },
        rate,
        glideFromRate,
        gainDb: volumeDb(held.volume),
        filter: filterSettings(held.filter, held.resonance),
        voice,
        duration,
        muted: isMuted(mix, sound, key),
      });
    }
  }
  return { events, dropped, state: next };
}
