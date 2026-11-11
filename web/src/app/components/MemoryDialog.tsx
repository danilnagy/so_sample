import { memo, useMemo, useState } from 'react';

import { MEMORY_PAGES, type MemoryRow } from '../../core/project';
import { playCodes, secondsOf } from '../samples';
import { store, useAppFields } from '../store';
import { useNarrow } from '../useNarrow';
import { PlayIcon } from './Icons';
import { MiniWave } from './MiniWave';

type Column = 'name' | 'length' | 'pages';

/** Every buffer the project stores on the device, sortable by sample name or size. */
function MemoryDialogView() {
  const { samples, project } = useAppFields('samples', 'project');
  const narrow = useNarrow();
  const [column, setColumn] = useState<Column>('pages');
  const [ascending, setAscending] = useState(false);
  // One layout pass per project or library change, and one stored-codes view per row, so sorting re-renders cheaply.
  const memory = useMemo(() => store.memory(project, samples), [project, samples]);
  const resolve = useMemo(() => store.resolver(samples), [samples]);
  const stored = useMemo(() => {
    const map = new Map<MemoryRow, Uint8Array>();
    if ('rows' in memory) for (const row of memory.rows) map.set(row, resolve(row.sampleId).subarray(0, row.codes));
    return map;
  }, [memory, resolve]);
  const nameOf = (id: string) => samples.find((s) => s.id === id)?.name ?? 'missing sample';
  const sortBy = (next: Column) => {
    if (next === column) setAscending(!ascending);
    else {
      setColumn(next);
      setAscending(next === 'name');
    }
  };
  /** "Sound 9 keys 1–3, 5", "Sound 1": the uses grouped by sound, keys as ranges. */
  const usedBy = (uses: string[]): string => {
    const bySound = new Map<string, number[]>();
    for (const use of uses) {
      const m = /^(Sound \d+)(?: key (\d+))?$/.exec(use)!;
      if (!bySound.has(m[1])) bySound.set(m[1], []);
      if (m[2]) bySound.get(m[1])!.push(Number(m[2]));
    }
    return [...bySound]
      .map(([sound, keys]) => {
        if (!keys.length) return sound;
        const ranges: string[] = [];
        for (let i = 0; i < keys.length; i++) {
          let j = i;
          while (j + 1 < keys.length && keys[j + 1] === keys[j] + 1) j++;
          ranges.push(j > i ? `${keys[i]}–${keys[j]}` : `${keys[i]}`);
          i = j;
        }
        return `${sound} key${keys.length > 1 ? 's' : ''} ${ranges.join(', ')}`;
      })
      .join('; ');
  };
  const arrow = (c: Column) => (c === column ? (ascending ? ' ↑' : ' ↓') : '');
  let rows: MemoryRow[] = [];
  if ('rows' in memory) {
    rows = [...memory.rows].sort((a, b) => {
      const order = column === 'name' ? nameOf(a.sampleId).localeCompare(nameOf(b.sampleId)) : column === 'length' ? a.codes - b.codes : a.pages - b.pages || a.codes - b.codes;
      return ascending ? order : -order;
    });
  }
  return (
    <div className="modal-backdrop" onClick={() => store.closeEditor()}>
      <div className="modal wide" onClick={(e) => e.stopPropagation()}>
        <header>
          <strong>Project memory</strong>
          <span className={'pages' in memory && memory.pages > MEMORY_PAGES ? 'warn' : 'muted'}>
            {'pages' in memory ? `${memory.pages} of ${MEMORY_PAGES} pages, ${secondsOf(memory.pages * 4096)}` : 'cannot be compiled'}
          </span>
          <div className="spacer" />
          <button onClick={() => store.closeEditor()}>Close</button>
        </header>
        <div className="editor-body">
          {'error' in memory ? (
            <p className="warn">{memory.error}</p>
          ) : rows.length === 0 ? (
            <p className="muted">No channel uses a sample yet.</p>
          ) : (
            <table className="memory">
              <colgroup>
                <col className="play" />
                <col className="sample" />
                <col className="shape" />
                <col className="stored" />
                <col />
                <col className="length" />
                <col className="pages" />
              </colgroup>
              <thead>
                <tr>
                  <th></th>
                  <th>
                    <button className="sort" onClick={() => sortBy('name')}>
                      Sample{arrow('name')}
                    </button>
                  </th>
                  <th>Shape</th>
                  <th>Stored in</th>
                  <th>Used by</th>
                  <th className="num">
                    <button className="sort" onClick={() => sortBy('length')}>
                      Length{arrow('length')}
                    </button>
                  </th>
                  <th className="num">
                    <button className="sort" onClick={() => sortBy('pages')}>
                      Pages{arrow('pages')}
                    </button>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={`${row.storedIn}:${row.sampleId}`}>
                    <td className="nowrap">
                      <button className="play" title="Play the stored codes" aria-label={`Play ${nameOf(row.sampleId)}`} onClick={() => playCodes(resolve(row.sampleId), 0, row.codes)}>
                        <PlayIcon />
                      </button>
                    </td>
                    <td>{nameOf(row.sampleId)}</td>
                    <td className="nowrap">
                      <MiniWave codes={stored.get(row)!} windows={row.windows} title={`${row.windows.length} window${row.windows.length === 1 ? '' : 's'} into the stored codes`} width={narrow ? 80 : 160} />
                    </td>
                    <td className="muted nowrap">{row.storedIn}</td>
                    <td className="muted">{usedBy(row.usedBy)}</td>
                    <td className="num nowrap">{secondsOf(row.codes)}</td>
                    <td className="num nowrap" data-unit={row.pages === 1 ? 'page' : 'pages'}>
                      {row.pages}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <p className="muted">
            A sample used by a melodic sound is stored once, whole, and every other use is a window into it. Samples used only by kits are stored in a kit's buffer up to the furthest window end, packed together, and a later kit needing no more of a sample plays it from there; a kit's pages are shared among its rows by length, to a tenth. The device holds {MEMORY_PAGES} pages of 4096 codes.
          </p>
        </div>
      </div>
    </div>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const MemoryDialog = memo(MemoryDialogView);
