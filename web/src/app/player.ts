/**
 * The preview player: schedules the pattern onto Web Audio one step at a time, 200 ms
 * ahead of the clock, reading the pattern as it is at that moment, so an edit sounds on
 * the next step rather than the next bar; and reports where it is for the cursor.
 *
 * Each note is a buffer source at its rate (gliding into a pitch change), through a
 * biquad for the filter where the device filters, a gain for the volume, then the gain
 * of its sound (and of its key, for a drum) which the mix sets live for mute and solo. A
 * master gain sets one full-volume voice to full scale and a limiter catches the sum of
 * four.
 */

import { SAMPLE_RATE, decodeMulawCodes } from '../core/mulaw';
import { STEPS } from '../core/pattern';
import type { Project, SampleResolver } from '../core/project';
import { GLIDE_SECONDS, type Mix, type PlaybackState, barSeconds, initialPlaybackState, scheduleStep, soundSilent, stepOffsets } from './playback';

/** The fade at a note's cut (its length, or the next repeat): short enough to keep a 15 ms retrigger distinct. */
const CUT_FADE_SECONDS = 0.004;
import { audioContext } from './samples';
import { volumeDb } from './laws';

export type PlaybackMode = 'pattern' | 'song';

export interface PlaybackPosition {
  mode: PlaybackMode;
  /** Pattern number 1..16 and step 1..16 now sounding. */
  pattern: number;
  step: number;
  /** In song mode, the index of the chain entry sounding; null in pattern mode. */
  entry: number | null;
}

export interface PlayerHost {
  /** The project to play, or null when none; a change of id stops the player. */
  project(): { id: string; project: Project; mix: Mix } | null;
  resolver(): SampleResolver;
  selectedPattern(): number;
  /** Called when the player stops on its own. */
  onStop(): void;
  /** Called as each bar starts sounding. */
  onBar?(position: PlaybackPosition): void;
}

/** One scheduled step: when it sounds, what to restore if it is cancelled, and its sources. */
interface Step {
  step: number;
  time: number;
  stateBefore: PlaybackState;
  sources: AudioBufferSourceNode[];
  notes: SoundingNote[];
}

/** A scheduled note's span, for showing which key each sound is sounding. */
interface SoundingNote {
  sound: number;
  key: number;
  start: number;
  end: number;
}

/** A bar being scheduled or sounding; its steps are added as the clock approaches them. */
interface Bar {
  start: number;
  mode: PlaybackMode;
  pattern: number;
  entry: number | null;
  offsets: number[];
  length: number;
  chainIndexBefore: number;
  steps: Step[];
}

/** Steps are scheduled this far ahead of the clock, on this tick. */
const LOOKAHEAD_SECONDS = 0.2;
const TICK_MS = 25;

export class Player {
  private readonly host: PlayerHost;
  private mode: PlaybackMode = 'pattern';
  private timer: ReturnType<typeof setInterval> | null = null;
  private projectId: string | null = null;
  private state: PlaybackState = initialPlaybackState();
  private nextBarStart = 0;
  private chainIndex = 0;
  private bars: Bar[] = [];
  private readonly sources = new Set<AudioBufferSourceNode>();
  /** The notes scheduled so far that may still be sounding, pruned as they end. */
  private notes: SoundingNote[] = [];
  /** How to tear down each scheduled note's nodes, for notes cancelled before they start. */
  private readonly releases = new Map<AudioBufferSourceNode, () => void>();
  private readonly buffers = new Map<string, { codes: Uint8Array; buffer: AudioBuffer }>();
  private master: GainNode | null = null;
  private lastBar: Bar | null = null;
  /** Live mute and solo: every note of a sound passes its gain, and a drum key's note its key gain too. */
  private soundGains: (GainNode | null)[] = new Array(16).fill(null);
  private keyGains: (GainNode | null)[][] = Array.from({ length: 8 }, () => new Array(16).fill(null));
  private appliedMix: string | null = null;

  constructor(host: PlayerHost) {
    this.host = host;
  }

  playing(): boolean {
    return this.timer !== null;
  }

  start(mode: PlaybackMode): void {
    this.stop();
    const current = this.host.project();
    if (!current) return;
    const context = audioContext();
    this.mode = mode;
    this.projectId = current.id;
    this.state = initialPlaybackState();
    this.chainIndex = 0;
    this.bars = [];
    this.lastBar = null;
    this.nextBarStart = context.currentTime + 0.05;
    this.tick();
    this.timer = setInterval(() => this.tick(), TICK_MS);
  }

  stop(): void {
    if (this.timer !== null) clearInterval(this.timer);
    this.timer = null;
    this.notes = [];
    for (const source of this.sources) {
      try {
        source.stop();
      } catch {
        // Already ended.
      }
    }
    this.sources.clear();
    this.bars = [];
  }

  position(): PlaybackPosition | null {
    if (this.timer === null) return null;
    const now = audioContext().currentTime;
    const bar = this.bars.find((b) => now >= b.start && now < b.start + b.length);
    if (!bar) return null;
    let step = 1;
    for (let i = 0; i < bar.offsets.length; i++) if (now - bar.start >= bar.offsets[i]) step = i + 1;
    return { mode: bar.mode, pattern: bar.pattern, step, entry: bar.entry };
  }

  /**
   * Change the mode while playing: the bar sounding finishes, and the switch happens at
   * its end. Steps already queued past it are cancelled and scheduled again in the new
   * mode; a switch to song mode starts the chain from its first entry.
   */
  setMode(mode: PlaybackMode): void {
    if (this.timer === null || mode === this.mode) {
      this.mode = mode;
      return;
    }
    const now = audioContext().currentTime;
    // Only steps of a bar that has not started are cancelled: the bar sounding plays out.
    const pending = this.bars.filter((b) => b.start > now).sort((a, b) => a.start - b.start);
    for (const bar of pending) this.cancelSteps(bar.steps);
    if (pending.length) {
      const first = pending[0];
      this.bars = this.bars.filter((b) => !pending.includes(b));
      if (first.steps.length) this.state = first.steps[0].stateBefore;
      this.chainIndex = first.chainIndexBefore;
      this.nextBarStart = first.start;
    }
    this.mode = mode;
    if (mode === 'song') this.chainIndex = 0;
    this.tick();
  }

  private cancelSteps(steps: Step[]): void {
    for (const step of steps) {
      for (const source of step.sources) {
        try {
          source.stop();
        } catch {
          // Never started.
        }
        this.releases.get(source)?.();
        this.sources.delete(source);
      }
      this.notes = this.notes.filter((n) => !step.notes.includes(n));
    }
  }

  /** The key each sound (1..16, by index) is sounding now, or null: the latest note of the sound that has started and not ended. */
  sounding(): (number | null)[] {
    const out: (number | null)[] = new Array(16).fill(null);
    if (this.timer === null) return out;
    const now = audioContext().currentTime;
    this.notes = this.notes.filter((n) => n.end > now - 0.5);
    const latest: (SoundingNote | null)[] = new Array(16).fill(null);
    for (const n of this.notes) {
      if (n.start > now || n.end <= now) continue;
      const held = latest[n.sound - 1];
      if (!held || n.start >= held.start) latest[n.sound - 1] = n;
    }
    return latest.map((n) => n?.key ?? null);
  }

  private tick(): void {
    const current = this.host.project();
    if (!current || current.id !== this.projectId) {
      this.stop();
      this.host.onStop();
      return;
    }
    const context = audioContext();
    // After a stall (a background tab throttles timers) the missed time is skipped, not piled onto now.
    if (this.nextBarStart < context.currentTime && !this.bars.some((b) => b.start + b.length > context.currentTime)) this.nextBarStart = context.currentTime + 0.02;
    const horizon = context.currentTime + LOOKAHEAD_SECONDS;
    for (;;) {
      let bar = this.bars.find((b) => b.steps.length < STEPS);
      if (!bar) {
        if (this.nextBarStart >= horizon) break;
        bar = this.openBar(current.project);
      }
      const next = bar.steps.length + 1;
      const time = bar.start + bar.offsets[next - 1];
      if (time >= horizon) break;
      if (time >= context.currentTime - 0.05) this.scheduleOneStep(bar, next, time, current.project, current.mix, context);
      else bar.steps.push({ step: next, time, stateBefore: this.state, sources: [], notes: [] });
    }
    this.applyMix(current.mix, context);
    const keep = context.currentTime - 2;
    this.bars = this.bars.filter((b) => b.start + b.length > keep);
    const sounding = this.bars.find((b) => context.currentTime >= b.start && context.currentTime < b.start + b.length) ?? null;
    if (sounding && sounding !== this.lastBar) {
      this.lastBar = sounding;
      this.host.onBar?.({ mode: sounding.mode, pattern: sounding.pattern, step: 1, entry: sounding.entry });
    }
  }

  /** The next bar: which pattern plays is decided as its first step comes into view. */
  private openBar(project: Project): Bar {
    const chainIndexBefore = this.chainIndex;
    let pattern: number;
    let entry: number | null = null;
    if (this.mode === 'song') {
      const chain = project.chain.length ? project.chain : [1];
      entry = this.chainIndex % chain.length;
      pattern = chain[entry];
      this.chainIndex++;
    } else pattern = this.host.selectedPattern();
    const bar: Bar = {
      start: this.nextBarStart,
      mode: this.mode,
      pattern,
      entry,
      offsets: stepOffsets(project.tempo, project.swing),
      length: barSeconds(project.tempo),
      chainIndexBefore,
      steps: [],
    };
    this.bars.push(bar);
    this.nextBarStart = bar.start + bar.length;
    return bar;
  }

  private scheduleOneStep(bar: Bar, step: number, time: number, project: Project, mix: Mix, context: AudioContext): void {
    const resolve = this.host.resolver();
    const codesOf = (id: string): Uint8Array => {
      try {
        return resolve(id);
      } catch {
        return new Uint8Array(0);
      }
    };
    const entry: Step = { step, time, stateBefore: this.state, sources: [], notes: [] };
    const { events, state } = scheduleStep(project, (id) => codesOf(id).length, bar.pattern - 1, step, time, this.state, mix);
    this.state = state;
    const master = this.masterNode(context);
    for (const event of events) {
      // Muted notes are scheduled too, through gains the mix sets live, so a mute or solo acts at once.
      const codes = codesOf(event.clip.sampleId);
      if (!codes.length) continue;
      const source = context.createBufferSource();
      source.buffer = this.bufferFor(context, event.clip.sampleId, codes);
      if (event.glideFromRate !== null) {
        source.playbackRate.setValueAtTime(event.glideFromRate, event.time);
        source.playbackRate.exponentialRampToValueAtTime(event.rate, event.time + GLIDE_SECONDS);
      } else source.playbackRate.setValueAtTime(event.rate, event.time);
      const gain = context.createGain();
      gain.gain.value = 10 ** (event.gainDb / 20);
      let head: AudioNode = source;
      if (event.filter) {
        const filter = context.createBiquadFilter();
        filter.type = event.filter.type;
        filter.frequency.value = event.filter.hz;
        filter.Q.value = event.filter.peakDb;
        head.connect(filter);
        head = filter;
      }
      head.connect(gain);
      gain.connect(this.gainFor(context, event.sound, event.key, master));
      // Everything the note built goes when it ends, or when its bar is cancelled before it starts (no ended event then).
      const release = () => {
        this.sources.delete(source);
        this.releases.delete(source);
        head.disconnect();
        gain.disconnect();
      };
      source.onended = release;
      this.releases.set(source, release);
      source.start(event.time, event.clip.start / SAMPLE_RATE, (event.clip.end - event.clip.start) / SAMPLE_RATE);
      // A note shorter than its clip (its length, or the next repeat restarting it) stops at its
      // duration, with a few milliseconds' fade so the cut does not click.
      const whole = (event.clip.end - event.clip.start) / SAMPLE_RATE / event.rate;
      if (event.duration < whole - 0.001) {
        const stop = event.time + Math.max(0, event.duration);
        const fade = Math.min(CUT_FADE_SECONDS, Math.max(0, event.duration) / 2);
        gain.gain.setValueAtTime(10 ** (event.gainDb / 20), stop - fade);
        gain.gain.linearRampToValueAtTime(0, stop);
        source.stop(stop);
      }
      this.sources.add(source);
      entry.sources.push(source);
      const note = { sound: event.sound, key: event.key, start: event.time, end: event.time + event.duration };
      entry.notes.push(note);
      this.notes.push(note);
    }
    bar.steps.push(entry);
  }

  /** The gain a note of this sound (and key, for a drum) plays through; created on first use. */
  private gainFor(context: AudioContext, sound: number, key: number, master: GainNode): GainNode {
    let soundGain = this.soundGains[sound - 1];
    if (!soundGain) {
      soundGain = context.createGain();
      soundGain.connect(master);
      this.soundGains[sound - 1] = soundGain;
      this.appliedMix = null;
    }
    if (sound <= 8) return soundGain;
    let keyGain = this.keyGains[sound - 9][key - 1];
    if (!keyGain) {
      keyGain = context.createGain();
      keyGain.connect(soundGain);
      this.keyGains[sound - 9][key - 1] = keyGain;
      this.appliedMix = null;
    }
    return keyGain;
  }

  /** Set every sound and key gain from the mix, when it has changed, with a short ramp against clicks. */
  private applyMix(mix: Mix, context: AudioContext): void {
    const signature = JSON.stringify(mix);
    if (signature === this.appliedMix) return;
    this.appliedMix = signature;
    const set = (gain: GainNode, on: boolean) => {
      gain.gain.cancelScheduledValues(context.currentTime);
      gain.gain.setTargetAtTime(on ? 1 : 0, context.currentTime, 0.005);
    };
    this.soundGains.forEach((gain, i) => gain && set(gain, !soundSilent(mix, i + 1)));
    this.keyGains.forEach((keys, kit) =>
      keys.forEach((gain, k) => {
        if (!gain) return;
        const mutes = mix.sliceMutes[kit] ?? [];
        const solos = mix.sliceSolos[kit] ?? [];
        set(gain, !(mutes[k] || (solos.some(Boolean) && !solos[k])));
      }),
    );
  }

  private masterNode(context: AudioContext): GainNode {
    if (this.master) return this.master;
    const master = context.createGain();
    // One voice at the loudest volume code reaches full scale; the limiter catches the sum of four.
    master.gain.value = 10 ** (-volumeDb(63) / 20);
    const limiter = context.createDynamicsCompressor();
    limiter.threshold.value = -6;
    limiter.knee.value = 0;
    limiter.ratio.value = 20;
    limiter.attack.value = 0.002;
    limiter.release.value = 0.1;
    master.connect(limiter);
    limiter.connect(context.destination);
    this.master = master;
    return master;
  }

  /** The sample's buffer at the device rate, rebuilt when its codes change. */
  private bufferFor(context: AudioContext, id: string, codes: Uint8Array): AudioBuffer {
    const cached = this.buffers.get(id);
    if (cached && cached.codes === codes) return cached.buffer;
    const buffer = context.createBuffer(1, codes.length, SAMPLE_RATE);
    buffer.getChannelData(0).set(Float32Array.from(decodeMulawCodes(codes)));
    this.buffers.set(id, { codes, buffer });
    return buffer;
  }
}
