import { memo } from 'react';

import { readEffects } from '../../core/pattern';
import { FX_BEHAVIOUR, FX_NAMES } from '../laws';
import { store, useAppFields } from '../store';
import { usePlaybackPick } from '../usePlayhead';

function FxRowView() {
  const { project, pattern, copying } = useAppFields('project', 'pattern', 'copying');
  if (!project) return null;
  const copyingFx = copying?.kind === 'fx';
  return (
    <div className="fxrow-wrap">
      <div className="fxrow">
        <span className="label">FX</span>
        <FxCells data={project.patterns[pattern - 1]} />
        {/* Copy and Clear act on this pattern's effects alone, as the pattern bar's do on the whole pattern. */}
        <button className={copyingFx ? 'cancel' : ''} onClick={() => (copyingFx ? store.cancelCopy() : store.startCopy('fx'))}>
          {copyingFx ? 'Cancel' : 'Copy'}
        </button>
        <button onClick={() => confirm(`Clear the effects of pattern ${pattern}?`) && store.clearEffects(pattern)}>Clear</button>
      </div>
      <Playhead pattern={pattern} />
    </div>
  );
}

/** The playhead: a thick segment under the sounding step, on the edge above the sequencer. On its own, so a step redraws only it. */
function Playhead({ pattern }: { pattern: number }) {
  const playing = usePlaybackPick((p) => (p && p.pattern === pattern ? p.step : null));
  return (
    <div className="playhead" aria-hidden="true">
      {Array.from({ length: 16 }, (_, i) => (
        <span key={i} className={i + 1 === playing ? 'on' : ''} />
      ))}
    </div>
  );
}

/** The sixteen effect cells of a pattern, memoized on its bytes: 256 options need no rebuild for unrelated changes. */
export const FxCells = memo(function FxCells({ data }: { data: Uint8Array }) {
  const effects = readEffects(data);
  return (
    <>
      {effects.map((fx, i) => (
        <label key={i} className={`fx ${fx ? 'on' : ''}`} title={fx ? `Step ${i + 1}: FX ${fx}, ${FX_NAMES[fx]}. Effect: ${FX_BEHAVIOUR[fx]}.` : `Step ${i + 1}: no effect`}>
          <span aria-hidden="true">{fx ?? '-'}</span>
          {/* The native list keeps the names; only the number shows in the cell. */}
          <select
            value={fx ?? ''}
            aria-label={`Effect on step ${i + 1}`}
            onChange={(e) => {
              const next = effects.slice();
              next[i] = e.target.value ? Number(e.target.value) : null;
              store.setEffects(next);
            }}
          >
            <option value="">- no effect</option>
            {Object.entries(FX_NAMES).map(([code, name]) => (
              <option key={code} value={code} title={FX_BEHAVIOUR[Number(code)]}>
                {code} {name}
              </option>
            ))}
          </select>
        </label>
      ))}
    </>
  );
});

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const FxRow = memo(FxRowView);
