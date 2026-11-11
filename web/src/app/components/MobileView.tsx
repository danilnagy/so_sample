import { memo, useEffect, useRef, useState } from 'react';

import { DEFAULT_PARAMETERS, PARAMETER_NAMES, type ParameterName, changedParameters, effectiveParameter, patternIsEmpty, readCell } from '../../core/pattern';
import { type LaneParameter, timingBadge, PARAMETER_LABELS, PARAMETER_RANGES, RESONANCE_CODES, keySemitones, parameterMeaning, semitoneLabel, timingChoices, timingIndex, timingLabel, timingMeaning, timingTitle } from '../laws';
import { isMuted, soundSilent } from '../playback';
import { playCodes } from '../samples';
import { type MobileView as View, dropText, kitDisplayName, mixOf, store, useAppFields, type useAppState, voiceDrops } from '../store';
import { usePlaybackPick, useSoundingKeys } from '../usePlayhead';
import { FxCells } from './FxRow';
import { ArrowDownIcon, ArrowUpIcon, DragIcon, PlayIcon, TrashIcon } from './Icons';
import { WarnGlyph } from './Hint';
import { PatternBar } from './PatternBar';
import { PatternPicker } from './PatternPicker';
import { SoundLabel } from './TrackGrid';

const VIEWS: { id: View; label: string }[] = [
  { id: 'sound', label: 'Sound' },
  { id: 'fx', label: 'FX' },
  { id: 'pattern', label: 'Pattern' },
  { id: 'song', label: 'Song' },
];

/**
 * The pad layout for narrow screens: a view bar, the pattern strip (the desktop bar's
 * buttons, one row of 16 or two of 8), then the view: the sound list (the desktop label
 * column with play, mute and solo), or a context row and one 4x4 grid showing a
 * sixteen-wide strip of the project (effects, one sound's steps), or the song's rows.
 */
export function MobileView() {
  const { project, pattern, mobile, copying } = useAppFields('project', 'pattern', 'mobile', 'copying');
  if (!project) return null;
  const { view } = mobile;
  return (
    <div className="mobile">
      <div className="viewbar" role="tablist">
        {VIEWS.map((v) => (
          <button key={v.id} role="tab" aria-selected={view === v.id} className={view === v.id ? 'on' : ''} onClick={() => store.setMobileView(v.id)}>
            {v.label}
          </button>
        ))}
      </div>
      <PatternBar compact />
      {view === 'fx' && <FxPads data={project.patterns[pattern - 1]} pattern={pattern} copying={copying} />}
      {view === 'sound' && <SoundList />}
      {view === 'pattern' && <SequencePads />}
      {view === 'song' && <SongPads />}
    </div>
  );
}

/** The step marker of a pattern's pads, following playback on its own so a step redraws only the marker, not the pads. */
function LivePadMarks({ pattern }: { pattern: number }) {
  const step = usePlaybackPick((p) => (p && p.pattern === pattern ? p.step : null));
  return <PadMarks at={step} />;
}

/** A layer over the pads carrying the playing marker under pad `at`, so a faded pad keeps a full-strength marker. */
function PadMarks({ at, cells = 16 }: { at: number | null | undefined; cells?: number }) {
  return (
    <div className="pad-marks" aria-hidden="true">
      {Array.from({ length: cells }, (_, i) => (
        <span key={i} className={at === i + 1 ? 'on' : ''} />
      ))}
    </div>
  );
}

/**
 * The effects of the current pattern on the pads; each pad holds the native list, as the FX
 * row does. The bar carries Copy and Clear for the whole pattern and for its effects, the
 * phone's home for the desktop pattern bar's buttons; a pending copy is finished by tapping
 * a pattern in the strip above.
 */
function FxPadsView({ data, pattern, copying }: { data: Uint8Array; pattern: number; copying: ReturnType<typeof useAppState>['copying'] }) {
  const group = (kind: 'pattern' | 'fx', label: string) => {
    const active = copying?.kind === kind;
    return (
      <span className="group" key={kind}>
        <span className="muted">{label}</span>
        <button className={active ? 'cancel' : ''} onClick={() => (active ? store.cancelCopy() : store.startCopy(kind))}>
          {active ? 'Cancel' : 'Copy'}
        </button>
        <button onClick={() => confirm(kind === 'pattern' ? `Clear pattern ${pattern}?` : `Clear the effects of pattern ${pattern}?`) && (kind === 'pattern' ? store.clearPattern(pattern) : store.clearEffects(pattern))}>Clear</button>
      </span>
    );
  };
  return (
    <>
      {/* The pattern's actions at the left, the effects' at the right; the two wrap onto two lines when the row is short. */}
      <div className="context wrap">
        {group('pattern', 'Pattern')}
        <div className="spacer" />
        {copying && <span className="muted hint">{copying.kind === 'pattern' ? `Copy pattern ${copying.from} to…` : `Copy FX of pattern ${copying.from} to…`}</span>}
        {group('fx', 'FX')}
      </div>
      {/* The step sounding, only while the pattern shown is the one playing; the pattern strip above points at the one that is. */}
      <div className="pad-wrap">
        <div className="pad-grid">
          <FxCells data={data} />
          <LivePadMarks pattern={pattern} />
        </div>
      </div>
    </>
  );
}

/** What a sound holds, for the pads and the Pattern view's bar. */
function soundInfo(project: NonNullable<ReturnType<typeof useAppState>['project']>, samples: ReturnType<typeof useAppState>['samples'], sound: number) {
  const melodic = sound <= 8;
  const clip = melodic ? project.melodic[sound - 1] : null;
  const track = melodic ? null : project.drums[sound - 9];
  const empty = melodic ? !clip : !track;
  const name = melodic ? (clip ? (samples.find((s) => s.id === clip.sampleId)?.name ?? 'missing sample') : '') : track ? kitDisplayName(project, samples, sound) : '';
  return { melodic, clip, track, empty, name };
}

/** Play a sound as its row's play button would: its window at the given key for a melodic sound, that key's sample for a kit. */
function auditionSound(sound: number, info: ReturnType<typeof soundInfo>, key: number): void {
  const clip = info.melodic ? info.clip : info.track?.slices[key - 1];
  if (!clip) return;
  store.audition(sound, key, () => playCodes(store.resolver()(clip.sampleId), clip.start, clip.end, info.melodic ? 2 ** (keySemitones(key) / 12) : 1));
}

/** Mute and solo for one sound, as a pair of buttons. */
function MixButtons({ sound, empty }: { sound: number; empty: boolean }) {
  const { project } = useAppFields('project');
  if (!project) return null;
  const mix = mixOf(project);
  return (
    <>
      <button className={`mix ${mix.mutes[sound - 1] ? 'on' : ''}`} disabled={empty} aria-pressed={!!mix.mutes[sound - 1]} title="Mute this sound in the preview" aria-label={`Mute Sound ${sound}`} onClick={() => store.toggleMute(sound)} onDoubleClick={() => store.clearMix()}>
        M
      </button>
      <button className={`mix ${mix.solos[sound - 1] ? 'on' : ''}`} disabled={empty} aria-pressed={!!mix.solos[sound - 1]} title="Solo this sound in the preview" aria-label={`Solo Sound ${sound}`} onClick={() => store.toggleSolo(sound)} onDoubleClick={() => store.clearMix()}>
        S
      </button>
    </>
  );
}

/** Opens what edits a sound: the clip editor or the library for a melodic slot, the kit editor for a drum slot. */
function openSoundEditor(info: ReturnType<typeof soundInfo>, sound: number) {
  if (info.melodic) {
    if (info.clip) store.openClipEditor({ kind: 'melodic', slot: sound });
    else store.openLibrary({ kind: 'melodic', slot: sound });
  } else store.openKitEditor(sound);
}

function editLabel(info: ReturnType<typeof soundInfo>) {
  return info.empty ? (info.melodic ? 'Add sample…' : 'Add kit…') : 'Edit…';
}

const PARAMETER_TITLES: Record<ParameterName, string> = { pitch: 'Pitch', volume: 'Volume', filter: 'Filter', resonance: 'Resonance' };

/**
 * The parameter row of the Pattern view: a list of the four step parameters at the left and,
 * at the right, a slider with the selected step's value, as the desktop's lanes show it. The
 * value is the step's own lock, else the one it inherits from the last lock before it, else
 * the default. Clear removes the step's lock on the chosen parameter and Clear all removes all
 * four, as a double-click on a desktop lane handle does, so the step holds the values before
 * it. With no step selected the row stays in place, disabled, so the pads do not move.
 */
/** The row's choice: the four parameters, then the note's timing (Length on a melodic sound, Repeat on a drum). */
function LaneSelect({ sound, value }: { sound: number; value: LaneParameter }) {
  const title = value === 'timing' ? timingTitle(sound) : PARAMETER_TITLES[value];
  return (
    <select className="param-select" value={value} aria-label="Step parameter" title={title} onChange={(e) => store.setLaneParameter(sound, e.target.value as LaneParameter)}>
      {PARAMETER_NAMES.map((name) => (
        <option key={name} value={name} title={PARAMETER_TITLES[name]}>
          {PARAMETER_LABELS[name]}
        </option>
      ))}
      <option value="timing" title={timingTitle(sound)}>
        {timingLabel(sound)}
      </option>
    </select>
  );
}

/**
 * The parameter row on the note's timing: a slider through the sound's values (1 to 14
 * steps or full for a melodic note, 1 to 8 hits for a drum), the value, and Clear back to
 * the default. Timing belongs to the note alone, so a step without a note has none.
 */
function TimingRow({ sound, data, step }: { sound: number; data: Uint8Array; step: number | null }) {
  const cell = step === null ? null : readCell(data, step, sound);
  const note = !!cell?.key;
  const choices = timingChoices(sound);
  const index = timingIndex(sound, cell?.timing);
  const title = timingTitle(sound);
  return (
    <div className={`param-row ${step === null ? 'disabled' : ''}`}>
      <LaneSelect sound={sound} value="timing" />
      <input
        type="range"
        className="param-slider"
        min={0}
        max={choices.length - 1}
        step={1}
        value={index}
        disabled={!note}
        aria-label={step === null ? `${title} of the selected note` : `${title} of the note on step ${step}`}
        title={!note ? 'Tap a step with a note to set its timing' : `${title} of step ${step}: ${timingMeaning(sound, cell?.timing)}`}
        onChange={(e) => step !== null && store.setStepTiming(step, sound, choices[Number(e.target.value)])}
      />
      <span className={`param-value ${cell?.timing !== undefined ? 'locked' : step === null ? 'none' : 'default'}`}>
        {step === null ? 'no step' : note ? timingMeaning(sound, cell?.timing) : 'no note'}
      </span>
      <button
        className="param-clear"
        disabled={cell?.timing === undefined}
        title={sound <= 8 ? 'Back to the full length' : 'Back to a single hit'}
        aria-label={`Clear ${title} of step ${step ?? ''}`}
        onClick={() => step !== null && store.setStepTiming(step, sound, sound <= 8 ? 15 : 1)}
      >
        Clear
      </button>
    </div>
  );
}

function ParameterRow({ sound, data, step }: { sound: number; data: Uint8Array; step: number | null }) {
  const { laneParameter } = useAppFields('laneParameter');
  const choice = laneParameter[sound] ?? 'volume';
  if (choice === 'timing') return <TimingRow sound={sound} data={data} step={step} />;
  return <LockRow sound={sound} data={data} step={step} parameter={choice} />;
}

function LockRow({ sound, data, step, parameter }: { sound: number; data: Uint8Array; step: number | null; parameter: ParameterName }) {
  const cell = step === null ? null : readCell(data, step, sound);
  const effective = step === null ? null : effectiveParameter(data, step, sound, parameter);
  const code = effective?.code ?? DEFAULT_PARAMETERS[parameter];
  const clearable = (name: ParameterName) => !!cell && cell[name] !== 0;
  const anyClearable = PARAMETER_NAMES.some(clearable);
  const [lo, hi] = PARAMETER_RANGES[parameter];
  // Resonance has eight levels: the slider moves through them rather than every code.
  const resonance = parameter === 'resonance';
  const position = resonance ? RESONANCE_CODES.reduce((best, c, i) => (Math.abs(c - code) < Math.abs(RESONANCE_CODES[best] - code) ? i : best), 0) : code;
  const state = step === null ? 'none' : effective ? (effective.own ? 'locked' : 'inherited') : 'default';
  return (
    <div className={`param-row ${step === null ? 'disabled' : ''}`}>
      <LaneSelect sound={sound} value={parameter} />
      <input
        type="range"
        className="param-slider"
        min={resonance ? 0 : lo}
        max={resonance ? RESONANCE_CODES.length - 1 : hi}
        step={1}
        value={position}
        disabled={step === null}
        aria-label={step === null ? `${PARAMETER_TITLES[parameter]} of the selected step` : `${PARAMETER_TITLES[parameter]} of step ${step}`}
        title={step === null ? 'Tap a step to edit its value' : `${PARAMETER_TITLES[parameter]} of step ${step}: ${parameterMeaning(parameter, code)}, ${state}`}
        onChange={(e) => step !== null && store.setStepParameter(step, sound, parameter, resonance ? RESONANCE_CODES[Number(e.target.value)] : Number(e.target.value))}
      />
      <span className={`param-value ${state}`} title={state === 'none' ? 'Tap a step to see its value' : state === 'locked' ? 'Set on this step' : state === 'inherited' ? 'Carried from the last step that sets it' : 'No step sets it: the default'}>
        {step === null ? 'no step' : parameterMeaning(parameter, code)}
      </span>
      <button
        className="param-clear"
        disabled={!clearable(parameter)}
        title={`Remove this step's ${PARAMETER_TITLES[parameter].toLowerCase()} lock, so it holds the last one before it`}
        aria-label={`Clear ${PARAMETER_TITLES[parameter]} of step ${step ?? ''}`}
        onClick={() => step !== null && store.resetStepParameters(step, sound, [parameter])}
      >
        Clear
      </button>
      <button
        className="param-clear-all"
        disabled={!anyClearable}
        title="Remove all four of this step's locks, so it holds the values before it"
        aria-label={`Clear all parameters of step ${step ?? ''}`}
        onClick={() => step !== null && store.resetStepParameters(step, sound)}
      >
        Clear all
      </button>
    </div>
  );
}

/**
 * The Sound view: the sequencer's first column (number, icon, name, shape) with, at the
 * right, a play button of its own (the desktop's appears on hover, which touch lacks) that
 * the monitor covers while the sound plays, from the preview or an audition, showing the
 * key, and the mute and solo buttons, as if the step pads were taken out. Tapping a header opens its editor,
 * as on the desktop, and makes it the sound the Pattern view sequences.
 */
/** Opening a sound from the list also makes it the Pattern view's: one function for every row, so the rows stay memoized. */
const chooseSound = (sound: number) => store.setMobileSound(sound);

function SoundListView() {
  const sounding = useSoundingKeys();
  return (
    <div className="grid sounds" role="list">
      {Array.from({ length: 16 }, (_, i) => (
        <SoundRow key={i + 1} sound={i + 1} sounding={sounding[i]} />
      ))}
    </div>
  );
}

/** One row of the Sound view, memoized: a monitor lighting up redraws only its own row. */
const SoundRow = memo(function SoundRow({ sound, sounding }: { sound: number; sounding: number | null }) {
  const { project, samples } = useAppFields('project', 'samples');
  if (!project) return null;
  const mix = mixOf(project);
  const info = soundInfo(project, samples, sound);
  const empty = info.empty;
  const current = store.currentKey(sound);
  const key = sounding;
  return (
    <>
      <SoundLabel sound={sound} onOpen={chooseSound} />
      {/* The play button, with the monitor over it while the sound plays: a tile with the key that lets taps through. */}
      <span className="play-cell">
        <button className="icon-button play-column" disabled={empty} title={`Play key ${current}`} aria-label={`Play Sound ${sound} (key ${current})`} onClick={() => auditionSound(sound, info, current)}>
          <PlayIcon />
        </button>
        <span className={`monitor ${key ? 'on' : ''} ${key && isMuted(mix, sound, key) ? 'silent' : ''}`} role="status" aria-label={key ? `Sound ${sound} plays key ${key}` : `Sound ${sound} silent`} title="The key this sound is sounding">
          {key ?? ''}
        </span>
      </span>
      <MixButtons sound={sound} empty={empty} />
    </>
  );
});

/** The Pattern view: one sound's sixteen steps on the pads, the sound chosen from a list in the bar, with play, edit, mute and solo; the key strip and the parameter row above the pads. */
function SequencePadsView() {
  const { project, pattern, samples, mobile } = useAppFields('project', 'pattern', 'samples', 'mobile');
  const selected = mobile.step;
  // A press anywhere but on a pad, in the parameter row or on undo and redo (which show the value they restore) drops the selection.
  useEffect(() => {
    if (selected === null) return;
    const away = (e: PointerEvent) => {
      if (!(e.target as Element).closest?.('.pad-grid .pad.step, .param-row, .undo-buttons')) store.setMobileStep(null);
    };
    document.addEventListener('pointerdown', away);
    return () => document.removeEventListener('pointerdown', away);
  }, [selected]);
  if (!project) return null;
  const sound = mobile.sound;
  const info = soundInfo(project, samples, sound);
  const { melodic, clip, track, empty } = info;
  const data = project.patterns[pattern - 1];
  const mix = mixOf(project);
  const current = store.currentKey(sound);
  const changes = changedParameters(data, sound);
  const drops = voiceDrops(data);
  return (
    <>
      <div className="context">
        {/* Choosing here changes the sound without playing it; the Sound view's pads play on a tap. */}
        <select className="sound-select" value={sound} aria-label="Sound" onChange={(e) => store.setMobileSound(Number(e.target.value))}>
          {Array.from({ length: 16 }, (_, i) => {
            const s = i + 1;
            const other = soundInfo(project, samples, s);
            return (
              <option key={s} value={s}>
                {s} {other.name || (other.melodic ? 'no sample' : 'no kit')}
              </option>
            );
          })}
        </select>
        {!empty && (
          <button className="icon-button" title={`Play key ${current}`} aria-label={`Play Sound ${sound}, key ${current}`} onClick={() => auditionSound(sound, info, current)}>
            <PlayIcon />
          </button>
        )}
        <button onClick={() => openSoundEditor(info, sound)}>{editLabel(info)}</button>
        <MixButtons sound={sound} empty={empty} />
      </div>
      {/* The current key: new notes take it and the play button plays it; a tap chooses and plays a key. */}
      <div className="keys" role="radiogroup" aria-label="Current key">
        {Array.from({ length: 16 }, (_, i) => {
          const key = i + 1;
          const has = melodic ? !!clip : !!track?.slices[key - 1];
          return (
            <button
              key={key}
              role="radio"
              aria-checked={current === key}
              className={`key ${current === key ? 'on' : ''} ${has ? '' : 'silent'}`}
              disabled={!has}
              title={melodic ? `Key ${key}, ${semitoneLabel(keySemitones(key))}` : track?.slices[key - 1] ? `Key ${key}` : `Key ${key}: no sample`}
              onClick={() => {
                store.setCurrentKey(sound, key);
                auditionSound(sound, info, key);
              }}
            >
              {key}
            </button>
          );
        })}
      </div>
      {!empty && <ParameterRow sound={sound} data={data} step={selected} />}
      <div className="pad-wrap">
      <div className="pad-grid">
        {Array.from({ length: 16 }, (_, i) => {
          const step = i + 1;
          const cell = readCell(data, step, sound);
          const silent = cell?.key ? isMuted(mix, sound, cell.key) : soundSilent(mix, sound);
          const differ = changes.get(step);
          const dropped = !!drops.get(step)?.includes(sound);
          return (
            <button
              key={step}
              className={`pad step ${cell?.key ? 'note' : cell ? 'lock' : ''} ${differ ? 'changed' : ''} ${dropped ? 'dropped' : ''} ${step === selected ? 'selected' : ''} ${(step - 1) % 4 === 0 ? 'beat' : ''} ${silent || empty ? 'silent' : ''}`}
              disabled={empty}
              aria-pressed={step === selected}
              title={
                `Step ${step}${cell?.key ? `, key ${cell.key}` : ''}.` +
                (differ && cell ? ` ${differ.map((n) => `${n[0].toUpperCase()}${n.slice(1)} ${cell[n]}`).join(', ')} ${differ.length === 1 ? 'changes' : 'change'} the value held before this step.` : '') +
                (dropped ? ` ${dropText(step, sound)}` : '') +
                (cell?.key ? (step === selected ? ' Tap removes the note.' : ' Tap selects the step; tapping again removes the note.') : ` Tap adds a note on key ${current} and selects the step.`)
              }
              onClick={() => store.tapStep(step, sound)}
            >
              {cell?.key ?? ''}
              {cell?.key && cell.timing !== undefined && <span className="timing-badge">{timingBadge(sound, cell.timing)}</span>}
              {dropped && <WarnGlyph text={dropText(step, sound)} />}
            </button>
          );
        })}
        {/* Only while the pattern shown is the one sounding; otherwise the strip above shows which is. */}
        <LivePadMarks pattern={pattern} />
      </div>
      </div>
    </>
  );
}

/**
 * The song's entries as pads, the grid growing a row at a time, each showing its pattern.
 * Tap selects an entry and shows its remove button; the + pad at the end opens the 4x4
 * pattern picker, which appends.
 */
function SongPadsView() {
  const { project, songEntry } = useAppFields('project', 'songEntry');
  const playingEntry = usePlaybackPick((p) => p?.entry ?? null);
  const [adding, setAdding] = useState<DOMRect | null>(null);
  /** The entry being dragged by its handle, if any. */
  const [dragging, setDragging] = useState<number | null>(null);
  const list = useRef<HTMLDivElement>(null);
  if (!project) return null;
  const chain = project.chain;
  const picked = songEntry !== null && songEntry < chain.length ? songEntry : null;
  /** The entry whose row the pointer is over, from the rows' boxes. */
  const rowAt = (y: number): number | null => {
    const rows = list.current?.querySelectorAll<HTMLElement>('.song-row') ?? [];
    for (let i = 0; i < rows.length; i++) {
      const r = rows[i].getBoundingClientRect();
      if (y >= r.top && y < r.bottom) return i;
    }
    return null;
  };
  const dragTo = (y: number) => {
    if (dragging === null) return;
    const over = rowAt(y);
    if (over === null || over === dragging) return;
    const next = chain.slice();
    const [item] = next.splice(dragging, 1);
    next.splice(over, 0, item);
    store.setChain(next);
    if (songEntry === dragging) store.setSongEntry(over);
    setDragging(over);
  };
  return (
    <>
      <div className="context">
        <div className="spacer" />
        <button onClick={() => confirm('Clear the song? Pattern 1 alone stays.') && store.clearChain()}>Clear</button>
        <span className="count" title="Patterns in the song, of the 128 the device holds">
          {chain.length} / 128
        </span>
      </div>
      {/* The entries as rows, like the sounds: a handle to drag, the entry's place, its pattern, and move and remove buttons. */}
      <div className="song-list" ref={list} role="list">
        {chain.map((p, i) => (
          <div
            className={`song-row ${picked === i ? 'on' : ''} ${playingEntry === i ? 'playing' : ''} ${dragging === i ? 'dragging' : ''}`}
            key={i}
            role="listitem"
            aria-current={playingEntry === i ? 'true' : undefined}
          >
            <span
              className="handle"
              role="button"
              aria-label={`Drag entry ${i + 1}`}
              title="Drag to reorder"
              onPointerDown={(e) => {
                e.currentTarget.setPointerCapture(e.pointerId);
                setDragging(i);
              }}
              onPointerMove={(e) => dragging !== null && dragTo(e.clientY)}
              onPointerUp={() => setDragging(null)}
              onPointerCancel={() => setDragging(null)}
            >
              <DragIcon />
            </span>
            <button
              className={`entry ${patternIsEmpty(project.patterns[p - 1]) ? '' : 'filled'}`}
              aria-pressed={picked === i}
              title={`Entry ${i + 1}: pattern ${p}.${i === 0 ? ' The first pattern is what the device plays after a restore.' : ''} Tap to select.`}
              onClick={() => store.selectSongEntry(i)}
            >
              <span className="badge">{i + 1}</span>
              <span className="pattern-number">Pattern {p}</span>
            </button>
            <span className="row-actions">
              <button
                className="icon-button"
                aria-label={`Move entry ${i + 1} up`}
                title="Move one place earlier"
                disabled={i === 0}
                onClick={() => moveEntry(chain, i, i - 1, songEntry)}
              >
                <ArrowUpIcon />
              </button>
              <button className="icon-button" aria-label={`Move entry ${i + 1} down`} title="Move one place later" disabled={i === chain.length - 1} onClick={() => moveEntry(chain, i, i + 1, songEntry)}>
                <ArrowDownIcon />
              </button>
              <button
                className="icon-button"
                aria-label={`Remove entry ${i + 1}`}
                title={chain.length === 1 ? 'The song keeps at least one pattern' : 'Remove this entry from the song'}
                disabled={chain.length === 1}
                onClick={() => {
                  store.setChain(chain.filter((_, j) => j !== i));
                  if (songEntry === i) store.setSongEntry(null);
                }}
              >
                <TrashIcon />
              </button>
            </span>
          </div>
        ))}
        <button
          className="song-add"
          title={chain.length >= 128 ? 'The song holds 128 patterns' : 'Add a pattern to the end of the song'}
          aria-label="Add a pattern to the song"
          disabled={chain.length >= 128}
          onClick={(e) => setAdding(adding ? null : e.currentTarget.getBoundingClientRect())}
        >
          + Add pattern
        </button>
        {adding && <PatternPicker anchor={adding} onClose={() => setAdding(null)} />}
      </div>
    </>
  );
}

/** Swap two neighbouring entries; a selection on either follows its entry. */
function moveEntry(chain: number[], from: number, to: number, selected: number | null): void {
  if (to < 0 || to >= chain.length) return;
  const next = chain.slice();
  [next[from], next[to]] = [next[to], next[from]];
  store.setChain(next);
  if (selected === from) store.setSongEntry(to);
  else if (selected === to) store.setSongEntry(from);
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const SoundList = memo(SoundListView);
export const SequencePads = memo(SequencePadsView);
export const SongPads = memo(SongPadsView);
export const FxPads = memo(FxPadsView);
