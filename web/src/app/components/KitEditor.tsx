import { memo, useEffect, useMemo, useRef, useState } from 'react';

import { keysUsed } from '../../core/pattern';
import { pagesFor } from '../../core/project';
import { downloadBytes } from '../download';
import { playCodes, secondsOf } from '../samples';
import { kitDisplayName, store, useAppFields } from '../store';

/**
 * The kit editor: a modal with sixteen pads for one drum sound's keys, laid out like the
 * PO-33 with keys 1-4 on the top row. Its "..." pushes the clip editor for that key.
 */
/** The Kits menu hangs from its button's right edge when there is room to its left, else from its left edge, and never past the screen. */
function kitsMenuPlacement(button: DOMRect): React.CSSProperties {
  const width = Math.min(420, window.innerWidth - 16);
  if (button.right - 8 >= 280) return { right: window.innerWidth - button.right, maxWidth: Math.min(width, button.right - 8) };
  return { left: Math.max(8, Math.min(button.left, window.innerWidth - 8 - width)), maxWidth: width };
}

function KitEditorView({ slot }: { slot: number }) {
  const { project, samples, pattern, kits } = useAppFields('project', 'samples', 'pattern', 'kits');
  const [over, setOver] = useState<number | null>(null);
  /** The Kits button's rectangle while its menu is open; the menu floats from it, over the modal's edge. */
  const [menu, setMenu] = useState<DOMRect | null>(null);
  const archiveInput = useRef<HTMLInputElement>(null);
  // The Kits menu closes on a click outside it.
  useEffect(() => {
    if (!menu) return;
    const away = (e: MouseEvent) => {
      if (!(e.target as Element).closest('.menu')) setMenu(null);
    };
    document.addEventListener('mousedown', away);
    return () => document.removeEventListener('mousedown', away);
  }, [menu]);
  // The kit's own buffer: its parts packed together, which the layout pass reports row by row; one pass per change.
  const memory = useMemo(() => store.memory(project, samples), [project, samples]);
  if (!project) return null;
  const exportKit = (kitId: string) => {
    store
      .kitArchive(kitId)
      .then(({ name, bytes }) => downloadBytes(name, bytes, 'application/zip'))
      .catch((error) => store.notify((error as Error).message));
    setMenu(null);
  };
  const track = project.drums[slot - 9];
  const name = kitDisplayName(project, samples, slot);
  const used = keysUsed(project.patterns[pattern - 1], slot);
  const current = store.currentKey(slot);
  const byId = new Map(samples.map((s) => [s.id, s]));
  const stored = 'rows' in memory ? memory.rows.filter((r) => r.storedIn === `Sound ${slot} kit`).reduce((n, r) => n + r.codes, 0) : 0;
  /** A tap on a filled pad plays it and makes its key the sound's current one: the filled pad, and what the play buttons and new notes use. */
  const play = (key: number) => {
    const clip = track?.slices[key - 1];
    if (!clip) return;
    store.setCurrentKey(slot, key);
    store.audition(slot, key, () => playCodes(store.resolver()(clip.sampleId), clip.start, clip.end));
  };
  const open = (key: number) => {
    const target = { kind: 'drum' as const, slot, key };
    if (track?.slices[key - 1]) store.openClipEditor(target);
    else store.openLibrary(target);
  };
  const press = (key: number) => (track?.slices[key - 1] ? play(key) : open(key));
  const save = () => {
    const existing = kits.find((k) => k.name === name);
    if (existing && !confirm(`Replace the saved kit "${name}"?`)) return;
    void store.saveKit(slot, name, existing?.id);
  };
  return (
    <div className="modal-backdrop" onClick={() => store.closeEditor()}>
      <div className="modal editor" onClick={(e) => e.stopPropagation()}>
        <header>
          <strong>Sound {slot}</strong>
          <input className="kit-name" value={project.kitNames?.[slot - 9] ?? ''} placeholder={name} aria-label="Kit name" onChange={(e) => store.setKitName(slot, e.target.value)} />
          <span className="muted">
            {track ? `${track.slices.filter(Boolean).length} of 16 keys` : 'no samples'}
            {stored ? ` · ${pagesFor(stored)} page${pagesFor(stored) === 1 ? '' : 's'}` : ''}
          </span>
          <div className="spacer" />
          <button disabled={!track} onClick={() => confirm(`Clear every key of Sound ${slot}? Samples stay in the library.`) && store.clearDrumKit(slot)}>
            Clear kit
          </button>
          <div className="menu">
            <button className={menu ? 'on' : ''} onClick={(e) => setMenu(menu ? null : e.currentTarget.getBoundingClientRect())}>
              Kits ▾
            </button>
            {menu && (
              <div className="items kits-menu" style={{ top: menu.bottom + 2, ...kitsMenuPlacement(menu) }}>
                <button
                  disabled={!track}
                  onClick={() => {
                    save();
                    setMenu(null);
                  }}
                >
                  Save this kit as "{name}"
                </button>
                <button
                  onClick={() => {
                    archiveInput.current?.click();
                    setMenu(null);
                  }}
                >
                  Import kit…
                </button>
                {kits.length === 0 && <p className="muted">No saved kits yet.</p>}
                {kits.map((kit) => (
                  <div className="kit-row" key={kit.id}>
                    <span title={`${kit.slices.filter(Boolean).length} keys`}>{kit.name}</span>
                    <button
                      onClick={() => {
                        if (!track || confirm(`Replace the keys of Sound ${slot} with "${kit.name}"?`)) store.loadKit(kit.id, slot);
                        setMenu(null);
                      }}
                    >
                      Load
                    </button>
                    <button onClick={() => exportKit(kit.id)}>Export</button>
                    <button onClick={() => confirm(`Delete the saved kit "${kit.name}"? Its samples stay in the library.`) && void store.deleteKit(kit.id)}>Delete</button>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button onClick={() => store.closeEditor()}>Close</button>
        </header>
        <input
          ref={archiveInput}
          type="file"
          accept=".zip,application/zip"
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = '';
            if (!file) return;
            const into = !track || confirm(`Replace the keys of Sound ${slot} with the imported kit?`) ? slot : undefined;
            store
              .importKitArchive(file, into)
              .then((message) => store.notify(message))
              .catch((error) => store.notify(`Could not import ${file.name}: ${(error as Error).message}`));
          }}
        />
        <div className="editor-body">
          <div className="kit">
            {Array.from({ length: 16 }, (_, k) => {
              const key = k + 1;
              const clip = track?.slices[k] ?? null;
              const sample = clip ? byId.get(clip.sampleId) : undefined;
              const classes = ['pad'];
              if (!clip) classes.push('empty');
              if (key === current) classes.push('current');
              if (used.has(key)) classes.push('used');
              if (over === key) classes.push('over');
              return (
                <div
                  key={key}
                  role="button"
                  tabIndex={0}
                  className={classes.join(' ')}
                  aria-label={`Sound ${slot} key ${key}${sample ? `: ${sample.name}` : ', empty'}`}
                  title={`${clip ? `Key ${key}: click to play and make it the current key. Drop audio files to replace.` : `Key ${key}: click to choose a sample, or drop audio files here.`}${used.has(key) ? ' Played in the current pattern.' : ''}`}
                  onClick={() => press(key)}
                  onKeyDown={(e) => {
                    if (e.target !== e.currentTarget) return;
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      press(key);
                    }
                  }}
                  onDragOver={(e) => {
                    if (!e.dataTransfer.types.includes('Files')) return;
                    e.preventDefault();
                    setOver(key);
                  }}
                  onDragLeave={() => setOver((o) => (o === key ? null : o))}
                  onDrop={(e) => {
                    e.preventDefault();
                    setOver(null);
                    if (e.dataTransfer.files.length) void store.assignFilesToPads(slot, key, e.dataTransfer.files);
                  }}
                >
                  <span className="pad-key">{key}</span>
                  <button
                    className="pad-more"
                    title={clip ? 'Edit the window or change the sample' : 'Choose a sample'}
                    aria-label={`Edit Sound ${slot} key ${key}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      open(key);
                    }}
                  >
                    …
                  </button>
                  <span className="pad-name">{clip ? (sample?.name ?? 'missing sample') : 'empty'}</span>
                  {clip && <span className="pad-length">{secondsOf(clip.end - clip.start)}</span>}
                </div>
              );
            })}
          </div>
          <p className="muted">Click a pad to play it and make it the current key (the filled pad: what the play buttons play and a new note takes), or an empty pad to choose its sample. The … button edits a pad's window. Drop audio files on a pad to assign them from that key on. A dot marks a key the current pattern plays.</p>
        </div>
      </div>
    </div>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const KitEditor = memo(KitEditorView);
