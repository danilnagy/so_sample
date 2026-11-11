import { Fragment, memo, useEffect, useRef, useState } from 'react';

import { isUnmodified, modifiedLength } from '../../core/edits';
import { pagesFor } from '../../core/project';
import type { SampleRecord } from '../db';
import { playCodes, secondsOf } from '../samples';
import { store, useAppFields } from '../store';
import { useNarrow } from '../useNarrow';
import { FolderPicker } from './FolderPicker';
import { PencilIcon, PlayIcon, TrashIcon } from './Icons';
import { MiniWave } from './MiniWave';

const megabytes = (bytes: number): string => (bytes >= 1e9 ? `${(bytes / 1e9).toFixed(1)} GB` : `${(bytes / 1e6).toFixed(1)} MB`);

/**
 * How much of the browser's storage the site uses, as the browser estimates it, read again
 * when the library changes. The memory meter counts device pages; this counts the browser.
 */
function StorageNote({ samples }: { samples: SampleRecord[] }) {
  const [estimate, setEstimate] = useState<{ usage: number; quota: number } | null>(null);
  useEffect(() => {
    let live = true;
    navigator.storage
      ?.estimate?.()
      .then(({ usage, quota }) => {
        if (live && usage !== undefined && quota) setEstimate({ usage, quota });
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [samples]);
  if (!estimate) return null;
  return (
    <p className="muted storage-note">
      This browser holds {megabytes(estimate.usage)} for SoSample, of {megabytes(estimate.quota)} it allows the site. Export projects to keep copies elsewhere.
    </p>
  );
}
import { SampleEditor } from './SampleEditor';

const ALL = '__all__';

/**
 * A folder in the list: selects on click; when selected, a pencil renames it in place and a
 * trash empties it. With `actions` off (the chips on a phone) it is the button alone; as a
 * `bar` (under the chips on a phone) it is the selected folder's name, count and the two
 * actions as a row.
 */
function FolderRow({ name, count, selected, onSelect, onRenamed, actions = true, bar = false }: { name: string; count: number; selected: boolean; onSelect: () => void; onRenamed: (to: string) => void; actions?: boolean; bar?: boolean }) {
  const { samples } = useAppFields('samples');
  const [draft, setDraft] = useState<string | null>(null);
  const commit = () => {
    const to = (draft ?? '').trim();
    setDraft(null);
    if (!to || to === name) return;
    const existing = samples.filter((s) => s.folder === to).length;
    if (existing && !confirm(`"${to}" exists. Move the ${count} sample${count === 1 ? '' : 's'} of "${name}" into it?`)) return;
    void store.renameFolder(name, to);
    onRenamed(to);
  };
  const remove = () => {
    if (confirm(`Delete the folder "${name}"? Its ${count} sample${count === 1 ? '' : 's'} stay in the library, in no folder.`)) {
      void store.deleteFolder(name);
      onRenamed('');
    }
  };
  const editor = draft !== null && (
    <input
      className="folder-edit"
      value={draft}
      aria-label="Folder name"
      autoFocus
      onFocus={(e) => e.target.select()}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        e.stopPropagation();
        if (e.key === 'Enter') commit();
        if (e.key === 'Escape') setDraft(null);
      }}
    />
  );
  if (bar) {
    return (
      <div className="folder-bar">
        {editor || <strong title={name}>{name}</strong>}
        <span className="muted">{samplesText(count)}</span>
        <div className="spacer" />
        <button disabled={draft !== null} onClick={() => setDraft(name)}>
          Rename
        </button>
        <button onClick={remove}>Delete</button>
      </div>
    );
  }
  if (editor) return editor;
  return (
    <div className={`folder-row ${selected ? 'on' : ''}`}>
      <button className={selected ? 'on' : ''} title={name} onClick={onSelect}>
        {name}
      </button>
      {selected && actions && (
        <span className="folder-actions">
          <button className="icon-button" title="Rename the folder" aria-label={`Rename folder ${name}`} onClick={() => setDraft(name)}>
            <PencilIcon />
          </button>
          <button className="icon-button" title="Delete the folder; its samples stay, in no folder" aria-label={`Delete folder ${name}`} onClick={remove}>
            <TrashIcon />
          </button>
        </span>
      )}
    </div>
  );
}

function samplesText(count: number): string {
  return `${count} sample${count === 1 ? '' : 's'}`;
}

function LibraryView() {
  const { samples, library, project } = useAppFields('samples', 'library', 'project');
  const narrow = useNarrow();
  const [folder, setFolder] = useState(ALL);
  const [over, setOver] = useState(false);
  /** The sample whose folder picker is open, and the screen rectangle of its folder cell. */
  const [picking, setPicking] = useState<{ id: string; anchor: DOMRect } | null>(null);
  /** Samples ticked for a bulk action; ids that left the library are ignored. */
  const [ticked, setTicked] = useState<Set<string>>(() => new Set());
  const lastTicked = useRef<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const selectAll = useRef<HTMLInputElement>(null);
  const editorRow = useRef<HTMLTableRowElement>(null);
  const folders = Array.from(new Set(samples.map((s) => s.folder))).sort();
  const editing = library.editing;
  // A sample opened for editing must be in view: when a newly opened one is outside the folder filter,
  // the filter widens to all folders (derived during render), and the editor row is scrolled to.
  const [seenEditing, setSeenEditing] = useState(editing);
  if (editing !== seenEditing) {
    setSeenEditing(editing);
    const sample = editing ? samples.find((s) => s.id === editing) : undefined;
    if (sample && folder !== ALL && sample.folder !== folder) setFolder(ALL);
  }
  useEffect(() => {
    if (editing) editorRow.current?.scrollIntoView({ block: 'nearest' });
  }, [editing]);
  const shown = samples.filter((s) => folder === ALL || s.folder === folder);
  const target = library.target;
  const targetFolder = folder === ALL ? '' : folder;
  const selected = shown.filter((s) => ticked.has(s.id));
  const allShown = shown.length > 0 && selected.length === shown.length;
  useEffect(() => {
    if (selectAll.current) selectAll.current.indeterminate = selected.length > 0 && !allShown;
  }, [selected.length, allShown]);
  /** Tick or untick one sample; with Shift, every shown sample between it and the last one ticked. */
  const tick = (id: string, on: boolean, range: boolean) => {
    // The range is fixed here, before the state updater runs, since the last-ticked mark moves at once.
    const ids = [id];
    const from = lastTicked.current ? shown.findIndex((s) => s.id === lastTicked.current) : -1;
    const to = shown.findIndex((s) => s.id === id);
    if (range && from >= 0 && to >= 0) for (const s of shown.slice(Math.min(from, to), Math.max(from, to) + 1)) ids.push(s.id);
    lastTicked.current = id;
    setTicked((previous) => {
      const next = new Set(previous);
      for (const i of ids) if (on) next.add(i);
      else next.delete(i);
      return next;
    });
  };
  const deleteSelected = () => {
    const count = selected.length;
    if (!count || !confirm(`Delete ${count === 1 ? 'this sample' : `these ${count} samples`}? Tracks using them will be emptied.`)) return;
    void store.deleteSamples(selected.map((s) => s.id));
    setTicked(new Set());
  };

  const use = (sample: SampleRecord) => {
    if (!target) return;
    const length = modifiedLength(sample.mods, sample.codes.length);
    store.setClip(target, { sampleId: sample.id, start: 0, end: length });
    store.closeLibrary();
  };
  const inUse = (id: string): boolean =>
    !!project && (project.melodic.some((c) => c?.sampleId === id) || project.drums.some((d) => d?.slices.some((c) => c?.sampleId === id)));

  return (
    <div className="modal-backdrop" onClick={() => store.closeLibrary()}>
      <div className="modal wide" onClick={(e) => e.stopPropagation()}>
        <header>
          <strong>Library</strong>
          {target && (
            <span className="muted">
              {target.kind === 'melodic' ? `choosing a sample for Sound ${target.slot}` : `choosing a sample for Sound ${target.slot}, key ${target.key}`}
            </span>
          )}
          {selected.length > 0 && (
            <span className="muted">
              {selected.length} selected
            </span>
          )}
          <div className="spacer" />
          {selected.length > 0 && (
            <>
              <button onClick={deleteSelected}>Delete {selected.length === 1 ? 'selected' : `${selected.length} selected`}</button>
              <button onClick={() => setTicked(new Set())}>Clear selection</button>
            </>
          )}
          <button onClick={() => input.current?.click()}>Add files…</button>
          <input
            ref={input}
            type="file"
            accept="audio/*,.wav,.aif,.aiff,.mp3,.flac,.ogg"
            multiple
            hidden
            onChange={(e) => {
              if (e.target.files) void store.importFiles(e.target.files, targetFolder);
              e.target.value = '';
            }}
          />
          <button onClick={() => store.closeLibrary()}>Close</button>
        </header>
        <div className="library">
          <div className="folders">
            <button className={folder === ALL ? 'on' : ''} onClick={() => setFolder(ALL)}>
              All samples
            </button>
            {folders.map((f) =>
              f ? (
                <FolderRow key={f} name={f} count={samples.filter((s) => s.folder === f).length} selected={folder === f} onSelect={() => setFolder(f)} onRenamed={(to) => setFolder(to || ALL)} actions={!narrow} />
              ) : (
                <button key="none" className={folder === '' ? 'on' : ''} title="Samples in no folder" onClick={() => setFolder('')}>
                  (no folder)
                </button>
              ),
            )}
            <button
              onClick={() => {
                const name = prompt('New folder name');
                if (name) setFolder(name);
              }}
            >
              New folder
            </button>
          </div>
          {/* On a phone the chips have no room for their actions: the selected folder gets a row of its own. */}
          {narrow &&
            (folder === ALL || folder === '' ? (
              <div className="folder-bar">
                <strong>{folder === ALL ? 'All samples' : 'No folder'}</strong>
                <span className="muted">{samplesText(shown.length)}</span>
              </div>
            ) : (
              <FolderRow key={folder} bar name={folder} count={shown.length} selected onSelect={() => {}} onRenamed={(to) => setFolder(to || ALL)} />
            ))}
          <div
            className="list"
            onDragOver={(e) => {
              e.preventDefault();
              setOver(true);
            }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setOver(false);
              void store.importFiles(e.dataTransfer.files, targetFolder);
            }}
          >
            <div className={`drop ${over ? 'over' : ''}`}>
              Drop audio files here{folder !== ALL ? ` to add them to "${folder}"` : ''}. Files are mixed to mono, resampled to 23437.5 Hz and stored in this browser.
            </div>
            {shown.length === 0 && <p className="muted">No samples{folder !== ALL ? ' in this folder' : ''} yet.</p>}
            {shown.length > 0 && (
              <table>
                <colgroup>
                  <col className="select" />
                  <col className="play" />
                  <col />
                  <col className="shape" />
                  <col className="length" />
                  <col className="pages" />
                  <col className="folder" />
                  <col className={`actions ${target ? 'picking' : ''}`} />
                </colgroup>
                <thead>
                  <tr>
                    <th className="select">
                      <input
                        ref={selectAll}
                        type="checkbox"
                        checked={allShown}
                        aria-label={allShown ? 'Select none' : 'Select all'}
                        title={allShown ? 'Select none' : `Select all${folder === ALL ? '' : ' in this folder'}`}
                        onChange={(e) => setTicked(e.target.checked ? new Set([...ticked, ...shown.map((s) => s.id)]) : new Set([...ticked].filter((id) => !shown.some((s) => s.id === id))))}
                      />
                    </th>
                    <th></th>
                    <th>Name</th>
                    <th>Shape</th>
                    <th className="num">Length</th>
                    <th className="num">Pages</th>
                    <th>Folder</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {shown.map((s) => (
                    <Fragment key={s.id}>
                    {editing !== s.id && (
                    <tr className={`sample ${ticked.has(s.id) ? 'ticked' : ''}`} title="Edit the sample" onClick={() => store.openSampleEditor(s.id)}>
                      <td className="select" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={ticked.has(s.id)}
                          aria-label={`Select ${s.name}`}
                          onClick={(e) => tick(s.id, !ticked.has(s.id), e.shiftKey)}
                          onChange={() => {}}
                        />
                      </td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <button className="play" title="Play the sample" aria-label={`Play ${s.name}`} onClick={() => playCodes(store.resolver()(s.id))}>
                          <PlayIcon />
                        </button>
                      </td>
                      <td className="name" title={`${s.name}${isUnmodified(s.mods, s.codes.length) ? '' : ', edited'}${inUse(s.id) ? ', in use' : ''}. From ${s.sourceName} at ${Math.round(s.sourceRate)} Hz`}>
                        {s.name}
                        {!isUnmodified(s.mods, s.codes.length) && <span className="muted"> *</span>}
                        {inUse(s.id) && <span className="muted"> · in use</span>}
                      </td>
                      <td>
                        <MiniWave codes={s.codes} windows={[s.mods ? { start: s.mods.start, end: s.mods.end } : { start: 0, end: s.codes.length }]} title={s.mods ? 'The original, with the trimmed part marked' : 'The sample'} width={narrow ? 80 : 160} />
                      </td>
                      <td className="num">{secondsOf(modifiedLength(s.mods, s.codes.length))}</td>
                      <td className="num" data-unit={pagesFor(modifiedLength(s.mods, s.codes.length)) === 1 ? 'page' : 'pages'}>
                        {pagesFor(modifiedLength(s.mods, s.codes.length))}
                      </td>
                      <td className="folder" onClick={(e) => e.stopPropagation()}>
                        <button
                          className={`folder-cell ${s.folder ? '' : 'empty'}`}
                          title={`${s.folder || 'No folder'}. Click to change`}
                          onClick={(e) => setPicking(picking?.id === s.id ? null : { id: s.id, anchor: e.currentTarget.getBoundingClientRect() })}
                        >
                          {s.folder || '(no folder)'}
                        </button>
                        {picking?.id === s.id && (
                          <FolderPicker
                            value={s.folder}
                            folders={folders}
                            anchor={picking.anchor}
                            onClose={() => setPicking(null)}
                            onPick={(f) => {
                              void store.moveSample(s.id, f);
                              setPicking(null);
                            }}
                          />
                        )}
                      </td>
                      <td className="actions" onClick={(e) => e.stopPropagation()}>
                        {target && <button onClick={() => use(s)}>Use</button>}{' '}
                        <button
                          className="trash"
                          title="Delete the sample"
                          aria-label={`Delete ${s.name}`}
                          onClick={() => {
                            if (confirm(`Delete "${s.name}"? Tracks using it will be emptied.`)) void store.deleteSample(s.id);
                          }}
                        >
                          <TrashIcon />
                        </button>
                      </td>
                    </tr>
                    )}
                    {editing === s.id && (
                      <tr className="editor-row" ref={editorRow}>
                        <td colSpan={8}>
                          <SampleEditor id={s.id} />
                        </td>
                      </tr>
                    )}
                    </Fragment>
                  ))}
                </tbody>
              </table>
            )}
            <StorageNote samples={samples} />
          </div>
        </div>
      </div>
    </div>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const Library = memo(LibraryView);
