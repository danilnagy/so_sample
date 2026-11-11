import { beforeEach, describe, expect, it, vi } from 'vitest';

import { writeCell } from '../../core/pattern';
import { type Project, emptyProject } from '../../core/project';
import { SILENT_MIX } from '../playback';

/** A clock and node factory standing in for Web Audio: sources remember when they were started and stopped. */
const fake = {
  currentTime: 0,
  started: [] as { time: number; stopped: boolean }[],
};
const param = () => {
  const p = { value: 0, target: null as number | null, setValueAtTime() {}, exponentialRampToValueAtTime() {}, cancelScheduledValues() {}, setTargetAtTime(v: number) {
    p.target = v;
  } };
  return p;
};
const gains: { gain: ReturnType<typeof param> }[] = [];
const node = () => ({ connect() {}, disconnect() {} });
vi.mock('../samples', () => ({
  audioContext: () => ({
    get currentTime() {
      return fake.currentTime;
    },
    destination: {},
    createGain: () => {
      const g = { ...node(), gain: param() };
      gains.push(g);
      return g;
    },
    createBiquadFilter: () => ({ ...node(), type: '', frequency: param(), Q: param() }),
    createDynamicsCompressor: () => ({ ...node(), threshold: param(), knee: param(), ratio: param(), attack: param(), release: param() }),
    createBuffer: (_c: number, length: number) => ({ getChannelData: () => new Float32Array(length) }),
    createBufferSource: () => {
      const entry = { time: 0, stopped: false };
      return {
        ...node(),
        buffer: null,
        playbackRate: param(),
        onended: null,
        start(time: number) {
          entry.time = time;
          fake.started.push(entry);
        },
        stop() {
          entry.stopped = true;
        },
      };
    },
  }),
}));

const { Player } = await import('../player');

function project(): Project {
  const p = emptyProject(120);
  p.melodic[0] = { sampleId: 's', start: 0, end: 2000 };
  for (let i = 0; i < 3; i++) writeCell(p.patterns[i], 1, 1, { key: 5, pitch: 0, volume: 0, filter: 0, resonance: 0 });
  p.chain = [2, 3];
  return p;
}

/** Move the clock forward the way a browser does: in small steps, the scheduler ticking as it goes. */
function advanceTo(time: number): void {
  while (fake.currentTime < time - 1e-9) {
    fake.currentTime = Math.min(time, fake.currentTime + 0.1);
    vi.advanceTimersByTime(25);
  }
}

describe('Player', () => {
  beforeEach(() => {
    fake.currentTime = 0;
    fake.started = [];
    gains.length = 0;
    vi.useFakeTimers();
  });

  it('reports the key each sound is sounding for as long as its note lasts', () => {
    const live = project();
    // A longer window on Sound 1: 20000 codes is 0.85 s at the base key.
    live.melodic[0] = { sampleId: 's', start: 0, end: 20000 };
    const player = new Player({
      project: () => ({ id: 'p', project: live, mix: { mutes: [], solos: [], sliceMutes: [], sliceSolos: [] } }),
      resolver: () => () => new Uint8Array(20000),
      selectedPattern: () => 1,
      onStop: () => {},
    });
    expect(player.sounding().every((k) => k === null)).toBe(true);
    player.start('pattern');
    // The bar starts at 0.05 s; the step-1 note sounds from then until about 0.9 s.
    advanceTo(0.3);
    expect(player.sounding()[0]).toBe(5);
    expect(player.sounding()[1]).toBeNull();
    advanceTo(1.2);
    expect(player.sounding()[0]).toBeNull();
    // The next bar's note at 2.05 s sounds again.
    advanceTo(2.3);
    expect(player.sounding()[0]).toBe(5);
    player.stop();
    expect(player.sounding()[0]).toBeNull();
  });

  it('plays a note added to the pattern mid-bar on its step, not a bar later', () => {
    const live = project();
    const player = new Player({
      project: () => ({ id: 'p', project: live, mix: { mutes: [], solos: [], sliceMutes: [], sliceSolos: [] } }),
      resolver: () => () => new Uint8Array(2000),
      selectedPattern: () => 1,
      onStop: () => {},
    });
    player.start('pattern');
    // The bar runs 0.05 to 2.05 s; step 9 falls at 1.05 s. At 0.5 s add a note there.
    advanceTo(0.5);
    writeCell(live.patterns[0], 9, 1, { key: 5, pitch: 0, volume: 0, filter: 0, resonance: 0 });
    advanceTo(1.2);
    expect(fake.started.filter((s) => Math.abs(s.time - 1.05) < 0.01).length).toBe(1);
    // And one removed before its step comes into view never sounds.
    writeCell(live.patterns[0], 13, 1, { key: 5, pitch: 0, volume: 0, filter: 0, resonance: 0 });
    advanceTo(1.3);
    writeCell(live.patterns[0], 13, 1, null);
    advanceTo(1.8);
    expect(fake.started.filter((s) => Math.abs(s.time - 1.55) < 0.01).length).toBe(0);
    player.stop();
  });

  it('applies a mute at once, through a gain the sounding notes already pass', () => {
    let mix = { mutes: [] as boolean[], solos: [] as boolean[], sliceMutes: [] as boolean[][], sliceSolos: [] as boolean[][] };
    const player = new Player({
      project: () => ({ id: 'p', project: project(), mix }),
      resolver: () => () => new Uint8Array(2000),
      selectedPattern: () => 1,
      onStop: () => {},
    });
    player.start('pattern');
    advanceTo(0.5);
    const before = gains.filter((g) => g.gain.target === 0).length;
    mix = { ...mix, mutes: [true] };
    advanceTo(0.6);
    const muted = gains.filter((g) => g.gain.target === 0).length;
    mix = { ...mix, mutes: [] };
    advanceTo(0.7);
    const back = gains.filter((g) => g.gain.target === 0).length;
    expect([before, muted, back]).toEqual([0, 1, 0]);
    player.stop();
  });

  it('switches mode at the end of the bar sounding, cancelling bars queued past it', () => {
    const stopped: string[] = [];
    const player = new Player({
      project: () => ({ id: 'p', project: project(), mix: SILENT_MIX }),
      resolver: () => () => new Uint8Array(2000),
      selectedPattern: () => 1,
      onStop: () => stopped.push('stop'),
    });
    player.start('pattern');
    // At 120 BPM a bar is 2 s; the first bar starts 50 ms in. Move into it.
    advanceTo(1.0);
    expect(player.position()).toMatchObject({ mode: 'pattern', pattern: 1, entry: null });
    // Near its end the next bar is queued in pattern mode.
    advanceTo(1.9);
    const queued = fake.started.filter((s) => s.time > 1.9);
    expect(queued.length).toBe(1);
    // Switching now keeps the bar sounding and cancels the queued one.
    player.setMode('song');
    expect(queued[0].stopped).toBe(true);
    expect(player.position()).toMatchObject({ mode: 'pattern', pattern: 1 });
    // Into the next bar: the song's first entry, pattern 2.
    advanceTo(2.2);
    expect(player.position()).toMatchObject({ mode: 'song', pattern: 2, entry: 0 });
    advanceTo(4.2);
    expect(player.position()).toMatchObject({ mode: 'song', pattern: 3, entry: 1 });
    // Back to pattern mode: the selected pattern, from the next bar.
    player.setMode('pattern');
    expect(player.position()).toMatchObject({ mode: 'song', pattern: 3 });
    advanceTo(6.2);
    expect(player.position()).toMatchObject({ mode: 'pattern', pattern: 1, entry: null });
    player.stop();
    expect(player.position()).toBeNull();
    expect(stopped).toEqual([]);
  });
});
