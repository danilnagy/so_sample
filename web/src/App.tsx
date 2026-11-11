import { useEffect } from 'react';

import { ChainStrip } from './app/components/ChainStrip';
import { FxRow } from './app/components/FxRow';
import { PatternBar } from './app/components/PatternBar';
import { StatusBar } from './app/components/StatusBar';
import { TopBar } from './app/components/TopBar';
import { TrackGrid } from './app/components/TrackGrid';
import { Modals } from './app/components/Modals';
import { MobileView } from './app/components/MobileView';
import { Welcome } from './app/components/Welcome';
import { Toast } from './app/components/Toast';
import { Guide } from './guide/Guide';
import { isGuidePath } from './guide/urls';
import { unlockAudioOnFirstGesture } from './app/samples';
import { store, useAppState } from './app/store';
import { useNarrow } from './app/useNarrow';

export default function App() {
  const state = useAppState();
  const narrow = useNarrow();
  useEffect(() => {
    void store.init();
    unlockAudioOnFirstGesture();
    const onKey = (e: KeyboardEvent) => {
      // Undo and redo, except in a text field, which keeps its own.
      const typing = e.target instanceof HTMLElement && (/^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName) || e.target.isContentEditable) && !(e.target instanceof HTMLInputElement && e.target.type === 'range');
      if ((e.metaKey || e.ctrlKey) && !e.altKey && !typing && !store.state.welcome) {
        const key = e.key.toLowerCase();
        if (key === 'z' || key === 'y') {
          e.preventDefault();
          if (key === 'y' || e.shiftKey) store.redo();
          else store.undo();
          return;
        }
      }
      if (e.key === 'Escape' && store.state.welcome) store.dismissWelcome();
      else if (e.key === 'Escape' && store.modalOpen()) store.closeTopLayer();
      else if (e.key === 'Escape') store.cancelCopy();
      // Space is the transport when no control has the keyboard, or when a transport-row button (Play, the modes,
      // Follow, tempo) has it after a click; a focused cell or field keeps it.
      if (e.key === ' ' && !e.repeat && !store.state.welcome && !store.modalOpen() && (e.target === document.body || !!(e.target as HTMLElement).closest?.('.statusbar .transport-group'))) {
        e.preventDefault();
        store.togglePlayback();
      }
    };
    window.addEventListener('keydown', onKey);
    const stopTracking = store.trackGestures();
    // Leaving the page writes the edit still waiting for its timer. The page being hidden (a tab
    // switch, the app sent to the background, the first step of closing) is the event mobile
    // browsers send dependably, and early enough for the write to finish; pagehide backs it up.
    const leave = () => void store.saveNow();
    const hidden = () => {
      if (document.visibilityState === 'hidden') leave();
    };
    document.addEventListener('visibilitychange', hidden);
    window.addEventListener('pagehide', leave);
    // The browser's back and forward buttons move between the usual layout and the guide.
    const navigate = () => store.setGuide(isGuidePath(), true);
    window.addEventListener('popstate', navigate);
    return () => {
      window.removeEventListener('keydown', onKey);
      stopTracking();
      document.removeEventListener('visibilitychange', hidden);
      window.removeEventListener('pagehide', leave);
      window.removeEventListener('popstate', navigate);
    };
  }, []);
  if (!state.ready || !state.project) return <div className="notice">{state.loading}</div>;
  // One root for both layouts, the modals after the layout: switching layout remounts the
  // layout alone, and an open Library or editor keeps its state (folder, selection).
  if (state.guide) {
    // The guide layout: the same app with every view and dialog on one page, explained.
    return (
      <div className={`app guide-mode ${narrow ? 'narrow' : ''}`}>
        <TopBar />
        <Guide />
        <StatusBar />
        <Toast />
        {state.welcome && <Welcome />}
      </div>
    );
  }
  return (
    <div className={`app ${narrow ? 'narrow' : ''}`}>
      {narrow ? (
        // Too narrow for the sequencer: the pad layout.
        <>
          <TopBar />
          <div className="main">
            <div className="stack">
              <MobileView />
            </div>
          </div>
          <StatusBar />
        </>
      ) : (
        <>
          <TopBar />
          <PatternBar />
          <FxRow />
          <div className="main">
            <div className="stack">
              <TrackGrid />
            </div>
          </div>
          <ChainStrip />
          <StatusBar />
        </>
      )}
      <Modals />
      {state.welcome && <Welcome />}
    </div>
  );
}
