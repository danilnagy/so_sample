import { useMemo, useState } from 'react';

import { type Modifications, isUnmodified, modifiedLength, noModifications, renderModifications } from '../../core/edits';
import { decodeMulawCodes, encodeMulaw } from '../../core/mulaw';
import { MEMORY_PAGES, pagesFor } from '../../core/project';
import { playCodes, secondsOf } from '../samples';
import { store, useAppFields } from '../store';
import { usePlayhead } from '../usePlayhead';
import { FolderPicker } from './FolderPicker';
import { PlayIcon } from './Icons';
import { Waveform } from './Waveform';

/**
 * The sample editor, in place of a sample's row in the Library: its header carries what
 * the row showed (play, name, length, pages, folder, the picker's actions) with the
 * editing state, and the body holds the waveform and the controls.
 */
export function SampleEditor({ id }: { id: string }) {
  const { samples, library, project } = useAppFields('samples', 'library', 'project');
  const sample = samples.find((s) => s.id === id);
  const original = useMemo(() => (sample ? decodeMulawCodes(sample.codes) : new Float64Array(0)), [sample]);
  const [playhead, play] = usePlayhead();
  const [picking, setPicking] = useState<DOMRect | null>(null);
  const length = sample?.codes.length ?? 0;
  const mods = useMemo(() => sample?.mods ?? noModifications(length), [sample, length]);
  // The edited result, as the device will play it, for the waveform's preview and the play button.
  const edited = useMemo(() => (sample ? renderModifications(sample.codes, mods) : new Float64Array(0)), [sample, mods]);
  if (!sample) return null;
  const set = (change: Partial<Modifications>) => store.setSampleMods(id, { ...mods, ...change });
  const modified = !isUnmodified(sample.mods, length);
  const resultLength = mods.end - mods.start;
  const pages = pagesFor(resultLength);
  const ms = (codes: number) => Math.round((codes / 23437.5) * 1000);
  const fromMs = (value: number) => Math.round((value / 1000) * 23437.5);
  const target = library.target;
  const inUse = !!project && (project.melodic.some((c) => c?.sampleId === id) || project.drums.some((d) => d?.slices.some((c) => c?.sampleId === id)));
  const folders = Array.from(new Set(samples.map((s) => s.folder))).sort();
  const use = () => {
    if (!target) return;
    store.setClip(target, { sampleId: id, start: 0, end: modifiedLength(sample.mods, length) });
    store.closeLibrary();
  };
  return (
    <div className="sample-editor">
      <header>
        <button className="play" title="Play the sample with its edits" aria-label={`Play ${sample.name}`} onClick={() => play(() => playCodes(encodeMulaw(edited)))}>
          <PlayIcon />
        </button>
        <input className="name" value={sample.name} aria-label="Sample name" title="Rename the sample" onChange={(e) => store.renameSample(id, e.target.value)} />
        <span className="muted">
          {modified ? 'modified' : 'original'}
          {inUse ? ' · in use' : ''}
        </span>
        <div className="spacer" />
        <button
          onClick={() => {
            if (confirm(`Delete "${sample.name}"? Tracks using it will be emptied.`)) void store.deleteSample(id);
          }}
        >
          Delete
        </button>
        <button onClick={() => store.closeSampleEditor()}>Done</button>
      </header>
      <div className="toolbar">
        <span className={pages > MEMORY_PAGES ? 'warn' : 'muted'} title="Length and device pages after the edits">
          {secondsOf(resultLength)} · {pages} page{pages === 1 ? '' : 's'}
          {pages > MEMORY_PAGES ? ', longer than the device memory' : ''}
        </span>
        <span className="folder">
          <button className={`folder-cell ${sample.folder ? '' : 'empty'}`} title={`${sample.folder || 'No folder'}. Click to change`} onClick={(e) => setPicking(picking ? null : e.currentTarget.getBoundingClientRect())}>
            {sample.folder || '(no folder)'}
          </button>
          {picking && (
            <FolderPicker
              value={sample.folder}
              folders={folders}
              anchor={picking}
              onClose={() => setPicking(null)}
              onPick={(f) => {
                void store.moveSample(id, f);
                setPicking(null);
              }}
            />
          )}
        </span>
        {target && <button onClick={use}>Use</button>}
        <div className="spacer" />
        <button disabled={!modified} onClick={() => set(noModifications(length))}>
          Reset
        </button>
        <button
          disabled={!modified}
          title="Bake the edits into the sample's codes"
          onClick={() => {
            if (confirm('Replace the original with the edited sample?')) void store.bakeSample(id, 'replace');
          }}
        >
          Resample
        </button>
        <button disabled={!modified} title="Bake the edits into a new library sample" onClick={() => void store.bakeSample(id, 'copy')}>
          Resample as copy
        </button>
      </div>
        <div className="editor-body">
          {/* The preview plays the trimmed result, so its position maps onto the original from the trim's start. */}
          <Waveform samples={original} start={mods.start} end={mods.end} onChange={(start, end) => set({ start, end })} playhead={playhead === null ? null : mods.start + playhead} edited={{ samples: edited, offset: mods.start }} />
          <div className="controls">
            <label>
              Start
              <input type="number" min={0} max={mods.end - 128} value={mods.start} onChange={(e) => set({ start: Math.max(0, Math.min(mods.end - 128, Number(e.target.value))) })} />
            </label>
            <label>
              End
              <input type="number" min={mods.start + 128} max={length} value={mods.end} onChange={(e) => set({ end: Math.max(mods.start + 128, Math.min(length, Number(e.target.value))) })} />
            </label>
            <label>
              Gain {mods.gainDb > 0 ? '+' : ''}
              {mods.gainDb} dB
              <input type="range" min={-24} max={24} step={0.5} value={mods.gainDb} onChange={(e) => set({ gainDb: Number(e.target.value) })} />
            </label>
            <label className="check">
              <input type="checkbox" checked={mods.normalize} onChange={(e) => set({ normalize: e.target.checked })} />
              Normalize
            </label>
            <label>
              Fade in (ms)
              <input type="number" min={0} max={ms(resultLength)} value={ms(mods.fadeIn)} onChange={(e) => set({ fadeIn: Math.min(resultLength, fromMs(Number(e.target.value))) })} />
            </label>
            <label>
              Fade out (ms)
              <input type="number" min={0} max={ms(resultLength)} value={ms(mods.fadeOut)} onChange={(e) => set({ fadeOut: Math.min(resultLength, fromMs(Number(e.target.value))) })} />
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={!!mods.compressor}
                onChange={(e) => set({ compressor: e.target.checked ? { thresholdDb: -20, ratio: 4, makeupDb: 6 } : null })}
              />
              Compressor
            </label>
          </div>
          {mods.compressor && (
            <div className="controls section" aria-label="Compressor settings">
              <label>
                Threshold {mods.compressor.thresholdDb} dB
                <input type="range" min={-60} max={0} value={mods.compressor.thresholdDb} onChange={(e) => set({ compressor: { ...mods.compressor!, thresholdDb: Number(e.target.value) } })} />
              </label>
              <label>
                Ratio {mods.compressor.ratio}:1
                <input type="range" min={1} max={20} step={0.5} value={mods.compressor.ratio} onChange={(e) => set({ compressor: { ...mods.compressor!, ratio: Number(e.target.value) } })} />
              </label>
              <label>
                Makeup +{mods.compressor.makeupDb} dB
                <input type="range" min={0} max={24} value={mods.compressor.makeupDb} onChange={(e) => set({ compressor: { ...mods.compressor!, makeupDb: Number(e.target.value) } })} />
              </label>
            </div>
          )}
          <p className="muted">Edits are applied when a project is sent; Resample bakes them into the sample.</p>
        </div>
    </div>
  );
}
