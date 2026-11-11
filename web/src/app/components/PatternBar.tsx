import { memo } from 'react';
import { patternIsEmpty } from '../../core/pattern';
import { store, useAppFields, voiceWarning } from '../store';
import { usePlaybackPick } from '../usePlayhead';
import { WarnGlyph } from './Hint';

/** The sixteen pattern buttons; `compact` leaves out the label and the Copy and Clear buttons, for the strip above the pads on a phone. */
function PatternBarView({ compact = false }: { compact?: boolean }) {
  const { project, pattern, copying } = useAppFields('project', 'pattern', 'copying');
  const playingPattern = usePlaybackPick((p) => p?.pattern ?? null);
  if (!project) return null;
  return (
    <div className={`patterns ${compact ? 'compact' : ''}`}>
      {!compact && (
        <span className="muted" style={{ width: 200 }}>
          {copying ? (copying.kind === 'pattern' ? `Copy pattern ${copying.from} to…` : `Copy FX of pattern ${copying.from} to…`) : 'Pattern'}
        </span>
      )}
      {project.patterns.map((data, i) => {
        const number = i + 1;
        const warning = voiceWarning(data);
        return (
          <button
            key={number}
            className={`pattern ${number === pattern ? 'on' : ''} ${patternIsEmpty(data) ? '' : 'filled'} ${playingPattern === number ? 'playing' : ''} ${warning ? 'warn' : ''}`}
            title={`Pattern ${number}. Shift-click adds it to the song.${warning ? ` ${warning}.` : ''}`}
            onClick={(e) => {
              if (copying) store.copyTo(number);
              else if (e.shiftKey) store.appendToChain(number);
              else store.selectPattern(number);
            }}
          >
            {number}
            {/* The four-voice warning, on the pattern it concerns; its own tap opens the words. */}
            {warning && <WarnGlyph text={`Pattern ${number}: ${warning}.`} />}
          </button>
        );
      })}
      {!compact && (
        <>
          <button className={copying?.kind === 'pattern' ? 'cancel' : ''} onClick={() => (copying?.kind === 'pattern' ? store.cancelCopy() : store.startCopy('pattern'))}>
            {copying?.kind === 'pattern' ? 'Cancel' : 'Copy'}
          </button>
          <button onClick={() => confirm(`Clear pattern ${pattern}?`) && store.clearPattern(pattern)}>Clear</button>
        </>
      )}
    </div>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const PatternBar = memo(PatternBarView);
