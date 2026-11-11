import { store } from '../store';

/** The first visit's welcome: what the app is, where the work is kept, and the way to the guide. */
export function Welcome() {
  return (
    <div className="modal-backdrop" onClick={() => store.dismissWelcome()}>
      <div className="modal welcome" role="dialog" aria-labelledby="welcome-title" onClick={(e) => e.stopPropagation()}>
        <header>
          <strong id="welcome-title">Welcome to SoSample</strong>
        </header>
        <div className="editor-body">
          <p>
            Build samples, kits, patterns and songs for the PO-33 K.O! in your browser, hear them here, and send them to the device through its audio input. Ten projects and seven drum kits are ready
            to play: press <b>Play</b> at the bottom.
          </p>
          <p className="muted">Everything you make is kept on this device. Nothing is uploaded.</p>
          <p className="muted">An independent, open-source project, not affiliated with Teenage Engineering.</p>
          <div className="welcome-actions">
            <button
              className="primary"
              onClick={() => {
                store.dismissWelcome();
                store.setGuide(true);
              }}
            >
              Open the guide
            </button>
            <button onClick={() => store.dismissWelcome()}>Start making</button>
          </div>
        </div>
      </div>
    </div>
  );
}
