import { memo, useMemo } from 'react';

import { decodeMulawCodes } from '../../core/mulaw';
import { MIN_WINDOW_CODES, pagesFor } from '../../core/project';
import { playCodes, secondsOf } from '../samples';
import { type LibraryTarget, store, useAppFields } from '../store';
import { usePlayhead } from '../usePlayhead';
import { Waveform } from './Waveform';

/** Edit the window of one track clip (a melodic sound or one drum key) into its sample. */
function ClipEditorView({ target }: { target: LibraryTarget }) {
  const { project, samples } = useAppFields('project', 'samples');
  const clip = target.kind === 'melodic' ? project?.melodic[target.slot - 1] : project?.drums[target.slot - 9]?.slices[target.key - 1];
  const sample = clip ? samples.find((s) => s.id === clip.sampleId) : undefined;
  const codes = useMemo(() => (sample ? store.resolver()(sample.id) : new Uint8Array(0)), [sample]);
  const decoded = useMemo(() => decodeMulawCodes(codes), [codes]);
  const [playhead, play] = usePlayhead();
  if (!clip || !sample) return null;
  const where = target.kind === 'melodic' ? `Sound ${target.slot}` : `Sound ${target.slot}, key ${target.key}`;
  const set = (start: number, end: number) => store.setClip(target, { ...clip, start, end });
  const start = Math.min(clip.start, codes.length);
  const end = Math.min(clip.end, codes.length);
  return (
    <div className="modal-backdrop" onClick={() => store.closeEditor()}>
      <div className="modal editor" onClick={(e) => e.stopPropagation()}>
        <header>
          <strong>{where}</strong>
          <span className="muted">{sample.name}</span>
          <div className="spacer" />
          <button onClick={() => play(() => playCodes(codes, start, end))}>Preview</button>
          <button onClick={() => set(0, codes.length)}>Whole sample</button>
          <button onClick={() => store.openSampleEditor(sample.id)}>Edit sample</button>
          <button onClick={() => store.openLibrary(target)}>Change sample…</button>
          <button
            onClick={() => {
              store.setClip(target, null);
              store.closeEditor();
            }}
          >
            Clear
          </button>
          <button onClick={() => store.closeEditor()}>Close</button>
        </header>
        <div className="editor-body">
          <Waveform samples={decoded} start={start} end={end} minimum={MIN_WINDOW_CODES} onChange={set} playhead={playhead} />
          <div className="controls">
            <label>
              Start
              <input type="number" min={0} max={end - MIN_WINDOW_CODES} value={start} onChange={(e) => set(Math.max(0, Math.min(end - MIN_WINDOW_CODES, Number(e.target.value))), end)} />
            </label>
            <label>
              End
              <input type="number" min={start + MIN_WINDOW_CODES} max={codes.length} value={end} onChange={(e) => set(start, Math.max(start + MIN_WINDOW_CODES, Math.min(codes.length, Number(e.target.value))))} />
            </label>
          </div>
          <p className="muted">
            Plays {secondsOf(end - start)} of the sample. The whole sample ({pagesFor(codes.length)} page{pagesFor(codes.length) === 1 ? '' : 's'}) is stored on the device once, however many tracks use it; the window is free.
          </p>
        </div>
      </div>
    </div>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const ClipEditor = memo(ClipEditorView);
