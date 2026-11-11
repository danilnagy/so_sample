/**
 * Application state and actions. A small external store read with useSyncExternalStore;
 * every project change is written to IndexedDB shortly after.
 */

import { useRef, useSyncExternalStore } from 'react';

import { type UnpackedSample, packKit, packProject, sha256Hex, unpackKit, unpackProject } from '../core/archive';
import { type Modifications, applyModifications, isUnmodified, modifiedLength } from '../core/edits';
import { type LabelStreams, labelsForBody } from '../core/labels';
import { recoverFrame } from '../core/modem/decode';
import { transferSeconds } from '../core/modem/encode';
import { encodeRestoreWav } from '../core/modem/encode';
import { encodePackets } from '../core/packets';
import { type Cell, type ParameterName, PARAMETER_NAMES, emptyPattern, readCell, writeCell, writeEffects, readEffects, DEFAULT_PARAMETERS } from '../core/pattern';
import { type Clip, type MemoryRow, type Project, compileProject, emptyProject, importProject, memorySummary, projectPages } from '../core/project';
import { parseFrame, serializeState } from '../core/state';
import { emptyTemplateState } from '../core/template';
import type { WavData } from '../core/wav';
import { type KitRecord, type ProjectRecord, type SampleRecord, db, newId } from './db';
import { bytesOf, unzipFiles, zipFiles } from './archive';
import { BASE_KEY, VOICE_RANK } from './laws';
import { type PlaybackMode, type PlaybackPosition, Player } from './player';
import type { Mix } from './playback';
import { PRESETS, PRESET_KITS, fetchPreset, presetsDisabled } from './presets';
import { GUIDE_URL, isGuidePath } from '../guide/urls';
import { type Playback, importAudioFile } from './samples';

export type Theme = 'system' | 'light' | 'dark';

export type LibraryTarget = { kind: 'melodic'; slot: number } | { kind: 'drum'; slot: number; key: number };

/** The modal editors. They stack: an editor opened from another returns to it on close. */
export type Editor = { kind: 'clip'; target: LibraryTarget } | { kind: 'kit'; slot: number } | { kind: 'memory' };

/** The pad layout's views, for narrow screens. */
export type MobileView = 'fx' | 'sound' | 'pattern' | 'song';

export type DeviceMode = 'send' | 'import' | null;

export interface ProjectSummary {
  id: string;
  name: string;
  updatedAt: number;
}

export interface AppState {
  ready: boolean;
  projects: ProjectSummary[];
  project: ProjectRecord | null;
  samples: SampleRecord[];
  pattern: number;
  /** The Library: whether it is open, the slot it is choosing a sample for, and the sample expanded for editing in it. */
  library: { open: boolean; target: LibraryTarget | null; editing: string | null };
  /** Open editors, the last one on top; the Library opens above them all. */
  editors: Editor[];
  /** Sounds whose roll is unrolled below their row in the pattern grid. */
  unrolled: number[];
  /** The parameter each sound's lane shows, by sound; volume unless chosen. */
  laneParameter: Record<number, ParameterName>;
  /** Kits saved in the app, by name. */
  kits: KitRecord[];
  device: DeviceMode;
  theme: Theme;
  /** Browser device id of the audio input used to record backups; '' is the default input. */
  inputDevice: string;
  notice: string | null;
  saving: boolean;
  /** A pattern copy in progress: what is being copied and from which pattern; the pattern bar picks the target. */
  copying: { kind: 'pattern' | 'fx'; from: number } | null;
  /** The preview's mode while it plays, else null. */
  playing: PlaybackMode | null;
  /** The mode the transport starts in. */
  playbackMode: PlaybackMode;
  /** In song mode, the pattern on screen follows the one sounding. */
  followPlayhead: boolean;
  /** The pad layout: which view the pads show, the sound whose steps they show, and the key new notes take (null: like the nearest note). */
  mobile: { view: MobileView; sound: number; step: number | null };
  /** The song entry selected in the song strip or the Song pads, for the move and remove buttons; null when none. */
  songEntry: number | null;
  /** What the app is doing before it is ready, for the loading screen. */
  loading: string;
  /** Bumped when an audition starts, so the monitors wake while the preview is stopped. */
  auditionTick: number;
  /** The first-visit welcome is showing. */
  welcome: boolean;
  /** The guide layout: every view and dialog on one page with its explanation, at /guide. */
  guide: boolean;
}

type Listener = () => void;

class Store {
  state: AppState = {
    ready: false,
    projects: [],
    project: null,
    samples: [],
    pattern: 1,
    library: { open: false, target: null, editing: null },
    editors: [],
    unrolled: [],
    laneParameter: {},
    kits: [],
    device: null,
    theme: 'system',
    inputDevice: '',
    notice: null,
    saving: false,
    copying: null,
    playing: null,
    // Song mode is the default: the preview plays the chain, as the device does.
    playbackMode: 'song',
    followPlayhead: true,
    mobile: { view: 'sound', sound: 1, step: null },
    songEntry: null,
    loading: 'Loading…',
    auditionTick: 0,
    welcome: false,
    guide: isGuidePath(),
  };

  private listeners = new Set<Listener>();
  private rendered = new Map<string, { key: string; codes: Uint8Array }>();
  private saveTimer: ReturnType<typeof setTimeout> | null = null;
  /** Sample records waiting to be written after an edit, by id; the write takes the latest state. */
  private sampleWrites = new Map<string, ReturnType<typeof setTimeout>>();
  /** The project state waiting for the save timer, so a switch can write it first. */
  private pending: ProjectRecord | null = null;

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  getState = (): AppState => this.state;

  private set(partial: Partial<AppState>): void {
    this.state = { ...this.state, ...partial };
    for (const listener of this.listeners) listener();
  }

  /** Change state without notifying, for a change that a following `set` or `update` reports together with its own. */
  private patch(partial: Partial<AppState>): void {
    this.state = { ...this.state, ...partial };
  }

  // Lifecycle

  private initialising: Promise<void> | null = null;

  /** Load the library and the open project; called once, and a second call (React's strict mode mounts twice) joins the first. */
  init(): Promise<void> {
    this.initialising ??= this.load().finally(() => {
      this.initialising = null;
    });
    return this.initialising;
  }

  private async load(): Promise<void> {
    const theme = ((await db.settings.get('theme'))?.value as Theme | undefined) ?? 'system';
    const followPlayhead = ((await db.settings.get('followPlayhead'))?.value as boolean | undefined) ?? true;
    applyTheme(theme);
    const inputDevice = ((await db.settings.get('inputDevice'))?.value as string | undefined) ?? '';
    // The library in memory first: adding the bundled kits and projects below matches their samples against it.
    this.patch({ samples: await db.samples.orderBy('name').toArray(), kits: await db.kits.orderBy('name').toArray() });
    let projects = await this.summaries();
    // The kits and projects the app comes with: any the library lacks is added now, so every
    // user has all of them, and a deleted one is back on the next load. Opening with ?nopresets skips this.
    let notice: string | null = null;
    let failed = false;
    const firstLaunch = projects.length === 0;
    if (!presetsDisabled()) {
      try {
        const added = await this.addMissingPresets();
        if (added.projects || added.kits) {
          projects = await this.summaries();
          const what = [added.kits ? plural(added.kits, 'kit') : '', added.projects ? plural(added.projects, 'project') : ''].filter(Boolean).join(' and ');
          notice = firstLaunch ? `Added the ${what} the app comes with. Everything you make stays on this device.` : `Added ${what} the app comes with.`;
        }
      } catch (error) {
        notice = `The kits and projects the app comes with could not be loaded: ${(error as Error).message}`;
        failed = true;
      }
    }
    const samples = this.state.samples;
    const kits = this.state.kits;
    const lastId = (await db.settings.get('lastProject'))?.value as string | undefined;
    let project = lastId ? await db.projects.get(lastId) : undefined;
    // Nothing chosen yet: the first bundled project, else whatever is there, else a new one.
    if (!project && projects.length) {
      const first = PRESETS.length ? await db.projects.where('id').anyOf(projects.map((p) => p.id)).filter((p) => p.preset === PRESETS[0].slug).first() : undefined;
      project = first ?? (await db.projects.get(projects[0].id));
    }
    if (!project) project = await this.create('Untitled');
    // A first visit gets a short welcome with a link to the guide; ?nowelcome skips it, for tests.
    const welcomed = (await db.settings.get('welcomed'))?.value === true;
    const welcome = !welcomed && !this.state.guide && !(typeof location !== 'undefined' && new URLSearchParams(location.search).has('nowelcome'));
    this.set({ theme, followPlayhead, inputDevice, samples, kits, projects: await this.summaries(), welcome });
    await this.activate(project, { ready: true });
    // The welcome says the same thing on a first visit, so the notice gives way to it; a failure is said regardless.
    if (notice && (!welcome || failed)) this.notify(notice);
    // A word with the browser about keeping the data; best effort.
    void navigator.storage?.persist?.().catch(() => {});
  }

  /**
   * Import every bundled kit and project whose slug no record carries, kits first so the
   * projects' drums reuse their samples. Two tabs opened at once on a first launch would both
   * find everything missing, so the work holds a lock shared by the site's tabs, and the
   * library is read again inside it: the second tab finds what the first added.
   */
  private async addMissingPresets(): Promise<{ kits: number; projects: number }> {
    const locks = typeof navigator !== 'undefined' ? navigator.locks : undefined;
    if (!locks) return this.addMissingPresetsNow();
    return locks.request('sosample-presets', () => this.addMissingPresetsNow());
  }

  private async addMissingPresetsNow(): Promise<{ kits: number; projects: number }> {
    this.patch({ samples: await db.samples.orderBy('name').toArray(), kits: await db.kits.orderBy('name').toArray() });
    const haveKits = new Set(this.state.kits.map((k) => k.preset).filter((slug): slug is string => !!slug));
    const missingKits = PRESET_KITS.filter((k) => !haveKits.has(k.slug));
    let kits = 0;
    for (const kit of missingKits) {
      this.set({ loading: `Adding the ${kit.name} kit (${kits + 1} of ${missingKits.length})…` });
      await this.importKitArchive(await fetchPreset(kit), undefined, { preset: kit.slug });
      kits++;
    }
    const present = new Set((await db.projects.toArray()).map((p) => p.preset).filter((slug): slug is string => !!slug));
    const missing = PRESETS.filter((p) => !present.has(p.slug));
    let projects = 0;
    for (const preset of missing) {
      this.set({ loading: `Adding ${preset.name} (${projects + 1} of ${missing.length})…` });
      await this.importProjectArchive(await fetchPreset(preset), { activate: false, preset: preset.slug });
      projects++;
    }
    return { kits, projects };
  }


  private async summaries(): Promise<ProjectSummary[]> {
    const records = await db.projects.orderBy('updatedAt').reverse().toArray();
    return records.map((p) => ({ id: p.id, name: p.name, updatedAt: p.updatedAt }));
  }

  private async create(name: string): Promise<ProjectRecord> {
    const base = emptyProject(120);
    const now = Date.now();
    const record: ProjectRecord = {
      id: newId(),
      name,
      ...base,
      mutes: new Array(16).fill(false),
      solos: new Array(16).fill(false),
      createdAt: now,
      updatedAt: now,
    };
    await db.projects.put(record);
    return record;
  }

  // Playback

  private player: Player | null = null;

  /** The player's view of the project, rebuilt only when the record changes: the player asks forty times a second. */
  private playerView: { record: ProjectRecord; samples: SampleRecord[]; view: { id: string; project: Project; mix: Mix } } | null = null;
  private playerResolver: { samples: SampleRecord[]; resolve: (id: string) => Uint8Array } | null = null;

  private playerInstance(): Player {
    this.player ??= new Player({
      project: () => {
        const record = this.state.project;
        if (!record) return null;
        const samples = this.state.samples;
        if (this.playerView?.record !== record || this.playerView.samples !== samples) this.playerView = { record, samples, view: { id: record.id, project: this.fitted(record, samples), mix: mixOf(record) } };
        return this.playerView.view;
      },
      resolver: () => {
        if (this.playerResolver?.samples !== this.state.samples) this.playerResolver = { samples: this.state.samples, resolve: this.resolver() };
        return this.playerResolver.resolve;
      },
      selectedPattern: () => this.state.pattern,
      onStop: () => this.set({ playing: null }),
      // Following: in song mode the pattern on screen changes with the song, bar by bar.
      onBar: (position) => {
        if (this.state.followPlayhead && position.mode === 'song' && position.pattern !== this.state.pattern) this.selectPattern(position.pattern);
      },
    });
    return this.player;
  }

  // The pad layout

  setMobileView(view: MobileView): void {
    this.set({ mobile: { ...this.state.mobile, view, step: null } });
  }

  /** Choose the sound the pads sequence; no step of it is selected yet. */
  setMobileSound(sound: number): void {
    this.set({ mobile: { ...this.state.mobile, sound, step: null } });
  }

  // The current key: per sound, the key a new note takes and an audition plays. It starts at
  // key 5 (melodic) or 1 (drum), follows the key strip on a phone and the last key programmed
  // in a roll, and is saved with the project.

  currentKey(sound: number): number {
    return this.state.project?.keys?.[sound - 1] ?? defaultKey(sound);
  }

  setCurrentKey(sound: number, key: number): void {
    if (this.currentKey(sound) === key) return;
    // A choice, like a selection: saved with the project, but no undo step of its own, and an undo leaves it as it is.
    this.update(
      (p) => {
        const keys = p.keys ? [...p.keys] : Array.from({ length: 16 }, (_, i) => defaultKey(i + 1));
        keys[sound - 1] = key;
        return { ...p, keys };
      },
      { undoable: false },
    );
  }

  /** The step whose parameters the pad layout's parameter row edits; null when none is selected. */
  setMobileStep(step: number | null): void {
    this.set({ mobile: { ...this.state.mobile, step } });
  }

  /**
   * A pad tap in the Pattern view. A blank step takes a note on the current key and becomes
   * the selected step; a note elsewhere is selected first, so its parameters can be edited;
   * the selected note goes.
   */
  tapStep(step: number, sound: number): void {
    const data = this.state.project?.patterns[this.state.pattern - 1];
    if (!data) return;
    const cell = readCell(data, step, sound);
    if (cell?.key && this.state.mobile.step === step) this.setCell(step, sound, null);
    else if (!cell?.key) this.setCell(step, sound, newNote(data, step, sound, this.currentKey(sound)));
    this.setMobileStep(step);
  }

  // Mute and solo: preview only, saved with the project, never sent to the device.

  /** Mutes and solos exclude each other: a mute pressed while sounds are soloed drops the solos first, and the reverse. */
  toggleMute(sound: number): void {
    this.update((p) => ({ ...p, mutes: flipped(p.mutes, sound - 1, 16), solos: new Array(16).fill(false) }), { undoable: false });
  }

  toggleSolo(sound: number): void {
    this.update((p) => ({ ...p, solos: flipped(p.solos, sound - 1, 16), mutes: new Array(16).fill(false) }), { undoable: false });
  }

  /** Within a kit the same rule holds between its key mutes and key solos. */
  toggleSliceMute(slot: number, key: number): void {
    this.update((p) => ({ ...p, sliceMutes: flippedKit(p.sliceMutes, slot - 9, key - 1), sliceSolos: clearedKit(p.sliceSolos, slot - 9) }), { undoable: false });
  }

  toggleSliceSolo(slot: number, key: number): void {
    this.update((p) => ({ ...p, sliceSolos: flippedKit(p.sliceSolos, slot - 9, key - 1), sliceMutes: clearedKit(p.sliceMutes, slot - 9) }), { undoable: false });
  }

  /** Every mute and solo off, at both levels. */
  clearMix(): void {
    this.update((p) => ({ ...p, mutes: new Array(16).fill(false), solos: new Array(16).fill(false), sliceMutes: undefined, sliceSolos: undefined }), { undoable: false });
  }

  /** Start the preview in a mode (the chosen one by default). */
  play(mode = this.state.playbackMode): void {
    if (!this.state.project) return;
    if (typeof AudioContext === 'undefined') {
      this.notify('This browser cannot play audio');
      return;
    }
    this.playerInstance().start(mode);
    this.set({ playing: mode, playbackMode: mode });
  }

  stopPlayback(): void {
    this.player?.stop();
    if (this.state.playing) this.set({ playing: null });
  }

  togglePlayback(): void {
    if (this.state.playing) this.stopPlayback();
    else this.play();
  }

  /** Choose the transport's mode; a running preview switches when the bar sounding ends. */
  setPlaybackMode(mode: PlaybackMode): void {
    if (this.state.playing) this.player?.setMode(mode);
    this.set({ playbackMode: mode, playing: this.state.playing ? mode : null });
  }

  async setFollowPlayhead(follow: boolean): Promise<void> {
    this.set({ followPlayhead: follow });
    const now = this.playbackPosition();
    if (follow && now?.mode === 'song' && now.pattern !== this.state.pattern) this.selectPattern(now.pattern);
    await db.settings.put({ key: 'followPlayhead', value: follow });
  }

  playbackPosition(): PlaybackPosition | null {
    return this.player?.position() ?? null;
  }

  /** The last audition of each sound: which key, and the playback to ask whether it still sounds. */
  private readonly auditions = new Map<number, { key: number; playback: Playback }>();

  /** Play a sound's key by hand (a play button, the key strip, a roll lane) and count it as sounding while it plays. */
  audition(sound: number, key: number, start: () => Playback): void {
    try {
      this.auditions.set(sound, { key, playback: start() });
      this.set({ auditionTick: this.state.auditionTick + 1 });
    } catch (error) {
      this.notify((error as Error).message);
    }
  }

  /** The key each sound is sounding, by sound index, or null: the preview's notes and the auditions still playing. */
  soundingKeys(): (number | null)[] {
    const keys = this.player?.sounding() ?? new Array<number | null>(16).fill(null);
    for (const [sound, audition] of this.auditions) {
      if (audition.playback.position() !== null) keys[sound - 1] = audition.key;
      else this.auditions.delete(sound);
    }
    return keys;
  }

  /** Whether any audition is still playing. */
  auditioning(): boolean {
    for (const audition of this.auditions.values()) if (audition.playback.position() !== null) return true;
    return false;
  }

  private noticeTimer: ReturnType<typeof setTimeout> | null = null;

  /** Show a message in the status slot for a few seconds, or clear it. */
  notify(notice: string | null): void {
    if (this.noticeTimer) clearTimeout(this.noticeTimer);
    this.noticeTimer = notice ? setTimeout(() => this.set({ notice: null }), NOTICE_SECONDS * 1000) : null;
    this.set({ notice });
  }

  // Projects

  async newProject(): Promise<void> {
    await this.flush();
    const project = await this.create(`Project ${this.state.projects.length + 1}`);
    await db.settings.put({ key: 'lastProject', value: project.id });
    this.set({ project, projects: await this.summaries(), pattern: 1 });
  }

  /** A copy of a project (the current one unless an id is given), with its own id and a distinct name, opened as the current one. */
  async duplicateProject(id?: string): Promise<void> {
    await this.flush();
    const current = id && id !== this.state.project?.id ? await db.projects.get(id) : this.state.project;
    if (!current) return;
    const now = Date.now();
    const copy: ProjectRecord = {
      ...current,
      id: newId(),
      name: copyName(current.name, this.state.projects.map((p) => p.name)),
      chain: [...current.chain],
      melodic: current.melodic.map((c) => (c ? { ...c } : null)),
      drums: current.drums.map((d) => (d ? { slices: d.slices.map((c) => (c ? { ...c } : null)) } : null)),
      patterns: current.patterns.map((p) => p.slice()),
      mutes: [...current.mutes],
      solos: [...current.solos],
      kitNames: current.kitNames ? [...current.kitNames] : undefined,
      keys: current.keys ? [...current.keys] : undefined,
      preset: undefined,
      createdAt: now,
      updatedAt: now,
    };
    await db.projects.put(copy);
    await this.activate(copy, { projects: await this.summaries() });
  }

  async openProject(id: string): Promise<void> {
    await this.flush();
    const project = await db.projects.get(id);
    if (!project) return;
    await this.activate(project);
  }

  /**
   * Make a project the current one: its clips of samples deleted while it was closed are
   * dropped (a sample is deleted from the library, not from each project), and it is
   * remembered as the one to open next time.
   */
  private async activate(project: ProjectRecord, extra: Partial<AppState> = {}): Promise<void> {
    this.history = { id: project.id, past: [], future: [], gesture: null };
    await db.settings.put({ key: 'lastProject', value: project.id });
    this.set({ project: this.clampClips(project, { windows: false }), pattern: 1, ...extra });
  }

  async deleteProject(id: string): Promise<void> {
    if (this.pending?.id === id) {
      if (this.saveTimer) clearTimeout(this.saveTimer);
      this.saveTimer = null;
      this.pending = null;
      this.set({ saving: false });
    } else {
      await this.flush();
    }
    await db.projects.delete(id);
    const projects = await this.summaries();
    if (this.state.project?.id === id) {
      const next = projects.length ? await db.projects.get(projects[0].id) : await this.create('Untitled');
      if (next) await this.activate(next);
    }
    this.set({ projects: await this.summaries() });
  }

  renameProject(name: string): void {
    this.update((p) => ({ ...p, name }));
  }

  private update(change: (project: ProjectRecord) => ProjectRecord, { undoable = true }: { undoable?: boolean } = {}): void {
    const current = this.state.project;
    if (!current) return;
    const changed = change(current);
    // A change that returns the record itself (a clamp that found nothing to clamp) is no edit: nothing to save.
    if (changed === current) return;
    if (undoable) this.record(current);
    this.commit({ ...changed, updatedAt: Date.now() });
  }

  // Undo and redo: the open project's earlier versions, in memory. An edit replaces the
  // record and copies only what it changes, so a version costs little more than the
  // pattern it touched. Mute and solo are not edits here (they only shape the preview), and
  // an undo leaves them as they are. Switching project starts a new history.

  private history: { id: string | null; past: ProjectRecord[]; future: ProjectRecord[]; gesture: unknown } = { id: null, past: [], future: [], gesture: null };
  private pointerHeld = 0;
  /** Set while one action is running: every update it makes (a roll click writes the note and the key) is one step. */
  private action: object | null = null;

  /**
   * One gesture is one step: the edits made while a pointer is held (a drag across steps, a
   * slider), while one field has the keyboard (typing a tempo), or by one action (a roll
   * click writes the note and the sound's key) join the step they started.
   */
  private gesture(): unknown {
    if (this.pointerHeld) return this.pointerHeld;
    const active = typeof document !== 'undefined' ? document.activeElement : null;
    if (active && /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName)) return active;
    // An action's updates run in one task: the first opens a token, cleared when the task is done.
    if (!this.action) {
      const token = {};
      this.action = token;
      queueMicrotask(() => {
        if (this.action === token) this.action = null;
      });
    }
    return this.action;
  }

  /** Follow the pointer for gestures; called once at start-up. */
  trackGestures(): () => void {
    let presses = 0;
    const down = () => (this.pointerHeld = ++presses);
    const up = () => (this.pointerHeld = 0);
    window.addEventListener('pointerdown', down, true);
    window.addEventListener('pointerup', up, true);
    window.addEventListener('pointercancel', up, true);
    return () => {
      window.removeEventListener('pointerdown', down, true);
      window.removeEventListener('pointerup', up, true);
      window.removeEventListener('pointercancel', up, true);
    };
  }

  /** Keep the version an edit is about to replace, unless the edit continues the gesture that made the last step. */
  private record(before: ProjectRecord): void {
    const h = this.history;
    if (h.id !== before.id) this.history = { id: before.id, past: [], future: [], gesture: null };
    const gesture = this.gesture();
    const continues = gesture !== null && gesture === this.history.gesture && this.history.past.length > 0;
    this.history.gesture = gesture;
    this.history.future = [];
    if (continues) return;
    this.history.past.push(before);
    if (this.history.past.length > UNDO_STEPS) this.history.past.shift();
  }

  canUndo(): boolean {
    return this.history.id === this.state.project?.id && this.history.past.length > 0;
  }

  canRedo(): boolean {
    return this.history.id === this.state.project?.id && this.history.future.length > 0;
  }

  undo(): void {
    this.travel('past', 'future');
  }

  redo(): void {
    this.travel('future', 'past');
  }

  private travel(from: 'past' | 'future', to: 'past' | 'future'): void {
    const current = this.state.project;
    if (!current || this.history.id !== current.id) return;
    const target = this.history[from].pop();
    if (!target) return;
    this.history[to].push(current);
    this.history.gesture = null;
    // The mix and the current keys stay as they are; clips of a sample deleted since are dropped, as on opening.
    const project = this.clampClips({ ...target, mutes: current.mutes, solos: current.solos, sliceMutes: current.sliceMutes, sliceSolos: current.sliceSolos, keys: current.keys, updatedAt: Date.now() }, { windows: false });
    // Show what changed: the first pattern that differs (an edit copies only the pattern it touches).
    const changed = current.patterns.findIndex((data, i) => data !== target.patterns[i]);
    this.commit(project, changed >= 0 ? { pattern: changed + 1 } : {});
  }

  /** Make a record the current project and save it after a pause. */
  private commit(project: ProjectRecord, extra: Partial<AppState> = {}): void {
    this.set({ project, saving: true, ...extra });
    if (this.saveTimer) clearTimeout(this.saveTimer);
    this.pending = project;
    this.saveTimer = setTimeout(() => void this.flush(), 300);
  }

  /**
   * Switch between the app's layouts: the usual one, and the guide at /guide, which shows
   * every view and dialog at once, explained. Same data, same components; the address
   * follows, so the browser's back button switches back.
   */
  setGuide(on: boolean, fromHistory = false): void {
    if (on === this.state.guide) return;
    if (!fromHistory && typeof history !== 'undefined') {
      const url = on ? GUIDE_URL : import.meta.env.BASE_URL;
      history.pushState(null, '', url + location.search);
    }
    // Open editors, the library and the device dialogs are shown in place in the guide; leaving it closes them.
    this.set({ guide: on, ...(on ? {} : { editors: [], device: null, library: { ...this.state.library, open: false, target: null, editing: null } }) });
    if (typeof window !== 'undefined') window.scrollTo(0, 0);
  }

  /** Close the welcome for good. */
  dismissWelcome(): void {
    this.set({ welcome: false });
    void db.settings.put({ key: 'welcomed', value: true });
  }

  /** Write any edit still waiting for its save timer: before leaving the page. */
  saveNow(): Promise<void> {
    return this.flush();
  }

  /** Write the edit still waiting for its save timer, if any. */
  private async flush(): Promise<void> {
    if (this.saveTimer) clearTimeout(this.saveTimer);
    this.saveTimer = null;
    const project = this.pending;
    this.pending = null;
    if (!project) return;
    await db.projects.put(project);
    this.set({ saving: false, projects: await this.summaries() });
  }

  // Globals and chain

  setTempo(tempo: number): void {
    if (tempo >= 60 && tempo <= 240) this.update((p) => ({ ...p, tempo }));
  }

  setSwing(swing: number): void {
    if (swing >= 0 && swing <= 18) this.update((p) => ({ ...p, swing }));
  }

  setChain(chain: number[]): void {
    if (chain.length > 128) return;
    this.update((p) => ({ ...p, chain }));
    // A selection past the new end is gone.
    if (this.state.songEntry !== null && this.state.songEntry >= chain.length) this.set({ songEntry: null });
  }

  // The selected song entry: a click on a chip or pad selects it (again deselects); the move
  // and remove buttons act on it. Shared by the desktop strip and the phone's Song pads.

  selectSongEntry(index: number | null): void {
    this.set({ songEntry: this.state.songEntry === index ? null : index });
  }

  /** Set the selection outright, as a drag or a move that carries the selected entry does. */
  setSongEntry(index: number | null): void {
    this.set({ songEntry: index });
  }

  /** Swap the selected entry with its neighbour, left (-1) or right (+1); the selection follows it. */
  moveSongEntry(delta: -1 | 1): void {
    const chain = this.state.project?.chain;
    const from = this.state.songEntry;
    if (!chain || from === null) return;
    const to = from + delta;
    if (to < 0 || to >= chain.length) return;
    const next = chain.slice();
    [next[from], next[to]] = [next[to], next[from]];
    this.setChain(next);
    this.set({ songEntry: to });
  }

  /** Remove the selected entry; the song keeps at least one pattern. */
  removeSongEntry(): void {
    const chain = this.state.project?.chain;
    const index = this.state.songEntry;
    if (!chain || index === null || chain.length <= 1) return;
    this.setChain(chain.filter((_, i) => i !== index));
    this.set({ songEntry: null });
  }

  /** The song back to its start: pattern 1 alone, as a new project has it. */
  clearChain(): void {
    this.setChain([1]);
  }

  appendToChain(pattern: number): void {
    const chain = this.state.project?.chain ?? [];
    if (chain.length < 128) this.setChain([...chain, pattern]);
  }

  // Patterns

  selectPattern(pattern: number): void {
    this.set({ pattern });
  }

  copyPattern(from: number, to: number): void {
    if (from === to) return;
    this.update((p) => {
      const patterns = p.patterns.slice();
      patterns[to - 1] = p.patterns[from - 1].slice();
      return { ...p, patterns };
    });
  }

  clearPattern(pattern: number): void {
    this.update((p) => {
      const patterns = p.patterns.slice();
      patterns[pattern - 1] = emptyPattern();
      return { ...p, patterns };
    });
  }

  /** Begin a copy of the current pattern, or of its FX row; the next pattern clicked is the target. */
  startCopy(kind: 'pattern' | 'fx'): void {
    this.set({ copying: { kind, from: this.state.pattern } });
  }

  cancelCopy(): void {
    if (this.state.copying) this.set({ copying: null });
  }

  /** Finish a copy onto a pattern and select it. */
  copyTo(to: number): void {
    const copying = this.state.copying;
    if (!copying) return;
    if (copying.kind === 'pattern') this.copyPattern(copying.from, to);
    else this.copyEffects(copying.from, to);
    this.set({ copying: null });
    this.selectPattern(to);
  }

  /** The sixteen step effects of one pattern onto another; the notes stay. */
  copyEffects(from: number, to: number): void {
    if (from === to) return;
    this.update((p) => {
      const patterns = p.patterns.slice();
      const data = p.patterns[to - 1].slice();
      writeEffects(data, readEffects(p.patterns[from - 1]));
      patterns[to - 1] = data;
      return { ...p, patterns };
    });
  }

  clearEffects(pattern: number): void {
    this.update((p) => {
      const patterns = p.patterns.slice();
      const data = p.patterns[pattern - 1].slice();
      writeEffects(data, new Array(16).fill(null));
      patterns[pattern - 1] = data;
      return { ...p, patterns };
    });
  }

  setCell(step: number, sound: number, cell: Cell | null): void {
    const pattern = this.state.pattern;
    this.update((p) => {
      const patterns = p.patterns.slice();
      const data = p.patterns[pattern - 1].slice();
      writeCell(data, step, sound, cell);
      patterns[pattern - 1] = data;
      return { ...p, patterns };
    });
  }

  /** Toggle a note; a new note takes the sound's current key and the parameters of its nearest note. */
  toggleNote(step: number, sound: number): void {
    const data = this.state.project?.patterns[this.state.pattern - 1];
    if (!data) return;
    const cell = readCell(data, step, sound);
    if (cell?.key !== null && cell?.key !== undefined) {
      this.setCell(step, sound, null);
      return;
    }
    this.setCell(step, sound, newNote(data, step, sound, this.currentKey(sound)));
  }

  /**
   * A roll click: give the step this key, which becomes the sound's current key. The PO-33
   * holds one note per sound and step, so an existing note moves to the key and keeps its
   * parameters, and clicking the key it already has removes it. A lock without a note
   * becomes a note, its unlocked parameters taken from the sound's nearest note.
   */
  setRollNote(step: number, sound: number, key: number): void {
    const data = this.state.project?.patterns[this.state.pattern - 1];
    if (!data) return;
    const cell = readCell(data, step, sound);
    if (cell?.key === key) {
      this.setCell(step, sound, null);
      return;
    }
    this.setCell(step, sound, cell?.key ? { ...cell, key } : newNote(data, step, sound, key));
    this.setCurrentKey(sound, key);
  }

  setLaneParameter(sound: number, parameter: ParameterName): void {
    this.set({ laneParameter: { ...this.state.laneParameter, [sound]: parameter } });
  }

  /**
   * Set one parameter of a step from the lane. A step without a cell becomes a lock without
   * a note; code 0 clears the lock, and a lock-only cell with nothing left is removed.
   */
  setStepParameter(step: number, sound: number, parameter: ParameterName, code: number): void {
    const data = this.state.project?.patterns[this.state.pattern - 1];
    if (!data) return;
    const cell = readCell(data, step, sound) ?? { key: null, pitch: 0, volume: 0, filter: 0, resonance: 0 };
    const next: Cell = { ...cell, [parameter]: code };
    const empty = next.key === null && !next.pitch && !next.volume && !next.filter && !next.resonance;
    this.setCell(step, sound, empty ? null : next);
  }

  /**
   * Remove a step's locks, the given parameters or all four, as a double-click on a lane
   * handle does: the code becomes 0, so the step holds the last lock before it. A note keeps
   * its key; a step without a note and with nothing left is emptied.
   */
  resetStepParameters(step: number, sound: number, parameters: readonly ParameterName[] = PARAMETER_NAMES): void {
    const data = this.state.project?.patterns[this.state.pattern - 1];
    if (!data) return;
    const cell = readCell(data, step, sound);
    if (!cell) return;
    const next: Cell = { ...cell };
    for (const name of parameters) next[name] = 0;
    const empty = next.key === null && !next.pitch && !next.volume && !next.filter && !next.resonance;
    this.setCell(step, sound, empty ? null : next);
  }

  /** Unroll a sound's roll if it is not open already. */
  unroll(sound: number): void {
    if (!this.state.unrolled.includes(sound)) this.set({ unrolled: [...this.state.unrolled, sound].sort((a, b) => a - b) });
  }

  /** Unroll or roll up a sound's piano roll in the pattern grid. */
  toggleRoll(sound: number): void {
    const unrolled = this.state.unrolled.includes(sound) ? this.state.unrolled.filter((s) => s !== sound) : [...this.state.unrolled, sound].sort((a, b) => a - b);
    this.set({ unrolled });
  }

  setEffects(effects: (number | null)[]): void {
    const pattern = this.state.pattern;
    this.update((p) => {
      const patterns = p.patterns.slice();
      const data = p.patterns[pattern - 1].slice();
      writeEffects(data, effects);
      patterns[pattern - 1] = data;
      return { ...p, patterns };
    });
  }

  // Tracks and samples

  setMelodic(slot: number, clip: Clip | null): void {
    this.update((p) => ({ ...p, melodic: p.melodic.map((c, i) => (i === slot - 1 ? clip : c)) }));
  }

  setDrumSlice(slot: number, key: number, clip: Clip | null): void {
    this.update((p) => {
      const track = p.drums[slot - 9] ?? { slices: new Array(16).fill(null) };
      const slices = track.slices.map((c, i) => (i === key - 1 ? clip : c));
      const drums = p.drums.slice();
      drums[slot - 9] = slices.some((s) => s) ? { slices } : null;
      return { ...p, drums };
    });
  }

  /** Empty every key of a drum kit and forget its name; the pattern notes on that sound stay and play nothing. */
  clearDrumKit(slot: number): void {
    this.update((p) => {
      const drums = p.drums.slice();
      drums[slot - 9] = null;
      return { ...withKitName(p, slot, null), drums };
    });
  }

  // Kits (app-only)

  /** Name a drum sound's kit; an empty name falls back to the default. */
  setKitName(slot: number, name: string): void {
    this.update((p) => withKitName(p, slot, name.trim() ? name : null));
  }

  /** Save a drum sound's kit under a name, replacing the saved kit `replace` when given. */
  async saveKit(slot: number, name: string, replace?: string): Promise<KitRecord | null> {
    const project = this.state.project;
    const track = project?.drums[slot - 9];
    if (!project || !track) {
      this.notify(`Sound ${slot} has no kit to save`);
      return null;
    }
    const now = Date.now();
    const previous = replace ? this.state.kits.find((k) => k.id === replace) : undefined;
    const kit: KitRecord = {
      id: previous?.id ?? newId(),
      name: name.trim() || kitDisplayName(project, this.state.samples, slot),
      slices: track.slices.map((c) => (c ? { ...c } : null)),
      // Saved over a bundled kit, the record stays that kit, edited, as an edited bundled project does; without its
      // identity the next load would find the bundled kit missing and add it a second time.
      preset: previous?.preset,
      createdAt: previous?.createdAt ?? now,
      updatedAt: now,
    };
    await db.kits.put(kit);
    this.set({ kits: [...this.state.kits.filter((k) => k.id !== kit.id), kit].sort((a, b) => a.name.localeCompare(b.name)) });
    this.notify(`Saved kit "${kit.name}"`);
    return kit;
  }

  /** Load a saved kit into a drum sound, replacing its keys and name. Keys whose sample left the library stay empty. */
  loadKit(id: string, slot: number): void {
    const kit = this.state.kits.find((k) => k.id === id);
    if (!kit) return;
    const present = new Set(this.state.samples.map((s) => s.id));
    let missing = 0;
    const slices = kit.slices.map((c) => {
      if (!c) return null;
      if (!present.has(c.sampleId)) {
        missing++;
        return null;
      }
      return { ...c };
    });
    this.update((p) => {
      const drums = p.drums.slice();
      drums[slot - 9] = slices.some((c) => c) ? { slices } : null;
      return { ...withKitName(p, slot, kit.name), drums };
    });
    if (missing) this.notify(`Loaded "${kit.name}"; ${missing} key${missing === 1 ? '' : 's'} left empty because the sample is no longer in the library`);
  }

  async deleteKit(id: string): Promise<void> {
    await db.kits.delete(id);
    this.set({ kits: this.state.kits.filter((k) => k.id !== id) });
  }

  /** Import audio files and assign them to consecutive keys of a drum sound, from `key` on. */
  async assignFilesToPads(slot: number, key: number, files: FileList | File[]): Promise<void> {
    const list = Array.from(files).slice(0, 17 - key);
    const added = await this.importFiles(list, '');
    added.forEach((sample, i) => this.setDrumSlice(slot, key + i, { sampleId: sample.id, start: 0, end: sample.codes.length }));
  }


  clearTrack(sound: number): void {
    if (sound <= 8) this.setMelodic(sound, null);
    else
      this.update((p) => {
        const drums = p.drums.slice();
        drums[sound - 9] = null;
        return { ...p, drums };
      });
  }

  setClip(target: LibraryTarget, clip: Clip | null): void {
    if (target.kind === 'melodic') this.setMelodic(target.slot, clip);
    else this.setDrumSlice(target.slot, target.key, clip);
  }

  // Editors

  private pushEditor(editor: Editor): void {
    this.set({ editors: [...this.state.editors, editor], library: { open: false, target: null, editing: null } });
  }

  /** Edit a sample: the Library opens, or stays open, with that sample's editor expanded under its row. */
  openSampleEditor(id: string): void {
    this.set({ library: { ...this.state.library, open: true, editing: id } });
  }

  /** Fold the expanded sample editor away, leaving the Library open. */
  closeSampleEditor(): void {
    // A renamed sample finds its place in the order now, not while its name was being typed.
    this.set({ library: { ...this.state.library, editing: null }, samples: [...this.state.samples].sort((a, b) => a.name.localeCompare(b.name)) });
  }

  openClipEditor(target: LibraryTarget): void {
    this.pushEditor({ kind: 'clip', target });
  }

  /** The pad editor of a drum sound. */
  openKitEditor(slot: number): void {
    this.pushEditor({ kind: 'kit', slot });
  }

  /** The project memory dialog: every buffer the device will hold. */
  openMemory(): void {
    this.pushEditor({ kind: 'memory' });
  }

  /** Close the top editor, returning to the one it was opened from. */
  closeEditor(): void {
    this.set({ editors: this.state.editors.slice(0, -1) });
  }

  /** Close the top modal layer: the device dialog, then a sample editor expanded in the Library, then the Library, then the top editor. */
  closeTopLayer(): void {
    if (this.state.device) this.closeDevice();
    else if (this.state.library.open && this.state.library.editing) this.closeSampleEditor();
    else if (this.state.library.open) this.closeLibrary();
    else if (this.state.editors.length) this.closeEditor();
  }

  /** Whether any modal is open, so grid shortcuts stay off. In the guide the editors and dialogs sit in the page, not over it. */
  modalOpen(): boolean {
    if (this.state.guide) return false;
    return !!this.state.device || this.state.library.open || this.state.editors.length > 0;
  }

  openDevice(mode: DeviceMode): void {
    this.set({ device: mode });
  }

  closeDevice(): void {
    this.set({ device: null });
  }

  /** Store a sample's edits; the record is written after a pause. Clip windows into it are left as they are (see clampClips). */
  setSampleMods(id: string, mods: Modifications): void {
    const sample = this.state.samples.find((s) => s.id === id);
    if (!sample) return;
    const record = { ...sample, mods: isUnmodified(mods, sample.codes.length) ? undefined : mods, updatedAt: Date.now() };
    this.set({ samples: this.state.samples.map((s) => (s.id === id ? record : s)) });
    this.scheduleSampleWrite(id);
  }

  /** Write a sample's record 300 ms after its last edit; slider drags would otherwise write the whole sample per tick. */
  private scheduleSampleWrite(id: string): void {
    const pending = this.sampleWrites.get(id);
    if (pending) clearTimeout(pending);
    this.sampleWrites.set(
      id,
      setTimeout(() => {
        this.sampleWrites.delete(id);
        const latest = this.state.samples.find((s) => s.id === id);
        if (latest) void db.samples.put(latest);
      }, 300),
    );
  }

  private cancelSampleWrite(id: string): void {
    const pending = this.sampleWrites.get(id);
    if (pending) clearTimeout(pending);
    this.sampleWrites.delete(id);
  }

  /** Bake a sample's edits into its codes, replacing it or adding a copy. */
  async bakeSample(id: string, mode: 'replace' | 'copy'): Promise<void> {
    const sample = this.state.samples.find((s) => s.id === id);
    if (!sample || !sample.mods) return;
    this.cancelSampleWrite(id);
    const codes = applyModifications(sample.codes, sample.mods);
    const now = Date.now();
    if (mode === 'replace') {
      const record: SampleRecord = { ...sample, codes, mods: undefined, updatedAt: now };
      await db.samples.put(record);
      // An edit made during the write (a rename, a slider tick) was made to the old record: the newer one is kept, as is.
      const latest = this.state.samples.find((s) => s.id === id);
      if (latest !== sample) {
        if (latest) {
          this.scheduleSampleWrite(id);
          this.notify('The sample changed while it was being resampled; the change was kept and the resample left undone');
        }
        return;
      }
      this.set({ samples: this.state.samples.map((s) => (s.id === id ? record : s)) });
    } else {
      const record: SampleRecord = { ...sample, id: newId(), name: `${sample.name} (resampled)`, codes, mods: undefined, createdAt: now, updatedAt: now };
      await db.samples.put(record);
      // The copy takes the place of the sample being edited.
      this.set({ samples: [...this.state.samples, record].sort((a, b) => a.name.localeCompare(b.name)), library: { ...this.state.library, open: true, editing: record.id } });
    }
  }

  /**
   * A project's clips against the library: clips of a sample no longer in it are dropped and,
   * with `windows`, every window is pulled inside its sample's current (trimmed) length.
   * Windows are fitted only on the way to the device, the preview and an export, never saved:
   * a trim dragged back, or reset, gives the sounds their whole windows again.
   */
  private clampClips(project: ProjectRecord, { windows = true, samples = this.state.samples }: { windows?: boolean; samples?: SampleRecord[] } = {}): ProjectRecord {
    const lengths = new Map(samples.map((s) => [s.id, modifiedLength(s.mods, s.codes.length)]));
    const fix = (clip: Clip | null): Clip | null => {
      if (!clip) return null;
      const length = lengths.get(clip.sampleId);
      if (length === undefined || length <= 0) return null;
      if (!windows) return clip;
      // Only pull the window inside the sample; never widen it, an empty window is device data.
      const end = Math.min(clip.end, length);
      const start = Math.min(clip.start, end);
      return start === clip.start && end === clip.end ? clip : { ...clip, start, end };
    };
    // Unchanged tracks keep their identity, so memoized rows and rolls can tell nothing happened to them.
    const same = <T,>(before: T[], after: T[]): T[] => (after.every((v, i) => v === before[i]) ? before : after);
    const melodic = same(project.melodic, project.melodic.map(fix));
    const drums = same(
      project.drums,
      project.drums.map((d) => {
        if (!d) return d;
        const slices = same(d.slices, d.slices.map(fix));
        if (slices === d.slices) return d;
        return slices.some((s) => s) ? { slices } : null;
      }),
    );
    return melodic === project.melodic && drums === project.drums ? project : { ...project, melodic, drums };
  }

  openLibrary(target: LibraryTarget | null): void {
    this.set({ library: { open: true, target, editing: null } });
  }

  closeLibrary(): void {
    this.set({ library: { open: false, target: null, editing: null } });
  }

  /** Import audio files into the library; returns the samples added. */
  async importFiles(files: FileList | File[], folder: string): Promise<SampleRecord[]> {
    const added: SampleRecord[] = [];
    for (const file of Array.from(files)) {
      try {
        const { codes, sourceRate } = await importAudioFile(file);
        if (codes.length < 128) throw new Error('shorter than 128 codes');
        const now = Date.now();
        const record: SampleRecord = {
          id: newId(),
          name: file.name.replace(/\.[^.]+$/, ''),
          folder,
          codes,
          sourceName: file.name,
          sourceRate,
          createdAt: now,
          updatedAt: now,
        };
        await db.samples.put(record);
        added.push(record);
      } catch (error) {
        this.notify(`${file.name}: ${(error as Error).message}`);
      }
    }
    if (added.length) this.set({ samples: [...this.state.samples, ...added].sort((a, b) => a.name.localeCompare(b.name)) });
    return added;
  }

  /** Rename a sample; the state changes at once so a name field follows typing, the record is written after. */
  /**
   * Rename a sample. The list keeps its order while the name is typed (a row that jumped as
   * its prefix changed would carry the editor with it) and sorts when the editor closes; the
   * write waits for a pause in typing, as a slider drag's does.
   */
  renameSample(id: string, name: string): void {
    this.set({ samples: this.state.samples.map((s) => (s.id === id ? { ...s, name, updatedAt: Date.now() } : s)) });
    this.scheduleSampleWrite(id);
  }

  /** Rename a folder: every sample in it moves to the new name. Into an existing name, the folders merge. */
  async renameFolder(from: string, to: string): Promise<void> {
    const name = to.trim();
    if (!name || name === from) return;
    await this.renameFolderTo(from, name);
  }

  /** Delete a folder: its samples stay in the library, in no folder. */
  async deleteFolder(folder: string): Promise<void> {
    if (!folder) return;
    await this.renameFolderTo(folder, '');
  }

  private async renameFolderTo(from: string, to: string): Promise<void> {
    const moved = this.state.samples.filter((s) => s.folder === from).map((s) => ({ ...s, folder: to, updatedAt: Date.now() }));
    const ids = new Set(moved.map((s) => s.id));
    this.set({ samples: this.state.samples.map((s) => (ids.has(s.id) ? { ...s, folder: to } : s)) });
    await db.samples.bulkPut(moved);
  }

  async moveSample(id: string, folder: string): Promise<void> {
    this.set({ samples: this.state.samples.map((s) => (s.id === id ? { ...s, folder } : s)) });
    await db.samples.update(id, { folder, updatedAt: Date.now() });
  }

  async deleteSample(id: string): Promise<void> {
    await this.deleteSamples([id]);
  }

  /** Delete samples from the library; clips in the current project that pointed at them become empty. */
  async deleteSamples(ids: string[]): Promise<void> {
    const gone = new Set(ids);
    if (!gone.size) return;
    for (const id of gone) this.cancelSampleWrite(id);
    await db.samples.bulkDelete([...gone]);
    const editing = this.state.library.editing;
    const library = editing && gone.has(editing) ? { ...this.state.library, editing: null } : this.state.library;
    this.set({ samples: this.state.samples.filter((s) => !gone.has(s.id)), library });
    this.update((p) => ({
      ...p,
      melodic: p.melodic.map((c) => (c && gone.has(c.sampleId) ? null : c)),
      drums: p.drums.map((d) => {
        if (!d) return d;
        const slices = d.slices.map((c) => (c && gone.has(c.sampleId) ? null : c));
        return slices.some((s) => s) ? { slices } : null;
      }),
    }));
  }

  // Theme

  async setTheme(theme: Theme): Promise<void> {
    applyTheme(theme);
    this.set({ theme });
    await db.settings.put({ key: 'theme', value: theme });
  }

  // Device

  async setInputDevice(inputDevice: string): Promise<void> {
    this.set({ inputDevice });
    await db.settings.put({ key: 'inputDevice', value: inputDevice });
  }

  /** A project as the device and the preview take it: dead clips dropped, windows inside their trimmed samples. */
  fitted(project: ProjectRecord, samples: SampleRecord[] = this.state.samples): Project {
    return asProject(this.clampClips(project, { samples }));
  }

  resolver(samples: SampleRecord[] = this.state.samples): (id: string) => Uint8Array {
    const byId = new Map(samples.map((s) => [s.id, s]));
    return (id) => {
      const sample = byId.get(id);
      if (!sample) throw new Error('A track uses a sample that is no longer in the library');
      if (!sample.mods) return sample.codes;
      const key = JSON.stringify(sample.mods) + ':' + sample.updatedAt;
      const cached = this.rendered.get(id);
      if (cached && cached.key === key) return cached.codes;
      const codes = applyModifications(sample.codes, sample.mods);
      this.rendered.set(id, { key, codes });
      return codes;
    };
  }

  /** The buffers a project (the current one by default) stores on the device, or the reason it cannot be compiled. */
  memory(project = this.state.project, samples = this.state.samples): { rows: MemoryRow[]; pages: number } | { error: string } {
    if (!project) return { error: 'No project' };
    try {
      return memorySummary(this.fitted(project, samples), this.resolver(samples));
    } catch (error) {
      return { error: (error as Error).message };
    }
  }

  /** Pages the current project needs on the device, or null when it cannot be compiled. */
  pages(): number | null {
    const project = this.state.project;
    if (!project) return null;
    try {
      return projectPages(this.fitted(project), this.resolver());
    } catch {
      return null;
    }
  }

  buildLabels(): LabelStreams {
    const project = this.state.project;
    if (!project) throw new Error('No project');
    const state = compileProject(this.fitted(project), this.resolver(), emptyTemplateState());
    return labelsForBody(encodePackets(serializeState(state)));
  }

  buildRestore(): Uint8Array {
    return encodeRestoreWav(this.buildLabels());
  }

  /** Seconds the current project's transfer takes, or null when it cannot be compiled. */
  transferSeconds(): number | null {
    try {
      return transferSeconds(this.buildLabels().left.length);
    } catch {
      return null;
    }
  }

  /** Decode a recorded backup into a new project and new library samples; returns a summary. */
  // Archives

  /** A project (the current one by default) as a zip: project.json and its samples as mu-law WAVs. */
  async projectArchive(id = this.state.project?.id): Promise<{ name: string; bytes: Uint8Array }> {
    await this.flush();
    const project = id && id === this.state.project?.id ? this.state.project : id ? await db.projects.get(id) : undefined;
    if (!project) throw new Error('No project to export');
    // Clips of a sample deleted since the project was last open are dropped, as opening it would do.
    const files = await packProject(this.clampClips(project), this.state.samples);
    return { name: `${project.name.trim() || 'project'}.sosample.zip`, bytes: zipFiles(files) };
  }

  /** A saved kit as a zip: kit.json and its samples. */
  async kitArchive(kitId: string): Promise<{ name: string; bytes: Uint8Array }> {
    const kit = this.state.kits.find((k) => k.id === kitId);
    if (!kit) throw new Error('No such saved kit');
    const files = await packKit({ name: kit.name, slices: kit.slices }, this.state.samples);
    return { name: `${kit.name.trim() || 'kit'}.kit.zip`, bytes: zipFiles(files) };
  }

  /** Import a project archive as a new project and open it. Library samples with the same audio and edits are reused. */
  /**
   * Import a project archive. It becomes the open project unless `activate` is false (the
   * presets load in a batch); `rename` may give it another name, as when one is taken.
   */
  async importProjectArchive(source: Uint8Array | Blob, options: { activate?: boolean; rename?: (name: string) => string; preset?: string } = {}): Promise<string> {
    const { project, samples } = await unpackProject(unzipFiles(await bytesOf(source)));
    const { ids, added, reused } = await this.adoptSamples(samples);
    const rename = (clip: Clip | null): Clip | null => (clip ? { ...clip, sampleId: ids.get(clip.sampleId)! } : null);
    const now = Date.now();
    const record: ProjectRecord = {
      id: newId(),
      name: options.rename ? options.rename(project.name) : project.name,
      tempo: project.tempo,
      swing: project.swing,
      chain: project.chain,
      melodic: project.melodic.map(rename),
      drums: project.drums.map((d) => (d ? { slices: d.slices.map(rename) } : null)),
      patterns: project.patterns,
      mutes: new Array(16).fill(false),
      solos: new Array(16).fill(false),
      kitNames: project.kitNames,
      preset: options.preset,
      createdAt: now,
      updatedAt: now,
    };
    await this.flush();
    await db.projects.put(record);
    if (options.activate === false) {
      this.set({ projects: await this.summaries() });
    } else {
      await this.activate(record, { projects: await this.summaries() });
    }
    return `Imported "${record.name}": ${plural(added, 'sample')} added, ${reused} reused.`;
  }

  /** Import a kit archive into the saved kits and, given a slot, load it into that drum sound. */
  async importKitArchive(source: Uint8Array | Blob, slot?: number, options: { preset?: string } = {}): Promise<string> {
    const { kit, samples } = await unpackKit(unzipFiles(await bytesOf(source)));
    const { ids, added, reused } = await this.adoptSamples(samples);
    const now = Date.now();
    const record: KitRecord = { id: newId(), name: kit.name, slices: kit.slices.map((c) => (c ? { ...c, sampleId: ids.get(c.sampleId)! } : null)), preset: options.preset, createdAt: now, updatedAt: now };
    await db.kits.put(record);
    this.set({ kits: [...this.state.kits, record].sort((a, b) => a.name.localeCompare(b.name)) });
    if (slot !== undefined) this.loadKit(record.id, slot);
    return `Imported kit "${kit.name}": ${plural(added, 'sample')} added, ${reused} reused.`;
  }

  /** Library ids for unpacked samples: one with the same audio and edits is reused, the rest are added. */
  private async adoptSamples(samples: UnpackedSample[]): Promise<{ ids: Map<string, string>; added: number; reused: number }> {
    const key = (sha: string, mods: Modifications | undefined, length: number): string => {
      if (isUnmodified(mods, length)) return sha;
      const m = mods!;
      return [sha, m.start, m.end, m.gainDb, m.normalize, m.fadeIn, m.fadeOut, m.compressor?.thresholdDb, m.compressor?.ratio, m.compressor?.makeupDb].join(',');
    };
    const existing = new Map<string, string>();
    for (const s of this.state.samples) existing.set(key(await cachedSha256(s.codes), s.mods, s.codes.length), s.id);
    const ids = new Map<string, string>();
    const records: SampleRecord[] = [];
    let reused = 0;
    const now = Date.now();
    for (const s of samples) {
      const k = key(s.sha256, s.mods, s.codes.length);
      const found = existing.get(k);
      if (found) {
        ids.set(s.file, found);
        reused++;
        continue;
      }
      const record: SampleRecord = { id: newId(), name: s.name, folder: s.folder, codes: s.codes, sourceName: s.sourceName, sourceRate: s.sourceRate, createdAt: now, updatedAt: now };
      if (s.mods) record.mods = s.mods;
      records.push(record);
      ids.set(s.file, record.id);
      existing.set(k, record.id);
    }
    if (records.length) {
      await db.samples.bulkPut(records);
      this.set({ samples: [...this.state.samples, ...records].sort((a, b) => a.name.localeCompare(b.name)) });
    }
    return { ids, added: records.length, reused };
  }

  async importBackup(wav: WavData, name: string): Promise<string> {
    const { frame, attempts } = recoverFrame(wav);
    const { project, samples } = importProject(parseFrame(frame));
    const now = Date.now();
    const folder = name;
    const records: SampleRecord[] = [];
    const ids = new Map<string, string>();
    for (const [sampleId, codes] of samples) {
      const id = newId();
      ids.set(sampleId, id);
      records.push({ id, name: `${name} ${sampleId.replace('device-', '')}`, folder, codes, sourceName: name, sourceRate: 23437.5, createdAt: now, updatedAt: now });
    }
    const rename = (clip: Clip | null): Clip | null => (clip ? { ...clip, sampleId: ids.get(clip.sampleId)! } : null);
    const record: ProjectRecord = {
      id: newId(),
      name,
      tempo: project.tempo,
      swing: project.swing,
      chain: project.chain,
      melodic: project.melodic.map(rename),
      drums: project.drums.map((d) => (d ? { slices: d.slices.map(rename) } : null)),
      patterns: project.patterns,
      mutes: new Array(16).fill(false),
      solos: new Array(16).fill(false),
      createdAt: now,
      updatedAt: now,
    };
    await db.samples.bulkPut(records);
    await db.projects.put(record);
    await db.settings.put({ key: 'lastProject', value: record.id });
    this.set({
      samples: [...this.state.samples, ...records].sort((a, b) => a.name.localeCompare(b.name)),
      projects: await this.summaries(),
      project: record,
      pattern: 1,
    });
    const method = attempts[attempts.length - 1].method;
    return `Imported "${name}": ${records.length} sample${records.length === 1 ? '' : 's'}, ${frame.packets.length} packets (${method}).`;
  }
}

const hashes = new WeakMap<Uint8Array, Promise<string>>();

/** The SHA-256 of a codes array, computed once for as long as the array lives. */
function cachedSha256(codes: Uint8Array): Promise<string> {
  let hash = hashes.get(codes);
  if (!hash) {
    hash = sha256Hex(codes);
    hashes.set(codes, hash);
  }
  return hash;
}

function plural(count: number, noun: string): string {
  return `${count} ${noun}${count === 1 ? '' : 's'}`;
}

/** How long a notice stays in the status slot. */
export const NOTICE_SECONDS = 6;

const warnings = new WeakMap<Uint8Array, string | null>();

const dropTables = new WeakMap<Uint8Array, Map<number, number[]>>();

/** The notes a pattern drops to the four voices: by step, the sounds beyond the fourth in the device's rank. Cached per pattern bytes. */
export function voiceDrops(data: Uint8Array): Map<number, number[]> {
  const cached = dropTables.get(data);
  if (cached) return cached;
  const drops = new Map<number, number[]>();
  for (let step = 1; step <= 16; step++) {
    const dropped = VOICE_RANK.filter((sound) => readCell(data, step, sound)?.key).slice(4);
    if (dropped.length) drops.set(step, dropped);
  }
  dropTables.set(data, drops);
  return drops;
}

/** The four-voice warning for a pattern as a sentence, or null when nothing is dropped. Cached per pattern bytes. */
export function voiceWarning(data: Uint8Array): string | null {
  const cached = warnings.get(data);
  if (cached !== undefined) return cached;
  const parts = [...voiceDrops(data)].map(([step, dropped]) => `step ${step} drops sound${dropped.length > 1 ? 's' : ''} ${dropped.join(', ')}`);
  const warning = parts.length ? `4 voices: ${parts.join('; ')}` : null;
  warnings.set(data, warning);
  return warning;
}

/** What a dropped note's own glyph says. */
export function dropText(step: number, sound: number): string {
  return `Dropped: step ${step} has more notes than the device's four voices, and Sound ${sound} is beyond the fourth in its rank.`;
}

/** The key a sound starts on: 5 (the base key) for a melodic sound, 1 for a drum. */
export function defaultKey(sound: number): number {
  return sound <= 8 ? BASE_KEY : 1;
}

/**
 * The note a step without one takes, on `key`: the locks the step already holds stay, and
 * the rest come from the sound's nearest note before the step, else its nearest after,
 * else the defaults. The same rule serves the sequencer, the roll and the phone's pads.
 */
function newNote(data: Uint8Array, step: number, sound: number, key: number): Cell {
  const template = noteTemplate(data, step, sound, key);
  const cell = readCell(data, step, sound);
  if (!cell) return template;
  return { ...template, pitch: cell.pitch || template.pitch, volume: cell.volume || template.volume, filter: cell.filter || template.filter, resonance: cell.resonance || template.resonance };
}

/** A new note on `key`, with the parameters of the sound's nearest note before this step, else its nearest after, else the defaults. */
function noteTemplate(data: Uint8Array, step: number, sound: number, key: number): Cell {
  for (let s = step; s >= 1; s--) {
    const c = readCell(data, s, sound);
    if (c?.key) return { ...c, key };
  }
  for (let s = step + 1; s <= 16; s++) {
    const c = readCell(data, s, sound);
    if (c?.key) return { ...c, key };
  }
  return { key, ...DEFAULT_PARAMETERS };
}

function withKitName(project: ProjectRecord, slot: number, name: string | null): ProjectRecord {
  const kitNames = project.kitNames ? [...project.kitNames] : new Array<string | null>(8).fill(null);
  kitNames[slot - 9] = name;
  return { ...project, kitNames };
}

/** A drum sound's kit name: the one given, else key 1's sample name, else the first sample's. */
export function kitDisplayName(project: ProjectRecord, samples: SampleRecord[], slot: number): string {
  const named = project.kitNames?.[slot - 9];
  if (named) return named;
  const first = project.drums[slot - 9]?.slices.find((c) => c);
  const sample = first ? samples.find((s) => s.id === first.sampleId) : undefined;
  return sample?.name ?? `Kit ${slot}`;
}

/** "Name copy", then "Name copy 2" and so on, avoiding the names in use. */
export function copyName(name: string, taken: string[]): string {
  const base = `${name.replace(/ copy( \d+)?$/, '')} copy`;
  if (!taken.includes(base)) return base;
  for (let n = 2; ; n++) if (!taken.includes(`${base} ${n}`)) return `${base} ${n}`;
}

/** The preview's mix from a project record, with the per-key arrays filled in for older records. */
export function mixOf(record: ProjectRecord): Mix {
  const kits = (table?: boolean[][]) => Array.from({ length: 8 }, (_, i) => table?.[i] ?? new Array(16).fill(false));
  return { mutes: record.mutes ?? [], solos: record.solos ?? [], sliceMutes: kits(record.sliceMutes), sliceSolos: kits(record.sliceSolos) };
}

function flipped(flags: boolean[] | undefined, index: number, length: number): boolean[] {
  const next = Array.from({ length }, (_, i) => flags?.[i] ?? false);
  next[index] = !next[index];
  return next;
}

/** The table with one kit's flags all off; absent tables stay absent. */
function clearedKit(table: boolean[][] | undefined, kit: number): boolean[][] | undefined {
  if (!table?.[kit]?.some(Boolean)) return table;
  return table.map((flags, i) => (i === kit ? new Array(16).fill(false) : flags));
}

function flippedKit(table: boolean[][] | undefined, kit: number, index: number): boolean[][] {
  return Array.from({ length: 8 }, (_, i) => (i === kit ? flipped(table?.[i], index, 16) : (table?.[i] ?? new Array(16).fill(false))));
}

/** How many steps undo keeps. */
const UNDO_STEPS = 200;

export function asProject(record: ProjectRecord): Project {
  // The parts the core compiles and plays; callers pass the fitted record (Store.fitted).
  return {
    tempo: record.tempo,
    swing: record.swing,
    chain: record.chain,
    melodic: record.melodic,
    drums: record.drums,
    patterns: record.patterns,
  };
}

export function applyTheme(theme: Theme): void {
  if (theme === 'system') delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = theme;
}

export const store = new Store();

export function useAppState(): AppState {
  return useSyncExternalStore(store.subscribe, store.getState, store.getState);
}

/**
 * Only the named fields of the state: the component re-renders when one of them changes,
 * not on every change of the store (a pattern selected, the transport started). For views
 * that are costly to draw, such as the library's table and the lists of sounds and songs.
 */
export function useAppFields<K extends keyof AppState>(...keys: K[]): Pick<AppState, K> {
  const last = useRef<Pick<AppState, K> | null>(null);
  const read = (): Pick<AppState, K> => {
    const state = store.getState();
    const previous = last.current;
    if (previous && keys.every((k) => previous[k] === state[k])) return previous;
    const next = {} as Pick<AppState, K>;
    for (const k of keys) next[k] = state[k];
    last.current = next;
    return next;
  };
  return useSyncExternalStore(store.subscribe, read, read);
}
