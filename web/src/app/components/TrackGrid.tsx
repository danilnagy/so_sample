import { type ReactElement, memo, useMemo, useRef, useState } from 'react';

import { PARAMETER_NAMES, type ParameterName, changedParameters, effectiveParameter, readCell } from '../../core/pattern';
import type { Clip, DrumTrack } from '../../core/project';
import { playCodes } from '../samples';
import { dropText, kitDisplayName, mixOf, store, useAppFields, voiceDrops } from '../store';
import { isMuted, soundSilent } from '../playback';
import { BASE_KEY, PARAMETER_LABELS, PARAMETER_RANGES, RESONANCE_CODES, keySemitones, parameterMeaning, rollKeys, semitoneLabel } from '../laws';
import { WarnGlyph } from './Hint';
import { ChevronIcon, KeysIcon, PlayIcon, SlicesIcon } from './Icons';
import { MiniWave } from './MiniWave';

/** Move keyboard focus to another step cell. */
function focusCell(step: number, sound: number): void {
  (document.querySelector(`.cell[data-step="${step}"][data-sound="${sound}"]`) as HTMLElement | null)?.focus();
}

/**
 * The sixteen step cells of one sound. Memoized: a change elsewhere in the app, such as a
 * sample edit, leaves a sound's cells untouched unless its pattern changed. Clicking a step
 * with no note while the roll is closed opens the roll, where the key is chosen. The focused
 * cell is the keyboard cursor: arrows move it, space toggles the note, Delete clears the step.
 */
const StepCells = memo(function StepCells({ sound, data, row, unrolled, empty, silent, currentKey }: { sound: number; data: Uint8Array; row: number; unrolled: boolean; empty: boolean; silent: boolean; currentKey: number }) {
  const changes = changedParameters(data, sound);
  const drops = voiceDrops(data);
  const cells: ReactElement[] = [];
  for (let step = 1; step <= 16; step++) {
    const cell = readCell(data, step, sound);
    const differ = changes.get(step);
    const dropped = !!drops.get(step)?.includes(sound);
    const classes = ['cell'];
    if (dropped) classes.push('dropped');
    if (silent) classes.push('silent');
    if ((step - 1) % 4 === 0) classes.push('beat');
    if (cell?.key) classes.push('note');
    else if (cell) classes.push('lock');
    if (differ) classes.push('changed');
    cells.push(
      <button
        key={step}
        className={classes.join(' ')}
        style={{ gridRow: row, gridColumn: step + 1 }}
        data-step={step}
        data-sound={sound}
        title={
          `Sound ${sound}, step ${step}.` +
          (differ && cell ? ` ${differ.map((n) => `${n[0].toUpperCase()}${n.slice(1)} ${cell[n]}`).join(', ')} ${differ.length === 1 ? 'changes' : 'change'} the value held before this step.` : '') +
          (dropped ? ` ${dropText(step, sound)}` : '') +
          (cell && !cell.key ? ' Parameter lock without a note.' : '') +
          (cell?.key ? ' Click removes the note.' : unrolled ? ` Click adds a note on key ${currentKey}.` : ` Click opens the roll; with the roll open, a click adds a note on key ${currentKey}.`) +
          ' Space toggles a note; Delete clears the step.'
        }
        onClick={(e) => {
          // A note goes on a click. A blank pad opens the roll when it is closed; with the roll open, it takes a
          // note on the sound's current key, with the parameters of its nearest note.
          if (empty) return;
          if (cell?.key) store.setCell(step, sound, null);
          else if (unrolled || e.shiftKey) store.toggleNote(step, sound);
          else store.unroll(sound);
        }}
        onKeyDown={(e) => {
          if (e.key === ' ') store.toggleNote(step, sound);
          else if (e.key === 'Delete' || e.key === 'Backspace') store.setCell(step, sound, null);
          else if (e.key === 'ArrowRight' && step < 16) focusCell(step + 1, sound);
          else if (e.key === 'ArrowLeft' && step > 1) focusCell(step - 1, sound);
          else if (e.key === 'ArrowDown' && sound < 16) focusCell(step, sound + 1);
          else if (e.key === 'ArrowUp' && sound > 1) focusCell(step, sound - 1);
          else return;
          e.preventDefault();
        }}
      >
        {cell?.key ?? ''}
        {dropped && <WarnGlyph text={dropText(step, sound)} />}
      </button>,
    );
  }
  return <>{cells}</>;
});

const LANE_HEIGHT = 80;
const COLUMN = 31; // a step cell plus its gap
const HANDLE = 5;

/** Code to a y position in the lane, top = high; resonance snaps to its levels. */
function codeToY(parameter: ParameterName, code: number): number {
  const [lo, hi] = PARAMETER_RANGES[parameter];
  return HANDLE + (1 - (code - lo) / (hi - lo)) * (LANE_HEIGHT - 2 * HANDLE);
}

function yToCode(parameter: ParameterName, y: number): number {
  const [lo, hi] = PARAMETER_RANGES[parameter];
  const t = Math.max(0, Math.min(1, (LANE_HEIGHT - HANDLE - y) / (LANE_HEIGHT - 2 * HANDLE)));
  const code = Math.round(lo + t * (hi - lo));
  if (parameter !== 'resonance') return code;
  return RESONANCE_CODES.reduce((best, c) => (Math.abs(c - code) < Math.abs(best - code) ? c : best), RESONANCE_CODES[0]);
}

/** The curve of one parameter across the steps, as polyline points, in the lane's own scale. */
function curvePoints(data: Uint8Array, sound: number, parameter: ParameterName): string {
  const points: string[] = [];
  for (let step = 1; step <= 16; step++) {
    const value = effectiveParameter(data, step, sound, parameter);
    if (value) points.push(`${(step - 1) * COLUMN + 14},${codeToY(parameter, value.code).toFixed(1)}`);
  }
  return points.length > 1 ? points.join(' ') : '';
}

/**
 * The parameter lane: one handle per step for the chosen parameter, joined by the curve,
 * with the other three parameters' curves underlaid in the light stroke for context.
 * A filled handle is a locked value on a note, an outlined one a lock without a note, and
 * a pale one the value the step inherits from the last lock before it. Dragging sets the
 * step; dragging across steps paints those that have notes; double-click clears the lock.
 */
function ParameterLane({ sound, data, parameter }: { sound: number; data: Uint8Array; parameter: ParameterName }) {
  const [dragging, setDragging] = useState<number | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  const points = Array.from({ length: 16 }, (_, s) => {
    const step = s + 1;
    const cell = readCell(data, step, sound);
    const value = effectiveParameter(data, step, sound, parameter);
    return { step, cell, value, x: s * COLUMN + 14 };
  });
  const place = (e: React.PointerEvent): { step: number; code: number } => {
    const rect = svg.current!.getBoundingClientRect();
    const step = Math.max(1, Math.min(16, Math.floor((e.clientX - rect.left) / COLUMN) + 1));
    return { step, code: yToCode(parameter, e.clientY - rect.top) };
  };
  const curve = curvePoints(data, sound, parameter);
  const underlays = PARAMETER_NAMES.filter((name) => name !== parameter).map((name) => ({ name, points: curvePoints(data, sound, name) }));
  return (
    <div className="param-lane">
      <div className="selector" role="radiogroup" aria-label={`Sound ${sound} lane parameter`}>
        {PARAMETER_NAMES.map((name) => (
          <button key={name} className={name === parameter ? 'on' : ''} role="radio" aria-checked={name === parameter} onClick={() => store.setLaneParameter(sound, name)}>
            {PARAMETER_LABELS[name]}
          </button>
        ))}
      </div>
      <svg
        ref={svg}
        viewBox={`0 0 ${16 * COLUMN - 3} ${LANE_HEIGHT}`}
        preserveAspectRatio="none"
        aria-label={`${PARAMETER_LABELS[parameter]} per step for Sound ${sound}`}
        onPointerDown={(e) => {
          const { step, code } = place(e);
          (e.target as Element).setPointerCapture?.(e.pointerId);
          e.currentTarget.setPointerCapture(e.pointerId);
          setDragging(step);
          store.setStepParameter(step, sound, parameter, code);
        }}
        onPointerMove={(e) => {
          if (dragging === null) return;
          const { step, code } = place(e);
          if (step === dragging) store.setStepParameter(step, sound, parameter, code);
          else if (readCell(data, step, sound)?.key) {
            // Painting across steps changes those that have notes.
            setDragging(step);
            store.setStepParameter(step, sound, parameter, code);
          }
        }}
        onPointerUp={() => setDragging(null)}
        onPointerCancel={() => setDragging(null)}
        onDoubleClick={(e) => {
          const rect = svg.current!.getBoundingClientRect();
          const step = Math.max(1, Math.min(16, Math.floor((e.clientX - rect.left) / COLUMN) + 1));
          store.setStepParameter(step, sound, parameter, 0);
        }}
      >
        {[1, 5, 9, 13].map((step) => (
          <line key={step} className="baseline" x1={(step - 1) * COLUMN - 2} x2={(step - 1) * COLUMN - 2} y1={0} y2={LANE_HEIGHT} />
        ))}
        {underlays.map(
          (u) =>
            u.points && (
              <polyline key={u.name} className="curve under" points={u.points}>
                <title>{PARAMETER_LABELS[u.name]}</title>
              </polyline>
            ),
        )}
        {curve && <polyline className="curve" points={curve} />}
        {points.map((p) => {
          if (!p.value) return null;
          const y = codeToY(parameter, p.value.code);
          const kind = p.value.own ? (p.cell?.key ? '' : 'lock') : 'held';
          return (
            <g key={p.step}>
              <circle className={`handle ${kind}`} cx={p.x} cy={y} r={HANDLE}>
                <title>{`Step ${p.step}: ${parameterMeaning(parameter, p.value.code)}${p.value.own ? '' : ', held from the last lock'}`}</title>
              </circle>
              {dragging === p.step && (
                <text className="value" x={p.x + 8} y={y < 20 ? y + 14 : y - 8}>
                  {parameterMeaning(parameter, p.value.code)}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

interface RollProps {
  sound: number;
  data: Uint8Array;
  /** Per key 1..16 of a drum sound: muted and soloed in the preview. */
  sliceMutes: boolean[];
  sliceSolos: boolean[];
  /** The whole sound is silenced by the preview's mix. */
  silent: boolean;
  /** The parameter the lane shows. */
  parameter: ParameterName;
  track: DrumTrack | null;
  melodicClip: Clip | null;
  /** Per key 1..16: the resolved codes of the key's sample and its name, or null for an empty key. */
  laneCodes: (Uint8Array | null)[];
  laneNames: (string | null)[];
  row: number;
}

/** Equal when every input is the same, comparing the per-key arrays element by element. */
function sameRoll(a: RollProps, b: RollProps): boolean {
  return (
    a.sound === b.sound &&
    a.data === b.data &&
    a.parameter === b.parameter &&
    a.track === b.track &&
    a.melodicClip === b.melodicClip &&
    a.row === b.row &&
    a.laneCodes.every((c, i) => c === b.laneCodes[i]) &&
    a.laneNames.every((n, i) => n === b.laneNames[i]) &&
    a.silent === b.silent &&
    a.sliceMutes.every((m, i) => m === b.sliceMutes[i]) &&
    a.sliceSolos.every((s, i) => s === b.sliceSolos[i])
  );
}

/**
 * The roll of one sound: a lane per key, by pitch for a melodic sound and by key for a kit.
 * Memoized on its own inputs, so edits to other sounds' samples leave it alone.
 */
const Roll = memo(function Roll({ sound, data, parameter, track, melodicClip, laneCodes, laneNames, row, sliceMutes, sliceSolos, silent }: RollProps) {
  const melodic = sound <= 8;
  const changes = changedParameters(data, sound);
  const lanes = rollKeys(melodic).map((key, index) => {
    const slice = track?.slices[key - 1] ?? null;
    const clip = melodic ? melodicClip : slice;
    const codes = laneCodes[key - 1];
    const semitones = keySemitones(key);
    // A divider every four lanes; in both orders each group is one row of the device's keys.
    const group = index > 0 && index % 4 === 0;
    const preview = () => {
      if (clip && codes) store.audition(sound, key, () => playCodes(codes, clip.start, clip.end, melodic ? 2 ** (semitones / 12) : 1));
    };
    const steps: ReactElement[] = [];
    for (let step = 1; step <= 16; step++) {
      const cell = readCell(data, step, sound);
      const on = cell?.key === key;
      const classes = ['lane-step'];
      if ((step - 1) % 4 === 0) classes.push('beat');
      if (on) classes.push('on');
      if (on && changes.has(step)) classes.push('changed');
      steps.push(
        <button
          key={step}
          className={classes.join(' ')}
          aria-pressed={on}
          aria-label={`Sound ${sound}, step ${step}, key ${key}`}
          title={`Step ${step}, key ${key}${melodic ? ` (${semitoneLabel(semitones)})` : ''}. ${on ? 'Click removes the note.' : cell?.key ? `Click moves the note from key ${cell.key}.` : 'Click adds a note.'}`}
          onClick={() => store.setRollNote(step, sound, key)}
        />,
      );
    }
    return (
      <div className={`lane ${group ? 'group' : ''} ${melodic && key === BASE_KEY ? 'base' : ''} ${silent || (!melodic && (!slice || isMuted({ mutes: [], solos: [], sliceMutes: [sliceMutes], sliceSolos: [sliceSolos] }, 9, key))) ? 'silent' : ''}`} key={key}>
        <div
          // A drum lane opens its key's editor; a melodic lane only labels a key, the sample is set in the sound's row.
          className={`lane-label ${melodic ? '' : 'drum'}`}
          role={melodic ? undefined : 'button'}
          tabIndex={melodic ? undefined : 0}
          title={melodic ? `Key ${key}, ${semitoneLabel(semitones)}` : clip ? `Edit key ${key}'s window or change its sample` : `Choose a sample for key ${key}`}
          onClick={
            melodic
              ? undefined
              : () => {
                  const target = { kind: 'drum' as const, slot: sound, key };
                  if (clip) store.openClipEditor(target);
                  else store.openLibrary(target);
                }
          }
          onKeyDown={
            melodic
              ? undefined
              : (e) => {
                  if (e.target !== e.currentTarget) return;
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    e.currentTarget.click();
                  }
                }
          }
        >
          <span className="lane-key">{key}</span>
          <span className="icon-slot">
            {clip && codes && (
              <button
                className="play"
                title={`Play key ${key}`}
                aria-label={`Play Sound ${sound} key ${key}`}
                onClick={(e) => {
                  e.stopPropagation();
                  preview();
                }}
              >
                <PlayIcon />
              </button>
            )}
          </span>
          <span className="lane-name muted">{melodic ? semitoneLabel(semitones) : slice ? (laneNames[key - 1] ?? 'missing sample') : ''}</span>
          {slice && codes && <MiniWave codes={codes} windows={[slice]} width={56} />}
        </div>
        {steps}
        {!melodic && (
          <>
            <button className={`mix ${sliceMutes[key - 1] ? 'on' : ''}`} style={{ gridColumn: 19 }} disabled={!slice} aria-pressed={sliceMutes[key - 1]} title={slice ? `Mute key ${key} in the preview` : 'Nothing to mute: this key has no sample'} aria-label={`Mute Sound ${sound} key ${key}`} onClick={() => store.toggleSliceMute(sound, key)} onDoubleClick={() => store.clearMix()}>
              M
            </button>
            <button className={`mix ${sliceSolos[key - 1] ? 'on' : ''}`} style={{ gridColumn: 20 }} disabled={!slice} aria-pressed={sliceSolos[key - 1]} title={slice ? `Solo key ${key} in the preview` : 'Nothing to solo: this key has no sample'} aria-label={`Solo Sound ${sound} key ${key}`} onClick={() => store.toggleSliceSolo(sound, key)} onDoubleClick={() => store.clearMix()}>
              S
            </button>
          </>
        )}
      </div>
    );
  });
  return (
    <div className="roll" style={{ gridRow: row, gridColumn: '1 / -1' }}>
      {lanes}
      <ParameterLane sound={sound} data={data} parameter={parameter} />
    </div>
  );
}, sameRoll);

/**
 * A sound's header, the first column of the sequencer: number, icon (a play button covers it
 * on hover), name and shape. The whole header opens the sound's editor; the play button is
 * its own target and plays the sound's current key. The phone's Sound view lists these too.
 */
export const SoundLabel = memo(function SoundLabel({ sound, style, onOpen }: { sound: number; style?: React.CSSProperties; onOpen?: (sound: number) => void }) {
  const { project, samples } = useAppFields('project', 'samples');
  const byId = useMemo(() => new Map(samples.map((s) => [s.id, s])), [samples]);
  const resolve = useMemo(() => store.resolver(samples), [samples]);
  if (!project) return null;
  const mix = mixOf(project);
  const melodic = sound <= 8;
  let icon;
  let name;
  let title;
  let empty: boolean;
  let open: () => void;
  let play: (() => void) | null = null;
  let shape = null;
  const key = store.currentKey(sound);
  if (melodic) {
    const clip = project.melodic[sound - 1];
    const sample = clip ? byId.get(clip.sampleId) : undefined;
    icon = <KeysIcon empty={!clip} />;
    empty = !clip;
    name = clip ? (sample?.name ?? 'missing sample') : 'Add sample…';
    title = clip ? 'Edit the window or change the sample' : 'Choose a sample';
    open = () => {
      if (clip) store.openClipEditor({ kind: 'melodic', slot: sound });
      else store.openLibrary({ kind: 'melodic', slot: sound });
    };
    // The audition plays the window at the sound's current key.
    if (clip && sample) {
      const codes = resolve(clip.sampleId);
      play = () => store.audition(sound, key, () => playCodes(codes, clip.start, clip.end, 2 ** (keySemitones(key) / 12)));
      shape = <MiniWave codes={codes} windows={[clip]} width={56} />;
    }
  } else {
    const track = project.drums[sound - 9];
    icon = <SlicesIcon filled={Array.from({ length: 16 }, (_, k) => !!track?.slices[k])} />;
    empty = !track;
    name = track ? kitDisplayName(project, samples, sound) : 'Add kit…';
    title = 'Edit the kit';
    open = () => store.openKitEditor(sound);
    // The audition plays the kit's current key, when that key holds a sample.
    const slice = track?.slices[key - 1];
    if (slice) {
      const codes = resolve(slice.sampleId);
      play = () => store.audition(sound, key, () => playCodes(codes, slice.start, slice.end));
    }
  }
  const silent = soundSilent(mix, sound) || empty;
  const activate = () => {
    onOpen?.(sound);
    open();
  };
  return (
    // The whole header is one target that opens the sound's editor; only the play button is its own.
    <div
      className={`label ${silent ? 'silent' : ''} ${empty ? 'empty' : ''}`}
      style={style}
      role="button"
      tabIndex={0}
      title={title}
      aria-label={`Sound ${sound}: ${title}`}
      onClick={activate}
      onKeyDown={(e) => {
        if (e.target !== e.currentTarget) return;
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          activate();
        }
      }}
    >
      <span className="badge">{sound}</span>
      <span className="icon-slot">
        {icon}
        {play && (
          <button
            className="play"
            title={`Play key ${key}`}
            aria-label={`Play Sound ${sound}, key ${key}`}
            onClick={(e) => {
              e.stopPropagation();
              play!();
            }}
          >
            <PlayIcon />
          </button>
        )}
      </span>
      <span className={`name ${empty ? 'empty' : ''}`}>{name}</span>
      {shape}
    </div>
  );
});

function TrackGridView() {
  const { project, pattern, samples, unrolled, laneParameter } = useAppFields('project', 'pattern', 'samples', 'unrolled', 'laneParameter');
  // Stable per samples list, so memoized rows and rolls keep their props between unrelated renders.
  const byId = useMemo(() => new Map(samples.map((s) => [s.id, s])), [samples]);
  const resolve = useMemo(() => store.resolver(samples), [samples]);
  if (!project) return null;
  const mix = mixOf(project);
  const data = project.patterns[pattern - 1];
  const rows: ReactElement[] = [];
  /** Grid row of the next element: each sound takes one row, plus one when unrolled. */
  let row = 0;
  for (let sound = 1; sound <= 16; sound++) {
    row++;
    const open_ = unrolled.includes(sound);
    const melodic = sound <= 8;
    const empty = melodic ? !project.melodic[sound - 1] : !project.drums[sound - 9];
    // Silenced by the preview's mix, or holding nothing to play: the row fades.
    const silent = soundSilent(mix, sound) || empty;
    rows.push(<SoundLabel key={`h${sound}`} sound={sound} style={{ gridRow: row, gridColumn: 1 }} />);
    // The chevron sits in its own column, right of step 16.
    rows.push(
      <button
        key={`c${sound}`}
        className={`chevron ${open_ ? 'open' : ''} ${silent ? 'silent' : ''}`}
        style={{ gridRow: row, gridColumn: 18 }}
        // Nothing to unroll without a sample or kit; a roll already open can still be rolled up.
        disabled={empty && !open_}
        onClick={() => store.toggleRoll(sound)}
        aria-expanded={open_}
        aria-label={`${open_ ? 'Roll up' : 'Unroll'} Sound ${sound}`}
        title={open_ ? 'Roll up' : empty ? 'Assign a sample or kit to unroll the keys' : 'Unroll the keys of this sound'}
      >
        <ChevronIcon />
      </button>,
    );
    // Mute and solo for the preview, right of the chevron; the device has no such state.
    rows.push(
      <button key={`m${sound}`} className={`mix ${mix.mutes[sound - 1] ? 'on' : ''}`} style={{ gridRow: row, gridColumn: 19 }} disabled={empty} aria-pressed={!!mix.mutes[sound - 1]} title={empty ? 'Nothing to mute: assign a sample or kit first' : 'Mute this sound in the preview'} aria-label={`Mute Sound ${sound}`} onClick={() => store.toggleMute(sound)} onDoubleClick={() => store.clearMix()}>
        M
      </button>,
      <button key={`o${sound}`} className={`mix ${mix.solos[sound - 1] ? 'on' : ''}`} style={{ gridRow: row, gridColumn: 20 }} disabled={empty} aria-pressed={!!mix.solos[sound - 1]} title={empty ? 'Nothing to solo: assign a sample or kit first' : 'Solo this sound in the preview'} aria-label={`Solo Sound ${sound}`} onClick={() => store.toggleSolo(sound)} onDoubleClick={() => store.clearMix()}>
        S
      </button>,
    );
    rows.push(<StepCells key={`s${sound}`} sound={sound} data={data} row={row} unrolled={open_} empty={empty} silent={silent} currentKey={store.currentKey(sound)} />);
    if (!open_) continue;
    row++;
    const track = melodic ? null : project.drums[sound - 9];
    const melodicClip = melodic ? project.melodic[sound - 1] : null;
    // Resolved codes are stable per sample until it is edited, so an untouched roll keeps its props.
    const laneCodes: (Uint8Array | null)[] = [];
    const laneNames: (string | null)[] = [];
    for (let k = 0; k < 16; k++) {
      const clip = melodic ? melodicClip : (track?.slices[k] ?? null);
      const sample = clip ? byId.get(clip.sampleId) : undefined;
      laneCodes.push(sample ? resolve(sample.id) : null);
      laneNames.push(sample ? sample.name : null);
    }
    rows.push(
      <Roll key={`r${sound}`} sound={sound} data={data} parameter={laneParameter[sound] ?? 'volume'} track={track} melodicClip={melodicClip} laneCodes={laneCodes} laneNames={laneNames} row={row} sliceMutes={mix.sliceMutes[sound - 9] ?? []} sliceSolos={mix.sliceSolos[sound - 9] ?? []} silent={silent} />,
    );
  }
  return <div className="grid">{rows}</div>;
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const TrackGrid = memo(TrackGridView);
