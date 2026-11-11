import { describe, expect, it } from 'vitest';

import { DEFAULT_PARAMETERS, emptyPattern, writeCell } from '../../core/pattern';
import { type Project, emptyProject } from '../../core/project';
import { GLIDE_SECONDS, type Mix, RESONANCE_PEAK_DB, VOICE_RELEASE_SECONDS, filterSettings, initialPlaybackState, isMuted, noteRate, scheduleBar, stepOffsets } from '../playback';

const LENGTHS: Record<string, number> = { tone: 23438, hit: 2000, long: 60000 };
const length = (id: string) => LENGTHS[id];

function project(): Project {
  const p = emptyProject(120);
  p.melodic[0] = { sampleId: 'tone', start: 0, end: 23438 };
  p.melodic[1] = { sampleId: 'tone', start: 0, end: 23438 };
  p.melodic[2] = { sampleId: 'tone', start: 0, end: 23438 };
  p.melodic[3] = { sampleId: 'long', start: 0, end: 60000 };
  p.melodic[7] = { sampleId: 'tone', start: 1000, end: 3000 };
  const slices = new Array(16).fill(null);
  slices[0] = { sampleId: 'hit', start: 0, end: 2000 };
  slices[2] = { sampleId: 'hit', start: 500, end: 1500 };
  p.drums[0] = { slices };
  p.drums[2] = { slices };
  return p;
}

const note = (data: Uint8Array, step: number, sound: number, key: number, params: Partial<typeof DEFAULT_PARAMETERS> = {}) =>
  writeCell(data, step, sound, { key, pitch: 0, volume: 0, filter: 0, resonance: 0, ...params });

describe('step timing', () => {
  it('spaces sixteen steps over a bar of four beats and delays even steps by swing/24', () => {
    const straight = stepOffsets(120, 0);
    expect(straight[0]).toBe(0);
    expect(straight[1]).toBeCloseTo(0.125, 9);
    expect(straight[15]).toBeCloseTo(1.875, 9);
    const swung = stepOffsets(120, 12);
    expect(swung[0]).toBe(0);
    expect(swung[1]).toBeCloseTo(0.125 + 0.0625, 9);
    expect(swung[2]).toBeCloseTo(0.25, 9);
  });
});

describe('note laws', () => {
  it('rates: key 5 is the base, keys and the pitch code add semitones, drums take the pitch only', () => {
    expect(noteRate(1, 5, 13)).toBe(1);
    expect(noteRate(1, 6, 13)).toBeCloseTo(2 ** (2 / 12), 9);
    expect(noteRate(1, 5, 15)).toBeCloseTo(2 ** (2 / 12), 9);
    expect(noteRate(1, 13, 13)).toBeCloseTo(0.5, 9);
    expect(noteRate(9, 7, 25)).toBeCloseTo(2, 9);
  });

  it('filters: low-pass to 31, flat 32 to 43 and at 63, high-pass from 44, with the resonance peak', () => {
    expect(filterSettings(63, 1)).toBeNull();
    expect(filterSettings(0, 1)).toBeNull();
    expect(filterSettings(40, 1)).toBeNull();
    const low = filterSettings(16, 1)!;
    expect(low.type).toBe('lowpass');
    expect(low.hz).toBeGreaterThan(1300);
    expect(low.hz).toBeLessThan(1450);
    expect(low.peakDb).toBe(RESONANCE_PEAK_DB[0]);
    const high = filterSettings(52, 60)!;
    expect(high.type).toBe('highpass');
    expect(high.hz).toBeGreaterThan(1550);
    expect(high.hz).toBeLessThan(1700);
    expect(high.peakDb).toBe(13.1);
    expect(filterSettings(1, 1)!.hz).toBeCloseTo(2 ** 6.894, 2);
  });
});

describe('scheduleBar', () => {
  it('plays notes at their step times with held parameters and default values', () => {
    const p = project();
    note(p.patterns[0], 1, 1, 5);
    note(p.patterns[0], 2, 1, 6, { volume: 63 });
    note(p.patterns[0], 3, 1, 6);
    note(p.patterns[0], 5, 9, 3);
    const { events, dropped } = scheduleBar(p, length, 0, 10, initialPlaybackState());
    expect(dropped).toEqual([]);
    expect(events.map((e) => [e.step, e.sound, e.key])).toEqual([
      [1, 1, 5],
      [2, 1, 6],
      [3, 1, 6],
      [5, 9, 3],
    ]);
    expect(events[0].time).toBe(10);
    expect(events[1].time).toBeCloseTo(10.125, 9);
    expect(events[0].rate).toBe(1);
    expect(events[0].gainDb).toBe(0);
    expect(events[0].filter).toBeNull();
    expect(events[0].glideFromRate).toBeNull();
    expect(events[0].duration).toBeCloseTo(1, 3);
    // The volume lock on step 2 holds on step 3.
    expect(events[1].gainDb).toBe(7.5);
    expect(events[2].gainDb).toBe(7.5);
    expect(events[3].clip).toEqual({ sampleId: 'hit', start: 500, end: 1500 });
    // Three one-second tones still sound at step 5, so the hit takes the fourth voice.
    expect(events[3].voice).toBe(3);
  });

  it('glides into a pitch change on the same sound, and not into a key change', () => {
    const p = project();
    note(p.patterns[0], 1, 1, 5, { pitch: 13 });
    note(p.patterns[0], 2, 1, 6);
    note(p.patterns[0], 3, 1, 6, { pitch: 15 });
    note(p.patterns[0], 4, 1, 6);
    const { events } = scheduleBar(p, length, 0, 0, initialPlaybackState());
    expect(events[0].glideFromRate).toBeNull();
    expect(events[1].glideFromRate).toBeNull();
    expect(events[2].glideFromRate).toBeCloseTo(events[2].rate * 2 ** (-2 / 12), 9);
    expect(events[3].glideFromRate).toBeNull();
    expect(GLIDE_SECONDS).toBeGreaterThan(0.02);
  });

  it('carries held locks and voices into the next bar', () => {
    const p = project();
    note(p.patterns[0], 16, 1, 5, { filter: 16, resonance: 56 });
    note(p.patterns[1], 1, 1, 5);
    const first = scheduleBar(p, length, 0, 0, initialPlaybackState());
    const second = scheduleBar(p, length, 1, 2, first.state);
    expect(second.events[0].filter).toEqual(filterSettings(16, 56));
    expect(second.events[0].glideFromRate).toBeNull();
  });

  it('gives four voices by rank and drops the rest; a voice frees in its last 100 ms', () => {
    const p = project();
    for (const sound of [1, 2, 3, 4]) note(p.patterns[0], 1, sound, 5);
    note(p.patterns[0], 1, 11, 1);
    const { events, dropped } = scheduleBar(p, length, 0, 0, initialPlaybackState());
    expect(events.map((e) => e.sound)).toEqual([1, 2, 3, 11]);
    expect(dropped).toEqual([{ step: 1, sound: 4, key: 5 }]);
    // Sound 4's long note holds a voice; a one-second tone ends within 100 ms of step 9 (1.0 s), so a new note there plays.
    const q = project();
    note(q.patterns[0], 1, 1, 5);
    note(q.patterns[0], 1, 2, 5);
    note(q.patterns[0], 1, 3, 5);
    note(q.patterns[0], 1, 4, 5);
    note(q.patterns[0], 8, 8, 5);
    note(q.patterns[0], 9, 8, 5);
    const run = scheduleBar(q, length, 0, 0, initialPlaybackState());
    expect(run.dropped).toEqual([{ step: 8, sound: 8, key: 5 }]);
    expect(run.events.filter((e) => e.sound === 8).map((e) => e.step)).toEqual([9]);
    expect(VOICE_RELEASE_SECONDS).toBe(0.1);
  });

  it('skips keys without a sample and windows past the sample, and clamps windows to the sample', () => {
    const p = project();
    note(p.patterns[0], 1, 9, 2);
    note(p.patterns[0], 2, 16, 1);
    p.melodic[7] = { sampleId: 'tone', start: 23000, end: 30000 };
    note(p.patterns[0], 3, 8, 5);
    const { events } = scheduleBar(p, length, 0, 0, initialPlaybackState());
    expect(events.map((e) => [e.step, e.sound])).toEqual([[3, 8]]);
    expect(events[0].clip.end).toBe(23438);
  });

  it('starts every sound at the device defaults', () => {
    const state = initialPlaybackState();
    expect(state.held[0]).toEqual(DEFAULT_PARAMETERS);
    expect(state.held[15]).toEqual(DEFAULT_PARAMETERS);
    expect(emptyPattern().length).toBe(1032);
  });
});

describe('mute and solo', () => {
  const mix = (over: Partial<Mix>): Mix => ({ mutes: [], solos: [], sliceMutes: [], sliceSolos: [], ...over });

  it('mutes a sound, and a solo anywhere silences the others', () => {
    expect(isMuted(mix({}), 3, 5)).toBe(false);
    expect(isMuted(mix({ mutes: [false, false, true] }), 3, 5)).toBe(true);
    const solo2 = mix({ solos: [false, true] });
    expect(isMuted(solo2, 2, 5)).toBe(false);
    expect(isMuted(solo2, 1, 5)).toBe(true);
    expect(isMuted(solo2, 9, 1)).toBe(true);
  });

  it('mutes and solos keys within a drum sound without touching other sounds', () => {
    const keyMute = mix({ sliceMutes: [[false, true]] });
    expect(isMuted(keyMute, 9, 2)).toBe(true);
    expect(isMuted(keyMute, 9, 1)).toBe(false);
    expect(isMuted(keyMute, 10, 2)).toBe(false);
    const keySolo = mix({ sliceSolos: [[false, false, true]] });
    expect(isMuted(keySolo, 9, 3)).toBe(false);
    expect(isMuted(keySolo, 9, 1)).toBe(true);
    expect(isMuted(keySolo, 1, 5)).toBe(false);
  });

  it('keeps muted notes in the voice count but marks them silent', () => {
    const p = project();
    for (const sound of [1, 2, 3, 4]) note(p.patterns[0], 1, sound, 5);
    note(p.patterns[0], 1, 11, 1);
    const { events, dropped } = scheduleBar(p, length, 0, 0, initialPlaybackState(), mix({ mutes: [true] }));
    expect(events.map((e) => [e.sound, e.muted])).toEqual([
      [1, true],
      [2, false],
      [3, false],
      [11, false],
    ]);
    expect(dropped.map((d) => d.sound)).toEqual([4]);
  });
});

describe('note timing (aux-nibble-results, -2, -3)', () => {
  const timed = (data: Uint8Array, step: number, sound: number, key: number, timing?: number) =>
    writeCell(data, step, sound, { key, pitch: 0, volume: 0, filter: 0, resonance: 0, timing });
  const at60 = () => {
    const p = project();
    p.tempo = 60;
    p.swing = 0;
    return p;
  };

  it('a drum retrigger plays n hits a step/n apart on one voice, each cut by the next (60 BPM)', () => {
    const p = at60();
    timed(p.patterns[0], 1, 9, 1, 4);
    const { events, dropped } = scheduleBar(p, length, 0, 0, initialPlaybackState());
    const hits = events.filter((e) => e.sound === 9);
    expect(dropped).toEqual([]);
    expect(hits.map((e) => e.time)).toEqual([0, 0.0625, 0.125, 0.1875]);
    expect(new Set(hits.map((e) => e.voice)).size).toBe(1);
    // The 85 ms hit restarts every 62.5 ms; the last plays out.
    expect(hits.map((e) => +e.duration.toFixed(4))).toEqual([0.0625, 0.0625, 0.0625, +(2000 / 23437.5).toFixed(4)]);
  });

  it('the repeats never need another voice: with three voices held, all four hits still play', () => {
    const p = at60();
    for (const sound of [1, 2, 3]) timed(p.patterns[0], 1, sound, 5);
    timed(p.patterns[0], 1, 9, 1, 4);
    const { events, dropped } = scheduleBar(p, length, 0, 0, initialPlaybackState());
    expect(dropped).toEqual([]);
    expect(events.filter((e) => e.sound === 9)).toHaveLength(4);
    // The held tones play out, whole: the retriggers cut nothing of theirs.
    for (const held of events.filter((e) => e.sound <= 3)) expect(held.duration).toBeCloseTo(23438 / 23437.5, 6);
  });

  it('a melodic note lasts its length in steps; F (the default) plays the whole sample', () => {
    const p = at60();
    timed(p.patterns[0], 1, 4, 5, 2);
    timed(p.patterns[0], 9, 4, 5);
    const long = scheduleBar(p, length, 0, 0, initialPlaybackState()).events.filter((e) => e.sound === 4);
    expect(long[0].duration).toBeCloseTo(0.5, 6);
    expect(long[1].duration).toBeCloseTo(60000 / 23437.5, 6);
  });

  it('under swing a note starts late but its time ends on the unswung grid (120 BPM, swing 12)', () => {
    const p = project();
    p.tempo = 120;
    p.swing = 12;
    timed(p.patterns[0], 1, 9, 1, 4);
    timed(p.patterns[0], 2, 11, 1, 4);
    timed(p.patterns[0], 3, 4, 5, 1);
    timed(p.patterns[0], 6, 4, 5, 1);
    const { events } = scheduleBar(p, length, 0, 0, initialPlaybackState());
    // Odd step: all four repeats, 31.25 ms apart. Even step (62.5 ms late): only the two before the next grid line.
    expect(events.filter((e) => e.sound === 9).map((e) => +e.time.toFixed(5))).toEqual([0, 0.03125, 0.0625, 0.09375]);
    expect(events.filter((e) => e.sound === 11).map((e) => +e.time.toFixed(5))).toEqual([0.1875, 0.21875]);
    // One step: 125 ms from an odd step, 62.5 ms from an even one.
    const melodic = events.filter((e) => e.sound === 4);
    expect(melodic[0].duration).toBeCloseTo(0.125, 6);
    expect(melodic[1].duration).toBeCloseTo(0.0625, 6);
  });
});
